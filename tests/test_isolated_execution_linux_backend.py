from __future__ import annotations

import hashlib
import errno
import json
import os
import platform
import stat
import subprocess
import sys
import time
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

import tool_system.isolated_execution.linux_backend as linux_backend
from tool_system.isolated_execution.contract import (
    ISOLATION_REQUEST_SCHEMA_V1,
    ExecutableFormatV1,
    ExecutablePolicyV1,
    ExpectedFileIdentityV1,
    ExpectedFileTypeV1,
    FilesystemPolicyV1,
    IsolationRequestV1,
    NetworkPolicyV1,
    OutputPolicyV1,
    ProcessPolicyV1,
    ReadOnlyRootV1,
    RequestIdentityV1,
    StreamPolicyV1,
    WorkloadIdentityV1,
)
from tool_system.isolated_execution.evidence import (
    ExecutionOutcomeV1,
    validate_execution_evidence_v1,
)
from tool_system.isolated_execution.linux_backend import (
    BACKEND_PROFILE,
    REQUIRED_CAPABILITY_SET_DIGEST,
    IdentityMismatch,
    LinuxNativeSupervisorV1,
    _OwnedCgroupTree,
    _RawStreams,
    _read_pt_interp,
    _safe_absolute_open,
    _seal_expected_file,
)


HOSTED_RESULT_PREFIX = "TS_B02A_IMPLEMENTATION_HOSTED_RESULT="
ROOT_MARKER = "TS_B02A_IMPLEMENTATION_ROOT_TEST"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected(
    source: Path,
    private_path: str,
    file_type: ExpectedFileTypeV1,
) -> ExpectedFileIdentityV1:
    value = os.stat(source)
    return ExpectedFileIdentityV1(
        source_path=str(source),
        private_path=private_path,
        file_type=file_type,
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
        size=value.st_size,
        sha256=_sha256(source),
    )


def _root(source: Path, private_path: str) -> ReadOnlyRootV1:
    value = os.stat(source)
    return ReadOnlyRootV1(
        source_path=str(source),
        private_path=private_path,
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
    )


