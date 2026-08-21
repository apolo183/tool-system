from __future__ import annotations

import ctypes
import array
import errno
import fcntl
import hashlib
import json
import mmap
import os
import platform
import re
import resource
import select
import selectors
import shutil
import signal
import socket
import stat
import struct
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Callable, Final, Mapping

from .contract import (
    CLONE_NAMESPACE_FLAGS_MASK_V1,
    FCNTL_DENIED_COMMANDS_V1,
    FUTEX_PRIVATE_FLAG_V1,
    PIPE2_DENIED_FLAGS_V1,
    LINUX_NATIVE_SUPERVISOR_V1,
    MAX_PRIVATE_FILESYSTEM_INODES_V1,
    NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1,
    REQUIRED_CAPABILITY_SET_SHA256_V1,
    REQUIRED_OBSERVATION_CLASSES_V1,
    ExecutableFormatV1,
    ExpectedFileIdentityV1,
    IsolationRequestV1,
    ObservationClassV1,
    ReadOnlyRootV1,
    SOCKET_DENIAL_FILTER_ROWS_V1,
    SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1,
    SOCKET_DENIAL_FILTER_SHA256_V1,
    X32_SYSCALL_BIT_V1,
    canonical_sha256,
    validate_isolation_request_v1,
)
from .evidence import (
    FILESYSTEM_QUOTA_FD_TARGET_REGISTERS_X86_64_V1,
    FILESYSTEM_QUOTA_FD_WRITE_SYSCALLS_X86_64_V1,
    ISOLATION_EVIDENCE_SCHEMA_V1,
    REQUIRED_MEMFD_SEALS_V1,
    REQUIRED_OBSERVATION_EVENTS_V1,
    STREAM_PIPE_CAPACITY_BYTES_V1,
    CleanupEvidenceV1,
    CorrelationEvidenceV1,
    EvidenceCompletenessV1,
    EvidenceStageStatusV1,
    EvidenceStageV1,
    ExecChainEvidenceV1,
    ExecutionEvidenceV1,
    ExecutionOutcomeV1,
    FilesystemEvidenceV1,
    FilesystemLimitKindV1,
    FilesystemLimitObservationV1,
    FilesystemLimitScopeV1,
    NetworkEvidenceV1,
    OSObservationV1,
    ObservedFileIdentityV1,
    PrivateMountQuotaEvidenceV1,
    ProcessEvidenceV1,
    ProcessMemberEvidenceV1,
    ReadOnlyRootScanEvidenceV1,
    SecondaryExecDenialEvidenceV1,
    StageDependencyV1,
    StreamCountV1,
    StreamDecodingStatusV1,
    StreamEvidenceV1,
    _build_execution_evidence_v1,
)


BACKEND_PROFILE: Final = LINUX_NATIVE_SUPERVISOR_V1
REQUIRED_CAPABILITY_SET_DIGEST: Final = REQUIRED_CAPABILITY_SET_SHA256_V1

CGROUP_ROOT: Final = Path("/sys/fs/cgroup")
CGROUP_CHILDREN: Final = ("composition", "combined-stream", "timeout")
POLL_SECONDS: Final = 0.01
MAX_FAILURE_TEXT: Final = 2_048
MAX_SECONDARY_EXEC_DENIALS: Final = 256

CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
REQUIRED_NAMESPACE_FLAGS = (
    CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS
)

MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_NOEXEC = 8
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
PTRACE_PEEKDATA = 2
PTRACE_CONT = 7
PTRACE_KILL = 8
PTRACE_SYSCALL = 24
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_SETOPTIONS = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_GETSIGINFO = 0x4202
PTRACE_O_TRACEFORK = 0x02
PTRACE_O_TRACESYSGOOD = 0x01
PTRACE_O_TRACEVFORK = 0x04
PTRACE_O_TRACECLONE = 0x08
PTRACE_O_TRACEEXEC = 0x10
PTRACE_O_TRACEEXIT = 0x40
PTRACE_O_EXITKILL = 0x00100000
PTRACE_EVENT_FORK = 1
PTRACE_EVENT_VFORK = 2
PTRACE_EVENT_CLONE = 3
PTRACE_EVENT_EXEC = 4
PTRACE_EVENT_EXIT = 6

PR_SET_NO_NEW_PRIVS = 38
PR_SET_PDEATHSIG = 1
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_ALLOW = 0x7FFF0000
AUDIT_ARCH_X86_64 = 0xC000003E
NR_SOCKET_X86_64 = 41
NR_PTRACE_X86_64 = 101
NR_MOUNT_X86_64 = 165
NR_UMOUNT2_X86_64 = 166
NR_PIVOT_ROOT_X86_64 = 155
NR_UNSHARE_X86_64 = 272
NR_SETNS_X86_64 = 308
NR_BPF_X86_64 = 321

SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914
IFF_UP = 0x1

F_ADD_SEALS = 1033
F_GET_SEALS = 1034
F_SEAL_SEAL = 0x0001
F_SEAL_SHRINK = 0x0002
F_SEAL_GROW = 0x0004
F_SEAL_WRITE = 0x0008
REQUIRED_FILE_SEALS = F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE

STAGE_PASS = "PASS"
STAGE_FAIL = "FAIL"
STAGE_NOT_REACHED = "NOT_REACHED"

_LIBC = ctypes.CDLL(None, use_errno=True)
_LIBC.ptrace.restype = ctypes.c_long

_QUOTA_FD_TARGET_REGISTER_BY_SYSCALL: Final = dict(
    FILESYSTEM_QUOTA_FD_TARGET_REGISTERS_X86_64_V1
)
# Pathname lookup can cross a symlink, rename boundary, or mount after the
# ptrace entry stop.  V1 therefore never attributes a path-backed quota errno
# to a private scope.  We still recognize every mutating path syscall so such
# an errno fails evidence closed instead of being misreported as SUCCESS.
_UNATTRIBUTED_PATH_QUOTA_SYSCALLS_X86_64: Final = frozenset(
    (2, 76, 82, 83, 85, 86, 88, 133, 257, 258, 259, 264, 265, 266, 316, 437)
)

_MOUNTINFO_ESCAPE_RE = re.compile(r"\\(040|011|012|134)")


def _mountinfo_unescape(value: str) -> str:
    mapping = {"040": " ", "011": "\t", "012": "\n", "134": "\\"}
    return _MOUNTINFO_ESCAPE_RE.sub(lambda match: mapping[match.group(1)], value)


def _provider_proc_root() -> Path:
    private = Path("/run/tool-system-provider/proc")
    return private if private.is_dir() else Path("/proc")


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


class UserRegsStructX86_64(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_ulonglong)
        for name in (
            "r15", "r14", "r13", "r12", "rbp", "rbx", "r11", "r10",
            "r9", "r8", "rax", "rcx", "rdx", "rsi", "rdi", "orig_rax",
            "rip", "cs", "eflags", "rsp", "ss", "fs_base", "gs_base",
            "ds", "es", "fs", "gs",
        )
    ]


class IsolationBackendError(RuntimeError):
    """Stable base for fail-closed backend errors."""


class CapabilityBlocker(IsolationBackendError):
    """A required host capability was absent before workload release."""


class IdentityMismatch(IsolationBackendError):
    """A selected, sealed, or observed object did not match its request."""


class ObservationLoss(IsolationBackendError):
    """A mandatory current-run OS observation was unavailable."""


class CleanupIncomplete(IsolationBackendError):
    """Owned resources could not be proved absent after execution."""


class InvalidIsolationRequest(IsolationBackendError):
    """The typed request failed total validation before any OS side effect."""


def _bounded_failure(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"[-MAX_FAILURE_TEXT:]


def _raise_errno(operation: str) -> None:
    number = ctypes.get_errno()
    raise OSError(number, f"{operation}: {os.strerror(number)}")


def _mount(
    source: str | None,
    target: str | Path,
    fs_type: str | None,
    flags: int,
    data: str | None = None,
) -> None:
    result = _LIBC.mount(
        os.fsencode(source) if source is not None else None,
        os.fsencode(target),
        os.fsencode(fs_type) if fs_type is not None else None,
        ctypes.c_ulong(flags),
        os.fsencode(data) if data is not None else None,
    )
    if result != 0:
        _raise_errno(f"mount({target})")


def _umount(target: str | Path, flags: int = 0) -> None:
    if _LIBC.umount2(os.fsencode(target), flags) != 0:
        _raise_errno(f"umount2({target})")


def _unshare(flags: int) -> None:
    if _LIBC.unshare(ctypes.c_int(flags)) != 0:
        _raise_errno("unshare")


def _pivot_root(new_root: str | Path, old_root: str | Path) -> None:
    if _LIBC.syscall(
        SYS_PIVOT_ROOT_X86_64,
        os.fsencode(new_root),
        os.fsencode(old_root),
    ) != 0:
        _raise_errno("pivot_root")


def _openat2(
    dirfd: int,
    path: str,
    *,
    flags: int = os.O_RDONLY | os.O_CLOEXEC,
    resolve: int,
) -> int:
    how = OpenHow(flags=flags, mode=0, resolve=resolve)
    descriptor = _LIBC.syscall(
        SYS_OPENAT2_X86_64,
        dirfd,
        path.encode("utf-8"),
        ctypes.byref(how),
        ctypes.sizeof(how),
    )
    if descriptor < 0:
        _raise_errno(f"openat2({path})")
    return int(descriptor)


def _execveat(
    descriptor: int,
    argv: tuple[str, ...],
    environment: Mapping[str, str],
) -> None:
    argv_bytes = [value.encode("utf-8") for value in argv]
    env_bytes = [
        f"{name}={value}".encode("utf-8")
        for name, value in sorted(environment.items())
    ]
    argv_array = (ctypes.c_char_p * (len(argv_bytes) + 1))(*argv_bytes, None)
    env_array = (ctypes.c_char_p * (len(env_bytes) + 1))(*env_bytes, None)
    result = _LIBC.syscall(
        SYS_EXECVEAT_X86_64,
        descriptor,
        ctypes.c_char_p(b""),
        argv_array,
        env_array,
        AT_EMPTY_PATH,
    )
    if result != 0:
        _raise_errno("execveat")


def _sha256_fd(descriptor: int, *, deadline_ns: int | None = None) -> str:
    original = os.lseek(descriptor, 0, os.SEEK_CUR)
    digest = hashlib.sha256()
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        while True:
            if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
                raise CapabilityBlocker("deadline elapsed while hashing selected input")
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)
    finally:
        os.lseek(descriptor, original, os.SEEK_SET)


def _identity_from_stat(value: os.stat_result, digest: str) -> dict[str, object]:
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "mode": value.st_mode,
        "size": value.st_size,
        "sha256": digest,
    }


def _fd_identity(
    descriptor: int, *, deadline_ns: int | None = None
) -> dict[str, object]:
    return _identity_from_stat(
        os.fstat(descriptor), _sha256_fd(descriptor, deadline_ns=deadline_ns)
    )


def _identity_matches_expected(
    actual: Mapping[str, object], expected: ExpectedFileIdentityV1
) -> bool:
    return all(
        actual[key] == value
        for key, value in (
            ("device", expected.device),
            ("inode", expected.inode),
            ("mode", expected.mode),
            ("size", expected.size),
            ("sha256", expected.sha256),
        )
    )


@dataclass
class _SealedFile:
    expected: ExpectedFileIdentityV1
    source_fd: int
    sealed_fd: int
    source_identity: dict[str, object]
    sealed_identity: dict[str, object]

    def close(self) -> None:
        failures: list[str] = []
        for name in ("source_fd", "sealed_fd"):
            descriptor = getattr(self, name)
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    failures.append(f"{name}: {_bounded_failure(exc)}")
                finally:
                    setattr(self, name, -1)
        if failures:
            raise CleanupIncomplete(
                "sealed-file descriptor cleanup failed: " + "; ".join(failures)
            )


def _safe_absolute_open(path: str, *, directory: bool = False) -> int:
    if not path.startswith("/") or path.startswith("//") or path == "/":
        raise IdentityMismatch(f"unsafe absolute selection path: {path!r}")
    root_fd = os.open("/", O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    flags = (
        O_PATH | os.O_CLOEXEC
        if directory
        else os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC
    )
    if directory:
        flags |= os.O_DIRECTORY
    try:
        return _openat2(
            root_fd,
            path.removeprefix("/"),
            flags=flags,
            resolve=RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
        )
    finally:
        os.close(root_fd)


def _seal_expected_file(
    expected: ExpectedFileIdentityV1,
    *,
    deadline_ns: int | None = None,
    source_descriptor: int | None = None,
) -> _SealedFile:
    source_fd = (
        source_descriptor
        if source_descriptor is not None
        else _safe_absolute_open(expected.source_path)
    )
    sealed_fd = -1
    try:
        source_stat_before = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat_before.st_mode):
            raise IdentityMismatch("selected object is not a regular file")
        source_identity = _fd_identity(source_fd, deadline_ns=deadline_ns)
        source_stat_after = os.fstat(source_fd)
        if (
            source_stat_before.st_dev,
            source_stat_before.st_ino,
            source_stat_before.st_size,
            source_stat_before.st_mtime_ns,
            source_stat_before.st_ctime_ns,
        ) != (
            source_stat_after.st_dev,
            source_stat_after.st_ino,
            source_stat_after.st_size,
            source_stat_after.st_mtime_ns,
            source_stat_after.st_ctime_ns,
        ):
            raise IdentityMismatch("selected object changed while hashing")
        if not _identity_matches_expected(source_identity, expected):
            raise IdentityMismatch(
                f"selected identity does not match request: {expected.source_path}"
            )
        try:
            os.getxattr(source_fd, "security.capability")
        except OSError as exc:
            if exc.errno not in {errno.ENODATA, errno.ENOTSUP, errno.EOPNOTSUPP}:
                raise ObservationLoss("file capability observation failed") from exc
        else:
            raise IdentityMismatch("selected object carries file capabilities")
        if source_stat_before.st_mode & (stat.S_ISUID | stat.S_ISGID):
            raise IdentityMismatch("set-id selected objects are forbidden")

        sealed_fd = os.memfd_create(
            f"ts-b02a-{expected.file_type.value}",
            os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING,
        )
        os.lseek(source_fd, 0, os.SEEK_SET)
        remaining = expected.size
        while remaining:
            if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
                raise CapabilityBlocker("deadline elapsed while sealing selected input")
            chunk = os.read(source_fd, min(65_536, remaining))
            if not chunk:
                raise IdentityMismatch("selected object became short while sealing")
            view = memoryview(chunk)
            while view:
                written = os.write(sealed_fd, view)
                if written <= 0:
                    raise ObservationLoss("short memfd seal write")
                view = view[written:]
            remaining -= len(chunk)
        if os.read(source_fd, 1):
            raise IdentityMismatch("selected object grew while sealing")
        # The immutable seal, rather than mutable permission-bit rewriting,
        # supplies the write prohibition.  Keeping the requested mode lets the
        # exec-stop identity match the selected executable exactly.
        os.fchmod(sealed_fd, stat.S_IMODE(expected.mode))
        fcntl.fcntl(sealed_fd, F_ADD_SEALS, REQUIRED_FILE_SEALS)
        if fcntl.fcntl(sealed_fd, F_GET_SEALS) != REQUIRED_FILE_SEALS:
            raise ObservationLoss("immutable memfd seal set is incomplete")
        sealed_identity = _fd_identity(sealed_fd, deadline_ns=deadline_ns)
        if sealed_identity["sha256"] != expected.sha256:
            raise IdentityMismatch("sealed digest differs from expected digest")
        return _SealedFile(
            expected=expected,
            source_fd=source_fd,
            sealed_fd=sealed_fd,
            source_identity=source_identity,
            sealed_identity=sealed_identity,
        )
    except BaseException as original:
        cleanup_failures: list[str] = []
        for label, descriptor in (
            ("source", source_fd),
            ("sealed", sealed_fd),
        ):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(
                        f"{label}: {_bounded_failure(exc)}"
                    )
        if cleanup_failures:
            raise CleanupIncomplete(
                "sealed-file acquisition cleanup failed: "
                + "; ".join(cleanup_failures)
            ) from original
        raise


def _read_pt_interp(descriptor: int) -> str | None:
    original = os.lseek(descriptor, 0, os.SEEK_CUR)
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        header = os.read(descriptor, 64)
        if len(header) < 64 or header[:4] != b"\x7fELF" or header[4] != 2:
            raise IdentityMismatch("entrypoint is not ELF64")
        if header[5] not in {1, 2}:
            raise IdentityMismatch("ELF byte order is unsupported")
        endian = "<" if header[5] == 1 else ">"
        machine = struct.unpack_from(endian + "H", header, 18)[0]
        if machine != 62:
            raise IdentityMismatch("ELF machine is not x86_64")
        phoff = struct.unpack_from(endian + "Q", header, 32)[0]
        phentsize = struct.unpack_from(endian + "H", header, 54)[0]
        phnum = struct.unpack_from(endian + "H", header, 56)[0]
        if phentsize < 56 or phnum > 4_096:
            raise IdentityMismatch("ELF program-header table is invalid")
        for index in range(phnum):
            os.lseek(descriptor, phoff + index * phentsize, os.SEEK_SET)
            row = os.read(descriptor, phentsize)
            if len(row) != phentsize:
                raise IdentityMismatch("ELF program-header table is truncated")
            if struct.unpack_from(endian + "I", row, 0)[0] != 3:
                continue
            offset = struct.unpack_from(endian + "Q", row, 8)[0]
            size = struct.unpack_from(endian + "Q", row, 32)[0]
            if size <= 1 or size > 4_096:
                raise IdentityMismatch("PT_INTERP length is invalid")
            os.lseek(descriptor, offset, os.SEEK_SET)
            raw = os.read(descriptor, size)
            if len(raw) != size or not raw.endswith(b"\0"):
                raise IdentityMismatch("PT_INTERP is truncated or unterminated")
            try:
                value = raw[:-1].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise IdentityMismatch("PT_INTERP is not UTF-8") from exc
            if not value.startswith("/") or os.path.normpath(value) != value:
                raise IdentityMismatch("PT_INTERP is not an absolute canonical path")
            return value
        return None
    finally:
        os.lseek(descriptor, original, os.SEEK_SET)


def _read_shebang(descriptor: int) -> str:
    original = os.lseek(descriptor, 0, os.SEEK_CUR)
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        first_line = os.read(descriptor, 4_096).split(b"\n", 1)[0]
    finally:
        os.lseek(descriptor, original, os.SEEK_SET)
    if not first_line.startswith(b"#!"):
        raise IdentityMismatch("script entrypoint lacks a shebang")
    try:
        rendered = first_line[2:].strip().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IdentityMismatch("script shebang is not UTF-8") from exc
    parts = rendered.split()
    if len(parts) != 1 or not parts[0].startswith("/"):
        raise IdentityMismatch("script shebang must name one absolute interpreter")
    return parts[0]


def _namespace_links(pid: str | int = "self") -> dict[str, str]:
    return {
        name: os.readlink(f"/proc/{pid}/ns/{name}")
        for name in ("mnt", "pid", "net", "ipc", "uts")
    }


def _wait_until(predicate, deadline_ns: int, description: str) -> None:
    while time.monotonic_ns() < deadline_ns:
        if predicate():
            return
        time.sleep(POLL_SECONDS)
    raise ObservationLoss(f"deadline expired while observing {description}")


def _cgroup_populated(path: Path) -> int:
    rows = dict(
        line.split(maxsplit=1)
        for line in (path / "cgroup.events").read_text(encoding="ascii").splitlines()
    )
    if rows.get("populated") not in {"0", "1"}:
        raise ObservationLoss(f"invalid cgroup.events at {path}")
    return int(rows["populated"])


def _cgroup_members(path: Path) -> tuple[int, ...]:
    return tuple(
        sorted(
            int(line)
            for line in (path / "cgroup.procs")
            .read_text(encoding="ascii")
            .splitlines()
            if line
        )
    )


def _cgroup_frozen(path: Path) -> int:
    rows = dict(
        line.split(maxsplit=1)
        for line in (path / "cgroup.events").read_text(encoding="ascii").splitlines()
    )
    if rows.get("frozen") not in {"0", "1"}:
        raise ObservationLoss(f"invalid cgroup frozen observation at {path}")
    return int(rows["frozen"])


def _set_cgroup_frozen(path: Path, frozen: bool) -> None:
    control = path / "cgroup.freeze"
    if not control.is_file():
        raise CapabilityBlocker(f"cgroup.freeze is unavailable: {path}")
    control.write_text("1" if frozen else "0", encoding="ascii")
    _wait_until(
        lambda: _cgroup_frozen(path) == int(frozen),
        time.monotonic_ns() + 2_000_000_000,
        f"{path} frozen={int(frozen)}",
    )


def _proc_cgroup(pid: int) -> str:
    rows = (_provider_proc_root() / str(pid) / "cgroup").read_text(
        encoding="ascii"
    ).splitlines()
    unified = [row[3:] for row in rows if row.startswith("0::")]
    if len(unified) != 1:
        raise ObservationLoss(f"PID {pid} has no unique unified cgroup")
    return unified[0]


def _validate_cgroup2_host_gate() -> dict[str, object]:
    matching = [
        row
        for row in Path("/proc/self/mountinfo")
        .read_text(encoding="utf-8")
        .splitlines()
        if _mountinfo_unescape(row.split()[4]) == str(CGROUP_ROOT)
    ]
    if len(matching) != 1:
        raise CapabilityBlocker("cgroup root mount identity is ambiguous")
    left, right = matching[0].split(" - ", 1)
    left_columns = left.split()
    right_columns = right.split()
    current = _proc_cgroup(os.getpid())
    if (
        right_columns[0] != "cgroup2"
        or "rw" not in left_columns[5].split(",")
        or not current.startswith("/")
        or not (CGROUP_ROOT / "cgroup.controllers").is_file()
        or not os.access(CGROUP_ROOT, os.W_OK)
    ):
        raise CapabilityBlocker("writable unified cgroup2 delegation is unavailable")
    return {
        "filesystem_type": right_columns[0],
        "mount_root": left_columns[3],
        "mountpoint": left_columns[4],
        "current_unified_cgroup": current,
        "mount_id": int(left_columns[0]),
        "writable": True,
    }


def _validate_core_pattern_host_gate() -> bool:
    """Reject host configurations that pipe workload crashes to a helper."""

    descriptor = _openat2(
        AT_FDCWD,
        "/proc/sys/kernel/core_pattern",
        flags=os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK,
        resolve=RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    )
    try:
        payload = os.read(descriptor, 4_097)
        if len(payload) > 4_096 or os.read(descriptor, 1):
            raise CapabilityBlocker("host core_pattern exceeded its strict bound")
    finally:
        os.close(descriptor)
    if not payload:
        raise CapabilityBlocker("host core_pattern was empty")
    if payload.startswith(b"|"):
        raise CapabilityBlocker("host core_pattern invokes a pipe helper")
    return True


def _proc_starttime(pid: int) -> int:
    payload = (_provider_proc_root() / str(pid) / "stat").read_text(
        encoding="ascii"
    )
    try:
        return int(payload.rsplit(") ", 1)[1].split()[19])
    except (IndexError, ValueError) as exc:
        raise ObservationLoss(f"invalid /proc/{pid}/stat") from exc


@dataclass
class _BoundPid:
    pid: int
    starttime: int
    cgroup: str
    pidfd: int

    @classmethod
    def bind(cls, pid: int, expected_cgroup: str) -> _BoundPid:
        before = _proc_starttime(pid)
        pidfd = os.pidfd_open(pid)
        try:
            after = _proc_starttime(pid)
            actual_cgroup = _proc_cgroup(pid)
            if before != after or actual_cgroup != expected_cgroup:
                raise ObservationLoss(f"PID {pid} identity changed during pidfd bind")
            return cls(pid, after, actual_cgroup, pidfd)
        except BaseException:
            os.close(pidfd)
            raise

    def revalidate(self) -> None:
        if (
            _proc_starttime(self.pid) != self.starttime
            or _proc_cgroup(self.pid) != self.cgroup
        ):
            raise ObservationLoss(f"PID {self.pid} identity changed after pidfd bind")

    def readable(self, timeout: float = 0.0) -> bool:
        selector = selectors.DefaultSelector()
        try:
            selector.register(self.pidfd, selectors.EVENT_READ)
            return bool(selector.select(timeout=timeout))
        finally:
            selector.close()

    def close(self) -> None:
        if self.pidfd >= 0:
            os.close(self.pidfd)
            self.pidfd = -1


def _bounded_kill_and_reap(pid: int, pidfd: int, timeout: float = 2.0) -> None:
    """Pidfd-kill then bounded-reap, or only reap when binding was unavailable."""

    if pid <= 0:
        return
    if pidfd >= 0:
        poller = select.poll()
        poller.register(pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
        if not poller.poll(0):
            signal.pidfd_send_signal(pidfd, signal.SIGKILL, None, 0)
            if not poller.poll(max(1, int(timeout * 1_000))):
                raise CleanupIncomplete("owned child pidfd did not become readable")
    deadline_ns = time.monotonic_ns() + int(timeout * 1_000_000_000)
    while True:
        try:
            waited, _ = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return
        if waited == pid:
            return
        if time.monotonic_ns() >= deadline_ns:
            raise CleanupIncomplete("owned child reap exceeded its bound")
        time.sleep(POLL_SECONDS)


def _bounded_waitpid_status(
    pid: int, *, timeout: float, include_stops: bool = False
) -> int:
    deadline_ns = time.monotonic_ns() + int(timeout * 1_000_000_000)
    options = os.WNOHANG | (os.WUNTRACED if include_stops else 0)
    while time.monotonic_ns() < deadline_ns:
        try:
            waited, status_value = os.waitpid(pid, options)
        except ChildProcessError as exc:
            raise ObservationLoss("owned child disappeared before wait observation") from exc
        if waited == pid:
            return status_value
        time.sleep(POLL_SECONDS)
    raise CapabilityBlocker("owned synthetic child wait exceeded its bound")


@dataclass
class _OwnedCgroupTree:
    execution_id: str
    nonce: str
    parent: Path = field(init=False)
    children: dict[str, Path] = field(init=False)
    identities: dict[str, tuple[int, int]] = field(default_factory=dict)
    created_paths: list[Path] = field(default_factory=list)
    observed_pids_max: int | None = None

    def __post_init__(self) -> None:
        if (
            not self.execution_id
            or len(self.execution_id) > 64
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in self.execution_id)
        ):
            raise CapabilityBlocker("execution_id is not a safe cgroup component")
        self.parent = CGROUP_ROOT / self.execution_id
        self.children = {
            name: self.parent / name for name in CGROUP_CHILDREN
        }

    @property
    def exact_paths(self) -> tuple[Path, ...]:
        return (self.parent, *(self.children[name] for name in CGROUP_CHILDREN))

    def claim(self, max_processes: int) -> None:
        if not (CGROUP_ROOT / "cgroup.controllers").is_file():
            raise CapabilityBlocker("unified cgroup v2 is unavailable")
        if self.parent.exists():
            raise CapabilityBlocker(f"cgroup collision: {self.parent}")
        self.parent.mkdir()
        self.created_paths.append(self.parent)
        value = os.stat(self.parent)
        self.identities[str(self.parent)] = (value.st_dev, value.st_ino)
        controllers = set(
            (self.parent / "cgroup.controllers")
            .read_text(encoding="ascii")
            .split()
        )
        if "pids" not in controllers:
            raise CapabilityBlocker("pids controller is unavailable")
        (self.parent / "cgroup.subtree_control").write_text(
            "+pids", encoding="ascii"
        )
        for path in self.children.values():
            if path.exists():
                raise CapabilityBlocker(f"cgroup collision: {path}")
            path.mkdir()
            self.created_paths.append(path)
            value = os.stat(path)
            self.identities[str(path)] = (value.st_dev, value.st_ino)
        (self.children["composition"] / "pids.max").write_text(
            str(max_processes), encoding="ascii"
        )
        raw_pids_max = (
            self.children["composition"] / "pids.max"
        ).read_text(encoding="ascii").strip()
        if not raw_pids_max.isdecimal() or int(raw_pids_max) != max_processes:
            raise CapabilityBlocker("composition pids.max read-back mismatched")
        self.observed_pids_max = int(raw_pids_max)
        for path in self.exact_paths:
            if not (path / "cgroup.events").is_file() or not (
                path / "cgroup.kill"
            ).is_file():
                raise CapabilityBlocker(f"cgroup kill/events unavailable: {path}")
            if not (path / "cgroup.freeze").is_file():
                raise CapabilityBlocker(f"cgroup freeze unavailable: {path}")
            if _cgroup_populated(path) != 0:
                raise CapabilityBlocker(f"new cgroup unexpectedly populated: {path}")

    def validate(self, path: Path) -> None:
        identity = self.identities.get(str(path))
        if identity is None or not path.is_dir():
            raise CleanupIncomplete(f"unclaimed cgroup cleanup refused: {path}")
        value = os.stat(path)
        if (value.st_dev, value.st_ino) != identity:
            raise CleanupIncomplete(f"cgroup identity changed: {path}")

    def kill(self, name: str) -> None:
        path = self.children[name]
        self.validate(path)
        (path / "cgroup.kill").write_text("1", encoding="ascii")

    def release(self) -> dict[str, object]:
        failures: list[str] = []
        released: list[str] = []
        claimed = list(self.created_paths)
        for path in reversed(claimed):
            try:
                if str(path) not in self.identities:
                    raise CleanupIncomplete(
                        f"created cgroup lacks authenticated identity: {path}"
                    )
                self.validate(path)
                if _cgroup_populated(path):
                    if path == self.parent:
                        raise CleanupIncomplete(
                            "parent cgroup populated; no-kill parent release refused"
                        )
                    (path / "cgroup.kill").write_text("1", encoding="ascii")
                    _wait_until(
                        lambda path=path: _cgroup_populated(path) == 0,
                        time.monotonic_ns() + 8_000_000_000,
                        f"{path} populated=0",
                    )
                if _cgroup_frozen(path):
                    _set_cgroup_frozen(path, False)
                if any(candidate.is_dir() for candidate in path.iterdir()):
                    raise CleanupIncomplete(f"unexpected child cgroup below {path}")
                path.rmdir()
                released.append(str(path))
            except BaseException as exc:
                failures.append(_bounded_failure(exc))
        residues = [str(path) for path in self.created_paths if path.exists()]
        if residues:
            failures.append(f"cgroup residues: {residues}")
        return {
            "exact_paths": [str(path) for path in self.exact_paths],
            "released_paths": released,
            "populated_zero": not residues and not failures,
            "failures": failures,
        }


@dataclass
class _RawStreams:
    stdout_limit: int
    stderr_limit: int
    combined_limit: int
    retained_limit: int
    # This is populated only from the final F_GETPIPE_SZ readback after the
    # complete workload cgroup has been killed.  A setup-time expectation is
    # deliberately not evidence of the terminal pipe capacity.
    pipe_capacity_bytes: int | None = None
    counts: dict[str, int] = field(
        default_factory=lambda: {"stdout": 0, "stderr": 0}
    )
    retained: dict[str, bytearray] = field(
        default_factory=lambda: {"stdout": bytearray(), "stderr": bytearray()}
    )
    trigger: str | None = None
    observer_loss: bool = False

    def next_read_size(self, name: str) -> int:
        if name not in self.counts:
            raise ObservationLoss(f"unknown stream: {name}")
        stream_limit = self.stdout_limit if name == "stdout" else self.stderr_limit
        stream_remaining = max(0, stream_limit - self.counts[name])
        combined_remaining = max(
            0, self.combined_limit - sum(self.counts.values())
        )
        # Read the first byte beyond the tightest remaining limit, then freeze.
        return max(1, min(65_535, stream_remaining, combined_remaining) + 1)

    def consume(self, name: str, payload: bytes) -> None:
        if name not in self.counts:
            self.observer_loss = True
            raise ObservationLoss(f"unknown stream: {name}")
        self.counts[name] += len(payload)
        combined_room = max(
            0,
            self.retained_limit
            - sum(len(value) for value in self.retained.values()),
        )
        stream_room = max(
            0,
            (self.stdout_limit if name == "stdout" else self.stderr_limit)
            - len(self.retained[name]),
        )
        room = min(combined_room, stream_room)
        self.retained[name].extend(payload[:room])
        if self.trigger is None and self.counts[name] > (
            self.stdout_limit if name == "stdout" else self.stderr_limit
        ):
            self.trigger = f"{name}_raw_byte_limit"
        if self.trigger is None and sum(self.counts.values()) > self.combined_limit:
            self.trigger = "combined_raw_byte_limit"

    def record(self) -> dict[str, object]:
        retained = {name: len(value) for name, value in self.retained.items()}
        discarded = {
            name: self.counts[name] - retained[name] for name in self.counts
        }
        try:
            self.retained["stdout"].decode("utf-8", "strict")
            self.retained["stderr"].decode("utf-8", "strict")
        except UnicodeDecodeError:
            decoding_status = "utf8_replaced"
        else:
            decoding_status = "utf8_valid"
        return {
            "raw_bytes": dict(self.counts),
            "combined_raw_bytes": sum(self.counts.values()),
            "retained_bytes": retained,
            "discarded_bytes": discarded,
            "trigger": self.trigger,
            "observer_loss": self.observer_loss,
            "decoding_status": decoding_status,
            "pipe_capacity_bytes": self.pipe_capacity_bytes,
        }


