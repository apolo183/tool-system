from __future__ import annotations

import hashlib
import json
import posixpath
import re
import stat
from dataclasses import dataclass
from enum import Enum


ISOLATION_REQUEST_SCHEMA_V1 = "tool-system-isolation-request-v1"
ISOLATION_PROFILE_V1 = "ts_b02_core_local_os_v1"
LINUX_NATIVE_SUPERVISOR_V1 = "linux_native_supervisor_v1"

REQUIRED_CAPABILITIES_V1 = (
    "linux_x86_64",
    "privileged_supervisor",
    "mount_pid_net_ipc_uts_namespaces",
    "recursive_private_mount_propagation",
    "private_cgroup_v2",
    "cgroup_kill_and_populated_zero",
    "private_root_pivot_root",
    "tmpfs_byte_and_inode_quotas",
    "default_deny_network",
    "inherited_network_descriptor_closure",
    "seccomp_socket_denial",
    "native_syscall_abi_ceiling_denial",
    "openat2_boundary_resolution",
    "execveat_descriptor_execution",
    "ptrace_exec_observation",
    "sealed_executable_interpreter_loader_chain",
    "secondary_exec_entry_denial",
    "non_namespaced_keyring_denial",
    "fixed_resource_limit_mutation_denial",
    "unaccounted_memfd_denial",
    "filesystem_xattr_mutation_denial",
    "filesystem_lock_and_lease_denial",
    "filesystem_global_sync_denial",
    "filesystem_ioctl_denial",
    "shared_futex_denial",
    "cross_process_memory_barrier_denial",
    "host_uid_scope_priority_denial",
    "host_system_perf_event_denial",
    "core_pipe_helper_gate",
    "zero_core_rlimit",
    "pidfd_process_identity",
    "historical_pidfd_member_ack",
    "incremental_raw_stream_limits",
    "stream_pipe_capacity_mutation_denial",
    "packet_pipe_denial",
    "monotonic_timeout",
    "complete_owned_resource_cleanup",
)

DENIED_CONTROL_OPERATIONS_V1 = (
    "cgroup_control",
    "core_dump_control",
    "anonymous_memory_file_control",
    "filesystem_lock_and_lease_control",
    "filesystem_global_sync_control",
    "filesystem_ioctl_control",
    "filesystem_xattr_control",
    "shared_futex_control",
    "cross_process_memory_barrier_control",
    "host_uid_scope_priority_control",
    "host_system_perf_event_control",
    "keyring_control",
    "mount_control",
    "namespace_control",
    "network_control",
    "provider_descriptor_access",
    "provider_process_ptrace",
    "privilege_escalation",
    "resource_limit_control",
    "secondary_exec_control",
    "stream_pipe_capacity_control",
    "packet_pipe_control",
)


def canonical_json_bytes(value: object) -> bytes:
    """Return the sole canonical JSON representation used by this interface."""

    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return rendered.encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("value must be finite canonical JSON") from exc


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