def _compile_fixture(tmp_path: Path, body: str, name: str = "workload") -> Path:
    source = tmp_path / f"{name}.c"
    binary = tmp_path / name
    source.write_text(body, encoding="utf-8")
    completed = subprocess.run(
        [
            "/usr/bin/cc",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(source),
            "-o",
            str(binary),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return binary.resolve()


def _loader(binary: Path) -> tuple[str, Path]:
    descriptor = os.open(binary, os.O_RDONLY)
    try:
        private_path = _read_pt_interp(descriptor)
    finally:
        os.close(descriptor)
    assert private_path is not None
    return private_path, Path(private_path).resolve()


def _shared_library_root(loader_source: Path) -> Path:
    # Ubuntu's dynamic loader and libc live in one canonical multiarch root.
    # Resolve it from the actual loader rather than guessing a distribution.
    return loader_source.parent.resolve()


def _request(binary: Path, *, deadline_seconds: float = 30) -> IsolationRequestV1:
    parsed_loader, loader_source = _loader(binary)
    library_root = _shared_library_root(loader_source)
    fixture_root = binary.parent.resolve()
    digest = hashlib.sha256(b"ts-b02a-implementation-fixture").hexdigest()
    execution_id = "ts-b02a-" + uuid.uuid4().hex[:20]
    return IsolationRequestV1(
        schema_version=ISOLATION_REQUEST_SCHEMA_V1,
        execution_id=execution_id,
        identity=RequestIdentityV1(
            task_sha256=digest,
            source_sha256=digest,
            candidate_sha256=digest,
            workspace_sha256=digest,
            configuration_sha256=digest,
            policy_sha256=digest,
        ),
        filesystem=FilesystemPolicyV1(
            read_only_inputs=(
                _root(fixture_root, "/inputs/fixture"),
                _root(library_root, "/lib/x86_64-linux-gnu"),
            ),
            cwd_private_path="/work",
            scratch_private_path="/scratch",
            output_private_path="/output",
            scratch_byte_limit=1_048_576,
            scratch_inode_limit=128,
            output_byte_limit=1_048_576,
            output_inode_limit=128,
            retained_output_paths=("result.txt",),
        ),
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.ELF_DYNAMIC,
            entrypoint=_expected(binary, "/fixture/workload", ExpectedFileTypeV1.ELF),
            interpreter=None,
            loader=_expected(
                loader_source,
                parsed_loader,
                ExpectedFileTypeV1.LOADER,
            ),
            parsed_interpreter_path=parsed_loader,
            argv=("/fixture/workload",),
            environment=(),
        ),
        workload=WorkloadIdentityV1(uid=65534, gid=65534),
        network=NetworkPolicyV1(),
        streams=StreamPolicyV1(
            stdout_raw_byte_limit=65_536,
            stderr_raw_byte_limit=65_536,
            combined_raw_byte_limit=98_304,
            retained_byte_limit=32_768,
        ),
        process=ProcessPolicyV1(
            deadline_monotonic_ns=time.monotonic_ns()
            + int(deadline_seconds * 1_000_000_000),
            termination_grace_ns=100_000_000,
            cgroup_name=execution_id,
            max_processes=64,
        ),
        output=OutputPolicyV1(
            structured_result_byte_limit=262_144,
            file_output_byte_limit=1_048_576,
        ),
    )


def _is_github_hosted() -> bool:
    return (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
        and os.environ.get("RUNNER_OS") == "Linux"
        and os.environ.get("RUNNER_ARCH") == "X64"
    )


def test_backend_profile_has_no_fallback() -> None:
    backend = LinuxNativeSupervisorV1()
    assert backend.backend_profile == "linux_native_supervisor_v1"
    assert backend.backend_profile == BACKEND_PROFILE
    assert backend.required_capability_set_sha256 == REQUIRED_CAPABILITY_SET_DIGEST
    assert not hasattr(backend, "fallback")


def test_raw_stream_accounting_is_bounded_and_post_decode() -> None:
    streams = _RawStreams(8, 8, 12, 6)
    streams.consume("stdout", b"abcdef")
    streams.consume("stderr", b"\xff" * 9)
    value = streams.record()
    assert value["raw_bytes"] == {"stdout": 6, "stderr": 9}
    assert value["combined_raw_bytes"] == 15
    assert value["retained_bytes"] == {"stdout": 6, "stderr": 0}
    assert value["discarded_bytes"] == {"stdout": 0, "stderr": 9}
    assert value["trigger"] == "stderr_raw_byte_limit"
    assert value["decoding_status"] == "utf8_valid"


def test_memfd_seal_blocks_path_replacement_and_in_place_mutation(tmp_path: Path) -> None:
    selected = tmp_path / "selected"
    selected.write_bytes(b"original-payload")
    selected.chmod(0o755)
    expected = _expected(selected, "/fixture/selected", ExpectedFileTypeV1.ELF)
    sealed = _seal_expected_file(expected)
    try:
        original_sealed_digest = sealed.sealed_identity["sha256"]
        replacement = tmp_path / "replacement"
        replacement.write_bytes(b"replacement")
        replacement.chmod(0o755)
        os.replace(replacement, selected)
        selected.write_bytes(b"mutated-after-rename")
        assert _sha256(selected) != original_sealed_digest
        assert sealed.sealed_identity["sha256"] == original_sealed_digest
        assert sealed.sealed_identity["inode"] != expected.inode
    finally:
        sealed.close()


def test_symlink_and_proc_magic_link_selection_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"x")
    link = tmp_path / "link"
    link.symlink_to(target)
    for candidate in (link, Path("/proc/self/fd/0")):
        try:
            descriptor = _safe_absolute_open(str(candidate))
        except OSError as exc:
            assert exc.errno in {errno.ELOOP, errno.EXDEV}
        else:
            os.close(descriptor)
            raise AssertionError(f"unsafe selection unexpectedly opened: {candidate}")


