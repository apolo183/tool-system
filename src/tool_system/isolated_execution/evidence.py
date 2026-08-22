from __future__ import annotations

import json
import re
import signal
import stat
from dataclasses import dataclass
from enum import Enum

from .contract import (
    FCNTL_DENIED_COMMANDS_V1,
    ISOLATION_PROFILE_V1,
    LINUX_NATIVE_SUPERVISOR_V1,
    MAX_PRIVATE_FILESYSTEM_BYTES_V1,
    MAX_PRIVATE_FILESYSTEM_INODES_V1,
    MAX_LINUX_PATH_COMPONENTS_V1,
    MAX_RAW_STREAM_BYTES_V1,
    MAX_RETAINED_STREAM_BYTES_V1,
    MAX_RUNTIME_HORIZON_NS_V1,
    NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1,
    READ_ONLY_ALLOWED_INODE_TYPES_V1,
    READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1,
    READ_ONLY_TOTAL_SCAN_ENTRY_LIMIT_V1,
    REQUIRED_CAPABILITY_SET_SHA256_V1,
    REQUIRED_OBSERVATION_CLASSES_V1,
    SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1,
    SOCKET_DENIAL_FILTER_SHA256_V1,
    ExpectedFileIdentityV1,
    ExpectedFileTypeV1,
    IsolationRequestV1,
    ObservationClassV1,
    ReadOnlyRootV1,
    canonical_json_bytes,
    canonical_sha256,
    effective_exec_argv_v1,
    effective_exec_environment_v1,
    validate_isolation_request_v1,
)