def _interface_flags(interface: str) -> int:
    request = bytearray(40)
    encoded = interface.encode("ascii")
    request[: len(encoded)] = encoded
    descriptor = _LIBC.socket(2, 2 | os.O_CLOEXEC, 0)
    if descriptor < 0:
        _raise_errno("socket(network-control)")
    try:
        fcntl.ioctl(descriptor, SIOCGIFFLAGS, request, True)
        return int(struct.unpack_from("H", request, 16)[0])
    finally:
        os.close(descriptor)


def _set_interface_flags(interface: str, flags: int) -> None:
    request = bytearray(40)
    encoded = interface.encode("ascii")
    request[: len(encoded)] = encoded
    struct.pack_into("H", request, 16, flags)
    descriptor = _LIBC.socket(2, 2 | os.O_CLOEXEC, 0)
    if descriptor < 0:
        _raise_errno("socket(network-control)")
    try:
        fcntl.ioctl(descriptor, SIOCSIFFLAGS, request, True)
    finally:
        os.close(descriptor)


def _seccomp_filter_identity(
    rows: tuple[tuple[int, int, int, int], ...],
) -> str:
    """Bind the published identity to the exact cBPF rows passed to prctl."""

    return canonical_sha256(
        {
            "version": "tool-system-seccomp-cbpf-v1",
            "native_syscall_exclusive_ceiling_x86_64": (
                NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
            ),
            "rows": [list(row) for row in rows],
        }
    )


def _install_seccomp_filter() -> str:
    # Wrong architecture is fatal.  X32 is killed; native syscall numbers at
    # or above the frozen v1 ceiling and audited control operations fail with
    # EPERM.  Only the audited native range can reach the conditional rules.
    row_values = tuple(SOCKET_DENIAL_FILTER_ROWS_V1)
    filter_identity = _seccomp_filter_identity(row_values)
    if filter_identity != SOCKET_DENIAL_FILTER_SHA256_V1:
        raise CapabilityBlocker("actual seccomp program identity drifted")
    rows = [SockFilter(*row) for row in row_values]
    instructions = (SockFilter * len(rows))(*rows)
    program = SockFprog(len=len(instructions), filter=instructions)
    if _LIBC.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        _raise_errno("prctl(PR_SET_NO_NEW_PRIVS)")
    if _LIBC.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(program)) != 0:
        _raise_errno("prctl(PR_SET_SECCOMP)")
    return filter_identity


def _close_unlisted_fds(keep: set[int]) -> None:
    try:
        descriptors = [
            int(entry.name)
            for entry in (_provider_proc_root() / "self" / "fd").iterdir()
            if entry.name.isdigit()
        ]
    except OSError as exc:
        raise ObservationLoss("could not enumerate inherited descriptors") from exc
    for descriptor in descriptors:
        if descriptor > 2 and descriptor not in keep:
            try:
                os.close(descriptor)
            except OSError as exc:
                if exc.errno != errno.EBADF:
                    raise


def _drop_workload_identity(request: IsolationRequestV1, keep: set[int]) -> None:
    _close_unlisted_fds(keep)
    os.umask(0o077)
    os.setgroups([])
    os.setgid(request.workload.gid)
    os.setuid(request.workload.uid)
    _install_seccomp_filter()


def _status_rows(pid: int) -> dict[str, str]:
    return {
        line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in (_provider_proc_root() / str(pid) / "status")
        .read_text(encoding="ascii")
        .splitlines()
        if ":" in line
    }


def _host_pid_for_namespace_member(
    namespace_pid: int,
    starttime_ticks: int,
    composition: Path,
    expected_cgroup: str,
    expected_pid_namespace: str,
) -> int:
    """Resolve a stopped PID-namespace task to one exact host PID."""

    matches: list[int] = []
    for host_pid in _cgroup_members(composition):
        try:
            rows = _status_rows(host_pid)
            namespace_ids = tuple(
                int(value) for value in rows.get("NSpid", "").split()
            )
            if (
                namespace_ids
                and namespace_ids[-1] == namespace_pid
                and os.readlink(f"/proc/{host_pid}/ns/pid")
                == expected_pid_namespace
                and _proc_starttime(host_pid) == starttime_ticks
                and _proc_cgroup(host_pid) == expected_cgroup
            ):
                matches.append(host_pid)
        except (OSError, ValueError, ObservationLoss):
            continue
    if len(matches) != 1:
        raise ObservationLoss(
            "namespace PID did not map to one exact host cgroup member"
        )
    bound = _BoundPid.bind(matches[0], expected_cgroup)
    try:
        if bound.starttime != starttime_ticks or bound.readable():
            raise ObservationLoss("mapped exec member identity was not stable")
    finally:
        bound.close()
    return matches[0]


def _translate_limit_member(
    value: dict[str, object],
    composition: Path,
    expected_cgroup: str,
    expected_pid_namespace: str,
) -> None:
    namespace_pid = value.get("pid")
    starttime_ticks = value.get("starttime_ticks")
    if not isinstance(namespace_pid, int) or not isinstance(starttime_ticks, int):
        raise ObservationLoss("filesystem-limit member identity is malformed")
    value["namespace_pid"] = namespace_pid
    value["pid"] = _host_pid_for_namespace_member(
        namespace_pid,
        starttime_ticks,
        composition,
        expected_cgroup,
        expected_pid_namespace,
    )


def _mandatory_abi_control() -> dict[str, object]:
    """Exercise pidfd signal, ptrace exec-stop, and execveat before release."""

    ready_read = -1
    ready_write = -1
    lifetime_read = -1
    lifetime_write = -1
    signal_child = -1
    signal_pidfd = -1
    signal_reaped = False
    ready_selector: selectors.BaseSelector | None = None
    executable_fd = -1
    trace_gate_read = -1
    trace_gate_write = -1
    trace_child = -1
    trace_pidfd = -1
    trace_reaped = False
    exec_event = False

    def close_owned(descriptor: int) -> int:
        if descriptor >= 0:
            os.close(descriptor)
        return -1

    try:
        ready_read, ready_write = os.pipe2(os.O_CLOEXEC)
        lifetime_read, lifetime_write = os.pipe2(os.O_CLOEXEC)
        signal_child = os.fork()
        if signal_child == 0:
            try:
                os.close(ready_read)
                os.close(lifetime_write)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                _write_all(ready_write, b"r")
                os.close(ready_write)
                os.read(lifetime_read, 1)
                os.close(lifetime_read)
            except BaseException:
                os._exit(126)
            os._exit(0)
        ready_write = close_owned(ready_write)
        lifetime_read = close_owned(lifetime_read)
        signal_pidfd = os.pidfd_open(signal_child)
        ready_selector = selectors.DefaultSelector()
        ready_selector.register(ready_read, selectors.EVENT_READ)
        became_ready = bool(ready_selector.select(timeout=2))
        ready_selector.close()
        ready_selector = None
        ready_payload = os.read(ready_read, 1) if became_ready else b""
        ready_read = close_owned(ready_read)
        if ready_payload != b"r":
            raise CapabilityBlocker("pidfd signal control did not become ready")
        signal.pidfd_send_signal(signal_pidfd, signal.SIGTERM, None, 0)
        if not _BoundPid(signal_child, 0, "", signal_pidfd).readable(2):
            raise CapabilityBlocker("pidfd signal control lacked exit readiness")
        signal_status = _bounded_waitpid_status(signal_child, timeout=2)
        signal_reaped = True
        if (
            not os.WIFSIGNALED(signal_status)
            or os.WTERMSIG(signal_status) != signal.SIGTERM
        ):
            raise CapabilityBlocker("pidfd signal control did not deliver SIGTERM")
        lifetime_write = close_owned(lifetime_write)
        signal_pidfd = close_owned(signal_pidfd)

        executable_fd = os.open("/proc/self/exe", os.O_RDONLY | os.O_CLOEXEC)
        trace_gate_read, trace_gate_write = os.pipe2(os.O_CLOEXEC)
        trace_child = os.fork()
        if trace_child == 0:
            try:
                os.close(trace_gate_write)
                if os.read(trace_gate_read, 1) != b"g":
                    os._exit(125)
                os.close(trace_gate_read)
                if _LIBC.ptrace(PTRACE_TRACEME, 0, None, None) != 0:
                    _raise_errno("ptrace synthetic TRACEME")
                os.kill(os.getpid(), signal.SIGSTOP)
                _execveat(
                    executable_fd,
                    ("python", "-I", "-S", "-c", "pass"),
                    {},
                )
            except BaseException:
                os._exit(126)
        trace_gate_read = close_owned(trace_gate_read)
        executable_fd = close_owned(executable_fd)
        trace_pidfd = os.pidfd_open(trace_child)
        _write_all(trace_gate_write, b"g")
        trace_gate_write = close_owned(trace_gate_write)
        status_value = _bounded_waitpid_status(
            trace_child, timeout=2, include_stops=True
        )
        if not os.WIFSTOPPED(status_value):
            raise CapabilityBlocker("ptrace synthetic child lacked initial stop")
        if _LIBC.ptrace(
            PTRACE_SETOPTIONS,
            trace_child,
            None,
            PTRACE_O_TRACEEXEC | PTRACE_O_EXITKILL,
        ) != 0:
            _raise_errno("ptrace synthetic SETOPTIONS")
        if _LIBC.ptrace(PTRACE_CONT, trace_child, None, None) != 0:
            _raise_errno("ptrace synthetic CONT")
        deadline_ns = time.monotonic_ns() + 5_000_000_000
        exit_status: int | None = None
        while time.monotonic_ns() < deadline_ns:
            waited, status_value = os.waitpid(trace_child, os.WNOHANG)
            if waited == 0:
                time.sleep(POLL_SECONDS)
                continue
            if os.WIFEXITED(status_value):
                exit_status = os.WEXITSTATUS(status_value)
                trace_reaped = True
                break
            if os.WIFSIGNALED(status_value):
                trace_reaped = True
                raise CapabilityBlocker("ptrace synthetic child was signaled")
            if os.WIFSTOPPED(status_value):
                if status_value >> 16 == PTRACE_EVENT_EXEC:
                    exec_event = True
                if _LIBC.ptrace(PTRACE_CONT, trace_child, None, None) != 0:
                    number = ctypes.get_errno()
                    if number != errno.ESRCH:
                        _raise_errno("ptrace synthetic CONT event")
        if not exec_event or exit_status != 0:
            raise CapabilityBlocker("execveat/ptrace synthetic control failed")
        return {
            "pidfd_send_signal": True,
            "ptrace_exec_event": exec_event,
            "execveat": True,
            "synthetic_only": True,
        }
    finally:
        cleanup_failures: list[str] = []
        if ready_selector is not None:
            try:
                ready_selector.close()
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        # Close every gate before waiting so a child that was never pidfd-bound
        # receives EOF and exits without an unsafe numeric-PID signal.
        for descriptor_name in (
            "ready_read",
            "ready_write",
            "lifetime_read",
            "lifetime_write",
            "executable_fd",
            "trace_gate_read",
            "trace_gate_write",
        ):
            descriptor = locals()[descriptor_name]
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if signal_child > 0 and not signal_reaped:
            try:
                _bounded_kill_and_reap(signal_child, signal_pidfd)
                signal_reaped = True
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if trace_child > 0 and not trace_reaped:
            try:
                if trace_pidfd >= 0:
                    if _LIBC.ptrace(PTRACE_KILL, trace_child, None, None) != 0:
                        number = ctypes.get_errno()
                        if number not in {errno.ESRCH, errno.EIO, errno.EPERM}:
                            raise CleanupIncomplete(
                                f"ptrace synthetic KILL failed: errno={number}"
                            )
                _bounded_kill_and_reap(trace_child, trace_pidfd)
                trace_reaped = True
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        for descriptor in (signal_pidfd, trace_pidfd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if cleanup_failures:
            raise CleanupIncomplete(
                "mandatory ABI control cleanup failed: "
                + "; ".join(cleanup_failures)
            )


def _loader_identity_observed(pid: int, expected: os.stat_result) -> bool:
    expected_device = f"{os.major(expected.st_dev):02x}:{os.minor(expected.st_dev):02x}"
    for row in (_provider_proc_root() / str(pid) / "maps").read_text(
        encoding="utf-8"
    ).splitlines():
        columns = row.split(maxsplit=5)
        if (
            len(columns) >= 5
            and columns[3] == expected_device
            and int(columns[4]) == expected.st_ino
        ):
            return True
    return False


def _fd_set_at_exec(pid: int) -> tuple[int, ...]:
    directory = _provider_proc_root() / str(pid) / "fd"
    try:
        return tuple(sorted(int(entry.name) for entry in directory.iterdir()))
    except OSError as exc:
        raise ObservationLoss("exec-stop FD observation failed") from exc


def _file_size_limits(pid: int) -> tuple[int, int]:
    for line in (_provider_proc_root() / str(pid) / "limits").read_text(
        encoding="ascii"
    ).splitlines():
        columns = line.split()
        if columns[:3] == ["Max", "file", "size"] and len(columns) >= 5:
            try:
                return int(columns[3]), int(columns[4])
            except ValueError as exc:
                raise ObservationLoss("RLIMIT_FSIZE observation is not numeric") from exc
    raise ObservationLoss("RLIMIT_FSIZE observation is absent")


def _core_size_limits(pid: int) -> tuple[int, int]:
    for line in (_provider_proc_root() / str(pid) / "limits").read_text(
        encoding="ascii"
    ).splitlines():
        columns = line.split()
        if columns[:3] == ["Max", "core", "file"] and len(columns) >= 6:
            try:
                return int(columns[4]), int(columns[5])
            except ValueError as exc:
                raise ObservationLoss("RLIMIT_CORE observation is not numeric") from exc
    raise ObservationLoss("RLIMIT_CORE observation is absent")


def _read_proc_nul_vector(pid: int, name: str) -> tuple[str, ...]:
    descriptor = os.open(
        _provider_proc_root() / str(pid) / name,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK,
    )
    try:
        payload = os.read(descriptor, 65_537)
        if len(payload) > 65_536 or os.read(descriptor, 1):
            raise ObservationLoss(f"exec-stop {name} exceeded its exact bound")
    finally:
        os.close(descriptor)
    if payload and not payload.endswith(b"\0"):
        raise ObservationLoss(f"exec-stop {name} was not NUL terminated")
    try:
        return tuple(
            item.decode("utf-8") for item in payload.rstrip(b"\0").split(b"\0")
        ) if payload else ()
    except UnicodeDecodeError as exc:
        raise ObservationLoss(f"exec-stop {name} was not UTF-8") from exc


def _private_fd_target(
    pid: int, descriptor: int, request: IsolationRequestV1
) -> dict[str, object] | None:
    path = os.readlink(_provider_proc_root() / str(pid) / "fd" / str(descriptor))
    for scope, root in (
        ("scratch", request.filesystem.scratch_private_path),
        ("output", request.filesystem.output_private_path),
    ):
        if path == root or path.startswith(root.rstrip("/") + "/"):
            return {
                "scope": scope,
                "target_path": path,
                "target_fd": descriptor,
                "signal_code": None,
                "fault_address": None,
            }
    return None


def _register_value(registers: UserRegsStructX86_64, name: str) -> int:
    try:
        return int(getattr(registers, name))
    except AttributeError as exc:
        raise ObservationLoss(f"unknown x86_64 syscall register: {name}") from exc


def _signed_register(value: int) -> int:
    return int(ctypes.c_longlong(value).value)


def _ptrace_read_bytes(pid: int, address: int, size: int) -> bytes:
    if address <= 0 or not 0 <= size <= 16_384:
        raise ObservationLoss("tracee memory read exceeded its strict bound")
    payload = bytearray()
    for offset in range(0, size, ctypes.sizeof(ctypes.c_long)):
        ctypes.set_errno(0)
        word = _LIBC.ptrace(
            PTRACE_PEEKDATA,
            pid,
            ctypes.c_void_p(address + offset),
            None,
        )
        number = ctypes.get_errno()
        if word == -1 and number:
            raise ObservationLoss(
                f"tracee iovec observation failed: errno={number}"
            )
        payload.extend(
            int(ctypes.c_ulong(word).value).to_bytes(
                ctypes.sizeof(ctypes.c_long), "little"
            )
        )
    return bytes(payload[:size])


def _quota_requested_bytes(
    pid: int, syscall_number: int, registers: UserRegsStructX86_64
) -> int | None:
    max_rw_count = 0x7FFFF000
    scalar_register = {
        1: "rdx",
        18: "rdx",
        40: "r10",
        275: "r8",
        326: "r8",
    }.get(syscall_number)
    if scalar_register is not None:
        return min(_register_value(registers, scalar_register), max_rw_count)
    if syscall_number in {20, 296, 328}:
        count = _register_value(registers, "rdx")
        if not 0 <= count <= 1_024:
            raise ObservationLoss("tracee iovec count exceeded its strict bound")
        raw = _ptrace_read_bytes(
            pid,
            _register_value(registers, "rsi"),
            count * 16,
        ) if count else b""
        total = sum(struct.unpack_from("=Q", raw, index * 16 + 8)[0] for index in range(count))
        if total > (1 << 63) - 1:
            raise ObservationLoss("tracee iovec byte count overflowed")
        return min(total, max_rw_count)
    return None


def _quota_syscall_entry(
    pid: int,
    registers: UserRegsStructX86_64,
    request: IsolationRequestV1,
) -> dict[str, object]:
    syscall_number = int(registers.orig_rax)
    result: dict[str, object] = {
        "syscall_number": syscall_number,
        "limit_kind": None,
        "target": None,
        "target_error": None,
    }
    fd_register = _QUOTA_FD_TARGET_REGISTER_BY_SYSCALL.get(syscall_number)
    if fd_register is not None:
        descriptor = _signed_register(_register_value(registers, fd_register))
        result["limit_kind"] = "syscall_errno"
        try:
            result["target"] = _private_fd_target(pid, descriptor, request)
        except BaseException as exc:
            result["target_error"] = _bounded_failure(exc)
        result["requested_bytes"] = _quota_requested_bytes(
            pid, syscall_number, registers
        )
    elif syscall_number in _UNATTRIBUTED_PATH_QUOTA_SYSCALLS_X86_64:
        result["limit_kind"] = "unattributed_path_quota_errno"
    return result


def _host_mounts_under(root: Path) -> tuple[str, ...]:
    lexical = str(root)
    prefix = lexical.rstrip("/") + "/"
    rows: list[str] = []
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        mountpoint = _mountinfo_unescape(line.split()[4])
        if mountpoint == lexical or mountpoint.startswith(prefix):
            rows.append(mountpoint)
    return tuple(sorted(rows))


def _scan_residue(root: Path, namespace_ids: Mapping[str, str]) -> tuple[str, ...]:
    """Boundedly scan procfs for references to this exact run."""

    root_text = str(root)
    namespace_values = set(namespace_ids.values())
    findings: list[str] = []
    deadline_ns = time.monotonic_ns() + 5_000_000_000
    observed_nodes = 0

    def account() -> None:
        nonlocal observed_nodes
        observed_nodes += 1
        if observed_nodes > 262_144 or time.monotonic_ns() >= deadline_ns:
            raise CleanupIncomplete("procfs residue scan exceeded its strict bound")

    try:
        with os.scandir("/proc") as processes:
            for proc_entry in processes:
                if not proc_entry.name.isdecimal():
                    continue
                account()
                proc = Path("/proc") / proc_entry.name
                for name in ("cwd", "root"):
                    account()
                    try:
                        value = os.readlink(proc / name)
                    except OSError:
                        continue
                    if value == root_text or value.startswith(root_text + "/"):
                        findings.append(f"{proc.name}/{name}->{value}")
                for directory in ("fd", "ns"):
                    try:
                        entries = os.scandir(proc / directory)
                    except OSError:
                        continue
                    with entries:
                        for entry in entries:
                            account()
                            try:
                                value = os.readlink(entry.path)
                            except OSError:
                                continue
                            if (
                                value == root_text
                                or value.startswith(root_text + "/")
                                or value in namespace_values
                            ):
                                findings.append(
                                    f"{proc.name}/{directory}/{entry.name}->{value}"
                                )
                            if len(findings) > 64:
                                raise CleanupIncomplete(
                                    "procfs residue finding count exceeded its bound"
                                )
    except OSError as exc:
        raise CleanupIncomplete("procfs residue scan failed") from exc
    return tuple(findings)


def _operstate_diagnostic() -> dict[str, object]:
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


def _loopback_positive_negative_control() -> dict[str, object]:
    server: socket.socket | None = None
    client: socket.socket | None = None
    accepted: socket.socket | None = None
    denial: socket.socket | None = None
    try:
        original = _interface_flags("lo")
        _set_interface_flags("lo", original | IFF_UP)
        flags_after_up = _interface_flags("lo")
        operstate_after_up = _operstate_diagnostic()
        if not flags_after_up & IFF_UP:
            raise CapabilityBlocker("loopback IFF_UP positive control failed")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(1)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        endpoint = server.getsockname()
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect(endpoint)
        accepted, _ = server.accept()
        client.sendall(b"p")
        positive = accepted.recv(1) == b"p"
        if not positive:
            raise CapabilityBlocker("loopback payload positive control failed")
        accepted.close()
        accepted = None
        client.close()
        client = None

        _set_interface_flags("lo", flags_after_up & ~IFF_UP)
        flags_after_down = _interface_flags("lo")
        operstate_after_down = _operstate_diagnostic()
        if flags_after_down & IFF_UP:
            raise CapabilityBlocker("loopback remained administratively up")
        if server.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1:
            raise CapabilityBlocker("loopback listener died before denial control")
        denial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        denial.settimeout(0.25)
        try:
            denial.connect(endpoint)
        except OSError as exc:
            denial_errno = exc.errno
        else:
            raise CapabilityBlocker("live loopback endpoint remained reachable")
        return {
            "flags_after_up": flags_after_up,
            "flags_after_down": flags_after_down,
            "operstate_after_up": operstate_after_up,
            "operstate_after_down": operstate_after_down,
            "positive": positive,
            "negative": True,
            "denial_errno": denial_errno,
            "namespace_inode": os.stat("/proc/self/ns/net").st_ino,
        }
    finally:
        for value in (denial, accepted, client, server):
            if value is not None:
                value.close()
        try:
            flags = _interface_flags("lo")
            if flags & IFF_UP:
                _set_interface_flags("lo", flags & ~IFF_UP)
        except OSError:
            pass


def _path_inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _request_boundary_check(request: IsolationRequestV1) -> None:
    roots = request.filesystem.read_only_inputs
    for index, left in enumerate(roots):
        for right in roots[index + 1 :]:
            if _path_inside(left.private_path, right.private_path) or _path_inside(
                right.private_path, left.private_path
            ):
                raise IdentityMismatch("nested private input roots are forbidden")
    writable = (
        request.filesystem.cwd_private_path,
        request.filesystem.scratch_private_path,
        request.filesystem.output_private_path,
    )
    for path in writable:
        if any(
            _path_inside(path, root.private_path)
            or _path_inside(root.private_path, path)
            for root in roots
        ):
            raise IdentityMismatch("writable and read-only private roots overlap")
    for expected in (
        request.executable.entrypoint,
        request.executable.interpreter,
        request.executable.loader,
    ):
        if expected is None:
            continue
        matching = [
            root
            for root in roots
            if _path_inside(expected.source_path, root.source_path)
        ]
        if len(matching) != 1:
            raise IdentityMismatch(
                f"expected object lacks one exact authorized source root: "
                f"{expected.source_path}"
            )
        if any(_path_inside(expected.private_path, path) for path in writable):
            raise IdentityMismatch(
                f"sealed private identity overlaps a writable root: "
                f"{expected.private_path}"
            )


def _validate_root_identity(root: ReadOnlyRootV1) -> int:
    descriptor = _safe_absolute_open(root.source_path, directory=True)
    try:
        value = os.fstat(descriptor)
        if (
            value.st_dev != root.device
            or value.st_ino != root.inode
            or value.st_mode != root.mode
            or not stat.S_ISDIR(value.st_mode)
        ):
            raise IdentityMismatch(
                f"read-only root identity mismatch: {root.source_path}"
            )
        # A nested mount would retain an independently writable subtree after
        # a bind remount.  Core v1 rejects it instead of weakening isolation.
        lexical = root.source_path.rstrip("/") + "/"
        rows = Path("/proc/self/mountinfo").read_text(
            encoding="utf-8"
        ).splitlines()
        for row in rows:
            columns = row.split()
            if len(columns) < 5:
                raise ObservationLoss("host mountinfo row is malformed")
            mountpoint = _mountinfo_unescape(columns[4])
            if mountpoint.startswith(lexical):
                raise CapabilityBlocker(
                    f"read-only root contains a nested mount: {mountpoint}"
                )
        return descriptor
    except BaseException as original:
        try:
            os.close(descriptor)
        except BaseException as cleanup_exc:
            raise CleanupIncomplete(
                "read-only root acquisition cleanup failed: "
                + _bounded_failure(cleanup_exc)
            ) from original
        raise


def _select_expected_from_roots(
    expected: ExpectedFileIdentityV1,
    root_fds: tuple[tuple[ReadOnlyRootV1, int], ...]
    | list[tuple[ReadOnlyRootV1, int]],
) -> int:
    matches: list[tuple[ReadOnlyRootV1, int, str]] = []
    for root, descriptor in root_fds:
        prefix = root.source_path.rstrip("/") + "/"
        if expected.source_path.startswith(prefix):
            relative = expected.source_path[len(prefix) :]
            if relative and not relative.startswith("/"):
                matches.append((root, descriptor, relative))
    if len(matches) != 1:
        raise IdentityMismatch(
            f"expected file lacks one unique authorized root: {expected.source_path}"
        )
    _, root_fd, relative = matches[0]
    return _openat2(
        root_fd,
        relative,
        flags=os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC,
        resolve=(
            RESOLVE_BENEATH
            | RESOLVE_NO_MAGICLINKS
            | RESOLVE_NO_SYMLINKS
            | RESOLVE_NO_XDEV
        ),
    )


@dataclass
class _PreparedRequest:
    request: IsolationRequestV1
    root_fds: tuple[tuple[ReadOnlyRootV1, int], ...]
    entrypoint: _SealedFile
    interpreter: _SealedFile | None
    loader: _SealedFile | None

    @classmethod
    def create(cls, request: IsolationRequestV1) -> _PreparedRequest:
        _request_boundary_check(request)
        root_fds: list[tuple[ReadOnlyRootV1, int]] = []
        sealed: list[_SealedFile] = []
        try:
            for root in request.filesystem.read_only_inputs:
                root_fds.append((root, _validate_root_identity(root)))
            entrypoint = _seal_expected_file(
                request.executable.entrypoint,
                deadline_ns=request.process.deadline_monotonic_ns,
                source_descriptor=_select_expected_from_roots(
                    request.executable.entrypoint, root_fds
                ),
            )
            sealed.append(entrypoint)
            interpreter = (
                _seal_expected_file(
                    request.executable.interpreter,
                    deadline_ns=request.process.deadline_monotonic_ns,
                    source_descriptor=_select_expected_from_roots(
                        request.executable.interpreter, root_fds
                    ),
                )
                if request.executable.interpreter is not None
                else None
            )
            if interpreter is not None:
                sealed.append(interpreter)
            loader = (
                _seal_expected_file(
                    request.executable.loader,
                    deadline_ns=request.process.deadline_monotonic_ns,
                    source_descriptor=_select_expected_from_roots(
                        request.executable.loader, root_fds
                    ),
                )
                if request.executable.loader is not None
                else None
            )
            if loader is not None:
                sealed.append(loader)
            if request.executable.format is ExecutableFormatV1.ELF_STATIC:
                if _read_pt_interp(entrypoint.sealed_fd) is not None:
                    raise IdentityMismatch("static request selected a dynamic ELF")
            elif request.executable.format is ExecutableFormatV1.ELF_DYNAMIC:
                parsed = _read_pt_interp(entrypoint.sealed_fd)
                if (
                    parsed != request.executable.parsed_interpreter_path
                    or loader is None
                    or loader.expected.private_path != parsed
                ):
                    raise IdentityMismatch("PT_INTERP does not match loader request")
            else:
                parsed = _read_shebang(entrypoint.sealed_fd)
                if (
                    parsed != request.executable.parsed_interpreter_path
                    or interpreter is None
                    or interpreter.expected.private_path != parsed
                ):
                    raise IdentityMismatch("shebang does not match interpreter request")
                interpreter_loader = _read_pt_interp(interpreter.sealed_fd)
                if loader is None or interpreter_loader != loader.expected.private_path:
                    raise IdentityMismatch(
                        "interpreter PT_INTERP does not match loader request"
                    )
            return cls(
                request=request,
                root_fds=tuple(root_fds),
                entrypoint=entrypoint,
                interpreter=interpreter,
                loader=loader,
            )
        except BaseException as original:
            cleanup_failures: list[str] = []
            for _, descriptor in root_fds:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
            for item in sealed:
                try:
                    item.close()
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
            if cleanup_failures:
                raise CleanupIncomplete(
                    "prepared-request acquisition cleanup failed: "
                    + "; ".join(cleanup_failures)
                ) from original
            raise

    def close(self) -> None:
        failures: list[str] = []
        for _, descriptor in self.root_fds:
            try:
                os.close(descriptor)
            except BaseException as exc:
                failures.append(_bounded_failure(exc))
        for item in (self.entrypoint, self.interpreter, self.loader):
            if item is not None:
                try:
                    item.close()
                except BaseException as exc:
                    failures.append(_bounded_failure(exc))
        self.root_fds = ()
        if failures:
            raise CleanupIncomplete(
                "prepared-request descriptor cleanup failed: "
                + "; ".join(failures)
            )


def _inside_path(root: Path, private_path: str) -> Path:
    if (
        not private_path.startswith("/")
        or private_path.startswith("//")
        or "\x00" in private_path
    ):
        raise IdentityMismatch(f"unsafe private path: {private_path!r}")
    raw_components = private_path[1:].split("/")
    if len(raw_components) > 64:
        raise IdentityMismatch("private path exceeds the v1 component-depth bound")
    relative = Path(private_path[1:])
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in raw_components
    ):
        raise IdentityMismatch(f"unsafe private path: {private_path!r}")
    candidate = root.joinpath(*relative.parts)
    if candidate == root or root not in candidate.parents:
        raise IdentityMismatch(f"private path escaped provider root: {private_path!r}")
    return candidate