def test_cgroup_name_validation_refuses_escape() -> None:
    for execution_id in ("../escape", "/absolute", "UPPER", "a" * 65):
        try:
            _OwnedCgroupTree(execution_id, "0" * 64)
        except Exception as exc:
            assert "execution" in str(exc) or "cgroup" in str(exc)
        else:
            raise AssertionError(f"unsafe cgroup ID accepted: {execution_id}")


@pytest.mark.parametrize(
    "failure_point",
    ("pidfd_open", "selector", "second_pipe", "trace_pipe"),
)
def test_mandatory_abi_control_failure_has_no_fd_or_child_residue(
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    before_fds = set(os.listdir("/proc/self/fd"))
    created_children: list[int] = []
    original_fork = linux_backend.os.fork

    def tracking_fork() -> int:
        child = original_fork()
        if child > 0:
            created_children.append(child)
        return child

    monkeypatch.setattr(linux_backend.os, "fork", tracking_fork)
    if failure_point == "pidfd_open":
        def fail_pidfd_open(_pid: int, _flags: int = 0) -> int:
            raise OSError(errno.EMFILE, "injected pidfd_open failure")

        monkeypatch.setattr(linux_backend.os, "pidfd_open", fail_pidfd_open)
    elif failure_point == "selector":
        def fail_selector():
            raise OSError(errno.EMFILE, "injected selector failure")

        monkeypatch.setattr(
            linux_backend.selectors,
            "DefaultSelector",
            fail_selector,
        )
    else:
        original_pipe2 = linux_backend.os.pipe2
        calls = 0
        fail_at = 2 if failure_point == "second_pipe" else 3

        def fail_pipe2(flags: int) -> tuple[int, int]:
            nonlocal calls
            calls += 1
            if calls == fail_at:
                raise OSError(errno.EMFILE, "injected pipe2 failure")
            return original_pipe2(flags)

        monkeypatch.setattr(linux_backend.os, "pipe2", fail_pipe2)
    with pytest.raises(OSError, match="injected"):
        linux_backend._mandatory_abi_control()
    assert set(os.listdir("/proc/self/fd")) == before_fds
    for child in created_children:
        with pytest.raises(ChildProcessError):
            os.waitpid(child, os.WNOHANG)


@pytest.mark.parametrize(
    "failure_point", ("pidfd_open", "selector", "read", "second_pipe")
)
def test_seccomp_control_failure_has_no_fd_or_direct_child_residue(
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    before_fds = set(os.listdir("/proc/self/fd"))
    parent_pid = os.getpid()
    direct_children: list[int] = []
    original_fork = linux_backend.os.fork

    def tracking_fork() -> int:
        child = original_fork()
        if os.getpid() == parent_pid and child > 0:
            direct_children.append(child)
        return child

    monkeypatch.setattr(linux_backend.os, "fork", tracking_fork)
    if failure_point == "pidfd_open":
        original = linux_backend.os.pidfd_open

        def fail_parent_pidfd(pid: int, flags: int = 0) -> int:
            if os.getpid() == parent_pid:
                raise OSError(errno.EMFILE, "injected seccomp pidfd failure")
            return original(pid, flags)

        monkeypatch.setattr(linux_backend.os, "pidfd_open", fail_parent_pidfd)
    elif failure_point == "selector":
        original = linux_backend.selectors.DefaultSelector

        def fail_parent_selector():
            if os.getpid() == parent_pid:
                raise OSError(errno.EMFILE, "injected seccomp selector failure")
            return original()

        monkeypatch.setattr(
            linux_backend.selectors, "DefaultSelector", fail_parent_selector
        )
    elif failure_point == "read":
        original = linux_backend.os.read

        def fail_parent_read(fd: int, size: int) -> bytes:
            if os.getpid() == parent_pid:
                raise OSError(errno.EIO, "injected seccomp read failure")
            return original(fd, size)

        monkeypatch.setattr(linux_backend.os, "read", fail_parent_read)
    else:
        original_pipe2 = linux_backend.os.pipe2
        pipe_calls = 0

        def fail_second_pipe(flags: int) -> tuple[int, int]:
            nonlocal pipe_calls
            pipe_calls += 1
            if pipe_calls == 2:
                raise OSError(errno.EMFILE, "injected seccomp second-pipe failure")
            return original_pipe2(flags)

        monkeypatch.setattr(linux_backend.os, "pipe2", fail_second_pipe)

    with pytest.raises(OSError, match="injected seccomp"):
        linux_backend._seccomp_socket_control(
            {
                "x32_kill_control": True,
            }
        )
    assert set(os.listdir("/proc/self/fd")) == before_fds
    assert bool(direct_children) is (failure_point != "second_pipe")
    for child in direct_children:
        with pytest.raises(ChildProcessError):
            os.waitpid(child, os.WNOHANG)


def test_seccomp_x32_pidfd_failure_closes_gate_and_reaps_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before_fds = set(os.listdir("/proc/self/fd"))
    parent_pid = os.getpid()
    children: list[int] = []
    original_fork = linux_backend.os.fork

    def tracking_fork() -> int:
        child = original_fork()
        if os.getpid() == parent_pid and child > 0:
            children.append(child)
        return child

    def fail_pidfd(_pid: int, _flags: int = 0) -> int:
        raise OSError(errno.EMFILE, "injected x32 pidfd failure")

    monkeypatch.setattr(linux_backend.os, "fork", tracking_fork)
    monkeypatch.setattr(linux_backend.os, "pidfd_open", fail_pidfd)
    with pytest.raises(OSError, match="injected x32 pidfd failure"):
        linux_backend._seccomp_process_controls()
    assert set(os.listdir("/proc/self/fd")) == before_fds
    assert children
    for child in children:
        with pytest.raises(ChildProcessError):
            os.waitpid(child, os.WNOHANG)


def test_seccomp_nested_wait_failure_still_reaps_pidfd_bound_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before_fds = set(os.listdir("/proc/self/fd"))
    child = os.fork()
    if child == 0:
        os._exit(0)

    def fail_wait(_pid: int, *, timeout: float, include_stops: bool = False) -> int:
        raise OSError(errno.EIO, "injected nested wait failure")

    monkeypatch.setattr(linux_backend, "_bounded_waitpid_status", fail_wait)
    with pytest.raises(OSError, match="injected nested wait failure"):
        linux_backend._bounded_seccomp_nested_child(child, lambda _status: True)
    with pytest.raises(ChildProcessError):
        os.waitpid(child, os.WNOHANG)
    assert set(os.listdir("/proc/self/fd")) == before_fds


def test_prepared_close_accumulates_failure_and_continues_all_descriptors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_read, root_write = os.pipe2(os.O_CLOEXEC)
    source_read, source_write = os.pipe2(os.O_CLOEXEC)
    sealed = linux_backend._SealedFile(
        expected=object(),  # type: ignore[arg-type]
        source_fd=source_read,
        sealed_fd=source_write,
        source_identity={},
        sealed_identity={},
    )
    prepared = linux_backend._PreparedRequest(
        request=object(),  # type: ignore[arg-type]
        root_fds=((object(), root_read),),  # type: ignore[arg-type]
        entrypoint=sealed,
        interpreter=None,
        loader=None,
    )
    original_close = linux_backend.os.close
    failed = False

    def fail_one(descriptor: int) -> None:
        nonlocal failed
        if descriptor == root_read and not failed:
            failed = True
            raise OSError(errno.EIO, "injected prepared close failure")
        original_close(descriptor)

    monkeypatch.setattr(linux_backend.os, "close", fail_one)
    try:
        with pytest.raises(linux_backend.CleanupIncomplete, match="prepared-request"):
            prepared.close()
        assert prepared.root_fds == ()
        assert sealed.source_fd == -1 and sealed.sealed_fd == -1
        for descriptor in (source_read, source_write):
            with pytest.raises(OSError):
                os.fstat(descriptor)
    finally:
        monkeypatch.setattr(linux_backend.os, "close", original_close)
        for descriptor in (root_read, root_write):
            try:
                original_close(descriptor)
            except OSError:
                pass


@pytest.mark.parametrize("terminal_kind", ("workload_exit", "limit"))
def test_complete_report_batch_consumes_ack_and_event_after_terminal(
    terminal_kind: str,
) -> None:
    records = (
        {"kind": terminal_kind},
        {"kind": "member_birth", "id": 1},
        {"kind": "member_exit_stop", "id": 2},
        {"kind": "secondary_exec_denial", "id": 3},
        {"kind": "process_event", "event_classes": ["exit_stop"]},
    )
    buffer = bytearray(
        b"".join(
            json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"
            for value in records
        )
    )
    acknowledged: list[int] = []
    events: list[str] = []

    def consume(value: dict[str, object]) -> bool:
        kind = value["kind"]
        if kind in {"member_birth", "member_exit_stop", "secondary_exec_denial"}:
            acknowledged.append(int(value["id"]))
        if kind == "process_event":
            events.extend(str(item) for item in value["event_classes"])
        return kind in {"workload_exit", "limit"}

    assert linux_backend._consume_json_line_batch(buffer, consume) is True
    assert acknowledged == [1, 2, 3]
    assert events == ["exit_stop"]
    assert buffer == b""


@pytest.mark.parametrize("terminal", ("timeout", "limit"))
def test_queued_earlier_exit_cannot_be_swallowed_by_selected_terminal(
    terminal: str,
) -> None:
    record = linux_backend._RunRecord(started_ns=1)
    if terminal == "timeout":
        linux_backend._select_timeout_terminal(record, 100)
    else:
        linux_backend._select_limit_terminal(record, 100)
    value = {
        "kind": "workload_exit",
        "exit_code": 0,
        "exit_observed_monotonic_ns": 99,
        "event_classes": ["exit"],
    }
    with pytest.raises(
        linux_backend.ObservationLoss,
        match=f"selected {terminal} boundary",
    ):
        linux_backend._record_workload_exit(
            record,
            value,
            deadline_ns=100,
            provider_observed_ns=101,
        )


def test_post_terminal_exit_is_validated_but_does_not_replace_outcome() -> None:
    record = linux_backend._RunRecord(started_ns=1)
    linux_backend._select_timeout_terminal(record, 100)
    linux_backend._record_workload_exit(
        record,
        {
            "kind": "workload_exit",
            "exit_code": 137,
            "exit_observed_monotonic_ns": 101,
            "event_classes": ["signal_exit"],
        },
        deadline_ns=100,
        provider_observed_ns=102,
    )
    assert record.timeout_triggered is True
    assert record.limit_triggered is False
    assert record.workload_exit_code is None
    assert record.process["timeout_trigger_monotonic_ns"] == 100
    assert "workload_exit_monotonic_ns" not in record.process
    assert record.exit_observation["exit_observed_monotonic_ns"] == 101


def test_selected_terminal_does_not_skip_exit_timestamp_validation() -> None:
    record = linux_backend._RunRecord(started_ns=1)
    linux_backend._select_timeout_terminal(record, 100)
    with pytest.raises(linux_backend.ObservationLoss, match="malformed"):
        linux_backend._record_workload_exit(
            record,
            {
                "kind": "workload_exit",
                "exit_code": 137,
                "exit_observed_monotonic_ns": None,
                "event_classes": ["signal_exit"],
            },
            deadline_ns=100,
            provider_observed_ns=102,
        )


def test_linux_backend_hosted_real_isolation(tmp_path: Path) -> None:
    if not _is_github_hosted():
        print(
            HOSTED_RESULT_PREFIX
            + '{"capability_pass":false,"disposition":"NOT_EXECUTED"}'
        )
        return
    if os.geteuid() != 0:
        command = [
            "/usr/bin/sudo",
            "-n",
            "--",
            "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1",
            f"{ROOT_MARKER}=1",
            "GITHUB_ACTIONS=true",
            "RUNNER_ENVIRONMENT=github-hosted",
            "RUNNER_OS=Linux",
            "RUNNER_ARCH=X64",
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "-s",
            str(Path(__file__).resolve()),
            "-k",
            "test_linux_backend_hosted_real_isolation",
        ]
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90,
        )
        assert completed.returncode == 0, (
            completed.stdout.decode("utf-8", "replace")
            + completed.stderr.decode("utf-8", "replace")
        )
        assert HOSTED_RESULT_PREFIX.encode() in completed.stdout
        assert b'"disposition":"HOSTED_IMPLEMENTATION_PASS"' in completed.stdout
        return

    assert os.environ.get(ROOT_MARKER) == "1"
    assert platform.system() == "Linux"
    assert platform.machine() == "x86_64"
    binary = _compile_fixture(
        tmp_path,
        r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    errno = 0;
    if (syscall(470, 0, 0, 0, 0, 0, 0) != -1 || errno != EPERM) return 47;
    errno = 0;
    if (socket(AF_INET, SOCK_STREAM, 0) != -1 || errno != EPERM) return 31;
    errno = 0;
    if (open("/etc/passwd", O_RDONLY) != -1 || errno != ENOENT) return 32;
    int input_fd = open("/inputs/fixture/workload", O_RDONLY);
    if (input_fd < 0) return 38;
    int available = 0;
    errno = 0;
    if (ioctl(input_fd, FIONREAD, &available) != -1 || errno != EPERM) return 39;
    errno = 0;
    if (fcntl(input_fd, F_SETFL, O_NONBLOCK) != -1 || errno != EPERM) return 40;
    if (fcntl(input_fd, F_GETFL) < 0) return 41;
    if (close(input_fd) != 0) return 42;
    int pipefds[2];
    errno = 0;
    if (pipe2(pipefds, 0x4000) != -1 || errno != EPERM) return 43;
    errno = 0;
    if (pipe2(pipefds, 0x80) != -1 || errno != EPERM) return 44;
    if (pipe2(pipefds, 0) != 0) return 45;
    if (close(pipefds[0]) != 0 || close(pipefds[1]) != 0) return 46;
    int fd = open("/output/result.txt", O_WRONLY | O_TRUNC);
    if (fd < 0) return 33;
    if (write(fd, "retained\n", 9) != 9) return 34;
    if (close(fd) != 0) return 35;
    errno = 0;
    if (open("/output/undeclared.txt", O_WRONLY | O_CREAT | O_EXCL, 0600) != -1
        || errno != EACCES) return 37;
    if (write(STDOUT_FILENO, "ISOLATED_OK\n", 12) != 12) return 36;
    return 0;
}
'''.lstrip(),
    )
    request = _request(binary)
    request = replace(
        request,
        process=replace(request.process, max_processes=3),
    )
    evidence = LinuxNativeSupervisorV1().execute(request)
    validation = validate_execution_evidence_v1(request, evidence)
    assert evidence.outcome is ExecutionOutcomeV1.SUCCESS, evidence.to_record()
    assert evidence.complete is True, validation.reasons
    assert validation.ok is True, validation.reasons
    assert evidence.filesystem.retained_outputs[0].sha256 == hashlib.sha256(
        b"retained\n"
    ).hexdigest()
    assert evidence.network.inherited_network_fd_absent_at_exec is True
    assert evidence.streams.pipe_capacity_bytes == 4096
    assert evidence.process.secondary_exec_denials == ()
    assert evidence.process.observed_pids_max == 3
    assert "exec_denied" not in evidence.process.event_classes
    exec_payload = next(
        item.payload()
        for item in evidence.observations
        if item.event_id == "exec.ptrace"
    )
    assert exec_payload["core_soft_limit"] == 0
    assert exec_payload["core_hard_limit"] == 0
    assert evidence.process.current_execution_survivor_count == 0
    print(
        HOSTED_RESULT_PREFIX
        + '{"capability_pass":true,"disposition":"HOSTED_IMPLEMENTATION_PASS"}',
        flush=True,
    )