ISOLATION_EVIDENCE_SCHEMA_V1 = "tool-system-execution-evidence-v1"
STREAM_PIPE_CAPACITY_BYTES_V1 = 4_096
_PRIVATE_TMPFS_MOUNT_OPTIONS_V1 = ("nodev", "noexec", "nosuid", "rw")
_READ_ONLY_BIND_MOUNT_OPTIONS_V1 = ("nodev", "nosuid", "ro")
_STREAM_LIMIT_TRIGGERS_V1 = {
    "stdout_raw_byte_limit": "stdout",
    "stderr_raw_byte_limit": "stderr",
    "combined_raw_byte_limit": "combined",
}
_FAILURE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_EVENT_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_MAX_ERROR_COUNT = 256
_MAX_ERROR_BYTES = 16_384
_MAX_OBSERVATION_BYTES = 1_048_576
_MAX_STAGE_COUNT = 64
_MAX_OBSERVATION_COUNT = 64
_MAX_JSON_DEPTH_V1 = 64
_MAX_JSON_NODES_V1 = 16_384
_MAX_PATH_BYTES = 4_095
_MAX_INTEGER_V1 = (1 << 63) - 1
_MAX_UNSIGNED_64_V1 = (1 << 64) - 1
_MAX_PID_V1 = (1 << 31) - 1
_MAX_PROCESS_COUNT_V1 = 256
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LINUX_OPERSTATE_VALUES_V1 = frozenset(
    {"unknown", "notpresent", "down", "lowerlayerdown", "testing", "dormant", "up"}
)
_OPERSTATE_ERROR_TYPES_V1 = frozenset(
    {
        "FileNotFoundError",
        "IsADirectoryError",
        "NotADirectoryError",
        "OSError",
        "PermissionError",
        "UnicodeDecodeError",
        "UnicodeError",
    }
)
REQUIRED_MEMFD_SEALS_V1 = (
    "F_SEAL_GROW",
    "F_SEAL_SEAL",
    "F_SEAL_SHRINK",
    "F_SEAL_WRITE",
)
REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1 = (
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
REQUIRED_NETWORK_DENIAL_CLASSES_V1 = (
    "dns",
    "inherited_descriptor",
    "ipv4",
    "ipv6",
    "loopback",
    "namespace_bridge",
    "netlink",
    "packet",
)
FILESYSTEM_QUOTA_FD_TARGET_REGISTERS_X86_64_V1 = (
    (1, "rdi"),    # write
    (18, "rdi"),   # pwrite64
    (20, "rdi"),   # writev
    (40, "rdi"),   # sendfile output
    (77, "rdi"),   # ftruncate
    (275, "rdx"),  # splice output
    (285, "rdi"),  # fallocate
    (296, "rdi"),  # pwritev
    (326, "rdx"),  # copy_file_range output
    (328, "rdi"),  # pwritev2
)
FILESYSTEM_QUOTA_FD_WRITE_SYSCALLS_X86_64_V1 = tuple(
    syscall_number
    for syscall_number, _ in FILESYSTEM_QUOTA_FD_TARGET_REGISTERS_X86_64_V1
)
REQUIRED_STAGE_DEPENDENCIES_V1 = (
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
ALLOWED_PROCESS_EVENT_CLASSES_V1 = (
    "clone",
    "exec",
    "exec_denied",
    "exit",
    "exit_stop",
    "fork",
    "signal_exit",
    "vfork",
)
REQUIRED_OBSERVATION_EVENTS_V1 = (
    (
        "host.gate",
        ObservationClassV1.CAPABILITY,
        "Linux capability and namespace ABI",
    ),
    (
        "identity.seal",
        ObservationClassV1.EXEC_CHAIN,
        "openat2, fstat, SHA-256, and memfd seals",
    ),
    (
        "cgroup.claim",
        ObservationClassV1.CAPABILITY,
        "Linux capability and namespace ABI",
    ),
    (
        "namespace.setup",
        ObservationClassV1.CAPABILITY,
        "Linux capability and namespace ABI",
    ),
    (
        "filesystem.gate",
        ObservationClassV1.FILESYSTEM,
        "mount, openat2, tmpfs, and statvfs",
    ),
    (
        "network.gate",
        ObservationClassV1.NETWORK,
        "network namespace, ioctl, and seccomp",
    ),
    (
        "stream.control",
        ObservationClassV1.STREAMS,
        "nonblocking pipe byte drainage",
    ),
    ("timeout.control", ObservationClassV1.TIME, "CLOCK_MONOTONIC"),
    (
        "deadline.release_recheck",
        ObservationClassV1.TIME,
        "CLOCK_MONOTONIC",
    ),
    (
        "workload.release",
        ObservationClassV1.CAPABILITY,
        "Linux capability and namespace ABI",
    ),
    (
        "exec.ptrace",
        ObservationClassV1.EXEC_CHAIN,
        "ptrace exec-stop and procfs",
    ),
    (
        "process.contain",
        ObservationClassV1.PROCESS,
        "cgroup v2, procfs, and pidfd",
    ),
    (
        "streams.final",
        ObservationClassV1.STREAMS,
        "nonblocking pipe byte drainage",
    ),
    (
        "cleanup.final",
        ObservationClassV1.CLEANUP,
        "cgroup.events, procfs, mountinfo, and filesystem",
    ),
)
_REQUIRED_OBSERVATION_PAYLOAD_KEYS_V1 = {
    "host.gate": frozenset(
        {
            "execution_id", "os", "architecture", "effective_uid",
            "cgroup_v2", "openat2", "pidfd", "monotonic", "fallback",
            "cgroup2_gate", "mandatory_abi_control",
            "core_pipe_helper_absent",
        }
    ),
    "identity.seal": frozenset(
        {"execution_id", "entrypoint", "interpreter", "loader", "seals"}
    ),
    "cgroup.claim": frozenset(
        {
            "execution_id", "exact_paths", "identity_count", "nonce_sha256",
            "observed_pids_max",
        }
    ),
    "namespace.setup": frozenset(
        {
            "execution_id", "namespace_ids", "parent_namespace_ids",
            "all_distinct_from_parent", "host_mounts_during_live_namespace",
            "private_mount_propagation",
        }
    ),
    "filesystem.gate": frozenset(
        {
            "execution_id", "rejected_boundary_attempts", "quota_controls",
            "private_quota_observations", "read_only_mount_observations",
            "read_only_input_scans", "declared_output_control",
            "provider_view_controls", "private_root_mount_observation",
        }
    ),
    "network.gate": frozenset(
        {
            "execution_id", "network", "socket_denial_errno",
            "seccomp_filter_sha256", "seccomp_controls",
        }
    ),
    "stream.control": frozenset(
        {
            "execution_id", "mode", "observed_bytes", "monotonic_elapsed_ns",
            "populated_before_kill", "freeze_positive_control",
            "unfreeze_positive_control", "cgroup_kill_written",
            "pidfd_exit_observed", "populated_zero",
        }
    ),
    "timeout.control": frozenset(
        {
            "execution_id", "mode", "observed_bytes", "monotonic_elapsed_ns",
            "populated_before_kill", "freeze_positive_control",
            "unfreeze_positive_control", "cgroup_kill_written",
            "pidfd_exit_observed", "populated_zero",
        }
    ),
    "deadline.release_recheck": frozenset(
        {
            "execution_id", "release_recheck_monotonic_ns",
            "deadline_monotonic_ns", "termination_grace_ns", "eligible",
        }
    ),
    "workload.release": frozenset({"execution_id", "released"}),
    "exec.ptrace": frozenset(
        {
            "execution_id", "kind", "actual_entrypoint", "actual_interpreter",
            "actual_loader", "loader_map_identity_match", "uid", "gid",
            "groups", "cap_eff", "no_new_privs", "fd_set",
            "stdio_pipe_identities", "stdio_provider_match",
            "file_size_soft_limit", "file_size_hard_limit", "seccomp_mode",
            "core_soft_limit", "core_hard_limit",
            "seccomp_filters", "baseline_seccomp_filters",
            "seccomp_filter_delta", "effective_argv_sha256",
            "effective_argv_count", "effective_environment_sha256",
            "effective_environment_count", "inherited_network_fd_absent",
            "exec_pid", "namespace_exec_pid", "exec_starttime_ticks",
            "exec_cgroup", "secondary_exec_policy",
        }
    ),
    "process.contain": frozenset(
        {
            "execution_id", "initial_pid", "initial_starttime_ticks",
            "initial_pidfd_opened", "observed_pids_max", "member_observations",
            "member_count", "all_members_pidfd_bound", "event_classes",
            "secondary_exec_denials",
            "retained_outputs", "workload_exit_code",
            "workload_exit_monotonic_ns", "timeout_trigger_monotonic_ns",
            "limit_triggered", "timeout_triggered", "grace_started_monotonic_ns",
            "grace_finished_monotonic_ns", "force_kill_after_grace",
            "populated_before_kill", "cgroup_kill_written",
            "populated_after_kill", "pidfd_exit_observed", "survivor_count",
            "quota_observed_after_kill", "scratch_observed_byte_ceiling",
            "scratch_observed_inode_ceiling", "output_observed_byte_ceiling",
            "output_observed_inode_ceiling", "scratch_used_bytes",
            "scratch_used_inodes", "output_used_bytes", "output_used_inodes",
            "declared_output_allowlist", "observed_output_paths",
            "undeclared_output_blocked", "output_parent_directories_nonwritable",
            "filesystem_limit_observation",
        }
    ),
    "streams.final": frozenset(
        {
            "execution_id", "raw_bytes", "combined_raw_bytes", "retained_bytes",
            "discarded_bytes", "trigger", "observer_loss", "decoding_status",
            "pipe_capacity_bytes",
        }
    ),
    "cleanup.final": frozenset(
        {
            "execution_id", "cgroup_release", "mounts", "process_residue",
            "temporary_root_removed", "pidfd_exit_observed", "failures",
        }
    ),
}


class EvidenceStageStatusV1(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_REACHED = "NOT_REACHED"


class ExecutionOutcomeV1(str, Enum):
    NOT_EXECUTED = "not_executed"
    SUCCESS = "success"
    WORKLOAD_FAILURE = "workload_failure"
    POLICY_DENIAL = "policy_denial"
    CAPABILITY_BLOCKER = "capability_blocker"
    LIMIT = "limit"
    TIMEOUT = "timeout"
    OBSERVATION_INCOMPLETE = "observation_incomplete"
    CLEANUP_INCOMPLETE = "cleanup_incomplete"


class StreamDecodingStatusV1(str, Enum):
    UTF8_VALID = "utf8_valid"
    UTF8_REPLACED = "utf8_replaced"
    NOT_DECODED = "not_decoded"


class FilesystemLimitKindV1(str, Enum):
    SYSCALL_ERRNO = "syscall_errno"
    SIGNAL = "signal"


class FilesystemLimitScopeV1(str, Enum):
    SCRATCH = "scratch"
    OUTPUT = "output"


class EvidenceValidationErrorCodeV1(str, Enum):
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    CORRELATION_MISMATCH = "CORRELATION_MISMATCH"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"


@dataclass(frozen=True)
class EvidenceValidationV1:
    error_code: EvidenceValidationErrorCodeV1 | None
    reasons: tuple[str, ...]
    matching: bool
    complete: bool

    @property
    def ok(self) -> bool:
        return (
            self.error_code is None
            and not self.reasons
            and self.matching
            and self.complete
        )


@dataclass(frozen=True)
class CorrelationEvidenceV1:
    schema_version: str
    profile: str
    execution_id: str
    request_sha256: str
    task_sha256: str
    source_sha256: str
    candidate_sha256: str
    workspace_sha256: str
    configuration_sha256: str
    policy_sha256: str
    backend_profile: str
    backend_configuration_sha256: str
    required_capability_set_sha256: str
    os_name: str
    architecture: str
    started_monotonic_ns: int
    deadline_monotonic_ns: int
    finished_monotonic_ns: int

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "profile": self.profile,
            "execution_id": self.execution_id,
            "request_sha256": self.request_sha256,
            "task_sha256": self.task_sha256,
            "source_sha256": self.source_sha256,
            "candidate_sha256": self.candidate_sha256,
            "workspace_sha256": self.workspace_sha256,
            "configuration_sha256": self.configuration_sha256,
            "policy_sha256": self.policy_sha256,
            "backend_profile": self.backend_profile,
            "backend_configuration_sha256": self.backend_configuration_sha256,
            "required_capability_set_sha256": self.required_capability_set_sha256,
            "os_name": self.os_name,
            "architecture": self.architecture,
            "started_monotonic_ns": self.started_monotonic_ns,
            "deadline_monotonic_ns": self.deadline_monotonic_ns,
            "finished_monotonic_ns": self.finished_monotonic_ns,
        }


@dataclass(frozen=True)
class EvidenceStageV1:
    stage_id: str
    sequence: int
    status: EvidenceStageStatusV1
    failure_code: str | None = None
    blocked_by: str | None = None

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "stage_id": self.stage_id,
            "sequence": self.sequence,
            "status": self.status.value,
        }
        if self.failure_code is not None:
            record["failure_code"] = self.failure_code
        if self.blocked_by is not None:
            record["blocked_by"] = self.blocked_by
        return record


@dataclass(frozen=True)
class StageDependencyV1:
    stage_id: str
    depends_on: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {"stage_id": self.stage_id, "depends_on": list(self.depends_on)}


@dataclass(frozen=True)
class OSObservationV1:
    sequence: int
    observation_class: ObservationClassV1
    event_id: str
    os_source: str
    monotonic_ns: int
    payload_json: bytes

    @classmethod
    def from_payload(
        cls,
        *,
        sequence: int,
        observation_class: ObservationClassV1,
        event_id: str,
        os_source: str,
        monotonic_ns: int,
        payload: object,
    ) -> OSObservationV1:
        return cls(
            sequence=sequence,
            observation_class=observation_class,
            event_id=event_id,
            os_source=os_source,
            monotonic_ns=monotonic_ns,
            payload_json=canonical_json_bytes(payload),
        )

    def payload(self) -> object:
        return json.loads(self.payload_json.decode("utf-8"))

    @property
    def payload_sha256(self) -> str:
        return canonical_sha256(self.payload())

    def to_record(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "observation_class": self.observation_class.value,
            "event_id": self.event_id,
            "os_source": self.os_source,
            "monotonic_ns": self.monotonic_ns,
            "payload": self.payload(),
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class ObservedFileIdentityV1:
    path: str
    device: int
    inode: int
    mode: int
    size: int
    sha256: str

    def to_record(self) -> dict[str, object]:
        return {
            "path": self.path,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "size": self.size,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ExecChainEvidenceV1:
    requested_entrypoint: ExpectedFileIdentityV1
    selected_entrypoint: ObservedFileIdentityV1 | None
    sealed_entrypoint: ObservedFileIdentityV1 | None
    actual_entrypoint: ObservedFileIdentityV1 | None
    requested_interpreter: ExpectedFileIdentityV1 | None
    selected_interpreter: ObservedFileIdentityV1 | None
    sealed_interpreter: ObservedFileIdentityV1 | None
    actual_interpreter: ObservedFileIdentityV1 | None
    requested_loader: ExpectedFileIdentityV1 | None
    selected_loader: ObservedFileIdentityV1 | None
    sealed_loader: ObservedFileIdentityV1 | None
    actual_loader: ObservedFileIdentityV1 | None
    entrypoint_seals: tuple[str, ...]
    interpreter_seals: tuple[str, ...]
    loader_seals: tuple[str, ...]
    effective_argv_sha256: str | None
    effective_argv_count: int | None
    effective_environment_sha256: str | None
    effective_environment_count: int | None
    open_sequence: int | None
    seal_sequence: int | None
    recheck_sequence: int | None
    exec_sequence: int | None
    ptrace_exec_sequence: int | None
    mismatch_code: str | None = None
    denial_code: str | None = None

    def to_record(self) -> dict[str, object]:
        return {
            "requested_entrypoint": self.requested_entrypoint.to_record(),
            "selected_entrypoint": (
                self.selected_entrypoint.to_record()
                if self.selected_entrypoint is not None
                else None
            ),
            "sealed_entrypoint": (
                self.sealed_entrypoint.to_record()
                if self.sealed_entrypoint is not None
                else None
            ),
            "actual_entrypoint": (
                self.actual_entrypoint.to_record()
                if self.actual_entrypoint is not None
                else None
            ),
            "requested_interpreter": (
                self.requested_interpreter.to_record()
                if self.requested_interpreter is not None
                else None
            ),
            "selected_interpreter": (
                self.selected_interpreter.to_record()
                if self.selected_interpreter is not None
                else None
            ),
            "sealed_interpreter": (
                self.sealed_interpreter.to_record()
                if self.sealed_interpreter is not None
                else None
            ),
            "actual_interpreter": (
                self.actual_interpreter.to_record()
                if self.actual_interpreter is not None
                else None
            ),
            "requested_loader": (
                self.requested_loader.to_record()
                if self.requested_loader is not None
                else None
            ),
            "selected_loader": (
                self.selected_loader.to_record()
                if self.selected_loader is not None
                else None
            ),
            "sealed_loader": (
                self.sealed_loader.to_record()
                if self.sealed_loader is not None
                else None
            ),
            "actual_loader": (
                self.actual_loader.to_record()
                if self.actual_loader is not None
                else None
            ),
            "entrypoint_seals": list(self.entrypoint_seals),
            "interpreter_seals": list(self.interpreter_seals),
            "loader_seals": list(self.loader_seals),
            "effective_argv_sha256": self.effective_argv_sha256,
            "effective_argv_count": self.effective_argv_count,
            "effective_environment_sha256": self.effective_environment_sha256,
            "effective_environment_count": self.effective_environment_count,
            "open_sequence": self.open_sequence,
            "seal_sequence": self.seal_sequence,
            "recheck_sequence": self.recheck_sequence,
            "exec_sequence": self.exec_sequence,
            "ptrace_exec_sequence": self.ptrace_exec_sequence,
            "mismatch_code": self.mismatch_code,
            "denial_code": self.denial_code,
        }


@dataclass(frozen=True)
class ProcessMemberEvidenceV1:
    pid: int
    starttime_ticks: int
    cgroup_path: str
    pidfd_opened: bool
    identity_revalidated: bool
    observed_before_grace: bool
    observed_before_kill: bool
    pidfd_unreadable_before_kill: bool
    pidfd_exit_observed: bool

    def to_record(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "starttime_ticks": self.starttime_ticks,
            "cgroup_path": self.cgroup_path,
            "pidfd_opened": self.pidfd_opened,
            "identity_revalidated": self.identity_revalidated,
            "observed_before_grace": self.observed_before_grace,
            "observed_before_kill": self.observed_before_kill,
            "pidfd_unreadable_before_kill": self.pidfd_unreadable_before_kill,
            "pidfd_exit_observed": self.pidfd_exit_observed,
        }


@dataclass(frozen=True)
class SecondaryExecDenialEvidenceV1:
    """Ptrace syscall-entry denial of an exec after the sealed initial exec."""

    pid: int
    starttime_ticks: int
    cgroup_path: str
    syscall_number: int
    errno: int
    monotonic_ns: int

    def to_record(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "starttime_ticks": self.starttime_ticks,
            "cgroup_path": self.cgroup_path,
            "syscall_number": self.syscall_number,
            "errno": self.errno,
            "monotonic_ns": self.monotonic_ns,
        }


@dataclass(frozen=True)
class ProcessEvidenceV1:
    """OS-derived process-tree and teardown evidence.

    ``grace_started_monotonic_ns`` and ``grace_finished_monotonic_ns`` are
    equal for the v1 ``LIMIT`` outcome: a stream or private-filesystem limit
    triggers an immediate frozen whole-cgroup kill.  For success, workload
    failure, and timeout, their difference covers the requested termination
    grace before the forced whole-cgroup kill.
    """

    cgroup_name: str
    initial_pid: int | None
    initial_starttime_ticks: int | None
    initial_pidfd_opened: bool
    observed_uid: int | None
    observed_gid: int | None
    observed_uid_tuple: tuple[int, int, int, int] | None
    observed_gid_tuple: tuple[int, int, int, int] | None
    observed_supplementary_groups: tuple[int, ...]
    observed_effective_capability_mask: int | None
    observed_no_new_privs: bool | None
    observed_pids_max: int | None
    member_observations: tuple[ProcessMemberEvidenceV1, ...]
    member_count_observed: int
    all_members_pidfd_bound: bool
    event_classes: tuple[str, ...]
    secondary_exec_denials: tuple[SecondaryExecDenialEvidenceV1, ...]
    timeout_triggered: bool
    limit_triggered: bool
    workload_exit_monotonic_ns: int | None
    timeout_trigger_monotonic_ns: int | None
    termination_grace_ns: int
    grace_started_monotonic_ns: int | None
    grace_finished_monotonic_ns: int | None
    force_kill_after_grace: bool
    cgroup_kill_written: bool
    populated_before_kill: int | None
    populated_after_cleanup: int | None
    pidfd_exit_observed: bool
    survivor_observation_available: bool
    current_execution_survivor_count: int | None

    def to_record(self) -> dict[str, object]:
        return {
            "cgroup_name": self.cgroup_name,
            "initial_pid": self.initial_pid,
            "initial_starttime_ticks": self.initial_starttime_ticks,
            "initial_pidfd_opened": self.initial_pidfd_opened,
            "observed_uid": self.observed_uid,
            "observed_gid": self.observed_gid,
            "observed_uid_tuple": (
                list(self.observed_uid_tuple)
                if self.observed_uid_tuple is not None
                else None
            ),
            "observed_gid_tuple": (
                list(self.observed_gid_tuple)
                if self.observed_gid_tuple is not None
                else None
            ),
            "observed_supplementary_groups": list(
                self.observed_supplementary_groups
            ),
            "observed_effective_capability_mask": self.observed_effective_capability_mask,
            "observed_no_new_privs": self.observed_no_new_privs,
            "observed_pids_max": self.observed_pids_max,
            "member_observations": [
                item.to_record() for item in self.member_observations
            ],
            "member_count_observed": self.member_count_observed,
            "all_members_pidfd_bound": self.all_members_pidfd_bound,
            "event_classes": list(self.event_classes),
            "secondary_exec_denials": [
                item.to_record() for item in self.secondary_exec_denials
            ],
            "timeout_triggered": self.timeout_triggered,
            "limit_triggered": self.limit_triggered,
            "workload_exit_monotonic_ns": self.workload_exit_monotonic_ns,
            "timeout_trigger_monotonic_ns": self.timeout_trigger_monotonic_ns,
            "termination_grace_ns": self.termination_grace_ns,
            "grace_started_monotonic_ns": self.grace_started_monotonic_ns,
            "grace_finished_monotonic_ns": self.grace_finished_monotonic_ns,
            "force_kill_after_grace": self.force_kill_after_grace,
            "cgroup_kill_written": self.cgroup_kill_written,
            "populated_before_kill": self.populated_before_kill,
            "populated_after_cleanup": self.populated_after_cleanup,
            "pidfd_exit_observed": self.pidfd_exit_observed,
            "survivor_observation_available": self.survivor_observation_available,
            "current_execution_survivor_count": self.current_execution_survivor_count,
        }


@dataclass(frozen=True)
class PrivateMountQuotaEvidenceV1:
    filesystem_type: str
    mount_options: tuple[str, ...]
    byte_ceiling: int
    inode_ceiling: int
    fragment_size: int

    def to_record(self) -> dict[str, object]:
        return {
            "filesystem_type": self.filesystem_type,
            "mount_options": list(self.mount_options),
            "byte_ceiling": self.byte_ceiling,
            "inode_ceiling": self.inode_ceiling,
            "fragment_size": self.fragment_size,
        }


@dataclass(frozen=True)
class FilesystemLimitObservationV1:
    kind: FilesystemLimitKindV1
    scope: FilesystemLimitScopeV1
    target_path: str
    target_fd: int | None
    syscall_number: int | None
    errno: int | None
    signal_number: int | None
    signal_code: int | None
    fault_address: int | None
    pid: int
    starttime_ticks: int
    cgroup_path: str
    monotonic_ns: int

    def to_record(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "scope": self.scope.value,
            "target_path": self.target_path,
            "target_fd": self.target_fd,
            "syscall_number": self.syscall_number,
            "errno": self.errno,
            "signal_number": self.signal_number,
            "signal_code": self.signal_code,
            "fault_address": self.fault_address,
            "pid": self.pid,
            "starttime_ticks": self.starttime_ticks,
            "cgroup_path": self.cgroup_path,
            "monotonic_ns": self.monotonic_ns,
        }


@dataclass(frozen=True)
class ReadOnlyRootScanEvidenceV1:
    root: ReadOnlyRootV1
    observed_device: int
    observed_inode: int
    entries_scanned: int
    entry_limit: int
    allowed_inode_types: tuple[str, ...]
    fd_relative: bool
    nofollow: bool
    no_xdev: bool
    identity_revalidated: bool
    stable_during_scan: bool

    def to_record(self) -> dict[str, object]:
        return {
            "root": self.root.to_record(),
            "observed_device": self.observed_device,
            "observed_inode": self.observed_inode,
            "entries_scanned": self.entries_scanned,
            "entry_limit": self.entry_limit,
            "allowed_inode_types": list(self.allowed_inode_types),
            "fd_relative": self.fd_relative,
            "nofollow": self.nofollow,
            "no_xdev": self.no_xdev,
            "identity_revalidated": self.identity_revalidated,
            "stable_during_scan": self.stable_during_scan,
        }


@dataclass(frozen=True)
class FilesystemEvidenceV1:
    effective_read_only_inputs: tuple[ReadOnlyRootV1, ...]
    read_only_input_scans: tuple[ReadOnlyRootScanEvidenceV1, ...]
    cwd_private_path: str
    scratch_private_path: str
    output_private_path: str
    scratch_used_bytes: int
    scratch_used_inodes: int
    scratch_byte_limit: int
    scratch_inode_limit: int
    output_used_bytes: int
    output_used_inodes: int
    output_byte_limit: int
    output_inode_limit: int
    structured_result_bytes: int
    structured_result_byte_limit: int
    file_output_byte_limit: int
    quota_observed_before_release: bool
    scratch_quota_before_release: PrivateMountQuotaEvidenceV1 | None
    output_quota_before_release: PrivateMountQuotaEvidenceV1 | None
    quota_observed_after_kill: bool
    scratch_observed_byte_ceiling: int | None
    scratch_observed_inode_ceiling: int | None
    output_observed_byte_ceiling: int | None
    output_observed_inode_ceiling: int | None
    declared_output_allowlist: tuple[str, ...]
    observed_output_paths: tuple[str, ...]
    undeclared_output_blocked: bool
    output_parent_directories_nonwritable: bool
    limit_observation: FilesystemLimitObservationV1 | None
    rejected_boundary_attempts: tuple[str, ...]
    retained_outputs: tuple[ObservedFileIdentityV1, ...]
    teardown_observed: bool

    def to_record(self) -> dict[str, object]:
        return {
            "effective_read_only_inputs": [
                item.to_record() for item in self.effective_read_only_inputs
            ],
            "read_only_input_scans": [
                item.to_record() for item in self.read_only_input_scans
            ],
            "cwd_private_path": self.cwd_private_path,
            "scratch_private_path": self.scratch_private_path,
            "output_private_path": self.output_private_path,
            "scratch_used_bytes": self.scratch_used_bytes,
            "scratch_used_inodes": self.scratch_used_inodes,
            "scratch_byte_limit": self.scratch_byte_limit,
            "scratch_inode_limit": self.scratch_inode_limit,
            "output_used_bytes": self.output_used_bytes,
            "output_used_inodes": self.output_used_inodes,
            "output_byte_limit": self.output_byte_limit,
            "output_inode_limit": self.output_inode_limit,
            "structured_result_bytes": self.structured_result_bytes,
            "structured_result_byte_limit": self.structured_result_byte_limit,
            "file_output_byte_limit": self.file_output_byte_limit,
            "quota_observed_before_release": self.quota_observed_before_release,
            "scratch_quota_before_release": (
                self.scratch_quota_before_release.to_record()
                if self.scratch_quota_before_release is not None
                else None
            ),
            "output_quota_before_release": (
                self.output_quota_before_release.to_record()
                if self.output_quota_before_release is not None
                else None
            ),
            "quota_observed_after_kill": self.quota_observed_after_kill,
            "scratch_observed_byte_ceiling": self.scratch_observed_byte_ceiling,
            "scratch_observed_inode_ceiling": self.scratch_observed_inode_ceiling,
            "output_observed_byte_ceiling": self.output_observed_byte_ceiling,
            "output_observed_inode_ceiling": self.output_observed_inode_ceiling,
            "declared_output_allowlist": list(self.declared_output_allowlist),
            "observed_output_paths": list(self.observed_output_paths),
            "undeclared_output_blocked": self.undeclared_output_blocked,
            "output_parent_directories_nonwritable": (
                self.output_parent_directories_nonwritable
            ),
            "limit_observation": (
                self.limit_observation.to_record()
                if self.limit_observation is not None
                else None
            ),
            "rejected_boundary_attempts": list(self.rejected_boundary_attempts),
            "retained_outputs": [item.to_record() for item in self.retained_outputs],
            "teardown_observed": self.teardown_observed,
        }


@dataclass(frozen=True)
class NetworkEvidenceV1:
    namespace_inode: int | None
    flags_after_up: int | None
    flags_after_down: int | None
    operstate_after_up_json: bytes
    operstate_after_down_json: bytes
    live_endpoint_positive_control: bool
    live_endpoint_denial_control: bool
    inherited_network_fd_absent_at_exec: bool
    seccomp_filter_sha256: str
    socket_denial_errno: int | None
    denied_attempt_classes: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "namespace_inode": self.namespace_inode,
            "flags_after_up": self.flags_after_up,
            "flags_after_down": self.flags_after_down,
            "operstate_after_up": json.loads(
                self.operstate_after_up_json.decode("utf-8")
            ),
            "operstate_after_down": json.loads(
                self.operstate_after_down_json.decode("utf-8")
            ),
            "live_endpoint_positive_control": self.live_endpoint_positive_control,
            "live_endpoint_denial_control": self.live_endpoint_denial_control,
            "inherited_network_fd_absent_at_exec": self.inherited_network_fd_absent_at_exec,
            "seccomp_filter_sha256": self.seccomp_filter_sha256,
            "socket_denial_errno": self.socket_denial_errno,
            "denied_attempt_classes": list(self.denied_attempt_classes),
        }


@dataclass(frozen=True)
class StreamCountV1:
    emitted_bytes: int
    retained_bytes: int
    discarded_bytes: int
    limit_bytes: int
    limit_triggered: bool

    def to_record(self) -> dict[str, object]:
        return {
            "emitted_bytes": self.emitted_bytes,
            "retained_bytes": self.retained_bytes,
            "discarded_bytes": self.discarded_bytes,
            "limit_bytes": self.limit_bytes,
            "limit_triggered": self.limit_triggered,
        }


@dataclass(frozen=True)
class StreamEvidenceV1:
    """Raw byte accounting only; workload output bytes are not returned here.

    ``pipe_capacity_bytes`` is the OS read-back for each provider-owned
    workload stdout/stderr pipe.  V1 fixes both pipes to the same 4096-byte
    capacity so post-trigger raw-byte overshoot remains independently bounded;
    it is ``None`` only when that OS observation was never reached.
    """

    stdout: StreamCountV1
    stderr: StreamCountV1
    combined: StreamCountV1
    retained_byte_limit: int
    pipe_capacity_bytes: int | None
    decoding_status: StreamDecodingStatusV1
    overflow: bool
    observer_loss: bool

    def to_record(self) -> dict[str, object]:
        return {
            "stdout": self.stdout.to_record(),
            "stderr": self.stderr.to_record(),
            "combined": self.combined.to_record(),
            "retained_byte_limit": self.retained_byte_limit,
            "pipe_capacity_bytes": self.pipe_capacity_bytes,
            "decoding_status": self.decoding_status.value,
            "overflow": self.overflow,
            "observer_loss": self.observer_loss,
        }


@dataclass(frozen=True)
class CleanupEvidenceV1:
    cgroup_populated_zero: bool
    cgroup_removed: bool
    namespace_fds_closed: bool
    mounts_removed: bool
    cwd_root_fds_clear: bool
    processes_gone: bool
    pidfds_exit_observed: bool
    temporary_root_removed: bool
    residue: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.cgroup_populated_zero
            and self.cgroup_removed
            and self.namespace_fds_closed
            and self.mounts_removed
            and self.cwd_root_fds_clear
            and self.processes_gone
            and self.pidfds_exit_observed
            and self.temporary_root_removed
            and not self.residue
        )

    def to_record(self) -> dict[str, object]:
        return {
            "cgroup_populated_zero": self.cgroup_populated_zero,
            "cgroup_removed": self.cgroup_removed,
            "namespace_fds_closed": self.namespace_fds_closed,
            "mounts_removed": self.mounts_removed,
            "cwd_root_fds_clear": self.cwd_root_fds_clear,
            "processes_gone": self.processes_gone,
            "pidfds_exit_observed": self.pidfds_exit_observed,
            "temporary_root_removed": self.temporary_root_removed,
            "residue": list(self.residue),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class EvidenceCompletenessV1:
    required_observation_classes: tuple[ObservationClassV1, ...]
    observed_observation_classes: tuple[ObservationClassV1, ...]
    missing_observation_classes: tuple[ObservationClassV1, ...]
    sequence_gaps: tuple[int, ...]
    provider_errors: tuple[str, ...]
    observer_errors: tuple[str, ...]
    buffer_loss: bool
    teardown_observed: bool
    cleanup: CleanupEvidenceV1

    def to_record(self) -> dict[str, object]:
        return {
            "required_observation_classes": [
                item.value for item in self.required_observation_classes
            ],
            "observed_observation_classes": [
                item.value for item in self.observed_observation_classes
            ],
            "missing_observation_classes": [
                item.value for item in self.missing_observation_classes
            ],
            "sequence_gaps": list(self.sequence_gaps),
            "provider_errors": list(self.provider_errors),
            "observer_errors": list(self.observer_errors),
            "buffer_loss": self.buffer_loss,
            "teardown_observed": self.teardown_observed,
            "cleanup": self.cleanup.to_record(),
        }


_EVIDENCE_PRODUCER_TOKEN = object()


@dataclass(frozen=True, init=False)
class ExecutionEvidenceV1:
    """OS-derived execution facts; this type does not carry workload output."""

    correlation: CorrelationEvidenceV1
    capability_stages: tuple[EvidenceStageV1, ...]
    stage_dependencies: tuple[StageDependencyV1, ...]
    observations: tuple[OSObservationV1, ...]
    exec_chain: ExecChainEvidenceV1
    process: ProcessEvidenceV1
    filesystem: FilesystemEvidenceV1
    network: NetworkEvidenceV1
    streams: StreamEvidenceV1
    completeness: EvidenceCompletenessV1
    outcome: ExecutionOutcomeV1
    workload_released: bool
    workload_exit_code: int | None

    def __init__(
        self,
        *,
        correlation: CorrelationEvidenceV1,
        capability_stages: tuple[EvidenceStageV1, ...],
        stage_dependencies: tuple[StageDependencyV1, ...],
        observations: tuple[OSObservationV1, ...],
        exec_chain: ExecChainEvidenceV1,
        process: ProcessEvidenceV1,
        filesystem: FilesystemEvidenceV1,
        network: NetworkEvidenceV1,
        streams: StreamEvidenceV1,
        completeness: EvidenceCompletenessV1,
        outcome: ExecutionOutcomeV1,
        workload_released: bool,
        workload_exit_code: int | None,
        _producer_token: object,
    ) -> None:
        if _producer_token is not _EVIDENCE_PRODUCER_TOKEN:
            raise TypeError(
                "ExecutionEvidenceV1 may be produced only by isolated-execution"
            )
        for name, value in (
            ("correlation", correlation),
            ("capability_stages", capability_stages),
            ("stage_dependencies", stage_dependencies),
            ("observations", observations),
            ("exec_chain", exec_chain),
            ("process", process),
            ("filesystem", filesystem),
            ("network", network),
            ("streams", streams),
            ("completeness", completeness),
            ("outcome", outcome),
            ("workload_released", workload_released),
            ("workload_exit_code", workload_exit_code),
        ):
            object.__setattr__(self, name, value)

    @property
    def complete(self) -> bool:
        try:
            return not _structural_reasons(self) and not _intrinsic_completeness_reasons(
                self
            )
        except (AttributeError, TypeError, ValueError, RecursionError):
            return False

    def canonical_record(self) -> dict[str, object]:
        return {
            "correlation": self.correlation.to_record(),
            "capability_stages": [
                item.to_record() for item in self.capability_stages
            ],
            "stage_dependencies": [
                item.to_record() for item in self.stage_dependencies
            ],
            "observations": [item.to_record() for item in self.observations],
            "exec_chain": self.exec_chain.to_record(),
            "process": self.process.to_record(),
            "filesystem": self.filesystem.to_record(),
            "network": self.network.to_record(),
            "streams": self.streams.to_record(),
            "completeness": self.completeness.to_record(),
            "outcome": self.outcome.value,
            "workload_released": self.workload_released,
            "workload_exit_code": self.workload_exit_code,
            "complete": self.complete,
        }

    @property
    def record_sha256(self) -> str:
        return canonical_sha256(self.canonical_record())

    def to_record(self) -> dict[str, object]:
        return {**self.canonical_record(), "record_sha256": self.record_sha256}


def _build_execution_evidence_v1(
    *,
    correlation: CorrelationEvidenceV1,
    capability_stages: tuple[EvidenceStageV1, ...],
    stage_dependencies: tuple[StageDependencyV1, ...],
    observations: tuple[OSObservationV1, ...],
    exec_chain: ExecChainEvidenceV1,
    process: ProcessEvidenceV1,
    filesystem: FilesystemEvidenceV1,
    network: NetworkEvidenceV1,
    streams: StreamEvidenceV1,
    completeness: EvidenceCompletenessV1,
    outcome: ExecutionOutcomeV1,
    workload_released: bool,
    workload_exit_code: int | None,
) -> ExecutionEvidenceV1:
    """Internal producer entry; it is deliberately absent from ``__all__``."""

    return ExecutionEvidenceV1(
        correlation=correlation,
        capability_stages=capability_stages,
        stage_dependencies=stage_dependencies,
        observations=observations,
        exec_chain=exec_chain,
        process=process,
        filesystem=filesystem,
        network=network,
        streams=streams,
        completeness=completeness,
        outcome=outcome,
        workload_released=workload_released,
        workload_exit_code=workload_exit_code,
        _producer_token=_EVIDENCE_PRODUCER_TOKEN,
    )


def _selected_identity_matches(
    requested: ExpectedFileIdentityV1 | None,
    selected: ObservedFileIdentityV1 | None,
) -> bool:
    if requested is None or selected is None:
        return requested is None and selected is None
    return (
        selected.path == requested.source_path
        and selected.device == requested.device
        and selected.inode == requested.inode
        and selected.mode == requested.mode
        and selected.size == requested.size
        and selected.sha256 == requested.sha256
    )


def _sealed_identity_matches(
    requested: ExpectedFileIdentityV1 | None,
    sealed: ObservedFileIdentityV1 | None,
    seals: tuple[str, ...],
) -> bool:
    if requested is None or sealed is None:
        return requested is None and sealed is None and seals == ()
    return (
        sealed.path == requested.private_path
        and sealed.mode == requested.mode
        and sealed.size == requested.size
        and sealed.sha256 == requested.sha256
        and seals == REQUIRED_MEMFD_SEALS_V1
    )


def _actual_identity_matches_sealed(
    sealed: ObservedFileIdentityV1 | None,
    actual: ObservedFileIdentityV1 | None,
) -> bool:
    if sealed is None or actual is None:
        return sealed is None and actual is None
    return (
        actual.device == sealed.device
        and actual.inode == sealed.inode
        and actual.mode == sealed.mode
        and actual.size == sealed.size
        and actual.sha256 == sealed.sha256
    )


def _utf8_size(value: object) -> int | None:
    if not isinstance(value, str) or len(value) > _MAX_OBSERVATION_BYTES:
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
    return (
        bool(parts)
        and len(parts) <= MAX_LINUX_PATH_COMPONENTS_V1
        and not _contains_control_character(value)
        and all(
        part
        and (size := _utf8_size(part)) is not None
        and size <= 255
        for part in parts
        )
    )


def _valid_os_absolute_path(value: object) -> bool:
    size = _utf8_size(value)
    if (
        not isinstance(value, str)
        or size is None
        or not 0 < size <= _MAX_PATH_BYTES
        or not value.startswith("/")
        or value.startswith("//")
        or _contains_control_character(value)
    ):
        return False
    if value == "/":
        return True
    parts = value[1:].split("/")
    return (
        len(parts) <= MAX_LINUX_PATH_COMPONENTS_V1
        and all(
            part not in {"", ".", ".."}
            and (part_size := _utf8_size(part)) is not None
            and part_size <= 255
            for part in parts
        )
    )


def _namespace_inode_v1(name: str, value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(rf"{re.escape(name)}:\[([1-9][0-9]{{0,18}})\]", value)
    if match is None:
        return None
    inode = int(match.group(1))
    return inode if inode <= _MAX_INTEGER_V1 else None


def _bounded_json_shape(value: object) -> bool:
    stack: list[tuple[object, int]] = [(value, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > _MAX_JSON_NODES_V1 or depth > _MAX_JSON_DEPTH_V1:
            return False
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return True


def _contains_forbidden_absolute_claim_key(value: object) -> bool:
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, item in current.items():
                normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
                absolute_modifier = any(
                    modifier in normalized
                    for modifier in (
                        "absolute",
                        "absolutely",
                        "guaranteed",
                        "unconditional",
                    )
                )
                if (
                    "zeroeffect" in normalized
                    or "hardzero" in normalized
                    or absolute_modifier
                    and (
                        "noeffect" in normalized
                        or "nosideeffect" in normalized
                    )
                ):
                    return True
                stack.append(item)
        elif isinstance(current, list):
            stack.extend(current)
    return False


def _bounded_errors(values: object) -> bool:
    if not isinstance(values, tuple) or len(values) > _MAX_ERROR_COUNT:
        return False
    total = 0
    for item in values:
        if not isinstance(item, str) or not item or len(item) > _MAX_ERROR_BYTES:
            return False
        size = _utf8_size(item)
        if size is None:
            return False
        total += size
        if total > _MAX_ERROR_BYTES:
            return False
    return True


def _stage_graph_reasons(evidence: ExecutionEvidenceV1) -> list[str]:
    reasons: list[str] = []
    stages = evidence.capability_stages
    dependencies = evidence.stage_dependencies
    if not isinstance(stages, tuple) or not stages:
        return ["capability stages must be a non-empty tuple"]
    if len(stages) > _MAX_STAGE_COUNT:
        return ["capability stage count exceeds the v1 bound"]
    if not isinstance(dependencies, tuple):
        return ["stage dependencies must be a tuple"]
    if len(dependencies) > _MAX_STAGE_COUNT:
        return ["stage dependency count exceeds the v1 bound"]
    if not all(isinstance(item, EvidenceStageV1) for item in stages):
        return ["capability stage entry has the wrong type"]
    if not all(isinstance(item, StageDependencyV1) for item in dependencies):
        return ["stage dependency entry has the wrong type"]
    if not all(isinstance(item.stage_id, str) for item in stages):
        return ["capability stage IDs must be strings"]
    if not all(isinstance(item.stage_id, str) for item in dependencies):
        return ["stage dependency IDs must be strings"]
    expected_stage_ids = tuple(item[0] for item in REQUIRED_STAGE_DEPENDENCIES_V1)
    if tuple(item.stage_id for item in stages) != expected_stage_ids:
        reasons.append("capability stages do not match the frozen backend stage order")
    if tuple(
        (item.stage_id, item.depends_on) for item in dependencies
    ) != REQUIRED_STAGE_DEPENDENCIES_V1:
        reasons.append("stage dependencies do not match the frozen backend DAG")
    stage_by_id = {item.stage_id: item for item in stages}
    dependency_by_id = {item.stage_id: item.depends_on for item in dependencies}
    if len(stage_by_id) != len(stages):
        reasons.append("capability stage IDs must be unique")
    if len(dependency_by_id) != len(dependencies):
        reasons.append("stage dependency IDs must be unique")
    if set(stage_by_id) != set(dependency_by_id):
        reasons.append("stage/dependency key sets must match exactly")
        return reasons
    sequences = [item.sequence for item in stages]
    if not all(type(item) is int for item in sequences) or sequences != list(
        range(1, len(stages) + 1)
    ):
        reasons.append("capability stage sequence must be contiguous and ordered")
    for item in stages:
        if _EVENT_ID_RE.fullmatch(item.stage_id) is None:
            reasons.append(f"invalid stage ID: {item.stage_id!r}")
        if item.status is EvidenceStageStatusV1.PASS:
            if item.failure_code is not None or item.blocked_by is not None:
                reasons.append(f"PASS stage has failure metadata: {item.stage_id}")
        elif item.status is EvidenceStageStatusV1.FAIL:
            if (
                item.failure_code is None
                or _FAILURE_CODE_RE.fullmatch(item.failure_code) is None
                or item.blocked_by is not None
            ):
                reasons.append(f"FAIL stage shape is invalid: {item.stage_id}")
        elif item.status is EvidenceStageStatusV1.NOT_REACHED:
            if item.failure_code is not None or not item.blocked_by:
                reasons.append(f"NOT_REACHED stage shape is invalid: {item.stage_id}")
        else:
            reasons.append(f"unknown stage status: {item.stage_id}")
    for stage_id, direct in dependency_by_id.items():
        if not isinstance(direct, tuple) or not all(
            isinstance(item, str) for item in direct
        ):
            reasons.append(f"dependencies must be a string tuple: {stage_id}")
            continue
        if len(direct) != len(set(direct)):
            reasons.append(f"dependencies must be a unique tuple: {stage_id}")
            continue
        if any(item not in stage_by_id for item in direct):
            reasons.append(f"stage has an unknown dependency: {stage_id}")
            continue
        stage_sequence = stage_by_id[stage_id].sequence
        if type(stage_sequence) is not int or any(
            type(stage_by_id[item].sequence) is not int
            or stage_by_id[item].sequence >= stage_sequence
            for item in direct
        ):
            reasons.append(
                f"stage dependencies must strictly precede their consumer: {stage_id}"
            )
    if reasons:
        return reasons

    ancestors_by_id: dict[str, set[str]] = {}
    for stage in stages:
        values = set(dependency_by_id[stage.stage_id])
        for dependency in dependency_by_id[stage.stage_id]:
            values.update(ancestors_by_id[dependency])
        ancestors_by_id[stage.stage_id] = values

    for stage_id, stage in stage_by_id.items():
        direct_nonpass = [
            item
            for item in dependency_by_id[stage_id]
            if stage_by_id[item].status is not EvidenceStageStatusV1.PASS
        ]
        if stage.status in {EvidenceStageStatusV1.PASS, EvidenceStageStatusV1.FAIL}:
            if direct_nonpass:
                reasons.append(
                    f"reached stage has non-PASS prerequisite: {stage_id}"
                )
            continue
        blocker = stage.blocked_by
        if blocker not in stage_by_id or blocker not in ancestors_by_id[stage_id]:
            reasons.append(f"NOT_REACHED blocker is not an ancestor: {stage_id}")
            continue
        if not direct_nonpass:
            reasons.append(f"NOT_REACHED stage has no blocked prerequisite: {stage_id}")
            continue
        seen: set[str] = set()
        cursor = blocker
        for _ in range(len(stages)):
            if stage_by_id[cursor].status is not EvidenceStageStatusV1.NOT_REACHED:
                break
            if cursor in seen:
                reasons.append(f"NOT_REACHED blocker cycle: {stage_id}")
                break
            seen.add(cursor)
            next_cursor = stage_by_id[cursor].blocked_by
            if next_cursor not in stage_by_id:
                reasons.append(f"NOT_REACHED blocker is unknown: {stage_id}")
                break
            cursor = next_cursor
        else:
            reasons.append(f"NOT_REACHED blocker chain exceeds the stage bound: {stage_id}")
            continue
        if stage_by_id[cursor].status is not EvidenceStageStatusV1.FAIL:
            reasons.append(f"blocker chain does not terminate in FAIL: {stage_id}")
    return reasons


def _observation_reasons(evidence: ExecutionEvidenceV1) -> list[str]:
    reasons: list[str] = []
    observations = evidence.observations
    if not isinstance(observations, tuple):
        return ["observations must be an immutable tuple"]
    if len(observations) > _MAX_OBSERVATION_COUNT:
        return ["observation count exceeds the v1 bound"]
    if sum(
        len(item.payload_json)
        for item in observations
        if isinstance(item, OSObservationV1)
        and isinstance(item.payload_json, bytes)
    ) > _MAX_OBSERVATION_BYTES:
        return ["aggregate observation payload exceeds the one-MiB v1 bound"]
    sequences = [item.sequence for item in observations if isinstance(item, OSObservationV1)]
    if len(sequences) != len(observations):
        return ["observation entry has the wrong type"]
    if not all(type(item) is int for item in sequences) or sequences != list(
        range(1, len(observations) + 1)
    ):
        reasons.append("observation sequence must be contiguous and ordered")
    event_ids = tuple(item.event_id for item in observations)
    if all(isinstance(item, str) for item in event_ids) and len(event_ids) != len(
        set(event_ids)
    ):
        reasons.append("observation event IDs must be unique")
    prior_monotonic = evidence.correlation.started_monotonic_ns
    required_event_map = {
        event_id: (observation_class, os_source)
        for event_id, observation_class, os_source in REQUIRED_OBSERVATION_EVENTS_V1
    }
    for item in observations:
        if (
            not isinstance(item.event_id, str)
            or _EVENT_ID_RE.fullmatch(item.event_id) is None
        ):
            reasons.append(f"invalid observation event ID: {item.event_id!r}")
        if (
            not isinstance(item.observation_class, ObservationClassV1)
            or not isinstance(item.os_source, str)
            or not item.os_source
            or (source_size := _utf8_size(item.os_source)) is None
            or source_size > 256
        ):
            reasons.append(f"observation OS source is missing: {item.event_id}")
        expected_event = required_event_map.get(item.event_id)
        if expected_event is not None and (
            item.observation_class,
            item.os_source,
        ) != expected_event:
            reasons.append(
                "observation class/source does not match the frozen event: "
                f"{item.event_id}"
            )
        if (
            type(item.monotonic_ns) is not int
            or item.monotonic_ns < 0
            or item.monotonic_ns > _MAX_INTEGER_V1
        ):
            reasons.append(f"observation monotonic value is invalid: {item.event_id}")
            continue
        if item.monotonic_ns < prior_monotonic:
            reasons.append(f"observation monotonic order regressed: {item.event_id}")
        if item.monotonic_ns > evidence.correlation.finished_monotonic_ns:
            reasons.append(f"observation is after execution finish: {item.event_id}")
        prior_monotonic = item.monotonic_ns
        if (
            not isinstance(item.payload_json, bytes)
            or len(item.payload_json) > _MAX_OBSERVATION_BYTES
        ):
            reasons.append(f"observation payload is not bounded immutable bytes: {item.event_id}")
            continue
        try:
            payload = json.loads(item.payload_json.decode("utf-8"))
            if not _bounded_json_shape(payload):
                reasons.append(
                    f"observation payload nesting/count exceeds v1: {item.event_id}"
                )
                continue
            if _contains_forbidden_absolute_claim_key(payload):
                reasons.append(
                    f"observation contains a prohibited absolute-claim key: {item.event_id}"
                )
            if canonical_json_bytes(payload) != item.payload_json:
                reasons.append(f"observation payload is not canonical: {item.event_id}")
            if (
                not isinstance(payload, dict)
                or payload.get("execution_id") != evidence.correlation.execution_id
            ):
                reasons.append(
                    f"observation is not bound to the current execution: {item.event_id}"
                )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            RecursionError,
        ):
            reasons.append(f"observation payload is invalid JSON: {item.event_id}")
    return reasons


def _stream_reasons(streams: StreamEvidenceV1) -> list[str]:
    reasons: list[str] = []
    for label, value in (
        ("stdout", streams.stdout),
        ("stderr", streams.stderr),
        ("combined", streams.combined),
    ):
        if not isinstance(value, StreamCountV1):
            reasons.append(f"{label} stream count has the wrong type")
            continue
        counts = (
            value.emitted_bytes,
            value.retained_bytes,
            value.discarded_bytes,
            value.limit_bytes,
        )
        if any(
            type(item) is not int or item < 0 or item > _MAX_INTEGER_V1
            for item in counts
        ):
            reasons.append(f"{label} stream counts must be non-negative integers")
        if value.limit_bytes <= 0:
            reasons.append(f"{label} stream limit must be positive")
        if value.limit_bytes > MAX_RAW_STREAM_BYTES_V1:
            reasons.append(f"{label} stream limit exceeds the 64 MiB v1 bound")
        # The crossing read consumes one byte beyond the tightest remaining
        # limit.  Before the provider freezes the cgroup, that read can free a
        # complete pipe capacity for refill; the other stream can also retain
        # one full pipe when the combined limit is first crossed.
        maximum_overshoot = (
            STREAM_PIPE_CAPACITY_BYTES_V1 * 2 + 1
            if label == "combined"
            else STREAM_PIPE_CAPACITY_BYTES_V1 + 1
        )
        if (
            type(value.emitted_bytes) is int
            and type(value.limit_bytes) is int
            and value.emitted_bytes > value.limit_bytes + maximum_overshoot
        ):
            reasons.append(f"{label} stream accounting exceeds the pipe overshoot bound")
        if value.emitted_bytes != value.retained_bytes + value.discarded_bytes:
            reasons.append(f"{label} emitted bytes do not equal retained plus discarded")
        if value.retained_bytes > value.limit_bytes:
            reasons.append(f"{label} retained bytes exceed the configured limit")
        if value.limit_triggered != (value.emitted_bytes > value.limit_bytes):
            reasons.append(f"{label} limit trigger does not match raw accounting")
        if type(value.limit_triggered) is not bool:
            reasons.append(f"{label} limit trigger must be a boolean")
    if isinstance(streams.stdout, StreamCountV1) and isinstance(
        streams.stderr, StreamCountV1
    ) and isinstance(streams.combined, StreamCountV1):
        if streams.combined.emitted_bytes != (
            streams.stdout.emitted_bytes + streams.stderr.emitted_bytes
        ):
            reasons.append("combined emitted bytes do not match stdout plus stderr")
        if streams.combined.retained_bytes != (
            streams.stdout.retained_bytes + streams.stderr.retained_bytes
        ):
            reasons.append("combined retained bytes do not match stdout plus stderr")
        if streams.combined.discarded_bytes != (
            streams.stdout.discarded_bytes + streams.stderr.discarded_bytes
        ):
            reasons.append("combined discarded bytes do not match stdout plus stderr")
        if (
            type(streams.retained_byte_limit) is not int
            or streams.retained_byte_limit <= 0
            or streams.retained_byte_limit > MAX_RETAINED_STREAM_BYTES_V1
            or streams.combined.retained_bytes > streams.retained_byte_limit
        ):
            reasons.append("combined retained bytes exceed the retained-byte limit")
    if not isinstance(streams.decoding_status, StreamDecodingStatusV1):
        reasons.append("stream decoding status must use the v1 enum")
    if streams.pipe_capacity_bytes is not None and (
        type(streams.pipe_capacity_bytes) is not int
        or streams.pipe_capacity_bytes != STREAM_PIPE_CAPACITY_BYTES_V1
    ):
        reasons.append("workload stream pipe capacity must equal the core v1 value")
    if type(streams.overflow) is not bool or type(streams.observer_loss) is not bool:
        reasons.append("stream overflow and observer-loss flags must be booleans")
    return reasons


def _observed_file_reasons(
    value: object, *, label: str, optional: bool
) -> list[str]:
    if value is None and optional:
        return []
    if not isinstance(value, ObservedFileIdentityV1):
        return [f"{label} must be ObservedFileIdentityV1"]
    reasons: list[str] = []
    if (
        not isinstance(value.path, str)
        or (path_size := _utf8_size(value.path)) is None
        or path_size > _MAX_PATH_BYTES
        or not value.path.startswith("/")
        or value.path.startswith("//")
        or "\x00" in value.path
        or not _valid_linux_path_components(value.path)
    ):
        reasons.append(f"{label}.path must be an absolute NUL-free path")
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
    if (
        type(value.size) is not int
        or value.size < 0
        or value.size > MAX_PRIVATE_FILESYSTEM_BYTES_V1
    ):
        reasons.append(f"{label}.size must be a non-negative integer")
    if not isinstance(value.sha256, str) or _SHA256_RE.fullmatch(value.sha256) is None:
        reasons.append(f"{label}.sha256 must be lowercase SHA-256")
    return reasons


def _expected_file_reasons(value: object, *, label: str) -> list[str]:
    if not isinstance(value, ExpectedFileIdentityV1):
        return [f"{label} must be ExpectedFileIdentityV1"]
    reasons: list[str] = []
    if not isinstance(value.file_type, ExpectedFileTypeV1):
        reasons.append(f"{label}.file_type must use the v1 enum")
    for path_label, path in (
        ("source_path", value.source_path),
        ("private_path", value.private_path),
    ):
        size = _utf8_size(path)
        if (
            size is None
            or size > _MAX_PATH_BYTES
            or not path.startswith("/")
            or path.startswith("//")
            or "\x00" in path
            or not _valid_linux_path_components(path)
        ):
            reasons.append(f"{label}.{path_label} must be a bounded absolute path")
    observed = ObservedFileIdentityV1(
        path=value.source_path,
        device=value.device,
        inode=value.inode,
        mode=value.mode,
        size=value.size,
        sha256=value.sha256,
    )
    reasons.extend(_observed_file_reasons(observed, label=label, optional=False))
    return reasons


def _read_only_root_reasons(value: object, *, label: str) -> list[str]:
    if not isinstance(value, ReadOnlyRootV1):
        return [f"{label} must be ReadOnlyRootV1"]
    reasons: list[str] = []
    for path_label, path in (
        ("source_path", value.source_path),
        ("private_path", value.private_path),
    ):
        size = _utf8_size(path)
        if (
            size is None
            or size > _MAX_PATH_BYTES
            or not path.startswith("/")
            or path.startswith("//")
            or "\x00" in path
            or not _valid_linux_path_components(path)
        ):
            reasons.append(f"{label}.{path_label} must be a bounded absolute path")
    if (
        type(value.device) is not int
        or value.device < 0
        or value.device > _MAX_INTEGER_V1
    ):
        reasons.append(f"{label}.device is invalid")
    if (
        type(value.inode) is not int
        or value.inode <= 0
        or value.inode > _MAX_INTEGER_V1
    ):
        reasons.append(f"{label}.inode is invalid")
    if (
        type(value.mode) is not int
        or value.mode < 0
        or value.mode > 0xFFFFFFFF
        or not stat.S_ISDIR(value.mode)
    ):
        reasons.append(f"{label}.mode must identify a directory")
    return reasons


def _exec_chain_reasons(chain: ExecChainEvidenceV1) -> list[str]:
    reasons: list[str] = []
    reasons.extend(
        _expected_file_reasons(
            chain.requested_entrypoint, label="requested_entrypoint"
        )
    )
    for label, value, optional in (
        ("selected_entrypoint", chain.selected_entrypoint, True),
        ("sealed_entrypoint", chain.sealed_entrypoint, True),
        ("actual_entrypoint", chain.actual_entrypoint, True),
        ("selected_interpreter", chain.selected_interpreter, True),
        ("sealed_interpreter", chain.sealed_interpreter, True),
        ("actual_interpreter", chain.actual_interpreter, True),
        ("selected_loader", chain.selected_loader, True),
        ("sealed_loader", chain.sealed_loader, True),
        ("actual_loader", chain.actual_loader, True),
    ):
        reasons.extend(_observed_file_reasons(value, label=label, optional=optional))
    for label, value in (
        ("requested_interpreter", chain.requested_interpreter),
        ("requested_loader", chain.requested_loader),
    ):
        if value is not None:
            reasons.extend(_expected_file_reasons(value, label=label))
    for label, values in (
        ("entrypoint_seals", chain.entrypoint_seals),
        ("interpreter_seals", chain.interpreter_seals),
        ("loader_seals", chain.loader_seals),
    ):
        if (
            not isinstance(values, tuple)
            or len(values) > len(REQUIRED_MEMFD_SEALS_V1)
            or not all(isinstance(item, str) for item in values)
        ):
            reasons.append(f"{label} must be a bounded immutable string tuple")
    for label, value in (
        ("effective_argv_sha256", chain.effective_argv_sha256),
        (
            "effective_environment_sha256",
            chain.effective_environment_sha256,
        ),
    ):
        if value is not None and (
            not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None
        ):
            reasons.append(f"{label} must be lowercase SHA-256 or null")
    for label, value, maximum in (
        ("effective_argv_count", chain.effective_argv_count, 1_024),
        (
            "effective_environment_count",
            chain.effective_environment_count,
            128,
        ),
    ):
        if value is not None and (
            type(value) is not int or value < 0 or value > maximum
        ):
            reasons.append(f"{label} exceeds the bounded v1 entry count")
    sequence = (
        chain.open_sequence,
        chain.seal_sequence,
        chain.recheck_sequence,
        chain.exec_sequence,
        chain.ptrace_exec_sequence,
    )
    if not all(
        item is None or (type(item) is int and 0 < item <= _MAX_INTEGER_V1)
        for item in sequence
    ):
        reasons.append("exec-chain sequence values must be positive integers or null")
    for label, value in (
        ("mismatch_code", chain.mismatch_code),
        ("denial_code", chain.denial_code),
    ):
        if value is not None and (
            not isinstance(value, str) or _FAILURE_CODE_RE.fullmatch(value) is None
        ):
            reasons.append(f"{label} must be a stable bounded code")
    return reasons


def _process_reasons(process: ProcessEvidenceV1) -> list[str]:
    reasons: list[str] = []
    if (
        not isinstance(process.cgroup_name, str)
        or not process.cgroup_name
        or (cgroup_size := _utf8_size(process.cgroup_name)) is None
        or cgroup_size > 63
    ):
        reasons.append("process cgroup name must be a non-empty string")
    for label, value, maximum in (
        ("initial_pid", process.initial_pid, _MAX_PID_V1),
        ("initial_starttime_ticks", process.initial_starttime_ticks, _MAX_INTEGER_V1),
        ("observed_uid", process.observed_uid, _MAX_PID_V1),
        ("observed_gid", process.observed_gid, _MAX_PID_V1),
    ):
        if value is not None and (
            type(value) is not int or value <= 0 or value > maximum
        ):
            reasons.append(f"process {label} must be a positive integer or null")
    if (
        not isinstance(process.observed_supplementary_groups, tuple)
        or len(process.observed_supplementary_groups) > 64
        or not all(
            type(item) is int and 0 <= item <= _MAX_PID_V1
            for item in process.observed_supplementary_groups
        )
    ):
        reasons.append("observed supplementary groups must be an integer tuple")
    if process.observed_effective_capability_mask is not None and (
        type(process.observed_effective_capability_mask) is not int
        or process.observed_effective_capability_mask < 0
        or process.observed_effective_capability_mask > _MAX_UNSIGNED_64_V1
    ):
        reasons.append("observed capability mask must be non-negative or null")
    if process.observed_no_new_privs is not None and type(
        process.observed_no_new_privs
    ) is not bool:
        reasons.append("observed no_new_privs must be a boolean or null")
    for label, values in (
        ("observed_uid_tuple", process.observed_uid_tuple),
        ("observed_gid_tuple", process.observed_gid_tuple),
    ):
        if values is not None and (
            not isinstance(values, tuple)
            or len(values) != 4
            or not all(type(item) is int and 0 <= item <= _MAX_PID_V1 for item in values)
        ):
            reasons.append(f"process {label} must be a four-integer tuple or null")
    if process.observed_pids_max is not None and (
        type(process.observed_pids_max) is not int
        or not 0 < process.observed_pids_max <= 256
    ):
        reasons.append("observed pids.max must be 1..256 or null")
    members = process.member_observations
    if not isinstance(members, tuple) or len(members) > 256:
        reasons.append("process member observations must be a bounded tuple")
    elif not all(isinstance(item, ProcessMemberEvidenceV1) for item in members):
        reasons.append("process member observation has the wrong type")
    else:
        identities = tuple((item.pid, item.starttime_ticks) for item in members)
        if identities != tuple(sorted(identities)) or len(identities) != len(
            set(identities)
        ):
            reasons.append("process member identities must be sorted and unique")
        for index, item in enumerate(members):
            if not 0 < item.pid <= _MAX_PID_V1:
                reasons.append(f"process member[{index}] PID is invalid")
            if not 0 < item.starttime_ticks <= _MAX_INTEGER_V1:
                reasons.append(f"process member[{index}] starttime is invalid")
            path_size = _utf8_size(item.cgroup_path)
            if (
                path_size is None
                or path_size > 256
                or not item.cgroup_path.startswith("/")
                or item.cgroup_path.startswith("//")
                or "\x00" in item.cgroup_path
            ):
                reasons.append(f"process member[{index}] cgroup path is invalid")
            for field in (
                "pidfd_opened",
                "identity_revalidated",
                "observed_before_grace",
                "observed_before_kill",
                "pidfd_unreadable_before_kill",
                "pidfd_exit_observed",
            ):
                if type(getattr(item, field)) is not bool:
                    reasons.append(
                        f"process member[{index}] {field} must be a boolean"
                    )
    if (
        type(process.member_count_observed) is not int
        or process.member_count_observed < 0
        or process.member_count_observed > _MAX_PROCESS_COUNT_V1
    ):
        reasons.append("observed process member count is invalid")
    denials = process.secondary_exec_denials
    if not isinstance(denials, tuple) or len(denials) > _MAX_PROCESS_COUNT_V1:
        reasons.append("secondary exec denials must be a bounded immutable tuple")
    elif not all(isinstance(item, SecondaryExecDenialEvidenceV1) for item in denials):
        reasons.append("secondary exec denial has the wrong type")
    else:
        ordering = tuple(
            (
                item.monotonic_ns,
                item.pid,
                item.starttime_ticks,
                item.syscall_number,
            )
            for item in denials
        )
        if ordering != tuple(sorted(ordering)):
            reasons.append("secondary exec denials must be canonically ordered")
        for index, item in enumerate(denials):
            if type(item.pid) is not int or not 0 < item.pid <= _MAX_PID_V1:
                reasons.append(f"secondary exec denial[{index}] PID is invalid")
            if (
                type(item.starttime_ticks) is not int
                or not 0 < item.starttime_ticks <= _MAX_INTEGER_V1
            ):
                reasons.append(
                    f"secondary exec denial[{index}] starttime is invalid"
                )
            path_size = _utf8_size(item.cgroup_path)
            if (
                path_size is None
                or path_size > 256
                or not item.cgroup_path.startswith("/")
                or item.cgroup_path.startswith("//")
                or "\x00" in item.cgroup_path
            ):
                reasons.append(
                    f"secondary exec denial[{index}] cgroup path is invalid"
                )
            if type(item.syscall_number) is not int or item.syscall_number not in {
                59,
                322,
            }:
                reasons.append(
                    f"secondary exec denial[{index}] syscall is not execve/execveat"
                )
            if type(item.errno) is not int or item.errno != 1:
                reasons.append(
                    f"secondary exec denial[{index}] errno must be EPERM"
                )
            if (
                type(item.monotonic_ns) is not int
                or not 0 < item.monotonic_ns <= _MAX_INTEGER_V1
            ):
                reasons.append(
                    f"secondary exec denial[{index}] monotonic time is invalid"
                )
    event_classes = process.event_classes
    if not isinstance(event_classes, tuple):
        reasons.append("process event classes must be a bounded unique string tuple")
    elif (
        len(event_classes) > len(ALLOWED_PROCESS_EVENT_CLASSES_V1)
        or not all(isinstance(item, str) for item in event_classes)
        or tuple(sorted(event_classes)) != event_classes
        or len(event_classes) != len(set(event_classes))
        or any(item not in ALLOWED_PROCESS_EVENT_CLASSES_V1 for item in event_classes)
    ):
        reasons.append("process event classes must be the sorted v1 event subset")
    elif ("exec_denied" in event_classes) != bool(denials):
        reasons.append(
            "exec_denied event class and secondary exec denials must agree"
        )
    for label in (
        "initial_pidfd_opened",
        "all_members_pidfd_bound",
        "timeout_triggered",
        "limit_triggered",
        "force_kill_after_grace",
        "cgroup_kill_written",
        "pidfd_exit_observed",
        "survivor_observation_available",
    ):
        if type(getattr(process, label)) is not bool:
            reasons.append(f"process {label} must be a boolean")
    for label in (
        "workload_exit_monotonic_ns",
        "timeout_trigger_monotonic_ns",
    ):
        value = getattr(process, label)
        if value is not None and (
            type(value) is not int or not 0 < value <= _MAX_INTEGER_V1
        ):
            reasons.append(f"process {label} must be positive or null")
    if (
        process.workload_exit_monotonic_ns is not None
        and process.timeout_trigger_monotonic_ns is not None
    ):
        reasons.append("workload-exit and timeout trigger times are mutually exclusive")
    if (
        type(process.termination_grace_ns) is not int
        or process.termination_grace_ns <= 0
        or process.termination_grace_ns > _MAX_INTEGER_V1
    ):
        reasons.append("observed termination grace is invalid")
    grace_values = (
        process.grace_started_monotonic_ns,
        process.grace_finished_monotonic_ns,
    )
    if not all(
        item is None or (type(item) is int and 0 < item <= _MAX_INTEGER_V1)
        for item in grace_values
    ):
        reasons.append("grace monotonic observations must be positive or null")
    elif (grace_values[0] is None) != (grace_values[1] is None):
        reasons.append("grace monotonic observations must be present together")
    elif (
        grace_values[0] is not None
        and grace_values[1] is not None
        and grace_values[1] < grace_values[0]
    ):
        reasons.append("grace monotonic interval is reversed")
    if process.cgroup_kill_written != process.force_kill_after_grace:
        reasons.append("cgroup.kill and force-after-grace observations must agree")
    for label, value in (
        ("populated_before_kill", process.populated_before_kill),
        ("populated_after_cleanup", process.populated_after_cleanup),
    ):
        if value is not None and (type(value) is not int or value not in {0, 1}):
            reasons.append(f"process {label} must be zero, one, or null")
    survivor_count = process.current_execution_survivor_count
    if survivor_count is not None and (
        type(survivor_count) is not int
        or survivor_count < 0
        or survivor_count > _MAX_PROCESS_COUNT_V1
    ):
        reasons.append("current-execution survivor count must be non-negative or null")
    return reasons


def _filesystem_reasons(filesystem: FilesystemEvidenceV1) -> list[str]:
    reasons: list[str] = []
    scans = filesystem.read_only_input_scans
    if (
        not isinstance(scans, tuple)
        or len(scans) != len(filesystem.effective_read_only_inputs)
        or len(scans) > 16
        or not all(isinstance(item, ReadOnlyRootScanEvidenceV1) for item in scans)
    ):
        reasons.append("read-only input scan evidence has the wrong bounded shape")
    else:
        total_entries = 0
        for expected_root, scan in zip(filesystem.effective_read_only_inputs, scans):
            total_entries += scan.entries_scanned if type(scan.entries_scanned) is int else 0
            if (
                scan.root != expected_root
                or type(scan.observed_device) is not int
                or not 0 <= scan.observed_device <= _MAX_INTEGER_V1
                or scan.observed_device != expected_root.device
                or type(scan.observed_inode) is not int
                or not 0 < scan.observed_inode <= _MAX_INTEGER_V1
                or scan.observed_inode != expected_root.inode
                or type(scan.entries_scanned) is not int
                or not 0 <= scan.entries_scanned <= READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1
                or scan.entry_limit != READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1
                or scan.allowed_inode_types != READ_ONLY_ALLOWED_INODE_TYPES_V1
                or scan.fd_relative is not True
                or scan.nofollow is not True
                or scan.no_xdev is not True
                or scan.identity_revalidated is not True
                or scan.stable_during_scan is not True
            ):
                reasons.append("read-only input scan evidence is invalid or mismatched")
        if total_entries > READ_ONLY_TOTAL_SCAN_ENTRY_LIMIT_V1:
            reasons.append("read-only input scan total exceeds the core v1 bound")
    if (
        not isinstance(filesystem.effective_read_only_inputs, tuple)
        or len(filesystem.effective_read_only_inputs) > 16
    ):
        reasons.append("effective read-only roots must be ReadOnlyRootV1 tuples")
    else:
        for index, root in enumerate(filesystem.effective_read_only_inputs):
            reasons.extend(
                _read_only_root_reasons(
                    root, label=f"effective_read_only_inputs[{index}]"
                )
            )
    for label in ("cwd_private_path", "scratch_private_path", "output_private_path"):
        value = getattr(filesystem, label)
        if (
            not isinstance(value, str)
            or (path_size := _utf8_size(value)) is None
            or path_size > _MAX_PATH_BYTES
                or not value.startswith("/")
                or value.startswith("//")
                or "\x00" in value
                or not _valid_linux_path_components(value)
        ):
            reasons.append(f"filesystem {label} must be an absolute NUL-free path")
    if (
        not isinstance(filesystem.rejected_boundary_attempts, tuple)
        or len(filesystem.rejected_boundary_attempts)
        > len(REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1)
        or not all(
            isinstance(item, str)
            and item
            and (size := _utf8_size(item)) is not None
            and size <= 128
            for item in filesystem.rejected_boundary_attempts
        )
    ):
        reasons.append("rejected boundary attempts must be bounded immutable strings")
    if (
        not isinstance(filesystem.retained_outputs, tuple)
        or len(filesystem.retained_outputs) > 64
    ):
        reasons.append("retained outputs must be an immutable tuple")
    else:
        for index, value in enumerate(filesystem.retained_outputs):
            reasons.extend(
                _observed_file_reasons(
                    value, label=f"retained_outputs[{index}]", optional=False
                )
            )
    if type(filesystem.teardown_observed) is not bool:
        reasons.append("filesystem teardown observation must be a boolean")
    for label in ("quota_observed_before_release", "quota_observed_after_kill"):
        if type(getattr(filesystem, label)) is not bool:
            reasons.append(f"filesystem {label} must be a boolean")
    for label in ("scratch_quota_before_release", "output_quota_before_release"):
        quota = getattr(filesystem, label)
        if quota is not None and not isinstance(quota, PrivateMountQuotaEvidenceV1):
            reasons.append(f"filesystem {label} has the wrong type")
            continue
        if quota is None:
            continue
        if quota.filesystem_type != "tmpfs":
            reasons.append(f"filesystem {label} must identify tmpfs")
        if quota.mount_options != _PRIVATE_TMPFS_MOUNT_OPTIONS_V1:
            reasons.append(
                f"filesystem {label} mount options must equal the exact v1 projection"
            )
        for field, maximum in (
            ("byte_ceiling", MAX_PRIVATE_FILESYSTEM_BYTES_V1),
            ("inode_ceiling", MAX_PRIVATE_FILESYSTEM_INODES_V1),
            ("fragment_size", 65_536),
        ):
            value = getattr(quota, field)
            if type(value) is not int or not 0 < value <= maximum:
                reasons.append(f"filesystem {label} {field} is invalid")
    for label, maximum in (
        ("scratch_observed_byte_ceiling", MAX_PRIVATE_FILESYSTEM_BYTES_V1),
        ("scratch_observed_inode_ceiling", MAX_PRIVATE_FILESYSTEM_INODES_V1),
        ("output_observed_byte_ceiling", MAX_PRIVATE_FILESYSTEM_BYTES_V1),
        ("output_observed_inode_ceiling", MAX_PRIVATE_FILESYSTEM_INODES_V1),
    ):
        value = getattr(filesystem, label)
        if value is not None and (
            type(value) is not int or not 0 < value <= maximum
        ):
            reasons.append(f"filesystem {label} is invalid")
    for label, paths in (
        ("declared_output_allowlist", filesystem.declared_output_allowlist),
        ("observed_output_paths", filesystem.observed_output_paths),
    ):
        if (
            not isinstance(paths, tuple)
            or len(paths) > 64
            or not all(
                isinstance(item, str)
                and item
                and not item.startswith("/")
                and "\x00" not in item
                and all(part not in {"", ".", ".."} for part in item.split("/"))
                and _valid_linux_path_components(item)
                and (size := _utf8_size(item)) is not None
                and size <= _MAX_PATH_BYTES
                for item in paths
            )
        ):
            reasons.append(f"filesystem {label} is not a bounded relative-path tuple")
        elif len(paths) != len(set(paths)):
            reasons.append(f"filesystem {label} must be unique")
    if isinstance(filesystem.observed_output_paths, tuple) and tuple(
        sorted(filesystem.observed_output_paths)
    ) != filesystem.observed_output_paths:
        reasons.append("filesystem observed output paths must be sorted")
    for label in (
        "undeclared_output_blocked",
        "output_parent_directories_nonwritable",
    ):
        if type(getattr(filesystem, label)) is not bool:
            reasons.append(f"filesystem {label} must be a boolean")
    limit_observation = filesystem.limit_observation
    if limit_observation is not None:
        if not isinstance(limit_observation, FilesystemLimitObservationV1):
            reasons.append("filesystem limit observation has the wrong type")
        else:
            if not isinstance(limit_observation.kind, FilesystemLimitKindV1):
                reasons.append("filesystem limit kind must use the v1 enum")
            if not isinstance(limit_observation.scope, FilesystemLimitScopeV1):
                reasons.append("filesystem limit scope must use the v1 enum")
            if (
                type(limit_observation.pid) is not int
                or not 0 < limit_observation.pid <= _MAX_PID_V1
                or type(limit_observation.starttime_ticks) is not int
                or not 0 < limit_observation.starttime_ticks <= _MAX_INTEGER_V1
                or type(limit_observation.monotonic_ns) is not int
                or not 0 < limit_observation.monotonic_ns <= _MAX_INTEGER_V1
            ):
                reasons.append("filesystem limit process/time identity is invalid")
            cgroup_size = _utf8_size(limit_observation.cgroup_path)
            if (
                cgroup_size is None
                or cgroup_size > 256
                or not limit_observation.cgroup_path.startswith("/")
                or limit_observation.cgroup_path.startswith("//")
                or not _valid_linux_path_components(limit_observation.cgroup_path)
            ):
                reasons.append("filesystem limit cgroup path is invalid")
            target_size = _utf8_size(limit_observation.target_path)
            target_root = (
                filesystem.scratch_private_path
                if limit_observation.scope is FilesystemLimitScopeV1.SCRATCH
                else filesystem.output_private_path
                if limit_observation.scope is FilesystemLimitScopeV1.OUTPUT
                else None
            )
            if (
                target_size is None
                or target_size > _MAX_PATH_BYTES
                or not limit_observation.target_path.startswith("/")
                or limit_observation.target_path.startswith("//")
                or not _valid_linux_path_components(limit_observation.target_path)
                or target_root is None
                or not (
                    limit_observation.target_path == target_root
                    or limit_observation.target_path.startswith(
                        target_root.rstrip("/") + "/"
                    )
                )
            ):
                reasons.append("filesystem limit target is outside its private scope")
            if limit_observation.kind is FilesystemLimitKindV1.SYSCALL_ERRNO:
                if (
                    type(limit_observation.syscall_number) is not int
                    or limit_observation.syscall_number
                    not in FILESYSTEM_QUOTA_FD_WRITE_SYSCALLS_X86_64_V1
                    or limit_observation.errno not in {27, 28, 122}
                    or limit_observation.signal_number is not None
                    or type(limit_observation.target_fd) is not int
                    or not 0 <= limit_observation.target_fd <= 1_048_575
                    or limit_observation.signal_code is not None
                    or limit_observation.fault_address is not None
                ):
                    reasons.append("filesystem syscall-limit observation is invalid")
            elif limit_observation.kind is FilesystemLimitKindV1.SIGNAL:
                reasons.append(
                    "filesystem signal-limit observations are not attributable in v1"
                )
    return reasons


def _network_reasons(network: NetworkEvidenceV1) -> list[str]:
    reasons: list[str] = []
    for label, payload_json in (
        ("operstate_after_up", network.operstate_after_up_json),
        ("operstate_after_down", network.operstate_after_down_json),
    ):
        try:
            diagnostic = json.loads(payload_json.decode("utf-8"))
        except (
            AttributeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RecursionError,
        ):
            diagnostic = None
        if not (
            isinstance(diagnostic, dict)
            and (
                set(diagnostic) == {"value"}
                and diagnostic.get("value") in _LINUX_OPERSTATE_VALUES_V1
                or set(diagnostic) == {"unavailable", "error_type"}
                and diagnostic.get("unavailable") is True
                and diagnostic.get("error_type") in _OPERSTATE_ERROR_TYPES_V1
            )
        ):
            reasons.append(f"network {label} diagnostic has an invalid v1 schema")
    if network.namespace_inode is not None and (
        type(network.namespace_inode) is not int
        or network.namespace_inode <= 0
        or network.namespace_inode > _MAX_INTEGER_V1
    ):
        reasons.append("network namespace inode must be positive or null")
    for label, value in (
        ("flags_after_up", network.flags_after_up),
        ("flags_after_down", network.flags_after_down),
    ):
        if value is not None and (
            type(value) is not int or value < 0 or value > 0xFFFFFFFF
        ):
            reasons.append(f"network {label} is invalid")
    for label in (
        "live_endpoint_positive_control",
        "live_endpoint_denial_control",
        "inherited_network_fd_absent_at_exec",
    ):
        if type(getattr(network, label)) is not bool:
            reasons.append(f"network {label} must be a boolean")
    if (
        not isinstance(network.seccomp_filter_sha256, str)
        or _SHA256_RE.fullmatch(network.seccomp_filter_sha256) is None
    ):
        reasons.append("network seccomp filter identity must be SHA-256")
    if network.socket_denial_errno is not None and (
        type(network.socket_denial_errno) is not int
        or network.socket_denial_errno <= 0
        or network.socket_denial_errno > 4_095
    ):
        reasons.append("network socket-denial errno must be positive or null")
    if (
        not isinstance(network.denied_attempt_classes, tuple)
        or not all(
            isinstance(item, str)
            and item
            and (size := _utf8_size(item)) is not None
            and size <= 128
            for item in network.denied_attempt_classes
        )
    ):
        reasons.append("network denial classes must be a bounded unique string tuple")
    elif (
        len(network.denied_attempt_classes) > 64
        or len(network.denied_attempt_classes)
        != len(set(network.denied_attempt_classes))
    ):
        reasons.append("network denial classes must be a bounded unique string tuple")
    return reasons


def _cleanup_reasons(cleanup: CleanupEvidenceV1) -> list[str]:
    reasons: list[str] = []
    for label in (
        "cgroup_populated_zero",
        "cgroup_removed",
        "namespace_fds_closed",
        "mounts_removed",
        "cwd_root_fds_clear",
        "processes_gone",
        "pidfds_exit_observed",
        "temporary_root_removed",
    ):
        if type(getattr(cleanup, label)) is not bool:
            reasons.append(f"cleanup {label} must be a boolean")
    if (
        not _bounded_errors(cleanup.residue)
    ):
        reasons.append("cleanup residue must be a bounded immutable string tuple")
    return reasons


def _structural_reasons(evidence: ExecutionEvidenceV1) -> list[str]:
    group_types = (
        ("correlation", evidence.correlation, CorrelationEvidenceV1),
        ("exec_chain", evidence.exec_chain, ExecChainEvidenceV1),
        ("process", evidence.process, ProcessEvidenceV1),
        ("filesystem", evidence.filesystem, FilesystemEvidenceV1),
        ("network", evidence.network, NetworkEvidenceV1),
        ("streams", evidence.streams, StreamEvidenceV1),
        ("completeness", evidence.completeness, EvidenceCompletenessV1),
    )
    wrong_groups = [
        f"{label} has the wrong type"
        for label, value, expected_type in group_types
        if not isinstance(value, expected_type)
    ]
    if wrong_groups:
        return wrong_groups
    reasons = _stage_graph_reasons(evidence)
    reasons.extend(_observation_reasons(evidence))
    if not isinstance(evidence.observations, tuple) or not all(
        isinstance(item, OSObservationV1) for item in evidence.observations
    ):
        return reasons
    reasons.extend(_stream_reasons(evidence.streams))
    reasons.extend(_exec_chain_reasons(evidence.exec_chain))
    reasons.extend(_process_reasons(evidence.process))
    reasons.extend(_filesystem_reasons(evidence.filesystem))
    reasons.extend(_network_reasons(evidence.network))
    correlation = evidence.correlation
    if not isinstance(evidence.outcome, ExecutionOutcomeV1):
        reasons.append("execution outcome must use the v1 enum")
    if type(evidence.workload_released) is not bool:
        reasons.append("workload_released must be a boolean")
    if evidence.workload_exit_code is not None and type(
        evidence.workload_exit_code
    ) is not int:
        reasons.append("workload_exit_code must be an integer or null")
    elif evidence.workload_exit_code is not None and not (
        0 <= evidence.workload_exit_code <= 255
    ):
        reasons.append("workload_exit_code is outside the OS wait-status range")
    if isinstance(evidence.process, ProcessEvidenceV1) and (
        (evidence.workload_exit_code is None)
        != (evidence.process.workload_exit_monotonic_ns is None)
    ):
        reasons.append(
            "workload exit code and OS-observed exit timestamp must be present together"
        )
    if evidence.workload_released is False and evidence.workload_exit_code is not None:
        reasons.append("an unreleased workload must not carry an exit code")
    if correlation.schema_version != ISOLATION_EVIDENCE_SCHEMA_V1:
        reasons.append("evidence schema version is invalid")
    if correlation.profile != ISOLATION_PROFILE_V1:
        reasons.append("evidence isolation profile is invalid")
    if correlation.backend_profile != LINUX_NATIVE_SUPERVISOR_V1:
        reasons.append("evidence backend profile is invalid")
    if correlation.required_capability_set_sha256 != REQUIRED_CAPABILITY_SET_SHA256_V1:
        reasons.append("evidence capability-set digest is invalid")
    for label in (
        "request_sha256",
        "task_sha256",
        "source_sha256",
        "candidate_sha256",
        "workspace_sha256",
        "configuration_sha256",
        "policy_sha256",
        "backend_configuration_sha256",
        "required_capability_set_sha256",
    ):
        value = getattr(correlation, label)
        if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
            reasons.append(f"correlation {label} must be lowercase SHA-256")
    if (
        not isinstance(correlation.execution_id, str)
        or not correlation.execution_id
        or (execution_id_size := _utf8_size(correlation.execution_id)) is None
        or execution_id_size > 63
    ):
        reasons.append("correlation execution ID must be a non-empty string")
    if correlation.os_name != "Linux" or correlation.architecture != "x86_64":
        reasons.append("evidence host must be Linux/x86_64")
    if (
        type(correlation.started_monotonic_ns) is not int
        or type(correlation.deadline_monotonic_ns) is not int
        or type(correlation.finished_monotonic_ns) is not int
        or correlation.started_monotonic_ns <= 0
        or correlation.started_monotonic_ns > _MAX_INTEGER_V1
        or correlation.deadline_monotonic_ns > _MAX_INTEGER_V1
        or correlation.finished_monotonic_ns > _MAX_INTEGER_V1
        or correlation.deadline_monotonic_ns < correlation.started_monotonic_ns
        or correlation.finished_monotonic_ns < correlation.started_monotonic_ns
    ):
        reasons.append("evidence monotonic interval is invalid")
    completeness = evidence.completeness
    if not isinstance(completeness.cleanup, CleanupEvidenceV1):
        reasons.append("cleanup evidence has the wrong type")
        return reasons
    reasons.extend(_cleanup_reasons(completeness.cleanup))
    if completeness.required_observation_classes != REQUIRED_OBSERVATION_CLASSES_V1:
        reasons.append("evidence required observation bitmap is invalid")
    for label in (
        "required_observation_classes",
        "observed_observation_classes",
        "missing_observation_classes",
    ):
        values = getattr(completeness, label)
        if not isinstance(values, tuple) or not all(
            isinstance(item, ObservationClassV1) for item in values
        ):
            reasons.append(f"completeness {label} must be an observation-class tuple")
    if (
        type(completeness.buffer_loss) is not bool
        or type(completeness.teardown_observed) is not bool
    ):
        reasons.append("completeness loss and teardown flags must be booleans")
    derived_observed = tuple(
        item
        for item in REQUIRED_OBSERVATION_CLASSES_V1
        if any(obs.observation_class is item for obs in evidence.observations)
    )
    derived_missing = tuple(
        item for item in REQUIRED_OBSERVATION_CLASSES_V1 if item not in derived_observed
    )
    if completeness.observed_observation_classes != derived_observed:
        reasons.append("observed observation bitmap is not derived from observations")
    if completeness.missing_observation_classes != derived_missing:
        reasons.append("missing observation bitmap is not derived from observations")
    if not _bounded_errors(completeness.provider_errors):
        reasons.append("provider errors are not bounded immutable strings")
    if not _bounded_errors(completeness.observer_errors):
        reasons.append("observer errors are not bounded immutable strings")
    gaps = completeness.sequence_gaps
    if (
        not isinstance(gaps, tuple)
        or len(gaps) > _MAX_OBSERVATION_COUNT
        or not all(
            type(item) is int and 0 < item <= _MAX_OBSERVATION_COUNT
            for item in gaps
        )
    ):
        reasons.append("sequence gaps must be a tuple of positive integers")
    elif tuple(sorted(gaps)) != gaps or len(gaps) != len(set(gaps)):
        reasons.append("sequence gaps must be sorted and unique")
    if evidence.process.cgroup_name != correlation.execution_id:
        reasons.append("process cgroup does not match execution ID")
    if (
        type(evidence.process.member_count_observed) is not int
        or evidence.process.member_count_observed < 0
    ):
        reasons.append("observed process member count is invalid")
    if (
        type(evidence.process.termination_grace_ns) is not int
        or evidence.process.termination_grace_ns <= 0
    ):
        reasons.append("observed termination grace is invalid")
    if evidence.process.populated_after_cleanup not in {0, None}:
        reasons.append("post-cleanup cgroup populated value is invalid")
    if not isinstance(evidence.filesystem.effective_read_only_inputs, tuple):
        reasons.append("effective read-only roots must be an immutable tuple")
    for used_name, used, limit, maximum in (
        (
            "scratch bytes",
            evidence.filesystem.scratch_used_bytes,
            evidence.filesystem.scratch_byte_limit,
            MAX_PRIVATE_FILESYSTEM_BYTES_V1,
        ),
        (
            "scratch inodes",
            evidence.filesystem.scratch_used_inodes,
            evidence.filesystem.scratch_inode_limit,
            MAX_PRIVATE_FILESYSTEM_INODES_V1,
        ),
        (
            "output bytes",
            evidence.filesystem.output_used_bytes,
            evidence.filesystem.output_byte_limit,
            MAX_PRIVATE_FILESYSTEM_BYTES_V1,
        ),
        (
            "output inodes",
            evidence.filesystem.output_used_inodes,
            evidence.filesystem.output_inode_limit,
            MAX_PRIVATE_FILESYSTEM_INODES_V1,
        ),
        (
            "structured result bytes",
            evidence.filesystem.structured_result_bytes,
            evidence.filesystem.structured_result_byte_limit,
            MAX_RETAINED_STREAM_BYTES_V1,
        ),
        (
            "file output bytes",
            evidence.filesystem.output_used_bytes,
            evidence.filesystem.file_output_byte_limit,
            MAX_PRIVATE_FILESYSTEM_BYTES_V1,
        ),
    ):
        if (
            type(used) is not int
            or type(limit) is not int
            or used < 0
            or used > maximum
            or limit <= 0
            or limit > maximum
            or used > limit
        ):
            reasons.append(f"filesystem {used_name} accounting is invalid")
    try:
        for payload in (
            evidence.network.operstate_after_up_json,
            evidence.network.operstate_after_down_json,
        ):
            if not isinstance(payload, bytes) or len(payload) > _MAX_OBSERVATION_BYTES:
                raise ValueError("network diagnostic exceeds the v1 bound")
            parsed = json.loads(payload.decode("utf-8"))
            if not _bounded_json_shape(parsed):
                raise ValueError("network diagnostic nesting exceeds the v1 bound")
            if _contains_forbidden_absolute_claim_key(parsed):
                raise ValueError("network diagnostic contains a prohibited claim")
            if canonical_json_bytes(parsed) != payload:
                reasons.append("network operstate diagnostic is not canonical JSON")
    except (
        AttributeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ):
        reasons.append("network operstate diagnostic is invalid")
    return reasons


def _intrinsic_completeness_reasons(evidence: ExecutionEvidenceV1) -> list[str]:
    reasons: list[str] = []
    if (
        evidence.correlation.deadline_monotonic_ns
        - evidence.correlation.started_monotonic_ns
        > MAX_RUNTIME_HORIZON_NS_V1
    ):
        reasons.append("execution deadline exceeds the 300-second v1 horizon")
    if any(
        stage.status is not EvidenceStageStatusV1.PASS
        for stage in evidence.capability_stages
    ):
        reasons.append("one or more provider stages are not PASS")
    observed_event_map = tuple(
        (item.event_id, item.observation_class, item.os_source)
        for item in evidence.observations
    )
    if observed_event_map != REQUIRED_OBSERVATION_EVENTS_V1:
        reasons.append("required OS event IDs, classes, or sources are incomplete")
    reasons.extend(_os_payload_completeness_reasons(evidence))
    completeness = evidence.completeness
    if completeness.required_observation_classes != REQUIRED_OBSERVATION_CLASSES_V1:
        reasons.append("required observation bitmap is incomplete")
    if completeness.missing_observation_classes:
        reasons.append("one or more required observations are missing")
    if completeness.sequence_gaps:
        reasons.append("provider sequence contains gaps")
    if completeness.provider_errors:
        reasons.append("provider errors were observed")
    if completeness.observer_errors:
        reasons.append("observer errors were observed")
    if completeness.buffer_loss or evidence.streams.overflow or evidence.streams.observer_loss:
        reasons.append("stream or observation loss occurred")
    if not completeness.teardown_observed or not evidence.filesystem.teardown_observed:
        reasons.append("terminal teardown observation is missing")
    if not completeness.cleanup.complete:
        reasons.append("cleanup is incomplete or residue remains")
    if not evidence.process.survivor_observation_available:
        reasons.append("survivor observation is unavailable")
    if evidence.process.current_execution_survivor_count != 0:
        reasons.append("one or more current-execution survivors remain")
    if evidence.process.populated_after_cleanup != 0:
        reasons.append("execution cgroup did not reach populated zero")
    if not evidence.process.pidfd_exit_observed:
        reasons.append("pidfd exit observation is missing")
    if (
        evidence.process.initial_pid is None
        or evidence.process.initial_starttime_ticks is None
        or not evidence.process.initial_pidfd_opened
        or evidence.process.member_count_observed < 1
        or not evidence.process.all_members_pidfd_bound
    ):
        reasons.append("stable process and complete-member identity is unproved")
    members = evidence.process.member_observations
    expected_cgroup_path = f"/{evidence.correlation.execution_id}/composition"
    if (
        not members
        or evidence.process.member_count_observed != len(members)
        or not all(
            item.cgroup_path == expected_cgroup_path
            and item.pidfd_opened
            and item.identity_revalidated
            and item.pidfd_exit_observed
            and (
                (
                    item.observed_before_kill
                    and item.pidfd_unreadable_before_kill
                )
                or (
                    item.observed_before_grace
                    and not item.observed_before_kill
                    and not item.pidfd_unreadable_before_kill
                )
            )
            for item in members
        )
        or not any(item.observed_before_grace for item in members)
        or not any(item.observed_before_kill for item in members)
        or (
            evidence.process.initial_pid,
            evidence.process.initial_starttime_ticks,
        )
        not in {(item.pid, item.starttime_ticks) for item in members}
    ):
        reasons.append("per-member pidfd/starttime/cgroup evidence is incomplete")
    member_identities = {(item.pid, item.starttime_ticks) for item in members}
    if any(
        (item.pid, item.starttime_ticks) not in member_identities
        or item.cgroup_path != expected_cgroup_path
        or item.monotonic_ns < evidence.correlation.started_monotonic_ns
        or item.monotonic_ns > evidence.correlation.finished_monotonic_ns
        for item in evidence.process.secondary_exec_denials
    ):
        reasons.append(
            "secondary exec denial is not bound to a current cgroup member and interval"
        )
    if (
        evidence.process.observed_uid is None
        or evidence.process.observed_uid <= 0
        or evidence.process.observed_gid is None
        or evidence.process.observed_gid <= 0
        or evidence.process.observed_supplementary_groups != ()
        or evidence.process.observed_effective_capability_mask != 0
        or evidence.process.observed_no_new_privs is not True
        or evidence.process.observed_uid_tuple
        != (evidence.process.observed_uid,) * 4
        or evidence.process.observed_gid_tuple
        != (evidence.process.observed_gid,) * 4
    ):
        reasons.append("unprivileged workload identity observations are incomplete")
    if evidence.process.observed_pids_max is None:
        reasons.append("OS read-back of composition pids.max is missing")
    if (
        not evidence.process.cgroup_kill_written
        or evidence.process.populated_before_kill != 1
    ):
        reasons.append("exact cgroup termination observation is incomplete")
    grace_start = evidence.process.grace_started_monotonic_ns
    grace_finish = evidence.process.grace_finished_monotonic_ns
    terminal_times = tuple(
        value
        for value in (
            evidence.process.workload_exit_monotonic_ns,
            evidence.process.timeout_trigger_monotonic_ns,
        )
        if value is not None
    )
    grace_shape_invalid = (
        evidence.process.force_kill_after_grace is not True
        or grace_start is None
        or grace_finish is None
        or grace_start < evidence.correlation.started_monotonic_ns
        or grace_finish > evidence.correlation.finished_monotonic_ns
    )
    if evidence.outcome is ExecutionOutcomeV1.LIMIT:
        grace_shape_invalid = grace_shape_invalid or grace_finish != grace_start
    else:
        grace_shape_invalid = (
            grace_shape_invalid
            or grace_finish - grace_start < evidence.process.termination_grace_ns
        )
    if grace_shape_invalid:
        reasons.append("full monotonic termination grace before force-kill is unproved")
    if any(
        value < evidence.correlation.started_monotonic_ns
        or value > evidence.correlation.finished_monotonic_ns
        or grace_start is None
        or value > grace_start
        for value in terminal_times
    ):
        reasons.append("terminal trigger time is outside its observed execution interval")
    event_classes = evidence.process.event_classes
    if "exec" not in event_classes:
        reasons.append("ptrace process event classes do not include exec")
    if evidence.outcome not in {
        ExecutionOutcomeV1.LIMIT,
        ExecutionOutcomeV1.TIMEOUT,
    } and (
        "exit_stop" not in event_classes
        or not ({"exit", "signal_exit"} & set(event_classes))
    ):
        reasons.append("normal process event classes lack exit-stop or terminal exit")
    if (
        evidence.filesystem.rejected_boundary_attempts
        != REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1
    ):
        reasons.append("filesystem boundary denial controls are incomplete")
    for label, quota in (
        ("scratch", evidence.filesystem.scratch_quota_before_release),
        ("output", evidence.filesystem.output_quota_before_release),
    ):
        if (
            quota is None
            or quota.filesystem_type != "tmpfs"
            or quota.mount_options != _PRIVATE_TMPFS_MOUNT_OPTIONS_V1
            or quota.fragment_size != 4_096
        ):
            reasons.append(f"{label} tmpfs mount enforcement is incomplete")
    if (
        not evidence.filesystem.quota_observed_before_release
        or not evidence.filesystem.quota_observed_after_kill
        or evidence.filesystem.scratch_observed_byte_ceiling is None
        or evidence.filesystem.scratch_observed_inode_ceiling is None
        or evidence.filesystem.output_observed_byte_ceiling is None
        or evidence.filesystem.output_observed_inode_ceiling is None
    ):
        reasons.append("private quota observations are incomplete across execution")
    if (
        not evidence.filesystem.undeclared_output_blocked
        or not evidence.filesystem.output_parent_directories_nonwritable
        or not set(evidence.filesystem.observed_output_paths).issubset(
            evidence.filesystem.declared_output_allowlist
        )
    ):
        reasons.append("declared-only output allowlist enforcement is incomplete")
    retained_relative_paths = tuple(
        sorted(
            item.path.removeprefix(
                evidence.filesystem.output_private_path.rstrip("/") + "/"
            )
            for item in evidence.filesystem.retained_outputs
        )
    )
    if retained_relative_paths != evidence.filesystem.observed_output_paths:
        reasons.append("retained output identities do not cover observed output files")
    chain = evidence.exec_chain
    if chain.mismatch_code is not None or chain.denial_code is not None:
        reasons.append("exec chain was denied or mismatched")
    for label, requested, selected, sealed, actual, seals in (
        (
            "entrypoint",
            chain.requested_entrypoint,
            chain.selected_entrypoint,
            chain.sealed_entrypoint,
            chain.actual_entrypoint,
            chain.entrypoint_seals,
        ),
        (
            "interpreter",
            chain.requested_interpreter,
            chain.selected_interpreter,
            chain.sealed_interpreter,
            chain.actual_interpreter,
            chain.interpreter_seals,
        ),
        (
            "loader",
            chain.requested_loader,
            chain.selected_loader,
            chain.sealed_loader,
            chain.actual_loader,
            chain.loader_seals,
        ),
    ):
        if not _selected_identity_matches(requested, selected):
            reasons.append(f"selected {label} identity does not match request")
        if not _sealed_identity_matches(requested, sealed, seals):
            reasons.append(f"sealed {label} identity or seal set is mismatched")
        if not _actual_identity_matches_sealed(sealed, actual):
            reasons.append(f"actual {label} identity does not match sealed object")
    sequence = (
        chain.open_sequence,
        chain.seal_sequence,
        chain.recheck_sequence,
        chain.exec_sequence,
        chain.ptrace_exec_sequence,
    )
    if not all(type(item) is int and item > 0 for item in sequence) or not all(
        left < right for left, right in zip(sequence, sequence[1:])
    ):
        reasons.append("exec open/seal/recheck/exec/ptrace sequence is incomplete")
    if (
        chain.effective_argv_sha256 is None
        or chain.effective_argv_count is None
        or chain.effective_environment_sha256 is None
        or chain.effective_environment_count is None
    ):
        reasons.append("effective exec argv/environment observation is incomplete")
    if (
        evidence.network.flags_after_up is None
        or evidence.network.flags_after_up & 1 != 1
    ):
        reasons.append("loopback IFF_UP positive observation is missing")
    if evidence.network.flags_after_down is None or evidence.network.flags_after_down & 1:
        reasons.append("loopback IFF_UP clear observation is missing")
    if not evidence.network.inherited_network_fd_absent_at_exec:
        reasons.append("inherited network descriptor closure is unproved")
    if evidence.network.seccomp_filter_sha256 != SOCKET_DENIAL_FILTER_SHA256_V1:
        reasons.append("socket-denial filter observation is mismatched")
    if evidence.network.socket_denial_errno != 1:
        reasons.append("socket denial did not return EPERM")
    if not (
        evidence.network.live_endpoint_positive_control
        and evidence.network.live_endpoint_denial_control
    ):
        reasons.append("network positive/negative controls are incomplete")
    if (
        evidence.network.denied_attempt_classes
        != REQUIRED_NETWORK_DENIAL_CLASSES_V1
    ):
        reasons.append("network denial control classes are incomplete")
    filesystem_limit = evidence.filesystem.limit_observation
    if filesystem_limit is not None and (
        (
            filesystem_limit.pid,
            filesystem_limit.starttime_ticks,
        )
        not in {(item.pid, item.starttime_ticks) for item in members}
        or filesystem_limit.cgroup_path != expected_cgroup_path
        or filesystem_limit.monotonic_ns
        < evidence.correlation.started_monotonic_ns
        or filesystem_limit.monotonic_ns
        > evidence.correlation.finished_monotonic_ns
        or grace_start is None
        or filesystem_limit.monotonic_ns > grace_start
    ):
        reasons.append("filesystem limit observation is not bound to the process set")
    scope_is_scratch = (
        filesystem_limit is not None
        and filesystem_limit.scope is FilesystemLimitScopeV1.SCRATCH
    )
    scope_used_bytes = (
        evidence.filesystem.scratch_used_bytes
        if scope_is_scratch
        else evidence.filesystem.output_used_bytes
    )
    scope_byte_ceiling = (
        evidence.filesystem.scratch_observed_byte_ceiling
        if scope_is_scratch
        else evidence.filesystem.output_observed_byte_ceiling
    )
    scope_byte_limit = (
        evidence.filesystem.scratch_byte_limit
        if scope_is_scratch
        else evidence.filesystem.output_byte_limit
    )
    scope_used_inodes = (
        evidence.filesystem.scratch_used_inodes
        if scope_is_scratch
        else evidence.filesystem.output_used_inodes
    )
    scope_inode_ceiling = (
        evidence.filesystem.scratch_observed_inode_ceiling
        if scope_is_scratch
        else evidence.filesystem.output_observed_inode_ceiling
    )
    scope_inode_limit = (
        evidence.filesystem.scratch_inode_limit
        if scope_is_scratch
        else evidence.filesystem.output_inode_limit
    )
    byte_ceiling_hit = scope_used_bytes == scope_byte_ceiling == scope_byte_limit
    inode_ceiling_hit = (
        scope_used_inodes == scope_inode_ceiling == scope_inode_limit
    )
    file_size_limit = max(
        evidence.filesystem.scratch_byte_limit,
        evidence.filesystem.file_output_byte_limit,
    )
    if (
        filesystem_limit is not None
        and filesystem_limit.errno == 27
        and scope_byte_limit != file_size_limit
    ):
        reasons.append(
            "filesystem EFBIG observation scope does not match the exact "
            "process file-size limit"
        )
    if (
        filesystem_limit is not None
        and filesystem_limit.monotonic_ns >= evidence.correlation.deadline_monotonic_ns
    ):
        reasons.append("filesystem limit observation is not strictly pre-deadline")
    if filesystem_limit is not None and (
        (
            filesystem_limit.kind is FilesystemLimitKindV1.SYSCALL_ERRNO
            and filesystem_limit.errno in {28, 122}
            and not (byte_ceiling_hit or inode_ceiling_hit)
        )
    ):
        reasons.append(
            "filesystem quota signal is not correlated with a full private tmpfs"
        )
    limit_signal = filesystem_limit is not None or any(
        item.limit_triggered
        for item in (
            evidence.streams.stdout,
            evidence.streams.stderr,
            evidence.streams.combined,
        )
    )
    if limit_signal != evidence.process.limit_triggered:
        reasons.append("observed output limit signal and process trigger disagree")
    if limit_signal and evidence.outcome is not ExecutionOutcomeV1.LIMIT:
        reasons.append("an observed output limit must produce the limit outcome")
    if evidence.process.timeout_triggered != (
        evidence.process.timeout_trigger_monotonic_ns is not None
    ):
        reasons.append("timeout trigger flag and monotonic observation disagree")
    if evidence.process.limit_triggered and evidence.process.timeout_triggered:
        reasons.append("limit and timeout triggers are mutually exclusive")
    if evidence.outcome in {
        ExecutionOutcomeV1.NOT_EXECUTED,
        ExecutionOutcomeV1.POLICY_DENIAL,
        ExecutionOutcomeV1.CAPABILITY_BLOCKER,
        ExecutionOutcomeV1.OBSERVATION_INCOMPLETE,
        ExecutionOutcomeV1.CLEANUP_INCOMPLETE,
    }:
        reasons.append("outcome cannot carry complete execution evidence")
    if evidence.outcome is ExecutionOutcomeV1.SUCCESS:
        if (
            evidence.workload_released is not True
            or evidence.workload_exit_code != 0
            or evidence.process.limit_triggered
            or evidence.process.timeout_triggered
            or evidence.process.workload_exit_monotonic_ns is None
            or evidence.process.workload_exit_monotonic_ns
            >= evidence.correlation.deadline_monotonic_ns
            or evidence.process.timeout_trigger_monotonic_ns is not None
        ):
            reasons.append("success outcome does not match workload observations")
    elif evidence.outcome is ExecutionOutcomeV1.WORKLOAD_FAILURE:
        if (
            evidence.workload_released is not True
            or evidence.workload_exit_code in {None, 0}
            or evidence.process.workload_exit_monotonic_ns is None
            or evidence.process.workload_exit_monotonic_ns
            >= evidence.correlation.deadline_monotonic_ns
            or evidence.process.timeout_trigger_monotonic_ns is not None
        ):
            reasons.append("workload-failure outcome does not match exit observation")
    elif evidence.outcome is ExecutionOutcomeV1.LIMIT:
        if (
            evidence.workload_released is not True
            or evidence.workload_exit_code is not None
            or not evidence.process.limit_triggered
            or evidence.process.timeout_triggered
            or evidence.process.workload_exit_monotonic_ns is not None
            or evidence.process.timeout_trigger_monotonic_ns is not None
        ):
            reasons.append("limit outcome lacks an observed limit trigger")
    elif evidence.outcome is ExecutionOutcomeV1.TIMEOUT:
        if (
            evidence.workload_released is not True
            or evidence.workload_exit_code is not None
            or not evidence.process.timeout_triggered
            or evidence.process.limit_triggered
            or evidence.process.workload_exit_monotonic_ns is not None
            or evidence.process.timeout_trigger_monotonic_ns is None
            or evidence.process.timeout_trigger_monotonic_ns
            < evidence.correlation.deadline_monotonic_ns
        ):
            reasons.append("timeout outcome lacks an observed timeout trigger")
    if evidence.outcome not in {
        ExecutionOutcomeV1.SUCCESS,
        ExecutionOutcomeV1.WORKLOAD_FAILURE,
    } and evidence.process.workload_exit_monotonic_ns is not None:
        reasons.append("non-exit outcome must not carry a workload-exit timestamp")
    if (
        evidence.outcome is not ExecutionOutcomeV1.TIMEOUT
        and evidence.process.timeout_trigger_monotonic_ns is not None
    ):
        reasons.append("non-timeout outcome must not carry a timeout timestamp")
    return reasons


def _os_payload_completeness_reasons(
    evidence: ExecutionEvidenceV1,
) -> list[str]:
    """Bind each frozen OS event payload to its typed evidence projection."""

    payloads = {item.event_id: item.payload() for item in evidence.observations}
    if set(payloads) != {item[0] for item in REQUIRED_OBSERVATION_EVENTS_V1}:
        return ["required OS payload set is incomplete"]
    if not all(isinstance(value, dict) for value in payloads.values()):
        return ["required OS payload must be an object"]
    reasons: list[str] = []
    for event_id, payload in payloads.items():
        if set(payload) != _REQUIRED_OBSERVATION_PAYLOAD_KEYS_V1[event_id]:
            reasons.append(f"{event_id} payload key set does not match core v1")

    host = payloads["host.gate"]
    cgroup2_gate = host.get("cgroup2_gate")
    mandatory_abi = host.get("mandatory_abi_control")
    if not (
        host.get("os") == "Linux"
        and host.get("architecture") == "x86_64"
        and host.get("effective_uid") == 0
        and host.get("cgroup_v2") is True
        and host.get("openat2") is True
        and host.get("pidfd") is True
        and host.get("monotonic") is True
        and host.get("fallback") is False
        and host.get("core_pipe_helper_absent") is True
        and isinstance(cgroup2_gate, dict)
        and set(cgroup2_gate)
        == {
            "filesystem_type",
            "mount_root",
            "mountpoint",
            "current_unified_cgroup",
            "mount_id",
            "writable",
        }
        and cgroup2_gate.get("filesystem_type") == "cgroup2"
        and cgroup2_gate.get("mountpoint") == "/sys/fs/cgroup"
        and _valid_os_absolute_path(cgroup2_gate.get("mount_root"))
        and _valid_os_absolute_path(cgroup2_gate.get("current_unified_cgroup"))
        and type(cgroup2_gate.get("mount_id")) is int
        and 0 < cgroup2_gate["mount_id"] <= _MAX_INTEGER_V1
        and cgroup2_gate.get("writable") is True
        and mandatory_abi
        == {
            "pidfd_send_signal": True,
            "ptrace_exec_event": True,
            "execveat": True,
            "synthetic_only": True,
        }
    ):
        reasons.append("host.gate OS payload is incomplete")

    chain = evidence.exec_chain
    identity = payloads["identity.seal"]
    for name, selected, sealed in (
        ("entrypoint", chain.selected_entrypoint, chain.sealed_entrypoint),
        ("interpreter", chain.selected_interpreter, chain.sealed_interpreter),
        ("loader", chain.selected_loader, chain.sealed_loader),
    ):
        expected = (
            {
                "source_identity": selected.to_record(),
                "sealed_identity": sealed.to_record(),
            }
            if selected is not None and sealed is not None
            else None
        )
        if identity.get(name) != expected:
            reasons.append(f"identity.seal {name} payload is mismatched")
    if tuple(identity.get("seals", ())) != REQUIRED_MEMFD_SEALS_V1:
        reasons.append("identity.seal memfd seal payload is incomplete")

    execution_id = evidence.correlation.execution_id
    cgroup_root = f"/sys/fs/cgroup/{execution_id}"
    expected_cgroup_paths = (
        cgroup_root,
        f"{cgroup_root}/composition",
        f"{cgroup_root}/combined-stream",
        f"{cgroup_root}/timeout",
    )
    claim = payloads["cgroup.claim"]
    if (
        tuple(claim.get("exact_paths", ())) != expected_cgroup_paths
        or claim.get("identity_count") != len(expected_cgroup_paths)
        or claim.get("observed_pids_max") != evidence.process.observed_pids_max
        or not isinstance(claim.get("nonce_sha256"), str)
        or _SHA256_RE.fullmatch(claim["nonce_sha256"]) is None
    ):
        reasons.append("cgroup.claim ownership payload is incomplete")

    namespace = payloads["namespace.setup"]
    namespace_ids = namespace.get("namespace_ids")
    parent_ids = namespace.get("parent_namespace_ids")
    namespace_names = {"mnt", "pid", "net", "ipc", "uts"}
    if not (
        isinstance(namespace_ids, dict)
        and isinstance(parent_ids, dict)
        and set(namespace_ids) == namespace_names
        and set(parent_ids) == namespace_names
        and all(
            (child_inode := _namespace_inode_v1(name, namespace_ids[name]))
            is not None
            and (parent_inode := _namespace_inode_v1(name, parent_ids[name]))
            is not None
            and child_inode != parent_inode
            for name in namespace_names
        )
        and namespace.get("all_distinct_from_parent") is True
        and namespace.get("private_mount_propagation") is True
        and namespace.get("host_mounts_during_live_namespace") == []
    ):
        reasons.append("namespace.setup OS identity payload is incomplete")

    filesystem = payloads["filesystem.gate"]
    private_quota = filesystem.get("private_quota_observations")
    read_only_mounts = filesystem.get("read_only_mount_observations")
    read_only_scans = filesystem.get("read_only_input_scans")
    declared_control = filesystem.get("declared_output_control")
    provider_views = filesystem.get("provider_view_controls")
    private_root_mount = filesystem.get("private_root_mount_observation")
    scratch_quota = evidence.filesystem.scratch_quota_before_release
    output_quota = evidence.filesystem.output_quota_before_release
    if not (
        filesystem.get("rejected_boundary_attempts")
        == list(REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1)
        and filesystem.get("quota_controls")
        == {"byte_enospc": True, "inode_enospc": True}
        and isinstance(private_quota, dict)
        and set(private_quota) == {"observed_before_release", "scratch", "output"}
        and private_quota.get("observed_before_release") is True
        and scratch_quota is not None
        and private_quota.get("scratch") == scratch_quota.to_record()
        and output_quota is not None
        and private_quota.get("output") == output_quota.to_record()
    ):
        reasons.append("filesystem.gate OS enforcement payload is incomplete")
    expected_read_only = {
        root.private_path: (
            root.device,
            root.inode,
            root.mode,
            {
                key: value
                for key, value in scan.to_record().items()
                if key != "root"
            },
        )
        for root, scan in zip(
            evidence.filesystem.effective_read_only_inputs,
            evidence.filesystem.read_only_input_scans,
        )
    }
    for sealed in (
        chain.sealed_entrypoint,
        chain.sealed_interpreter,
        chain.sealed_loader,
    ):
        if sealed is not None:
            expected_read_only[sealed.path] = (
                sealed.device,
                sealed.inode,
                sealed.mode,
                None,
            )
    read_only_mount_keys = {
        "target",
        "mount_options",
        "statvfs_read_only",
        "write_denial_errno",
        "device",
        "inode",
        "mode",
        "tree_control",
    }
    if not (
        isinstance(read_only_mounts, list)
        and len(read_only_mounts) == len(expected_read_only)
        and all(isinstance(item, dict) for item in read_only_mounts)
        and {item.get("target") for item in read_only_mounts}
        == set(expected_read_only)
        and all(
            set(item) == read_only_mount_keys
            and item.get("mount_options") == list(_READ_ONLY_BIND_MOUNT_OPTIONS_V1)
            and item.get("statvfs_read_only") is True
            and item.get("write_denial_errno") == 30
            and (
                item.get("device"),
                item.get("inode"),
                item.get("mode"),
                item.get("tree_control"),
            )
            == expected_read_only[item["target"]]
            for item in read_only_mounts
        )
    ):
        reasons.append("filesystem.gate read-only mount payload is incomplete")
    if read_only_scans != [
        item.to_record() for item in evidence.filesystem.read_only_input_scans
    ]:
        reasons.append("filesystem.gate read-only input scan payload is incomplete")
    if not (
        isinstance(declared_control, dict)
        and set(declared_control)
        == {
            "declared_output_allowlist",
            "undeclared_output_blocked",
            "output_parent_directories_nonwritable",
            "creation_denial_errno",
        }
        and tuple(declared_control.get("declared_output_allowlist", ()))
        == evidence.filesystem.declared_output_allowlist
        and declared_control.get("undeclared_output_blocked") is True
        and declared_control.get("output_parent_directories_nonwritable") is True
        and declared_control.get("creation_denial_errno") == 13
    ):
        reasons.append("filesystem.gate declared-output control is incomplete")
    if provider_views != {
        "proc_view": {
            "absent": True,
            "access_errno": 2,
            "private_pid_namespace": True,
            "provider_sensitive_paths_denied": True,
            "provider_private_access_errno": 13,
        },
        "sys_view": {"absent": True, "access_errno": 2},
        "device_view": {"absent": True, "access_errno": 2},
    }:
        reasons.append("filesystem.gate provider-view denial payload is incomplete")
    if private_root_mount != {
        "filesystem_type": "tmpfs",
        "mount_options": ["nodev", "nosuid", "rw"],
        "mode": stat.S_IFDIR | 0o755,
        "root_device_changed": True,
        "old_root_removed": True,
    }:
        reasons.append("filesystem.gate private-root mount payload is incomplete")

    network_event = payloads["network.gate"]
    network_control = network_event.get("network")
    seccomp = network_event.get("seccomp_controls")
    network_control_keys = {
        "flags_after_up",
        "flags_after_down",
        "operstate_after_up",
        "operstate_after_down",
        "positive",
        "negative",
        "denial_errno",
        "namespace_inode",
    }
    seccomp_keys = {
        "network",
        "filter_syscalls",
        "clone_control_flags_errno",
        "clone_flag_controls",
        "ordinary_fork_positive",
        "ordinary_vfork_positive",
        "x32_kill_control",
        "fcntl_command_controls",
        "futex_controls",
        "pipe2_controls",
        "native_syscall_exclusive_ceiling",
        "ceiling_syscall_errno",
        "control_scope",
        "observed_filter_sha256",
    }
    seccomp_network_keys = {
        "dns",
        "ipv4",
        "ipv6",
        "namespace_bridge",
        "netlink",
        "packet",
    }
    seccomp_clone_keys = {
        "namespace",
        "thread",
        "untraced",
        "vm",
        "fs",
        "files",
        "sighand",
    }
    expected_filter_controls = {
        name: 1 for name, _ in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1
    }
    expected_fcntl_controls = {name: 1 for name, _ in FCNTL_DENIED_COMMANDS_V1}
    if not (
        isinstance(network_control, dict)
        and set(network_control) == network_control_keys
        and network_control.get("namespace_inode") == evidence.network.namespace_inode
        and network_control.get("flags_after_up") == evidence.network.flags_after_up
        and network_control.get("flags_after_down") == evidence.network.flags_after_down
        and network_control.get("positive")
        is evidence.network.live_endpoint_positive_control
        and network_control.get("negative")
        is evidence.network.live_endpoint_denial_control
        and network_control.get("operstate_after_up")
        == json.loads(evidence.network.operstate_after_up_json.decode("utf-8"))
        and network_control.get("operstate_after_down")
        == json.loads(evidence.network.operstate_after_down_json.decode("utf-8"))
        and type(network_control.get("denial_errno")) is int
        and 0 < network_control["denial_errno"] <= 4_095
        and network_event.get("socket_denial_errno") == 1
        and network_event.get("seccomp_filter_sha256")
        == evidence.network.seccomp_filter_sha256
        and isinstance(seccomp, dict)
        and set(seccomp) == seccomp_keys
        and seccomp.get("observed_filter_sha256")
        == evidence.network.seccomp_filter_sha256
        and isinstance(seccomp.get("filter_syscalls"), dict)
        and set(seccomp["filter_syscalls"]) == set(expected_filter_controls)
        and seccomp["filter_syscalls"] == expected_filter_controls
        and seccomp.get("clone_control_flags_errno") == 1
        and isinstance(seccomp.get("clone_flag_controls"), dict)
        and set(seccomp["clone_flag_controls"]) == seccomp_clone_keys
        and seccomp["clone_flag_controls"]
        == {
            "namespace": 1,
            "thread": 1,
            "untraced": 1,
            "vm": 1,
            "fs": 1,
            "files": 1,
            "sighand": 1,
        }
        and seccomp.get("ordinary_fork_positive") is True
        and seccomp.get("ordinary_vfork_positive") is True
        and seccomp.get("x32_kill_control") is True
        and seccomp.get("native_syscall_exclusive_ceiling")
        == NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
        and seccomp.get("ceiling_syscall_errno") == 1
        and isinstance(seccomp.get("fcntl_command_controls"), dict)
        and set(seccomp["fcntl_command_controls"]) == set(expected_fcntl_controls)
        and seccomp["fcntl_command_controls"] == expected_fcntl_controls
        and seccomp.get("futex_controls")
        == {"shared_wake_errno": 1, "private_wake_result": 0}
        and seccomp.get("pipe2_controls")
        == {"direct_errno": 1, "notification_errno": 1, "ordinary": True}
        and seccomp.get("control_scope") == "outer_supervisor_pre_workload_release"
        and isinstance(seccomp.get("network"), dict)
        and set(seccomp["network"]) == seccomp_network_keys
        and all(value == 1 for value in seccomp["network"].values())
    ):
        reasons.append("network.gate OS/seccomp payload is incomplete")

    for event_id, mode, minimum_elapsed in (
        ("stream.control", "stream", 1),
        ("timeout.control", "timeout", 25_000_000),
    ):
        control = payloads[event_id]
        if not (
            control.get("mode") == mode
            and type(control.get("observed_bytes")) is int
            and (
                control["observed_bytes"] > 8_192
                if mode == "stream"
                else control["observed_bytes"] == 0
            )
            and type(control.get("monotonic_elapsed_ns")) is int
            and control["monotonic_elapsed_ns"] >= minimum_elapsed
            and control.get("populated_before_kill") == 1
            and control.get("freeze_positive_control") is True
            and control.get("unfreeze_positive_control") is True
            and control.get("cgroup_kill_written") is True
            and control.get("pidfd_exit_observed") is True
            and control.get("populated_zero") is True
        ):
            reasons.append(f"{event_id} OS control payload is incomplete")

    deadline = payloads["deadline.release_recheck"]
    release_ns = deadline.get("release_recheck_monotonic_ns")
    if not (
        type(release_ns) is int
        and evidence.correlation.started_monotonic_ns
        <= release_ns
        < evidence.correlation.deadline_monotonic_ns
        and deadline.get("deadline_monotonic_ns")
        == evidence.correlation.deadline_monotonic_ns
        and deadline.get("termination_grace_ns")
        == evidence.process.termination_grace_ns
        and evidence.correlation.deadline_monotonic_ns - release_ns
        <= MAX_RUNTIME_HORIZON_NS_V1
        and release_ns + evidence.process.termination_grace_ns
        < evidence.correlation.deadline_monotonic_ns
        and deadline.get("eligible") is True
    ):
        reasons.append("deadline release recheck payload is incomplete")
    if payloads["workload.release"].get("released") is not True:
        reasons.append("workload release payload is incomplete")

    exec_payload = payloads["exec.ptrace"]
    expected_file_size_limit = max(
        evidence.filesystem.scratch_byte_limit,
        evidence.filesystem.file_output_byte_limit,
    )
    expected_exec_payload_keys = {
        "execution_id",
        "kind",
        "actual_entrypoint",
        "actual_interpreter",
        "actual_loader",
        "loader_map_identity_match",
        "uid",
        "gid",
        "groups",
        "cap_eff",
        "no_new_privs",
        "fd_set",
        "stdio_pipe_identities",
        "stdio_provider_match",
        "file_size_soft_limit",
        "file_size_hard_limit",
        "core_soft_limit",
        "core_hard_limit",
        "seccomp_mode",
        "seccomp_filters",
        "baseline_seccomp_filters",
        "seccomp_filter_delta",
        "effective_argv_sha256",
        "effective_argv_count",
        "effective_environment_sha256",
        "effective_environment_count",
        "inherited_network_fd_absent",
        "exec_pid",
        "namespace_exec_pid",
        "exec_starttime_ticks",
        "exec_cgroup",
        "secondary_exec_policy",
    }
    if set(exec_payload) != expected_exec_payload_keys:
        reasons.append("exec.ptrace payload key set does not match core v1")
    for name, observed in (
        ("actual_entrypoint", chain.actual_entrypoint),
        ("actual_interpreter", chain.actual_interpreter),
        ("actual_loader", chain.actual_loader),
    ):
        expected = observed.to_record() if observed is not None else None
        if exec_payload.get(name) != expected:
            reasons.append(f"exec.ptrace {name} payload is mismatched")
    stdio = exec_payload.get("stdio_pipe_identities")
    stdio_identities: list[tuple[int, int]] = []
    stdio_valid = isinstance(stdio, dict) and set(stdio) == {"0", "1", "2"}
    if stdio_valid:
        for descriptor in ("0", "1", "2"):
            identity = stdio[descriptor]
            if not (
                isinstance(identity, dict)
                and set(identity) == {"device", "inode", "mode"}
                and type(identity.get("device")) is int
                and 0 <= identity["device"] <= _MAX_INTEGER_V1
                and type(identity.get("inode")) is int
                and 0 < identity["inode"] <= _MAX_INTEGER_V1
                and type(identity.get("mode")) is int
                and 0 <= identity["mode"] <= 0xFFFFFFFF
                and stat.S_ISFIFO(identity["mode"])
            ):
                stdio_valid = False
                break
            stdio_identities.append((identity["device"], identity["inode"]))
    baseline_filters = exec_payload.get("baseline_seccomp_filters")
    observed_filters = exec_payload.get("seccomp_filters")
    observed_filter_count = (
        int(observed_filters)
        if isinstance(observed_filters, str) and observed_filters.isdecimal()
        else None
    )
    secondary_exec_policy = exec_payload.get("secondary_exec_policy")
    if not (
        exec_payload.get("kind") == "ptrace_exec"
        and exec_payload.get("loader_map_identity_match") is True
        and exec_payload.get("inherited_network_fd_absent") is True
        and exec_payload.get("effective_argv_sha256")
        == chain.effective_argv_sha256
        and exec_payload.get("effective_argv_count")
        == chain.effective_argv_count
        and exec_payload.get("effective_environment_sha256")
        == chain.effective_environment_sha256
        and exec_payload.get("effective_environment_count")
        == chain.effective_environment_count
        and exec_payload.get("fd_set") == [0, 1, 2]
        and exec_payload.get("stdio_provider_match") is True
        and stdio_valid
        and len(stdio_identities) == len(set(stdio_identities)) == 3
        and exec_payload.get("file_size_soft_limit")
        == expected_file_size_limit
        and exec_payload.get("file_size_hard_limit")
        == expected_file_size_limit
        and type(exec_payload.get("core_soft_limit")) is int
        and exec_payload["core_soft_limit"] == 0
        and type(exec_payload.get("core_hard_limit")) is int
        and exec_payload["core_hard_limit"] == 0
        and exec_payload.get("seccomp_mode") == "2"
        and type(baseline_filters) is int
        and 0 <= baseline_filters <= 256
        and observed_filter_count == baseline_filters + 1
        and exec_payload.get("seccomp_filter_delta") == 1
        and type(exec_payload.get("namespace_exec_pid")) is int
        and 0 < exec_payload["namespace_exec_pid"] <= _MAX_PID_V1
        and secondary_exec_policy
        == {
            "execve": 59,
            "execveat": 322,
            "ptrace_entry_denial": True,
            "ptrace_event_exec_backstop": True,
        }
    ):
        reasons.append("exec.ptrace identity/descriptor payload is incomplete")

    process_payload = payloads["process.contain"]
    if not (
        process_payload.get("initial_pid") == evidence.process.initial_pid
        and process_payload.get("initial_starttime_ticks")
        == evidence.process.initial_starttime_ticks
        and process_payload.get("initial_pidfd_opened")
        is evidence.process.initial_pidfd_opened
        and process_payload.get("member_observations")
        == [item.to_record() for item in evidence.process.member_observations]
        and process_payload.get("member_count")
        == evidence.process.member_count_observed
        and process_payload.get("observed_pids_max")
        == evidence.process.observed_pids_max
        and process_payload.get("all_members_pidfd_bound")
        is evidence.process.all_members_pidfd_bound
        and process_payload.get("secondary_exec_denials")
        == [item.to_record() for item in evidence.process.secondary_exec_denials]
        and process_payload.get("retained_outputs")
        == [item.to_record() for item in evidence.filesystem.retained_outputs]
        and process_payload.get("workload_exit_code")
        == evidence.workload_exit_code
        and process_payload.get("workload_exit_monotonic_ns")
        == evidence.process.workload_exit_monotonic_ns
        and process_payload.get("timeout_trigger_monotonic_ns")
        == evidence.process.timeout_trigger_monotonic_ns
        and process_payload.get("limit_triggered")
        is evidence.process.limit_triggered
        and process_payload.get("timeout_triggered")
        is evidence.process.timeout_triggered
        and process_payload.get("grace_started_monotonic_ns")
        == evidence.process.grace_started_monotonic_ns
        and process_payload.get("grace_finished_monotonic_ns")
        == evidence.process.grace_finished_monotonic_ns
        and process_payload.get("force_kill_after_grace") is True
        and process_payload.get("cgroup_kill_written") is True
        and process_payload.get("populated_before_kill") == 1
        and process_payload.get("populated_after_kill") == 0
        and process_payload.get("pidfd_exit_observed") is True
        and process_payload.get("survivor_count") == 0
        and tuple(process_payload.get("event_classes", ()))
        == evidence.process.event_classes
        and process_payload.get("quota_observed_after_kill") is True
        and process_payload.get("scratch_observed_byte_ceiling")
        == evidence.filesystem.scratch_observed_byte_ceiling
        and process_payload.get("scratch_observed_inode_ceiling")
        == evidence.filesystem.scratch_observed_inode_ceiling
        and process_payload.get("output_observed_byte_ceiling")
        == evidence.filesystem.output_observed_byte_ceiling
        and process_payload.get("output_observed_inode_ceiling")
        == evidence.filesystem.output_observed_inode_ceiling
        and process_payload.get("scratch_used_bytes")
        == evidence.filesystem.scratch_used_bytes
        and process_payload.get("scratch_used_inodes")
        == evidence.filesystem.scratch_used_inodes
        and process_payload.get("output_used_bytes")
        == evidence.filesystem.output_used_bytes
        and process_payload.get("output_used_inodes")
        == evidence.filesystem.output_used_inodes
        and tuple(process_payload.get("declared_output_allowlist", ()))
        == evidence.filesystem.declared_output_allowlist
        and tuple(process_payload.get("observed_output_paths", ()))
        == evidence.filesystem.observed_output_paths
        and process_payload.get("undeclared_output_blocked") is True
        and process_payload.get("output_parent_directories_nonwritable") is True
        and process_payload.get("filesystem_limit_observation")
        == (
            evidence.filesystem.limit_observation.to_record()
            if evidence.filesystem.limit_observation is not None
            else None
        )
    ):
        reasons.append("process.contain OS payload is incomplete")
    observation_times = {
        item.event_id: item.monotonic_ns for item in evidence.observations
    }
    exec_observed_ns = observation_times.get("exec.ptrace")
    process_observed_ns = observation_times.get("process.contain")
    if (
        type(exec_observed_ns) is not int
        or type(process_observed_ns) is not int
        or any(
            item.monotonic_ns < exec_observed_ns
            or item.monotonic_ns > process_observed_ns
            for item in evidence.process.secondary_exec_denials
        )
    ):
        reasons.append(
            "secondary exec denial time is outside the ptrace observation interval"
        )

    stream_payload = payloads["streams.final"]
    if "decoded_stdout" in stream_payload or "decoded_stderr" in stream_payload:
        reasons.append("streams.final must not publish workload output bytes")
    raw = stream_payload.get("raw_bytes")
    retained = stream_payload.get("retained_bytes")
    discarded = stream_payload.get("discarded_bytes")
    trigger = stream_payload.get("trigger")
    trigger_label = (
        _STREAM_LIMIT_TRIGGERS_V1.get(trigger)
        if isinstance(trigger, str)
        else None
    )
    trigger_matches_counts = (
        trigger is None
        and not evidence.streams.stdout.limit_triggered
        and not evidence.streams.stderr.limit_triggered
        and not evidence.streams.combined.limit_triggered
    ) or (
        trigger_label is not None
        and getattr(evidence.streams, trigger_label).limit_triggered is True
    )
    if not (
        raw
        == {
            "stdout": evidence.streams.stdout.emitted_bytes,
            "stderr": evidence.streams.stderr.emitted_bytes,
        }
        and stream_payload.get("combined_raw_bytes")
        == evidence.streams.combined.emitted_bytes
        and retained
        == {
            "stdout": evidence.streams.stdout.retained_bytes,
            "stderr": evidence.streams.stderr.retained_bytes,
        }
        and discarded
        == {
            "stdout": evidence.streams.stdout.discarded_bytes,
            "stderr": evidence.streams.stderr.discarded_bytes,
        }
        and stream_payload.get("observer_loss") is evidence.streams.observer_loss
        and stream_payload.get("decoding_status")
        == evidence.streams.decoding_status.value
        and stream_payload.get("pipe_capacity_bytes")
        == evidence.streams.pipe_capacity_bytes
        == STREAM_PIPE_CAPACITY_BYTES_V1
        and trigger_matches_counts
    ):
        reasons.append("streams.final raw accounting payload is mismatched")

    cleanup_payload = payloads["cleanup.final"]
    release = cleanup_payload.get("cgroup_release")
    if not (
        isinstance(release, dict)
        and set(release)
        == {"exact_paths", "released_paths", "populated_zero", "failures"}
        and release.get("populated_zero") is True
        and release.get("failures") == []
        and tuple(release.get("exact_paths", ())) == expected_cgroup_paths
        and set(release.get("released_paths", ())) == set(expected_cgroup_paths)
        and cleanup_payload.get("mounts") == []
        and cleanup_payload.get("process_residue") == []
        and cleanup_payload.get("temporary_root_removed") is True
        and cleanup_payload.get("pidfd_exit_observed") is True
        and cleanup_payload.get("failures") == []
    ):
        reasons.append("cleanup.final OS payload is incomplete")
    return reasons


def _correlation_reasons(
    request: IsolationRequestV1, evidence: ExecutionEvidenceV1
) -> list[str]:
    correlation = evidence.correlation
    expected = {
        "execution_id": request.execution_id,
        "request_sha256": request.request_sha256,
        **request.identity.to_record(),
        "backend_profile": request.backend_profile.value,
        "backend_configuration_sha256": request.identity.configuration_sha256,
        "required_capability_set_sha256": request.required_capability_set_sha256,
        "deadline_monotonic_ns": request.process.deadline_monotonic_ns,
    }
    actual = correlation.to_record()
    reasons = [
        f"correlation mismatch: {name}"
        for name, value in expected.items()
        if actual.get(name) != value
    ]
    if evidence.exec_chain.requested_entrypoint != request.executable.entrypoint:
        reasons.append("requested entrypoint evidence does not match request")
    if evidence.exec_chain.requested_interpreter != request.executable.interpreter:
        reasons.append("requested interpreter evidence does not match request")
    if evidence.exec_chain.requested_loader != request.executable.loader:
        reasons.append("requested loader evidence does not match request")
    effective_argv = effective_exec_argv_v1(request)
    effective_environment = effective_exec_environment_v1(request)
    if (
        evidence.exec_chain.effective_argv_sha256
        != canonical_sha256(list(effective_argv))
        or evidence.exec_chain.effective_argv_count != len(effective_argv)
    ):
        reasons.append("effective exec argv digest/count does not match request")
    if (
        evidence.exec_chain.effective_environment_sha256
        != canonical_sha256([list(item) for item in effective_environment])
        or evidence.exec_chain.effective_environment_count
        != len(effective_environment)
    ):
        reasons.append("effective exec environment digest/count does not match request")
    if evidence.process.cgroup_name != request.process.cgroup_name:
        reasons.append("evidence cgroup identity does not match request")
    if evidence.filesystem.effective_read_only_inputs != request.filesystem.read_only_inputs:
        reasons.append("effective read-only roots do not match request")
    if evidence.filesystem.cwd_private_path != request.filesystem.cwd_private_path:
        reasons.append("effective cwd does not match request")
    if evidence.filesystem.scratch_private_path != request.filesystem.scratch_private_path:
        reasons.append("effective scratch root does not match request")
    if evidence.filesystem.output_private_path != request.filesystem.output_private_path:
        reasons.append("effective output root does not match request")
    if (
        evidence.filesystem.declared_output_allowlist
        != request.filesystem.retained_output_paths
    ):
        reasons.append("declared output allowlist does not match request")
    for name in (
        "scratch_byte_limit",
        "scratch_inode_limit",
        "output_byte_limit",
        "output_inode_limit",
    ):
        if getattr(evidence.filesystem, name) != getattr(request.filesystem, name):
            reasons.append(f"filesystem limit does not match request: {name}")
    if evidence.streams.stdout.limit_bytes != request.streams.stdout_raw_byte_limit:
        reasons.append("stdout limit does not match request")
    if evidence.streams.stderr.limit_bytes != request.streams.stderr_raw_byte_limit:
        reasons.append("stderr limit does not match request")
    if evidence.streams.combined.limit_bytes != request.streams.combined_raw_byte_limit:
        reasons.append("combined stream limit does not match request")
    if evidence.streams.retained_byte_limit != request.streams.retained_byte_limit:
        reasons.append("retained stream limit does not match request")
    observed_identity_present = (
        evidence.process.observed_uid is not None
        or evidence.process.observed_gid is not None
        or evidence.process.observed_uid_tuple is not None
        or evidence.process.observed_gid_tuple is not None
        or evidence.process.observed_supplementary_groups != ()
        or evidence.process.observed_effective_capability_mask is not None
        or evidence.process.observed_no_new_privs is not None
    )
    if observed_identity_present and (
        evidence.process.observed_uid != request.workload.uid
        or evidence.process.observed_gid != request.workload.gid
        or evidence.process.observed_supplementary_groups
        != request.workload.supplementary_groups
        or evidence.process.observed_effective_capability_mask
        != request.workload.effective_capability_mask
        or evidence.process.observed_no_new_privs != request.workload.no_new_privs
        or evidence.process.observed_uid_tuple != (request.workload.uid,) * 4
        or evidence.process.observed_gid_tuple != (request.workload.gid,) * 4
    ):
        reasons.append("observed workload identity does not match request")
    if (
        evidence.process.observed_pids_max is not None
        and evidence.process.observed_pids_max != request.process.max_processes
    ):
        reasons.append("observed pids.max does not match request")
    if evidence.process.termination_grace_ns != request.process.termination_grace_ns:
        reasons.append("observed termination grace does not match request")
    if (
        evidence.filesystem.structured_result_byte_limit
        != request.output.structured_result_byte_limit
        or evidence.filesystem.file_output_byte_limit
        != request.output.file_output_byte_limit
    ):
        reasons.append("result/output limit evidence does not match request")
    scratch_quota = evidence.filesystem.scratch_quota_before_release
    output_quota = evidence.filesystem.output_quota_before_release
    if (
        scratch_quota is not None
        and (
            scratch_quota.byte_ceiling != request.filesystem.scratch_byte_limit
            or scratch_quota.inode_ceiling
            != request.filesystem.scratch_inode_limit
        )
    ):
        reasons.append("scratch pre-release OS quota does not match request")
    if (
        output_quota is not None
        and (
            output_quota.byte_ceiling != request.filesystem.output_byte_limit
            or output_quota.inode_ceiling != request.filesystem.output_inode_limit
        )
    ):
        reasons.append("output pre-release OS quota does not match request")
    for label, actual, expected_value in (
        (
            "scratch byte",
            evidence.filesystem.scratch_observed_byte_ceiling,
            request.filesystem.scratch_byte_limit,
        ),
        (
            "scratch inode",
            evidence.filesystem.scratch_observed_inode_ceiling,
            request.filesystem.scratch_inode_limit,
        ),
        (
            "output byte",
            evidence.filesystem.output_observed_byte_ceiling,
            request.filesystem.output_byte_limit,
        ),
        (
            "output inode",
            evidence.filesystem.output_observed_inode_ceiling,
            request.filesystem.output_inode_limit,
        ),
    ):
        if actual is not None and actual != expected_value:
            reasons.append(f"{label} post-kill OS quota does not match request")
    reasons.extend(_os_payload_correlation_reasons(request, evidence))
    return reasons


def _os_payload_correlation_reasons(
    request: IsolationRequestV1, evidence: ExecutionEvidenceV1
) -> list[str]:
    payloads = {item.event_id: item.payload() for item in evidence.observations}
    exec_payload = payloads.get("exec.ptrace")
    if not isinstance(exec_payload, dict):
        return ["exec.ptrace correlation payload is missing"]
    reasons: list[str] = []

    def decimal_four(name: str) -> tuple[int, ...] | None:
        value = exec_payload.get(name)
        if not isinstance(value, str):
            return None
        try:
            parsed = tuple(int(item) for item in value.split())
        except (ValueError, TypeError):
            return None
        return parsed if len(parsed) == 4 else None

    if decimal_four("uid") != (request.workload.uid,) * 4:
        reasons.append("exec.ptrace UID four-tuple does not match request")
    if decimal_four("gid") != (request.workload.gid,) * 4:
        reasons.append("exec.ptrace GID four-tuple does not match request")
    if (
        exec_payload.get("groups") != ""
        or exec_payload.get("cap_eff") not in {"0", "0000000000000000"}
        or exec_payload.get("no_new_privs") != "1"
    ):
        reasons.append("exec.ptrace privilege payload does not match request")
    exec_identity = (
        exec_payload.get("exec_pid"),
        exec_payload.get("exec_starttime_ticks"),
    )
    if (
        exec_payload.get("exec_cgroup")
        != f"/{request.execution_id}/composition"
        or exec_identity
        not in {
            (item.pid, item.starttime_ticks)
            for item in evidence.process.member_observations
        }
    ):
        reasons.append("exec.ptrace process identity is not in the bound member set")
    return reasons


def validate_execution_evidence_v1(
    request: IsolationRequestV1,
    evidence: object,
) -> EvidenceValidationV1:
    """Validate current-run structure, exact correlation, and completeness.

    This is local corruption and invocation matching.  It is not independent
    attestation and does not provide durable cross-run replay consumption.
    """

    request_validation = validate_isolation_request_v1(request)
    if not request_validation.ok:
        return EvidenceValidationV1(
            EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH,
            tuple(f"request is invalid: {reason}" for reason in request_validation.reasons),
            matching=False,
            complete=False,
        )
    if not isinstance(evidence, ExecutionEvidenceV1):
        return EvidenceValidationV1(
            EvidenceValidationErrorCodeV1.INVALID_EVIDENCE,
            ("evidence must be ExecutionEvidenceV1",),
            matching=False,
            complete=False,
        )
    try:
        structural = _structural_reasons(evidence)
    except (AttributeError, TypeError, ValueError, RecursionError) as exc:
        structural = [f"malformed evidence structure: {type(exc).__name__}"]
    if structural:
        return EvidenceValidationV1(
            EvidenceValidationErrorCodeV1.INVALID_EVIDENCE,
            tuple(structural),
            matching=False,
            complete=False,
        )
    try:
        correlation = _correlation_reasons(request, evidence)
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError) as exc:
        correlation = [f"malformed correlation evidence: {type(exc).__name__}"]
    if correlation:
        return EvidenceValidationV1(
            EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH,
            tuple(correlation),
            matching=False,
            complete=evidence.complete,
        )
    try:
        incomplete = _intrinsic_completeness_reasons(evidence)
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError) as exc:
        incomplete = [f"malformed completeness evidence: {type(exc).__name__}"]
    if incomplete:
        return EvidenceValidationV1(
            EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE,
            tuple(incomplete),
            matching=True,
            complete=False,
        )
    return EvidenceValidationV1(None, (), matching=True, complete=True)
