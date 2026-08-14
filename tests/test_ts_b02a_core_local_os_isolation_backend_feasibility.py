from __future__ import annotations

import ctypes
import errno
import fcntl
import hashlib
import json
import os
import platform
import selectors
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path


NOT_EXECUTED = "NOT_EXECUTED"
CAPABILITY_PASS = "HOSTED_CAPABILITY_PASS"
RESULT_PREFIX = "TS_B02A_HOSTED_PROBE_RESULT="
ROOT_RESULT_PREFIX = "TS_B02A_ROOT_PROBE_RESULT="
ROOT_HANDSHAKE_PREFIX = "TS_B02A_ROOT_HELPER_HANDSHAKE="
DIAGNOSTIC_PREFIX = "TS_B02A_HOSTED_PROBE_DIAGNOSTIC="
DIAGNOSTIC_CHARACTER_LIMIT = 16_384
STAGE_PASS = "PASS"
STAGE_FAIL = "FAIL"
STAGE_NOT_REACHED = "NOT_REACHED"
CGROUP_ROOT = Path("/sys/fs/cgroup")
COMBINED_STREAM_LIMIT = 16_384
PER_STREAM_LIMIT = 12_288
SYNTHETIC_STREAM_BYTE_BUDGET = 1_048_576
SINGLE_STREAM_WRITE_COUNT = 64
COMBINED_STREAM_WRITE_COUNT = 32
COMPOSITION_HANDSHAKE_BYTES = 57
HELPER_WALL_SECONDS = 90
ROOT_HELPER_WATCHDOG_SECONDS = 75
ROOT_HELPER_HANDSHAKE_SECONDS = 8
ROOT_HELPER_GATE_SECONDS = 15
ROOT_CLEANUP_WATCHDOG_SECONDS = 15
POLL_INTERVAL_SECONDS = 0.02
OWNERSHIP_MARKER_NAME = ".ts-b02a-ownership-v1.json"
HELPER_LIFECYCLE_SUFFIX = ".root-helper-lifecycle-v1.json"
INSIDE_STAGE_ORDER = (
    "namespace_set",
    "private_propagation",
    "openat2",
    "quotas",
    "network",
    "filesystem_setup",
    "path_swap",
    "interpreter_seal",
    "pivot_root",
    "native_exec",
    "interpreter_exec",
    "process_tree_fixture",
)
ROOT_STAGE_ORDER = (
    "parent_cgroup_setup",
    "composition_setup",
    "inside_report",
    "live_host_mount_observation",
    "process_tree",
    "cgroup_kill",
    "pidfd_exit_observation",
    "composition_release",
    "stream_cgroup_setup",
    "stdout_stream_limit",
    "stdout_stream_safety",
    "stderr_stream_limit",
    "stderr_stream_safety",
    "combined_stream_limit",
    "combined_stream_safety",
    "stream_cgroup_release",
    "timeout_cgroup_setup",
    "timeout",
    "timeout_cgroup_release",
    "parent_cgroup_release",
)

CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_REMOUNT = 32
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18
MNT_DETACH = 2
AT_FDCWD = -100
AT_EMPTY_PATH = 0x1000
O_PATH = 0o10000000
RESOLVE_NO_XDEV = 0x01
RESOLVE_NO_MAGICLINKS = 0x02
RESOLVE_NO_SYMLINKS = 0x04
RESOLVE_BENEATH = 0x08
SYS_PIVOT_ROOT_X86_64 = 155
SYS_EXECVEAT_X86_64 = 322
SYS_OPENAT2_X86_64 = 437
PTRACE_TRACEME = 0
PTRACE_CONT = 7
PTRACE_SETOPTIONS = 0x4200
PTRACE_O_TRACEEXEC = 0x10
PTRACE_EVENT_EXEC = 4
PR_SET_NO_NEW_PRIVS = 38
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_ALLOW = 0x7FFF0000
AUDIT_ARCH_X86_64 = 0xC000003E
__NR_SOCKET_X86_64 = 41
SIOCGIFFLAGS = 0x8913
IFF_UP = 0x1

libc = ctypes.CDLL(None, use_errno=True)
_LAST_EXECUTION_ID: str | None = None


class _InsideStageBlocked(RuntimeError):
    def __init__(self, blocked_by: str) -> None:
        super().__init__(f"inside namespace blocked at {blocked_by}")
        self.blocked_by = blocked_by


class OpenHow(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("mode", ctypes.c_uint64),
        ("resolve", ctypes.c_uint64),
    ]


class SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class SockFprog(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_ushort),
        ("filter", ctypes.POINTER(SockFilter)),
    ]


def _raise_errno(operation: str) -> None:
    value = ctypes.get_errno()
    raise OSError(value, f"{operation}: {os.strerror(value)}")


def _mount(
    source: str | None,
    target: Path | str,
    fs_type: str | None,
    flags: int,
    data: str | None = None,
) -> None:
    result = libc.mount(
        source.encode() if source is not None else None,
        os.fsencode(target),
        fs_type.encode() if fs_type is not None else None,
        ctypes.c_ulong(flags),
        data.encode() if data is not None else None,
    )
    if result != 0:
        _raise_errno(f"mount({target})")


def _umount(target: Path | str, flags: int = 0) -> None:
    if libc.umount2(os.fsencode(target), flags) != 0:
        _raise_errno(f"umount2({target})")


def _sys_openat2(dirfd: int, path: str, *, resolve: int) -> int:
    how = OpenHow(flags=os.O_RDONLY, mode=0, resolve=resolve)
    fd = libc.syscall(
        SYS_OPENAT2_X86_64,
        dirfd,
        path.encode(),
        ctypes.byref(how),
        ctypes.sizeof(how),
    )
    if fd < 0:
        _raise_errno(f"openat2({path})")
    return int(fd)


def _execveat(fd: int, argv: list[str], environment: dict[str, str]) -> None:
    encoded_argv = [item.encode() for item in argv]
    encoded_env = [f"{key}={value}".encode() for key, value in environment.items()]
    argv_array = (ctypes.c_char_p * (len(encoded_argv) + 1))(
        *encoded_argv, None
    )
    env_array = (ctypes.c_char_p * (len(encoded_env) + 1))(*encoded_env, None)
    result = libc.syscall(
        SYS_EXECVEAT_X86_64,
        fd,
        ctypes.c_char_p(b""),
        argv_array,
        env_array,
        AT_EMPTY_PATH,
    )
    if result != 0:
        _raise_errno("execveat")


def _sha256_fd(fd: int) -> str:
    position = os.lseek(fd, 0, os.SEEK_CUR)
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while True:
        chunk = os.read(fd, 65_536)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(fd, position, os.SEEK_SET)
    return digest.hexdigest()


def _identity(fd: int) -> dict[str, int | str]:
    value = os.fstat(fd)
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "size": value.st_size,
        "sha256": _sha256_fd(fd),
    }


def _read_pt_interp(fd: int) -> str:
    position = os.lseek(fd, 0, os.SEEK_CUR)
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        header = os.read(fd, 64)
        if len(header) != 64 or header[:4] != b"\x7fELF" or header[4] != 2:
            raise AssertionError("fixture is not ELF64")
        endian = "<" if header[5] == 1 else ">"
        phoff = struct.unpack_from(endian + "Q", header, 32)[0]
        phentsize = struct.unpack_from(endian + "H", header, 54)[0]
        phnum = struct.unpack_from(endian + "H", header, 56)[0]
        for index in range(phnum):
            os.lseek(fd, phoff + index * phentsize, os.SEEK_SET)
            program = os.read(fd, phentsize)
            if len(program) < 56:
                raise AssertionError("truncated ELF program header")
            p_type = struct.unpack_from(endian + "I", program, 0)[0]
            if p_type != 3:
                continue
            offset = struct.unpack_from(endian + "Q", program, 8)[0]
            size = struct.unpack_from(endian + "Q", program, 32)[0]
            os.lseek(fd, offset, os.SEEK_SET)
            return os.read(fd, size).split(b"\0", 1)[0].decode("utf-8")
        raise AssertionError("ELF fixture has no PT_INTERP")
    finally:
        os.lseek(fd, position, os.SEEK_SET)


def _namespace_links(pid: str = "self") -> dict[str, str]:
    return {
        name: os.readlink(f"/proc/{pid}/ns/{name}")
        for name in ("mnt", "pid", "net", "ipc", "uts")
    }


def _wait_until(predicate, deadline: float, description: str) -> None:
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(f"deadline expired: {description}")


def _mark_not_reached(
    stage_results: dict[str, dict[str, object]],
    stage_order: tuple[str, ...],
    blocked_by: str,
) -> None:
    for stage in stage_order:
        if stage not in stage_results:
            stage_results[stage] = {
                "status": STAGE_NOT_REACHED,
                "blocked_by": blocked_by,
            }


def _mark_subset_not_reached(
    stage_results: dict[str, dict[str, object]],
    stages: tuple[str, ...],
    blocked_by: str,
) -> None:
    for stage in stages:
        if stage not in stage_results:
            stage_results[stage] = {
                "status": STAGE_NOT_REACHED,
                "blocked_by": blocked_by,
            }


def _first_blocking_stage(stage_results: object) -> str | None:
    if not isinstance(stage_results, dict):
        return "inside.stage_results_missing"
    for stage in INSIDE_STAGE_ORDER:
        observation = stage_results.get(stage)
        if not isinstance(observation, dict):
            return f"inside.{stage}"
        if observation.get("status") != STAGE_PASS:
            return f"inside.{stage}"
    if set(stage_results) != set(INSIDE_STAGE_ORDER):
        return "inside.stage_results_unexpected"
    return None


def _validate_inside_stage_schema(report: object) -> dict[str, dict[str, object]]:
    if not isinstance(report, dict):
        raise AssertionError("inside report is not a JSON object")
    stage_results = report.get("stage_results")
    if not isinstance(stage_results, dict):
        raise AssertionError("inside stage_results is not an object")
    if set(stage_results) != set(INSIDE_STAGE_ORDER):
        raise AssertionError(
            "inside stage_results keys are not the exact frozen stage set"
        )

    direct_failure: str | None = None
    for stage in INSIDE_STAGE_ORDER:
        key = f"inside.{stage}"
        observation = stage_results[stage]
        if not isinstance(observation, dict):
            raise AssertionError(f"{key} observation is not an object")
        status = observation.get("status")
        if status == STAGE_PASS:
            if observation != {"status": STAGE_PASS} or direct_failure is not None:
                raise AssertionError(f"{key} has an invalid PASS shape/order")
        elif status == STAGE_FAIL:
            if set(observation) != {"status", "failure"}:
                raise AssertionError(f"{key} has an invalid FAIL shape")
            failure = observation.get("failure")
            if not isinstance(failure, str) or not failure:
                raise AssertionError(f"{key} has an invalid direct failure")
            if len(failure) > DIAGNOSTIC_CHARACTER_LIMIT:
                raise AssertionError(f"{key} direct failure is unbounded")
            if direct_failure is not None:
                raise AssertionError("inside report contains multiple direct failures")
            direct_failure = key
        elif status == STAGE_NOT_REACHED:
            if set(observation) != {"status", "blocked_by"}:
                raise AssertionError(f"{key} has an invalid NOT_REACHED shape")
            if direct_failure is None or observation.get("blocked_by") != direct_failure:
                raise AssertionError(
                    f"{key} is not causally blocked by the preceding direct failure"
                )
        else:
            raise AssertionError(f"{key} has an unknown status")

    failures = report.get("failures")
    if not isinstance(failures, list) or not all(
        isinstance(item, str) and 0 < len(item) <= DIAGNOSTIC_CHARACTER_LIMIT
        for item in failures
    ):
        raise AssertionError("inside report failures list is invalid")
    if direct_failure is None:
        if failures or report.get("ready") is not True:
            raise AssertionError("successful inside report lacks exact ready evidence")
    else:
        failed_stage = direct_failure.removeprefix("inside.")
        if len(failures) != 1 or not failures[0].startswith(f"{failed_stage}: "):
            raise AssertionError("inside failures do not match the direct stage failure")
        if report.get("ready") is True:
            raise AssertionError("failed inside report cannot claim ready")
    return {
        stage: dict(stage_results[stage]) for stage in INSIDE_STAGE_ORDER
    }


def _build_stage_dependencies() -> dict[str, tuple[str, ...]]:
    dependencies: dict[str, tuple[str, ...]] = {}
    previous_inside: str | None = None
    for stage in INSIDE_STAGE_ORDER:
        key = f"inside.{stage}"
        dependencies[key] = (
            ("root.composition_setup", "root.inside_report")
            if previous_inside is None
            else (previous_inside,)
        )
        previous_inside = key
    dependencies.update(
        {
            "root.parent_cgroup_setup": (),
            "root.composition_setup": ("root.parent_cgroup_setup",),
            "root.inside_report": ("root.composition_setup",),
            "root.live_host_mount_observation": ("root.inside_report",),
            "root.process_tree": (
                "root.live_host_mount_observation",
                "inside.process_tree_fixture",
            ),
            "root.cgroup_kill": ("root.process_tree",),
            "root.pidfd_exit_observation": ("root.cgroup_kill",),
            "root.composition_release": ("root.parent_cgroup_setup",),
            "root.stream_cgroup_setup": (
                "root.parent_cgroup_setup",
                "root.composition_release",
            ),
            "root.stdout_stream_limit": ("root.stream_cgroup_setup",),
            "root.stdout_stream_safety": ("root.stream_cgroup_setup",),
            "root.stderr_stream_limit": (
                "root.stream_cgroup_setup",
                "root.stdout_stream_safety",
            ),
            "root.stderr_stream_safety": (
                "root.stream_cgroup_setup",
                "root.stdout_stream_safety",
            ),
            "root.combined_stream_limit": (
                "root.stream_cgroup_setup",
                "root.stdout_stream_safety",
                "root.stderr_stream_safety",
            ),
            "root.combined_stream_safety": (
                "root.stream_cgroup_setup",
                "root.stdout_stream_safety",
                "root.stderr_stream_safety",
            ),
            "root.stream_cgroup_release": ("root.stream_cgroup_setup",),
            "root.timeout_cgroup_setup": (
                "root.parent_cgroup_setup",
                "root.stream_cgroup_release",
            ),
            "root.timeout": ("root.timeout_cgroup_setup",),
            "root.timeout_cgroup_release": ("root.timeout_cgroup_setup",),
            "root.parent_cgroup_release": ("root.parent_cgroup_setup",),
            "cleanup": (),
        }
    )
    expected = {
        *(f"inside.{stage}" for stage in INSIDE_STAGE_ORDER),
        *(f"root.{stage}" for stage in ROOT_STAGE_ORDER),
        "cleanup",
    }
    if set(dependencies) != expected:
        raise AssertionError("frozen stage dependency graph is incomplete")
    return dependencies


def _assert_causal_result_graph(
    stage_results: dict[str, dict[str, object]],
    stage_dependencies: dict[str, tuple[str, ...] | list[str]],
    check_results: dict[str, dict[str, object]] | None = None,
    check_dependencies: dict[str, tuple[str, ...] | list[str]] | None = None,
) -> None:
    if set(stage_results) != set(stage_dependencies):
        raise AssertionError("stage result/dependency key sets differ")

    normalized_dependencies: dict[str, tuple[str, ...]] = {}
    for stage, raw_dependencies in stage_dependencies.items():
        if not isinstance(raw_dependencies, (tuple, list)) or not all(
            isinstance(item, str) for item in raw_dependencies
        ):
            raise AssertionError(f"invalid dependency list for {stage}")
        dependencies = tuple(raw_dependencies)
        if len(dependencies) != len(set(dependencies)):
            raise AssertionError(f"duplicate dependencies for {stage}")
        unknown = set(dependencies) - set(stage_results)
        if unknown:
            raise AssertionError(f"unknown dependencies for {stage}: {unknown}")
        normalized_dependencies[stage] = dependencies

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage: str) -> None:
        if stage in visiting:
            raise AssertionError(f"causal dependency cycle at {stage}")
        if stage in visited:
            return
        visiting.add(stage)
        for dependency in normalized_dependencies[stage]:
            visit(dependency)
        visiting.remove(stage)
        visited.add(stage)

    for stage in stage_results:
        visit(stage)

    ancestor_cache: dict[str, set[str]] = {}

    def ancestors(stage: str) -> set[str]:
        if stage not in ancestor_cache:
            values: set[str] = set(normalized_dependencies[stage])
            for dependency in normalized_dependencies[stage]:
                values.update(ancestors(dependency))
            ancestor_cache[stage] = values
        return ancestor_cache[stage]

    def validate_stage_observation(stage: str) -> None:
        observation = stage_results[stage]
        if not isinstance(observation, dict):
            raise AssertionError(f"stage observation is not an object: {stage}")
        status = observation.get("status")
        nonpass_dependencies = [
            dependency
            for dependency in normalized_dependencies[stage]
            if stage_results[dependency].get("status") != STAGE_PASS
        ]
        if status == STAGE_PASS:
            if observation != {"status": STAGE_PASS}:
                raise AssertionError(f"invalid PASS stage shape: {stage}")
            if nonpass_dependencies:
                raise AssertionError(
                    f"PASS stage has non-PASS prerequisites: "
                    f"{stage}->{nonpass_dependencies}"
                )
            return
        if status == STAGE_FAIL:
            if set(observation) != {"status", "failure"}:
                raise AssertionError(f"invalid FAIL stage shape: {stage}")
            failure = observation.get("failure")
            if not isinstance(failure, str) or not failure:
                raise AssertionError(f"invalid direct stage failure: {stage}")
            if nonpass_dependencies:
                raise AssertionError(
                    f"direct FAIL stage has non-PASS prerequisites: "
                    f"{stage}->{nonpass_dependencies}"
                )
            return
        if status != STAGE_NOT_REACHED or set(observation) != {
            "status",
            "blocked_by",
        }:
            raise AssertionError(f"invalid NOT_REACHED stage shape: {stage}")
        blocker = observation.get("blocked_by")
        if not isinstance(blocker, str) or blocker not in stage_results:
            raise AssertionError(f"unknown blocker for {stage}: {blocker!r}")
        if stage_results[blocker].get("status") == STAGE_PASS:
            raise AssertionError(f"PASS stage cannot block {stage}: {blocker}")
        if blocker not in ancestors(stage):
            raise AssertionError(
                f"blocker is not reachable from direct dependencies: {stage}->{blocker}"
            )
        if not nonpass_dependencies:
            raise AssertionError(
                f"NOT_REACHED stage has no non-PASS direct prerequisite: {stage}"
            )

    for stage in stage_results:
        validate_stage_observation(stage)

    for stage, observation in stage_results.items():
        if observation.get("status") != STAGE_NOT_REACHED:
            continue
        cursor = str(observation["blocked_by"])
        chain: set[str] = set()
        while stage_results[cursor].get("status") == STAGE_NOT_REACHED:
            if cursor in chain:
                raise AssertionError(f"NOT_REACHED blocker cycle from {stage}")
            chain.add(cursor)
            cursor = str(stage_results[cursor]["blocked_by"])
        if stage_results[cursor].get("status") != STAGE_FAIL:
            raise AssertionError(f"blocker chain does not terminate in FAIL: {stage}")

    if check_results is None and check_dependencies is None:
        return
    if check_results is None or check_dependencies is None:
        raise AssertionError("check results/dependencies must be supplied together")
    if set(check_results) != set(check_dependencies):
        raise AssertionError("check result/dependency key sets differ")
    for name, raw_dependencies in check_dependencies.items():
        if not isinstance(raw_dependencies, (tuple, list)) or not raw_dependencies:
            raise AssertionError(f"invalid check dependencies for {name}")
        dependencies = tuple(raw_dependencies)
        if not all(item in stage_results for item in dependencies):
            raise AssertionError(f"unknown check dependency for {name}")
        reachable = set(dependencies)
        for dependency in dependencies:
            reachable.update(ancestors(dependency))
        observation = check_results[name]
        if not isinstance(observation, dict):
            raise AssertionError(f"check observation is not an object: {name}")
        status = observation.get("status")
        if status == STAGE_PASS:
            if observation != {"status": STAGE_PASS}:
                raise AssertionError(f"invalid PASS check shape: {name}")
            nonpass_dependencies = [
                dependency
                for dependency in dependencies
                if stage_results[dependency].get("status") != STAGE_PASS
            ]
            if nonpass_dependencies:
                raise AssertionError(
                    f"PASS check has non-PASS prerequisites: "
                    f"{name}->{nonpass_dependencies}"
                )
        elif status == STAGE_FAIL:
            allowed = ({"status", "failure"}, {"status", "failure", "failed_by"})
            if set(observation) not in allowed:
                raise AssertionError(f"invalid FAIL check shape: {name}")
            if not isinstance(observation.get("failure"), str) or not observation["failure"]:
                raise AssertionError(f"invalid FAIL check evidence: {name}")
            failed_by = observation.get("failed_by")
            nonpass_dependencies = [
                dependency
                for dependency in dependencies
                if stage_results[dependency].get("status") != STAGE_PASS
            ]
            if failed_by is None:
                if nonpass_dependencies:
                    raise AssertionError(
                        f"direct FAIL check has non-PASS prerequisites: {name}"
                    )
            elif (
                failed_by not in reachable
                or stage_results[failed_by].get("status") != STAGE_FAIL
                or not nonpass_dependencies
            ):
                raise AssertionError(f"invalid failed_by for check {name}")
        elif status == STAGE_NOT_REACHED:
            if set(observation) != {"status", "blocked_by"}:
                raise AssertionError(f"invalid NOT_REACHED check shape: {name}")
            blocker = observation.get("blocked_by")
            if (
                not isinstance(blocker, str)
                or blocker not in reachable
                or stage_results[blocker].get("status") == STAGE_PASS
            ):
                raise AssertionError(f"invalid blocker for check {name}")
            if all(
                stage_results[dependency].get("status") == STAGE_PASS
                for dependency in dependencies
            ):
                raise AssertionError(
                    f"NOT_REACHED check has no non-PASS prerequisite: {name}"
                )
            cursor = blocker
            chain: set[str] = set()
            while stage_results[cursor].get("status") == STAGE_NOT_REACHED:
                if cursor in chain:
                    raise AssertionError(f"check blocker cycle: {name}")
                chain.add(cursor)
                cursor = str(stage_results[cursor]["blocked_by"])
            if stage_results[cursor].get("status") != STAGE_FAIL:
                raise AssertionError(f"check blocker does not terminate in FAIL: {name}")
        else:
            raise AssertionError(f"unknown check status: {name}")