def _ensure_mount_target(root: Path, private_path: str, *, directory: bool) -> Path:
    target = _inside_path(root, private_path)
    relative = target.relative_to(root)
    components = relative.parts if directory else relative.parts[:-1]
    current = root
    for component in components:
        current = current / component
        try:
            current.mkdir(mode=0o555)
        except FileExistsError:
            pass
        observed = os.lstat(current)
        if not stat.S_ISDIR(observed.st_mode) or observed.st_uid != 0:
            raise IdentityMismatch(
                f"mount-target parent is not a root-owned directory: {current}"
            )
        os.chown(current, 0, 0, follow_symlinks=False)
        os.chmod(current, 0o555, follow_symlinks=False)
        rechecked = os.lstat(current)
        if (
            not stat.S_ISDIR(rechecked.st_mode)
            or rechecked.st_uid != 0
            or rechecked.st_gid != 0
            or stat.S_IMODE(rechecked.st_mode) != 0o555
        ):
            raise ObservationLoss(f"mount-target parent hardening failed: {current}")
    if not directory:
        try:
            descriptor = os.open(
                target,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o400,
            )
        except FileExistsError:
            observed = os.lstat(target)
            if not stat.S_ISREG(observed.st_mode) or observed.st_uid != 0:
                raise IdentityMismatch(f"mount target is not a root-owned file: {target}")
        else:
            os.close(descriptor)
        os.chown(target, 0, 0, follow_symlinks=False)
        os.chmod(target, 0o400, follow_symlinks=False)
    return target


def _scan_read_only_tree(descriptor: int) -> dict[str, object]:
    """Reject workload-visible IPC/devices and escaping symlinks pre-release."""

    deadline_ns = time.monotonic_ns() + 5_000_000_000
    before = os.fstat(descriptor)

    def pass_once() -> tuple[tuple[object, ...], ...]:
        rows: list[tuple[object, ...]] = []
        stack: list[tuple[int, tuple[str, ...]]] = [(os.dup(descriptor), ())]
        try:
            while stack:
                directory_fd, prefix = stack.pop()
                try:
                    with os.scandir(directory_fd) as entries:
                        for entry in entries:
                            if (
                                len(rows) >= 4_096
                                or time.monotonic_ns() >= deadline_ns
                            ):
                                raise CapabilityBlocker(
                                    "read-only input traversal exceeded its strict bound"
                                )
                            value = entry.stat(follow_symlinks=False)
                            if value.st_dev != before.st_dev:
                                raise IdentityMismatch(
                                    "read-only input crossed a filesystem device"
                                )
                            relative = (*prefix, entry.name)
                            link_target: str | None = None
                            if stat.S_ISDIR(value.st_mode):
                                child = os.open(
                                    entry.name,
                                    os.O_RDONLY
                                    | os.O_DIRECTORY
                                    | os.O_NOFOLLOW
                                    | os.O_CLOEXEC,
                                    dir_fd=directory_fd,
                                )
                                stack.append((child, relative))
                            elif stat.S_ISREG(value.st_mode):
                                pass
                            elif stat.S_ISLNK(value.st_mode):
                                link_target = os.readlink(
                                    entry.name, dir_fd=directory_fd
                                )
                            else:
                                raise IdentityMismatch(
                                    "read-only input contains FIFO/socket/device IPC"
                                )
                            rows.append(
                                (
                                    relative,
                                    value.st_dev,
                                    value.st_ino,
                                    value.st_mode,
                                    value.st_size,
                                    value.st_mtime_ns,
                                    value.st_ctime_ns,
                                    link_target,
                                )
                            )
                finally:
                    os.close(directory_fd)
        finally:
            for directory_fd, _ in stack:
                try:
                    os.close(directory_fd)
                except OSError:
                    pass
        return tuple(sorted(rows))

    first = pass_once()
    second = pass_once()
    after = os.fstat(descriptor)
    if (
        before.st_dev,
        before.st_ino,
        before.st_mode,
    ) != (after.st_dev, after.st_ino, after.st_mode):
        raise ObservationLoss("read-only root changed during special-inode scan")
    if first != second:
        raise ObservationLoss("read-only input changed during double scan")
    return {
        "observed_device": after.st_dev,
        "observed_inode": after.st_ino,
        "entries_scanned": len(second),
        "entry_limit": 4_096,
        "allowed_inode_types": ["directory", "regular", "symlink"],
        "fd_relative": True,
        "nofollow": True,
        "no_xdev": True,
        "identity_revalidated": True,
        "stable_during_scan": True,
    }