REQUIRED_CAPABILITY_SET_SHA256_V1 = canonical_sha256(
    list(REQUIRED_CAPABILITIES_V1)
)
SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1 = (
    ("socket", 41),
    ("socketpair", 53),
    ("ptrace", 101),
    ("process_vm_readv", 310),
    ("process_vm_writev", 311),
    ("mount", 165),
    ("umount2", 166),
    ("pivot_root", 155),
    ("unshare", 272),
    ("setns", 308),
    ("bpf", 321),
    ("perf_event_open", 298),
    ("open_tree", 428),
    ("open_tree_attr", 467),
    ("move_mount", 429),
    ("fsopen", 430),
    ("fsconfig", 431),
    ("fsmount", 432),
    ("fspick", 433),
    ("mount_setattr", 442),
    ("clone3", 435),
    ("io_setup", 206),
    ("io_destroy", 207),
    ("io_getevents", 208),
    ("io_submit", 209),
    ("io_cancel", 210),
    ("io_pgetevents", 333),
    ("io_uring_setup", 425),
    ("add_key", 248),
    ("request_key", 249),
    ("keyctl", 250),
    ("setrlimit", 160),
    ("prlimit64", 302),
    ("memfd_create", 319),
    ("memfd_secret", 447),
    ("setxattr", 188),
    ("lsetxattr", 189),
    ("fsetxattr", 190),
    ("setxattrat", 463),
    ("removexattr", 197),
    ("lremovexattr", 198),
    ("fremovexattr", 199),
    ("removexattrat", 466),
    ("file_setattr", 469),
    ("flock", 73),
    ("sync", 162),
    ("syncfs", 306),
    ("quotactl", 179),
    ("quotactl_fd", 443),
    ("futex_waitv", 449),
    ("futex_wake", 454),
    ("futex_wait", 455),
    ("futex_requeue", 456),
    ("membarrier", 324),
    ("ioctl", 16),
    ("getpriority", 140),
    ("setpriority", 141),
    ("ioprio_set", 251),
    ("ioprio_get", 252),
)
FCNTL_DENIED_COMMANDS_V1 = (
    ("F_SETFL", 4),
    ("F_SETLK", 6),
    ("F_SETLKW", 7),
    ("F_OFD_SETLK", 37),
    ("F_OFD_SETLKW", 38),
    ("F_SETLEASE", 1024),
    ("F_SETPIPE_SZ", 1031),
    ("F_SET_RW_HINT", 1036),
    ("F_SET_FILE_RW_HINT", 1038),
    ("F_SETDELEG", 1040),
)
CLONE_NAMESPACE_FLAGS_MASK_V1 = 0x7E830F80
FUTEX_PRIVATE_FLAG_V1 = 0x80
PIPE2_DENIED_FLAGS_V1 = (
    ("O_DIRECT", 0x4000),
    ("O_NOTIFICATION_PIPE", 0x80),
)
X32_SYSCALL_BIT_V1 = 0x40000000
AUDIT_ARCH_X86_64_V1 = 0xC000003E
NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1 = 470
SOCKET_DENIAL_FILTER_ROWS_V1 = (
    (0x20, 0, 0, 4),
    (0x15, 1, 0, AUDIT_ARCH_X86_64_V1),
    (0x06, 0, 0, 0x80000000),
    (0x20, 0, 0, 0),
    (0x45, 0, 1, X32_SYSCALL_BIT_V1),
    (0x06, 0, 0, 0x80000000),
    # V1 is audited through Linux 6.18 syscall 469.  Fail closed for every
    # later native x86_64 syscall until a new profile deliberately audits it.
    (0x35, 0, 1, NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1),
    (0x06, 0, 0, 0x00050001),
    *(
        row
        for _, number in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1
        for row in (
            (0x15, 0, 1, number),
            (0x06, 0, 0, 0x00050001),
        )
    ),
    # Legacy futex is permitted only for process-private keys. Shared futex
    # operations can synchronize a host mapping of an authorized input inode.
    (0x15, 0, 3, 202),
    (0x20, 0, 0, 24),
    (0x45, 1, 0, FUTEX_PRIVATE_FLAG_V1),
    (0x06, 0, 0, 0x00050001),
    (0x20, 0, 0, 0),
    # Packet-mode and notification pipes can discard unread packet tails when
    # the trusted collector intentionally performs a short boundary read.
    (0x15, 0, 5, 293),
    (0x20, 0, 0, 24),
    (0x45, 0, 1, PIPE2_DENIED_FLAGS_V1[0][1]),
    (0x06, 0, 0, 0x00050001),
    (0x45, 0, 1, PIPE2_DENIED_FLAGS_V1[1][1]),
    (0x06, 0, 0, 0x00050001),
    (0x20, 0, 0, 0),
    # Mutating fcntl locks, leases, and pipe sizing are denied while
    # non-mutating fcntl commands remain available.  seccomp_data.args[1]
    # begins at byte offset 24.
    (0x15, 0, 1 + 2 * len(FCNTL_DENIED_COMMANDS_V1), 72),
    (0x20, 0, 0, 24),
    *(
        row
        for _, command in FCNTL_DENIED_COMMANDS_V1
        for row in (
            (0x15, 0, 1, command),
            (0x06, 0, 0, 0x00050001),
        )
    ),
    (0x20, 0, 0, 0),
    (0x15, 0, 3, 56),
    (0x20, 0, 0, 16),
    (0x45, 0, 1, CLONE_NAMESPACE_FLAGS_MASK_V1),
    (0x06, 0, 0, 0x00050001),
    (0x06, 0, 0, 0x7FFF0000),
)
SOCKET_DENIAL_FILTER_SHA256_V1 = canonical_sha256(
    {
        "version": "tool-system-seccomp-cbpf-v1",
        "native_syscall_exclusive_ceiling_x86_64": (
            NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
        ),
        "rows": [list(row) for row in SOCKET_DENIAL_FILTER_ROWS_V1],
    }
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXECUTION_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_ENVIRONMENT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1 = 65_536
_MAX_PATH_BYTES = 4_095
_MAX_ENVIRONMENT_ENTRIES = 128
_MAX_ARGV_ENTRIES = 1_024
_MAX_READ_ONLY_ROOTS = 16
_MAX_READ_ONLY_ROOT_PATH_BYTES = 32_768
_MAX_RETAINED_OUTPUT_PATHS = 64
_MAX_RETAINED_OUTPUT_PATH_BYTES = 65_536
MAX_PRIVATE_FILESYSTEM_BYTES_V1 = 64 * 1024 * 1024
MAX_PRIVATE_FILESYSTEM_INODES_V1 = 4_096
MAX_RAW_STREAM_BYTES_V1 = 64 * 1024 * 1024
MAX_RETAINED_STREAM_BYTES_V1 = 1 * 1024 * 1024
MAX_RUNTIME_HORIZON_NS_V1 = 300_000_000_000
MAX_LINUX_PATH_COMPONENTS_V1 = 64
READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1 = 4_096
READ_ONLY_TOTAL_SCAN_ENTRY_LIMIT_V1 = 16_384
READ_ONLY_ALLOWED_INODE_TYPES_V1 = ("directory", "regular", "symlink")
_MAX_EXPECTED_FILE_BYTES = 64 * 1024 * 1024
_MAX_INTEGER_V1 = (1 << 63) - 1
_MIN_PROCESS_COUNT = 3
_MAX_PROCESS_COUNT = 256
_MAX_GRACE_NS = 30_000_000_000
_PAGE_SIZE_BYTES = 4_096
_MIN_STRUCTURED_RESULT_BYTES = 262_144
_MAX_STRUCTURED_RESULT_BYTES = 1_048_576
_PROVIDER_CONTROL_PREFIXES = (
    "/dev",
    "/proc",
    "/run",
    "/sys",
)
_FORBIDDEN_ENVIRONMENT_NAMES = frozenset(
    {
        "BASH_ENV",
        "ENV",
        "GCONV_PATH",
        "GLIBC_TUNABLES",
        "LD_AUDIT",
        "LD_DEBUG",
        "LD_LIBRARY_PATH",
        "LD_PRELOAD",
        "PATH",
        "PERL5OPT",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONPATH",
        "RUBYOPT",
    }
)


class BackendProfileV1(str, Enum):
    LINUX_NATIVE_SUPERVISOR = LINUX_NATIVE_SUPERVISOR_V1


class ExecutableFormatV1(str, Enum):
    ELF_STATIC = "elf_static"
    ELF_DYNAMIC = "elf_dynamic"
    SCRIPT = "script"


class ExpectedFileTypeV1(str, Enum):
    ELF = "elf"
    SCRIPT = "script"
    INTERPRETER = "interpreter"
    LOADER = "loader"


class NetworkModeV1(str, Enum):
    DENY_ALL = "deny_all"


class ObservationClassV1(str, Enum):
    CAPABILITY = "capability"
    EXEC_CHAIN = "exec_chain"
    PROCESS = "process"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    STREAMS = "streams"
    TIME = "time"
    CLEANUP = "cleanup"


REQUIRED_OBSERVATION_CLASSES_V1 = tuple(ObservationClassV1)


class IsolationRequestErrorCodeV1(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"


@dataclass(frozen=True)
class IsolationRequestValidationV1:
    error_code: IsolationRequestErrorCodeV1 | None
    reasons: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.error_code is None and not self.reasons


@dataclass(frozen=True)
class RequestIdentityV1:
    task_sha256: str
    source_sha256: str
    candidate_sha256: str
    workspace_sha256: str
    configuration_sha256: str
    policy_sha256: str

    def to_record(self) -> dict[str, str]:
        return {
            "task_sha256": self.task_sha256,
            "source_sha256": self.source_sha256,
            "candidate_sha256": self.candidate_sha256,
            "workspace_sha256": self.workspace_sha256,
            "configuration_sha256": self.configuration_sha256,
            "policy_sha256": self.policy_sha256,
        }


@dataclass(frozen=True)
class ExpectedFileIdentityV1:
    source_path: str
    private_path: str
    file_type: ExpectedFileTypeV1
    device: int
    inode: int
    mode: int
    size: int
    sha256: str

    def to_record(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "private_path": self.private_path,
            "file_type": self.file_type.value,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "size": self.size,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ReadOnlyRootV1:
    source_path: str
    private_path: str
    device: int
    inode: int
    mode: int

    def to_record(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "private_path": self.private_path,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class FilesystemPolicyV1:
    read_only_inputs: tuple[ReadOnlyRootV1, ...]
    cwd_private_path: str
    scratch_private_path: str
    output_private_path: str
    scratch_byte_limit: int
    scratch_inode_limit: int
    output_byte_limit: int
    output_inode_limit: int
    retained_output_paths: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "read_only_inputs": [item.to_record() for item in self.read_only_inputs],
            "cwd_private_path": self.cwd_private_path,
            "scratch_private_path": self.scratch_private_path,
            "output_private_path": self.output_private_path,
            "scratch_byte_limit": self.scratch_byte_limit,
            "scratch_inode_limit": self.scratch_inode_limit,
            "output_byte_limit": self.output_byte_limit,
            "output_inode_limit": self.output_inode_limit,
            "retained_output_paths": list(self.retained_output_paths),
        }


@dataclass(frozen=True)
class ExecutablePolicyV1:
    format: ExecutableFormatV1
    entrypoint: ExpectedFileIdentityV1
    interpreter: ExpectedFileIdentityV1 | None
    loader: ExpectedFileIdentityV1 | None
    parsed_interpreter_path: str | None
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    descriptor_exec: bool = True
    path_lookup: bool = False

    def to_record(self) -> dict[str, object]:
        return {
            "format": self.format.value,
            "entrypoint": self.entrypoint.to_record(),
            "interpreter": (
                self.interpreter.to_record() if self.interpreter is not None else None
            ),
            "loader": self.loader.to_record() if self.loader is not None else None,
            "parsed_interpreter_path": self.parsed_interpreter_path,
            "argv": list(self.argv),
            "environment": [list(item) for item in self.environment],
            "descriptor_exec": self.descriptor_exec,
            "path_lookup": self.path_lookup,
        }


@dataclass(frozen=True)
class WorkloadIdentityV1:
    uid: int
    gid: int
    supplementary_groups: tuple[int, ...] = ()
    effective_capability_mask: int = 0
    no_new_privs: bool = True
    denied_control_operations: tuple[str, ...] = DENIED_CONTROL_OPERATIONS_V1

    def to_record(self) -> dict[str, object]:
        return {
            "uid": self.uid,
            "gid": self.gid,
            "supplementary_groups": list(self.supplementary_groups),
            "effective_capability_mask": self.effective_capability_mask,
            "no_new_privs": self.no_new_privs,
            "denied_control_operations": list(self.denied_control_operations),
        }


@dataclass(frozen=True)
class NetworkPolicyV1:
    mode: NetworkModeV1 = NetworkModeV1.DENY_ALL
    loopback_admin_up: bool = False
    inherited_network_fds: tuple[int, ...] = ()
    socket_filter_sha256: str = SOCKET_DENIAL_FILTER_SHA256_V1
    operstate_is_diagnostic: bool = True

    def to_record(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "loopback_admin_up": self.loopback_admin_up,
            "inherited_network_fds": list(self.inherited_network_fds),
            "socket_filter_sha256": self.socket_filter_sha256,
            "operstate_is_diagnostic": self.operstate_is_diagnostic,
        }


@dataclass(frozen=True)
class StreamPolicyV1:
    stdout_raw_byte_limit: int
    stderr_raw_byte_limit: int
    combined_raw_byte_limit: int
    retained_byte_limit: int
    decode_after_accounting: bool = True
    continuous_drain: bool = True

    def to_record(self) -> dict[str, object]:
        return {
            "stdout_raw_byte_limit": self.stdout_raw_byte_limit,
            "stderr_raw_byte_limit": self.stderr_raw_byte_limit,
            "combined_raw_byte_limit": self.combined_raw_byte_limit,
            "retained_byte_limit": self.retained_byte_limit,
            "decode_after_accounting": self.decode_after_accounting,
            "continuous_drain": self.continuous_drain,
        }


@dataclass(frozen=True)
class ProcessPolicyV1:
    deadline_monotonic_ns: int
    termination_grace_ns: int
    cgroup_name: str
    max_processes: int
    require_survivor_observation: bool = True

    def to_record(self) -> dict[str, object]:
        return {
            "deadline_monotonic_ns": self.deadline_monotonic_ns,
            "termination_grace_ns": self.termination_grace_ns,
            "cgroup_name": self.cgroup_name,
            "max_processes": self.max_processes,
            "require_survivor_observation": self.require_survivor_observation,
        }


@dataclass(frozen=True)
class OutputPolicyV1:
    structured_result_byte_limit: int
    file_output_byte_limit: int
    required_observation_classes: tuple[
        ObservationClassV1, ...
    ] = REQUIRED_OBSERVATION_CLASSES_V1

    def to_record(self) -> dict[str, object]:
        return {
            "structured_result_byte_limit": self.structured_result_byte_limit,
            "file_output_byte_limit": self.file_output_byte_limit,
            "required_observation_classes": [
                item.value for item in self.required_observation_classes
            ],
        }


@dataclass(frozen=True)
class IsolationRequestV1:
    schema_version: str
    execution_id: str
    identity: RequestIdentityV1
    filesystem: FilesystemPolicyV1
    executable: ExecutablePolicyV1
    workload: WorkloadIdentityV1
    network: NetworkPolicyV1
    streams: StreamPolicyV1
    process: ProcessPolicyV1
    output: OutputPolicyV1
    profile: str = ISOLATION_PROFILE_V1
    backend_profile: BackendProfileV1 = BackendProfileV1.LINUX_NATIVE_SUPERVISOR
    required_capability_set_sha256: str = REQUIRED_CAPABILITY_SET_SHA256_V1

    def canonical_record(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "execution_id": self.execution_id,
            "identity": self.identity.to_record(),
            "profile": self.profile,
            "backend_profile": self.backend_profile.value,
            "required_capability_set_sha256": self.required_capability_set_sha256,
            "filesystem": self.filesystem.to_record(),
            "executable": self.executable.to_record(),
            "workload": self.workload.to_record(),
            "network": self.network.to_record(),
            "streams": self.streams.to_record(),
            "process": self.process.to_record(),
            "output": self.output.to_record(),
        }

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self.canonical_record())

    def to_record(self) -> dict[str, object]:
        return {**self.canonical_record(), "request_sha256": self.request_sha256}


def effective_exec_argv_v1(request: IsolationRequestV1) -> tuple[str, ...]:
    """Return the exact argv that the sole v1 backend must pass to execveat."""

    if request.executable.format is ExecutableFormatV1.SCRIPT:
        interpreter = request.executable.interpreter
        if interpreter is None:
            raise ValueError("validated script request requires an interpreter")
        return (
            interpreter.private_path,
            request.executable.entrypoint.private_path,
            *request.executable.argv[1:],
        )
    return request.executable.argv


def effective_exec_environment_v1(
    request: IsolationRequestV1,
) -> tuple[tuple[str, str], ...]:
    """Return the exact sorted environment that v1 passes to execveat."""

    return request.executable.environment


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and _SHA256_RE.fullmatch(value) is not None
    )


def _utf8_size(value: object) -> int | None:
    if (
        not isinstance(value, str)
        or len(value) > MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1
    ):
        return None
    try:
        return len(value.encode("utf-8"))
    except UnicodeError:
        return None


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _valid_linux_path_components(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.split("/")
    if value.startswith("/"):
        parts = parts[1:]
    return bool(parts) and len(parts) <= MAX_LINUX_PATH_COMPONENTS_V1 and all(
        part
        and (size := _utf8_size(part)) is not None
        and size <= 255
        for part in parts
    )


def _exec_argument_environment_footprint(value: ExecutablePolicyV1) -> int | None:
    if (
        not isinstance(value.argv, tuple)
        or not 0 < len(value.argv) <= _MAX_ARGV_ENTRIES
        or not isinstance(value.environment, tuple)
        or len(value.environment) > _MAX_ENVIRONMENT_ENTRIES
    ):
        return None
    argv_sizes = tuple(_utf8_size(item) for item in value.argv)
    environment_sizes: list[tuple[int, int]] = []
    for item in value.environment:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(part, str) for part in item)
        ):
            return None
        name_size = _utf8_size(item[0])
        value_size = _utf8_size(item[1])
        if name_size is None or value_size is None:
            return None
        environment_sizes.append((name_size, value_size))
    if any(size is None for size in argv_sizes):
        return None
    return (
        sum(size + 1 for size in argv_sizes if size is not None)
        + sum(name_size + value_size + 2 for name_size, value_size in environment_sizes)
        + (len(value.argv) + len(value.environment) + 2) * 8
    )