def _run_causal_graph_negative_controls() -> dict[str, bool]:
    controls: dict[str, bool] = {}

    def rejected(operation) -> bool:
        try:
            operation()
        except AssertionError:
            return True
        return False

    def accepted(operation) -> bool:
        try:
            operation()
        except AssertionError:
            return False
        return True

    frozen_dependencies = _build_stage_dependencies()

    def accepted_failure_cascade(failed_stage: str) -> bool:
        ancestor_cache: dict[str, set[str]] = {}

        def ancestors(stage: str) -> set[str]:
            if stage not in ancestor_cache:
                values = set(frozen_dependencies[stage])
                for dependency in frozen_dependencies[stage]:
                    values.update(ancestors(dependency))
                ancestor_cache[stage] = values
            return ancestor_cache[stage]

        results = {
            stage: {"status": STAGE_PASS}
            for stage in frozen_dependencies
        }
        results[failed_stage] = {
            "status": STAGE_FAIL,
            "failure": f"synthetic direct failure at {failed_stage}",
        }
        for stage in frozen_dependencies:
            if failed_stage in ancestors(stage):
                results[stage] = {
                    "status": STAGE_NOT_REACHED,
                    "blocked_by": failed_stage,
                }
        return accepted(
            lambda: _assert_causal_result_graph(results, frozen_dependencies)
        )

    controls["parent_setup_fail_cascade_accepted"] = (
        accepted_failure_cascade("root.parent_cgroup_setup")
    )
    controls["malformed_report_fail_cascade_accepted"] = (
        accepted_failure_cascade("root.inside_report")
    )
    controls["stdout_unsafe_cleanup_cascade_accepted"] = (
        accepted_failure_cascade("root.stdout_stream_safety")
    )
    controls["stderr_unsafe_cleanup_cascade_accepted"] = (
        accepted_failure_cascade("root.stderr_stream_safety")
    )

    parent_results = {
        "root.parent_cgroup_setup": {
            "status": STAGE_FAIL,
            "failure": "synthetic parent setup failure",
        },
        "root.composition_setup": {
            "status": STAGE_NOT_REACHED,
            "blocked_by": "root.missing",
        },
    }
    parent_dependencies = {
        "root.parent_cgroup_setup": (),
        "root.composition_setup": ("root.parent_cgroup_setup",),
    }
    controls["parent_setup_unknown_blocker_rejected"] = rejected(
        lambda: _assert_causal_result_graph(parent_results, parent_dependencies)
    )

    malformed_report = {
        "stage_results": {
            INSIDE_STAGE_ORDER[0]: {"status": STAGE_PASS},
        },
        "failures": [],
        "ready": True,
    }
    controls["malformed_inside_report_rejected"] = rejected(
        lambda: _validate_inside_stage_schema(malformed_report)
    )

    def unsafe_stream_control(unsafe_stage: str, later_stage: str) -> bool:
        results = {
            "root.stream_cgroup_setup": {"status": STAGE_PASS},
            unsafe_stage: {
                "status": STAGE_FAIL,
                "failure": "synthetic unsafe shared cgroup",
            },
            later_stage: {
                "status": STAGE_NOT_REACHED,
                "blocked_by": "root.stream_cgroup_setup",
            },
        }
        dependencies = {
            "root.stream_cgroup_setup": (),
            unsafe_stage: ("root.stream_cgroup_setup",),
            later_stage: (unsafe_stage,),
        }
        return rejected(
            lambda: _assert_causal_result_graph(results, dependencies)
        )

    controls["stdout_unsafe_cleanup_false_blocker_rejected"] = (
        unsafe_stream_control(
            "root.stdout_stream_safety",
            "root.stderr_stream_limit",
        )
    )
    controls["stderr_unsafe_cleanup_false_blocker_rejected"] = (
        unsafe_stream_control(
            "root.stderr_stream_safety",
            "root.combined_stream_limit",
        )
    )
    legal_safety_results = {
        "root.stream_cgroup_setup": {"status": STAGE_PASS},
        "root.stdout_stream_safety": {
            "status": STAGE_FAIL,
            "failure": "synthetic unsafe shared cgroup",
        },
        "root.stderr_stream_limit": {
            "status": STAGE_NOT_REACHED,
            "blocked_by": "root.stdout_stream_safety",
        },
    }
    legal_safety_dependencies = {
        "root.stream_cgroup_setup": (),
        "root.stdout_stream_safety": ("root.stream_cgroup_setup",),
        "root.stderr_stream_limit": ("root.stdout_stream_safety",),
    }
    controls["safety_fail_to_later_not_reached_accepted"] = accepted(
        lambda: _assert_causal_result_graph(
            legal_safety_results,
            legal_safety_dependencies,
        )
    )
    pass_over_fail_results = {
        "root.setup": {
            "status": STAGE_FAIL,
            "failure": "synthetic setup failure",
        },
        "root.reached": {"status": STAGE_PASS},
    }
    pass_over_fail_dependencies = {
        "root.setup": (),
        "root.reached": ("root.setup",),
    }
    controls["pass_over_fail_dependency_rejected"] = rejected(
        lambda: _assert_causal_result_graph(
            pass_over_fail_results,
            pass_over_fail_dependencies,
        )
    )
    if not controls or not all(controls.values()):
        raise AssertionError(f"causal graph negative control failed: {controls}")
    return controls


def _cgroup_populated(path: Path) -> int:
    rows = dict(
        line.split(maxsplit=1)
        for line in (path / "cgroup.events").read_text(encoding="utf-8").splitlines()
    )
    return int(rows["populated"])


def _cgroup_process_ids(path: Path) -> set[int]:
    return {
        int(line)
        for line in (path / "cgroup.procs")
        .read_text(encoding="ascii")
        .splitlines()
        if line
    }


def _safe_cgroup_path(execution_id: str, suffix: str = "") -> Path:
    if not execution_id.startswith("ts-b02a-") or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for character in execution_id
    ):
        raise AssertionError("unsafe execution id")
    base = CGROUP_ROOT / execution_id
    path = base if not suffix else base / suffix
    if path.parent not in {CGROUP_ROOT, base}:
        raise AssertionError("cgroup path escaped root")
    return path


def _helper_lifecycle_path(execution_id: str, temp_root: Path) -> Path:
    if temp_root.name != execution_id:
        raise AssertionError("helper lifecycle scope does not match execution id")
    path = temp_root.parent / f".{execution_id}{HELPER_LIFECYCLE_SUFFIX}"
    if path.parent != temp_root.parent:
        raise AssertionError("helper lifecycle path escaped temporary parent")
    return path


def _argv_sha256(argv: list[str]) -> str:
    digest = hashlib.sha256()
    for argument in argv:
        encoded = os.fsencode(argument)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _proc_argv(pid: int) -> list[str]:
    payload = Path(f"/proc/{pid}/cmdline").read_bytes()
    return [
        os.fsdecode(argument)
        for argument in payload.split(b"\0")
        if argument
    ]


def _parse_proc_stat(payload: str, description: str) -> tuple[int, str]:
    try:
        tail = payload.rsplit(") ", 1)[1].split()
        state = tail[0]
        starttime = int(tail[19])
    except (IndexError, ValueError) as exc:
        raise AssertionError(f"invalid {description} identity") from exc
    return starttime, state


def _proc_starttime_and_state(pid: int) -> tuple[int, str]:
    payload = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    return _parse_proc_stat(payload, f"/proc/{pid}/stat")


def _self_proc_identity() -> tuple[int, int, str]:
    payload = Path("/proc/self/stat").read_text(encoding="ascii")
    try:
        visible_pid = int(payload.split(" ", 1)[0])
    except (IndexError, ValueError) as exc:
        raise AssertionError("invalid /proc/self visible PID") from exc
    starttime, state = _parse_proc_stat(payload, "/proc/self/stat")
    return visible_pid, starttime, state


def _stat_identity(path: Path | str) -> dict[str, int]:
    value = os.stat(path)
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "size": value.st_size,
    }


def _regular_file_identity(path: Path) -> dict[str, int | str]:
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        value = os.fstat(fd)
        if not stat.S_ISREG(value.st_mode):
            raise AssertionError(f"identity target is not a regular file: {path}")
        return _identity(fd)
    finally:
        os.close(fd)


def _current_root_helper_identity(
    execution_id: str,
    nonce: str,
    source_file: Path,
) -> dict[str, object]:
    pid, starttime, _ = _self_proc_identity()
    return {
        "version": 1,
        "execution_id": execution_id,
        "nonce_sha256": hashlib.sha256(nonce.encode("ascii")).hexdigest(),
        "pid": pid,
        "starttime": starttime,
        "argv_sha256": _argv_sha256(_proc_argv(pid)),
        "source_path": str(source_file),
        "source_identity": _regular_file_identity(source_file),
        "executable_identity": _stat_identity(f"/proc/{pid}/exe"),
    }


def _validate_helper_identity(
    identity: object,
    execution_id: str,
    nonce: str,
    expected_helper: dict[str, object],
) -> dict[str, object]:
    if set(expected_helper) != {
        "argv_sha256",
        "source_path",
        "source_identity",
        "executable_identity",
    }:
        raise AssertionError("expected root helper identity fields are not exact")
    if not isinstance(identity, dict):
        raise AssertionError("root helper identity is not an object")
    expected_keys = {
        "version",
        "execution_id",
        "nonce_sha256",
        "pid",
        "starttime",
        "argv_sha256",
        "source_path",
        "source_identity",
        "executable_identity",
    }
    if set(identity) != expected_keys:
        raise AssertionError("root helper identity fields are not exact")
    if (
        identity.get("version") != 1
        or identity.get("execution_id") != execution_id
        or identity.get("nonce_sha256")
        != hashlib.sha256(nonce.encode("ascii")).hexdigest()
        or not isinstance(identity.get("pid"), int)
        or int(identity["pid"]) <= 1
        or not isinstance(identity.get("starttime"), int)
        or int(identity["starttime"]) <= 0
    ):
        raise AssertionError("root helper process binding is invalid")
    for key in (
        "argv_sha256",
        "source_path",
        "source_identity",
        "executable_identity",
    ):
        if identity.get(key) != expected_helper.get(key):
            raise AssertionError(f"root helper {key} identity mismatch")
    return dict(identity)


def _write_helper_lifecycle(
    path: Path,
    record: dict[str, object],
    creator_uid: int,
) -> None:
    current = os.lstat(path)
    if (
        not stat.S_ISREG(current.st_mode)
        or path.is_symlink()
        or current.st_uid != creator_uid
        or stat.S_IMODE(current.st_mode) != 0o600
    ):
        raise AssertionError("helper lifecycle claim identity changed")
    replacement = path.with_name(path.name + ".next")
    fd = -1
    try:
        fd = os.open(
            replacement,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | os.O_NOFOLLOW,
            0o600,
        )
        _write_all(fd, json.dumps(record, sort_keys=True).encode("utf-8"))
        os.fsync(fd)
        os.close(fd)
        fd = -1
        replacement_stat = os.lstat(replacement)
        if replacement_stat.st_uid != creator_uid:
            raise AssertionError("helper lifecycle replacement owner changed")
        os.replace(replacement, path)
        _fsync_directory(path.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        if os.path.lexists(replacement):
            replacement_stat = os.lstat(replacement)
            if (
                stat.S_ISREG(replacement_stat.st_mode)
                and replacement_stat.st_uid == creator_uid
            ):
                replacement.unlink()


def _create_helper_lifecycle(
    execution_id: str,
    temp_root: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
    expected_helper: dict[str, object],
) -> tuple[Path, dict[str, object]]:
    _validate_nonce(nonce)
    _validate_temp_scope(
        execution_id,
        temp_root,
        creator_uid,
        parent_device,
        parent_inode,
    )
    if os.path.lexists(temp_root):
        raise AssertionError("temporary root exists before helper launch")
    path = _helper_lifecycle_path(execution_id, temp_root)
    if os.path.lexists(path) or os.path.lexists(path.with_name(path.name + ".next")):
        raise AssertionError("helper lifecycle claim collision")
    record: dict[str, object] = {
        "version": 1,
        "state": "launching",
        "execution_id": execution_id,
        "nonce": nonce,
        "temp_root": str(temp_root),
        "creator_uid": creator_uid,
        "parent_device": parent_device,
        "parent_inode": parent_inode,
        "expected_helper": expected_helper,
    }
    fd = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        _write_all(fd, json.dumps(record, sort_keys=True).encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)
    return path, record


def _load_helper_lifecycle(
    execution_id: str,
    temp_root: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
    *,
    require_bound: bool,
) -> tuple[Path, dict[str, object]]:
    _validate_nonce(nonce)
    _validate_temp_scope(
        execution_id,
        temp_root,
        creator_uid,
        parent_device,
        parent_inode,
    )
    path = _helper_lifecycle_path(execution_id, temp_root)
    value = os.lstat(path)
    if (
        not stat.S_ISREG(value.st_mode)
        or path.is_symlink()
        or value.st_uid != creator_uid
        or stat.S_IMODE(value.st_mode) != 0o600
    ):
        raise AssertionError("helper lifecycle claim is not creator-owned 0600")
    record = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "version": 1,
        "execution_id": execution_id,
        "nonce": nonce,
        "temp_root": str(temp_root),
        "creator_uid": creator_uid,
        "parent_device": parent_device,
        "parent_inode": parent_inode,
    }
    if not isinstance(record, dict) or any(
        record.get(key) != item for key, item in expected.items()
    ):
        raise AssertionError("helper lifecycle binding mismatch")
    expected_helper = record.get("expected_helper")
    if not isinstance(expected_helper, dict):
        raise AssertionError("helper lifecycle expected identity is invalid")
    state = record.get("state")
    if state == "bound":
        _validate_helper_identity(
            record.get("helper_identity"),
            execution_id,
            nonce,
            expected_helper,
        )
    elif require_bound:
        raise AssertionError("root helper identity was not persistently bound")
    elif state != "launching" or "helper_identity" in record:
        raise AssertionError("helper lifecycle state is invalid")
    return path, record


def _bind_helper_lifecycle(
    path: Path,
    record: dict[str, object],
    helper_identity: object,
    execution_id: str,
    nonce: str,
    creator_uid: int,
) -> dict[str, object]:
    if record.get("state") != "launching":
        raise AssertionError("helper lifecycle was not in launching state")
    expected_helper = record.get("expected_helper")
    if not isinstance(expected_helper, dict):
        raise AssertionError("helper lifecycle expected identity is invalid")
    validated = _validate_helper_identity(
        helper_identity,
        execution_id,
        nonce,
        expected_helper,
    )
    live_state, live_failures = _inspect_bound_helper(
        validated,
        require_privileged_identity=False,
    )
    if live_state != "matching" or live_failures:
        raise AssertionError(
            "root helper was not live with its exact identity before bind: "
            f"state={live_state}, failures={live_failures}"
        )
    record["state"] = "bound"
    record["helper_identity"] = validated
    _write_helper_lifecycle(path, record, creator_uid)
    return validated


def _inspect_bound_helper(
    identity: dict[str, object],
    *,
    require_privileged_identity: bool = True,
) -> tuple[str, list[str]]:
    pid = int(identity["pid"])
    try:
        starttime, process_state = _proc_starttime_and_state(pid)
    except FileNotFoundError:
        return "gone", []
    except ProcessLookupError:
        return "gone", []
    if starttime != int(identity["starttime"]):
        return "pid_reused", []
    if process_state == "Z":
        return "matching_zombie", []
    mismatches: list[str] = []
    try:
        if os.stat(f"/proc/{pid}").st_uid != 0:
            mismatches.append("helper uid is not root")
        if _argv_sha256(_proc_argv(pid)) != identity.get("argv_sha256"):
            mismatches.append("helper argv identity changed")
        if require_privileged_identity:
            if _stat_identity(f"/proc/{pid}/exe") != identity.get(
                "executable_identity"
            ):
                mismatches.append("helper executable identity changed")
            source_path = identity.get("source_path")
            if not isinstance(source_path, str) or _regular_file_identity(
                Path(source_path)
            ) != identity.get("source_identity"):
                mismatches.append("helper source identity changed")
    except (FileNotFoundError, ProcessLookupError):
        try:
            current_starttime, _ = _proc_starttime_and_state(pid)
        except (FileNotFoundError, ProcessLookupError):
            return "gone", []
        if current_starttime != int(identity["starttime"]):
            return "pid_reused", []
        mismatches.append("helper identity observation was lost")
    return ("identity_mismatch", mismatches) if mismatches else ("matching", [])


def _terminate_bound_helper(identity: dict[str, object]) -> dict[str, object]:
    pid = int(identity["pid"])
    evidence: dict[str, object] = {
        "initial_state": "unobserved",
        "helper_was_active": False,
        "helper_pidfd_opened": False,
        "helper_pidfd_open_esrch": False,
        "helper_pid_reuse_observed": False,
        "helper_sigkill_sent": False,
        "helper_signal_esrch": False,
        "helper_pidfd_exit_observed": False,
        "helper_terminated": False,
    }
    pidfd = -1
    try:
        try:
            pidfd = os.pidfd_open(pid)
        except ProcessLookupError:
            evidence.update(
                {
                    "initial_state": "gone_before_pidfd_open",
                    "helper_pidfd_open_esrch": True,
                    "helper_pidfd_exit_observed": True,
                    "helper_terminated": True,
                }
            )
            return evidence
        evidence["helper_pidfd_opened"] = True

        status, failures = _inspect_bound_helper(identity)
        evidence["initial_state"] = status
        evidence["helper_was_active"] = status in {
            "matching",
            "matching_zombie",
        }
        if failures or status == "identity_mismatch":
            raise AssertionError(
                "root helper identity mismatch; pidfd termination refused: "
                + repr(failures)
            )
        if status == "pid_reused":
            evidence["helper_pid_reuse_observed"] = True
            evidence["helper_terminated"] = True
            return evidence
        if status == "matching":
            try:
                signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                evidence["helper_sigkill_sent"] = True
            except ProcessLookupError:
                evidence["helper_signal_esrch"] = True

        poller = selectors.DefaultSelector()
        try:
            poller.register(pidfd, selectors.EVENT_READ)
            readable = bool(poller.select(timeout=8))
        finally:
            poller.close()
        evidence["helper_pidfd_exit_observed"] = readable
        evidence["helper_terminated"] = readable
        if not readable:
            raise AssertionError(
                "root helper pidfd did not become readable after termination gate"
            )
        return evidence
    finally:
        if pidfd >= 0:
            os.close(pidfd)