def _bind_fd_read_only(
    descriptor: int, target: Path, *, recursive: bool
) -> dict[str, object]:
    source = f"/proc/self/fd/{descriptor}"
    _mount(source, target, None, MS_BIND | (MS_REC if recursive else 0))
    lexical_target = str(target).rstrip("/") + "/"
    nested_targets = [
        _mountinfo_unescape(row.split()[4])
        for row in Path("/proc/self/mountinfo")
        .read_text(encoding="utf-8")
        .splitlines()
        if _mountinfo_unescape(row.split()[4]).startswith(lexical_target)
    ]
    if nested_targets:
        raise CapabilityBlocker(
            f"read-only bind unexpectedly contains submounts: {nested_targets}"
        )
    _mount(
        None,
        target,
        None,
        MS_BIND
        | MS_REMOUNT
        | MS_RDONLY
        | MS_NOSUID
        | MS_NODEV,
    )
    value = os.stat(target)
    expected = os.fstat(descriptor)
    if value.st_dev != expected.st_dev or value.st_ino != expected.st_ino:
        raise ObservationLoss(f"bind identity changed at {target}")
    statvfs_value = os.statvfs(target)
    matching = [
        row
        for row in Path("/proc/self/mountinfo")
        .read_text(encoding="utf-8")
        .splitlines()
        if _mountinfo_unescape(row.split()[4]) == str(target)
    ]
    if len(matching) != 1:
        raise ObservationLoss(f"read-only bind mount is ambiguous: {target}")
    mount_options = tuple(sorted(matching[0].split()[5].split(",")))
    if not {"ro", "nodev", "nosuid"}.issubset(mount_options) or not (
        statvfs_value.f_flag & os.ST_RDONLY
    ):
        raise CapabilityBlocker(f"read-only bind flags were not effective: {target}")
    denial_errno: int | None = None
    tree_control = None
    if stat.S_ISDIR(value.st_mode):
        scan_fd = os.open(
            target,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        try:
            tree_control = _scan_read_only_tree(scan_fd)
        finally:
            os.close(scan_fd)
    try:
        if stat.S_ISDIR(value.st_mode):
            probe = os.open(
                target,
                os.O_TMPFILE | os.O_RDWR | os.O_CLOEXEC,
                0o600,
            )
        else:
            probe = os.open(target, os.O_WRONLY | os.O_CLOEXEC)
    except OSError as exc:
        denial_errno = exc.errno
        if denial_errno != errno.EROFS:
            raise CapabilityBlocker(
                f"read-only write control returned errno {denial_errno}: {target}"
            ) from exc
    else:
        os.close(probe)
        raise CapabilityBlocker(f"read-only write control succeeded: {target}")
    return {
        "target": str(target),
        "mount_options": ["nodev", "nosuid", "ro"],
        "statvfs_read_only": True,
        "write_denial_errno": denial_errno,
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "tree_control": tree_control,
    }


def _tmpfs_usage(path: str) -> tuple[int, int]:
    value = os.statvfs(path)
    used_bytes = (value.f_blocks - value.f_bfree) * value.f_frsize
    used_inodes = value.f_files - value.f_ffree
    return used_bytes, used_inodes


def _tmpfs_usage_fd(descriptor: int) -> tuple[int, int]:
    value = os.fstatvfs(descriptor)
    used_bytes = (value.f_blocks - value.f_bfree) * value.f_frsize
    used_inodes = value.f_files - value.f_ffree
    return used_bytes, used_inodes


def _tmpfs_enforcement_observation(
    path: Path,
    *,
    expected_byte_limit: int,
    expected_inode_limit: int,
) -> dict[str, object]:
    value = os.statvfs(path)
    byte_ceiling = value.f_blocks * value.f_frsize
    inode_ceiling = value.f_files
    matching = [
        row
        for row in Path("/proc/self/mountinfo")
        .read_text(encoding="utf-8")
        .splitlines()
        if _mountinfo_unescape(row.split()[4]) == str(path)
    ]
    if len(matching) != 1:
        raise ObservationLoss(f"private tmpfs mount identity is ambiguous: {path}")
    left, right = matching[0].split(" - ", 1)
    mount_options = tuple(sorted(left.split()[5].split(",")))
    filesystem_type = right.split()[0]
    if (
        filesystem_type != "tmpfs"
        or not {"nosuid", "nodev", "noexec", "rw"}.issubset(mount_options)
        or byte_ceiling != expected_byte_limit
        or inode_ceiling != expected_inode_limit
    ):
        raise CapabilityBlocker(
            "private tmpfs enforcement differs from the requested exact ceiling"
        )
    return {
        "filesystem_type": filesystem_type,
        "mount_options": ["nodev", "noexec", "nosuid", "rw"],
        "byte_ceiling": byte_ceiling,
        "inode_ceiling": inode_ceiling,
        "fragment_size": value.f_frsize,
    }


def _prepare_declared_output_layout(
    output: Path,
    retained_paths: tuple[str, ...],
    *,
    uid: int,
    gid: int,
) -> dict[str, object]:
    directories = {output}
    for relative in retained_paths:
        parts = Path(relative).parts
        parent = output
        for component in parts[:-1]:
            parent = parent / component
            parent.mkdir(mode=0o555, exist_ok=True)
            directories.add(parent)
        target = parent / parts[-1]
        descriptor = os.open(
            target,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | os.O_CLOEXEC,
            0o600,
        )
        try:
            os.fchown(descriptor, uid, gid)
        finally:
            os.close(descriptor)
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        os.chown(directory, 0, 0)
        os.chmod(directory, 0o555)
    # A real negative creation control under the exact output mount.  It must
    # fail without ever creating a namespace entry.
    control = output / ".undeclared-output-control"
    read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
        try:
            descriptor = os.open(
                control,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                0o600,
            )
        except OSError as exc:
            os.write(write_fd, str(exc.errno).encode("ascii"))
            os._exit(0)
        os.close(descriptor)
        os.write(write_fd, b"0")
        os._exit(1)
    os.close(write_fd)
    raw_errno = os.read(read_fd, 32)
    os.close(read_fd)
    status_value = _bounded_waitpid_status(child, timeout=2)
    try:
        creation_errno = int(raw_errno.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise CapabilityBlocker("undeclared output control lacked errno") from exc
    if (
        not os.WIFEXITED(status_value)
        or os.WEXITSTATUS(status_value) != 0
        or creation_errno != errno.EACCES
        or control.exists()
    ):
        control.unlink(missing_ok=True)
        raise CapabilityBlocker("undeclared output creation control succeeded")
    return {
        "declared_output_allowlist": list(retained_paths),
        "undeclared_output_blocked": True,
        "output_parent_directories_nonwritable": True,
        "creation_denial_errno": creation_errno,
    }


def _snapshot_filesystem(
    request: IsolationRequestV1,
    scratch_fd: int,
    output_fd: int,
) -> dict[str, object]:
    """Observe private files only after the complete writer cgroup is empty."""

    scratch_used = _tmpfs_usage_fd(scratch_fd)
    output_used = _tmpfs_usage_fd(output_fd)
    scratch_capacity = os.fstatvfs(scratch_fd)
    output_capacity = os.fstatvfs(output_fd)
    if (
        scratch_capacity.f_blocks * scratch_capacity.f_frsize
        != request.filesystem.scratch_byte_limit
        or scratch_capacity.f_files != request.filesystem.scratch_inode_limit
        or output_capacity.f_blocks * output_capacity.f_frsize
        != request.filesystem.output_byte_limit
        or output_capacity.f_files != request.filesystem.output_inode_limit
        or scratch_used[0] > request.filesystem.scratch_byte_limit
        or scratch_used[1] > request.filesystem.scratch_inode_limit
        or output_used[0] > request.filesystem.output_byte_limit
        or output_used[0] > request.output.file_output_byte_limit
        or output_used[1] > request.filesystem.output_inode_limit
    ):
        raise ObservationLoss("kernel-enforced private filesystem quota was exceeded")
    declared = set(request.filesystem.retained_output_paths)
    allowed_directories = {
        "/".join(Path(relative).parts[:index])
        for relative in declared
        for index in range(1, len(Path(relative).parts))
    }
    observed_objects = 0
    logical_output_bytes = 0
    observed_output_paths: list[str] = []
    output_root_stat = os.fstat(output_fd)
    if output_root_stat.st_uid != 0 or output_root_stat.st_mode & 0o222:
        raise ObservationLoss("output root is not root-owned and non-writable")

    def walk(directory_fd: int, prefix: str = "") -> None:
        nonlocal observed_objects, logical_output_bytes
        for name in sorted(os.listdir(directory_fd)):
            relative = f"{prefix}/{name}" if prefix else name
            observed_objects += 1
            if observed_objects > request.filesystem.output_inode_limit:
                raise ObservationLoss("output traversal exceeded its inode ceiling")
            value = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(value.st_mode):
                if relative not in allowed_directories:
                    raise IdentityMismatch(
                        f"undeclared output directory was rejected: {relative}"
                    )
                if value.st_uid != 0 or value.st_mode & 0o222:
                    raise ObservationLoss(
                        f"output parent directory became writable: {relative}"
                    )
                child_fd = os.open(
                    name,
                    os.O_RDONLY
                    | os.O_DIRECTORY
                    | os.O_NOFOLLOW
                    | os.O_CLOEXEC,
                    dir_fd=directory_fd,
                )
                try:
                    walk(child_fd, relative)
                finally:
                    os.close(child_fd)
            elif (
                not stat.S_ISREG(value.st_mode)
                or value.st_nlink != 1
                or relative not in declared
            ):
                raise IdentityMismatch(
                    f"undeclared output object was rejected: {relative}"
                )
            else:
                observed_output_paths.append(relative)
                logical_output_bytes += value.st_size
                if logical_output_bytes > request.output.file_output_byte_limit:
                    raise IdentityMismatch(
                        "declared output logical bytes exceed the file-output limit"
                    )

    walk(output_fd)
    retained: list[dict[str, object]] = []
    snapshot_deadline_ns = time.monotonic_ns() + 5_000_000_000
    for relative in request.filesystem.retained_output_paths:
        identity_fd = _openat2(
            output_fd,
            relative,
            flags=O_PATH | os.O_CLOEXEC,
            resolve=(
                RESOLVE_BENEATH
                | RESOLVE_NO_MAGICLINKS
                | RESOLVE_NO_SYMLINKS
                | RESOLVE_NO_XDEV
            ),
        )
        try:
            value = os.fstat(identity_fd)
            if (
                not stat.S_ISREG(value.st_mode)
                or value.st_nlink != 1
                or value.st_size > request.output.file_output_byte_limit
            ):
                raise IdentityMismatch("retained output identity or size is forbidden")
            descriptor = _openat2(
                output_fd,
                relative,
                flags=os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC,
                resolve=(
                    RESOLVE_BENEATH
                    | RESOLVE_NO_MAGICLINKS
                    | RESOLVE_NO_SYMLINKS
                    | RESOLVE_NO_XDEV
                ),
            )
            try:
                reopened = os.fstat(descriptor)
                fields = ("st_dev", "st_ino", "st_mode", "st_size")
                if any(
                    getattr(reopened, name) != getattr(value, name)
                    for name in fields
                ):
                    raise ObservationLoss("retained output changed while reopening")
                retained.append(
                    _observed_file(
                        f"{request.filesystem.output_private_path}/{relative}",
                        descriptor,
                        deadline_ns=snapshot_deadline_ns,
                    )
                )
            finally:
                os.close(descriptor)
        finally:
            os.close(identity_fd)
    return {
        "scratch_used_bytes": scratch_used[0],
        "scratch_used_inodes": scratch_used[1],
        "output_used_bytes": output_used[0],
        "output_used_inodes": output_used[1],
        "retained_outputs": retained,
        "declared_output_allowlist": list(
            request.filesystem.retained_output_paths
        ),
        "observed_output_paths": sorted(observed_output_paths),
        "undeclared_output_blocked": True,
        "output_parent_directories_nonwritable": True,
        "quota_observed_after_kill": True,
        "scratch_observed_byte_ceiling": (
            scratch_capacity.f_blocks * scratch_capacity.f_frsize
        ),
        "scratch_observed_inode_ceiling": scratch_capacity.f_files,
        "output_observed_byte_ceiling": (
            output_capacity.f_blocks * output_capacity.f_frsize
        ),
        "output_observed_inode_ceiling": output_capacity.f_files,
    }


def _probe_tmpfs_quota(path: str, *, byte_limit: int, inode_limit: int) -> dict[str, bool]:
    byte_enospc = False
    inode_enospc = False
    byte_path = Path(path) / ".quota-byte-control"
    inode_prefix = Path(path) / ".quota-inode-control-"
    descriptor = os.open(byte_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        while True:
            try:
                os.write(descriptor, b"q" * 4096)
            except OSError as exc:
                if exc.errno != errno.ENOSPC:
                    raise
                byte_enospc = True
                break
    finally:
        os.close(descriptor)
        byte_path.unlink(missing_ok=True)
    created: list[Path] = []
    try:
        for index in range(inode_limit + 16):
            candidate = Path(f"{inode_prefix}{index}")
            try:
                fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except OSError as exc:
                if exc.errno != errno.ENOSPC:
                    raise
                inode_enospc = True
                break
            else:
                os.close(fd)
                created.append(candidate)
    finally:
        for candidate in created:
            candidate.unlink(missing_ok=True)
    # Very large caller limits are not fully filled by a capability probe;
    # the actual mount options remain the OS enforcement.  The positive
    # ENOSPC controls run against a separate tiny mount in setup below.
    return {"byte_enospc": byte_enospc, "inode_enospc": inode_enospc}


def _openat2_boundary_control(
    root: Path, *, output_private_path: str, scratch_private_path: str
) -> tuple[str, ...]:
    boundary = root / ".openat2-control"
    boundary.mkdir()
    (boundary / "inside").write_bytes(b"inside")
    (boundary / "outside").symlink_to("/etc/passwd")
    (boundary / "provider-control").symlink_to("/sys/fs/cgroup")
    (boundary / "mounted").mkdir()
    _mount(
        "tmpfs",
        boundary / "mounted",
        "tmpfs",
        MS_NOSUID | MS_NODEV | MS_NOEXEC,
        "size=4096,nr_inodes=8,mode=0700",
    )
    descriptor = os.open(boundary, O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    denied: list[str] = []
    resolution = (
        RESOLVE_BENEATH
        | RESOLVE_NO_MAGICLINKS
        | RESOLVE_NO_SYMLINKS
        | RESOLVE_NO_XDEV
    )
    try:
        positive = _openat2(descriptor, "inside", resolve=resolution)
        try:
            if os.read(positive, 6) != b"inside":
                raise CapabilityBlocker("openat2 positive control returned wrong bytes")
        finally:
            os.close(positive)
        for label, candidate in (
            ("traversal", "../etc/passwd"),
            ("symlink", "outside"),
            ("provider_control", "provider-control"),
            ("mount_crossing", "mounted"),
        ):
            try:
                escaped = _openat2(descriptor, candidate, resolve=resolution)
            except OSError as exc:
                if exc.errno not in {errno.EXDEV, errno.ELOOP}:
                    raise
                denied.append(label)
            else:
                os.close(escaped)
                raise CapabilityBlocker(f"openat2 {label} control escaped")

        proc_fd = os.open("/proc", O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            try:
                escaped = _openat2(
                    proc_fd,
                    "self/fd/0",
                    resolve=RESOLVE_NO_MAGICLINKS,
                )
            except OSError as exc:
                if exc.errno != errno.ELOOP:
                    raise
                denied.append("magic_link")
            else:
                os.close(escaped)
                raise CapabilityBlocker("openat2 proc magic-link control escaped")
        finally:
            os.close(proc_fd)

        output_fd = os.open(
            _inside_path(root, output_private_path),
            O_PATH | os.O_DIRECTORY | os.O_CLOEXEC,
        )
        try:
            scratch_name = Path(scratch_private_path).name
            try:
                escaped = _openat2(
                    output_fd,
                    f"../{scratch_name}",
                    resolve=(
                        RESOLVE_BENEATH
                        | RESOLVE_NO_MAGICLINKS
                        | RESOLVE_NO_SYMLINKS
                        | RESOLVE_NO_XDEV
                    ),
                )
            except OSError as exc:
                if exc.errno not in {errno.EXDEV, errno.ELOOP}:
                    raise
            else:
                os.close(escaped)
                raise CapabilityBlocker("undeclared output boundary control escaped")
        finally:
            os.close(output_fd)
    finally:
        os.close(descriptor)
        try:
            _umount(boundary / "mounted")
        except OSError:
            pass
        shutil.rmtree(boundary)
    expected = (
        "provider_control",
        "traversal",
        "symlink",
        "magic_link",
        "mount_crossing",
    )
    if set(denied) != set(expected):
        raise CapabilityBlocker(f"filesystem denial controls incomplete: {denied}")
    return expected


@dataclass
class _ReportWriter:
    descriptor: int
    byte_limit: int
    emitted_bytes: int = 0

    def write(self, value: Mapping[str, object]) -> None:
        payload = json.dumps(
            value,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        if len(payload) > self.byte_limit - self.emitted_bytes:
            # Do not publish a partial or over-limit provider record.  The
            # supervising reader also accounts the raw pipe bytes, so a
            # compromised producer cannot bypass this pre-write gate.
            raise ObservationLoss("structured-result byte limit would be exceeded")
        view = memoryview(payload)
        while view:
            written = os.write(self.descriptor, view)
            if written <= 0:
                raise ObservationLoss("short internal observation write")
            view = view[written:]
        self.emitted_bytes += len(payload)


def _send_snapshot_fds(socket_fd: int, scratch_fd: int, output_fd: int) -> None:
    rights = array.array("i", (scratch_fd, output_fd))
    channel = socket.socket(fileno=socket_fd)
    try:
        sent = channel.sendmsg(
            [b"ts-b02a-snapshot-v1"],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, rights)],
        )
        if sent != len(b"ts-b02a-snapshot-v1"):
            raise ObservationLoss("snapshot descriptor transfer was short")
    finally:
        channel.detach()


def _receive_snapshot_fds(socket_fd: int, timeout_seconds: float) -> tuple[int, int]:
    channel = socket.socket(fileno=socket_fd)
    received: list[int] = []
    try:
        channel.settimeout(timeout_seconds)
        payload, ancillary, flags, _ = channel.recvmsg(
            64,
            socket.CMSG_SPACE(2 * array.array("i").itemsize),
        )
        if payload != b"ts-b02a-snapshot-v1" or flags & (
            socket.MSG_CTRUNC | socket.MSG_TRUNC
        ):
            raise ObservationLoss("snapshot descriptor transfer was malformed")
        for level, kind, data in ancillary:
            if level != socket.SOL_SOCKET or kind != socket.SCM_RIGHTS:
                continue
            descriptors = array.array("i")
            usable = len(data) - (len(data) % descriptors.itemsize)
            descriptors.frombytes(data[:usable])
            received.extend(int(value) for value in descriptors)
        if len(received) != 2:
            raise ObservationLoss("snapshot descriptor transfer was incomplete")
        for descriptor in received:
            value = os.fstat(descriptor)
            if not stat.S_ISDIR(value.st_mode):
                raise ObservationLoss("snapshot descriptor is not a directory")
            os.set_inheritable(descriptor, False)
        return received[0], received[1]
    except BaseException:
        for descriptor in received:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise
    finally:
        channel.detach()


def _quota_capability_controls(root: Path) -> dict[str, bool]:
    byte_root = root / ".quota-byte-control"
    inode_root = root / ".quota-inode-control"
    byte_root.mkdir()
    inode_root.mkdir()
    byte_enospc = False
    inode_enospc = False
    try:
        _mount(
            "tmpfs",
            byte_root,
            "tmpfs",
            MS_NOSUID | MS_NODEV,
            "size=65536,nr_inodes=32,mode=0700",
        )
        descriptor = os.open(
            byte_root / "payload", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        try:
            for _ in range(64):
                try:
                    os.write(descriptor, b"q" * 4096)
                except OSError as exc:
                    if exc.errno != errno.ENOSPC:
                        raise
                    byte_enospc = True
                    break
        finally:
            os.close(descriptor)
        _umount(byte_root)

        _mount(
            "tmpfs",
            inode_root,
            "tmpfs",
            MS_NOSUID | MS_NODEV,
            "size=1048576,nr_inodes=16,mode=0700",
        )
        for index in range(64):
            try:
                descriptor = os.open(
                    inode_root / f"entry-{index}",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
            except OSError as exc:
                if exc.errno != errno.ENOSPC:
                    raise
                inode_enospc = True
                break
            else:
                os.close(descriptor)
        _umount(inode_root)
    finally:
        for path in (inode_root, byte_root):
            try:
                if path.is_mount():
                    _umount(path, MNT_DETACH)
            except OSError:
                pass
            shutil.rmtree(path, ignore_errors=True)
    if not byte_enospc or not inode_enospc:
        raise CapabilityBlocker("tmpfs byte/inode ENOSPC controls failed")
    return {"byte_enospc": True, "inode_enospc": True}


def _vfork_positive_control() -> bool:
    """Exercise vfork without returning through CPython in the shared child."""

    # mov eax,58; syscall; test rax,rax; jne parent; mov eax,60;
    # xor edi,edi; syscall; parent: ret
    machine_code = bytes.fromhex(
        "b83a0000000f054885c07509b83c00000031ff0f05c3"
    )
    mapping = mmap.mmap(
        -1,
        len(machine_code),
        prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC,
    )
    function = None
    child = -1
    child_pidfd = -1
    child_reaped = False
    try:
        mapping.write(machine_code)
        address = ctypes.addressof(ctypes.c_char.from_buffer(mapping))
        function = ctypes.CFUNCTYPE(ctypes.c_long)(address)
        child = int(function())
        if child <= 0:
            return False
        child_pidfd = os.pidfd_open(child)
        status_value = _bounded_waitpid_status(child, timeout=2)
        child_reaped = True
        return os.WIFEXITED(status_value) and os.WEXITSTATUS(status_value) == 0
    finally:
        if child > 0 and not child_reaped:
            _bounded_kill_and_reap(child, child_pidfd)
        if child_pidfd >= 0:
            os.close(child_pidfd)
        function = None
        mapping.close()


def _bounded_seccomp_nested_child(
    child: int, verifier: Callable[[int], bool]
) -> bool:
    """Bind, observe, and reap one short-lived seccomp-control child."""

    pidfd = -1
    reaped = False
    try:
        pidfd = os.pidfd_open(child)
        status_value = _bounded_waitpid_status(child, timeout=2)
        reaped = True
        return verifier(status_value)
    finally:
        if not reaped:
            _bounded_kill_and_reap(child, pidfd)
        if pidfd >= 0:
            os.close(pidfd)


def _seccomp_process_controls() -> dict[str, object]:
    """Run the fatal x32 probe as one gated, outer-owned direct child."""

    gate_read = gate_write = -1
    child = child_pidfd = -1
    child_reaped = False
    cleanup_failures: list[str] = []
    try:
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        child = os.fork()
        if child == 0:
            try:
                os.close(gate_write)
                if os.read(gate_read, 1) != b"g":
                    os._exit(125)
                os.close(gate_read)
                _install_seccomp_filter()
                _LIBC.syscall(X32_SYSCALL_BIT_V1 | 41, 0, 0, 0, 0, 0, 0)
            except BaseException:
                os._exit(126)
            os._exit(99)
        os.close(gate_read)
        gate_read = -1
        child_pidfd = os.pidfd_open(child)
        _write_all(gate_write, b"g")
        os.close(gate_write)
        gate_write = -1
        status_value = _bounded_waitpid_status(child, timeout=2)
        child_reaped = True
        return {
            "x32_kill_control": (
                os.WIFSIGNALED(status_value)
                and os.WTERMSIG(status_value) == signal.SIGSYS
            )
        }
    finally:
        for descriptor in (gate_read, gate_write):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if child > 0 and not child_reaped:
            try:
                if child_pidfd >= 0:
                    _bounded_kill_and_reap(child, child_pidfd)
                else:
                    # The child has not passed its parent-owned gate.  Closing
                    # the gate above makes it exit without signalling an
                    # unbound numeric PID.
                    _bounded_waitpid_status(child, timeout=2)
                child_reaped = True
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if child_pidfd >= 0:
            try:
                os.close(child_pidfd)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if cleanup_failures:
            raise CleanupIncomplete(
                "x32 seccomp control cleanup failed: "
                + "; ".join(cleanup_failures)
            )


def _seccomp_control_child_payload(write_fd: int) -> dict[str, object]:
    """Install the exact filter and exercise its synthetic controls."""

    observed_filter_sha256 = _install_seccomp_filter()
    controls: dict[str, int] = {}

    ctypes.set_errno(0)
    ceiling_result = _LIBC.syscall(
        NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1, 0, 0, 0, 0, 0, 0
    )
    ceiling_syscall_errno = ctypes.get_errno() if ceiling_result < 0 else 0

    fcntl_command_controls: dict[str, int] = {}
    for label, command in FCNTL_DENIED_COMMANDS_V1:
        try:
            fcntl.fcntl(write_fd, command, 0)
        except OSError as exc:
            fcntl_command_controls[label] = exc.errno
        else:
            fcntl_command_controls[label] = 0
    futex_word = ctypes.c_int(0)
    ctypes.set_errno(0)
    shared_futex_result = _LIBC.syscall(
        202, ctypes.byref(futex_word), 1, 1, 0, 0, 0
    )
    futex_shared_wake_errno = ctypes.get_errno() if shared_futex_result < 0 else 0
    ctypes.set_errno(0)
    futex_private_wake_result = _LIBC.syscall(
        202,
        ctypes.byref(futex_word),
        1 | FUTEX_PRIVATE_FLAG_V1,
        1,
        0,
        0,
        0,
    )
    futex_controls = {
        "shared_wake_errno": futex_shared_wake_errno,
        "private_wake_result": int(futex_private_wake_result),
    }
    pipe2_controls: dict[str, object] = {}
    for label, flag in PIPE2_DENIED_FLAGS_V1:
        descriptors = (ctypes.c_int * 2)(-1, -1)
        ctypes.set_errno(0)
        result = _LIBC.syscall(293, ctypes.byref(descriptors), flag)
        pipe2_controls[
            "direct_errno" if label == "O_DIRECT" else "notification_errno"
        ] = ctypes.get_errno() if result < 0 else 0
        if result == 0:
            os.close(descriptors[0])
            os.close(descriptors[1])
    ordinary_read, ordinary_write = os.pipe2(os.O_CLOEXEC)
    os.close(ordinary_read)
    os.close(ordinary_write)
    pipe2_controls["ordinary"] = True
    if fcntl.fcntl(write_fd, fcntl.F_GETPIPE_SZ) <= 0:
        raise CapabilityBlocker("seccomp F_GETPIPE_SZ positive control failed")

    def socket_denied(label: str, domain: int, kind: int) -> None:
        ctypes.set_errno(0)
        descriptor = _LIBC.socket(domain, kind, 0)
        observed = ctypes.get_errno() if descriptor < 0 else 0
        if descriptor >= 0:
            os.close(descriptor)
        controls[label] = observed

    socket_denied("dns", socket.AF_INET, socket.SOCK_DGRAM)
    socket_denied("ipv4", socket.AF_INET, socket.SOCK_STREAM)
    socket_denied("ipv6", socket.AF_INET6, socket.SOCK_STREAM)
    socket_denied("netlink", socket.AF_NETLINK, socket.SOCK_RAW)
    socket_denied("packet", socket.AF_PACKET, socket.SOCK_RAW)
    ctypes.set_errno(0)
    result = _LIBC.setns(-1, 0)
    controls["namespace_bridge"] = ctypes.get_errno() if result < 0 else 0
    syscall_controls: dict[str, int] = {}
    for label, number in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1:
        ctypes.set_errno(0)
        result = _LIBC.syscall(number, 0, 0, 0, 0, 0, 0)
        syscall_controls[label] = ctypes.get_errno() if result < 0 else 0
    ctypes.set_errno(0)
    clone_result = _LIBC.syscall(
        56,
        CLONE_NAMESPACE_FLAGS_MASK_V1 | int(signal.SIGCHLD),
        0,
        0,
        0,
        0,
    )
    clone_control_flags_errno = ctypes.get_errno() if clone_result < 0 else 0
    clone_flag_controls: dict[str, int] = {}
    for label, flag in (
        ("namespace", CLONE_NEWNS),
        ("thread", 0x00010000),
        ("untraced", 0x00800000),
        ("vm", 0x00000100),
        ("fs", 0x00000200),
        ("files", 0x00000400),
        ("sighand", 0x00000800),
    ):
        ctypes.set_errno(0)
        result = _LIBC.syscall(56, flag | int(signal.SIGCHLD), 0, 0, 0, 0)
        clone_flag_controls[label] = ctypes.get_errno() if result < 0 else 0
    return {
        "network": controls,
        "filter_syscalls": syscall_controls,
        "clone_control_flags_errno": clone_control_flags_errno,
        "clone_flag_controls": clone_flag_controls,
        "fcntl_command_controls": fcntl_command_controls,
        "futex_controls": futex_controls,
        "pipe2_controls": pipe2_controls,
        "native_syscall_exclusive_ceiling": (
            NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
        ),
        "ceiling_syscall_errno": ceiling_syscall_errno,
        "control_scope": "outer_supervisor_pre_workload_release",
        "observed_filter_sha256": observed_filter_sha256,
    }


def _seccomp_socket_control(
    process_controls: Mapping[str, object],
) -> dict[str, object]:
    """Run the exact-filter controls with bounded, pidfd-owned cleanup."""

    read_fd = -1
    write_fd = -1
    gate_read = -1
    gate_write = -1
    child = -1
    child_pidfd = -1
    child_reaped = False
    control_selector: selectors.BaseSelector | None = None
    payload = bytearray()
    try:
        read_fd, write_fd = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        child = os.fork()
        if child == 0:
            try:
                os.close(read_fd)
                os.close(gate_write)
                if os.read(gate_read, 1) != b"g":
                    os._exit(125)
                os.close(gate_read)
                os.set_blocking(write_fd, True)
                try:
                    observed_payload: dict[str, object] = {
                        "result": _seccomp_control_child_payload(write_fd)
                    }
                except CleanupIncomplete as exc:
                    observed_payload = {
                        "error_kind": "cleanup",
                        "failure": _bounded_failure(exc),
                    }
                except BaseException as exc:
                    observed_payload = {
                        "error_kind": "capability",
                        "failure": _bounded_failure(exc),
                    }
                _write_all(
                    write_fd,
                    json.dumps(
                        observed_payload,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8"),
                )
                os.close(write_fd)
            except BaseException:
                os._exit(126)
            os._exit(0)
        os.close(write_fd)
        write_fd = -1
        os.close(gate_read)
        gate_read = -1
        child_pidfd = os.pidfd_open(child)
        _write_all(gate_write, b"g")
        os.close(gate_write)
        gate_write = -1
        control_selector = selectors.DefaultSelector()
        control_selector.register(read_fd, selectors.EVENT_READ, "payload")
        control_selector.register(child_pidfd, selectors.EVENT_READ, "child")
        pipe_eof = False
        child_ready = False
        deadline_ns = time.monotonic_ns() + 5_000_000_000
        while not (pipe_eof and child_ready):
            remaining = (deadline_ns - time.monotonic_ns()) / 1_000_000_000
            if remaining <= 0:
                raise CapabilityBlocker("seccomp control exceeded its time bound")
            events = control_selector.select(timeout=min(remaining, POLL_SECONDS))
            for key, _ in events:
                if key.data == "child":
                    child_ready = True
                    continue
                while True:
                    try:
                        chunk = os.read(read_fd, 4_096)
                    except BlockingIOError:
                        break
                    if not chunk:
                        pipe_eof = True
                        break
                    payload.extend(chunk)
                    if len(payload) > 16_384:
                        raise CapabilityBlocker(
                            "seccomp control exceeded its strict byte bound"
                        )
        status_value = _bounded_waitpid_status(child, timeout=2)
        child_reaped = True
        if not os.WIFEXITED(status_value) or os.WEXITSTATUS(status_value) != 0:
            raise CapabilityBlocker("seccomp socket control child failed")
    finally:
        cleanup_failures: list[str] = []
        if control_selector is not None:
            try:
                control_selector.close()
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        # Gates close before any reap attempt so an unbound child that has not
        # been released exits by EOF rather than surviving a pidfd failure.
        for descriptor in (gate_read, gate_write, read_fd, write_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if child > 0 and not child_reaped:
            try:
                _bounded_kill_and_reap(child, child_pidfd)
                child_reaped = True
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if child_pidfd >= 0:
            try:
                os.close(child_pidfd)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if cleanup_failures:
            raise CleanupIncomplete(
                "seccomp synthetic control cleanup failed: "
                + "; ".join(cleanup_failures)
            )
    try:
        envelope = json.loads(bytes(payload).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityBlocker("seccomp control lacked structured errno") from exc
    if not isinstance(envelope, dict):
        raise CapabilityBlocker("seccomp control envelope was not an object")
    if envelope.get("error_kind") == "cleanup":
        raise CleanupIncomplete(
            f"seccomp child cleanup failed: {envelope.get('failure')}"
        )
    if envelope.get("error_kind") is not None:
        raise CapabilityBlocker(
            f"seccomp child control failed: {envelope.get('failure')}"
        )
    observed = envelope.get("result")
    if not isinstance(observed, dict):
        raise CapabilityBlocker("seccomp control was not an object")
    if set(process_controls) != {"x32_kill_control"}:
        raise CapabilityBlocker("seccomp process control set is incomplete")
    observed.update(process_controls)
    network = observed.get("network")
    filters = observed.get("filter_syscalls")
    if not isinstance(network, dict) or set(network) != {
        "dns",
        "ipv4",
        "ipv6",
        "namespace_bridge",
        "netlink",
        "packet",
    }:
        raise CapabilityBlocker("seccomp network control set is incomplete")
    if not isinstance(filters, dict) or tuple(filters) != tuple(
        sorted(name for name, _ in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1)
    ):
        raise CapabilityBlocker("seccomp privileged-control set is incomplete")
    if (
        any(value != errno.EPERM for value in (*network.values(), *filters.values()))
        or observed.get("clone_control_flags_errno") != errno.EPERM
        or observed.get("clone_flag_controls")
        != {
            "namespace": errno.EPERM,
            "thread": errno.EPERM,
            "untraced": errno.EPERM,
            "vm": errno.EPERM,
            "fs": errno.EPERM,
            "files": errno.EPERM,
            "sighand": errno.EPERM,
        }
        or observed.get("fcntl_command_controls")
        != {label: errno.EPERM for label, _ in FCNTL_DENIED_COMMANDS_V1}
        or observed.get("futex_controls")
        != {"shared_wake_errno": errno.EPERM, "private_wake_result": 0}
        or observed.get("pipe2_controls")
        != {
            "direct_errno": errno.EPERM,
            "notification_errno": errno.EPERM,
            "ordinary": True,
        }
        or observed.get("x32_kill_control") is not True
        or observed.get("native_syscall_exclusive_ceiling")
        != NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
        or observed.get("ceiling_syscall_errno") != errno.EPERM
        or observed.get("observed_filter_sha256")
        != SOCKET_DENIAL_FILTER_SHA256_V1
    ):
        raise CapabilityBlocker(
            f"seccomp control returned a non-EPERM result: {observed}"
        )
    return observed


def _mount_private_root(
    prepared: _PreparedRequest,
    temp_root: Path,
    seccomp_controls: Mapping[str, object],
) -> dict[str, object]:
    request = prepared.request
    _mount(None, "/", None, MS_REC | MS_PRIVATE)
    root_line = next(
        row
        for row in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
        if row.split()[4] == "/"
    )
    optional = root_line.split(" - ", 1)[0].split()[6:]
    if any(
        item.startswith(("shared:", "master:", "propagate_from:"))
        for item in optional
    ):
        raise CapabilityBlocker("root mount propagation is not recursive-private")

    new_root = temp_root / "private-root"
    new_root.mkdir(mode=0o700)
    _mount(
        "tmpfs",
        new_root,
        "tmpfs",
        MS_NOSUID | MS_NODEV,
        "size=16777216,nr_inodes=4096,mode=0755",
    )
    (new_root / ".old-root").mkdir()
    run_root = new_root / "run"
    run_root.mkdir(mode=0o555)
    os.chown(run_root, 0, 0)
    os.chmod(run_root, 0o555)
    provider_parent = run_root / "tool-system-provider"
    provider_parent.mkdir(mode=0o700)
    os.chown(provider_parent, 0, 0)
    os.chmod(provider_parent, 0o700)
    provider_proc = provider_parent / "proc"
    provider_proc.mkdir(mode=0o700)

    read_only_mount_observations: list[dict[str, object]] = []
    read_only_input_scans: list[dict[str, object]] = []
    total_scanned_entries = 0
    for root, descriptor in prepared.root_fds:
        target = _ensure_mount_target(new_root, root.private_path, directory=True)
        observation = _bind_fd_read_only(descriptor, target, recursive=False)
        observation["target"] = root.private_path
        if (
            observation["device"],
            observation["inode"],
            observation["mode"],
        ) != (root.device, root.inode, root.mode):
            raise IdentityMismatch(
                f"read-only root changed before release: {root.source_path}"
            )
        raw_scan = observation.get("tree_control")
        if not isinstance(raw_scan, dict):
            raise ObservationLoss("read-only root scan observation is absent")
        total_scanned_entries += int(raw_scan["entries_scanned"])
        if total_scanned_entries > 16_384:
            raise CapabilityBlocker(
                "read-only input scans exceeded their aggregate entry bound"
            )
        read_only_input_scans.append(
            {
                "root": root.to_record(),
                **{
                    key: raw_scan[key]
                    for key in (
                        "observed_device",
                        "observed_inode",
                        "entries_scanned",
                        "entry_limit",
                        "allowed_inode_types",
                        "fd_relative",
                        "nofollow",
                        "no_xdev",
                        "identity_revalidated",
                        "stable_during_scan",
                    )
                },
            }
        )
        read_only_mount_observations.append(observation)

    for item in (prepared.entrypoint, prepared.interpreter, prepared.loader):
        if item is None:
            continue
        target = _ensure_mount_target(
            new_root, item.expected.private_path, directory=False
        )
        observation = _bind_fd_read_only(
            item.sealed_fd, target, recursive=False
        )
        observation["target"] = item.expected.private_path
        if (
            observation["mode"] != item.expected.mode
            or observation["device"]
            != os.fstat(item.sealed_fd).st_dev
            or observation["inode"]
            != os.fstat(item.sealed_fd).st_ino
        ):
            raise IdentityMismatch("sealed bind identity changed before release")
        read_only_mount_observations.append(observation)

    cwd = _ensure_mount_target(
        new_root, request.filesystem.cwd_private_path, directory=True
    )
    os.chmod(cwd, 0o555)
    scratch = _ensure_mount_target(
        new_root, request.filesystem.scratch_private_path, directory=True
    )
    output = _ensure_mount_target(
        new_root, request.filesystem.output_private_path, directory=True
    )
    _mount(
        "tmpfs",
        scratch,
        "tmpfs",
        MS_NOSUID | MS_NODEV | MS_NOEXEC,
        (
            f"size={request.filesystem.scratch_byte_limit},"
            f"nr_inodes={request.filesystem.scratch_inode_limit},mode=0700"
        ),
    )
    _mount(
        "tmpfs",
        output,
        "tmpfs",
        MS_NOSUID | MS_NODEV | MS_NOEXEC,
        (
            f"size={min(request.filesystem.output_byte_limit, request.output.file_output_byte_limit)},"
            f"nr_inodes={request.filesystem.output_inode_limit},mode=0700"
        ),
    )
    private_quota_observations = {
        "observed_before_release": True,
        "scratch": _tmpfs_enforcement_observation(
            scratch,
            expected_byte_limit=request.filesystem.scratch_byte_limit,
            expected_inode_limit=request.filesystem.scratch_inode_limit,
        ),
        "output": _tmpfs_enforcement_observation(
            output,
            expected_byte_limit=request.filesystem.output_byte_limit,
            expected_inode_limit=request.filesystem.output_inode_limit,
        ),
    }
    os.chown(scratch, request.workload.uid, request.workload.gid)
    declared_output_control = _prepare_declared_output_layout(
        output,
        request.filesystem.retained_output_paths,
        uid=request.workload.uid,
        gid=request.workload.gid,
    )

    rejected = _openat2_boundary_control(
        new_root,
        output_private_path=request.filesystem.output_private_path,
        scratch_private_path=request.filesystem.scratch_private_path,
    )
    quota_controls = _quota_capability_controls(new_root)
    network = _loopback_positive_negative_control()

    host_root_device = os.stat("/").st_dev
    _pivot_root(new_root, new_root / ".old-root")
    os.chdir("/")
    _umount("/.old-root", MNT_DETACH)
    Path("/.old-root").rmdir()
    _mount(
        "proc",
        "/run/tool-system-provider/proc",
        "proc",
        MS_NOSUID | MS_NODEV | MS_NOEXEC,
    )
    os.chown("/run/tool-system-provider/proc", 0, 0)
    os.chmod("/run/tool-system-provider/proc", 0o700)
    kernel_view_read, kernel_view_write = os.pipe2(os.O_CLOEXEC)
    kernel_view_child = os.fork()
    if kernel_view_child == 0:
        os.close(kernel_view_read)
        os.setgroups([])
        os.setgid(request.workload.gid)
        os.setuid(request.workload.uid)
        denied: dict[str, int] = {}
        for label, path in (
            ("proc_view", "/proc/cpuinfo"),
            ("sys_view", "/sys/kernel"),
            ("device_view", "/dev/null"),
            ("provider_proc", "/run/tool-system-provider/proc/self/status"),
        ):
            try:
                descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
            except OSError as exc:
                denied[label] = exc.errno
            else:
                os.close(descriptor)
                denied[label] = 0
        os.write(
            kernel_view_write,
            json.dumps(denied, separators=(",", ":"), sort_keys=True).encode(
                "utf-8"
            ),
        )
        os._exit(0)
    os.close(kernel_view_write)
    kernel_view_payload = os.read(kernel_view_read, 4096)
    os.close(kernel_view_read)
    kernel_view_status = _bounded_waitpid_status(kernel_view_child, timeout=2)
    try:
        kernel_view_controls = json.loads(kernel_view_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityBlocker("kernel-view controls lacked structured errno") from exc
    if (
        not os.WIFEXITED(kernel_view_status)
        or os.WEXITSTATUS(kernel_view_status) != 0
        or not isinstance(kernel_view_controls, dict)
        or set(kernel_view_controls)
        != {"proc_view", "sys_view", "device_view", "provider_proc"}
        or kernel_view_controls
        != {
            "proc_view": errno.ENOENT,
            "sys_view": errno.ENOENT,
            "device_view": errno.ENOENT,
            "provider_proc": errno.EACCES,
        }
    ):
        raise CapabilityBlocker("kernel-view denial controls failed")
    provider_view_controls = {
        "proc_view": {
            "absent": True,
            "access_errno": kernel_view_controls["proc_view"],
            "private_pid_namespace": True,
            "provider_sensitive_paths_denied": True,
            "provider_private_access_errno": kernel_view_controls[
                "provider_proc"
            ],
        },
        "sys_view": {
            "absent": True,
            "access_errno": kernel_view_controls["sys_view"],
        },
        "device_view": {
            "absent": True,
            "access_errno": kernel_view_controls["device_view"],
        },
    }
    if os.stat("/").st_dev == host_root_device:
        raise CapabilityBlocker("pivot_root did not change root filesystem device")
    host_sentinel_hidden = not Path(str(temp_root / "host-sentinel")).exists()
    if not host_sentinel_hidden:
        raise CapabilityBlocker("host sentinel remained visible after pivot_root")
    provider_controls_hidden = not Path("/sys/fs/cgroup").exists()
    if not provider_controls_hidden:
        raise CapabilityBlocker("provider cgroup control remained visible after pivot_root")
    root_rows = [
        row
        for row in _provider_proc_root()
        .joinpath("self/mountinfo")
        .read_text(encoding="utf-8")
        .splitlines()
        if len(row.split()) >= 6 and row.split()[4] == "/"
    ]
    if len(root_rows) != 1:
        raise ObservationLoss("private root mount observation is ambiguous")
    left, right = root_rows[0].split(" - ", 1)
    root_options = set(left.split()[5].split(","))
    root_mode = os.stat("/").st_mode
    private_root_mount_observation = {
        "filesystem_type": right.split()[0],
        "mount_options": sorted(root_options & {"rw", "nodev", "nosuid"}),
        "mode": root_mode,
        "root_device_changed": os.stat("/").st_dev != host_root_device,
        "old_root_removed": not Path("/.old-root").exists(),
    }
    if private_root_mount_observation != {
        "filesystem_type": "tmpfs",
        "mount_options": ["nodev", "nosuid", "rw"],
        "mode": stat.S_IFDIR | 0o755,
        "root_device_changed": True,
        "old_root_removed": True,
    }:
        raise CapabilityBlocker("private root mount observation mismatched")
    rejected_exact = (
        "host_sentinel",
        "provider_control",
        "traversal",
        "symlink",
        "magic_link",
        "mount_crossing",
        "undeclared_output",
        "proc_view",
        "sys_view",
        "device_view",
    )
    if set(rejected) != set(rejected_exact) - {
        "host_sentinel",
        "undeclared_output",
        "proc_view",
        "sys_view",
        "device_view",
    }:
        raise CapabilityBlocker("filesystem boundary control projection mismatched")
    return {
        "private_mount_propagation": True,
        "rejected_boundary_attempts": list(rejected_exact),
        "quota_controls": quota_controls,
        "private_quota_observations": private_quota_observations,
        "read_only_mount_observations": read_only_mount_observations,
        "read_only_input_scans": read_only_input_scans,
        "declared_output_control": declared_output_control,
        "network": network,
        "seccomp_controls": seccomp_controls,
        "seccomp_filter_sha256": seccomp_controls.get(
            "observed_filter_sha256"
        ),
        "socket_denial_errno": errno.EPERM,
        "provider_view_controls": provider_view_controls,
        "private_root_mount_observation": private_root_mount_observation,
    }


def _observed_file(
    path: str,
    descriptor: int,
    *,
    deadline_ns: int | None = None,
) -> dict[str, object]:
    before = os.fstat(descriptor)
    digest = _sha256_fd(descriptor, deadline_ns=deadline_ns)
    after = os.fstat(descriptor)
    stable_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, name) != getattr(after, name) for name in stable_fields):
        raise ObservationLoss(f"file identity changed while hashing: {path}")
    return {
        "path": path,
        "device": after.st_dev,
        "inode": after.st_ino,
        "mode": after.st_mode,
        "size": after.st_size,
        "sha256": digest,
    }


def _ptrace_exec_observation(
    pid: int,
    prepared: _PreparedRequest,
    expected_stdio: Mapping[int, tuple[int, int, int]],
    baseline_seccomp_filters: int,
) -> dict[str, object]:
    request = prepared.request
    global_file_size_limit = max(
        request.filesystem.scratch_byte_limit,
        request.output.file_output_byte_limit,
    )
    actual_exec_path = _provider_proc_root() / str(pid) / "exe"
    actual_exec_fd = os.open(actual_exec_path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        actual_interpreter_or_entry = _observed_file(
            str(actual_exec_path), actual_exec_fd
        )
    finally:
        os.close(actual_exec_fd)
    status_rows = _status_rows(pid)
    if request.executable.format is ExecutableFormatV1.SCRIPT:
        script_fd = _safe_absolute_open(request.executable.entrypoint.private_path)
        try:
            actual_entrypoint = _observed_file(
                request.executable.entrypoint.private_path, script_fd
            )
        finally:
            os.close(script_fd)
        actual_interpreter = actual_interpreter_or_entry
    else:
        actual_entrypoint = actual_interpreter_or_entry
        actual_interpreter = None
    actual_loader: dict[str, object] | None = None
    loader_match = prepared.loader is None
    if prepared.loader is not None:
        loader_fd = _safe_absolute_open(prepared.loader.expected.private_path)
        try:
            actual_loader = _observed_file(
                prepared.loader.expected.private_path, loader_fd
            )
            loader_match = _loader_identity_observed(
                pid, os.fstat(prepared.loader.sealed_fd)
            )
        finally:
            os.close(loader_fd)
    fd_set = _fd_set_at_exec(pid)
    file_size_limits = _file_size_limits(pid)
    core_size_limits = _core_size_limits(pid)
    actual_argv = _read_proc_nul_vector(pid, "cmdline")
    raw_environment = _read_proc_nul_vector(pid, "environ")
    try:
        actual_environment = tuple(
            tuple(item.split("=", 1)) for item in raw_environment
        )
    except (TypeError, ValueError) as exc:
        raise ObservationLoss("exec-stop environment was malformed") from exc
    if any(len(item) != 2 for item in actual_environment):
        raise ObservationLoss("exec-stop environment lacked NAME=value entries")
    expected_argv = (
        (
            request.executable.interpreter.private_path,
            request.executable.entrypoint.private_path,
            *request.executable.argv[1:],
        )
        if request.executable.format is ExecutableFormatV1.SCRIPT
        and request.executable.interpreter is not None
        else request.executable.argv
    )
    expected_environment = request.executable.environment
    if actual_argv != expected_argv or actual_environment != expected_environment:
        raise IdentityMismatch("exec-stop argv/environment differs from request")
    stdio_observed: dict[str, dict[str, int]] = {}
    for descriptor in (0, 1, 2):
        value = os.stat(_provider_proc_root() / str(pid) / "fd" / str(descriptor))
        actual = (value.st_dev, value.st_ino, value.st_mode)
        if actual != expected_stdio[descriptor] or not stat.S_ISFIFO(value.st_mode):
            raise ObservationLoss(
                f"exec-stop stdio descriptor {descriptor} was not provider-owned pipe"
            )
        stdio_observed[str(descriptor)] = {
            "device": value.st_dev,
            "inode": value.st_ino,
            "mode": value.st_mode,
        }
    observation = {
        "actual_entrypoint": actual_entrypoint,
        "actual_interpreter": actual_interpreter,
        "actual_loader": actual_loader,
        "loader_map_identity_match": loader_match,
        "uid": status_rows.get("Uid"),
        "gid": status_rows.get("Gid"),
        "groups": status_rows.get("Groups", ""),
        "cap_eff": status_rows.get("CapEff"),
        "no_new_privs": status_rows.get("NoNewPrivs"),
        "fd_set": list(fd_set),
        "stdio_pipe_identities": stdio_observed,
        "stdio_provider_match": True,
        "file_size_soft_limit": file_size_limits[0],
        "file_size_hard_limit": file_size_limits[1],
        "core_soft_limit": core_size_limits[0],
        "core_hard_limit": core_size_limits[1],
        "seccomp_mode": status_rows.get("Seccomp"),
        "seccomp_filters": status_rows.get("Seccomp_filters"),
        "baseline_seccomp_filters": baseline_seccomp_filters,
        "seccomp_filter_delta": 1,
        "effective_argv_sha256": canonical_sha256(list(actual_argv)),
        "effective_argv_count": len(actual_argv),
        "effective_environment_sha256": canonical_sha256(
            [list(item) for item in actual_environment]
        ),
        "effective_environment_count": len(actual_environment),
        "inherited_network_fd_absent": all(value <= 2 for value in fd_set),
        "secondary_exec_policy": {
            "execve": 59,
            "execveat": 322,
            "ptrace_entry_denial": True,
            "ptrace_event_exec_backstop": True,
        },
    }
    expected_exec = (
        prepared.interpreter.sealed_identity
        if request.executable.format is ExecutableFormatV1.SCRIPT
        and prepared.interpreter is not None
        else prepared.entrypoint.sealed_identity
    )
    actual_exec = (
        actual_interpreter
        if request.executable.format is ExecutableFormatV1.SCRIPT
        else actual_entrypoint
    )
    if actual_exec is None or any(
        actual_exec.get(key) != expected_exec.get(key)
        for key in ("device", "inode", "mode", "size", "sha256")
    ):
        raise IdentityMismatch("ptrace executable identity differs from sealed object")
    if request.executable.format is ExecutableFormatV1.SCRIPT and any(
        actual_entrypoint.get(key) != prepared.entrypoint.sealed_identity.get(key)
        for key in ("device", "inode", "mode", "size", "sha256")
    ):
        raise IdentityMismatch("private-root script identity differs from sealed object")
    if prepared.loader is not None and (
        not loader_match
        or actual_loader is None
        or any(
            actual_loader.get(key) != prepared.loader.sealed_identity.get(key)
            for key in ("device", "inode", "mode", "size", "sha256")
        )
    ):
        raise IdentityMismatch("loader map identity differs from sealed loader")
    expected_uid = str(request.workload.uid)
    expected_gid = str(request.workload.gid)
    uid_values = str(observation["uid"]).split()
    gid_values = str(observation["gid"]).split()
    try:
        seccomp_filters = int(str(observation["seccomp_filters"]))
    except ValueError as exc:
        raise ObservationLoss("exec-stop seccomp filter count is invalid") from exc
    if not (
        isinstance(observation["uid"], str)
        and uid_values == [expected_uid] * 4
        and isinstance(observation["gid"], str)
        and gid_values == [expected_gid] * 4
        and str(observation["groups"]).strip() == ""
        and int(str(observation["cap_eff"]), 16) == 0
        and observation["no_new_privs"] == "1"
        and observation["seccomp_mode"] == "2"
        and seccomp_filters == baseline_seccomp_filters + 1
        and file_size_limits
        == (
            global_file_size_limit,
            global_file_size_limit,
        )
        and core_size_limits == (0, 0)
        and observation["inherited_network_fd_absent"] is True
        and observation["stdio_provider_match"] is True
    ):
        raise ObservationLoss("exec-stop workload identity/FD observation mismatched")
    return observation


def _await_event_ack(descriptor: int, request: IsolationRequestV1) -> None:
    deadline_ns = min(
        request.process.deadline_monotonic_ns
        + request.process.termination_grace_ns,
        time.monotonic_ns() + 5_000_000_000,
    )
    selector = selectors.DefaultSelector()
    try:
        selector.register(descriptor, selectors.EVENT_READ)
        remaining = max(0.0, (deadline_ns - time.monotonic_ns()) / 1_000_000_000)
        if not selector.select(timeout=remaining):
            raise ObservationLoss("outer member-binding acknowledgement timed out")
        if os.read(descriptor, 1) != b"a":
            raise ObservationLoss("outer member-binding acknowledgement was absent")
    finally:
        selector.close()


def _trace_workload(
    prepared: _PreparedRequest,
    report_writer: _ReportWriter,
    stdout_fd: int,
    stderr_fd: int,
    event_ack_fd: int,
) -> None:
    request = prepared.request
    global_file_size_limit = max(
        request.filesystem.scratch_byte_limit,
        request.output.file_output_byte_limit,
    )
    try:
        baseline_seccomp_filters = int(
            _status_rows(os.getpid()).get("Seccomp_filters", "0")
        )
    except ValueError as exc:
        raise ObservationLoss("provider seccomp baseline was not numeric") from exc
    stdin_fd, stdin_write = os.pipe2(os.O_CLOEXEC)
    os.close(stdin_write)
    expected_stdio = {
        descriptor: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
        )
        for descriptor, value in (
            (0, os.fstat(stdin_fd)),
            (1, os.fstat(stdout_fd)),
            (2, os.fstat(stderr_fd)),
        )
    }
    child = os.fork()
    if child == 0:
        try:
            os.dup2(stdin_fd, 0)
            os.dup2(stdout_fd, 1)
            os.dup2(stderr_fd, 2)
            if stdin_fd not in {0, 1, 2}:
                os.close(stdin_fd)
            if stdout_fd not in {1, 2}:
                os.close(stdout_fd)
            if stderr_fd not in {1, 2}:
                os.close(stderr_fd)
            if _LIBC.ptrace(PTRACE_TRACEME, 0, None, None) != 0:
                _raise_errno("ptrace(TRACEME)")
            os.kill(os.getpid(), signal.SIGSTOP)
            exec_item = (
                prepared.interpreter
                if request.executable.format is ExecutableFormatV1.SCRIPT
                else prepared.entrypoint
            )
            if exec_item is None:
                raise IdentityMismatch("script interpreter was not sealed")
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (
                    global_file_size_limit,
                    global_file_size_limit,
                ),
            )
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            _drop_workload_identity(request, {exec_item.sealed_fd})
            environment = dict(request.executable.environment)
            if request.executable.format is ExecutableFormatV1.SCRIPT:
                argv = (
                    request.executable.interpreter.private_path,
                    request.executable.entrypoint.private_path,
                    *request.executable.argv[1:],
                )
            else:
                argv = request.executable.argv
            os.chdir(request.filesystem.cwd_private_path)
            _execveat(exec_item.sealed_fd, tuple(argv), environment)
        except BaseException:
            os._exit(126)
        os._exit(127)

    os.close(stdin_fd)

    first_status = _bounded_waitpid_status(
        child, timeout=2, include_stops=True
    )
    if not os.WIFSTOPPED(first_status):
        raise ObservationLoss("workload did not enter initial ptrace stop")
    options = (
        PTRACE_O_TRACESYSGOOD
        |
        PTRACE_O_TRACEEXEC
        | PTRACE_O_TRACEFORK
        | PTRACE_O_TRACEVFORK
        | PTRACE_O_TRACECLONE
        | PTRACE_O_TRACEEXIT
        | PTRACE_O_EXITKILL
    )
    if _LIBC.ptrace(PTRACE_SETOPTIONS, child, None, options) != 0:
        _raise_errno("ptrace(SETOPTIONS)")
    if _LIBC.ptrace(PTRACE_SYSCALL, child, None, None) != 0:
        _raise_errno("ptrace(SYSCALL)")

    event_classes: set[str] = set()
    exec_observation: dict[str, object] | None = None
    root_exit_code: int | None = None
    root_exit_monotonic_ns: int | None = None
    root_exit_reported = False
    # A stopped tracee is the only authority for its syscall entry arguments.
    # Preserve the exact entry snapshot until the matching syscall-exit stop;
    # descendants auto-attached at fork begin inside the inherited fork syscall.
    syscall_entries: dict[int, dict[str, object]] = {}
    synthetic_child_stops: set[int] = set()
    limit_reported = False
    while True:
        try:
            waited_pid, status_value = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            time.sleep(POLL_SECONDS)
            continue
        if waited_pid == 0:
            time.sleep(POLL_SECONDS)
            continue
        if os.WIFEXITED(status_value):
            syscall_entries.pop(waited_pid, None)
            event_classes.add("exit")
            if waited_pid == child:
                root_exit_code = os.WEXITSTATUS(status_value)
        elif os.WIFSIGNALED(status_value):
            syscall_entries.pop(waited_pid, None)
            event_classes.add("signal_exit")
            if waited_pid == child:
                root_exit_code = 128 + os.WTERMSIG(status_value)
        elif os.WIFSTOPPED(status_value):
            event = status_value >> 16
            delivered_signal = 0
            resume_tracee = True
            stopped_by = os.WSTOPSIG(status_value)
            if event == PTRACE_EVENT_EXEC:
                event_classes.add("exec")
                exec_bound = _BoundPid.bind(
                    waited_pid,
                    f"/{request.execution_id}/composition",
                )
                exec_bound.close()
                if waited_pid != child or exec_observation is not None:
                    if _LIBC.ptrace(PTRACE_KILL, waited_pid, None, None) != 0:
                        number = ctypes.get_errno()
                        if number != errno.ESRCH:
                            _raise_errno("ptrace(KILL unauthorized exec)")
                    raise IdentityMismatch(
                        "secondary or descendant exec is outside the v1 request"
                    )
                initial_exec_entry = syscall_entries.get(waited_pid)
                if (
                    not isinstance(initial_exec_entry, dict)
                    or initial_exec_entry.get("syscall_number") not in {59, 322}
                    or initial_exec_entry.get("blocked_exec") is True
                ):
                    raise ObservationLoss(
                        "initial PTRACE_EVENT_EXEC lacked its syscall-entry state"
                    )
                # Linux emits the successful exec event before the matching
                # syscall-exit stop.  Retain this entry so that exit is
                # consumed as an exit, not inverted into a new post-exec
                # syscall entry that could fabricate an exec denial.
                initial_exec_entry["initial_exec_exit"] = True
                exec_observation = _ptrace_exec_observation(
                    waited_pid,
                    prepared,
                    expected_stdio,
                    baseline_seccomp_filters,
                )
                exec_observation.update(
                    {
                        "exec_pid": waited_pid,
                        "exec_starttime_ticks": _proc_starttime(waited_pid),
                        "exec_cgroup": _proc_cgroup(waited_pid),
                    }
                )
                report_writer.write(
                    {"kind": "ptrace_exec", **exec_observation},
                )
                _await_event_ack(event_ack_fd, request)
            elif event in {
                PTRACE_EVENT_FORK,
                PTRACE_EVENT_VFORK,
                PTRACE_EVENT_CLONE,
            }:
                event_class = {
                        PTRACE_EVENT_FORK: "fork",
                        PTRACE_EVENT_VFORK: "vfork",
                        PTRACE_EVENT_CLONE: "clone",
                    }[event]
                event_classes.add(event_class)
                child_message = ctypes.c_ulong()
                if _LIBC.ptrace(
                    PTRACE_GETEVENTMSG,
                    waited_pid,
                    None,
                    ctypes.byref(child_message),
                ) != 0:
                    _raise_errno("ptrace(GETEVENTMSG child)")
                new_child = int(child_message.value)
                synthetic_child_stops.add(new_child)
                syscall_entries[new_child] = {
                    "syscall_number": -1,
                    "limit_kind": None,
                    "target": None,
                    "target_error": None,
                }
                report_writer.write(
                    {
                        "kind": "member_birth",
                        "pid": new_child,
                        "starttime_ticks": _proc_starttime(new_child),
                        "cgroup_path": _proc_cgroup(new_child),
                        "monotonic_ns": time.monotonic_ns(),
                    }
                )
                _await_event_ack(event_ack_fd, request)
                report_writer.write(
                    {
                        "kind": "process_event",
                        "event_classes": [event_class],
                        "monotonic_ns": time.monotonic_ns(),
                    }
                )
            elif event == PTRACE_EVENT_EXIT:
                event_classes.add("exit_stop")
                committed_status = ctypes.c_ulong()
                if _LIBC.ptrace(
                    PTRACE_GETEVENTMSG,
                    waited_pid,
                    None,
                    ctypes.byref(committed_status),
                ) != 0:
                    _raise_errno("ptrace(GETEVENTMSG exit)")
                raw_status = int(committed_status.value)
                if os.WIFEXITED(raw_status):
                    event_classes.add("exit")
                    committed_exit = os.WEXITSTATUS(raw_status)
                elif os.WIFSIGNALED(raw_status):
                    event_classes.add("signal_exit")
                    committed_exit = 128 + os.WTERMSIG(raw_status)
                else:
                    raise ObservationLoss("ptrace exit-stop status was invalid")
                report_writer.write(
                    {
                        "kind": "member_exit_stop",
                        "pid": waited_pid,
                        "starttime_ticks": _proc_starttime(waited_pid),
                        "cgroup_path": _proc_cgroup(waited_pid),
                        "monotonic_ns": time.monotonic_ns(),
                    }
                )
                _await_event_ack(event_ack_fd, request)
                report_writer.write(
                    {
                        "kind": "process_event",
                        "event_classes": [
                            "exit_stop",
                            "exit" if os.WIFEXITED(raw_status) else "signal_exit",
                        ],
                        "monotonic_ns": time.monotonic_ns(),
                    }
                )
                if waited_pid == child:
                    root_exit_code = committed_exit
                    root_exit_monotonic_ns = time.monotonic_ns()
                # The outer supervisor has pidfd-bound and revalidated this
                # exact stopped identity before acknowledgement.  It is now
                # safe to let the committed exit complete so ordinary
                # fork/wait and reparenting semantics remain intact.
                resume_tracee = True
            elif stopped_by == signal.SIGTRAP | 0x80:
                if waited_pid in syscall_entries:
                    entry = syscall_entries.pop(waited_pid)
                    registers = UserRegsStructX86_64()
                    if _LIBC.ptrace(
                        PTRACE_GETREGS,
                        waited_pid,
                        None,
                        ctypes.byref(registers),
                    ) != 0:
                        _raise_errno("ptrace(GETREGS syscall-exit)")
                    signed_rax = ctypes.c_longlong(registers.rax).value
                    syscall_number = int(entry["syscall_number"])
                    if entry.get("initial_exec_exit") is True:
                        if signed_rax < 0:
                            raise ObservationLoss(
                                "initial exec reported a failing syscall-exit"
                            )
                        target = None
                        quota_errno = False
                    elif entry.get("blocked_exec") is True:
                        registers.rax = (1 << 64) - errno.EPERM
                        if _LIBC.ptrace(
                            PTRACE_SETREGS,
                            waited_pid,
                            None,
                            ctypes.byref(registers),
                        ) != 0:
                            _raise_errno("ptrace(SETREGS exec denial)")
                        denial_monotonic_ns = time.monotonic_ns()
                        report_writer.write(
                            {
                                "kind": "secondary_exec_denial",
                                "pid": waited_pid,
                                "starttime_ticks": _proc_starttime(waited_pid),
                                "cgroup_path": _proc_cgroup(waited_pid),
                                "syscall_number": syscall_number,
                                "errno": errno.EPERM,
                                "monotonic_ns": denial_monotonic_ns,
                            }
                        )
                        _await_event_ack(event_ack_fd, request)
                        event_classes.add("exec_denied")
                        report_writer.write(
                            {
                                "kind": "process_event",
                                "event_classes": ["exec_denied"],
                                "monotonic_ns": denial_monotonic_ns,
                            }
                        )
                        target = None
                        quota_errno = False
                    else:
                        target = entry.get("target")
                        quota_errno = signed_rax in {
                            -errno.ENOSPC,
                            -errno.EFBIG,
                            -errno.EDQUOT,
                        }
                    if (
                        quota_errno
                        and entry.get("limit_kind")
                        == "unattributed_path_quota_errno"
                    ):
                        raise ObservationLoss(
                            "path-backed quota errno cannot be attributed "
                            "to a stable private object in v1"
                        )
                    if quota_errno and entry.get("target_error") is not None:
                        raise ObservationLoss(
                            "quota syscall target could not be bound at entry: "
                            f"{entry['target_error']}"
                        )
                    if (
                        quota_errno
                        and entry.get("limit_kind") == "syscall_errno"
                        and not isinstance(target, dict)
                    ):
                        raise ObservationLoss(
                            "FD-backed quota errno lacked an exact private target"
                        )
                    requested_bytes = entry.get("requested_bytes")
                    if (
                        type(requested_bytes) is int
                        and signed_rax > 0
                        and signed_rax < requested_bytes
                    ):
                        if not isinstance(target, dict):
                            raise ObservationLoss(
                                "short FD write lacked an exact private target"
                            )
                        raise ObservationLoss(
                            "private filesystem write completed short; quota cause "
                            "cannot be distinguished without terminal saturation"
                        )
                    if (
                        isinstance(target, dict)
                        and quota_errno
                        and not limit_reported
                    ):
                        limit_kind = entry.get("limit_kind")
                        if limit_kind != "syscall_errno":
                            raise ObservationLoss(
                                "quota syscall entry classification was invalid"
                            )
                        report_writer.write(
                            {
                                "kind": "limit_candidate",
                                "limit_kind": limit_kind,
                                **target,
                                "syscall_number": syscall_number,
                                "errno": -signed_rax,
                                "signal_number": None,
                                "pid": waited_pid,
                                "starttime_ticks": _proc_starttime(waited_pid),
                                "cgroup_path": _proc_cgroup(waited_pid),
                                "monotonic_ns": time.monotonic_ns(),
                            }
                        )
                        limit_reported = True
                        resume_tracee = False
                else:
                    registers = UserRegsStructX86_64()
                    if _LIBC.ptrace(
                        PTRACE_GETREGS,
                        waited_pid,
                        None,
                        ctypes.byref(registers),
                    ) != 0:
                        _raise_errno("ptrace(GETREGS syscall-entry)")
                    entry = _quota_syscall_entry(
                        waited_pid,
                        registers,
                        request,
                    )
                    if (
                        exec_observation is not None
                        and int(registers.orig_rax) in {59, 322}
                    ):
                        entry["blocked_exec"] = True
                        registers.orig_rax = (1 << 64) - 1
                        if _LIBC.ptrace(
                            PTRACE_SETREGS,
                            waited_pid,
                            None,
                            ctypes.byref(registers),
                        ) != 0:
                            _raise_errno("ptrace(SETREGS exec entry denial)")
                    syscall_entries[waited_pid] = entry
            else:
                if (
                    stopped_by == signal.SIGSTOP
                    and waited_pid in synthetic_child_stops
                ):
                    synthetic_child_stops.remove(waited_pid)
                elif stopped_by == signal.SIGBUS:
                    # SIGBUS can be caused by a private-tmpfs allocation
                    # failure, but siginfo plus mount saturation cannot prove
                    # that causal link.  It therefore cannot be promoted to a
                    # quota LIMIT, and it also cannot be allowed to become a
                    # handled false SUCCESS.
                    raise ObservationLoss(
                        "workload SIGBUS cannot be attributed safely in v1"
                    )
                else:
                    delivered_signal = stopped_by
            if resume_tracee:
                if _LIBC.ptrace(
                    PTRACE_SYSCALL,
                    waited_pid,
                    None,
                    ctypes.c_void_p(delivered_signal),
                ) != 0:
                    number = ctypes.get_errno()
                    if number != errno.ESRCH:
                        _raise_errno("ptrace(SYSCALL event)")
        if root_exit_code is not None and not root_exit_reported:
            if exec_observation is None:
                raise ObservationLoss("PTRACE_EVENT_EXEC observation was missing")
            report_writer.write(
                {
                    "kind": "workload_exit",
                    "exit_code": root_exit_code,
                    "exit_observed_monotonic_ns": root_exit_monotonic_ns,
                    "event_classes": sorted(event_classes),
                },
            )
            root_exit_reported = True


def _namespace_init(
    prepared: _PreparedRequest,
    temp_root: Path,
    report_fd: int,
    gate_fd: int,
    stdout_fd: int,
    stderr_fd: int,
    snapshot_socket_fd: int,
    event_ack_fd: int,
    parent_namespaces: Mapping[str, str],
    seccomp_controls: Mapping[str, object],
) -> None:
    report_writer = _ReportWriter(
        report_fd, prepared.request.output.structured_result_byte_limit
    )
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        os.set_blocking(stdout_fd, True)
        os.set_blocking(stderr_fd, True)
        namespace_ids = _namespace_links()
        if any(
            namespace_ids[name] == parent_namespaces[name]
            for name in namespace_ids
        ):
            raise CapabilityBlocker("one or more required namespaces are not distinct")
        previous_umask = os.umask(0o077)
        try:
            setup = _mount_private_root(prepared, temp_root, seccomp_controls)
        finally:
            os.umask(previous_umask)
        scratch_fd = os.open(
            prepared.request.filesystem.scratch_private_path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
        )
        output_fd = os.open(
            prepared.request.filesystem.output_private_path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
        )
        try:
            _send_snapshot_fds(snapshot_socket_fd, scratch_fd, output_fd)
        finally:
            os.close(scratch_fd)
            os.close(output_fd)
            os.close(snapshot_socket_fd)
            snapshot_socket_fd = -1
        report_writer.write(
            {
                "kind": "ready",
                "namespace_ids": namespace_ids,
                **setup,
            },
        )
        if os.read(gate_fd, 1) != b"g":
            raise ObservationLoss("workload release gate closed without authorization")
        _trace_workload(
            prepared,
            report_writer,
            stdout_fd,
            stderr_fd,
            event_ack_fd,
        )
    except BaseException as exc:
        try:
            report_writer.write(
                {"kind": "failure", "failure": _bounded_failure(exc)},
            )
        except BaseException:
            pass
        if snapshot_socket_fd >= 0:
            try:
                os.close(snapshot_socket_fd)
            except OSError:
                pass
        os._exit(125)


def _namespace_anchor(
    prepared: _PreparedRequest,
    temp_root: Path,
    report_fd: int,
    placement_gate_fd: int,
    gate_fd: int,
    stdout_fd: int,
    stderr_fd: int,
    snapshot_socket_fd: int,
    event_ack_fd: int,
    parent_namespaces: Mapping[str, str],
    seccomp_controls: Mapping[str, object],
) -> None:
    report_writer = _ReportWriter(
        report_fd, prepared.request.output.structured_result_byte_limit
    )
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if os.read(placement_gate_fd, 1) != b"p":
            raise ObservationLoss("cgroup placement gate was not released")
        os.close(placement_gate_fd)
        _unshare(REQUIRED_NAMESPACE_FLAGS)
        child = os.fork()
        if child == 0:
            _namespace_init(
                prepared,
                temp_root,
                report_fd,
                gate_fd,
                stdout_fd,
                stderr_fd,
                snapshot_socket_fd,
                event_ack_fd,
                parent_namespaces,
                seccomp_controls,
            )
            os._exit(0)
        for descriptor in (
            report_fd,
            gate_fd,
            stdout_fd,
            stderr_fd,
            snapshot_socket_fd,
            event_ack_fd,
        ):
            try:
                os.close(descriptor)
            except OSError:
                pass
        remaining_seconds = max(
            1.0,
            (
                prepared.request.process.deadline_monotonic_ns
                + prepared.request.process.termination_grace_ns
                + 10_000_000_000
                - time.monotonic_ns()
            )
            / 1_000_000_000,
        )
        _bounded_waitpid_status(child, timeout=remaining_seconds)
    except BaseException as exc:
        try:
            report_writer.write(
                {"kind": "failure", "failure": _bounded_failure(exc)},
            )
        except BaseException:
            pass
        os._exit(124)
    os._exit(0)


def _auxiliary_cgroup_control(path: Path, *, mode: str) -> dict[str, object]:
    if mode not in {"stream", "timeout", "seccomp_process"}:
        raise ValueError(f"unknown auxiliary control: {mode}")
    gate_read = gate_write = payload_read = payload_write = -1
    child = pidfd = -1
    child_reaped = False
    placed = False
    cleanup_failures: list[str] = []
    try:
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        payload_read, payload_write = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        child = os.fork()
        if child == 0:
            try:
                os.close(gate_write)
                os.close(payload_read)
                if os.read(gate_read, 1) != b"g":
                    os._exit(125)
                os.close(gate_read)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                if mode == "stream":
                    os.set_blocking(payload_write, True)
                    while True:
                        os.write(payload_write, b"s" * 4096)
                if mode == "seccomp_process":
                    os.set_blocking(payload_write, True)
                    _install_seccomp_filter()
                    fork_child = os.fork()
                    if fork_child == 0:
                        os._exit(0)
                    fork_positive = _bounded_seccomp_nested_child(
                        fork_child,
                        lambda status_value: os.WIFEXITED(status_value)
                        and os.WEXITSTATUS(status_value) == 0,
                    )
                    _write_all(
                        payload_write,
                        canonical_json_bytes(
                            {
                                "ordinary_fork_positive": fork_positive,
                                "ordinary_vfork_positive": (
                                    _vfork_positive_control()
                                ),
                            }
                        )
                        + b"\n",
                    )
                while True:
                    signal.pause()
            except BaseException:
                os._exit(126)
        os.close(gate_read)
        gate_read = -1
        os.close(payload_write)
        payload_write = -1
        (path / "cgroup.procs").write_text(str(child), encoding="ascii")
        placed = True
        expected_cgroup = _proc_cgroup(child)
        if expected_cgroup != f"/{path.parent.name}/{path.name}":
            raise ObservationLoss("auxiliary child cgroup placement mismatched")
        bound = _BoundPid.bind(child, expected_cgroup)
        pidfd = bound.pidfd
        bound.pidfd = -1
        _set_cgroup_frozen(path, True)
        if _cgroup_frozen(path) != 1:
            raise CapabilityBlocker("auxiliary cgroup freeze positive control failed")
        _set_cgroup_frozen(path, False)
        if _cgroup_frozen(path) != 0:
            raise CapabilityBlocker("auxiliary cgroup freeze negative control failed")
        os.write(gate_write, b"g")
        os.close(gate_write)
        gate_write = -1
        started = time.monotonic_ns()
        observed_bytes = 0
        process_controls: dict[str, object] = {}
        if mode == "stream":
            deadline = started + 5_000_000_000
            while observed_bytes <= 8_192 and time.monotonic_ns() < deadline:
                selector = selectors.DefaultSelector()
                try:
                    selector.register(payload_read, selectors.EVENT_READ)
                    if not selector.select(timeout=POLL_SECONDS):
                        continue
                finally:
                    selector.close()
                try:
                    chunk = os.read(payload_read, 4096)
                except BlockingIOError:
                    continue
                if not chunk:
                    break
                observed_bytes += len(chunk)
            if observed_bytes <= 8_192:
                raise CapabilityBlocker("raw stream control did not exceed its limit")
        elif mode == "timeout":
            deadline = started + 25_000_000
            _wait_until(
                lambda: time.monotonic_ns() >= deadline,
                deadline + 100_000_000,
                "auxiliary monotonic deadline",
            )
        else:
            buffer = bytearray()
            deadline = started + 5_000_000_000
            selector = selectors.DefaultSelector()
            try:
                selector.register(payload_read, selectors.EVENT_READ)
                while b"\n" not in buffer:
                    remaining = (deadline - time.monotonic_ns()) / 1_000_000_000
                    if remaining <= 0:
                        raise CapabilityBlocker(
                            "filtered fork/vfork control exceeded its time bound"
                        )
                    if not selector.select(timeout=min(POLL_SECONDS, remaining)):
                        continue
                    chunk = os.read(payload_read, 4_096)
                    if not chunk:
                        raise CapabilityBlocker(
                            "filtered fork/vfork control exited without a result"
                        )
                    buffer.extend(chunk)
                    if len(buffer) > 4_096:
                        raise ObservationLoss(
                            "filtered fork/vfork result exceeded its byte bound"
                        )
            finally:
                selector.close()
            line, remainder = buffer.split(b"\n", 1)
            if remainder:
                raise ObservationLoss(
                    "filtered fork/vfork control emitted trailing data"
                )
            value = json.loads(line.decode("utf-8"))
            if value != {
                "ordinary_fork_positive": True,
                "ordinary_vfork_positive": True,
            }:
                raise CapabilityBlocker(
                    f"filtered fork/vfork control failed: {value!r}"
                )
            process_controls = value
        populated_before = _cgroup_populated(path)
        if populated_before != 1:
            raise ObservationLoss("auxiliary cgroup was not populated before kill")
        (path / "cgroup.kill").write_text("1", encoding="ascii")
        selector = selectors.DefaultSelector()
        try:
            selector.register(pidfd, selectors.EVENT_READ)
            pidfd_exit = bool(selector.select(timeout=2))
        finally:
            selector.close()
        if not pidfd_exit:
            _bounded_kill_and_reap(child, pidfd)
            child_reaped = True
            raise ObservationLoss(f"{mode} control lacked pidfd exit")
        _bounded_kill_and_reap(child, pidfd)
        child_reaped = True
        _wait_until(
            lambda: _cgroup_populated(path) == 0,
            time.monotonic_ns() + 5_000_000_000,
            f"{mode} control populated=0",
        )
        return {
            "mode": mode,
            "observed_bytes": observed_bytes,
            "monotonic_elapsed_ns": time.monotonic_ns() - started,
            "populated_before_kill": populated_before,
            "cgroup_kill_written": True,
            "pidfd_exit_observed": True,
            "populated_zero": True,
            "freeze_positive_control": True,
            "unfreeze_positive_control": True,
            **process_controls,
        }
    finally:
        # Closing gates first makes a child that was never pidfd-bound exit by
        # EOF.  Every later cleanup step is independent and failure-accumulating.
        for descriptor in (gate_write, gate_read, payload_read, payload_write):
            try:
                if descriptor >= 0:
                    os.close(descriptor)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if child > 0 and not child_reaped:
            try:
                waited, _ = os.waitpid(child, os.WNOHANG)
            except ChildProcessError:
                waited = child
            except BaseException as exc:
                waited = 0
                cleanup_failures.append(_bounded_failure(exc))
            if waited == child:
                child_reaped = True
            else:
                if placed:
                    try:
                        (path / "cgroup.kill").write_text("1", encoding="ascii")
                    except BaseException as exc:
                        cleanup_failures.append(_bounded_failure(exc))
                try:
                    if pidfd >= 0:
                        _bounded_kill_and_reap(child, pidfd)
                    else:
                        _bounded_waitpid_status(child, timeout=2)
                    child_reaped = True
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if placed:
            try:
                if _cgroup_populated(path):
                    (path / "cgroup.kill").write_text("1", encoding="ascii")
                _wait_until(
                    lambda: _cgroup_populated(path) == 0,
                    time.monotonic_ns() + 5_000_000_000,
                    f"{mode} cleanup populated=0",
                )
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if pidfd >= 0:
            try:
                os.close(pidfd)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        if cleanup_failures:
            raise CleanupIncomplete(
                f"{mode} auxiliary control cleanup failed: "
                + "; ".join(cleanup_failures)
            )


def _decode_json_lines(buffer: bytearray) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    while b"\n" in buffer:
        line, remainder = buffer.split(b"\n", 1)
        buffer[:] = remainder
        if not line:
            continue
        if len(line) > 1_048_576:
            raise ObservationLoss("internal observation line exceeded one MiB")
        value = json.loads(line.decode("utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("kind"), str):
            raise ObservationLoss("internal observation shape is invalid")
        values.append(value)
    if len(buffer) > 1_048_576:
        raise ObservationLoss("unterminated internal observation exceeded one MiB")
    return values


def _consume_json_line_batch(
    buffer: bytearray,
    consume: Callable[[dict[str, object]], bool],
) -> bool:
    """Consume every complete record even after a terminal record is seen."""

    terminal = False
    for value in _decode_json_lines(buffer):
        terminal = bool(consume(value)) or terminal
    return terminal


def _merge_process_event_classes(
    record: _RunRecord, raw_classes: object
) -> None:
    if not isinstance(raw_classes, list) or not raw_classes or not all(
        isinstance(item, str) for item in raw_classes
    ):
        raise ObservationLoss("process event classes are malformed")
    allowed = {
        "exec",
        "exec_denied",
        "fork",
        "vfork",
        "clone",
        "exit_stop",
        "exit",
        "signal_exit",
    }
    values = set(str(item) for item in raw_classes)
    if not values.issubset(allowed):
        raise ObservationLoss("process event class is unknown")
    current = record.process.get("event_classes", [])
    if not isinstance(current, list):
        raise ObservationLoss("process event accumulator is malformed")
    record.process["event_classes"] = sorted(set(current) | values)


@dataclass
class _RunRecord:
    started_ns: int
    finished_ns: int = 0
    stage_status: dict[str, tuple[str, str | None]] = field(default_factory=dict)
    observations: list[tuple[str, str, dict[str, object], int]] = field(
        default_factory=list
    )
    provider_errors: list[str] = field(default_factory=list)
    observer_errors: list[str] = field(default_factory=list)
    setup: dict[str, object] = field(default_factory=dict)
    exec_observation: dict[str, object] = field(default_factory=dict)
    exit_observation: dict[str, object] = field(default_factory=dict)
    process: dict[str, object] = field(default_factory=dict)
    cleanup: dict[str, object] = field(default_factory=dict)
    streams: _RawStreams | None = None
    workload_released: bool = False
    workload_exit_code: int | None = None
    timeout_triggered: bool = False
    limit_triggered: bool = False
    structured_result_bytes: int = 0
    policy_denial: bool = False

    def observe(
        self,
        observation_class: str,
        event_id: str,
        payload: dict[str, object],
    ) -> None:
        self.observations.append(
            (observation_class, event_id, payload, time.monotonic_ns())
        )


def _select_limit_terminal(record: _RunRecord, monotonic_ns: int) -> None:
    """Select LIMIT as the sole terminal trigger and clear losing timestamps."""

    if type(monotonic_ns) is not int or monotonic_ns < 0:
        raise ObservationLoss("limit terminal lacked a valid monotonic boundary")
    record.limit_triggered = True
    record.timeout_triggered = False
    record.workload_exit_code = None
    record.process.pop("workload_exit_monotonic_ns", None)
    record.process.pop("timeout_trigger_monotonic_ns", None)
    record.process["_limit_trigger_monotonic_ns"] = monotonic_ns


def _select_timeout_terminal(record: _RunRecord, monotonic_ns: int) -> None:
    """Select TIMEOUT unless a resource LIMIT has already won."""

    if record.limit_triggered:
        return
    record.timeout_triggered = True
    record.workload_exit_code = None
    record.process.pop("workload_exit_monotonic_ns", None)
    record.process["timeout_trigger_monotonic_ns"] = monotonic_ns


def _record_workload_exit(
    record: _RunRecord,
    value: Mapping[str, object],
    *,
    deadline_ns: int,
    provider_observed_ns: int,
) -> None:
    """Record an exit only when it is unambiguous with the chosen terminal."""

    raw_exit = value.get("exit_code")
    exit_ns = value.get("exit_observed_monotonic_ns")
    if type(raw_exit) is not int or type(exit_ns) is not int or exit_ns < 0:
        raise ObservationLoss("workload exit observation is malformed")
    if exit_ns > provider_observed_ns:
        raise ObservationLoss("workload exit timestamp is after provider receipt")
    if record.exit_observation:
        raise ObservationLoss("duplicate workload exit observation")

    if record.timeout_triggered:
        timeout_ns = record.process.get("timeout_trigger_monotonic_ns")
        if type(timeout_ns) is not int or exit_ns <= timeout_ns:
            raise ObservationLoss(
                "workload exit conflicts with the selected timeout boundary"
            )
        record.exit_observation = dict(value)
        record.workload_exit_code = None
        _merge_process_event_classes(record, value.get("event_classes"))
        return

    if record.limit_triggered:
        limit_ns = record.process.get("_limit_trigger_monotonic_ns")
        if type(limit_ns) is not int or exit_ns <= limit_ns:
            raise ObservationLoss(
                "workload exit conflicts with the selected limit boundary"
            )
        record.exit_observation = dict(value)
        record.workload_exit_code = None
        _merge_process_event_classes(record, value.get("event_classes"))
        return

    if provider_observed_ns >= deadline_ns:
        raise ObservationLoss("workload exit competed with the monotonic deadline")
    record.exit_observation = dict(value)
    _merge_process_event_classes(record, value.get("event_classes"))
    if exit_ns < deadline_ns:
        record.workload_exit_code = raw_exit
        record.process["workload_exit_monotonic_ns"] = exit_ns
    else:
        _select_timeout_terminal(record, max(exit_ns, deadline_ns))


def _require_predeadline_limit_observation(
    record: _RunRecord,
    value: Mapping[str, object],
    *,
    deadline_ns: int,
    provider_observed_ns: int,
) -> int:
    """Reject an ambiguous or losing resource-limit terminal observation."""

    monotonic_ns = value.get("monotonic_ns")
    if type(monotonic_ns) is not int or monotonic_ns < 0:
        raise ObservationLoss("filesystem limit lacked a monotonic timestamp")
    if monotonic_ns >= deadline_ns or provider_observed_ns >= deadline_ns:
        raise ObservationLoss(
            "filesystem limit competed with the monotonic deadline"
        )
    if (
        record.timeout_triggered
        or record.exit_observation
        or "workload_exit_monotonic_ns" in record.process
        or "timeout_trigger_monotonic_ns" in record.process
    ):
        raise ObservationLoss(
            "filesystem limit arrived after another terminal observation"
        )
    return monotonic_ns


def _select_stream_limit_at(
    record: _RunRecord, *, observed_ns: int, deadline_ns: int
) -> None:
    if observed_ns >= deadline_ns:
        raise ObservationLoss("stream limit first observed at/after the deadline")
    if (
        record.timeout_triggered
        or record.exit_observation
        or "workload_exit_monotonic_ns" in record.process
        or "timeout_trigger_monotonic_ns" in record.process
    ):
        raise ObservationLoss("stream limit arrived after another terminal observation")
    _select_limit_terminal(record, observed_ns)


STAGE_DEPENDENCIES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("request.validate", ()),
    ("host.gate", ("request.validate",)),
    ("identity.seal", ("host.gate",)),
    ("ownership.claim", ("identity.seal",)),
    ("namespace.setup", ("ownership.claim",)),
    ("filesystem.setup", ("namespace.setup",)),
    ("network.setup", ("namespace.setup",)),
    ("stream.control", ("ownership.claim",)),
    ("timeout.control", ("ownership.claim", "stream.control")),
    (
        "workload.release",
        ("filesystem.setup", "network.setup", "stream.control", "timeout.control"),
    ),
    ("exec.observe", ("workload.release",)),
    ("process.contain", ("exec.observe",)),
    ("cleanup", ("ownership.claim",)),
)


def _fail_stage_and_cascade(
    record: _RunRecord, failed_stage: str, failure_code: str
) -> None:
    if failed_stage not in dict(STAGE_DEPENDENCIES):
        raise ValueError(f"unknown stage: {failed_stage}")
    record.stage_status[failed_stage] = (STAGE_FAIL, failure_code)

    dependency_map = dict(STAGE_DEPENDENCIES)
    changed = True
    blocked: set[str] = {failed_stage}
    while changed:
        changed = False
        for stage, dependencies in STAGE_DEPENDENCIES:
            if stage in blocked:
                continue
            if any(item in blocked for item in dependencies):
                blocked.add(stage)
                changed = True
    for stage in blocked:
        if stage != failed_stage and stage not in record.stage_status:
            record.stage_status[stage] = (STAGE_NOT_REACHED, failed_stage)


def _mark_pass(record: _RunRecord, stage: str) -> None:
    if stage in record.stage_status:
        raise ObservationLoss(f"stage was recorded twice: {stage}")
    dependencies = dict(STAGE_DEPENDENCIES)[stage]
    if any(record.stage_status.get(item, (None,))[0] != STAGE_PASS for item in dependencies):
        raise ObservationLoss(f"stage passed over a non-PASS prerequisite: {stage}")
    record.stage_status[stage] = (STAGE_PASS, None)


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        try:
            written = os.write(descriptor, view)
        except InterruptedError:
            continue
        if written <= 0:
            raise CleanupIncomplete("ownership marker write made no progress")
        view = view[written:]


def _write_ownership_marker(
    marker: Path,
    *,
    execution_id: str,
    nonce: str,
    cgroups: Mapping[str, tuple[int, int]],
    state: str,
) -> None:
    payload = json.dumps(
        {
            "version": 1,
            "execution_id": execution_id,
            "nonce": nonce,
            "state": state,
            "temporary_root": str(marker.parent),
            "cgroups": {
                path: {"device": value[0], "inode": value[1]}
                for path, value in sorted(cgroups.items())
            },
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if marker.exists():
        replacement = marker.with_name(marker.name + ".next")
        descriptor = -1
        try:
            descriptor = os.open(
                replacement,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | os.O_NOFOLLOW,
                0o600,
            )
            _write_all(descriptor, payload)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(replacement, marker)
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                os.unlink(replacement)
            except FileNotFoundError:
                pass
            raise
    else:
        descriptor = -1
        try:
            descriptor = os.open(
                marker,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | os.O_NOFOLLOW,
                0o600,
            )
            _write_all(descriptor, payload)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                os.unlink(marker)
            except FileNotFoundError:
                pass
            raise
    directory_fd = os.open(marker.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _validate_owned_directory(
    path: Path, expected_identity: tuple[int, int]
) -> None:
    value = os.stat(path, follow_symlinks=False)
    if (
        not stat.S_ISDIR(value.st_mode)
        or (value.st_dev, value.st_ino) != expected_identity
    ):
        raise CleanupIncomplete(f"owned directory identity changed: {path}")


def _validate_ownership_marker(
    marker: Path,
    *,
    execution_id: str,
    nonce: str,
    expected_cgroups: Mapping[str, tuple[int, int]],
    expected_state: str = "owned",
) -> None:
    descriptor = os.open(
        marker,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        payload = os.read(descriptor, 65_537)
        if len(payload) > 65_536 or os.read(descriptor, 1):
            raise CleanupIncomplete("ownership marker exceeded its strict bound")
    finally:
        os.close(descriptor)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CleanupIncomplete("ownership marker is invalid") from exc
    expected_rows = {
        path: {"device": identity[0], "inode": identity[1]}
        for path, identity in sorted(expected_cgroups.items())
    }
    if not isinstance(value, dict) or any(
        (
            value.get("version") != 1,
            value.get("execution_id") != execution_id,
            value.get("nonce") != nonce,
            value.get("state") != expected_state,
            value.get("temporary_root") != str(marker.parent),
            value.get("cgroups") != expected_rows,
        )
    ):
        raise CleanupIncomplete("ownership marker correlation mismatched")


def _remove_owned_tree_at(
    parent_fd: int,
    name: str,
    expected_identity: tuple[int, int],
) -> None:
    """Python-3.10-compatible bounded iterative fd-relative removal."""

    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=parent_fd,
    )
    try:
        value = os.fstat(descriptor)
        if (value.st_dev, value.st_ino) != expected_identity:
            raise CleanupIncomplete("owned cleanup target identity changed")
        root_device = value.st_dev
        pending: list[tuple[tuple[str, ...], int]] = [((), os.dup(descriptor))]
        directories: list[tuple[str, ...]] = []
        observed_nodes = 0
        deadline_ns = time.monotonic_ns() + 5_000_000_000
        try:
            while pending:
                relative, directory_fd = pending.pop()
                try:
                    with os.scandir(directory_fd) as entries:
                        for entry in entries:
                            observed_nodes += 1
                            child_relative = (*relative, entry.name)
                            if (
                                observed_nodes > 16_384
                                or len(child_relative)
                                > MAX_PRIVATE_FILESYSTEM_INODES_V1
                                or time.monotonic_ns() >= deadline_ns
                            ):
                                raise CleanupIncomplete(
                                    "owned cleanup traversal exceeded its bound"
                                )
                            child = entry.stat(follow_symlinks=False)
                            if child.st_dev != root_device:
                                raise CleanupIncomplete(
                                    "owned cleanup refused a device crossing"
                                )
                            if stat.S_ISDIR(child.st_mode):
                                child_fd = os.open(
                                    entry.name,
                                    os.O_RDONLY
                                    | os.O_DIRECTORY
                                    | os.O_NOFOLLOW
                                    | os.O_CLOEXEC,
                                    dir_fd=directory_fd,
                                )
                                pending.append((child_relative, child_fd))
                                directories.append(child_relative)
                            else:
                                os.unlink(entry.name, dir_fd=directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            for _, directory_fd in pending:
                try:
                    os.close(directory_fd)
                except OSError:
                    pass
        for relative in sorted(directories, key=len, reverse=True):
            parent_relative = relative[:-1]
            parent_descriptor = os.dup(descriptor)
            try:
                for component in parent_relative:
                    child_descriptor = os.open(
                        component,
                        os.O_RDONLY
                        | os.O_DIRECTORY
                        | os.O_NOFOLLOW
                        | os.O_CLOEXEC,
                        dir_fd=parent_descriptor,
                    )
                    os.close(parent_descriptor)
                    parent_descriptor = child_descriptor
                    observed = os.fstat(parent_descriptor)
                    if observed.st_dev != root_device:
                        raise CleanupIncomplete(
                            "owned cleanup refused a device crossing"
                        )
                os.rmdir(relative[-1], dir_fd=parent_descriptor)
            finally:
                os.close(parent_descriptor)
    finally:
        os.close(descriptor)
    # The parent fd is pinned and unshared with the workload; re-open identity
    # validation above prevents replacing the named target with a foreign tree.
    os.rmdir(name, dir_fd=parent_fd)


def _read_until_ready(
    report_fd: int,
    anchor_pidfd: int,
    deadline_ns: int,
    byte_limit: int,
) -> tuple[dict[str, object], bytearray, int]:
    buffer = bytearray()
    emitted_bytes = 0
    selector = selectors.DefaultSelector()
    try:
        selector.register(report_fd, selectors.EVENT_READ, "report")
        selector.register(anchor_pidfd, selectors.EVENT_READ, "anchor")
        while time.monotonic_ns() < deadline_ns:
            for key, _ in selector.select(timeout=POLL_SECONDS):
                if key.data == "anchor":
                    raise CapabilityBlocker(
                        "namespace anchor exited before the capability gate"
                    )
                chunk = os.read(report_fd, 65_536)
                if not chunk:
                    raise CapabilityBlocker(
                        "namespace report closed before the capability gate"
                    )
                if len(chunk) > byte_limit - emitted_bytes:
                    raise ObservationLoss(
                        "structured-result pipe exceeded its exact byte limit"
                    )
                emitted_bytes += len(chunk)
                buffer.extend(chunk)
                for value in _decode_json_lines(buffer):
                    if value["kind"] == "failure":
                        raise CapabilityBlocker(
                            f"namespace setup failed: {value.get('failure')}"
                        )
                    if value["kind"] == "ready":
                        return value, buffer, emitted_bytes
                    raise ObservationLoss(
                        f"unexpected pre-release report: {value['kind']}"
                    )
        raise CapabilityBlocker("namespace capability gate timed out")
    finally:
        selector.close()


def _bind_all_members(
    path: Path, expected_cgroup: str
) -> tuple[_BoundPid, ...]:
    members = _cgroup_members(path)
    if not members:
        raise ObservationLoss("composition cgroup became empty before containment")
    bound: list[_BoundPid] = []
    try:
        for pid in members:
            bound.append(_BoundPid.bind(pid, expected_cgroup))
        if _cgroup_members(path) != members:
            raise ObservationLoss("composition membership changed during pidfd binding")
        for item in bound:
            item.revalidate()
            if item.readable():
                raise ObservationLoss("composition member exited before cgroup.kill")
        return tuple(bound)
    except BaseException:
        for item in bound:
            item.close()
        raise


def _bound_member_record(
    item: _BoundPid,
    *,
    observed_before_grace: bool,
    observed_before_kill: bool,
    pidfd_unreadable_before_kill: bool,
    pidfd_exit_observed: bool,
) -> dict[str, object]:
    return {
        "pid": item.pid,
        "starttime_ticks": item.starttime,
        "cgroup_path": item.cgroup,
        "pidfd_opened": item.pidfd >= 0,
        "identity_revalidated": True,
        "observed_before_grace": observed_before_grace,
        "observed_before_kill": observed_before_kill,
        "pidfd_unreadable_before_kill": pidfd_unreadable_before_kill,
        "pidfd_exit_observed": pidfd_exit_observed,
    }


def _retain_namespace_member(
    *,
    namespace_pid: int,
    starttime_ticks: int,
    reported_cgroup: str,
    composition: Path,
    expected_cgroup: str,
    expected_pid_namespace: str,
    event_members: dict[tuple[int, int], tuple[_BoundPid, dict[str, object]]],
    member_limit: int,
) -> tuple[_BoundPid, dict[str, object]]:
    if reported_cgroup != expected_cgroup:
        raise ObservationLoss("event-time member cgroup report mismatched")
    key = (namespace_pid, starttime_ticks)
    existing = event_members.get(key)
    if existing is not None:
        existing[0].revalidate()
        if existing[0].readable():
            raise ObservationLoss("event-time member exited before acknowledgement")
        return existing
    if len(event_members) >= member_limit:
        raise ObservationLoss(
            "historical process-member count exceeded request max_processes"
        )
    host_pid = _host_pid_for_namespace_member(
        namespace_pid,
        starttime_ticks,
        composition,
        expected_cgroup,
        expected_pid_namespace,
    )
    bound = _BoundPid.bind(host_pid, expected_cgroup)
    if bound.starttime != starttime_ticks or bound.readable():
        bound.close()
        raise ObservationLoss("event-time member identity changed during retention")
    member = _bound_member_record(
        bound,
        observed_before_grace=True,
        observed_before_kill=False,
        pidfd_unreadable_before_kill=False,
        pidfd_exit_observed=False,
    )
    event_members[key] = (bound, member)
    return bound, member


def _ack_member_report(
    value: Mapping[str, object],
    *,
    is_exit_stop: bool,
    composition: Path,
    expected_cgroup: str,
    expected_pid_namespace: str,
    event_members: dict[tuple[int, int], tuple[_BoundPid, dict[str, object]]],
    ack_fd: int,
    member_limit: int,
) -> None:
    namespace_pid = value.get("pid")
    starttime_ticks = value.get("starttime_ticks")
    reported_cgroup = value.get("cgroup_path")
    if (
        not isinstance(namespace_pid, int)
        or not isinstance(starttime_ticks, int)
        or not isinstance(reported_cgroup, str)
    ):
        raise ObservationLoss("event-time member report was malformed")
    key = (namespace_pid, starttime_ticks)
    if is_exit_stop and key not in event_members:
        raise ObservationLoss("member exit-stop lacked an acknowledged birth/exec bind")
    _, member = _retain_namespace_member(
        namespace_pid=namespace_pid,
        starttime_ticks=starttime_ticks,
        reported_cgroup=reported_cgroup,
        composition=composition,
        expected_cgroup=expected_cgroup,
        expected_pid_namespace=expected_pid_namespace,
        event_members=event_members,
        member_limit=member_limit,
    )
    if is_exit_stop:
        member["exit_stop_observed"] = True
    _write_all(ack_fd, b"a")


def _ack_secondary_exec_denial(
    value: Mapping[str, object],
    *,
    composition: Path,
    expected_cgroup: str,
    expected_pid_namespace: str,
    event_members: dict[tuple[int, int], tuple[_BoundPid, dict[str, object]]],
    ack_fd: int,
    member_limit: int,
    denials: list[dict[str, object]],
) -> None:
    namespace_pid = value.get("pid")
    starttime_ticks = value.get("starttime_ticks")
    reported_cgroup = value.get("cgroup_path")
    syscall_number = value.get("syscall_number")
    denial_errno = value.get("errno")
    monotonic_ns = value.get("monotonic_ns")
    if (
        not isinstance(namespace_pid, int)
        or not isinstance(starttime_ticks, int)
        or not isinstance(reported_cgroup, str)
        or syscall_number not in {59, 322}
        or denial_errno != errno.EPERM
        or not isinstance(monotonic_ns, int)
        or monotonic_ns <= 0
    ):
        raise ObservationLoss("secondary exec denial report was malformed")
    bound, _ = _retain_namespace_member(
        namespace_pid=namespace_pid,
        starttime_ticks=starttime_ticks,
        reported_cgroup=reported_cgroup,
        composition=composition,
        expected_cgroup=expected_cgroup,
        expected_pid_namespace=expected_pid_namespace,
        event_members=event_members,
        member_limit=member_limit,
    )
    if len(denials) >= MAX_SECONDARY_EXEC_DENIALS:
        raise ObservationLoss("secondary exec denial count exceeded its bound")
    if denials and monotonic_ns < int(denials[-1]["monotonic_ns"]):
        raise ObservationLoss("secondary exec denial order was non-monotonic")
    denials.append(
        {
            "pid": bound.pid,
            "starttime_ticks": bound.starttime,
            "cgroup_path": bound.cgroup,
            "syscall_number": syscall_number,
            "errno": denial_errno,
            "monotonic_ns": monotonic_ns,
        }
    )
    _write_all(ack_fd, b"a")


def _merged_member_records(process: Mapping[str, object]) -> list[dict[str, object]]:
    merged: dict[tuple[int, int], dict[str, object]] = {}
    for group_name in (
        "event_members",
        "members_before_grace",
        "members_before_kill",
    ):
        raw_group = process.get(group_name, ())
        if not isinstance(raw_group, list):
            continue
        for raw in raw_group:
            if not isinstance(raw, dict):
                continue
            key = (int(raw["pid"]), int(raw["starttime_ticks"]))
            projected = {
                name: raw[name]
                for name in (
                    "pid",
                    "starttime_ticks",
                    "cgroup_path",
                    "pidfd_opened",
                    "identity_revalidated",
                    "observed_before_grace",
                    "observed_before_kill",
                    "pidfd_unreadable_before_kill",
                    "pidfd_exit_observed",
                )
            }
            current = merged.setdefault(key, projected)
            for name in (
                "pidfd_opened",
                "identity_revalidated",
                "observed_before_grace",
                "observed_before_kill",
                "pidfd_unreadable_before_kill",
                "pidfd_exit_observed",
            ):
                current[name] = current.get(name) is True or raw.get(name) is True
    return [merged[key] for key in sorted(merged)]


@dataclass(frozen=True)
class _OwnedRunRoot:
    trusted_tmp_fd: int
    provider_parent: Path
    provider_parent_fd: int
    provider_parent_identity: tuple[int, int]
    temp_root: Path
    temp_root_fd: int
    temp_root_identity: tuple[int, int]
    marker: Path
    nonce: str


def _claim_run_root(execution_id: str, record: _RunRecord) -> _OwnedRunRoot:
    """Acquire the creator-owned temporary tree with total failure cleanup."""

    trusted_tmp_fd = provider_parent_fd = temp_root_fd = -1
    provider_parent: Path | None = None
    provider_parent_identity: tuple[int, int] | None = None
    temp_root: Path | None = None
    temp_root_identity: tuple[int, int] | None = None
    try:
        trusted_tmp_fd = _safe_absolute_open("/tmp", directory=True)
        trusted = os.fstat(trusted_tmp_fd)
        if trusted.st_uid != 0 or not (trusted.st_mode & stat.S_ISVTX):
            raise CapabilityBlocker(
                "trusted /tmp root lacks root ownership or sticky bit"
            )
        provider_parent = Path(
            tempfile.mkdtemp(
                prefix="tool-system-isolated-execution-", dir="/tmp"
            )
        )
        record.process["resource_claim_started"] = True
        parent_stat = os.stat(provider_parent, follow_symlinks=False)
        if not stat.S_ISDIR(parent_stat.st_mode):
            raise CleanupIncomplete("temporary provider parent is not a directory")
        provider_parent_identity = (parent_stat.st_dev, parent_stat.st_ino)
        os.chmod(provider_parent, 0o700)
        provider_parent_fd = os.open(
            provider_parent,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        opened_parent = os.fstat(provider_parent_fd)
        if (opened_parent.st_dev, opened_parent.st_ino) != provider_parent_identity:
            raise CleanupIncomplete("temporary provider parent changed while opening")
        os.mkdir(execution_id, mode=0o700, dir_fd=provider_parent_fd)
        temp_stat = os.stat(
            execution_id, dir_fd=provider_parent_fd, follow_symlinks=False
        )
        temp_root_identity = (temp_stat.st_dev, temp_stat.st_ino)
        temp_root = provider_parent / execution_id
        temp_root_fd = os.open(
            execution_id,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=provider_parent_fd,
        )
        opened_root = os.fstat(temp_root_fd)
        if (opened_root.st_dev, opened_root.st_ino) != temp_root_identity:
            raise CleanupIncomplete("temporary execution root changed while opening")
        marker = temp_root / ".ts-b02a-ownership-v1.json"
        nonce = os.urandom(32).hex()
        _write_ownership_marker(
            marker,
            execution_id=execution_id,
            nonce=nonce,
            cgroups={},
            state="claiming",
        )
        (temp_root / "host-sentinel").write_text(
            "provider-only", encoding="utf-8"
        )
        return _OwnedRunRoot(
            trusted_tmp_fd=trusted_tmp_fd,
            provider_parent=provider_parent,
            provider_parent_fd=provider_parent_fd,
            provider_parent_identity=provider_parent_identity,
            temp_root=temp_root,
            temp_root_fd=temp_root_fd,
            temp_root_identity=temp_root_identity,
            marker=marker,
            nonce=nonce,
        )
    except BaseException as original:
        cleanup_errors: list[str] = []
        if temp_root_fd >= 0:
            try:
                os.close(temp_root_fd)
            except OSError as exc:
                cleanup_errors.append(_bounded_failure(exc))
        if (
            provider_parent_fd >= 0
            and temp_root_identity is not None
            and temp_root is not None
        ):
            try:
                _remove_owned_tree_at(
                    provider_parent_fd, execution_id, temp_root_identity
                )
            except BaseException as exc:
                cleanup_errors.append(_bounded_failure(exc))
        if provider_parent_fd >= 0:
            try:
                os.close(provider_parent_fd)
            except OSError as exc:
                cleanup_errors.append(_bounded_failure(exc))
        if (
            trusted_tmp_fd >= 0
            and provider_parent is not None
            and provider_parent_identity is not None
        ):
            try:
                current = os.stat(
                    provider_parent.name,
                    dir_fd=trusted_tmp_fd,
                    follow_symlinks=False,
                )
                if (current.st_dev, current.st_ino) == provider_parent_identity:
                    os.rmdir(provider_parent.name, dir_fd=trusted_tmp_fd)
            except BaseException as exc:
                cleanup_errors.append(_bounded_failure(exc))
        if trusted_tmp_fd >= 0:
            try:
                os.close(trusted_tmp_fd)
            except OSError as exc:
                cleanup_errors.append(_bounded_failure(exc))
        removed = provider_parent is None
        if provider_parent is not None:
            try:
                removed = not provider_parent.exists()
            except BaseException as exc:
                removed = False
                cleanup_errors.append(_bounded_failure(exc))
        record.cleanup = {
            "cgroup_release": {
                "exact_paths": [],
                "released_paths": [],
                "populated_zero": True,
                "failures": [],
            },
            "mounts": [],
            "process_residue": [],
            "temporary_root_removed": removed,
            "pidfd_exit_observed": True,
            "failures": cleanup_errors,
        }
        if cleanup_errors or not removed:
            raise CleanupIncomplete(
                "partial temporary-root acquisition cleanup failed: "
                + "; ".join(cleanup_errors or ["owned root residue"])
            ) from original
        raise


def _run_prepared(
    prepared: _PreparedRequest,
    record: _RunRecord,
    seccomp_controls: Mapping[str, object],
) -> None:
    request = prepared.request
    seccomp_controls = dict(seccomp_controls)
    root_claim = _claim_run_root(request.execution_id, record)
    trusted_tmp_fd = root_claim.trusted_tmp_fd
    provider_parent = root_claim.provider_parent
    provider_parent_fd = root_claim.provider_parent_fd
    provider_parent_identity = root_claim.provider_parent_identity
    temp_root = root_claim.temp_root
    temp_root_fd = root_claim.temp_root_fd
    temp_root_identity = root_claim.temp_root_identity
    marker = root_claim.marker
    nonce = root_claim.nonce

    tree = _OwnedCgroupTree(request.execution_id, nonce)
    composition = tree.children["composition"]
    placement_read = placement_write = -1
    report_read = report_write = -1
    release_read = release_write = -1
    stdout_read = stdout_write = -1
    stderr_read = stderr_write = -1
    event_ack_read = event_ack_write = -1
    snapshot_parent = snapshot_child = -1
    scratch_snapshot_fd = output_snapshot_fd = -1
    anchor = -1
    anchor_pidfd = -1
    bound_members: tuple[_BoundPid, ...] = ()
    event_members: dict[
        tuple[int, int], tuple[_BoundPid, dict[str, object]]
    ] = {}
    secondary_exec_denials: list[dict[str, object]] = []
    namespace_ids: dict[str, str] = {}
    expected_cgroup = f"/{request.execution_id}/composition"
    cleanup_failures: list[str] = []
    pidfd_exit_observed = True
    populated_before_kill: int | None = None
    try:
        tree.claim(request.process.max_processes)
        _write_ownership_marker(
            marker,
            execution_id=request.execution_id,
            nonce=nonce,
            cgroups=tree.identities,
            state="owned",
        )
        _mark_pass(record, "ownership.claim")
        record.observe(
            "capability",
            "cgroup.claim",
            {
                "exact_paths": [str(path) for path in tree.exact_paths],
                "identity_count": len(tree.identities),
                "observed_pids_max": tree.observed_pids_max,
                "nonce_sha256": hashlib.sha256(nonce.encode("ascii")).hexdigest(),
            },
        )

        filtered_process_controls = _auxiliary_cgroup_control(
            tree.children["combined-stream"], mode="seccomp_process"
        )
        for key in ("ordinary_fork_positive", "ordinary_vfork_positive"):
            if filtered_process_controls.get(key) is not True:
                raise CapabilityBlocker(
                    f"exact-filter {key} control did not pass"
                )
            seccomp_controls[key] = True

        placement_read, placement_write = os.pipe2(os.O_CLOEXEC)
        report_read, report_write = os.pipe2(os.O_CLOEXEC)
        release_read, release_write = os.pipe2(os.O_CLOEXEC)
        stdout_read, stdout_write = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        stderr_read, stderr_write = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        event_ack_read, event_ack_write = os.pipe2(os.O_CLOEXEC)
        stream_pipe_capacity = STREAM_PIPE_CAPACITY_BYTES_V1
        for descriptor in (stdout_write, stderr_write):
            observed_capacity = fcntl.fcntl(
                descriptor, fcntl.F_SETPIPE_SZ, stream_pipe_capacity
            )
            readback_capacity = fcntl.fcntl(descriptor, fcntl.F_GETPIPE_SZ)
            if (
                observed_capacity != stream_pipe_capacity
                or readback_capacity != stream_pipe_capacity
            ):
                raise CapabilityBlocker(
                    "stream pipe capacity could not be frozen at 4096 bytes"
                )
        snapshot_parent_socket, snapshot_child_socket = socket.socketpair(
            socket.AF_UNIX,
            socket.SOCK_DGRAM | socket.SOCK_CLOEXEC,
        )
        snapshot_parent = snapshot_parent_socket.detach()
        snapshot_child = snapshot_child_socket.detach()
        parent_namespaces = _namespace_links()
        anchor = os.fork()
        if anchor == 0:
            for descriptor in (
                placement_write,
                report_read,
                release_write,
                stdout_read,
                stderr_read,
                snapshot_parent,
                event_ack_write,
            ):
                os.close(descriptor)
            _namespace_anchor(
                prepared,
                temp_root,
                report_write,
                placement_read,
                release_read,
                stdout_write,
                stderr_write,
                snapshot_child,
                event_ack_read,
                parent_namespaces,
                seccomp_controls,
            )
            os._exit(127)
        pidfd_exit_observed = False
        anchor_pidfd = os.pidfd_open(anchor)
        for descriptor_name in (
            "placement_read",
            "report_write",
            "release_read",
            "stdout_write",
            "stderr_write",
            "snapshot_child",
            "event_ack_read",
        ):
            descriptor = locals()[descriptor_name]
            os.close(descriptor)
            if descriptor_name == "placement_read":
                placement_read = -1
            elif descriptor_name == "report_write":
                report_write = -1
            elif descriptor_name == "release_read":
                release_read = -1
            elif descriptor_name == "stdout_write":
                stdout_write = -1
            elif descriptor_name == "stderr_write":
                stderr_write = -1
            else:
                if descriptor_name == "snapshot_child":
                    snapshot_child = -1
                else:
                    event_ack_read = -1

        (tree.children["composition"] / "cgroup.procs").write_text(
            str(anchor), encoding="ascii"
        )
        actual_cgroup = _proc_cgroup(anchor)
        if actual_cgroup != expected_cgroup:
            raise ObservationLoss(
                f"composition placement mismatch: {actual_cgroup!r}"
            )
        initial = _BoundPid.bind(anchor, expected_cgroup)
        os.close(anchor_pidfd)
        anchor_pidfd = initial.pidfd
        initial.pidfd = -1
        record.process.update(
            {
                "initial_pid": anchor,
                "initial_starttime": initial.starttime,
                "initial_pidfd_opened": True,
                "observed_pids_max": tree.observed_pids_max,
            }
        )
        os.write(placement_write, b"p")
        os.close(placement_write)
        placement_write = -1

        setup, pending_report, report_bytes = _read_until_ready(
            report_read,
            anchor_pidfd,
            min(request.process.deadline_monotonic_ns, time.monotonic_ns() + 30_000_000_000),
            request.output.structured_result_byte_limit,
        )
        record.structured_result_bytes = report_bytes
        scratch_snapshot_fd, output_snapshot_fd = _receive_snapshot_fds(
            snapshot_parent,
            max(
                0.001,
                min(
                    2.0,
                    (request.process.deadline_monotonic_ns - time.monotonic_ns())
                    / 1_000_000_000,
                ),
            ),
        )
        os.close(snapshot_parent)
        snapshot_parent = -1
        namespace_raw = setup.get("namespace_ids")
        if not isinstance(namespace_raw, dict) or set(namespace_raw) != {
            "mnt",
            "pid",
            "net",
            "ipc",
            "uts",
        }:
            raise ObservationLoss("namespace identity set is incomplete")
        namespace_ids = {str(key): str(value) for key, value in namespace_raw.items()}
        if _host_mounts_under(temp_root):
            raise CapabilityBlocker("private mount propagated into host mountinfo")
        _mark_pass(record, "namespace.setup")
        _mark_pass(record, "filesystem.setup")
        _mark_pass(record, "network.setup")
        record.setup = setup
        record.observe(
            "capability",
            "namespace.setup",
            {
                "namespace_ids": namespace_ids,
                "parent_namespace_ids": parent_namespaces,
                "all_distinct_from_parent": all(
                    namespace_ids[name] != parent_namespaces[name]
                    for name in namespace_ids
                ),
                "host_mounts_during_live_namespace": [],
                "private_mount_propagation": setup.get(
                    "private_mount_propagation"
                ),
            },
        )
        record.observe(
            "filesystem",
            "filesystem.gate",
            {
                "rejected_boundary_attempts": setup.get(
                    "rejected_boundary_attempts"
                ),
                "quota_controls": setup.get("quota_controls"),
                "private_quota_observations": setup.get(
                    "private_quota_observations"
                ),
                "read_only_mount_observations": setup.get(
                    "read_only_mount_observations"
                ),
                "read_only_input_scans": setup.get(
                    "read_only_input_scans"
                ),
                "declared_output_control": setup.get(
                    "declared_output_control"
                ),
                "provider_view_controls": setup.get(
                    "provider_view_controls"
                ),
                "private_root_mount_observation": setup.get(
                    "private_root_mount_observation"
                ),
            },
        )
        record.observe(
            "network",
            "network.gate",
            {
                "network": setup.get("network"),
                "socket_denial_errno": setup.get("socket_denial_errno"),
                "seccomp_controls": setup.get("seccomp_controls"),
                "seccomp_filter_sha256": setup.get(
                    "seccomp_filter_sha256"
                ),
            },
        )

        stream_control = _auxiliary_cgroup_control(
            tree.children["combined-stream"], mode="stream"
        )
        _mark_pass(record, "stream.control")
        record.observe("streams", "stream.control", stream_control)
        timeout_control = _auxiliary_cgroup_control(
            tree.children["timeout"], mode="timeout"
        )
        _mark_pass(record, "timeout.control")
        record.observe("time", "timeout.control", timeout_control)

        release_recheck_ns = time.monotonic_ns()
        if (
            release_recheck_ns + request.process.termination_grace_ns
            >= request.process.deadline_monotonic_ns
            or request.process.deadline_monotonic_ns - release_recheck_ns
            > 300_000_000_000
        ):
            raise CapabilityBlocker(
                "insufficient monotonic budget for the mandatory termination grace"
            )
        os.write(release_write, b"g")
        record.observe(
            "time",
            "deadline.release_recheck",
            {
                "release_recheck_monotonic_ns": release_recheck_ns,
                "deadline_monotonic_ns": request.process.deadline_monotonic_ns,
                "termination_grace_ns": request.process.termination_grace_ns,
                "eligible": True,
            },
        )
        os.close(release_write)
        release_write = -1
        record.workload_released = True
        _mark_pass(record, "workload.release")
        record.observe(
            "capability", "workload.release", {"released": True}
        )

        streams = _RawStreams(
            stdout_limit=request.streams.stdout_raw_byte_limit,
            stderr_limit=request.streams.stderr_raw_byte_limit,
            combined_limit=request.streams.combined_raw_byte_limit,
            retained_limit=request.streams.retained_byte_limit,
        )
        record.streams = streams
        report_buffer = pending_report
        selector = selectors.DefaultSelector()
        for descriptor, name in (
            (report_read, "report"),
            (stdout_read, "stdout"),
            (stderr_read, "stderr"),
        ):
            os.set_blocking(descriptor, False)
            selector.register(descriptor, selectors.EVENT_READ, name)
        terminate = False
        try:
            while selector.get_map() and not terminate:
                events = selector.select(timeout=POLL_SECONDS)
                for key, _ in events:
                    provider_observed_ns = time.monotonic_ns()
                    name = str(key.data)
                    try:
                        payload = os.read(
                            key.fd,
                            streams.next_read_size(name)
                            if name in {"stdout", "stderr"}
                            else 65_536,
                        )
                    except BlockingIOError:
                        continue
                    if not payload:
                        selector.unregister(key.fd)
                        continue
                    if name in {"stdout", "stderr"}:
                        streams.consume(name, payload)
                        if streams.trigger is not None:
                            _select_stream_limit_at(
                                record,
                                observed_ns=time.monotonic_ns(),
                                deadline_ns=request.process.deadline_monotonic_ns,
                            )
                            terminate = True
                            # Do not consume a second ready stream in this
                            # selector batch.  Freeze first; otherwise each
                            # pipe can refill after two crossing bytes and the
                            # frozen combined overshoot bound is off by one.
                            break
                        continue
                    if len(payload) > (
                        request.output.structured_result_byte_limit
                        - record.structured_result_bytes
                    ):
                        raise ObservationLoss(
                            "structured-result pipe exceeded its exact byte limit"
                        )
                    record.structured_result_bytes += len(payload)
                    report_buffer.extend(payload)
                    decoded_values: list[dict[str, object]] = []
                    _consume_json_line_batch(
                        report_buffer,
                        lambda value: bool(decoded_values.append(value)),
                    )
                    for value in decoded_values:
                        kind = value["kind"]
                        if kind == "ptrace_exec":
                            if record.exec_observation:
                                raise ObservationLoss(
                                    "duplicate root PTRACE_EVENT_EXEC observation"
                                )
                            namespace_pid = value.get("exec_pid")
                            starttime_ticks = value.get("exec_starttime_ticks")
                            if not isinstance(namespace_pid, int) or not isinstance(
                                starttime_ticks, int
                            ):
                                raise ObservationLoss(
                                    "exec member namespace identity is malformed"
                                )
                            bound_exec, _ = _retain_namespace_member(
                                namespace_pid=namespace_pid,
                                starttime_ticks=starttime_ticks,
                                reported_cgroup=str(value.get("exec_cgroup")),
                                composition=composition,
                                expected_cgroup=expected_cgroup,
                                expected_pid_namespace=namespace_ids["pid"],
                                event_members=event_members,
                                member_limit=max(1, request.process.max_processes - 2),
                            )
                            value["namespace_exec_pid"] = namespace_pid
                            value["exec_pid"] = bound_exec.pid
                            _write_all(event_ack_write, b"a")
                            record.exec_observation = value
                            _merge_process_event_classes(record, ["exec"])
                            _mark_pass(record, "exec.observe")
                            record.observe(
                                "exec_chain", "exec.ptrace", dict(value)
                            )
                        elif kind in {"member_birth", "member_exit_stop"}:
                            _ack_member_report(
                                value,
                                is_exit_stop=kind == "member_exit_stop",
                                composition=composition,
                                expected_cgroup=expected_cgroup,
                                expected_pid_namespace=namespace_ids["pid"],
                                event_members=event_members,
                                ack_fd=event_ack_write,
                                member_limit=max(1, request.process.max_processes - 2),
                            )
                        elif kind == "secondary_exec_denial":
                            _ack_secondary_exec_denial(
                                value,
                                composition=composition,
                                expected_cgroup=expected_cgroup,
                                expected_pid_namespace=namespace_ids["pid"],
                                event_members=event_members,
                                ack_fd=event_ack_write,
                                member_limit=max(
                                    1, request.process.max_processes - 2
                                ),
                                denials=secondary_exec_denials,
                            )
                            _merge_process_event_classes(
                                record, ["exec_denied"]
                            )
                        elif kind == "workload_exit":
                            _record_workload_exit(
                                record,
                                value,
                                deadline_ns=request.process.deadline_monotonic_ns,
                                provider_observed_ns=provider_observed_ns,
                            )
                            terminate = True
                            continue
                        elif kind in {"limit", "limit_candidate"}:
                            limit_ns = _require_predeadline_limit_observation(
                                record,
                                value,
                                deadline_ns=request.process.deadline_monotonic_ns,
                                provider_observed_ns=provider_observed_ns,
                            )
                            value["_predeadline_validated"] = True
                            _translate_limit_member(
                                value,
                                composition,
                                expected_cgroup,
                                namespace_ids["pid"],
                            )
                            if kind == "limit":
                                _select_limit_terminal(record, limit_ns)
                                record.process["filesystem_limit_event"] = dict(value)
                            else:
                                record.process["filesystem_limit_candidate"] = dict(value)
                            terminate = True
                            continue
                        elif kind == "process_event":
                            _merge_process_event_classes(
                                record, value.get("event_classes")
                            )
                        elif kind == "failure":
                            raise ObservationLoss(
                                f"namespace execution failure: {value.get('failure')}"
                            )
                        else:
                            raise ObservationLoss(
                                f"unknown namespace report kind: {kind}"
                            )
                    if (
                        provider_observed_ns
                        >= request.process.deadline_monotonic_ns
                        and not terminate
                    ):
                        _select_timeout_terminal(
                            record,
                            provider_observed_ns,
                        )
                        terminate = True
                if (
                    not terminate
                    and time.monotonic_ns()
                    >= request.process.deadline_monotonic_ns
                ):
                    _select_timeout_terminal(
                        record,
                        max(
                            time.monotonic_ns(),
                            request.process.deadline_monotonic_ns,
                        ),
                    )
                    terminate = True
        finally:
            selector.close()

        if not record.exec_observation:
            raise ObservationLoss("workload exec observation was not received")
        if record.stage_status.get("exec.observe", (None,))[0] != STAGE_PASS:
            _mark_pass(record, "exec.observe")

        # Freeze closes the fork/exit race while the complete process set is
        # bound to (pid,starttime,cgroup,pidfd).  SIGTERM is queued while
        # frozen, then the set runs for exactly the requested finite grace.
        _set_cgroup_frozen(composition, True)
        bound_members = _bind_all_members(composition, expected_cgroup)
        members_before_grace = [
            _bound_member_record(
                item,
                observed_before_grace=True,
                observed_before_kill=False,
                pidfd_unreadable_before_kill=False,
                pidfd_exit_observed=False,
            )
            for item in bound_members
        ]
        # With the complete tree frozen, drain every byte that was already
        # accepted by the two kernel pipes before choosing the terminal path.
        # No writer can refill either pipe at this point.  This closes the
        # finite-write/fast-exit race where the report pipe became readable
        # before the last stdout/stderr bytes were accounted.
        for descriptor, name in (
            (stdout_read, "stdout"),
            (stderr_read, "stderr"),
        ):
            while streams.trigger is None:
                try:
                    payload = os.read(descriptor, streams.next_read_size(name))
                except BlockingIOError:
                    break
                if not payload:
                    break
                streams.consume(name, payload)
            if streams.trigger is not None:
                if not record.limit_triggered:
                    _select_stream_limit_at(
                        record,
                        observed_ns=time.monotonic_ns(),
                        deadline_ns=request.process.deadline_monotonic_ns,
                    )
                break
        if _cgroup_populated(composition) != 1:
            raise ObservationLoss("composition was empty before termination grace")
        grace_started_ns = time.monotonic_ns()
        immediate_limit = record.limit_triggered or any(
            name in record.process
            for name in ("filesystem_limit_event", "filesystem_limit_candidate")
        )
        if immediate_limit:
            # Resource-limit termination is deliberately not graceful: the
            # already-frozen tree cannot refill either bounded 4096-byte pipe.
            grace_finished_ns = grace_started_ns
        else:
            for item in bound_members:
                signal.pidfd_send_signal(item.pidfd, signal.SIGTERM, None, 0)
            _set_cgroup_frozen(composition, False)
            grace_target_ns = grace_started_ns + request.process.termination_grace_ns
            grace_limit = False
            grace_selector = selectors.DefaultSelector()
            try:
                for descriptor, name in (
                    (report_read, "report"),
                    (stdout_read, "stdout"),
                    (stderr_read, "stderr"),
                ):
                    grace_selector.register(descriptor, selectors.EVENT_READ, name)
                while time.monotonic_ns() < grace_target_ns and not grace_limit:
                    for key, _ in grace_selector.select(timeout=POLL_SECONDS):
                        try:
                            name = str(key.data)
                            payload = os.read(
                                key.fd,
                                streams.next_read_size(name)
                                if name in {"stdout", "stderr"}
                                else 65_536,
                            )
                        except BlockingIOError:
                            continue
                        if not payload:
                            if key.data == "report":
                                raise ObservationLoss(
                                    "trusted trace report closed during grace"
                                )
                            grace_selector.unregister(key.fd)
                            continue
                        if name in {"stdout", "stderr"}:
                            streams.consume(name, payload)
                            if streams.trigger is not None:
                                raise ObservationLoss(
                                    "stream limit competed with an earlier terminal "
                                    "observation during grace"
                                )
                            continue
                        if len(payload) > (
                            request.output.structured_result_byte_limit
                            - record.structured_result_bytes
                        ):
                            raise ObservationLoss(
                                "structured-result pipe exceeded its exact byte limit"
                            )
                        record.structured_result_bytes += len(payload)
                        report_buffer.extend(payload)
                        decoded_values = []
                        _consume_json_line_batch(
                            report_buffer,
                            lambda value: bool(decoded_values.append(value)),
                        )
                        for value in decoded_values:
                            kind = value["kind"]
                            if kind == "failure":
                                raise ObservationLoss(
                                    f"namespace execution failure: {value.get('failure')}"
                                )
                            if kind == "ptrace_exec":
                                raise IdentityMismatch(
                                    "additional exec observation arrived during grace"
                                )
                            if kind in {"member_birth", "member_exit_stop"}:
                                _ack_member_report(
                                    value,
                                    is_exit_stop=kind == "member_exit_stop",
                                    composition=composition,
                                    expected_cgroup=expected_cgroup,
                                    expected_pid_namespace=namespace_ids["pid"],
                                    event_members=event_members,
                                    ack_fd=event_ack_write,
                                    member_limit=max(1, request.process.max_processes - 2),
                                )
                                continue
                            if kind == "secondary_exec_denial":
                                _ack_secondary_exec_denial(
                                    value,
                                    composition=composition,
                                    expected_cgroup=expected_cgroup,
                                    expected_pid_namespace=namespace_ids["pid"],
                                    event_members=event_members,
                                    ack_fd=event_ack_write,
                                    member_limit=max(
                                        1, request.process.max_processes - 2
                                    ),
                                    denials=secondary_exec_denials,
                                )
                                _merge_process_event_classes(
                                    record, ["exec_denied"]
                                )
                                continue
                            if kind in {"limit", "limit_candidate"}:
                                limit_ns = _require_predeadline_limit_observation(
                                    record,
                                    value,
                                    deadline_ns=request.process.deadline_monotonic_ns,
                                    provider_observed_ns=time.monotonic_ns(),
                                )
                                value["_predeadline_validated"] = True
                                _translate_limit_member(
                                    value,
                                    composition,
                                    expected_cgroup,
                                    namespace_ids["pid"],
                                )
                                if kind == "limit":
                                    _select_limit_terminal(record, limit_ns)
                                    record.process["filesystem_limit_event"] = dict(value)
                                else:
                                    record.process["filesystem_limit_candidate"] = dict(value)
                                grace_limit = True
                                continue
                            if kind == "process_event":
                                _merge_process_event_classes(
                                    record, value.get("event_classes")
                                )
                                continue
                            if kind == "workload_exit":
                                _record_workload_exit(
                                    record,
                                    value,
                                    deadline_ns=(
                                        request.process.deadline_monotonic_ns
                                    ),
                                    provider_observed_ns=time.monotonic_ns(),
                                )
                                continue
                            else:
                                raise ObservationLoss(
                                    f"unknown grace report kind: {kind}"
                                )
            finally:
                grace_selector.close()
            _set_cgroup_frozen(composition, True)
            grace_finished_ns = time.monotonic_ns()
            if grace_limit:
                # A limit discovered during an otherwise graceful interval is
                # reclassified at the exact freeze point, not as a shortened
                # grace.  LIMIT evidence therefore has equal trigger/freeze
                # timestamps and never claims the requested grace elapsed.
                grace_started_ns = grace_finished_ns
        # The complete cgroup is now quiescent.  Drain every atomic trusted
        # ptrace report already queued so grace-time descendants cannot be
        # omitted from the final process-event union.
        while True:
            try:
                queued = os.read(report_read, 65_536)
            except BlockingIOError:
                break
            if not queued:
                raise ObservationLoss("trusted trace report closed before kill")
            if len(queued) > (
                request.output.structured_result_byte_limit
                - record.structured_result_bytes
            ):
                raise ObservationLoss(
                    "structured-result pipe exceeded its exact byte limit"
                )
            record.structured_result_bytes += len(queued)
            report_buffer.extend(queued)
            decoded_values = []
            _consume_json_line_batch(
                report_buffer,
                lambda value: bool(decoded_values.append(value)),
            )
            for value in decoded_values:
                kind = value["kind"]
                if kind == "process_event":
                    _merge_process_event_classes(
                        record, value.get("event_classes")
                    )
                elif kind in {"member_birth", "member_exit_stop"}:
                    _ack_member_report(
                        value,
                        is_exit_stop=kind == "member_exit_stop",
                        composition=composition,
                        expected_cgroup=expected_cgroup,
                        expected_pid_namespace=namespace_ids["pid"],
                        event_members=event_members,
                        ack_fd=event_ack_write,
                        member_limit=max(1, request.process.max_processes - 2),
                    )
                elif kind == "secondary_exec_denial":
                    _ack_secondary_exec_denial(
                        value,
                        composition=composition,
                        expected_cgroup=expected_cgroup,
                        expected_pid_namespace=namespace_ids["pid"],
                        event_members=event_members,
                        ack_fd=event_ack_write,
                        member_limit=max(
                            1, request.process.max_processes - 2
                        ),
                        denials=secondary_exec_denials,
                    )
                    _merge_process_event_classes(record, ["exec_denied"])
                elif kind in {"limit", "limit_candidate"}:
                    limit_ns = _require_predeadline_limit_observation(
                        record,
                        value,
                        deadline_ns=request.process.deadline_monotonic_ns,
                        provider_observed_ns=time.monotonic_ns(),
                    )
                    value["_predeadline_validated"] = True
                    _translate_limit_member(
                        value,
                        composition,
                        expected_cgroup,
                        namespace_ids["pid"],
                    )
                    if kind == "limit":
                        _select_limit_terminal(record, limit_ns)
                        record.process["filesystem_limit_event"] = dict(value)
                    else:
                        record.process["filesystem_limit_candidate"] = dict(value)
                elif kind == "workload_exit":
                    _record_workload_exit(
                        record,
                        value,
                        deadline_ns=request.process.deadline_monotonic_ns,
                        provider_observed_ns=time.monotonic_ns(),
                    )
                elif kind == "failure":
                    raise ObservationLoss(
                        f"namespace execution failure: {value.get('failure')}"
                    )
                else:
                    raise ObservationLoss(
                        f"unexpected frozen trace report kind: {kind}"
                    )
        if report_buffer:
            raise ObservationLoss("frozen trace report ended with a partial record")
        for item, member in zip(bound_members, members_before_grace):
            member["pidfd_exit_observed"] = item.readable()
            item.close()
        bound_members = _bind_all_members(composition, expected_cgroup)
        members_before_kill = [
            _bound_member_record(
                item,
                observed_before_grace=False,
                observed_before_kill=True,
                pidfd_unreadable_before_kill=not item.readable(),
                pidfd_exit_observed=False,
            )
            for item in bound_members
        ]
        populated_before_kill = _cgroup_populated(composition)
        if populated_before_kill != 1:
            raise ObservationLoss(
                "SIGTERM-ignore containment control left no survivor to kill"
            )
        tree.kill("composition")
        record.process.update(
            {
                "member_count": len(bound_members),
                "all_members_pidfd_bound": True,
                "members_before_grace": members_before_grace,
                "members_before_kill": members_before_kill,
                "grace_started_monotonic_ns": grace_started_ns,
                "grace_finished_monotonic_ns": grace_finished_ns,
                "force_kill_after_grace": True,
                "populated_before_kill": populated_before_kill,
                "cgroup_kill_written": True,
            }
        )
        _wait_until(
            lambda: _cgroup_populated(composition) == 0,
            time.monotonic_ns() + 8_000_000_000,
            "composition cgroup populated=0",
        )
        for item in bound_members:
            if not item.readable(timeout=2):
                raise ObservationLoss(
                    f"PID {item.pid} lacked pidfd exit observation"
                )
        for member in members_before_kill:
            member["pidfd_exit_observed"] = True
        for item, member in event_members.values():
            if not item.readable(timeout=2):
                raise ObservationLoss(
                    f"event-time PID {item.pid} lacked pidfd exit observation"
                )
            member["pidfd_exit_observed"] = True
        record.process["event_members"] = [
            dict(member)
            for _, member in sorted(
                event_members.values(),
                key=lambda value: (
                    int(value[1]["pid"]),
                    int(value[1]["starttime_ticks"]),
                ),
            )
        ]
        record.process["secondary_exec_denials"] = [
            dict(item)
            for item in sorted(
                secondary_exec_denials,
                key=lambda item: (
                    int(item["monotonic_ns"]),
                    int(item["pid"]),
                    int(item["starttime_ticks"]),
                    int(item["syscall_number"]),
                ),
            )
        ]
        pidfd_exit_observed = True
        _bounded_waitpid_status(anchor, timeout=2)
        anchor = -1
        _set_cgroup_frozen(composition, False)
        if scratch_snapshot_fd < 0 or output_snapshot_fd < 0:
            raise ObservationLoss("private filesystem snapshot descriptors are absent")
        record.exit_observation.update(
            _snapshot_filesystem(
                request,
                scratch_snapshot_fd,
                output_snapshot_fd,
            )
        )
        candidate_raw = record.process.get("filesystem_limit_candidate")
        if isinstance(candidate_raw, dict):
            candidate = dict(candidate_raw)
            candidate_errno = candidate.get("errno")
            candidate_signal = candidate.get("signal_number")
            syscall_number = candidate.get("syscall_number")
            scope = candidate.get("scope")
            candidate_monotonic_ns = candidate.get("monotonic_ns")
            if scope == "scratch":
                scope_byte_limit = request.filesystem.scratch_byte_limit
                bytes_full = (
                    record.exit_observation.get("scratch_used_bytes")
                    == request.filesystem.scratch_byte_limit
                )
                inodes_full = (
                    record.exit_observation.get("scratch_used_inodes")
                    == request.filesystem.scratch_inode_limit
                )
            elif scope == "output":
                scope_byte_limit = request.output.file_output_byte_limit
                bytes_full = (
                    record.exit_observation.get("output_used_bytes")
                    == request.filesystem.output_byte_limit
                )
                inodes_full = (
                    record.exit_observation.get("output_used_inodes")
                    == request.filesystem.output_inode_limit
                )
            else:
                scope_byte_limit = None
                bytes_full = inodes_full = False
            limit_kind = candidate.get("limit_kind")
            correlated = (
                candidate_errno in {errno.ENOSPC, errno.EDQUOT}
                and (bytes_full or inodes_full)
                or candidate_errno == errno.EFBIG
                and limit_kind == "syscall_errno"
                and syscall_number
                in FILESYSTEM_QUOTA_FD_WRITE_SYSCALLS_X86_64_V1
                and record.exec_observation.get("file_size_soft_limit")
                == scope_byte_limit
            )
            terminal_conflict = (
                candidate.get("_predeadline_validated") is not True
                or type(candidate_monotonic_ns) is not int
                or candidate_monotonic_ns
                >= request.process.deadline_monotonic_ns
                or record.timeout_triggered
                or "workload_exit_monotonic_ns" in record.process
            )
            if correlated and not terminal_conflict:
                candidate["kind"] = "limit"
                candidate.pop("_predeadline_validated", None)
                record.process["filesystem_limit_event"] = candidate
                _select_limit_terminal(record, candidate_monotonic_ns)
            else:
                record.observer_errors.append(
                    "filesystem-limit candidate lacked matching private quota or "
                    "pre-deadline terminal evidence"
                )
        if record.limit_triggered and (
            record.timeout_triggered
            or "workload_exit_monotonic_ns" in record.process
            or "timeout_trigger_monotonic_ns" in record.process
        ):
            raise ObservationLoss("terminal trigger selection was not mutually exclusive")
        merged_members = _merged_member_records(record.process)
        if len(merged_members) > request.process.max_processes:
            raise ObservationLoss(
                "historical process-member union exceeded request max_processes"
            )
        record.process["member_observations"] = merged_members
        record.process["member_count"] = len(merged_members)
        raw_limit_observation = record.process.get("filesystem_limit_event")
        filesystem_limit_observation = None
        if isinstance(raw_limit_observation, dict):
            filesystem_limit_observation = {
                name: raw_limit_observation.get(name)
                for name in (
                    "limit_kind",
                    "scope",
                    "target_path",
                    "target_fd",
                    "syscall_number",
                    "errno",
                    "signal_number",
                    "signal_code",
                    "fault_address",
                    "pid",
                    "starttime_ticks",
                    "cgroup_path",
                    "monotonic_ns",
                )
            }
            filesystem_limit_observation["kind"] = (
                filesystem_limit_observation.pop("limit_kind")
            )
        process_payload = {
                "initial_pid": record.process.get("initial_pid"),
                "initial_starttime_ticks": record.process.get(
                    "initial_starttime"
                ),
                "initial_pidfd_opened": record.process.get(
                    "initial_pidfd_opened"
                ),
                "observed_pids_max": record.process.get("observed_pids_max"),
                "member_observations": merged_members,
                "member_count": len(merged_members),
                "all_members_pidfd_bound": record.process.get(
                    "all_members_pidfd_bound"
                ),
                "event_classes": record.process.get("event_classes", []),
                "secondary_exec_denials": record.process.get(
                    "secondary_exec_denials", []
                ),
                "retained_outputs": record.exit_observation.get(
                    "retained_outputs", []
                ),
                "workload_exit_code": record.workload_exit_code,
                "workload_exit_monotonic_ns": record.process.get(
                    "workload_exit_monotonic_ns"
                ),
                "timeout_trigger_monotonic_ns": record.process.get(
                    "timeout_trigger_monotonic_ns"
                ),
                "limit_triggered": record.limit_triggered,
                "timeout_triggered": record.timeout_triggered,
                "grace_started_monotonic_ns": record.process.get(
                    "grace_started_monotonic_ns"
                ),
                "grace_finished_monotonic_ns": record.process.get(
                    "grace_finished_monotonic_ns"
                ),
                "force_kill_after_grace": record.process.get(
                    "force_kill_after_grace"
                ),
                "populated_before_kill": populated_before_kill,
                "cgroup_kill_written": record.process.get(
                    "cgroup_kill_written"
                ),
                "populated_after_kill": 0,
                "pidfd_exit_observed": True,
                "survivor_count": 0,
                "filesystem_limit_observation": filesystem_limit_observation,
                **{
                    name: record.exit_observation.get(name)
                    for name in (
                        "quota_observed_after_kill",
                        "scratch_observed_byte_ceiling",
                        "scratch_observed_inode_ceiling",
                        "output_observed_byte_ceiling",
                        "output_observed_inode_ceiling",
                        "scratch_used_bytes",
                        "scratch_used_inodes",
                        "output_used_bytes",
                        "output_used_inodes",
                        "declared_output_allowlist",
                        "observed_output_paths",
                        "undeclared_output_blocked",
                        "output_parent_directories_nonwritable",
                    )
                },
        }

        # Drain all bytes already accepted by the kernel pipes after the kill.
        drain_selector = selectors.DefaultSelector()
        try:
            for descriptor, name in (
                (stdout_read, "stdout"),
                (stderr_read, "stderr"),
            ):
                drain_selector.register(descriptor, selectors.EVENT_READ, name)
            drain_deadline = time.monotonic_ns() + 2_000_000_000
            while drain_selector.get_map() and time.monotonic_ns() < drain_deadline:
                for key, _ in drain_selector.select(timeout=POLL_SECONDS):
                    try:
                        payload = os.read(key.fd, 65_536)
                    except BlockingIOError:
                        continue
                    if not payload:
                        drain_selector.unregister(key.fd)
                    else:
                        streams.consume(str(key.data), payload)
            if drain_selector.get_map():
                streams.observer_loss = True
                raise ObservationLoss("stream pipes did not reach EOF after cgroup kill")
        finally:
            drain_selector.close()
        if streams.trigger is not None and not record.limit_triggered:
            # A complete frozen pre-termination drain makes a first trigger
            # here impossible.  Treat it as observer loss instead of
            # publishing a LIMIT whose kill preceded its trigger.
            raise ObservationLoss(
                "stream limit was first observed only after cgroup.kill"
            )
        final_pipe_capacities = (
            fcntl.fcntl(stdout_read, fcntl.F_GETPIPE_SZ),
            fcntl.fcntl(stderr_read, fcntl.F_GETPIPE_SZ),
        )
        if final_pipe_capacities != (
            STREAM_PIPE_CAPACITY_BYTES_V1,
            STREAM_PIPE_CAPACITY_BYTES_V1,
        ):
            raise ObservationLoss(
                "terminal stream pipe capacity differed from the frozen value"
            )
        streams.pipe_capacity_bytes = final_pipe_capacities[0]
        record.setup["stream_pipe_capacity_bytes"] = final_pipe_capacities[0]
        process_payload["limit_triggered"] = record.limit_triggered
        _mark_pass(record, "process.contain")
        record.observe("process", "process.contain", process_payload)
        record.observe("streams", "streams.final", streams.record())
    finally:
        for item in bound_members:
            try:
                item.close()
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        for item, _ in event_members.values():
            try:
                item.close()
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        # Close every release/placement/data gate before waiting.  A partially
        # placed namespace supervisor must never keep cleanup blocked on a
        # pipe whose peer is still held by this process.
        for descriptor in (
            placement_read,
            placement_write,
            report_read,
            report_write,
            release_read,
            release_write,
            stdout_read,
            stdout_write,
            stderr_read,
            stderr_write,
            snapshot_parent,
            snapshot_child,
            event_ack_read,
            event_ack_write,
        ):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        if anchor > 0:
            try:
                if str(tree.children.get("composition", "")) in tree.identities:
                    tree.kill("composition")
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
            try:
                if anchor_pidfd < 0:
                    reap_deadline = time.monotonic_ns() + 2_000_000_000
                    while True:
                        waited, _ = os.waitpid(anchor, os.WNOHANG)
                        if waited == anchor:
                            pidfd_exit_observed = False
                            break
                        if time.monotonic_ns() >= reap_deadline:
                            raise CleanupIncomplete(
                                "unbound anchor did not exit after gate closure"
                            )
                        time.sleep(POLL_SECONDS)
                    raise CleanupIncomplete(
                        "anchor exited but pidfd identity was not acquired"
                    )
                bound_anchor = _BoundPid(anchor, 0, "", anchor_pidfd)
                if not bound_anchor.readable():
                    signal.pidfd_send_signal(
                        anchor_pidfd, signal.SIGKILL, None, 0
                    )
                if not bound_anchor.readable(timeout=2):
                    raise CleanupIncomplete("anchor pidfd did not become readable")
                pidfd_exit_observed = True
                reap_deadline = time.monotonic_ns() + 2_000_000_000
                while True:
                    try:
                        waited, _ = os.waitpid(anchor, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if waited == anchor:
                        break
                    if time.monotonic_ns() >= reap_deadline:
                        raise CleanupIncomplete("anchor reap exceeded its bound")
                    time.sleep(POLL_SECONDS)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        for descriptor in (
            scratch_snapshot_fd,
            output_snapshot_fd,
            anchor_pidfd,
        ):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        release: dict[str, object] = {
            "exact_paths": [str(path) for path in tree.exact_paths],
            "released_paths": [],
            "populated_zero": False,
            "failures": ["cgroup release was not observed"],
        }
        try:
            if tree.created_paths:
                release = tree.release()
            else:
                release = {
                    "exact_paths": [],
                    "released_paths": [],
                    "populated_zero": True,
                    "failures": [],
                }
        except BaseException as exc:
            cleanup_failures.append(_bounded_failure(exc))
        cleanup_failures.extend(str(item) for item in release["failures"])
        mounts: tuple[str, ...] = ("mount-scan-incomplete",)
        try:
            mounts = _host_mounts_under(temp_root)
        except BaseException as exc:
            cleanup_failures.append(_bounded_failure(exc))
        if mounts:
            cleanup_failures.append(f"host mount residue: {list(mounts)}")
        if temp_root_fd >= 0:
            try:
                os.close(temp_root_fd)
            except OSError as exc:
                cleanup_failures.append(_bounded_failure(exc))
            temp_root_fd = -1
        try:
            residue = _scan_residue(temp_root, namespace_ids)
        except BaseException as exc:
            residue = ("procfs-residue-scan-incomplete",)
            cleanup_failures.append(_bounded_failure(exc))
        if residue:
            cleanup_failures.append(f"process/namespace residue: {list(residue)}")
        ownership_authenticated = False
        try:
            ownership_claimed = (
                record.stage_status.get("ownership.claim", (None,))[0]
                == STAGE_PASS
            )
            _validate_owned_directory(
                provider_parent, provider_parent_identity
            )
            _validate_owned_directory(temp_root, temp_root_identity)
            _validate_ownership_marker(
                marker,
                execution_id=request.execution_id,
                nonce=nonce,
                expected_cgroups=tree.identities if ownership_claimed else {},
                expected_state="owned" if ownership_claimed else "claiming",
            )
            _write_ownership_marker(
                marker,
                execution_id=request.execution_id,
                nonce=nonce,
                cgroups=tree.identities,
                state="released",
            )
            ownership_authenticated = True
        except BaseException as exc:
            cleanup_failures.append(_bounded_failure(exc))
        if ownership_authenticated:
            try:
                _validate_owned_directory(
                    provider_parent, provider_parent_identity
                )
                _validate_owned_directory(temp_root, temp_root_identity)
                _remove_owned_tree_at(
                    provider_parent_fd,
                    request.execution_id,
                    temp_root_identity,
                )
                os.close(provider_parent_fd)
                provider_parent_fd = -1
                os.rmdir(provider_parent.name, dir_fd=trusted_tmp_fd)
            except BaseException as exc:
                cleanup_failures.append(_bounded_failure(exc))
        for descriptor in (temp_root_fd, provider_parent_fd, trusted_tmp_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except BaseException as exc:
                    cleanup_failures.append(_bounded_failure(exc))
        # Selection-root and sealed executable-chain descriptors are part of
        # this execution's owned cleanup transaction.  They must be gone
        # before cleanup.final is observed, including on successful runs.
        try:
            prepared.close()
        except BaseException as exc:
            cleanup_failures.append(_bounded_failure(exc))
        temporary_root_removed = False
        try:
            temporary_root_removed = not temp_root.exists() and not provider_parent.exists()
        except BaseException as exc:
            cleanup_failures.append(_bounded_failure(exc))
        record.cleanup = {
            "cgroup_release": release,
            "mounts": list(mounts),
            "process_residue": list(residue),
            "temporary_root_removed": temporary_root_removed,
            "pidfd_exit_observed": pidfd_exit_observed,
            "failures": cleanup_failures,
        }
        if cleanup_failures:
            record.provider_errors.extend(cleanup_failures)
            if record.stage_status.get("cleanup") is None:
                _fail_stage_and_cascade(
                    record, "cleanup", "CLEANUP_INCOMPLETE"
                )
        elif record.stage_status.get("ownership.claim", (None,))[0] == STAGE_PASS:
            _mark_pass(record, "cleanup")
        record.observe("cleanup", "cleanup.final", dict(record.cleanup))


def _observed_identity(
    value: Mapping[str, object] | None, *, path: str | None = None
) -> ObservedFileIdentityV1 | None:
    if not value:
        return None
    try:
        return ObservedFileIdentityV1(
            path=path if path is not None else str(value["path"]),
            device=int(value["device"]),
            inode=int(value["inode"]),
            mode=int(value["mode"]),
            size=int(value["size"]),
            sha256=str(value["sha256"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ObservationLoss("observed file identity is malformed") from exc


def _selected_observed(item: _SealedFile | None) -> ObservedFileIdentityV1 | None:
    if item is None:
        return None
    return _observed_identity(item.source_identity, path=item.expected.source_path)


def _sealed_observed(item: _SealedFile | None) -> ObservedFileIdentityV1 | None:
    if item is None:
        return None
    return _observed_identity(item.sealed_identity, path=item.expected.private_path)


def _parse_exec_identity(
    record: _RunRecord,
) -> tuple[
    int | None,
    int | None,
    tuple[int, int, int, int] | None,
    tuple[int, int, int, int] | None,
    tuple[int, ...],
    int | None,
    bool | None,
]:
    observation = record.exec_observation

    def first_decimal(name: str) -> int | None:
        raw = observation.get(name)
        if not isinstance(raw, str) or not raw:
            return None
        try:
            return int(raw.split()[0])
        except (IndexError, ValueError):
            return None

    uid = first_decimal("uid")
    gid = first_decimal("gid")
    def four_decimals(name: str) -> tuple[int, int, int, int] | None:
        raw = observation.get(name)
        if not isinstance(raw, str):
            return None
        try:
            values = tuple(int(item) for item in raw.split())
        except ValueError:
            return None
        return values if len(values) == 4 else None  # type: ignore[return-value]

    uid_tuple = four_decimals("uid")
    gid_tuple = four_decimals("gid")
    groups_raw = observation.get("groups")
    groups: tuple[int, ...] = ()
    if isinstance(groups_raw, str) and groups_raw.strip():
        try:
            groups = tuple(int(item) for item in groups_raw.split())
        except ValueError:
            groups = (-1,)
    cap_raw = observation.get("cap_eff")
    try:
        capabilities = int(cap_raw, 16) if isinstance(cap_raw, str) else None
    except ValueError:
        capabilities = None
    nnp_raw = observation.get("no_new_privs")
    no_new_privs = nnp_raw == "1" if isinstance(nnp_raw, str) else None
    return uid, gid, uid_tuple, gid_tuple, groups, capabilities, no_new_privs


def _stage_evidence(record: _RunRecord) -> tuple[EvidenceStageV1, ...]:
    values: list[EvidenceStageV1] = []
    for sequence, (stage, _) in enumerate(STAGE_DEPENDENCIES, start=1):
        status, detail = record.stage_status[stage]
        if status == STAGE_PASS:
            values.append(
                EvidenceStageV1(
                    stage_id=stage,
                    sequence=sequence,
                    status=EvidenceStageStatusV1.PASS,
                )
            )
        elif status == STAGE_FAIL:
            values.append(
                EvidenceStageV1(
                    stage_id=stage,
                    sequence=sequence,
                    status=EvidenceStageStatusV1.FAIL,
                    failure_code=detail,
                )
            )
        else:
            values.append(
                EvidenceStageV1(
                    stage_id=stage,
                    sequence=sequence,
                    status=EvidenceStageStatusV1.NOT_REACHED,
                    blocked_by=detail,
                )
            )
    return tuple(values)


def _build_evidence(
    request: IsolationRequestV1,
    prepared: _PreparedRequest | None,
    record: _RunRecord,
) -> ExecutionEvidenceV1:
    record.finished_ns = max(time.monotonic_ns(), record.started_ns)
    observations: list[OSObservationV1] = []
    os_source_by_event = {
        event_id: os_source
        for event_id, _observation_class, os_source in REQUIRED_OBSERVATION_EVENTS_V1
    }
    for sequence, (raw_class, event_id, payload, observed_ns) in enumerate(
        record.observations, start=1
    ):
        observations.append(
            OSObservationV1.from_payload(
                sequence=sequence,
                observation_class=ObservationClassV1(raw_class),
                event_id=event_id,
                os_source=os_source_by_event.get(
                    event_id, "unrecognized OS observation source"
                ),
                monotonic_ns=min(max(observed_ns, record.started_ns), record.finished_ns),
                payload={"execution_id": request.execution_id, **payload},
            )
        )
    observed_classes = tuple(
        item
        for item in REQUIRED_OBSERVATION_CLASSES_V1
        if any(value.observation_class is item for value in observations)
    )
    missing_classes = tuple(
        item for item in REQUIRED_OBSERVATION_CLASSES_V1 if item not in observed_classes
    )

    cleanup_failures = tuple(
        str(value) for value in record.cleanup.get("failures", ())
    )
    release = record.cleanup.get("cgroup_release")
    release_record = release if isinstance(release, dict) else {}
    temporary_removed = record.cleanup.get("temporary_root_removed") is True
    cleanup = CleanupEvidenceV1(
        cgroup_populated_zero=(
            release_record.get("populated_zero") is True and not cleanup_failures
        ),
        cgroup_removed=(
            not release_record.get("failures")
            and len(release_record.get("released_paths", ()))
            == len(release_record.get("exact_paths", ()))
        ),
        namespace_fds_closed=temporary_removed and not cleanup_failures,
        mounts_removed=not record.cleanup.get("mounts") and not cleanup_failures,
        cwd_root_fds_clear=(
            not record.cleanup.get("process_residue") and not cleanup_failures
        ),
        processes_gone=(
            not record.cleanup.get("process_residue") and not cleanup_failures
        ),
        pidfds_exit_observed=(
            record.cleanup.get("pidfd_exit_observed") is True
        ),
        temporary_root_removed=temporary_removed,
        residue=cleanup_failures,
    )

    exec_observation = record.exec_observation
    if prepared is None:
        selected_entrypoint = sealed_entrypoint = None
        selected_interpreter = sealed_interpreter = None
        selected_loader = sealed_loader = None
    else:
        selected_entrypoint = _selected_observed(prepared.entrypoint)
        sealed_entrypoint = _sealed_observed(prepared.entrypoint)
        selected_interpreter = _selected_observed(prepared.interpreter)
        sealed_interpreter = _sealed_observed(prepared.interpreter)
        selected_loader = _selected_observed(prepared.loader)
        sealed_loader = _sealed_observed(prepared.loader)
    actual_entrypoint = _observed_identity(
        exec_observation.get("actual_entrypoint")
        if isinstance(exec_observation.get("actual_entrypoint"), dict)
        else None
    )
    actual_interpreter = _observed_identity(
        exec_observation.get("actual_interpreter")
        if isinstance(exec_observation.get("actual_interpreter"), dict)
        else None
    )
    actual_loader = _observed_identity(
        exec_observation.get("actual_loader")
        if isinstance(exec_observation.get("actual_loader"), dict)
        else None
    )
    chain_complete = bool(record.exec_observation and prepared is not None)
    chain = ExecChainEvidenceV1(
        requested_entrypoint=request.executable.entrypoint,
        selected_entrypoint=selected_entrypoint,
        sealed_entrypoint=sealed_entrypoint,
        actual_entrypoint=actual_entrypoint,
        requested_interpreter=request.executable.interpreter,
        selected_interpreter=selected_interpreter,
        sealed_interpreter=sealed_interpreter,
        actual_interpreter=actual_interpreter,
        requested_loader=request.executable.loader,
        selected_loader=selected_loader,
        sealed_loader=sealed_loader,
        actual_loader=actual_loader,
        entrypoint_seals=REQUIRED_MEMFD_SEALS_V1 if prepared is not None else (),
        interpreter_seals=(
            REQUIRED_MEMFD_SEALS_V1
            if prepared is not None and prepared.interpreter is not None
            else ()
        ),
        loader_seals=(
            REQUIRED_MEMFD_SEALS_V1
            if prepared is not None and prepared.loader is not None
            else ()
        ),
        effective_argv_sha256=(
            str(exec_observation["effective_argv_sha256"])
            if exec_observation.get("effective_argv_sha256") is not None
            else None
        ),
        effective_argv_count=(
            int(exec_observation["effective_argv_count"])
            if exec_observation.get("effective_argv_count") is not None
            else None
        ),
        effective_environment_sha256=(
            str(exec_observation["effective_environment_sha256"])
            if exec_observation.get("effective_environment_sha256") is not None
            else None
        ),
        effective_environment_count=(
            int(exec_observation["effective_environment_count"])
            if exec_observation.get("effective_environment_count") is not None
            else None
        ),
        open_sequence=1 if prepared is not None else None,
        seal_sequence=2 if prepared is not None else None,
        recheck_sequence=3 if prepared is not None else None,
        exec_sequence=4 if record.workload_released else None,
        ptrace_exec_sequence=5 if record.exec_observation else None,
        mismatch_code=None if chain_complete else "EXEC_CHAIN_INCOMPLETE",
        denial_code=None,
    )

    (
        uid,
        gid,
        uid_tuple,
        gid_tuple,
        groups,
        capabilities,
        no_new_privs,
    ) = _parse_exec_identity(record)
    event_classes_raw = record.process.get("event_classes", ())
    event_classes = (
        tuple(str(item) for item in event_classes_raw)
        if isinstance(event_classes_raw, list)
        else ()
    )
    member_records = {
        (int(raw["pid"]), int(raw["starttime_ticks"])): raw
        for raw in _merged_member_records(record.process)
    }
    member_observations = tuple(
        ProcessMemberEvidenceV1(
            pid=key[0],
            starttime_ticks=key[1],
            cgroup_path=str(raw["cgroup_path"]),
            pidfd_opened=raw.get("pidfd_opened") is True,
            identity_revalidated=raw.get("identity_revalidated") is True,
            observed_before_grace=raw.get("observed_before_grace") is True,
            observed_before_kill=raw.get("observed_before_kill") is True,
            pidfd_unreadable_before_kill=(
                raw.get("pidfd_unreadable_before_kill") is True
            ),
            pidfd_exit_observed=raw.get("pidfd_exit_observed") is True,
        )
        for key, raw in sorted(member_records.items())
    )
    raw_secondary_denials = record.process.get("secondary_exec_denials", ())
    secondary_exec_denials = tuple(
        SecondaryExecDenialEvidenceV1(
            pid=int(raw["pid"]),
            starttime_ticks=int(raw["starttime_ticks"]),
            cgroup_path=str(raw["cgroup_path"]),
            syscall_number=int(raw["syscall_number"]),
            errno=int(raw["errno"]),
            monotonic_ns=int(raw["monotonic_ns"]),
        )
        for raw in raw_secondary_denials
        if isinstance(raw, dict)
    )
    process = ProcessEvidenceV1(
        cgroup_name=request.process.cgroup_name,
        initial_pid=(
            int(record.process["initial_pid"])
            if "initial_pid" in record.process
            else None
        ),
        initial_starttime_ticks=(
            int(record.process["initial_starttime"])
            if "initial_starttime" in record.process
            else None
        ),
        initial_pidfd_opened=record.process.get("initial_pidfd_opened") is True,
        observed_uid=uid,
        observed_gid=gid,
        observed_uid_tuple=uid_tuple,
        observed_gid_tuple=gid_tuple,
        observed_supplementary_groups=groups,
        observed_effective_capability_mask=capabilities,
        observed_no_new_privs=no_new_privs,
        observed_pids_max=(
            int(record.process["observed_pids_max"])
            if record.process.get("observed_pids_max") is not None
            else None
        ),
        member_observations=member_observations,
        member_count_observed=len(member_observations),
        all_members_pidfd_bound=record.process.get("all_members_pidfd_bound") is True,
        event_classes=event_classes,
        secondary_exec_denials=secondary_exec_denials,
        timeout_triggered=record.timeout_triggered,
        limit_triggered=record.limit_triggered,
        workload_exit_monotonic_ns=(
            int(record.process["workload_exit_monotonic_ns"])
            if record.process.get("workload_exit_monotonic_ns") is not None
            else None
        ),
        timeout_trigger_monotonic_ns=(
            int(record.process["timeout_trigger_monotonic_ns"])
            if record.process.get("timeout_trigger_monotonic_ns") is not None
            else None
        ),
        termination_grace_ns=request.process.termination_grace_ns,
        grace_started_monotonic_ns=(
            int(record.process["grace_started_monotonic_ns"])
            if "grace_started_monotonic_ns" in record.process
            else None
        ),
        grace_finished_monotonic_ns=(
            int(record.process["grace_finished_monotonic_ns"])
            if "grace_finished_monotonic_ns" in record.process
            else None
        ),
        force_kill_after_grace=(
            record.process.get("force_kill_after_grace") is True
        ),
        cgroup_kill_written=record.process.get("cgroup_kill_written") is True,
        populated_before_kill=(
            int(record.process["populated_before_kill"])
            if "populated_before_kill" in record.process
            else None
        ),
        populated_after_cleanup=0 if cleanup.cgroup_populated_zero else None,
        pidfd_exit_observed=cleanup.pidfds_exit_observed,
        survivor_observation_available=cleanup.processes_gone,
        current_execution_survivor_count=0 if cleanup.processes_gone else None,
    )

    exit_observation = record.exit_observation
    retained_outputs = tuple(
        value
        for value in (
            _observed_identity(item)
            for item in exit_observation.get("retained_outputs", ())
            if isinstance(item, dict)
        )
        if value is not None
    )
    structured_result_bytes = record.structured_result_bytes
    quota_root_raw = record.setup.get("private_quota_observations")
    quota_root = quota_root_raw if isinstance(quota_root_raw, dict) else {}

    def quota_before(name: str) -> PrivateMountQuotaEvidenceV1 | None:
        raw = quota_root.get(name)
        if not isinstance(raw, dict):
            return None
        try:
            options = raw["mount_options"]
            if not isinstance(options, list):
                return None
            return PrivateMountQuotaEvidenceV1(
                filesystem_type=str(raw["filesystem_type"]),
                mount_options=tuple(str(item) for item in options),
                byte_ceiling=int(raw["byte_ceiling"]),
                inode_ceiling=int(raw["inode_ceiling"]),
                fragment_size=int(raw["fragment_size"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    limit_raw = record.process.get("filesystem_limit_event")
    limit_record = limit_raw if isinstance(limit_raw, dict) else None
    limit_observation: FilesystemLimitObservationV1 | None = None
    if limit_record is not None:
        try:
            limit_kind = FilesystemLimitKindV1(str(limit_record["limit_kind"]))
            limit_observation = FilesystemLimitObservationV1(
                kind=limit_kind,
                scope=FilesystemLimitScopeV1(str(limit_record["scope"])),
                target_path=str(limit_record["target_path"]),
                target_fd=(
                    int(limit_record["target_fd"])
                    if limit_record.get("target_fd") is not None
                    else None
                ),
                syscall_number=(
                    int(limit_record["syscall_number"])
                    if limit_record.get("syscall_number") is not None
                    else None
                ),
                errno=(
                    int(limit_record["errno"])
                    if limit_record.get("errno") is not None
                    else None
                ),
                signal_number=(
                    int(limit_record["signal_number"])
                    if limit_record.get("signal_number") is not None
                    else None
                ),
                signal_code=(
                    int(limit_record["signal_code"])
                    if limit_record.get("signal_code") is not None
                    else None
                ),
                fault_address=(
                    int(limit_record["fault_address"])
                    if limit_record.get("fault_address") is not None
                    else None
                ),
                pid=int(limit_record["pid"]),
                starttime_ticks=int(limit_record["starttime_ticks"]),
                cgroup_path=str(limit_record["cgroup_path"]),
                monotonic_ns=int(limit_record["monotonic_ns"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ObservationLoss(
                "filesystem-limit observation is malformed"
            ) from exc

    scans_raw = record.setup.get("read_only_input_scans", ())
    read_only_input_scans: tuple[ReadOnlyRootScanEvidenceV1, ...] = ()
    if isinstance(scans_raw, list):
        try:
            read_only_input_scans = tuple(
                ReadOnlyRootScanEvidenceV1(
                    root=request.filesystem.read_only_inputs[index],
                    observed_device=int(raw["observed_device"]),
                    observed_inode=int(raw["observed_inode"]),
                    entries_scanned=int(raw["entries_scanned"]),
                    entry_limit=int(raw["entry_limit"]),
                    allowed_inode_types=tuple(
                        str(item) for item in raw["allowed_inode_types"]
                    ),
                    fd_relative=raw.get("fd_relative") is True,
                    nofollow=raw.get("nofollow") is True,
                    no_xdev=raw.get("no_xdev") is True,
                    identity_revalidated=(
                        raw.get("identity_revalidated") is True
                    ),
                    stable_during_scan=(
                        raw.get("stable_during_scan") is True
                    ),
                )
                for index, raw in enumerate(scans_raw)
                if isinstance(raw, dict)
            )
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ObservationLoss(
                "read-only input scan observation is malformed"
            ) from exc

    filesystem = FilesystemEvidenceV1(
        effective_read_only_inputs=request.filesystem.read_only_inputs,
        read_only_input_scans=read_only_input_scans,
        cwd_private_path=request.filesystem.cwd_private_path,
        scratch_private_path=request.filesystem.scratch_private_path,
        output_private_path=request.filesystem.output_private_path,
        scratch_used_bytes=int(exit_observation.get("scratch_used_bytes", 0)),
        scratch_used_inodes=int(exit_observation.get("scratch_used_inodes", 0)),
        scratch_byte_limit=request.filesystem.scratch_byte_limit,
        scratch_inode_limit=request.filesystem.scratch_inode_limit,
        output_used_bytes=int(exit_observation.get("output_used_bytes", 0)),
        output_used_inodes=int(exit_observation.get("output_used_inodes", 0)),
        output_byte_limit=request.filesystem.output_byte_limit,
        output_inode_limit=request.filesystem.output_inode_limit,
        structured_result_bytes=structured_result_bytes,
        structured_result_byte_limit=request.output.structured_result_byte_limit,
        file_output_byte_limit=request.output.file_output_byte_limit,
        quota_observed_before_release=(
            quota_root.get("observed_before_release") is True
        ),
        scratch_quota_before_release=quota_before("scratch"),
        output_quota_before_release=quota_before("output"),
        quota_observed_after_kill=(
            exit_observation.get("quota_observed_after_kill") is True
        ),
        scratch_observed_byte_ceiling=(
            int(exit_observation["scratch_observed_byte_ceiling"])
            if "scratch_observed_byte_ceiling" in exit_observation
            else None
        ),
        scratch_observed_inode_ceiling=(
            int(exit_observation["scratch_observed_inode_ceiling"])
            if "scratch_observed_inode_ceiling" in exit_observation
            else None
        ),
        output_observed_byte_ceiling=(
            int(exit_observation["output_observed_byte_ceiling"])
            if "output_observed_byte_ceiling" in exit_observation
            else None
        ),
        output_observed_inode_ceiling=(
            int(exit_observation["output_observed_inode_ceiling"])
            if "output_observed_inode_ceiling" in exit_observation
            else None
        ),
        declared_output_allowlist=request.filesystem.retained_output_paths,
        observed_output_paths=tuple(
            str(value)
            for value in exit_observation.get("observed_output_paths", ())
        ),
        undeclared_output_blocked=(
            exit_observation.get("undeclared_output_blocked") is True
        ),
        output_parent_directories_nonwritable=(
            exit_observation.get("output_parent_directories_nonwritable") is True
        ),
        limit_observation=limit_observation,
        rejected_boundary_attempts=tuple(
            str(value)
            for value in record.setup.get("rejected_boundary_attempts", ())
        ),
        retained_outputs=retained_outputs,
        teardown_observed=cleanup.complete,
    )

    network_raw = record.setup.get("network")
    network_record = network_raw if isinstance(network_raw, dict) else {}
    seccomp_raw = record.setup.get("seccomp_controls")
    seccomp_record = seccomp_raw if isinstance(seccomp_raw, dict) else {}
    denied_network_raw = seccomp_record.get("network")
    denied_network = (
        denied_network_raw if isinstance(denied_network_raw, dict) else {}
    )
    denied_attempt_classes: tuple[str, ...] = ()
    if (
        set(denied_network)
        == {"dns", "ipv4", "ipv6", "namespace_bridge", "netlink", "packet"}
        and all(value == errno.EPERM for value in denied_network.values())
        and network_record.get("negative") is True
        and exec_observation.get("inherited_network_fd_absent") is True
    ):
        denied_attempt_classes = (
            "dns",
            "inherited_descriptor",
            "ipv4",
            "ipv6",
            "loopback",
            "namespace_bridge",
            "netlink",
            "packet",
        )
    network = NetworkEvidenceV1(
        namespace_inode=(
            int(network_record["namespace_inode"])
            if "namespace_inode" in network_record
            else None
        ),
        flags_after_up=(
            int(network_record["flags_after_up"])
            if "flags_after_up" in network_record
            else None
        ),
        flags_after_down=(
            int(network_record["flags_after_down"])
            if "flags_after_down" in network_record
            else None
        ),
        operstate_after_up_json=json.dumps(
            network_record.get("operstate_after_up", {"unavailable": True}),
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
        operstate_after_down_json=json.dumps(
            network_record.get("operstate_after_down", {"unavailable": True}),
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
        live_endpoint_positive_control=network_record.get("positive") is True,
        live_endpoint_denial_control=network_record.get("negative") is True,
        inherited_network_fd_absent_at_exec=(
            exec_observation.get("inherited_network_fd_absent") is True
        ),
        seccomp_filter_sha256=str(
            record.setup.get(
                "seccomp_filter_sha256",
                request.network.socket_filter_sha256,
            )
        ),
        socket_denial_errno=(
            int(record.setup["socket_denial_errno"])
            if "socket_denial_errno" in record.setup
            else None
        ),
        denied_attempt_classes=denied_attempt_classes,
    )

    raw_streams = record.streams or _RawStreams(
        request.streams.stdout_raw_byte_limit,
        request.streams.stderr_raw_byte_limit,
        request.streams.combined_raw_byte_limit,
        request.streams.retained_byte_limit,
    )
    stream_record = raw_streams.record()
    raw_counts = stream_record["raw_bytes"]
    retained_counts = stream_record["retained_bytes"]
    discarded_counts = stream_record["discarded_bytes"]
    assert isinstance(raw_counts, dict)
    assert isinstance(retained_counts, dict)
    assert isinstance(discarded_counts, dict)

    def stream_count(name: str, limit: int) -> StreamCountV1:
        emitted = int(raw_counts[name])
        retained = int(retained_counts[name])
        discarded = int(discarded_counts[name])
        return StreamCountV1(
            emitted_bytes=emitted,
            retained_bytes=retained,
            discarded_bytes=discarded,
            limit_bytes=limit,
            limit_triggered=emitted > limit,
        )

    stdout_count = stream_count("stdout", request.streams.stdout_raw_byte_limit)
    stderr_count = stream_count("stderr", request.streams.stderr_raw_byte_limit)
    combined_emitted = stdout_count.emitted_bytes + stderr_count.emitted_bytes
    combined_retained = stdout_count.retained_bytes + stderr_count.retained_bytes
    combined_discarded = stdout_count.discarded_bytes + stderr_count.discarded_bytes
    streams = StreamEvidenceV1(
        stdout=stdout_count,
        stderr=stderr_count,
        combined=StreamCountV1(
            emitted_bytes=combined_emitted,
            retained_bytes=combined_retained,
            discarded_bytes=combined_discarded,
            limit_bytes=request.streams.combined_raw_byte_limit,
            limit_triggered=(
                combined_emitted > request.streams.combined_raw_byte_limit
            ),
        ),
        retained_byte_limit=request.streams.retained_byte_limit,
        pipe_capacity_bytes=(
            int(record.setup["stream_pipe_capacity_bytes"])
            if "stream_pipe_capacity_bytes" in record.setup
            else None
        ),
        decoding_status=StreamDecodingStatusV1(
            str(stream_record["decoding_status"])
        ),
        overflow=False,
        observer_loss=raw_streams.observer_loss,
    )

    ownership_reached = (
        record.process.get("resource_claim_started") is True
        or
        record.stage_status.get("ownership.claim", (None,))[0] == STAGE_PASS
    )
    if ownership_reached and not cleanup.complete:
        outcome = ExecutionOutcomeV1.CLEANUP_INCOMPLETE
    elif record.policy_denial:
        outcome = ExecutionOutcomeV1.POLICY_DENIAL
    elif not record.workload_released and (record.provider_errors or record.observer_errors):
        outcome = ExecutionOutcomeV1.CAPABILITY_BLOCKER
    elif not cleanup.complete:
        outcome = ExecutionOutcomeV1.CLEANUP_INCOMPLETE
    elif record.provider_errors or record.observer_errors:
        outcome = (
            ExecutionOutcomeV1.CAPABILITY_BLOCKER
            if not record.workload_released
            else ExecutionOutcomeV1.OBSERVATION_INCOMPLETE
        )
    elif record.timeout_triggered:
        outcome = ExecutionOutcomeV1.TIMEOUT
    elif record.limit_triggered:
        outcome = ExecutionOutcomeV1.LIMIT
    elif not record.workload_released:
        outcome = ExecutionOutcomeV1.CAPABILITY_BLOCKER
    elif record.workload_exit_code == 0:
        outcome = ExecutionOutcomeV1.SUCCESS
    elif record.workload_exit_code is not None:
        outcome = ExecutionOutcomeV1.WORKLOAD_FAILURE
    else:
        outcome = ExecutionOutcomeV1.OBSERVATION_INCOMPLETE

    completeness = EvidenceCompletenessV1(
        required_observation_classes=REQUIRED_OBSERVATION_CLASSES_V1,
        observed_observation_classes=observed_classes,
        missing_observation_classes=missing_classes,
        sequence_gaps=(),
        provider_errors=tuple(record.provider_errors)[:256],
        observer_errors=tuple(record.observer_errors)[:256],
        buffer_loss=raw_streams.observer_loss,
        teardown_observed=cleanup.complete,
        cleanup=cleanup,
    )
    correlation = CorrelationEvidenceV1(
        schema_version=ISOLATION_EVIDENCE_SCHEMA_V1,
        profile=request.profile,
        execution_id=request.execution_id,
        request_sha256=request.request_sha256,
        **request.identity.to_record(),
        backend_profile=request.backend_profile.value,
        backend_configuration_sha256=request.identity.configuration_sha256,
        required_capability_set_sha256=request.required_capability_set_sha256,
        os_name=platform.system(),
        architecture=platform.machine(),
        started_monotonic_ns=record.started_ns,
        deadline_monotonic_ns=request.process.deadline_monotonic_ns,
        finished_monotonic_ns=record.finished_ns,
    )
    return _build_execution_evidence_v1(
        correlation=correlation,
        capability_stages=_stage_evidence(record),
        stage_dependencies=tuple(
            StageDependencyV1(stage_id=stage, depends_on=dependencies)
            for stage, dependencies in STAGE_DEPENDENCIES
        ),
        observations=tuple(observations),
        exec_chain=chain,
        process=process,
        filesystem=filesystem,
        network=network,
        streams=streams,
        completeness=completeness,
        outcome=outcome,
        workload_released=record.workload_released,
        workload_exit_code=record.workload_exit_code,
    )


def _first_reachable_missing_stage(record: _RunRecord) -> str:
    for stage, dependencies in STAGE_DEPENDENCIES:
        if stage in record.stage_status:
            continue
        if all(
            record.stage_status.get(item, (None,))[0] == STAGE_PASS
            for item in dependencies
        ):
            return stage
    raise ObservationLoss("no reachable stage remained for direct failure")


class LinuxNativeSupervisorV1:
    """Fail-closed Linux/x86_64 local-OS isolation supervisor.

    The caller must enter this API with the already-qualified supervisor
    privilege.  This class never invokes an alternate backend, a container
    runtime, a helper binary, or an external service.
    """

    backend_profile = BACKEND_PROFILE
    required_capability_set_sha256 = REQUIRED_CAPABILITY_SET_DIGEST

    def execute(self, request: IsolationRequestV1) -> ExecutionEvidenceV1:
        if not isinstance(request, IsolationRequestV1):
            raise TypeError("request must be IsolationRequestV1")
        record = _RunRecord(started_ns=time.monotonic_ns())
        prepared: _PreparedRequest | None = None
        validation = validate_isolation_request_v1(request)
        if not validation.ok:
            code = (
                validation.error_code.value
                if validation.error_code is not None
                else "INVALID_REQUEST"
            )
            rendered = "; ".join(validation.reasons)[:MAX_FAILURE_TEXT]
            raise InvalidIsolationRequest(f"{code}: {rendered}")
        _mark_pass(record, "request.validate")
        try:
            if platform.system() != "Linux" or platform.machine() != "x86_64":
                raise CapabilityBlocker("core v1 supports only Linux/x86_64")
            if os.geteuid() != 0:
                raise CapabilityBlocker(
                    "linux_native_supervisor_v1 requires trusted root privilege"
                )
            if time.monotonic_ns() >= request.process.deadline_monotonic_ns:
                raise CapabilityBlocker("monotonic deadline elapsed before gate")
            if (
                request.process.deadline_monotonic_ns - time.monotonic_ns()
                > 300_000_000_000
            ):
                raise CapabilityBlocker("monotonic deadline exceeds the v1 horizon")
            cgroup2_gate = _validate_cgroup2_host_gate()
            core_pipe_helper_absent = _validate_core_pattern_host_gate()
            probe_fd = _openat2(
                AT_FDCWD,
                f"/proc/{os.getpid()}/status",
                resolve=RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
            )
            try:
                payload = os.read(probe_fd, 65_537)
                if (
                    len(payload) > 65_536
                    or f"Pid:\t{os.getpid()}\n".encode("ascii") not in payload
                ):
                    raise CapabilityBlocker(
                        "openat2 numeric-proc host control was invalid"
                    )
            finally:
                os.close(probe_fd)
            self_pidfd = os.pidfd_open(os.getpid())
            os.close(self_pidfd)
            abi_control = _mandatory_abi_control()
            # Fatal x32 and non-process exact-BPF controls run in gated,
            # outer-owned direct children before any selection FD exists.
            # Filtered fork/vfork positives run later in an owned auxiliary
            # cgroup before the request composition is created.
            process_controls = _seccomp_process_controls()
            seccomp_controls = _seccomp_socket_control(process_controls)
            _mark_pass(record, "host.gate")
            record.observe(
                "capability",
                "host.gate",
                {
                    "os": platform.system(),
                    "architecture": platform.machine(),
                    "effective_uid": os.geteuid(),
                    "cgroup_v2": (CGROUP_ROOT / "cgroup.controllers").is_file(),
                    "cgroup2_gate": cgroup2_gate,
                    "openat2": True,
                    "pidfd": True,
                    "monotonic": True,
                    "fallback": False,
                    "mandatory_abi_control": abi_control,
                    "core_pipe_helper_absent": core_pipe_helper_absent,
                },
            )

            prepared = _PreparedRequest.create(request)
            _mark_pass(record, "identity.seal")
            record.observe(
                "exec_chain",
                "identity.seal",
                {
                    "entrypoint": {
                        "source_identity": {
                            "path": prepared.entrypoint.expected.source_path,
                            **prepared.entrypoint.source_identity,
                        },
                        "sealed_identity": {
                            "path": prepared.entrypoint.expected.private_path,
                            **prepared.entrypoint.sealed_identity,
                        },
                    },
                    "interpreter": (
                        {
                            "source_identity": {
                                "path": prepared.interpreter.expected.source_path,
                                **prepared.interpreter.source_identity,
                            },
                            "sealed_identity": {
                                "path": prepared.interpreter.expected.private_path,
                                **prepared.interpreter.sealed_identity,
                            },
                        }
                        if prepared.interpreter is not None
                        else None
                    ),
                    "loader": (
                        {
                            "source_identity": {
                                "path": prepared.loader.expected.source_path,
                                **prepared.loader.source_identity,
                            },
                            "sealed_identity": {
                                "path": prepared.loader.expected.private_path,
                                **prepared.loader.sealed_identity,
                            },
                        }
                        if prepared.loader is not None
                        else None
                    ),
                    "seals": list(REQUIRED_MEMFD_SEALS_V1),
                },
            )
            _run_prepared(prepared, record, seccomp_controls)
        except BaseException as exc:
            failure_code = (
                "HOST_CAPABILITY_BLOCKER"
                if isinstance(exc, CapabilityBlocker)
                else "IDENTITY_MISMATCH"
                if isinstance(exc, IdentityMismatch)
                else "OBSERVATION_LOSS"
                if isinstance(exc, ObservationLoss)
                else "CLEANUP_INCOMPLETE"
                if isinstance(exc, CleanupIncomplete)
                else "PROVIDER_ERROR"
            )
            if isinstance(exc, ObservationLoss):
                record.observer_errors.append(_bounded_failure(exc))
            else:
                record.provider_errors.append(_bounded_failure(exc))
            if isinstance(exc, IdentityMismatch):
                record.policy_denial = True
            try:
                failed_stage = _first_reachable_missing_stage(record)
            except ObservationLoss:
                failed_stage = "cleanup"
            if failed_stage not in record.stage_status:
                _fail_stage_and_cascade(record, failed_stage, failure_code)
        finally:
            if prepared is not None:
                try:
                    prepared.close()
                except BaseException as exc:
                    failure = _bounded_failure(exc)
                    record.provider_errors.append(failure)
                    cleanup = dict(record.cleanup)
                    failures = list(cleanup.get("failures", []))
                    failures.append(failure)
                    cleanup["failures"] = failures
                    record.cleanup = cleanup
                    record.stage_status["cleanup"] = (
                        STAGE_FAIL,
                        "CLEANUP_INCOMPLETE",
                    )

        # Every unrecorded stage must be a declared dependent cascade.  This
        # rejects flat synthetic failures and guarantees one real cause.
        dependency_map = dict(STAGE_DEPENDENCIES)
        for stage, dependencies in STAGE_DEPENDENCIES:
            if stage in record.stage_status:
                continue
            blockers = [
                item
                for item in dependencies
                if record.stage_status.get(item, (None,))[0] != STAGE_PASS
            ]
            if not blockers:
                _fail_stage_and_cascade(
                    record, stage, "OBSERVATION_INCOMPLETE"
                )
                continue
            blocker = blockers[0]
            while record.stage_status[blocker][0] == STAGE_NOT_REACHED:
                detail = record.stage_status[blocker][1]
                if detail is None:
                    break
                blocker = detail
            record.stage_status[stage] = (STAGE_NOT_REACHED, blocker)
        return _build_evidence(request, prepared, record)


def execute_isolation_request_v1(
    request: IsolationRequestV1,
) -> ExecutionEvidenceV1:
    """Execute only through the sole core-v1 backend; no fallback exists."""

    return LinuxNativeSupervisorV1().execute(request)


__all__ = [
    "BACKEND_PROFILE",
    "REQUIRED_CAPABILITY_SET_DIGEST",
    "CapabilityBlocker",
    "CleanupIncomplete",
    "IdentityMismatch",
    "InvalidIsolationRequest",
    "IsolationBackendError",
    "LinuxNativeSupervisorV1",
    "ObservationLoss",
    "execute_isolation_request_v1",
]