def _valid_absolute_canonical_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= _MAX_PATH_BYTES
        and (size := _utf8_size(value)) is not None
        and size <= _MAX_PATH_BYTES
        and value.startswith("/")
        and not value.startswith("//")
        and not _contains_control_character(value)
        and value == posixpath.normpath(value)
        and _valid_linux_path_components(value)
    )


def _is_within(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _provider_control_path(path: str) -> bool:
    return isinstance(path, str) and any(
        _is_within(path, prefix) for prefix in _PROVIDER_CONTROL_PREFIXES
    )


def _safe_relative_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= _MAX_PATH_BYTES
        and (size := _utf8_size(value)) is not None
        and size <= _MAX_PATH_BYTES
        and bool(value)
        and not value.startswith("/")
        and not _contains_control_character(value)
        and value == posixpath.normpath(value)
        and value not in {".", ".."}
        and not value.startswith("../")
        and _valid_linux_path_components(value)
    )


def _positive_bounded_integer(value: object, *, maximum: int) -> bool:
    return type(value) is int and 0 < value <= maximum


def _validate_expected_file(
    value: object,
    *,
    label: str,
    expected_type: ExpectedFileTypeV1,
    reasons: list[str],
) -> None:
    if not isinstance(value, ExpectedFileIdentityV1):
        reasons.append(f"{label} must be ExpectedFileIdentityV1")
        return
    if value.file_type is not expected_type:
        reasons.append(f"{label}.file_type must be {expected_type.value}")
    for name in ("source_path", "private_path"):
        if not _valid_absolute_canonical_path(getattr(value, name)):
            reasons.append(f"{label}.{name} must be an absolute canonical path")
    if isinstance(value.source_path, str) and _provider_control_path(
        value.source_path
    ):
        reasons.append(f"{label}.source_path must not select provider controls")
    if value.source_path == "/" or value.private_path == "/":
        reasons.append(f"{label} paths must not be the filesystem root")
    if _provider_control_path(value.private_path):
        reasons.append(f"{label}.private_path must not expose provider controls")
    if (
        type(value.device) is not int
        or value.device < 0
        or value.device > _MAX_INTEGER_V1
    ):
        reasons.append(f"{label}.device must be a non-negative integer")
    if (
        type(value.inode) is not int
        or value.inode <= 0
        or value.inode > _MAX_INTEGER_V1
    ):
        reasons.append(f"{label}.inode must be a positive integer")
    if (
        type(value.mode) is not int
        or value.mode < 0
        or value.mode > 0xFFFFFFFF
        or not stat.S_ISREG(value.mode)
    ):
        reasons.append(f"{label}.mode must identify a regular file")
    elif value.mode & (stat.S_ISUID | stat.S_ISGID):
        reasons.append(f"{label}.mode must not carry set-id bits")
    elif expected_type is ExpectedFileTypeV1.SCRIPT:
        if not value.mode & stat.S_IROTH:
            reasons.append(
                f"{label}.mode must be readable by the unprivileged workload"
            )
    elif not value.mode & stat.S_IXOTH:
        reasons.append(
            f"{label}.mode must be executable by the unprivileged workload"
        )
    minimum_size = 4 if expected_type is ExpectedFileTypeV1.SCRIPT else 64
    if (
        type(value.size) is not int
        or value.size < minimum_size
        or value.size > _MAX_EXPECTED_FILE_BYTES
    ):
        reasons.append(
            f"{label}.size must be {minimum_size} bytes through the bounded "
            "64 MiB file limit"
        )
    if not _valid_sha256(value.sha256):
        reasons.append(f"{label}.sha256 must be lowercase SHA-256")