def _remove_bound_helper_lifecycle(
    path: Path,
    creator_uid: int,
    failures: list[str],
) -> None:
    replacement = path.with_name(path.name + ".next")
    if os.path.lexists(replacement):
        failures.append(
            "helper lifecycle replacement residue prevents claim removal"
        )
        return
    try:
        value = os.lstat(path)
    except FileNotFoundError:
        failures.append("bound helper lifecycle claim disappeared")
        return
    if (
        not stat.S_ISREG(value.st_mode)
        or path.is_symlink()
        or value.st_uid != creator_uid
        or stat.S_IMODE(value.st_mode) != 0o600
    ):
        failures.append("bound helper lifecycle identity changed before removal")
        return
    try:
        path.unlink()
        _fsync_directory(path.parent)
    except BaseException as exc:
        failures.append(f"bound helper lifecycle removal failed: {exc!r}")


def _validate_nonce(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise AssertionError("ownership nonce must be exactly 64 lowercase hex characters")


def _validate_temp_scope(
    execution_id: str,
    temp_root: Path,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
) -> os.stat_result:
    if temp_root.name != execution_id:
        raise AssertionError("temporary root name does not exactly match execution id")
    parent = temp_root.parent
    parent_stat = os.lstat(parent)
    if not stat.S_ISDIR(parent_stat.st_mode) or parent.is_symlink():
        raise AssertionError("temporary parent is not a real directory")
    if parent.resolve(strict=True) != parent.absolute():
        raise AssertionError("temporary parent contains a symlink")
    if parent == Path("/") or creator_uid <= 0:
        raise AssertionError("unsafe temporary parent or creator uid")
    if (
        parent_stat.st_uid != creator_uid
        or parent_stat.st_dev != parent_device
        or parent_stat.st_ino != parent_inode
    ):
        raise AssertionError("temporary parent ownership identity changed")
    if stat.S_IMODE(parent_stat.st_mode) & 0o022:
        raise AssertionError("temporary parent is group/world writable")
    return parent_stat


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_all(fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(fd, payload[offset:])
        if written <= 0:
            raise AssertionError("short ownership journal write")
        offset += written


def _write_ownership_journal(marker: Path, journal: dict[str, object]) -> None:
    replacement = marker.with_name(marker.name + ".next")
    payload = json.dumps(journal, sort_keys=True).encode("utf-8")
    fd = -1
    try:
        fd = os.open(
            replacement,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | os.O_NOFOLLOW,
            0o600,
        )
        _write_all(fd, payload)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(replacement, marker)
        _fsync_directory(marker.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        if replacement.exists():
            replacement_stat = os.lstat(replacement)
            if (
                stat.S_ISREG(replacement_stat.st_mode)
                and replacement_stat.st_uid == 0
            ):
                replacement.unlink()


def _create_ownership_journal(
    execution_id: str,
    temp_root: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
    helper_identity: dict[str, object],
) -> tuple[Path, dict[str, object]]:
    _validate_nonce(nonce)
    parent_stat = _validate_temp_scope(
        execution_id,
        temp_root,
        creator_uid,
        parent_device,
        parent_inode,
    )
    if os.path.lexists(temp_root):
        raise AssertionError("temporary root collision before ownership claim")
    temp_root.mkdir(mode=0o700)
    marker = temp_root / OWNERSHIP_MARKER_NAME
    journal: dict[str, object] = {
        "version": 1,
        "execution_id": execution_id,
        "nonce": nonce,
        "temp_root": str(temp_root),
        "creator_uid": creator_uid,
        "parent_device": parent_stat.st_dev,
        "parent_inode": parent_stat.st_ino,
        "helper_identity": helper_identity,
        "cgroups": {},
    }
    fd = os.open(
        marker,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        _write_all(fd, json.dumps(journal, sort_keys=True).encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(temp_root)
    return marker, journal


def _load_ownership_journal(
    execution_id: str,
    temp_root: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
    helper_identity: dict[str, object],
) -> tuple[Path, dict[str, object]]:
    _validate_nonce(nonce)
    _validate_temp_scope(
        execution_id,
        temp_root,
        creator_uid,
        parent_device,
        parent_inode,
    )
    root_stat = os.lstat(temp_root)
    if (
        not stat.S_ISDIR(root_stat.st_mode)
        or temp_root.is_symlink()
        or root_stat.st_uid != 0
        or stat.S_IMODE(root_stat.st_mode) != 0o700
    ):
        raise AssertionError("temporary root ownership marker scope is invalid")
    marker = temp_root / OWNERSHIP_MARKER_NAME
    marker_stat = os.lstat(marker)
    if (
        not stat.S_ISREG(marker_stat.st_mode)
        or marker.is_symlink()
        or marker_stat.st_uid != 0
        or stat.S_IMODE(marker_stat.st_mode) != 0o600
    ):
        raise AssertionError("ownership marker identity is invalid")
    journal = json.loads(marker.read_text(encoding="utf-8"))
    expected = {
        "version": 1,
        "execution_id": execution_id,
        "nonce": nonce,
        "temp_root": str(temp_root),
        "creator_uid": creator_uid,
        "parent_device": parent_device,
        "parent_inode": parent_inode,
        "helper_identity": helper_identity,
    }
    if any(journal.get(key) != value for key, value in expected.items()):
        raise AssertionError("ownership journal binding mismatch")
    if not isinstance(journal.get("cgroups"), dict):
        raise AssertionError("ownership journal cgroups field is invalid")
    return marker, journal


def _claim_cgroup(
    path: Path,
    marker: Path,
    journal: dict[str, object],
) -> None:
    key = str(path)
    cgroups = journal["cgroups"]
    if key in cgroups and cgroups[key].get("state") != "released":
        raise AssertionError(f"cgroup already claimed in journal: {path}")
    if path.exists():
        cgroups[key] = {"state": "collision"}
        _write_ownership_journal(marker, journal)
        raise AssertionError(f"cgroup collision before claim: {path}")
    cgroups[key] = {"state": "claiming"}
    _write_ownership_journal(marker, journal)
    try:
        path.mkdir()
    except BaseException:
        cgroups[key] = {"state": "collision"}
        _write_ownership_journal(marker, journal)
        raise
    value = os.stat(path)
    cgroups[key] = {
        "state": "owned",
        "device": value.st_dev,
        "inode": value.st_ino,
    }
    _write_ownership_journal(marker, journal)


def _release_owned_cgroup(
    path: Path,
    marker: Path,
    journal: dict[str, object],
    failures: list[str],
) -> None:
    key = str(path)
    entry = journal.get("cgroups", {}).get(key)
    if not isinstance(entry, dict):
        failures.append(f"cgroup is not listed in ownership journal: {path}")
        return
    if entry.get("state") == "released":
        if path.exists():
            failures.append(f"released cgroup path reappeared: {path}")
        return
    if entry.get("state") != "owned":
        failures.append(
            f"cgroup cleanup refused for non-owned state {entry.get('state')}: {path}"
        )
        return
    if path.exists():
        value = os.stat(path)
        if value.st_dev != entry.get("device") or value.st_ino != entry.get("inode"):
            failures.append(f"cgroup ownership identity changed: {path}")
            return
        local_failures: list[str] = []
        _kill_and_remove_cgroup(path, local_failures)
        if local_failures or path.exists():
            failures.extend(local_failures or [f"owned cgroup remains: {path}"])
            return
    entry["state"] = "released"
    _write_ownership_journal(marker, journal)


def _release_owned_parent_cgroup(
    path: Path,
    expected_children: tuple[Path, ...],
    marker: Path,
    journal: dict[str, object],
    failures: list[str],
) -> None:
    key = str(path)
    cgroups = journal.get("cgroups", {})
    entry = cgroups.get(key) if isinstance(cgroups, dict) else None
    if not isinstance(entry, dict):
        failures.append(f"parent cgroup is not listed in ownership journal: {path}")
        return
    if entry.get("state") == "released":
        if path.exists():
            failures.append(f"released parent cgroup path reappeared: {path}")
        return
    if entry.get("state") != "owned":
        failures.append(
            "parent cgroup no-kill release refused for non-owned state "
            f"{entry.get('state')}: {path}"
        )
        return
    allowed_keys = {key, *(str(child) for child in expected_children)}
    unexpected_keys = set(cgroups) - allowed_keys
    if unexpected_keys:
        failures.append(
            "parent cgroup no-kill release refused for unexpected journal "
            f"paths: {sorted(unexpected_keys)}"
        )
        return
    incomplete_children = {
        str(child): cgroups[str(child)]
        for child in expected_children
        if str(child) in cgroups
        and (
            not isinstance(cgroups[str(child)], dict)
            or cgroups[str(child)].get("state") != "released"
        )
    }
    if incomplete_children:
        failures.append(
            "parent cgroup no-kill release refused because expected children "
            f"are not released: {incomplete_children}"
        )
        return
    existing_expected_children = [
        str(child) for child in expected_children if child.exists()
    ]
    if existing_expected_children:
        failures.append(
            "parent cgroup no-kill release refused because expected child "
            f"paths remain: {existing_expected_children}"
        )
        return
    if not path.exists():
        failures.append(f"owned parent cgroup disappeared before release: {path}")
        return
    value = os.stat(path)
    if value.st_dev != entry.get("device") or value.st_ino != entry.get("inode"):
        failures.append(f"parent cgroup ownership identity changed: {path}")
        return
    child_directories = sorted(
        str(candidate)
        for candidate in path.iterdir()
        if candidate.is_dir()
    )
    if child_directories:
        failures.append(
            "parent cgroup no-kill release refused because child directories "
            f"remain: {child_directories}"
        )
        return
    try:
        populated = _cgroup_populated(path)
    except BaseException as exc:
        failures.append(f"parent populated observation failed: {exc!r}")
        return
    if populated != 0:
        failures.append(
            "parent cgroup no-kill release refused because populated != 0: "
            f"{populated}"
        )
        return
    try:
        path.rmdir()
    except BaseException as exc:
        failures.append(f"parent cgroup no-kill removal failed: {exc!r}")
        return
    entry["state"] = "released"
    _write_ownership_journal(marker, journal)


def _kill_and_remove_cgroup(path: Path, failures: list[str]) -> None:
    if not path.exists():
        return
    try:
        kill_path = path / "cgroup.kill"
        if kill_path.exists():
            kill_path.write_text("1", encoding="ascii")
        _wait_until(
            lambda: _cgroup_populated(path) == 0,
            time.monotonic() + 8,
            f"{path} populated=0",
        )
    except BaseException as exc:  # cleanup failure must survive the original error
        failures.append(f"cgroup cleanup {path}: {exc!r}")
    try:
        if path.exists():
            path.rmdir()
    except FileNotFoundError:
        pass
    except BaseException as exc:
        failures.append(f"cgroup removal {path}: {exc!r}")


def _compile_fixture(temp_root: Path) -> Path:
    source = temp_root / "synthetic_fixture.c"
    binary = temp_root / "synthetic_fixture"
    source.write_text(
        r'''
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

int main(void) {
    const char *blocked = getenv("TS_B02A_BLOCKED_FD");
    int blocked_fd = blocked ? atoi(blocked) : -1;
    const int domains[] = {AF_INET, AF_INET6, AF_NETLINK, AF_PACKET};
    if (getuid() == 0 || getgid() == 0) return 21;
    if (blocked_fd < 0 || fcntl(blocked_fd, F_GETFD) != -1 || errno != EBADF) return 22;
    for (unsigned long index = 0; index < sizeof(domains) / sizeof(domains[0]); index++) {
        errno = 0;
        if (socket(domains[index], SOCK_STREAM, 0) != -1 || errno != EPERM) return 23 + (int)index;
    }
    if (write(STDOUT_FILENO, "NATIVE_SEALED_OK\n", 17) != 17) return 24;
    if (write(STDERR_FILENO, "NETWORK_DENIED_OK\n", 18) != 18) return 25;
    return 0;
}
'''.lstrip(),
        encoding="utf-8",
    )
    compiler = Path("/usr/bin/cc")
    if not compiler.is_file():
        raise AssertionError("/usr/bin/cc is unavailable")
    completed = subprocess.run(
        [str(compiler), "-O2", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "synthetic ELF compilation failed: "
            + completed.stderr.decode("utf-8", "replace")
        )
    return binary


def _install_socket_seccomp() -> None:
    # BPF: reject a non-x86_64 ABI, return EPERM for socket(2), allow otherwise.
    instructions = (SockFilter * 7)(
        SockFilter(0x20, 0, 0, 4),
        SockFilter(0x15, 1, 0, AUDIT_ARCH_X86_64),
        SockFilter(0x06, 0, 0, SECCOMP_RET_KILL_PROCESS),
        SockFilter(0x20, 0, 0, 0),
        SockFilter(0x15, 0, 1, __NR_SOCKET_X86_64),
        SockFilter(0x06, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM),
        SockFilter(0x06, 0, 0, SECCOMP_RET_ALLOW),
    )
    program = SockFprog(len=len(instructions), filter=instructions)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        _raise_errno("prctl(PR_SET_NO_NEW_PRIVS)")
    if libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(program)) != 0:
        _raise_errno("prctl(PR_SET_SECCOMP)")


def _drop_privileges_and_close_fds(keep: set[int]) -> None:
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    descriptors = [
        int(entry.name)
        for entry in Path("/proc/self/fd").iterdir()
        if entry.name.isdigit()
    ]
    for fd in descriptors:
        if fd > 2 and fd not in keep:
            try:
                os.close(fd)
            except OSError:
                pass
    _install_socket_seccomp()


def _loader_observed(pid: int, expected: os.stat_result) -> bool:
    expected_device = f"{os.major(expected.st_dev):02x}:{os.minor(expected.st_dev):02x}"
    for line in Path(f"/proc/{pid}/maps").read_text(encoding="utf-8").splitlines():
        columns = line.split(maxsplit=5)
        if len(columns) < 5:
            continue
        if columns[3] == expected_device and int(columns[4]) == expected.st_ino:
            return True
    return False


def _status_at_exec(pid: int) -> dict[str, str]:
    return {
        line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines()
        if ":" in line
    }


def _fd_absent_at_exec_stop(pid: int, descriptor: int) -> bool:
    directory = Path(f"/proc/{pid}/fd")
    try:
        directory_status = os.stat(directory)
    except OSError as exc:
        raise AssertionError(
            f"exec-stop FD directory observation failed: {exc!r}"
        ) from exc
    if not stat.S_ISDIR(directory_status.st_mode):
        raise AssertionError("exec-stop FD observation path is not a directory")
    path = directory / str(descriptor)
    try:
        os.lstat(path)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return True
        raise AssertionError(
            f"inherited-FD lstat observation failed at exec stop: {exc!r}"
        ) from exc
    try:
        os.readlink(path)
    except OSError as exc:
        raise AssertionError(
            f"inherited-FD readlink observation failed at exec stop: {exc!r}"
        ) from exc
    return False


def _ptraced_exec(
    executable_fd: int,
    argv: list[str],
    environment: dict[str, str],
    expected_loader: os.stat_result,
    blocked_socket_fd: int,
) -> dict[str, object]:
    expected_executable = os.fstat(executable_fd)
    child = os.fork()
    if child == 0:
        try:
            if libc.ptrace(PTRACE_TRACEME, 0, None, None) != 0:
                _raise_errno("ptrace(TRACEME)")
            os.kill(os.getpid(), signal.SIGSTOP)
            _drop_privileges_and_close_fds({executable_fd})
            environment = dict(environment)
            environment["TS_B02A_BLOCKED_FD"] = str(blocked_socket_fd)
            _execveat(executable_fd, argv, environment)
        except BaseException:
            os._exit(126)
        os._exit(127)

    first_pid, first_status = os.waitpid(child, 0)
    if first_pid != child or not os.WIFSTOPPED(first_status):
        raise AssertionError("ptrace child did not enter initial stop")
    if libc.ptrace(PTRACE_SETOPTIONS, child, None, PTRACE_O_TRACEEXEC) != 0:
        _raise_errno("ptrace(SETOPTIONS)")
    if libc.ptrace(PTRACE_CONT, child, None, None) != 0:
        _raise_errno("ptrace(CONT)")

    deadline = time.monotonic() + 8
    exec_observation: dict[str, object] | None = None
    exit_code: int | None = None
    while time.monotonic() < deadline:
        waited_pid, status = os.waitpid(child, 0)
        if waited_pid != child:
            continue
        if os.WIFEXITED(status):
            exit_code = os.WEXITSTATUS(status)
            break
        if os.WIFSIGNALED(status):
            raise AssertionError(f"ptraced child signaled: {os.WTERMSIG(status)}")
        if not os.WIFSTOPPED(status):
            continue
        event = status >> 16
        if event == PTRACE_EVENT_EXEC:
            actual_executable = os.stat(f"/proc/{child}/exe")
            status_rows = _status_at_exec(child)
            exec_observation = {
                "event": event,
                "exe_identity_match": (
                    actual_executable.st_dev == expected_executable.st_dev
                    and actual_executable.st_ino == expected_executable.st_ino
                ),
                "loader_identity_match": _loader_observed(
                    child, expected_loader
                ),
                "uid_non_root": not status_rows["Uid"].startswith("0\t"),
                "gid_non_root": not status_rows["Gid"].startswith("0\t"),
                "cap_eff_zero": int(status_rows["CapEff"], 16) == 0,
                "no_new_privs": status_rows["NoNewPrivs"] == "1",
                "inherited_network_fd_absent_at_exec": (
                    _fd_absent_at_exec_stop(child, blocked_socket_fd)
                ),
            }
        if libc.ptrace(PTRACE_CONT, child, None, None) != 0:
            _raise_errno("ptrace(CONT after stop)")
    if exit_code is None:
        os.kill(child, signal.SIGKILL)
        os.waitpid(child, 0)
        raise AssertionError("ptraced child exceeded deadline")
    if exec_observation is None:
        raise AssertionError("PTRACE_EVENT_EXEC observation missing")
    exec_observation["exit_code"] = exit_code
    return exec_observation


def _probe_openat2(root: Path) -> dict[str, object]:
    boundary = root / "openat2-boundary"
    boundary.mkdir()
    (boundary / "inside").write_bytes(b"inside")
    (boundary / "outside-link").symlink_to("/etc/passwd")
    (boundary / "magic-link").symlink_to("/proc/self/fd/0")
    (boundary / "mounted").mkdir()
    _mount("tmpfs", boundary / "mounted", "tmpfs", MS_NOSUID | MS_NODEV, "size=4096")
    root_fd = os.open(boundary, O_PATH | os.O_DIRECTORY)
    resolution = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS | RESOLVE_NO_XDEV
    denied: dict[str, int] = {}
    magiclink_only_denied = False
    try:
        fd = _sys_openat2(root_fd, "inside", resolve=resolution)
        try:
            positive = os.read(fd, 6) == b"inside"
        finally:
            os.close(fd)
        for label, candidate in (
            ("traversal", "../etc/passwd"),
            ("symlink", "outside-link"),
            ("xdev", "mounted"),
        ):
            try:
                escaped = _sys_openat2(root_fd, candidate, resolve=resolution)
            except OSError as exc:
                if exc.errno not in {errno.EXDEV, errno.ELOOP}:
                    raise
                denied[label] = exc.errno
            else:
                os.close(escaped)
                raise AssertionError(f"openat2 {label} was not denied")
        proc_fd = os.open("/proc", O_PATH | os.O_DIRECTORY)
        try:
            try:
                magic = _sys_openat2(
                    proc_fd,
                    "self/fd/0",
                    resolve=RESOLVE_NO_MAGICLINKS,
                )
            except OSError as exc:
                if exc.errno != errno.ELOOP:
                    raise
                magiclink_only_denied = True
            else:
                os.close(magic)
                raise AssertionError("openat2 real procfs magic link was not denied")
        finally:
            os.close(proc_fd)
        return {
            "positive": positive,
            "denied": denied,
            "magiclink_only_denied": magiclink_only_denied,
        }
    finally:
        os.close(root_fd)
        _umount(boundary / "mounted")


def _probe_tmpfs_quotas(root: Path) -> dict[str, object]:
    byte_root = root / "tmpfs-bytes"
    inode_root = root / "tmpfs-inodes"
    byte_root.mkdir()
    inode_root.mkdir()
    byte_enospc = False
    inode_enospc = False
    try:
        _mount("tmpfs", byte_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=65536,nr_inodes=1024")
        try:
            fd = os.open(byte_root / "payload", os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                for _ in range(256):
                    try:
                        os.write(fd, b"x" * 4096)
                    except OSError as exc:
                        if exc.errno != errno.ENOSPC:
                            raise
                        byte_enospc = True
                        break
            finally:
                os.close(fd)
        finally:
            _umount(byte_root)

        _mount("tmpfs", inode_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=1048576,nr_inodes=16")
        try:
            for index in range(128):
                try:
                    fd = os.open(inode_root / f"f-{index}", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except OSError as exc:
                    if exc.errno != errno.ENOSPC:
                        raise
                    inode_enospc = True
                    break
                else:
                    os.close(fd)
        finally:
            _umount(inode_root)
    finally:
        shutil.rmtree(byte_root, ignore_errors=True)
        shutil.rmtree(inode_root, ignore_errors=True)
    return {"byte_enospc": byte_enospc, "inode_enospc": inode_enospc}


def _interface_flags(interface: str) -> int:
    encoded = interface.encode("ascii")
    if not encoded or len(encoded) >= 16:
        raise AssertionError(f"invalid interface name: {interface!r}")
    request = bytearray(40)
    request[: len(encoded)] = encoded
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as control:
        fcntl.ioctl(control.fileno(), SIOCGIFFLAGS, request, True)
    return int(struct.unpack_from("H", request, 16)[0])


def _loopback_operstate() -> dict[str, object]:
    try:
        value = Path("/sys/class/net/lo/operstate").read_text(
            encoding="ascii"
        ).strip()
    except (OSError, UnicodeError) as exc:
        return {
            "unavailable": True,
            "error_type": type(exc).__name__[:128],
        }
    return {"value": value[:128]}


def _probe_loopback_control() -> dict[str, object]:
    ip = Path("/usr/sbin/ip")
    if not ip.is_file():
        ip = Path("/usr/bin/ip")
    if not ip.is_file():
        raise AssertionError("iproute2 ip command unavailable")
    server: socket.socket | None = None
    client: socket.socket | None = None
    accepted: socket.socket | None = None
    denial_probe: socket.socket | None = None
    inherited_fd = -1
    try:
        subprocess.run(
            [str(ip), "link", "set", "lo", "up"], check=True, timeout=5
        )
        flags_after_up = _interface_flags("lo")
        operstate_after_up = _loopback_operstate()
        admin_up_observed = bool(flags_after_up & IFF_UP)
        if not admin_up_observed:
            raise AssertionError(
                f"IFF_UP absent after administrative up: flags={flags_after_up:#x}"
            )

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        endpoint = server.getsockname()
        client.connect(endpoint)
        accepted, _ = server.accept()
        client.sendall(b"p")
        positive = accepted.recv(1) == b"p"
        if not positive:
            raise AssertionError("live loopback endpoint positive control failed")
        inherited_fd = os.dup(client.fileno())
        os.set_inheritable(inherited_fd, True)
        if os.get_inheritable(inherited_fd) is not True:
            raise AssertionError(
                "inherited network FD positive control is not inheritable"
            )
        accepted.close()
        accepted = None
        client.close()
        client = None

        subprocess.run(
            [str(ip), "link", "set", "lo", "down"], check=True, timeout=5
        )
        flags_after_down = _interface_flags("lo")
        operstate_after_down = _loopback_operstate()
        admin_down_observed = not bool(flags_after_down & IFF_UP)
        if not admin_down_observed:
            raise AssertionError(
                f"IFF_UP remained after administrative down: flags={flags_after_down:#x}"
            )

        listener_active = (
            server.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
        )
        if not listener_active:
            raise AssertionError("negative-control endpoint stopped listening")
        denial_probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        denial_probe.settimeout(0.5)
        denial_observed = False
        denial_errno: int | None = None
        denial_exception_type: str | None = None
        try:
            denial_probe.connect(endpoint)
        except OSError as exc:
            denial_observed = True
            denial_errno = exc.errno
            denial_exception_type = type(exc).__name__
        else:
            raise AssertionError(
                "connection to the still-listening loopback endpoint succeeded "
                "after IFF_UP was cleared"
            )

        return {
            "admin_state_source": "SIOCGIFFLAGS/IFF_UP",
            "admin_up_observed": admin_up_observed,
            "admin_down_observed": admin_down_observed,
            "flags_after_up": flags_after_up,
            "flags_after_down": flags_after_down,
            "operstate_after_up": operstate_after_up,
            "operstate_after_down": operstate_after_down,
            "listener_endpoint": {"address": endpoint[0], "port": endpoint[1]},
            "listener_active_during_denial": listener_active,
            "positive_control": positive,
            "connectivity_denied": denial_observed,
            "denial_exception_type": denial_exception_type,
            "denial_errno": denial_errno,
            "inherited_fd": inherited_fd,
        }
    except BaseException:
        if inherited_fd >= 0:
            os.close(inherited_fd)
        raise
    finally:
        if denial_probe is not None:
            denial_probe.close()
        if accepted is not None:
            accepted.close()
        if client is not None:
            client.close()
        if server is not None:
            server.close()
        subprocess.run(
            [str(ip), "link", "set", "lo", "down"], check=True, timeout=5
        )


def _make_detached_descendant() -> dict[str, object]:
    read_fd, write_fd = os.pipe()
    first = os.fork()
    if first == 0:
        os.close(read_fd)
        os.setsid()
        second = os.fork()
        if second == 0:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            cgroup_membership = Path("/proc/self/cgroup").read_text(encoding="utf-8").strip()
            os.write(
                write_fd,
                json.dumps(
                    {
                        "namespace_pid": os.getpid(),
                        "cgroup_membership": cgroup_membership,
                    },
                    sort_keys=True,
                ).encode("utf-8"),
            )
            os.close(write_fd)
            while True:
                signal.pause()
        os._exit(0)
    os.close(write_fd)
    os.waitpid(first, 0)
    value = os.read(read_fd, 4096)
    os.close(read_fd)
    return json.loads(value)


def _inside_namespace(execution_id: str, temp_root: Path, report_fd: int, parent_ns_json: str) -> None:
    stage_order = INSIDE_STAGE_ORDER
    failures: list[str] = []
    result: dict[str, object] = {"execution_id": execution_id}
    stage_results: dict[str, dict[str, object]] = {}
    active_stage = stage_order[0]
    open_fds: list[int] = []
    try:
        active_stage = "namespace_set"
        current_ns = _namespace_links()
        parent_ns = json.loads(parent_ns_json)
        result["namespace_ids"] = current_ns
        result["namespaces_distinct"] = all(
            current_ns[name] != parent_ns[name] for name in current_ns
        )
        if result["namespaces_distinct"] is not True:
            raise AssertionError("one or more namespace identities did not change")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "private_propagation"
        _mount(None, "/", None, MS_REC | MS_PRIVATE)
        root_mount_line = next(
            line for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
            if line.split()[4] == "/"
        )
        optional = root_mount_line.split(" - ", 1)[0].split()[6:]
        result["private_mount_propagation"] = not any(
            field.startswith(("shared:", "master:", "propagate_from:"))
            for field in optional
        )
        if result["private_mount_propagation"] is not True:
            raise AssertionError("mount propagation remained shared or dependent")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "openat2"
        result["openat2"] = _probe_openat2(temp_root)
        if not (
            result["openat2"].get("positive") is True
            and set(result["openat2"].get("denied", {}))
            == {"traversal", "symlink", "xdev"}
            and result["openat2"].get("magiclink_only_denied") is True
        ):
            raise AssertionError(f"openat2 evidence incomplete: {result['openat2']}")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "quotas"
        result["tmpfs_quota"] = _probe_tmpfs_quotas(temp_root)
        if result["tmpfs_quota"] != {
            "byte_enospc": True,
            "inode_enospc": True,
        }:
            raise AssertionError(f"tmpfs quota evidence incomplete: {result['tmpfs_quota']}")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "network"
        network = _probe_loopback_control()
        inherited_fd = int(network.pop("inherited_fd"))
        open_fds.append(inherited_fd)
        result["network"] = network
        if not (
            network.get("admin_state_source") == "SIOCGIFFLAGS/IFF_UP"
            and network.get("admin_up_observed") is True
            and network.get("admin_down_observed") is True
            and network.get("listener_active_during_denial") is True
            and network.get("positive_control") is True
            and network.get("connectivity_denied") is True
            and isinstance(network.get("denial_exception_type"), str)
        ):
            raise AssertionError(f"loopback control evidence incomplete: {network}")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "filesystem_setup"
        compiled = _compile_fixture(temp_root)
        new_root = temp_root / "private-root"
        new_root.mkdir()
        _mount("tmpfs", new_root, "tmpfs", MS_NOSUID | MS_NODEV, "size=8388608,nr_inodes=512,mode=0755")
        for directory in ("usr", "proc", "fixtures", "scratch", "old-root"):
            (new_root / directory).mkdir()
        _mount("/usr", new_root / "usr", None, MS_BIND | MS_REC)
        _mount(None, new_root / "usr", None, MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV)
        for name, target in (("bin", "usr/bin"), ("lib", "usr/lib"), ("lib64", "usr/lib64"), ("sbin", "usr/sbin")):
            (new_root / name).symlink_to(target)
        _mount("tmpfs", new_root / "scratch", "tmpfs", MS_NOSUID | MS_NODEV, "size=1048576,nr_inodes=64,mode=0700")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "path_swap"
        selected = new_root / "fixtures" / "selected-elf"
        shutil.copy2(compiled, selected)
        selected.chmod(0o755)
        sealed_fd = os.open(selected, os.O_RDONLY)
        open_fds.append(sealed_fd)
        selected_identity = _identity(sealed_fd)
        selected.unlink()
        shutil.copy2("/usr/bin/false", selected)
        selected.chmod(0o755)
        result["path_swap_digest_differs"] = (
            hashlib.sha256(selected.read_bytes()).hexdigest()
            != selected_identity["sha256"]
        )
        if result["path_swap_digest_differs"] is not True:
            raise AssertionError("replacement path did not differ from the sealed ELF")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "interpreter_seal"
        script_path = new_root / "fixtures" / "sealed-script"
        script_path.write_text("#!/bin/sh\nprintf 'SCRIPT_INTERPRETER_OK\\n'\n", encoding="utf-8")
        script_path.chmod(0o555)
        script_fd = os.open(script_path, os.O_RDONLY)
        open_fds.append(script_fd)
        script_identity = _identity(script_fd)
        if not os.read(script_fd, 10).startswith(b"#!/bin/sh"):
            raise AssertionError("synthetic shebang parse failed")
        os.lseek(script_fd, 0, os.SEEK_SET)
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "pivot_root"
        _mount(str(new_root / "fixtures"), new_root / "fixtures", None, MS_BIND)
        _mount(None, new_root / "fixtures", None, MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV)

        host_root_device = os.stat("/").st_dev
        if libc.syscall(SYS_PIVOT_ROOT_X86_64, os.fsencode(new_root), os.fsencode(new_root / "old-root")) != 0:
            _raise_errno("pivot_root")
        os.chdir("/")
        _umount("/old-root", MNT_DETACH)
        Path("/old-root").rmdir()
        _mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV, None)
        result["pivot_root_old_root_hidden"] = not Path(str(temp_root / "host-sentinel")).exists()
        result["private_root_device"] = os.stat("/").st_dev
        result["private_root_device_differs"] = (
            result["private_root_device"] != host_root_device
        )
        result["scratch_quota_mount"] = Path("/scratch").is_dir()
        result["scratch_mount_device_differs"] = (
            os.stat("/scratch").st_dev != result["private_root_device"]
        )
        if not (
            result["pivot_root_old_root_hidden"] is True
            and result["private_root_device_differs"] is True
            and result["scratch_quota_mount"] is True
            and result["scratch_mount_device_differs"] is True
        ):
            raise AssertionError("pivot_root boundary evidence incomplete")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "native_exec"
        native_loader = _read_pt_interp(sealed_fd)
        loader_fd = os.open(native_loader, os.O_RDONLY)
        open_fds.append(loader_fd)
        loader_identity = _identity(loader_fd)
        loader_stat = os.fstat(loader_fd)
        result["native"] = _ptraced_exec(
            sealed_fd,
            ["/fixtures/selected-elf"],
            {"PATH": "/usr/bin", "LANG": "C"},
            loader_stat,
            inherited_fd,
        )
        native = result["native"]
        if not (
            native.get("event") == PTRACE_EVENT_EXEC
            and native.get("exe_identity_match") is True
            and native.get("loader_identity_match") is True
            and native.get("uid_non_root") is True
            and native.get("gid_non_root") is True
            and native.get("cap_eff_zero") is True
            and native.get("no_new_privs") is True
            and native.get("inherited_network_fd_absent_at_exec") is True
            and native.get("exit_code") == 0
        ):
            raise AssertionError(f"native exec evidence incomplete: {native}")
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "interpreter_exec"
        interpreter_fd = os.open("/bin/sh", os.O_RDONLY)
        open_fds.append(interpreter_fd)
        interpreter_identity = _identity(interpreter_fd)
        interpreter_loader = _read_pt_interp(interpreter_fd)
        interpreter_loader_fd = os.open(interpreter_loader, os.O_RDONLY)
        open_fds.append(interpreter_loader_fd)
        interpreter_observation = _ptraced_exec(
            interpreter_fd,
            ["/bin/sh", "/fixtures/sealed-script"],
            {"PATH": "/usr/bin", "LANG": "C"},
            os.fstat(interpreter_loader_fd),
            inherited_fd,
        )
        interpreter_observation["script_identity_match"] = (
            os.fstat(script_fd).st_dev == os.stat("/fixtures/sealed-script").st_dev
            and os.fstat(script_fd).st_ino == os.stat("/fixtures/sealed-script").st_ino
            and _sha256_fd(script_fd) == script_identity["sha256"]
        )
        result["interpreter"] = interpreter_observation
        if not (
            interpreter_observation.get("event") == PTRACE_EVENT_EXEC
            and interpreter_observation.get("exe_identity_match") is True
            and interpreter_observation.get("loader_identity_match") is True
            and interpreter_observation.get("script_identity_match") is True
            and interpreter_observation.get("uid_non_root") is True
            and interpreter_observation.get("gid_non_root") is True
            and interpreter_observation.get("cap_eff_zero") is True
            and interpreter_observation.get("no_new_privs") is True
            and interpreter_observation.get(
                "inherited_network_fd_absent_at_exec"
            )
            is True
            and interpreter_observation.get("exit_code") == 0
        ):
            raise AssertionError(
                f"interpreter exec evidence incomplete: {interpreter_observation}"
            )
        network["native_inherited_network_fd_absent_at_exec"] = (
            native.get("inherited_network_fd_absent_at_exec") is True
        )
        network["interpreter_inherited_network_fd_absent_at_exec"] = (
            interpreter_observation.get(
                "inherited_network_fd_absent_at_exec"
            )
            is True
        )
        network["inherited_network_fd_absent_at_exec"] = (
            network["native_inherited_network_fd_absent_at_exec"] is True
            and network["interpreter_inherited_network_fd_absent_at_exec"]
            is True
        )
        network["inherited_fd_closed_and_socket_denied"] = (
            network["inherited_network_fd_absent_at_exec"] is True
            and native.get("exit_code") == 0
            and interpreter_observation.get("exit_code") == 0
        )
        result["sealed_identities"] = {
            "native": selected_identity,
            "script": script_identity,
            "interpreter": interpreter_identity,
            "loader": loader_identity,
        }
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "process_tree_fixture"
        result["detached_descendant"] = _make_detached_descendant()
        if not (
            isinstance(result["detached_descendant"], dict)
            and int(result["detached_descendant"].get("namespace_pid", 0)) > 0
            and str(result["detached_descendant"].get("cgroup_membership", ""))
        ):
            raise AssertionError("detached descendant fixture evidence incomplete")
        stage_results[active_stage] = {"status": STAGE_PASS}
        result["ready"] = True
    except BaseException as exc:
        failure = repr(exc)
        failures.append(f"{active_stage}: {failure}")
        stage_results[active_stage] = {
            "status": STAGE_FAIL,
            "failure": failure,
        }
        _mark_not_reached(stage_results, stage_order, f"inside.{active_stage}")
    result["stage_results"] = stage_results
    result["failures"] = failures
    payload = json.dumps(result, sort_keys=True).encode("utf-8")
    os.write(report_fd, payload)
    os.fsync(report_fd)
    os.close(report_fd)
    for fd in open_fds:
        try:
            os.close(fd)
        except OSError:
            pass
    while True:
        signal.pause()


def _spawn_gated(
    argv: list[str],
    cgroup: Path,
    *,
    stdout,
    stderr,
    extra_fds: tuple[int, ...] = (),
) -> tuple[subprocess.Popen[bytes], int]:
    if not (cgroup / "cgroup.kill").is_file() or not (cgroup / "cgroup.events").is_file():
        raise AssertionError("cgroup kill/events capability missing before workload gate")
    if _cgroup_populated(cgroup) != 0:
        raise AssertionError("new cgroup was populated before workload gate")
    read_gate, write_gate = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "--gate-exec",
            str(read_gate),
            json.dumps(argv),
        ],
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        close_fds=True,
        pass_fds=(read_gate, *extra_fds),
    )
    os.close(read_gate)
    try:
        (cgroup / "cgroup.procs").write_text(str(process.pid), encoding="ascii")
        pidfd = os.pidfd_open(process.pid)
        os.write(write_gate, b"g")
        return process, pidfd
    except BaseException:
        os.close(write_gate)
        process.kill()
        process.wait(timeout=2)
        raise
    finally:
        try:
            os.close(write_gate)
        except OSError:
            pass


def _drain_until_limit(
    process: subprocess.Popen[bytes],
    deadline: float,
    *,
    per_stream_limit: int = PER_STREAM_LIMIT,
    combined_stream_limit: int = COMBINED_STREAM_LIMIT,
    retained_combined_limit: int = COMBINED_STREAM_LIMIT,
) -> dict[str, object]:
    selector = selectors.DefaultSelector()
    emitted = {"stdout": 0, "stderr": 0}
    retained = {"stdout": bytearray(), "stderr": bytearray()}
    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        if stream is None:
            raise AssertionError(f"missing {name} pipe")
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)
    trigger = None
    while selector.get_map() and time.monotonic() < deadline:
        for key, _ in selector.select(timeout=POLL_INTERVAL_SECONDS):
            chunk = os.read(key.fileobj.fileno(), 4096)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            name = key.data
            emitted[name] += len(chunk)
            stream_room = max(0, per_stream_limit - len(retained[name]))
            combined_room = max(
                0,
                retained_combined_limit
                - sum(len(value) for value in retained.values()),
            )
            keep = min(len(chunk), stream_room, combined_room)
            retained[name].extend(chunk[:keep])
            if emitted[name] > per_stream_limit:
                trigger = f"{name}_raw_stream_limit"
                break
            if sum(emitted.values()) > combined_stream_limit:
                trigger = "combined_raw_stream_limit"
                break
        if trigger:
            break
    selector.close()
    return {
        "trigger": trigger,
        "emitted": emitted,
        "retained": {key: len(value) for key, value in retained.items()},
        "discarded": {
            key: emitted[key] - len(retained[key]) for key in emitted
        },
    }


def _scan_for_residue(temp_root: Path, namespace_links: dict[str, str]) -> list[str]:
    findings: list[str] = []
    target = str(temp_root)
    namespace_values = set(namespace_links.values())
    for proc in Path("/proc").glob("[0-9]*"):
        for name in ("cwd", "root"):
            try:
                link = os.readlink(proc / name)
            except OSError:
                continue
            if link.startswith(target):
                findings.append(f"{proc.name}/{name}->{link}")
        for directory in ("fd", "ns"):
            try:
                entries = list((proc / directory).iterdir())
            except OSError:
                continue
            for entry in entries:
                try:
                    link = os.readlink(entry)
                except OSError:
                    continue
                if link.startswith(target) or link in namespace_values:
                    findings.append(f"{proc.name}/{directory}/{entry.name}->{link}")
    return findings[:32]


def _host_mounts_under(temp_root: Path) -> list[Path]:
    prefix = str(temp_root.resolve()) + "/"
    mounts: list[Path] = []
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        mount_point = line.split()[4].replace("\\040", " ")
        if mount_point == str(temp_root) or mount_point.startswith(prefix):
            mounts.append(Path(mount_point))
    return sorted(mounts, key=lambda value: len(value.parts), reverse=True)


def _unmount_then_remove_temp_root(temp_root: Path, failures: list[str]) -> None:
    for mount_point in _host_mounts_under(temp_root):
        try:
            _umount(mount_point, MNT_DETACH)
        except BaseException as exc:
            failures.append(f"host mount cleanup {mount_point}: {exc!r}")
    remaining = _host_mounts_under(temp_root)
    if remaining:
        failures.append(f"host mounts remain; recursive deletion suppressed: {remaining}")
        return
    if temp_root.exists():
        try:
            shutil.rmtree(temp_root, ignore_errors=False)
        except BaseException as exc:
            failures.append(f"temporary-root removal: {exc!r}")


def _run_timeout_probe(execution_id: str, path: Path) -> dict[str, object]:
    failures: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    pidfd = -1
    started = time.monotonic()
    try:
        if not path.is_dir() or _cgroup_populated(path) != 0:
            raise AssertionError("timeout cgroup is absent or populated before probe")
        process, pidfd = _spawn_gated(
            ["/usr/bin/sleep", "30"], path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        deadline = started + 0.35
        _wait_until(lambda: time.monotonic() >= deadline, deadline + 0.2, "monotonic timeout")
        alive_before_kill = process.poll() is None
        populated_before_kill = _cgroup_populated(path)
        if not alive_before_kill or populated_before_kill != 1:
            raise AssertionError(
                "timeout fixture was not live at the monotonic deadline"
            )
        (path / "cgroup.kill").write_text("1", encoding="ascii")
        poller = selectors.DefaultSelector()
        poller.register(pidfd, selectors.EVENT_READ)
        readable = bool(poller.select(timeout=2))
        poller.close()
        process.wait(timeout=2)
        _wait_until(lambda: _cgroup_populated(path) == 0, time.monotonic() + 5, "timeout cgroup empty")
        result = {
            "trigger": "monotonic_timeout",
            "elapsed_seconds": time.monotonic() - started,
            "alive_before_kill": alive_before_kill,
            "populated_before_kill": populated_before_kill,
            "cgroup_kill_written": True,
            "pidfd_exit_observed": readable,
            "process_exited_after_kill": process.poll() is not None,
            "returncode": process.returncode,
            "populated_zero": _cgroup_populated(path) == 0,
        }
        if not (
            result["pidfd_exit_observed"] is True
            and result["process_exited_after_kill"] is True
            and result["returncode"] == -signal.SIGKILL
            and result["populated_zero"] is True
        ):
            raise AssertionError(f"timeout kill evidence incomplete: {result}")
        return result
    finally:
        if process is not None and process.poll() is None:
            try:
                (path / "cgroup.kill").write_text("1", encoding="ascii")
                _wait_until(
                    lambda: _cgroup_populated(path) == 0,
                    time.monotonic() + 5,
                    "timeout failure cleanup",
                )
                process.wait(timeout=2)
            except BaseException as exc:
                failures.append(f"timeout process cleanup: {exc!r}")
        if pidfd >= 0:
            os.close(pidfd)
        if failures:
            raise AssertionError(failures)


def _run_stream_limit_probe(path: Path, mode: str) -> dict[str, object]:
    if mode not in {"stdout", "stderr", "combined"}:
        raise AssertionError(f"unknown stream probe mode: {mode}")
    failures: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    pidfd = -1
    try:
        if not path.is_dir() or _cgroup_populated(path) != 0:
            raise AssertionError(
                f"{mode} stream cgroup is absent or populated before probe"
            )
        if mode == "stdout":
            writer = (
                f"for _ in range({SINGLE_STREAM_WRITE_COUNT}): "
                "os.write(1, b'O' * 4096)\n"
                "while True: signal.pause()"
            )
        elif mode == "stderr":
            writer = (
                f"for _ in range({SINGLE_STREAM_WRITE_COUNT}): "
                "os.write(2, b'E' * 4096)\n"
                "while True: signal.pause()"
            )
        else:
            writer = (
                f"for _ in range({COMBINED_STREAM_WRITE_COUNT}):\n"
                " os.write(1, b'O' * 4096)\n"
                " os.write(2, b'E' * 4096)\n"
                "while True: signal.pause()"
            )
        command = [
            sys.executable,
            "-I",
            "-c",
            "import os, signal\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            + writer,
        ]
        process, pidfd = _spawn_gated(
            command,
            path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        expected_trigger = (
            "combined_raw_stream_limit"
            if mode == "combined"
            else f"{mode}_raw_stream_limit"
        )
        result = _drain_until_limit(
            process,
            time.monotonic() + 8,
            per_stream_limit=(
                PER_STREAM_LIMIT * 4 if mode == "combined" else PER_STREAM_LIMIT
            ),
            combined_stream_limit=(
                COMBINED_STREAM_LIMIT
                if mode == "combined"
                else PER_STREAM_LIMIT * 4
            ),
        )
        if result.get("trigger") != expected_trigger:
            raise AssertionError(
                f"{mode} stream limit did not trigger: {result}"
            )

        result["mode"] = mode
        result["theoretical_emitted_bytes"] = (
            COMBINED_STREAM_WRITE_COUNT * 8192
            if mode == "combined"
            else SINGLE_STREAM_WRITE_COUNT * 4096
        )
        if result["theoretical_emitted_bytes"] > SYNTHETIC_STREAM_BYTE_BUDGET:
            raise AssertionError("synthetic stream fixture exceeds byte budget")
        result["alive_before_kill"] = process.poll() is None
        result["populated_before_kill"] = _cgroup_populated(path)
        if (
            result["alive_before_kill"] is not True
            or result["populated_before_kill"] != 1
        ):
            raise AssertionError(
                f"{mode} stream fixture was not live before kill: {result}"
            )
        process.send_signal(signal.SIGTERM)
        time.sleep(0.05)
        result["term_ignored_before_kill"] = (
            process.poll() is None and _cgroup_populated(path) == 1
        )
        if result["term_ignored_before_kill"] is not True:
            raise AssertionError(
                f"{mode} stream fixture did not ignore TERM: {result}"
            )

        (path / "cgroup.kill").write_text("1", encoding="ascii")
        result["cgroup_kill_written"] = True
        poller = selectors.DefaultSelector()
        poller.register(pidfd, selectors.EVENT_READ)
        result["pidfd_exit_observed"] = bool(poller.select(timeout=2))
        poller.close()
        remaining_stdout, remaining_stderr = process.communicate(timeout=3)
        _wait_until(
            lambda: _cgroup_populated(path) == 0,
            time.monotonic() + 5,
            f"{mode} stream cgroup empty",
        )
        for name, remaining in (("stdout", remaining_stdout), ("stderr", remaining_stderr)):
            result["emitted"][name] += len(remaining)
            result["discarded"][name] += len(remaining)
        result["process_exited_after_kill"] = process.poll() is not None
        result["returncode"] = process.returncode
        result["populated_zero"] = _cgroup_populated(path) == 0
        result["accounting_complete"] = all(
            result["discarded"][name]
            == result["emitted"][name] - result["retained"][name]
            for name in ("stdout", "stderr")
        )
        retained_limit = (
            COMBINED_STREAM_LIMIT if mode == "combined" else PER_STREAM_LIMIT
        )
        result["retained_within_limit"] = (
            sum(result["retained"].values()) <= retained_limit
        )
        if not (
            result["pidfd_exit_observed"] is True
            and result["process_exited_after_kill"] is True
            and result["returncode"] == -signal.SIGKILL
            and result["populated_zero"] is True
            and result["accounting_complete"] is True
            and result["retained_within_limit"] is True
        ):
            raise AssertionError(
                f"{mode} stream kill/accounting evidence incomplete: {result}"
            )
        if not _stream_probe_evidence_complete(result, mode):
            raise AssertionError(
                f"{mode} stream exact evidence predicate failed: {result}"
            )
        return result
    finally:
        if process is not None and process.poll() is None:
            try:
                (path / "cgroup.kill").write_text("1", encoding="ascii")
                _wait_until(
                    lambda: _cgroup_populated(path) == 0,
                    time.monotonic() + 5,
                    f"{mode} stream failure cleanup",
                )
                process.wait(timeout=2)
            except BaseException as exc:
                failures.append(f"{mode} stream process cleanup: {exc!r}")
        if pidfd >= 0:
            os.close(pidfd)
        if failures:
            raise AssertionError(failures)


def _stream_probe_evidence_complete(observation: object, mode: str) -> bool:
    if not isinstance(observation, dict):
        return False
    emitted = observation.get("emitted")
    retained = observation.get("retained")
    discarded = observation.get("discarded")
    if not all(isinstance(value, dict) for value in (emitted, retained, discarded)):
        return False
    expected_trigger = (
        "combined_raw_stream_limit"
        if mode == "combined"
        else f"{mode}_raw_stream_limit"
    )
    try:
        accounting_complete = all(
            discarded[name] == emitted[name] - retained[name]
            for name in ("stdout", "stderr")
        )
        common = (
            observation.get("mode") == mode
            and observation.get("trigger") == expected_trigger
            and observation.get("alive_before_kill") is True
            and observation.get("populated_before_kill") == 1
            and observation.get("term_ignored_before_kill") is True
            and observation.get("cgroup_kill_written") is True
            and observation.get("pidfd_exit_observed") is True
            and observation.get("process_exited_after_kill") is True
            and observation.get("returncode") == -signal.SIGKILL
            and observation.get("populated_zero") is True
            and observation.get("accounting_complete") is True
            and observation.get("retained_within_limit") is True
            and 0 < observation.get("theoretical_emitted_bytes", 0)
            <= SYNTHETIC_STREAM_BYTE_BUDGET
            and accounting_complete
        )
        if not common:
            return False
        if mode in {"stdout", "stderr"}:
            other = "stderr" if mode == "stdout" else "stdout"
            return bool(
                emitted[mode] > PER_STREAM_LIMIT
                and retained[mode] <= PER_STREAM_LIMIT
                and discarded[mode] > 0
                and emitted[other] == 0
                and retained[other] == 0
                and discarded[other] == 0
                and sum(retained.values()) <= PER_STREAM_LIMIT
            )
        return bool(
            sum(emitted.values()) > COMBINED_STREAM_LIMIT
            and all(emitted[name] > 0 for name in ("stdout", "stderr"))
            and sum(retained.values()) <= COMBINED_STREAM_LIMIT
            and sum(discarded.values()) > 0
        )
    except (KeyError, TypeError, ValueError):
        return False


def _run_composition_domain(
    execution_id: str,
    temp_root: Path,
    source_file: Path,
    composition_cgroup: Path,
    marker: Path,
    journal: dict[str, object],
) -> dict[str, object]:
    composition_stages = (
        "composition_setup",
        "inside_report",
        "live_host_mount_observation",
        "process_tree",
        "cgroup_kill",
        "pidfd_exit_observation",
    )
    stage_results: dict[str, dict[str, object]] = {}
    failures: list[str] = []
    cleanup_failures: list[str] = []
    report: dict[str, object] = {}
    validated_inside_stages: dict[str, dict[str, object]] | None = None
    process_tree_evidence: dict[str, object] = {}
    process: subprocess.Popen[bytes] | None = None
    process_pidfd = -1
    member_pidfds: list[int] = []
    report_fd = -1
    claimed = False
    active_stage = composition_stages[0]
    parent_ns = _namespace_links()
    report_path = temp_root / "inside-report.json"
    try:
        active_stage = "composition_setup"
        _claim_cgroup(composition_cgroup, marker, journal)
        claimed = True
        report_fd = os.open(
            report_path,
            os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        os.set_inheritable(report_fd, True)
        command = [
            "/usr/bin/unshare",
            "--mount",
            "--pid",
            "--net",
            "--ipc",
            "--uts",
            "--fork",
            "--kill-child=KILL",
            str(sys.executable),
            "-I",
            str(source_file),
            "--inside-namespace",
            execution_id,
            str(temp_root),
            str(report_fd),
            json.dumps(parent_ns, sort_keys=True),
        ]
        process, process_pidfd = _spawn_gated(
            command,
            composition_cgroup,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            extra_fds=(report_fd,),
        )
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "inside_report"

        def report_is_complete() -> bool:
            try:
                json.loads(report_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
                return False
            return True

        _wait_until(
            report_is_complete,
            time.monotonic() + 35,
            "inside compositional report",
        )
        parsed_report = json.loads(report_path.read_text(encoding="utf-8"))
        validated_inside_stages = _validate_inside_stage_schema(parsed_report)
        report = parsed_report
        stage_results[active_stage] = {"status": STAGE_PASS}

        active_stage = "live_host_mount_observation"
        live_host_mounts = [
            str(path) for path in _host_mounts_under(temp_root)
        ]
        process_tree_evidence["host_mounts_during_live_namespace"] = (
            live_host_mounts
        )
        process_tree_evidence["namespace_alive_during_host_mount_observation"] = (
            process.poll() is None
        )
        if live_host_mounts:
            raise AssertionError(
                "private namespace mount leaked into host mountinfo while live: "
                f"{live_host_mounts}"
            )
        if process.poll() is not None:
            raise AssertionError(
                "namespace exited before live host mount observation completed"
            )
        stage_results[active_stage] = {"status": STAGE_PASS}
        if report.get("failures"):
            failures.extend(
                f"inside direct failure: {item}" for item in report["failures"]
            )
        inside_blocker = _first_blocking_stage(validated_inside_stages)
        if inside_blocker is not None:
            _mark_subset_not_reached(
                stage_results,
                ("process_tree", "cgroup_kill", "pidfd_exit_observation"),
                inside_blocker,
            )
        else:
            if report.get("ready") is not True:
                raise AssertionError("inside report omitted the ready evidence")

            active_stage = "process_tree"
            descendant = report.get("detached_descendant")
            if not isinstance(descendant, dict):
                raise AssertionError("detached descendant identity observation missing")
            expected_cgroup_suffix = f"/{execution_id}/composition"
            if not str(descendant.get("cgroup_membership", "")).endswith(
                expected_cgroup_suffix
            ):
                raise AssertionError(
                    f"detached descendant escaped cgroup: {descendant}"
                )
            namespace_pid = int(descendant.get("namespace_pid", 0))
            host_descendants: list[dict[str, int]] = []
            for candidate in Path("/proc").glob("[0-9]*"):
                try:
                    candidate_pid = int(candidate.name)
                    status_rows = _status_at_exec(candidate_pid)
                    nspid = [int(item) for item in status_rows["NSpid"].split()]
                    cgroup_rows = (candidate / "cgroup").read_text(encoding="utf-8")
                    candidate_starttime, _ = _proc_starttime_and_state(
                        candidate_pid
                    )
                except (OSError, KeyError, ValueError):
                    continue
                if (
                    nspid
                    and nspid[-1] == namespace_pid
                    and cgroup_rows.strip().endswith(expected_cgroup_suffix)
                ):
                    host_descendants.append(
                        {
                            "pid": candidate_pid,
                            "starttime": candidate_starttime,
                        }
                    )
            if len(host_descendants) != 1:
                raise AssertionError(
                    "detached descendant host PID mapping not unique: "
                    f"{host_descendants}"
                )
            detached_host_pid = host_descendants[0]["pid"]
            detached_starttime = host_descendants[0]["starttime"]
            try:
                detached_pidfd = os.pidfd_open(detached_host_pid)
            except ProcessLookupError as exc:
                raise AssertionError(
                    "detached descendant exited before pidfd binding"
                ) from exc
            member_pidfds.append(detached_pidfd)
            revalidated_starttime, _ = _proc_starttime_and_state(
                detached_host_pid
            )
            revalidated_status = _status_at_exec(detached_host_pid)
            revalidated_nspid = [
                int(item) for item in revalidated_status["NSpid"].split()
            ]
            revalidated_cgroup = Path(
                f"/proc/{detached_host_pid}/cgroup"
            ).read_text(encoding="utf-8")
            if not (
                revalidated_starttime == detached_starttime
                and revalidated_nspid
                and revalidated_nspid[-1] == namespace_pid
                and revalidated_cgroup.strip().endswith(
                    expected_cgroup_suffix
                )
                and detached_host_pid
                in _cgroup_process_ids(composition_cgroup)
            ):
                raise AssertionError(
                    "detached descendant identity changed after pidfd binding"
                )
            exact_members = _cgroup_process_ids(composition_cgroup)
            if detached_host_pid not in exact_members:
                raise AssertionError(
                    "exact detached descendant is not in the composition cgroup"
                )
            if len(exact_members) < 3:
                raise AssertionError(
                    f"complete process tree positive control too small: {exact_members}"
                )
            bound_member_starttimes: dict[int, int] = {}
            for pid in sorted(exact_members):
                member_pidfd = -1
                try:
                    before_starttime, _ = _proc_starttime_and_state(pid)
                    if pid == detached_host_pid:
                        member_pidfd = detached_pidfd
                    else:
                        member_pidfd = os.pidfd_open(pid)
                    after_starttime, _ = _proc_starttime_and_state(pid)
                    member_cgroup = Path(f"/proc/{pid}/cgroup").read_text(
                        encoding="utf-8"
                    )
                except (OSError, KeyError, ValueError) as exc:
                    if pid != detached_host_pid and member_pidfd >= 0:
                        os.close(member_pidfd)
                    raise AssertionError(
                        f"pidfd identity binding lost for cgroup process {pid}: {exc}"
                    ) from exc
                if not (
                    before_starttime == after_starttime
                    and member_cgroup.strip().endswith(
                        expected_cgroup_suffix
                    )
                    and pid in _cgroup_process_ids(composition_cgroup)
                ):
                    if pid != detached_host_pid:
                        os.close(member_pidfd)
                    raise AssertionError(
                        f"cgroup member identity changed during pidfd bind: {pid}"
                    )
                bound_member_starttimes[pid] = after_starttime
                if pid != detached_host_pid:
                    member_pidfds.append(member_pidfd)

            signal.pidfd_send_signal(
                detached_pidfd,
                signal.SIGTERM,
            )
            term_poller = selectors.DefaultSelector()
            try:
                term_poller.register(detached_pidfd, selectors.EVENT_READ)
                detached_exited_after_term = bool(
                    term_poller.select(timeout=0.05)
                )
            finally:
                term_poller.close()
            term_starttime, _ = _proc_starttime_and_state(detached_host_pid)
            term_status = _status_at_exec(detached_host_pid)
            term_nspid = [
                int(item) for item in term_status["NSpid"].split()
            ]
            term_cgroup = Path(f"/proc/{detached_host_pid}/cgroup").read_text(
                encoding="utf-8"
            )
            if not (
                detached_exited_after_term is False
                and term_starttime == detached_starttime
                and term_nspid
                and term_nspid[-1] == namespace_pid
                and term_cgroup.strip().endswith(expected_cgroup_suffix)
                and detached_host_pid
                in _cgroup_process_ids(composition_cgroup)
            ):
                raise AssertionError(
                    "pidfd TERM-ignore detached descendant control failed"
                )

            prekill_poller = selectors.DefaultSelector()
            try:
                for fd in member_pidfds:
                    prekill_poller.register(fd, selectors.EVENT_READ)
                member_exit_before_kill = bool(
                    prekill_poller.select(timeout=0)
                )
            finally:
                prekill_poller.close()
            if member_exit_before_kill:
                raise AssertionError(
                    "one or more bound cgroup members exited before cgroup.kill"
                )
            process_tree_evidence["member_count_before_kill"] = len(exact_members)
            process_tree_evidence["detached_host_pid"] = detached_host_pid
            process_tree_evidence["detached_pidfd_bound_before_term"] = True
            process_tree_evidence["detached_identity_revalidated"] = True
            process_tree_evidence["detached_term_sent_via_pidfd"] = True
            process_tree_evidence[
                "detached_pidfd_unreadable_after_term"
            ] = True
            process_tree_evidence["all_member_pidfds_identity_bound"] = (
                len(bound_member_starttimes) == len(exact_members)
            )
            process_tree_evidence[
                "all_member_pidfds_unreadable_before_kill"
            ] = True
            stage_results[active_stage] = {"status": STAGE_PASS}

            active_stage = "cgroup_kill"
            process_tree_evidence["alive_before_kill"] = process.poll() is None
            process_tree_evidence["populated_before_kill"] = _cgroup_populated(
                composition_cgroup
            )
            if not (
                process_tree_evidence["alive_before_kill"] is True
                and process_tree_evidence["populated_before_kill"] == 1
            ):
                raise AssertionError("composition process tree was not live before kill")
            (composition_cgroup / "cgroup.kill").write_text("1", encoding="ascii")
            process_tree_evidence["cgroup_kill_written"] = True
            composition_stdout, composition_stderr = process.communicate(timeout=5)
            _wait_until(
                lambda: _cgroup_populated(composition_cgroup) == 0,
                time.monotonic() + 8,
                "composition cgroup populated=0",
            )
            process_tree_evidence["process_exited_after_kill"] = (
                process.poll() is not None
            )
            process_tree_evidence["returncode"] = process.returncode
            process_tree_evidence["populated_zero"] = (
                _cgroup_populated(composition_cgroup) == 0
            )
            process_tree_evidence["bounded_stdout_bytes"] = len(composition_stdout)
            process_tree_evidence["bounded_stderr_bytes"] = len(composition_stderr)
            if not (
                process_tree_evidence["process_exited_after_kill"] is True
                and process_tree_evidence["returncode"] == -signal.SIGKILL
                and process_tree_evidence["populated_zero"] is True
                and len(composition_stdout) == 39
                and len(composition_stderr) == 18
            ):
                raise AssertionError(
                    f"composition kill evidence incomplete: {process_tree_evidence}"
                )
            stage_results[active_stage] = {"status": STAGE_PASS}

            active_stage = "pidfd_exit_observation"
            poller = selectors.DefaultSelector()
            try:
                for fd in member_pidfds:
                    poller.register(fd, selectors.EVENT_READ)
                poller.register(process_pidfd, selectors.EVENT_READ)
                events = poller.select(timeout=2)
            finally:
                poller.close()
            if len(events) != len(member_pidfds) + 1:
                raise AssertionError(
                    "not every composition process exit was pidfd-observed"
                )
            process_tree_evidence["all_member_pidfds_readable"] = True
            process_tree_evidence["process_pidfd_readable"] = True
            stage_results[active_stage] = {"status": STAGE_PASS}
    except BaseException as exc:
        failure = repr(exc)
        failures.append(f"{active_stage}: {failure}")
        stage_results[active_stage] = {
            "status": STAGE_FAIL,
            "failure": failure,
        }
        if active_stage in composition_stages:
            index = composition_stages.index(active_stage)
            _mark_subset_not_reached(
                stage_results,
                composition_stages[index + 1 :],
                f"root.{active_stage}",
            )
    finally:
        if report_fd >= 0:
            try:
                os.close(report_fd)
            except OSError:
                pass
        if process is not None and process.poll() is None and composition_cgroup.exists():
            try:
                (composition_cgroup / "cgroup.kill").write_text("1", encoding="ascii")
                _wait_until(
                    lambda: _cgroup_populated(composition_cgroup) == 0,
                    time.monotonic() + 8,
                    "composition domain cleanup",
                )
                process.communicate(timeout=3)
            except BaseException as exc:
                cleanup_failures.append(f"composition process cleanup: {exc!r}")
        elif process is not None:
            try:
                process.communicate(timeout=3)
            except BaseException as exc:
                cleanup_failures.append(f"composition process reap: {exc!r}")
        if process_pidfd >= 0:
            os.close(process_pidfd)
        for fd in member_pidfds:
            try:
                os.close(fd)
            except OSError:
                pass
        if claimed:
            release_failures: list[str] = []
            _release_owned_cgroup(
                composition_cgroup,
                marker,
                journal,
                release_failures,
            )
            if release_failures:
                cleanup_failures.extend(release_failures)
                stage_results["composition_release"] = {
                    "status": STAGE_FAIL,
                    "failure": repr(release_failures),
                }
            elif cleanup_failures:
                stage_results["composition_release"] = {
                    "status": STAGE_FAIL,
                    "failure": repr(cleanup_failures)[-4000:],
                }
            else:
                stage_results["composition_release"] = {"status": STAGE_PASS}
        else:
            failure = "composition cgroup ownership claim was not established"
            cleanup_failures.append(failure)
            stage_results["composition_release"] = {
                "status": STAGE_FAIL,
                "failure": failure,
            }
    return {
        "stage_results": stage_results,
        "failures": failures,
        "cleanup_failures": cleanup_failures,
        "report": report,
        "inside_stage_results": validated_inside_stages,
        "process_tree_evidence": process_tree_evidence,
    }


def _root_probe(
    execution_id: str,
    temp_root: Path,
    source_file: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
    helper_identity: dict[str, object],
) -> dict[str, object]:
    if os.geteuid() != 0:
        raise AssertionError("root helper is not root")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise AssertionError("root helper requires Linux x86_64")
    if not (CGROUP_ROOT / "cgroup.controllers").is_file():
        raise AssertionError("unified cgroup v2 is unavailable")
    if not Path("/usr/bin/unshare").is_file():
        raise AssertionError("/usr/bin/unshare is unavailable")

    parent_cgroup = _safe_cgroup_path(execution_id)
    composition_cgroup = _safe_cgroup_path(execution_id, "composition")
    stream_cgroup = _safe_cgroup_path(execution_id, "combined-stream")
    timeout_cgroup = _safe_cgroup_path(execution_id, "timeout")
    exact_cgroup_paths = {
        str(parent_cgroup),
        str(composition_cgroup),
        str(stream_cgroup),
        str(timeout_cgroup),
    }
    marker, journal = _create_ownership_journal(
        execution_id,
        temp_root,
        nonce,
        creator_uid,
        parent_device,
        parent_inode,
        helper_identity,
    )
    (temp_root / "host-sentinel").write_text("host-only", encoding="utf-8")

    root_stage_results: dict[str, dict[str, object]] = {}
    probe_failures: list[str] = []
    cleanup_failures: list[str] = []
    report: dict[str, object] = {}
    inside_stage_observations: dict[str, dict[str, object]] | None = None
    streams: dict[str, object] = {}
    timeout_result: dict[str, object] = {}
    process_tree_evidence: dict[str, object] = {}
    parent_claimed = False
    cleanup_safe = True
    cleanup_blocker = "cleanup.uninitialized"

    try:
        _claim_cgroup(parent_cgroup, marker, journal)
        parent_claimed = True
        root_stage_results["parent_cgroup_setup"] = {"status": STAGE_PASS}
    except BaseException as exc:
        failure = repr(exc)
        probe_failures.append(f"parent_cgroup_setup: {failure}")
        root_stage_results["parent_cgroup_setup"] = {
            "status": STAGE_FAIL,
            "failure": failure,
        }
        _mark_subset_not_reached(
            root_stage_results,
            tuple(
                stage
                for stage in ROOT_STAGE_ORDER
                if stage not in {"parent_cgroup_setup", "parent_cgroup_release"}
            ),
            "root.parent_cgroup_setup",
        )
        cleanup_safe = False
        cleanup_blocker = "root.parent_cgroup_setup"

    if parent_claimed:
        composition = _run_composition_domain(
            execution_id,
            temp_root,
            source_file,
            composition_cgroup,
            marker,
            journal,
        )
        root_stage_results.update(composition["stage_results"])
        probe_failures.extend(composition["failures"])
        cleanup_failures.extend(composition["cleanup_failures"])
        report = composition["report"]
        inside_stage_observations = composition["inside_stage_results"]
        process_tree_evidence = composition["process_tree_evidence"]
        if composition["cleanup_failures"]:
            cleanup_safe = False
            cleanup_blocker = "root.composition_release"

        stream_claimed = False
        if cleanup_safe:
            try:
                _claim_cgroup(stream_cgroup, marker, journal)
                stream_claimed = True
                root_stage_results["stream_cgroup_setup"] = {
                    "status": STAGE_PASS
                }
            except BaseException as exc:
                failure = repr(exc)
                probe_failures.append(f"stream_cgroup_setup: {failure}")
                root_stage_results["stream_cgroup_setup"] = {
                    "status": STAGE_FAIL,
                    "failure": failure,
                }
                _mark_subset_not_reached(
                    root_stage_results,
                    (
                        "stdout_stream_limit",
                        "stdout_stream_safety",
                        "stderr_stream_limit",
                        "stderr_stream_safety",
                        "combined_stream_limit",
                        "combined_stream_safety",
                        "stream_cgroup_release",
                    ),
                    "root.stream_cgroup_setup",
                )
                cleanup_safe = False
                cleanup_blocker = "root.stream_cgroup_setup"
        else:
            _mark_subset_not_reached(
                root_stage_results,
                (
                    "stream_cgroup_setup",
                    "stdout_stream_limit",
                    "stdout_stream_safety",
                    "stderr_stream_limit",
                    "stderr_stream_safety",
                    "combined_stream_limit",
                    "combined_stream_safety",
                    "stream_cgroup_release",
                ),
                cleanup_blocker,
            )

        if stream_claimed:
            stream_sequence_safe = True
            stream_sequence_blocker = "cleanup.stream_sequence_uninitialized"
            for stage, safety_stage, key, mode in (
                (
                    "stdout_stream_limit",
                    "stdout_stream_safety",
                    "stdout_probe",
                    "stdout",
                ),
                (
                    "stderr_stream_limit",
                    "stderr_stream_safety",
                    "stderr_probe",
                    "stderr",
                ),
                (
                    "combined_stream_limit",
                    "combined_stream_safety",
                    "combined_probe",
                    "combined",
                ),
            ):
                if not stream_sequence_safe:
                    root_stage_results[stage] = {
                        "status": STAGE_NOT_REACHED,
                        "blocked_by": stream_sequence_blocker,
                    }
                    root_stage_results[safety_stage] = {
                        "status": STAGE_NOT_REACHED,
                        "blocked_by": stream_sequence_blocker,
                    }
                    continue
                try:
                    streams[key] = _run_stream_limit_probe(stream_cgroup, mode)
                    root_stage_results[stage] = {"status": STAGE_PASS}
                except BaseException as exc:
                    failure = repr(exc)
                    probe_failures.append(f"{stage}: {failure}")
                    root_stage_results[stage] = {
                        "status": STAGE_FAIL,
                        "failure": failure,
                    }
                try:
                    populated_after_probe = _cgroup_populated(stream_cgroup)
                    if populated_after_probe != 0:
                        raise AssertionError(
                            f"shared stream cgroup populated={populated_after_probe}"
                        )
                    root_stage_results[safety_stage] = {"status": STAGE_PASS}
                except BaseException as safety_exc:
                    safety_failure = repr(safety_exc)
                    probe_failures.append(
                        f"{safety_stage}: {safety_failure}"
                    )
                    root_stage_results[safety_stage] = {
                        "status": STAGE_FAIL,
                        "failure": safety_failure,
                    }
                    stream_sequence_safe = False
                    stream_sequence_blocker = f"root.{safety_stage}"
            stream_release_failures: list[str] = []
            _release_owned_cgroup(
                stream_cgroup,
                marker,
                journal,
                stream_release_failures,
            )
            if stream_release_failures:
                cleanup_failures.extend(stream_release_failures)
                root_stage_results["stream_cgroup_release"] = {
                    "status": STAGE_FAIL,
                    "failure": repr(stream_release_failures),
                }
                if cleanup_safe:
                    cleanup_blocker = "root.stream_cgroup_release"
                cleanup_safe = False
            else:
                root_stage_results["stream_cgroup_release"] = {
                    "status": STAGE_PASS
                }

        timeout_claimed = False
        if cleanup_safe:
            try:
                _claim_cgroup(timeout_cgroup, marker, journal)
                timeout_claimed = True
                root_stage_results["timeout_cgroup_setup"] = {
                    "status": STAGE_PASS
                }
            except BaseException as exc:
                failure = repr(exc)
                probe_failures.append(f"timeout_cgroup_setup: {failure}")
                root_stage_results["timeout_cgroup_setup"] = {
                    "status": STAGE_FAIL,
                    "failure": failure,
                }
                root_stage_results["timeout"] = {
                    "status": STAGE_NOT_REACHED,
                    "blocked_by": "root.timeout_cgroup_setup",
                }
                root_stage_results["timeout_cgroup_release"] = {
                    "status": STAGE_NOT_REACHED,
                    "blocked_by": "root.timeout_cgroup_setup",
                }
                cleanup_safe = False
                cleanup_blocker = "root.timeout_cgroup_setup"
        else:
            _mark_subset_not_reached(
                root_stage_results,
                (
                    "timeout_cgroup_setup",
                    "timeout",
                    "timeout_cgroup_release",
                ),
                cleanup_blocker,
            )

        if timeout_claimed:
            try:
                timeout_result = _run_timeout_probe(execution_id, timeout_cgroup)
                root_stage_results["timeout"] = {"status": STAGE_PASS}
            except BaseException as exc:
                failure = repr(exc)
                probe_failures.append(f"timeout: {failure}")
                root_stage_results["timeout"] = {
                    "status": STAGE_FAIL,
                    "failure": failure,
                }
                try:
                    timeout_empty = _cgroup_populated(timeout_cgroup) == 0
                except BaseException as cleanup_exc:
                    cleanup_failures.append(
                        f"timeout cleanup observation: {cleanup_exc!r}"
                    )
                    timeout_empty = False
                if not timeout_empty:
                    cleanup_failures.append("timeout cgroup remained populated")
                    cleanup_safe = False
                    cleanup_blocker = "root.timeout"
            timeout_release_failures: list[str] = []
            _release_owned_cgroup(
                timeout_cgroup,
                marker,
                journal,
                timeout_release_failures,
            )
            if timeout_release_failures:
                cleanup_failures.extend(timeout_release_failures)
                root_stage_results["timeout_cgroup_release"] = {
                    "status": STAGE_FAIL,
                    "failure": repr(timeout_release_failures),
                }
                cleanup_safe = False
                cleanup_blocker = "root.timeout_cgroup_release"
            else:
                root_stage_results["timeout_cgroup_release"] = {
                    "status": STAGE_PASS
                }

    if parent_claimed:
        recovery_failures: list[str] = []
        for path in (
            timeout_cgroup,
            stream_cgroup,
            composition_cgroup,
        ):
            entry = journal.get("cgroups", {}).get(str(path))
            if isinstance(entry, dict) and entry.get("state") == "owned":
                _release_owned_cgroup(path, marker, journal, recovery_failures)
        parent_release_failures: list[str] = []
        _release_owned_parent_cgroup(
            parent_cgroup,
            (
                composition_cgroup,
                stream_cgroup,
                timeout_cgroup,
            ),
            marker,
            journal,
            parent_release_failures,
        )
        recovery_failures.extend(parent_release_failures)
        if recovery_failures:
            cleanup_failures.extend(recovery_failures)
            root_stage_results["parent_cgroup_release"] = {
                "status": STAGE_FAIL,
                "failure": repr(recovery_failures),
            }
        else:
            root_stage_results["parent_cgroup_release"] = {
                "status": STAGE_PASS
            }
    else:
        root_stage_results["parent_cgroup_release"] = {
            "status": STAGE_NOT_REACHED,
            "blocked_by": "root.parent_cgroup_setup",
        }

    for stage in ROOT_STAGE_ORDER:
        if stage not in root_stage_results:
            failure = f"root stage observation missing: {stage}"
            root_stage_results[stage] = {
                "status": STAGE_FAIL,
                "failure": failure,
            }
            probe_failures.append(failure)

    namespace_links = report.get("namespace_ids", {})
    if isinstance(namespace_links, dict):
        residue = _scan_for_residue(temp_root, namespace_links)
        if residue:
            cleanup_failures.append(f"process/namespace residue: {residue}")
    for mount_point in _host_mounts_under(temp_root):
        try:
            _umount(mount_point, MNT_DETACH)
        except BaseException as exc:
            cleanup_failures.append(f"host mount cleanup {mount_point}: {exc!r}")
    remaining_mounts = _host_mounts_under(temp_root)
    if remaining_mounts:
        cleanup_failures.append(f"host mounts remain: {remaining_mounts}")

    cgroup_entries = journal.get("cgroups", {})
    unreleased_entries = {
        path: entry
        for path, entry in cgroup_entries.items()
        if not isinstance(entry, dict) or entry.get("state") != "released"
    }
    if unreleased_entries:
        cleanup_failures.append(
            f"ownership journal has unreleased cgroups: {unreleased_entries}"
        )
    unexpected_cgroup_paths = set(cgroup_entries) - exact_cgroup_paths
    if unexpected_cgroup_paths:
        cleanup_failures.append(
            f"ownership journal contains unexpected cgroups: {sorted(unexpected_cgroup_paths)}"
        )
    if any(Path(path).exists() for path in exact_cgroup_paths):
        cleanup_failures.append("one or more exact cgroup paths remain")

    if not cleanup_failures:
        try:
            shutil.rmtree(temp_root, ignore_errors=False)
        except BaseException as exc:
            cleanup_failures.append(f"temporary-root removal: {exc!r}")
    if temp_root.exists():
        cleanup_failures.append(
            "temporary root retained for authenticated outer cleanup"
        )

    stage_results: dict[str, dict[str, object]] = {}
    first_composition_blocker = next(
        (
            f"root.{stage}"
            for stage in (
                "composition_setup",
                "inside_report",
                "live_host_mount_observation",
                "process_tree",
                "cgroup_kill",
                "pidfd_exit_observation",
            )
            if root_stage_results.get(stage, {}).get("status") != STAGE_PASS
        ),
        "root.inside_report",
    )
    if inside_stage_observations is not None:
        for stage in INSIDE_STAGE_ORDER:
            stage_results[f"inside.{stage}"] = dict(
                inside_stage_observations[stage]
            )
    else:
        for stage in INSIDE_STAGE_ORDER:
            stage_results[f"inside.{stage}"] = {
                "status": STAGE_NOT_REACHED,
                "blocked_by": first_composition_blocker,
            }
    for stage in ROOT_STAGE_ORDER:
        stage_results[f"root.{stage}"] = dict(root_stage_results[stage])
    stage_results["cleanup"] = (
        {"status": STAGE_PASS}
        if not cleanup_failures
        else {"status": STAGE_FAIL, "failure": repr(cleanup_failures)[-4000:]}
    )

    network_evidence = report.get("network")
    expected_owned_paths = exact_cgroup_paths
    ownership_evidence = {
        "marker_created_with_o_excl": True,
        "temp_root_exact_execution_id": temp_root.name == execution_id,
        "journal_path_inside_temp_root": marker.parent == temp_root,
        "root_helper_identity_bound": journal.get("helper_identity")
        == helper_identity,
        "cgroup_claim_count": len(cgroup_entries),
        "exact_cgroup_paths": sorted(cgroup_entries),
        "expected_cgroup_paths": sorted(expected_owned_paths),
        "all_cgroups_released": all(
            isinstance(entry, dict) and entry.get("state") == "released"
            for entry in cgroup_entries.values()
        ),
        "temporary_root_removed": not temp_root.exists(),
    }

    stdout_probe = streams.get("stdout_probe")
    stderr_probe = streams.get("stderr_probe")
    combined_probe = streams.get("combined_probe")
    total_theoretical_stream_bytes = sum(
        int(observation.get("theoretical_emitted_bytes", 0))
        for observation in (stdout_probe, stderr_probe, combined_probe)
        if isinstance(observation, dict)
    )
    total_theoretical_output_bytes = (
        total_theoretical_stream_bytes + COMPOSITION_HANDSHAKE_BYTES
    )
    checks = {
        "namespace_set": report.get("namespaces_distinct") is True,
        "private_propagation": (
            report.get("private_mount_propagation") is True
            and process_tree_evidence.get(
                "host_mounts_during_live_namespace"
            )
            == []
            and process_tree_evidence.get(
                "namespace_alive_during_host_mount_observation"
            )
            is True
        ),
        "openat2": (
            isinstance(report.get("openat2"), dict)
            and report["openat2"].get("positive") is True
            and set(report["openat2"].get("denied", {}))
            == {"traversal", "symlink", "xdev"}
            and report["openat2"].get("magiclink_only_denied") is True
        ),
        "quotas": report.get("tmpfs_quota")
        == {"byte_enospc": True, "inode_enospc": True},
        "network": (
            isinstance(network_evidence, dict)
            and network_evidence.get("admin_state_source")
            == "SIOCGIFFLAGS/IFF_UP"
            and network_evidence.get("admin_up_observed") is True
            and network_evidence.get("admin_down_observed") is True
            and int(network_evidence.get("flags_after_up", 0)) & IFF_UP
            == IFF_UP
            and int(network_evidence.get("flags_after_down", IFF_UP)) & IFF_UP
            == 0
            and isinstance(network_evidence.get("listener_endpoint"), dict)
            and network_evidence["listener_endpoint"].get("address")
            == "127.0.0.1"
            and isinstance(
                network_evidence["listener_endpoint"].get("port"), int
            )
            and 0 < network_evidence["listener_endpoint"]["port"] <= 65_535
            and network_evidence.get("listener_active_during_denial") is True
            and network_evidence.get("positive_control") is True
            and network_evidence.get("connectivity_denied") is True
            and isinstance(
                network_evidence.get("denial_exception_type"), str
            )
        ),
        "pivot_root": (
            report.get("pivot_root_old_root_hidden") is True
            and report.get("private_root_device_differs") is True
            and report.get("scratch_quota_mount") is True
            and report.get("scratch_mount_device_differs") is True
        ),
        "path_swap": report.get("path_swap_digest_differs") is True,
        "native_exec": (
            isinstance(report.get("native"), dict)
            and report["native"].get("event") == PTRACE_EVENT_EXEC
            and report["native"].get("exe_identity_match") is True
            and report["native"].get("loader_identity_match") is True
            and report["native"].get("uid_non_root") is True
            and report["native"].get("gid_non_root") is True
            and report["native"].get("cap_eff_zero") is True
            and report["native"].get("no_new_privs") is True
            and report["native"].get(
                "inherited_network_fd_absent_at_exec"
            )
            is True
            and report["native"].get("exit_code") == 0
        ),
        "network_enforcement": (
            isinstance(network_evidence, dict)
            and network_evidence.get(
                "inherited_fd_closed_and_socket_denied"
            )
            is True
            and network_evidence.get(
                "inherited_network_fd_absent_at_exec"
            )
            is True
            and network_evidence.get(
                "native_inherited_network_fd_absent_at_exec"
            )
            is True
            and network_evidence.get(
                "interpreter_inherited_network_fd_absent_at_exec"
            )
            is True
            and isinstance(report.get("native"), dict)
            and report["native"].get("exit_code") == 0
        ),
        "interpreter_exec": (
            isinstance(report.get("interpreter"), dict)
            and report["interpreter"].get("event") == PTRACE_EVENT_EXEC
            and report["interpreter"].get("exe_identity_match") is True
            and report["interpreter"].get("loader_identity_match") is True
            and report["interpreter"].get("script_identity_match") is True
            and report["interpreter"].get("uid_non_root") is True
            and report["interpreter"].get("gid_non_root") is True
            and report["interpreter"].get("cap_eff_zero") is True
            and report["interpreter"].get("no_new_privs") is True
            and report["interpreter"].get(
                "inherited_network_fd_absent_at_exec"
            )
            is True
            and report["interpreter"].get("exit_code") == 0
        ),
        "process_tree": (
            process_tree_evidence.get("member_count_before_kill", 0) >= 3
            and process_tree_evidence.get(
                "detached_pidfd_bound_before_term"
            )
            is True
            and process_tree_evidence.get("detached_identity_revalidated")
            is True
            and process_tree_evidence.get("detached_term_sent_via_pidfd")
            is True
            and process_tree_evidence.get(
                "detached_pidfd_unreadable_after_term"
            )
            is True
            and process_tree_evidence.get(
                "all_member_pidfds_identity_bound"
            )
            is True
            and process_tree_evidence.get(
                "all_member_pidfds_unreadable_before_kill"
            )
            is True
            and process_tree_evidence.get("alive_before_kill") is True
            and process_tree_evidence.get("populated_before_kill") == 1
            and process_tree_evidence.get("cgroup_kill_written") is True
            and process_tree_evidence.get("process_exited_after_kill") is True
            and process_tree_evidence.get("returncode") == -signal.SIGKILL
            and process_tree_evidence.get("populated_zero") is True
            and process_tree_evidence.get("all_member_pidfds_readable") is True
            and process_tree_evidence.get("process_pidfd_readable") is True
            and process_tree_evidence.get(
                "host_mounts_during_live_namespace"
            )
            == []
            and process_tree_evidence.get(
                "namespace_alive_during_host_mount_observation"
            )
            is True
        ),
        "stream_limit": (
            _stream_probe_evidence_complete(stdout_probe, "stdout")
            and _stream_probe_evidence_complete(stderr_probe, "stderr")
            and _stream_probe_evidence_complete(combined_probe, "combined")
            and total_theoretical_stream_bytes
            == (
                2 * SINGLE_STREAM_WRITE_COUNT * 4096
                + COMBINED_STREAM_WRITE_COUNT * 8192
            )
            and total_theoretical_stream_bytes
            <= SYNTHETIC_STREAM_BYTE_BUDGET
            and total_theoretical_output_bytes
            <= SYNTHETIC_STREAM_BYTE_BUDGET
        ),
        "timeout": (
            timeout_result.get("trigger") == "monotonic_timeout"
            and timeout_result.get("alive_before_kill") is True
            and timeout_result.get("populated_before_kill") == 1
            and timeout_result.get("cgroup_kill_written") is True
            and timeout_result.get("pidfd_exit_observed") is True
            and timeout_result.get("process_exited_after_kill") is True
            and timeout_result.get("returncode") == -signal.SIGKILL
            and timeout_result.get("populated_zero") is True
        ),
        "ownership": (
            ownership_evidence["marker_created_with_o_excl"] is True
            and ownership_evidence["temp_root_exact_execution_id"] is True
            and ownership_evidence["journal_path_inside_temp_root"] is True
            and ownership_evidence["root_helper_identity_bound"] is True
            and ownership_evidence["cgroup_claim_count"] == 4
            and ownership_evidence["exact_cgroup_paths"]
            == ownership_evidence["expected_cgroup_paths"]
            and ownership_evidence["all_cgroups_released"] is True
            and ownership_evidence["temporary_root_removed"] is True
        ),
        "cleanup": not cleanup_failures,
    }

    stage_dependencies = _build_stage_dependencies()

    check_dependencies = {
        "namespace_set": ("inside.namespace_set",),
        "private_propagation": (
            "inside.private_propagation",
            "root.live_host_mount_observation",
        ),
        "openat2": ("inside.openat2",),
        "quotas": ("inside.quotas",),
        "network": ("inside.network",),
        "pivot_root": ("inside.pivot_root",),
        "path_swap": ("inside.path_swap",),
        "native_exec": ("inside.native_exec",),
        "network_enforcement": (
            "inside.native_exec",
            "inside.interpreter_exec",
        ),
        "interpreter_exec": ("inside.interpreter_exec",),
        "process_tree": (
            "inside.process_tree_fixture",
            "root.process_tree",
            "root.cgroup_kill",
            "root.pidfd_exit_observation",
            "root.composition_release",
        ),
        "stream_limit": (
            "root.stream_cgroup_setup",
            "root.stdout_stream_limit",
            "root.stdout_stream_safety",
            "root.stderr_stream_limit",
            "root.stderr_stream_safety",
            "root.combined_stream_limit",
            "root.combined_stream_safety",
            "root.stream_cgroup_release",
        ),
        "timeout": (
            "root.timeout_cgroup_setup",
            "root.timeout",
            "root.timeout_cgroup_release",
        ),
        "ownership": (
            "root.parent_cgroup_setup",
            "root.composition_setup",
            "root.composition_release",
            "root.stream_cgroup_setup",
            "root.stream_cgroup_release",
            "root.timeout_cgroup_setup",
            "root.timeout_cgroup_release",
            "root.parent_cgroup_release",
        ),
        "cleanup": ("cleanup",),
    }
    check_results: dict[str, dict[str, object]] = {}
    for name, passed in checks.items():
        dependencies = check_dependencies[name]
        blocked_dependency = next(
            (
                dependency
                for dependency in dependencies
                if stage_results[dependency].get("status") != STAGE_PASS
            ),
            None,
        )
        if blocked_dependency is not None:
            dependency_observation = stage_results[blocked_dependency]
            if dependency_observation.get("status") == STAGE_NOT_REACHED:
                check_results[name] = {
                    "status": STAGE_NOT_REACHED,
                    "blocked_by": dependency_observation.get(
                        "blocked_by", blocked_dependency
                    ),
                }
            else:
                check_results[name] = {
                    "status": STAGE_FAIL,
                    "failed_by": blocked_dependency,
                    "failure": str(
                        dependency_observation.get(
                            "failure",
                            f"dependency failed: {blocked_dependency}",
                        )
                    )[-2000:],
                }
        elif passed:
            check_results[name] = {"status": STAGE_PASS}
        else:
            failure = (
                f"acceptance predicate false after completed stages: {name}"
            )
            check_results[name] = {
                "status": STAGE_FAIL,
                "failure": failure,
            }
            probe_failures.append(failure)

    _assert_causal_result_graph(
        stage_results,
        stage_dependencies,
        check_results,
        check_dependencies,
    )
    if cleanup_failures:
        probe_failures.extend(
            f"cleanup: {item}" for item in cleanup_failures
        )
    has_blocker = bool(probe_failures) or any(
        observation.get("status") != STAGE_PASS
        for observation in (*stage_results.values(), *check_results.values())
    )
    return {
        "disposition": (
            CAPABILITY_PASS if not has_blocker else "HOSTED_CAPABILITY_BLOCKER"
        ),
        "execution_id": execution_id,
        "checks": checks,
        "stage_results": stage_results,
        "stage_dependencies": {
            key: list(value) for key, value in stage_dependencies.items()
        },
        "check_results": check_results,
        "check_dependencies": {
            key: list(value) for key, value in check_dependencies.items()
        },
        "causal_graph_validated": True,
        "network": network_evidence,
        "process_tree": process_tree_evidence,
        "streams": streams,
        "total_theoretical_stream_bytes": total_theoretical_stream_bytes,
        "total_theoretical_output_bytes": total_theoretical_output_bytes,
        "timeout": timeout_result,
        "ownership": ownership_evidence,
        "cleanup_complete": not cleanup_failures,
        "failures": probe_failures,
    }
def _root_cleanup(
    execution_id: str,
    temp_root: Path,
    nonce: str,
    creator_uid: int,
    parent_device: int,
    parent_inode: int,
) -> dict[str, object]:
    failures: list[str] = []
    child_paths = (
        _safe_cgroup_path(execution_id, "timeout"),
        _safe_cgroup_path(execution_id, "combined-stream"),
        _safe_cgroup_path(execution_id, "composition"),
    )
    parent_path = _safe_cgroup_path(execution_id)
    exact_paths = (*child_paths, parent_path)
    try:
        lifecycle_path, lifecycle = _load_helper_lifecycle(
            execution_id,
            temp_root,
            nonce,
            creator_uid,
            parent_device,
            parent_inode,
            require_bound=True,
        )
        helper_identity = lifecycle["helper_identity"]
        if not isinstance(helper_identity, dict):
            raise AssertionError("bound helper identity is invalid")
        helper_termination = _terminate_bound_helper(helper_identity)
    except BaseException as exc:
        return {
            "cleanup_complete": False,
            "ownership_validated": False,
            "already_absent": False,
            "helper_identity_validated": False,
            "helper_terminated": False,
            "lifecycle_removed": False,
            "failures": [
                "helper lifecycle/termination gate failed; resource cleanup "
                f"refused: {exc!r}"
            ],
        }

    if not os.path.lexists(temp_root):
        residues = [str(path) for path in exact_paths if path.exists()]
        if residues:
            failures.append(
                "ownership marker absent; cgroup cleanup refused: "
                + repr(residues)
            )
        if not failures:
            _remove_bound_helper_lifecycle(
                lifecycle_path,
                creator_uid,
                failures,
            )
        return {
            "cleanup_complete": not failures,
            "ownership_validated": True,
            "already_absent": not failures,
            "helper_identity_validated": True,
            "helper_terminated": helper_termination["helper_terminated"],
            "helper_termination": helper_termination,
            "lifecycle_removed": not os.path.lexists(lifecycle_path),
            "failures": failures,
        }

    try:
        marker, journal = _load_ownership_journal(
            execution_id,
            temp_root,
            nonce,
            creator_uid,
            parent_device,
            parent_inode,
            helper_identity,
        )
    except BaseException as exc:
        return {
            "cleanup_complete": False,
            "ownership_validated": True,
            "already_absent": False,
            "helper_identity_validated": True,
            "helper_terminated": helper_termination["helper_terminated"],
            "helper_termination": helper_termination,
            "lifecycle_removed": False,
            "failures": [
                f"ownership validation failed; resource cleanup refused: {exc!r}"
            ],
        }

    exact_strings = {str(path) for path in exact_paths}
    listed_strings = set(journal.get("cgroups", {}))
    unexpected = listed_strings - exact_strings
    if unexpected:
        failures.append(
            f"ownership journal contains unexpected paths: {sorted(unexpected)}"
        )
    for path in child_paths:
        entry = journal.get("cgroups", {}).get(str(path))
        if isinstance(entry, dict) and entry.get("state") in {
            "owned",
            "released",
        }:
            _release_owned_cgroup(path, marker, journal, failures)
        elif path.exists():
            failures.append(
                f"unowned exact cgroup path exists; cleanup refused: {path}"
            )
    _release_owned_parent_cgroup(
        parent_path,
        child_paths,
        marker,
        journal,
        failures,
    )
    residues = [str(path) for path in exact_paths if path.exists()]
    if residues:
        failures.append(f"exact cgroup residues remain: {residues}")

    process_residue = _scan_for_residue(temp_root, {})
    if process_residue:
        failures.append(f"process residue: {process_residue}")
    for mount_point in _host_mounts_under(temp_root):
        try:
            _umount(mount_point, MNT_DETACH)
        except BaseException as exc:
            failures.append(f"host mount cleanup {mount_point}: {exc!r}")
    remaining_mounts = _host_mounts_under(temp_root)
    if remaining_mounts:
        failures.append(f"host mounts remain: {remaining_mounts}")
    if not failures:
        try:
            shutil.rmtree(temp_root, ignore_errors=False)
        except BaseException as exc:
            failures.append(f"temporary-root removal: {exc!r}")
    if temp_root.exists():
        failures.append("authenticated temporary root remains")
    if not failures:
        _remove_bound_helper_lifecycle(
            lifecycle_path,
            creator_uid,
            failures,
        )
    return {
        "cleanup_complete": not failures,
        "ownership_validated": True,
        "already_absent": False,
        "helper_identity_validated": True,
        "helper_terminated": helper_termination["helper_terminated"],
        "helper_termination": helper_termination,
        "lifecycle_removed": not os.path.lexists(lifecycle_path),
        "failures": failures,
    }


def _root_watchdog_exit(_signum: int, _frame: object) -> None:
    os._exit(124)


def _await_root_helper_gate() -> None:
    selector = selectors.DefaultSelector()
    try:
        selector.register(0, selectors.EVENT_READ)
        events = selector.select(timeout=ROOT_HELPER_GATE_SECONDS)
    finally:
        selector.close()
    if not events or os.read(0, 2) != b"g":
        raise AssertionError("root helper lifecycle gate was not released")


def _root_main(argv: list[str]) -> int:
    mode = argv[1]
    execution_id = argv[2]
    temp_root = Path(argv[3])
    if mode == "--root-probe":
        if len(argv) != 9:
            raise AssertionError("root probe argv shape is invalid")
        signal.signal(signal.SIGALRM, _root_watchdog_exit)
        signal.alarm(ROOT_HELPER_WATCHDOG_SECONDS)
        source_file = Path(argv[4]).resolve()
        if source_file != Path(argv[0]).resolve():
            raise AssertionError("root helper source argv identity mismatch")
        helper_identity = _current_root_helper_identity(
            execution_id,
            argv[5],
            source_file,
        )
        print(
            ROOT_HANDSHAKE_PREFIX
            + json.dumps(helper_identity, sort_keys=True),
            flush=True,
        )
        _await_root_helper_gate()
        _, lifecycle = _load_helper_lifecycle(
            execution_id,
            temp_root,
            argv[5],
            int(argv[6]),
            int(argv[7]),
            int(argv[8]),
            require_bound=True,
        )
        if lifecycle.get("helper_identity") != helper_identity:
            raise AssertionError("persisted root helper identity changed before gate")
        result = _root_probe(
            execution_id,
            temp_root,
            source_file,
            argv[5],
            int(argv[6]),
            int(argv[7]),
            int(argv[8]),
            helper_identity,
        )
    elif mode == "--root-cleanup":
        if len(argv) != 8:
            raise AssertionError("root cleanup argv shape is invalid")
        signal.signal(signal.SIGALRM, _root_watchdog_exit)
        signal.alarm(ROOT_CLEANUP_WATCHDOG_SECONDS)
        result = _root_cleanup(
            execution_id,
            temp_root,
            argv[4],
            int(argv[5]),
            int(argv[6]),
            int(argv[7]),
        )
    else:
        raise AssertionError(f"unknown root mode: {mode}")
    signal.alarm(0)
    print(ROOT_RESULT_PREFIX + json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("cleanup_complete") else 1


def _parse_root_result(stdout: bytes) -> dict[str, object]:
    lines = stdout.decode("utf-8", "replace").splitlines()
    matches = [
        line[len(ROOT_RESULT_PREFIX) :]
        for line in lines
        if line.startswith(ROOT_RESULT_PREFIX)
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one root result, got {len(matches)}: {lines[-20:]}")
    return json.loads(matches[0])


def _read_root_helper_handshake(
    process: subprocess.Popen[bytes],
) -> dict[str, object]:
    if process.stdout is None:
        raise AssertionError("root helper stdout pipe is missing")
    descriptor = process.stdout.fileno()
    os.set_blocking(descriptor, False)
    selector = selectors.DefaultSelector()
    buffer = bytearray()
    deadline = time.monotonic() + ROOT_HELPER_HANDSHAKE_SECONDS
    try:
        selector.register(descriptor, selectors.EVENT_READ)
        while b"\n" not in buffer and time.monotonic() < deadline:
            for _, _ in selector.select(timeout=POLL_INTERVAL_SECONDS):
                chunk = os.read(descriptor, 4096)
                if not chunk:
                    raise AssertionError(
                        "root helper exited before lifecycle handshake"
                    )
                buffer.extend(chunk)
                if len(buffer) > DIAGNOSTIC_CHARACTER_LIMIT:
                    raise AssertionError("root helper handshake exceeded hard limit")
    finally:
        selector.close()
        os.set_blocking(descriptor, True)
    if b"\n" not in buffer:
        raise AssertionError("root helper lifecycle handshake timed out")
    line, trailing = bytes(buffer).split(b"\n", 1)
    if trailing:
        raise AssertionError("root helper emitted data before lifecycle gate")
    decoded = line.decode("utf-8", "strict")
    if not decoded.startswith(ROOT_HANDSHAKE_PREFIX):
        raise AssertionError("root helper handshake prefix is invalid")
    value = json.loads(decoded[len(ROOT_HANDSHAKE_PREFIX) :])
    if not isinstance(value, dict):
        raise AssertionError("root helper handshake payload is invalid")
    return value


def _bounded_diagnostic_value(value: object, depth: int = 0) -> object:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[-512:]
    if depth >= 4:
        return repr(value)[-512:]
    if isinstance(value, dict):
        bounded: dict[str, object] = {}
        entries = list(value.items())
        for raw_key, item in entries[:64]:
            key = str(raw_key)[:160]
            bounded[key] = _bounded_diagnostic_value(item, depth + 1)
        if len(entries) > 64:
            bounded["__omitted_entries__"] = len(entries) - 64
        return bounded
    if isinstance(value, (list, tuple)):
        items = [
            _bounded_diagnostic_value(item, depth + 1)
            for item in value[:32]
        ]
        if len(value) > 32:
            items.append({"__omitted_entries__": len(value) - 32})
        return items
    return repr(value)[-512:]


def _hosted_diagnostic(
    completed: subprocess.CompletedProcess[bytes],
    result: dict[str, object],
    cleanup_result: dict[str, object],
) -> tuple[dict[str, object], str]:
    result_summary = {
        key: result.get(key)
        for key in (
            "disposition",
            "execution_id",
            "cleanup_complete",
            "failures",
            "checks",
            "stage_results",
            "check_results",
            "network",
            "process_tree",
            "streams",
            "timeout",
            "ownership",
        )
    }
    diagnostic = {
        "returncode": completed.returncode,
        "result": _bounded_diagnostic_value(result_summary),
        "stderr_tail": completed.stderr.decode("utf-8", "replace")[-4000:],
        "outer_cleanup": _bounded_diagnostic_value(cleanup_result),
    }
    encoded = json.dumps(diagnostic, sort_keys=True)
    if len(encoded) > DIAGNOSTIC_CHARACTER_LIMIT:
        failures = result.get("failures")
        failure_count = len(failures) if isinstance(failures, list) else None
        diagnostic = {
            "diagnostic_truncated": True,
            "returncode": completed.returncode,
            "disposition": str(result.get("disposition"))[-128:],
            "execution_id": str(result.get("execution_id"))[-128:],
            "cleanup_complete": result.get("cleanup_complete"),
            "failure_count": failure_count,
            "failures_tail": repr(failures)[-4000:],
            "stderr_tail": completed.stderr.decode("utf-8", "replace")[-4000:],
            "outer_cleanup": _bounded_diagnostic_value(cleanup_result, 3),
        }
        encoded = json.dumps(diagnostic, sort_keys=True)
    if len(encoded) > DIAGNOSTIC_CHARACTER_LIMIT:
        raise AssertionError("bounded Hosted diagnostic exceeded its hard limit")
    return diagnostic, encoded


def _execute_hosted_capability_test(tmp_path: Path) -> None:
    global _LAST_EXECUTION_ID
    causal_negative_controls = _run_causal_graph_negative_controls()
    assert all(causal_negative_controls.values())
    github_actions = os.environ.get("GITHUB_ACTIONS")
    runner_environment = os.environ.get("RUNNER_ENVIRONMENT")
    if github_actions != "true" or runner_environment == "self-hosted":
        observation = {
            "disposition": NOT_EXECUTED,
            "capability_pass": False,
            "reason": "not running on an identified GitHub-hosted Actions runner",
        }
        print(RESULT_PREFIX + json.dumps(observation, sort_keys=True))
        assert observation["disposition"] == NOT_EXECUTED
        assert observation["capability_pass"] is False
        return

    assert runner_environment == "github-hosted", (
        "GitHub Actions execution without the github-hosted identity is not "
        "eligible for capability PASS"
    )
    assert os.environ.get("RUNNER_OS") == "Linux"
    assert os.environ.get("RUNNER_ARCH") == "X64"
    assert os.environ.get("GITHUB_REPOSITORY") == "apolo183/tool-system"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    assert platform.system() == "Linux"
    assert platform.machine() == "x86_64"

    sudo_gate = subprocess.run(
        ["/usr/bin/sudo", "-n", "--", "/usr/bin/id", "-u"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
    )
    assert sudo_gate.returncode == 0, sudo_gate.stderr.decode("utf-8", "replace")
    assert sudo_gate.stdout == b"0\n"

    execution_id = "ts-b02a-" + uuid.uuid4().hex[:20]
    _LAST_EXECUTION_ID = execution_id
    ownership_nonce = uuid.uuid4().hex + uuid.uuid4().hex
    creator_root = tmp_path / execution_id
    creator_parent_stat = os.lstat(tmp_path)
    creator_uid = os.geteuid()
    source_file = Path(__file__).resolve()
    command = [
        "/usr/bin/sudo",
        "-n",
        "--",
        sys.executable,
        "-I",
        str(source_file),
        "--root-probe",
        execution_id,
        str(creator_root),
        str(source_file),
        ownership_nonce,
        str(creator_uid),
        str(creator_parent_stat.st_dev),
        str(creator_parent_stat.st_ino),
    ]
    expected_helper = {
        "argv_sha256": _argv_sha256(command[3:]),
        "source_path": str(source_file),
        "source_identity": _regular_file_identity(source_file),
        "executable_identity": _stat_identity(sys.executable),
    }
    lifecycle_path, lifecycle = _create_helper_lifecycle(
        execution_id,
        creator_root,
        ownership_nonce,
        creator_uid,
        creator_parent_stat.st_dev,
        creator_parent_stat.st_ino,
        expected_helper,
    )
    launching_lifecycle = json.loads(json.dumps(lifecycle, sort_keys=True))
    process: subprocess.Popen[bytes] | None = None
    completed: subprocess.CompletedProcess[bytes] | None = None
    cleanup_result: dict[str, object] = {}
    probe_error: BaseException | None = None
    lifecycle_bound = False
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        handshake = _read_root_helper_handshake(process)
        _bind_helper_lifecycle(
            lifecycle_path,
            lifecycle,
            handshake,
            execution_id,
            ownership_nonce,
            creator_uid,
        )
        lifecycle_bound = True
        stdout, stderr = process.communicate(
            input=b"g",
            timeout=HELPER_WALL_SECONDS,
        )
        completed = subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout,
            stderr,
        )
    except BaseException as exc:
        probe_error = exc
    finally:
        if process is not None and not lifecycle_bound and process.poll() is None:
            try:
                process.communicate(
                    input=b"",
                    timeout=ROOT_HELPER_GATE_SECONDS + 2,
                )
            except subprocess.TimeoutExpired:
                pass
        elif (
            process is not None
            and process.stdin is not None
            and not process.stdin.closed
        ):
            try:
                process.stdin.close()
            except OSError:
                pass
        if not lifecycle_bound:
            assert process is None or process.poll() is not None, (
                "unbound root helper was not fully reaped; launching lifecycle "
                "claim retained"
            )
            _, observed_lifecycle = _load_helper_lifecycle(
                execution_id,
                creator_root,
                ownership_nonce,
                creator_uid,
                creator_parent_stat.st_dev,
                creator_parent_stat.st_ino,
                require_bound=False,
            )
            if observed_lifecycle.get("state") == "bound":
                lifecycle_bound = True
            else:
                assert observed_lifecycle == launching_lifecycle
                expected_paths = (
                    _safe_cgroup_path(execution_id),
                    _safe_cgroup_path(execution_id, "composition"),
                    _safe_cgroup_path(execution_id, "combined-stream"),
                    _safe_cgroup_path(execution_id, "timeout"),
                )
                assert not os.path.lexists(creator_root)
                assert not any(path.exists() for path in expected_paths)
                lifecycle_failures: list[str] = []
                _remove_bound_helper_lifecycle(
                    lifecycle_path,
                    creator_uid,
                    lifecycle_failures,
                )
                assert lifecycle_failures == [], lifecycle_failures
                cleanup_result = {
                    "cleanup_complete": True,
                    "ownership_validated": False,
                    "already_absent": True,
                    "helper_identity_validated": False,
                    "helper_terminated": False,
                    "popen_fully_reaped": True,
                    "lifecycle_removed": True,
                    "unbound_lifecycle_reaped": True,
                    "failures": [],
                }

        if lifecycle_bound:
            cleanup = subprocess.run(
                [
                    "/usr/bin/sudo",
                    "-n",
                    "--",
                    sys.executable,
                    "-I",
                    str(source_file),
                    "--root-cleanup",
                    execution_id,
                    str(creator_root),
                    ownership_nonce,
                    str(creator_uid),
                    str(creator_parent_stat.st_dev),
                    str(creator_parent_stat.st_ino),
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            cleanup_result = _parse_root_result(cleanup.stdout)
            if process is not None and process.poll() is None:
                if cleanup_result.get("helper_terminated") is True:
                    try:
                        process.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate(timeout=3)
                else:
                    try:
                        process.communicate(
                            timeout=ROOT_HELPER_GATE_SECONDS + 2
                        )
                    except subprocess.TimeoutExpired:
                        pass
            assert cleanup.returncode == 0, cleanup.stderr.decode(
                "utf-8", "replace"
            )
            assert cleanup_result["ownership_validated"] is True, cleanup_result
            assert cleanup_result["helper_identity_validated"] is True, cleanup_result
            assert cleanup_result["helper_terminated"] is True, cleanup_result
            assert cleanup_result["lifecycle_removed"] is True, cleanup_result
            helper_termination = cleanup_result["helper_termination"]
            assert set(helper_termination) == {
                "initial_state",
                "helper_was_active",
                "helper_pidfd_opened",
                "helper_pidfd_open_esrch",
                "helper_pid_reuse_observed",
                "helper_sigkill_sent",
                "helper_signal_esrch",
                "helper_pidfd_exit_observed",
                "helper_terminated",
            }, cleanup_result
            assert helper_termination["initial_state"] in {
                "gone_before_pidfd_open",
                "gone",
                "pid_reused",
                "matching",
                "matching_zombie",
            }, cleanup_result
            assert helper_termination["helper_terminated"] is True, cleanup_result
            assert (
                helper_termination["helper_was_active"] is False
                or helper_termination["helper_sigkill_sent"] is True
                or helper_termination["helper_signal_esrch"] is True
                or helper_termination["initial_state"] == "matching_zombie"
            ), cleanup_result
            assert (
                helper_termination["helper_pidfd_exit_observed"] is True
                or helper_termination["helper_pidfd_open_esrch"] is True
                or helper_termination["helper_pid_reuse_observed"] is True
            ), cleanup_result

        assert cleanup_result["cleanup_complete"] is True, cleanup_result
        assert cleanup_result["failures"] == [], cleanup_result
        assert process is None or process.poll() is not None
        assert not creator_root.exists()
        assert not os.path.lexists(lifecycle_path)

    if probe_error is not None:
        raise probe_error
    assert completed is not None
    result = _parse_root_result(completed.stdout)
    diagnostic, encoded_diagnostic = _hosted_diagnostic(
        completed,
        result,
        cleanup_result,
    )
    print(DIAGNOSTIC_PREFIX + encoded_diagnostic)
    assert completed.returncode == 0, diagnostic
    assert result["disposition"] == CAPABILITY_PASS, diagnostic
    assert result["cleanup_complete"] is True, diagnostic
    assert result["failures"] == [], diagnostic
    expected_checks = {
        "namespace_set",
        "private_propagation",
        "openat2",
        "quotas",
        "network",
        "pivot_root",
        "path_swap",
        "native_exec",
        "network_enforcement",
        "interpreter_exec",
        "process_tree",
        "stream_limit",
        "timeout",
        "ownership",
        "cleanup",
    }
    assert set(result["checks"]) == expected_checks, diagnostic
    assert all(value is True for value in result["checks"].values()), diagnostic
    expected_stage_keys = {
        *(f"inside.{stage}" for stage in INSIDE_STAGE_ORDER),
        *(f"root.{stage}" for stage in ROOT_STAGE_ORDER),
        "cleanup",
    }
    assert set(result["stage_results"]) == expected_stage_keys, diagnostic
    assert set(result["stage_dependencies"]) == expected_stage_keys, diagnostic
    assert set(result["check_results"]) == set(result["checks"]), diagnostic
    assert set(result["check_dependencies"]) == expected_checks, diagnostic
    _assert_causal_result_graph(
        result["stage_results"],
        result["stage_dependencies"],
        result["check_results"],
        result["check_dependencies"],
    )
    assert result["causal_graph_validated"] is True, diagnostic
    assert all(
        isinstance(observation, dict)
        and observation == {"status": STAGE_PASS}
        for observation in result["stage_results"].values()
    ), diagnostic
    assert all(
        isinstance(observation, dict)
        and observation == {"status": STAGE_PASS}
        for observation in result["check_results"].values()
    ), diagnostic
    assert all(
        "blocked_by" not in observation
        for observation in (
            *result["stage_results"].values(),
            *result["check_results"].values(),
        )
    ), diagnostic
    network = result["network"]
    assert network.get("admin_state_source") == "SIOCGIFFLAGS/IFF_UP", diagnostic
    assert network.get("admin_up_observed") is True, diagnostic
    assert network.get("admin_down_observed") is True, diagnostic
    assert int(network["flags_after_up"]) & IFF_UP == IFF_UP, diagnostic
    assert int(network["flags_after_down"]) & IFF_UP == 0, diagnostic
    assert network.get("listener_endpoint", {}).get("address") == "127.0.0.1", diagnostic
    assert 0 < int(network["listener_endpoint"]["port"]) <= 65_535, diagnostic
    assert network.get("listener_active_during_denial") is True, diagnostic
    assert network.get("connectivity_denied") is True, diagnostic
    assert isinstance(network.get("denial_exception_type"), str), diagnostic
    assert network.get("inherited_network_fd_absent_at_exec") is True, diagnostic
    assert (
        network.get("native_inherited_network_fd_absent_at_exec") is True
    ), diagnostic
    assert (
        network.get("interpreter_inherited_network_fd_absent_at_exec") is True
    ), diagnostic
    assert network.get("inherited_fd_closed_and_socket_denied") is True, diagnostic
    process_tree = result["process_tree"]
    assert process_tree["detached_pidfd_bound_before_term"] is True, diagnostic
    assert process_tree["detached_identity_revalidated"] is True, diagnostic
    assert process_tree["detached_term_sent_via_pidfd"] is True, diagnostic
    assert (
        process_tree["detached_pidfd_unreadable_after_term"] is True
    ), diagnostic
    assert process_tree["all_member_pidfds_identity_bound"] is True, diagnostic
    assert (
        process_tree["all_member_pidfds_unreadable_before_kill"] is True
    ), diagnostic
    assert process_tree["host_mounts_during_live_namespace"] == [], diagnostic
    assert (
        process_tree["namespace_alive_during_host_mount_observation"] is True
    ), diagnostic
    for key, mode, trigger in (
        ("stdout_probe", "stdout", "stdout_raw_stream_limit"),
        ("stderr_probe", "stderr", "stderr_raw_stream_limit"),
        ("combined_probe", "combined", "combined_raw_stream_limit"),
    ):
        observation = result["streams"][key]
        assert observation["trigger"] == trigger, diagnostic
        assert _stream_probe_evidence_complete(observation, mode), diagnostic
        assert observation["alive_before_kill"] is True, diagnostic
        assert observation["populated_before_kill"] == 1, diagnostic
        assert observation["term_ignored_before_kill"] is True, diagnostic
        assert observation["cgroup_kill_written"] is True, diagnostic
        assert observation["pidfd_exit_observed"] is True, diagnostic
        assert observation["process_exited_after_kill"] is True, diagnostic
        assert observation["returncode"] == -signal.SIGKILL, diagnostic
        assert observation["populated_zero"] is True, diagnostic
        assert observation["accounting_complete"] is True, diagnostic
        assert all(
            observation["discarded"][name]
            == observation["emitted"][name] - observation["retained"][name]
            for name in ("stdout", "stderr")
        ), diagnostic
    expected_stream_bytes = (
        2 * SINGLE_STREAM_WRITE_COUNT * 4096
        + COMBINED_STREAM_WRITE_COUNT * 8192
    )
    assert result["total_theoretical_stream_bytes"] == expected_stream_bytes, diagnostic
    assert result["total_theoretical_output_bytes"] == (
        expected_stream_bytes + COMPOSITION_HANDSHAKE_BYTES
    ), diagnostic
    assert result["total_theoretical_output_bytes"] <= SYNTHETIC_STREAM_BYTE_BUDGET, diagnostic
    timeout = result["timeout"]
    assert timeout["trigger"] == "monotonic_timeout", diagnostic
    assert timeout["alive_before_kill"] is True, diagnostic
    assert timeout["populated_before_kill"] == 1, diagnostic
    assert timeout["cgroup_kill_written"] is True, diagnostic
    assert timeout["pidfd_exit_observed"] is True, diagnostic
    assert timeout["process_exited_after_kill"] is True, diagnostic
    assert timeout["returncode"] == -signal.SIGKILL, diagnostic
    assert timeout["populated_zero"] is True, diagnostic
    ownership = result["ownership"]
    assert ownership["marker_created_with_o_excl"] is True, diagnostic
    assert ownership["temp_root_exact_execution_id"] is True, diagnostic
    assert ownership["journal_path_inside_temp_root"] is True, diagnostic
    assert ownership["root_helper_identity_bound"] is True, diagnostic
    assert ownership["cgroup_claim_count"] == 4, diagnostic
    assert ownership["exact_cgroup_paths"] == ownership["expected_cgroup_paths"], diagnostic
    assert ownership["all_cgroups_released"] is True, diagnostic
    assert ownership["temporary_root_removed"] is True, diagnostic
    assert NOT_EXECUTED not in json.dumps(result)
    public_result = {
        "disposition": CAPABILITY_PASS,
        "capability_pass": True,
        "execution_id": execution_id,
        "stage_count": len(result["stage_results"]),
        "check_count": len(result["check_results"]),
        "causal_graph_validated": result["causal_graph_validated"],
        "stream_triggers": {
            key: result["streams"][key]["trigger"]
            for key in ("stdout_probe", "stderr_probe", "combined_probe")
        },
        "root_helper_lifecycle_closed": (
            cleanup_result["helper_identity_validated"] is True
            and cleanup_result["helper_terminated"] is True
            and cleanup_result["lifecycle_removed"] is True
        ),
        "host_mounts_during_live_namespace": process_tree[
            "host_mounts_during_live_namespace"
        ],
        "inherited_network_fd_absent_at_exec": network[
            "inherited_network_fd_absent_at_exec"
        ],
        "cleanup_complete": True,
    }
    print(RESULT_PREFIX + json.dumps(public_result, sort_keys=True), flush=True)


def test_ts_b02a_core_local_os_isolation_backend_feasibility(tmp_path: Path) -> None:
    try:
        _execute_hosted_capability_test(tmp_path)
    except BaseException as exc:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            blocker = {
                "disposition": "HOSTED_CAPABILITY_BLOCKER",
                "capability_pass": False,
                "execution_id": _LAST_EXECUTION_ID,
                "failure_type": type(exc).__name__,
                "failure": str(exc)[-4000:],
            }
            print(RESULT_PREFIX + json.dumps(blocker, sort_keys=True), flush=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in {"--root-probe", "--root-cleanup"}:
        raise SystemExit(_root_main(sys.argv))
    if len(sys.argv) == 4 and sys.argv[1] == "--gate-exec":
        gate_fd = int(sys.argv[2])
        gated_argv = json.loads(sys.argv[3])
        if os.read(gate_fd, 1) != b"g":
            raise SystemExit(125)
        os.close(gate_fd)
        os.execv(gated_argv[0], gated_argv)
    if len(sys.argv) == 6 and sys.argv[1] == "--inside-namespace":
        _inside_namespace(
            sys.argv[2],
            Path(sys.argv[3]),
            int(sys.argv[4]),
            sys.argv[5],
        )
        raise SystemExit(0)