def validate_isolation_request_v1(
    request: object,
) -> IsolationRequestValidationV1:
    """Validate the exact local-OS request before any workload is released."""

    if not isinstance(request, IsolationRequestV1):
        return IsolationRequestValidationV1(
            IsolationRequestErrorCodeV1.INVALID_REQUEST,
            ("request must be IsolationRequestV1",),
        )

    invalid: list[str] = []
    identity: list[str] = []
    policy: list[str] = []
    capability: list[str] = []

    if request.schema_version != ISOLATION_REQUEST_SCHEMA_V1:
        invalid.append("schema_version must be tool-system-isolation-request-v1")
    if (
        not isinstance(request.execution_id, str)
        or len(request.execution_id) > 63
        or _EXECUTION_ID_RE.fullmatch(request.execution_id) is None
    ):
        invalid.append("execution_id must be a safe lowercase cgroup component")
    if request.profile != ISOLATION_PROFILE_V1:
        capability.append("profile must be ts_b02_core_local_os_v1")
    if request.backend_profile is not BackendProfileV1.LINUX_NATIVE_SUPERVISOR:
        capability.append("backend_profile must be linux_native_supervisor_v1")
    if request.required_capability_set_sha256 != REQUIRED_CAPABILITY_SET_SHA256_V1:
        capability.append("required capability-set digest does not match core v1")

    if not isinstance(request.identity, RequestIdentityV1):
        invalid.append("identity must be RequestIdentityV1")
    else:
        for name, value in request.identity.to_record().items():
            if not _valid_sha256(value):
                identity.append(f"identity.{name} must be lowercase SHA-256")

    filesystem = request.filesystem
    if not isinstance(filesystem, FilesystemPolicyV1):
        invalid.append("filesystem must be FilesystemPolicyV1")
    else:
        bounded_input_roots = (
            filesystem.read_only_inputs
            if isinstance(filesystem.read_only_inputs, tuple)
            and len(filesystem.read_only_inputs) <= _MAX_READ_ONLY_ROOTS
            else ()
        )
        if (
            not isinstance(filesystem.read_only_inputs, tuple)
            or not filesystem.read_only_inputs
            or len(filesystem.read_only_inputs) > _MAX_READ_ONLY_ROOTS
        ):
            policy.append("filesystem.read_only_inputs must be a non-empty tuple")
        else:
            source_paths: list[str] = []
            private_paths: list[str] = []
            for index, root in enumerate(filesystem.read_only_inputs):
                label = f"filesystem.read_only_inputs[{index}]"
                if not isinstance(root, ReadOnlyRootV1):
                    policy.append(f"{label} must be ReadOnlyRootV1")
                    continue
                if not _valid_absolute_canonical_path(root.source_path):
                    policy.append(f"{label}.source_path must be absolute and canonical")
                elif _provider_control_path(root.source_path):
                    policy.append(f"{label}.source_path must not select provider controls")
                elif root.source_path == "/":
                    policy.append(f"{label}.source_path must not expose the host root")
                if not _valid_absolute_canonical_path(root.private_path):
                    policy.append(f"{label}.private_path must be absolute and canonical")
                elif _provider_control_path(root.private_path):
                    policy.append(f"{label}.private_path must not expose provider controls")
                elif root.private_path == "/":
                    policy.append(f"{label}.private_path must not replace the private root")
                if (
                    isinstance(root.source_path, str)
                    and root.source_path in source_paths
                ) or (
                    isinstance(root.private_path, str)
                    and root.private_path in private_paths
                ):
                    policy.append(f"{label} duplicates an input-root binding")
                if _valid_absolute_canonical_path(root.source_path):
                    source_paths.append(root.source_path)
                if _valid_absolute_canonical_path(root.private_path):
                    private_paths.append(root.private_path)
                if (
                    type(root.device) is not int
                    or root.device < 0
                    or root.device > _MAX_INTEGER_V1
                ):
                    policy.append(f"{label}.device must be a non-negative integer")
                if (
                    type(root.inode) is not int
                    or root.inode <= 0
                    or root.inode > _MAX_INTEGER_V1
                ):
                    policy.append(f"{label}.inode must be a positive integer")
                if (
                    type(root.mode) is not int
                    or root.mode < 0
                    or root.mode > 0xFFFFFFFF
                    or not stat.S_ISDIR(root.mode)
                ):
                    policy.append(f"{label}.mode must identify a directory")
            for paths, label in (
                (source_paths, "source"),
                (private_paths, "private"),
            ):
                ordered = sorted(paths)
                for index, path in enumerate(ordered):
                    if any(
                        _is_within(path, other) or _is_within(other, path)
                        for other in ordered[:index]
                    ):
                        policy.append(
                            f"read-only input {label} roots must not overlap"
                        )
            root_path_bytes = sum(
                size
                for root in filesystem.read_only_inputs
                if isinstance(root, ReadOnlyRootV1)
                for size in (
                    _utf8_size(root.source_path),
                    _utf8_size(root.private_path),
                )
                if size is not None
            )
            if root_path_bytes > _MAX_READ_ONLY_ROOT_PATH_BYTES:
                policy.append("read-only input path bytes exceed the aggregate bound")
        owned_paths = (
            filesystem.cwd_private_path,
            filesystem.scratch_private_path,
            filesystem.output_private_path,
        )
        for name, value in zip(
            ("cwd_private_path", "scratch_private_path", "output_private_path"),
            owned_paths,
        ):
            if not _valid_absolute_canonical_path(value):
                policy.append(f"filesystem.{name} must be absolute and canonical")
            elif _provider_control_path(value):
                policy.append(f"filesystem.{name} must not expose provider controls")
            elif value == "/":
                policy.append(f"filesystem.{name} must not be the private root")
        if all(isinstance(item, str) for item in owned_paths) and len(
            set(owned_paths)
        ) != len(owned_paths):
            policy.append("cwd, scratch, and output private paths must be distinct")
        if all(_valid_absolute_canonical_path(item) for item in owned_paths):
            for index, path in enumerate(owned_paths):
                if any(
                    _is_within(path, other) or _is_within(other, path)
                    for other in owned_paths[:index]
                ):
                    policy.append("cwd, scratch, and output roots must be disjoint")
            scratch, output = owned_paths[1:]
            for input_root in (
                item.private_path
                for item in bounded_input_roots
                if isinstance(item, ReadOnlyRootV1)
                and _valid_absolute_canonical_path(item.private_path)
            ):
                if _is_within(scratch, input_root) or _is_within(
                    input_root, scratch
                ):
                    policy.append("scratch and read-only input roots must be disjoint")
                if _is_within(output, input_root) or _is_within(input_root, output):
                    policy.append("output and read-only input roots must be disjoint")
                cwd = owned_paths[0]
                if _is_within(cwd, input_root) or _is_within(input_root, cwd):
                    policy.append("cwd and read-only input roots must be disjoint")
        for name in ("scratch_byte_limit", "output_byte_limit"):
            if not _positive_bounded_integer(
                getattr(filesystem, name), maximum=MAX_PRIVATE_FILESYSTEM_BYTES_V1
            ):
                policy.append(
                    f"filesystem.{name} must be positive and at most 64 MiB"
                )
        for name in ("scratch_inode_limit", "output_inode_limit"):
            if not _positive_bounded_integer(
                getattr(filesystem, name), maximum=MAX_PRIVATE_FILESYSTEM_INODES_V1
            ):
                policy.append(
                    f"filesystem.{name} must be positive and at most 4096"
                )
        for name in ("scratch_byte_limit", "output_byte_limit"):
            value = getattr(filesystem, name)
            if type(value) is int and value % _PAGE_SIZE_BYTES != 0:
                policy.append(f"filesystem.{name} must be 4096-byte aligned")
        if (
            not isinstance(filesystem.retained_output_paths, tuple)
            or len(filesystem.retained_output_paths) > _MAX_RETAINED_OUTPUT_PATHS
        ):
            policy.append("filesystem.retained_output_paths must be a tuple")
        else:
            valid_retained = [
                item
                for item in filesystem.retained_output_paths
                if isinstance(item, str) and _safe_relative_path(item)
            ]
            if len(valid_retained) != len(filesystem.retained_output_paths):
                policy.append("retained output paths must be safe relative paths")
            elif len(valid_retained) != len(set(valid_retained)):
                policy.append("filesystem.retained_output_paths must be unique")
            elif sum(_utf8_size(item) or 0 for item in valid_retained) > (
                _MAX_RETAINED_OUTPUT_PATH_BYTES
            ):
                policy.append("retained output path bytes exceed the aggregate bound")
            else:
                ordered_retained = sorted(valid_retained)
                for index, path in enumerate(ordered_retained):
                    if any(
                        path.startswith(other.rstrip("/") + "/")
                        or other.startswith(path.rstrip("/") + "/")
                        for other in ordered_retained[:index]
                    ):
                        policy.append(
                            "retained output allowlist paths must not be nested"
                        )
                retained_parent_directories = {
                    "/".join(components[:depth])
                    for item in valid_retained
                    for components in (item.split("/"),)
                    for depth in range(1, len(components))
                }
                required_output_inodes = (
                    1
                    + len(retained_parent_directories)
                    + len(valid_retained)
                )
                if (
                    type(filesystem.output_inode_limit) is int
                    and filesystem.output_inode_limit < required_output_inodes
                ):
                    policy.append(
                        "filesystem.output_inode_limit cannot pre-create the "
                        "tmpfs root, retained parent directories, and retained files"
                    )

    executable = request.executable
    if not isinstance(executable, ExecutablePolicyV1):
        invalid.append("executable must be ExecutablePolicyV1")
    else:
        if not isinstance(executable.format, ExecutableFormatV1):
            invalid.append("executable.format must be ExecutableFormatV1")
        expected_entry_type = (
            ExpectedFileTypeV1.SCRIPT
            if executable.format is ExecutableFormatV1.SCRIPT
            else ExpectedFileTypeV1.ELF
        )
        _validate_expected_file(
            executable.entrypoint,
            label="executable.entrypoint",
            expected_type=expected_entry_type,
            reasons=identity,
        )
        if executable.format is ExecutableFormatV1.SCRIPT:
            _validate_expected_file(
                executable.interpreter,
                label="executable.interpreter",
                expected_type=ExpectedFileTypeV1.INTERPRETER,
                reasons=identity,
            )
        elif executable.interpreter is not None:
            policy.append("native ELF requests must not supply an interpreter")
        if executable.format is ExecutableFormatV1.ELF_STATIC:
            if executable.loader is not None or executable.parsed_interpreter_path is not None:
                policy.append("static ELF requests must not supply PT_INTERP loader data")
        else:
            _validate_expected_file(
                executable.loader,
                label="executable.loader",
                expected_type=ExpectedFileTypeV1.LOADER,
                reasons=identity,
            )
            if not _valid_absolute_canonical_path(executable.parsed_interpreter_path):
                policy.append("dynamic/script execution requires parsed interpreter path")
        if executable.descriptor_exec is not True or executable.path_lookup is not False:
            policy.append("executable must use descriptor exec with PATH lookup disabled")
        requested_files = tuple(
            item
            for item in (
                executable.entrypoint,
                executable.interpreter,
                executable.loader,
            )
            if isinstance(item, ExpectedFileIdentityV1)
            and _valid_absolute_canonical_path(item.private_path)
        )
        private_exec_paths = tuple(item.private_path for item in requested_files)
        for index, path in enumerate(private_exec_paths):
            if any(
                _is_within(path, other) or _is_within(other, path)
                for other in private_exec_paths[:index]
            ):
                policy.append(
                    "entrypoint, interpreter, and loader private paths must be disjoint"
                )
        if executable.format is ExecutableFormatV1.ELF_DYNAMIC and isinstance(
            executable.loader, ExpectedFileIdentityV1
        ):
            if executable.parsed_interpreter_path != executable.loader.private_path:
                policy.append("ELF PT_INTERP path must equal loader.private_path")
        if executable.format is ExecutableFormatV1.SCRIPT and isinstance(
            executable.interpreter, ExpectedFileIdentityV1
        ):
            if (
                executable.parsed_interpreter_path
                != executable.interpreter.private_path
            ):
                policy.append("script shebang path must equal interpreter.private_path")
        authorized_roots = (
            tuple(
                root
                for root in filesystem.read_only_inputs
                if isinstance(root, ReadOnlyRootV1)
            )
            if isinstance(filesystem, FilesystemPolicyV1)
            and isinstance(filesystem.read_only_inputs, tuple)
            else ()
        )
        owned_private_boundaries = (
            (
                filesystem.cwd_private_path,
                filesystem.scratch_private_path,
                filesystem.output_private_path,
            )
            if isinstance(filesystem, FilesystemPolicyV1)
            else ()
        )
        for item in requested_files:
            file_type_label = (
                item.file_type.value
                if isinstance(item.file_type, ExpectedFileTypeV1)
                else "executable"
            )
            source_matches = tuple(
                root
                for root in authorized_roots
                if isinstance(item.source_path, str)
                and isinstance(root.source_path, str)
                and item.source_path != root.source_path
                and _is_within(item.source_path, root.source_path)
            )
            if len(source_matches) != 1:
                policy.append(
                    f"{file_type_label} source must be inside one read-only input root"
                )
            private_boundaries = (
                *(
                    root.private_path
                    for root in authorized_roots
                    if isinstance(root.private_path, str)
                ),
                *(path for path in owned_private_boundaries if isinstance(path, str)),
            )
            if any(
                _is_within(item.private_path, boundary)
                or _is_within(boundary, item.private_path)
                for boundary in private_boundaries
            ):
                policy.append(
                    f"{file_type_label} private path overlaps a mounted boundary"
                )
        argv_shape_ok = (
            isinstance(executable.argv, tuple)
            and bool(executable.argv)
            and len(executable.argv) <= _MAX_ARGV_ENTRIES
        )
        argv_sizes = (
            tuple(_utf8_size(item) for item in executable.argv)
            if argv_shape_ok
            else ()
        )
        if (
            not argv_shape_ok
            or not all(
                isinstance(item, str) and not _contains_control_character(item)
                for item in executable.argv
            )
            or any(size is None for size in argv_sizes)
            or sum(size for size in argv_sizes if size is not None)
            > MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1
        ):
            policy.append("executable.argv must be a non-empty bounded NUL-free tuple")
        elif (
            isinstance(executable.entrypoint, ExpectedFileIdentityV1)
            and executable.argv[0] != executable.entrypoint.private_path
        ):
            policy.append("executable.argv[0] must equal entrypoint.private_path")
        environment = executable.environment
        if not isinstance(environment, tuple) or len(environment) > _MAX_ENVIRONMENT_ENTRIES:
            policy.append("executable.environment must be a bounded tuple")
        else:
            names: list[str] = []
            valid_pairs: list[tuple[str, str]] = []
            for item in environment:
                if (
                    not isinstance(item, tuple)
                    or len(item) != 2
                    or not all(isinstance(value, str) for value in item)
                ):
                    policy.append("environment entries must be immutable string pairs")
                    continue
                name, value = item
                name_size = _utf8_size(name)
                value_size = _utf8_size(value)
                if name_size is None or value_size is None:
                    policy.append("environment entries must be valid UTF-8 text")
                    continue
                valid_pairs.append((name, value))
                names.append(name)
                if (
                    _ENVIRONMENT_NAME_RE.fullmatch(name) is None
                    or _contains_control_character(value)
                ):
                    policy.append("environment entry is invalid or contains NUL")
                if name.upper() in _FORBIDDEN_ENVIRONMENT_NAMES:
                    policy.append(f"environment variable is forbidden: {name}")
            if names != sorted(names) or len(names) != len(set(names)):
                policy.append("environment names must be unique and sorted")
            if sum(
                (_utf8_size(name) or 0) + (_utf8_size(value) or 0)
                for name, value in valid_pairs
            ) > MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1:
                policy.append("environment byte length exceeds the bounded limit")
        footprint = _exec_argument_environment_footprint(executable)
        if (
            footprint is not None
            and footprint > MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1
        ):
            policy.append(
                "argv/environment UTF-8, NUL, and pointer footprint exceeds 65536 bytes"
            )

    workload = request.workload
    if not isinstance(workload, WorkloadIdentityV1):
        invalid.append("workload must be WorkloadIdentityV1")
    else:
        if not _positive_bounded_integer(workload.uid, maximum=(1 << 31) - 1):
            policy.append("workload.uid must be an unprivileged positive integer")
        if not _positive_bounded_integer(workload.gid, maximum=(1 << 31) - 1):
            policy.append("workload.gid must be an unprivileged positive integer")
        if workload.supplementary_groups != ():
            policy.append("workload supplementary groups must be empty")
        if workload.effective_capability_mask != 0:
            policy.append("workload effective capability mask must be zero")
        if workload.no_new_privs is not True:
            policy.append("workload no_new_privs must be true")
        if workload.denied_control_operations != DENIED_CONTROL_OPERATIONS_V1:
            policy.append("workload denied control operations must match core v1")

    network = request.network
    if not isinstance(network, NetworkPolicyV1):
        invalid.append("network must be NetworkPolicyV1")
    else:
        if network.mode is not NetworkModeV1.DENY_ALL:
            policy.append("network mode must be deny_all")
        if network.loopback_admin_up is not False:
            policy.append("loopback IFF_UP must be clear")
        if network.inherited_network_fds != ():
            policy.append("inherited network descriptors must be empty")
        if network.socket_filter_sha256 != SOCKET_DENIAL_FILTER_SHA256_V1:
            policy.append("socket-denial filter identity does not match core v1")
        if network.operstate_is_diagnostic is not True:
            policy.append("operstate must remain diagnostic only")

    streams = request.streams
    if not isinstance(streams, StreamPolicyV1):
        invalid.append("streams must be StreamPolicyV1")
    else:
        for name in (
            "stdout_raw_byte_limit",
            "stderr_raw_byte_limit",
            "combined_raw_byte_limit",
        ):
            if not _positive_bounded_integer(
                getattr(streams, name), maximum=MAX_RAW_STREAM_BYTES_V1
            ):
                policy.append(
                    f"streams.{name} must be positive and at most 64 MiB"
                )
        if not _positive_bounded_integer(
            streams.retained_byte_limit, maximum=MAX_RETAINED_STREAM_BYTES_V1
        ):
            policy.append(
                "streams.retained_byte_limit must be positive and at most 1 MiB"
            )
        if (
            type(streams.retained_byte_limit) is int
            and type(streams.combined_raw_byte_limit) is int
            and streams.retained_byte_limit > streams.combined_raw_byte_limit
        ):
            policy.append("retained-byte limit cannot exceed combined raw-byte limit")
        if (
            all(
                type(value) is int
                for value in (
                    streams.stdout_raw_byte_limit,
                    streams.stderr_raw_byte_limit,
                    streams.combined_raw_byte_limit,
                )
            )
            and streams.combined_raw_byte_limit
            > streams.stdout_raw_byte_limit + streams.stderr_raw_byte_limit
        ):
            policy.append(
                "combined raw-byte limit cannot exceed the two stream limits"
            )
        if streams.decode_after_accounting is not True or streams.continuous_drain is not True:
            policy.append("streams require post-accounting decode and continuous drainage")

    process = request.process
    if not isinstance(process, ProcessPolicyV1):
        invalid.append("process must be ProcessPolicyV1")
    else:
        if not _positive_bounded_integer(
            process.deadline_monotonic_ns, maximum=(1 << 63) - 1
        ):
            policy.append("process deadline must be a positive monotonic timestamp")
        if not _positive_bounded_integer(
            process.termination_grace_ns, maximum=_MAX_GRACE_NS
        ):
            policy.append("process termination grace must be finite and positive")
        if process.cgroup_name != request.execution_id:
            policy.append("process cgroup identity must equal execution_id")
        if not (
            _positive_bounded_integer(
                process.max_processes, maximum=_MAX_PROCESS_COUNT
            )
            and process.max_processes >= _MIN_PROCESS_COUNT
        ):
            policy.append(
                "process maximum must include two provider supervisors and at "
                "least one workload identity"
            )
        if process.require_survivor_observation is not True:
            policy.append("survivor observation must be required")

    output = request.output
    if not isinstance(output, OutputPolicyV1):
        invalid.append("output must be OutputPolicyV1")
    else:
        if not (
            type(output.structured_result_byte_limit) is int
            and _MIN_STRUCTURED_RESULT_BYTES
            <= output.structured_result_byte_limit
            <= _MAX_STRUCTURED_RESULT_BYTES
        ):
            policy.append(
                "output.structured_result_byte_limit must be 262144..1048576 bytes"
            )
        if not _positive_bounded_integer(
            output.file_output_byte_limit,
            maximum=MAX_PRIVATE_FILESYSTEM_BYTES_V1,
        ):
            policy.append(
                "output.file_output_byte_limit must be positive and at most 64 MiB"
            )
        elif output.file_output_byte_limit % _PAGE_SIZE_BYTES != 0:
            policy.append("output.file_output_byte_limit must be 4096-byte aligned")
        if (
            isinstance(filesystem, FilesystemPolicyV1)
            and type(output.file_output_byte_limit) is int
            and type(filesystem.output_byte_limit) is int
            and output.file_output_byte_limit != filesystem.output_byte_limit
        ):
            policy.append("file-output limit must equal the output filesystem quota")
        if output.required_observation_classes != REQUIRED_OBSERVATION_CLASSES_V1:
            policy.append("required observation classes must match core v1 exactly")

    if invalid:
        return IsolationRequestValidationV1(
            IsolationRequestErrorCodeV1.INVALID_REQUEST, tuple(invalid)
        )
    if capability:
        return IsolationRequestValidationV1(
            IsolationRequestErrorCodeV1.CAPABILITY_MISMATCH, tuple(capability)
        )
    if identity:
        return IsolationRequestValidationV1(
            IsolationRequestErrorCodeV1.IDENTITY_MISMATCH, tuple(identity)
        )
    if policy:
        return IsolationRequestValidationV1(
            IsolationRequestErrorCodeV1.POLICY_MISMATCH, tuple(policy)
        )
    return IsolationRequestValidationV1(None, ())
