from __future__ import annotations

import errno
import json
import signal
import stat
from dataclasses import FrozenInstanceError, replace

import pytest

import tool_system.isolated_execution as isolated_execution
from tool_system.isolated_execution.contract import (
    AUDIT_ARCH_X86_64_V1,
    CLONE_NAMESPACE_FLAGS_MASK_V1,
    DENIED_CONTROL_OPERATIONS_V1,
    FCNTL_DENIED_COMMANDS_V1,
    FUTEX_PRIVATE_FLAG_V1,
    PIPE2_DENIED_FLAGS_V1,
    ISOLATION_PROFILE_V1,
    ISOLATION_REQUEST_SCHEMA_V1,
    LINUX_NATIVE_SUPERVISOR_V1,
    MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1,
    MAX_LINUX_PATH_COMPONENTS_V1,
    MAX_PRIVATE_FILESYSTEM_BYTES_V1,
    MAX_PRIVATE_FILESYSTEM_INODES_V1,
    MAX_RAW_STREAM_BYTES_V1,
    MAX_RETAINED_STREAM_BYTES_V1,
    NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1,
    READ_ONLY_ALLOWED_INODE_TYPES_V1,
    READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1,
    REQUIRED_CAPABILITY_SET_SHA256_V1,
    REQUIRED_CAPABILITIES_V1,
    REQUIRED_OBSERVATION_CLASSES_V1,
    SOCKET_DENIAL_FILTER_SHA256_V1,
    SOCKET_DENIAL_FILTER_ROWS_V1,
    SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1,
    BackendProfileV1,
    ExecutableFormatV1,
    ExecutablePolicyV1,
    ExpectedFileIdentityV1,
    ExpectedFileTypeV1,
    FilesystemPolicyV1,
    IsolationRequestErrorCodeV1,
    IsolationRequestV1,
    NetworkModeV1,
    NetworkPolicyV1,
    ObservationClassV1,
    OutputPolicyV1,
    ProcessPolicyV1,
    ReadOnlyRootV1,
    RequestIdentityV1,
    StreamPolicyV1,
    WorkloadIdentityV1,
    X32_SYSCALL_BIT_V1,
    canonical_json_bytes,
    canonical_sha256,
    effective_exec_argv_v1,
    effective_exec_environment_v1,
    validate_isolation_request_v1,
)
from tool_system.isolated_execution.evidence import (
    ISOLATION_EVIDENCE_SCHEMA_V1,
    REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1,
    REQUIRED_MEMFD_SEALS_V1,
    REQUIRED_NETWORK_DENIAL_CLASSES_V1,
    REQUIRED_OBSERVATION_EVENTS_V1,
    REQUIRED_STAGE_DEPENDENCIES_V1,
    STREAM_PIPE_CAPACITY_BYTES_V1,
    CleanupEvidenceV1,
    CorrelationEvidenceV1,
    EvidenceCompletenessV1,
    EvidenceStageStatusV1,
    EvidenceStageV1,
    EvidenceValidationErrorCodeV1,
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
    ProcessEvidenceV1,
    ProcessMemberEvidenceV1,
    SecondaryExecDenialEvidenceV1,
    PrivateMountQuotaEvidenceV1,
    ReadOnlyRootScanEvidenceV1,
    StageDependencyV1,
    StreamCountV1,
    StreamDecodingStatusV1,
    StreamEvidenceV1,
    _build_execution_evidence_v1,
    validate_execution_evidence_v1,
)


def _sha(character: str) -> str:
    return character * 64


def _expected_file(
    *,
    source_path: str,
    private_path: str,
    file_type: ExpectedFileTypeV1,
    device: int,
    inode: int,
    sha256: str,
) -> ExpectedFileIdentityV1:
    return ExpectedFileIdentityV1(
        source_path=source_path,
        private_path=private_path,
        file_type=file_type,
        device=device,
        inode=inode,
        mode=stat.S_IFREG | 0o555,
        size=4096,
        sha256=sha256,
    )


def _valid_request() -> IsolationRequestV1:
    entrypoint = _expected_file(
        source_path="/srv/input/bin/true",
        private_path="/runtime/entrypoint",
        file_type=ExpectedFileTypeV1.ELF,
        device=8,
        inode=101,
        sha256=_sha("1"),
    )
    loader = _expected_file(
        source_path="/srv/input/lib/ld-linux-x86-64.so.2",
        private_path="/runtime/loader",
        file_type=ExpectedFileTypeV1.LOADER,
        device=8,
        inode=102,
        sha256=_sha("2"),
    )
    return IsolationRequestV1(
        schema_version=ISOLATION_REQUEST_SCHEMA_V1,
        execution_id="ts-b02a-0123456789abcdef0123",
        identity=RequestIdentityV1(
            task_sha256=_sha("a"),
            source_sha256=_sha("b"),
            candidate_sha256=_sha("c"),
            workspace_sha256=_sha("d"),
            configuration_sha256=_sha("e"),
            policy_sha256=_sha("f"),
        ),
        filesystem=FilesystemPolicyV1(
            read_only_inputs=(
                ReadOnlyRootV1(
                    source_path="/srv/input",
                    private_path="/inputs/source",
                    device=8,
                    inode=201,
                    mode=stat.S_IFDIR | 0o555,
                ),
            ),
            cwd_private_path="/workspace",
            scratch_private_path="/scratch",
            output_private_path="/output",
            scratch_byte_limit=1_048_576,
            scratch_inode_limit=128,
            output_byte_limit=1_048_576,
            output_inode_limit=128,
            retained_output_paths=("result.json",),
        ),
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.ELF_DYNAMIC,
            entrypoint=entrypoint,
            interpreter=None,
            loader=loader,
            parsed_interpreter_path=loader.private_path,
            argv=(entrypoint.private_path,),
            environment=(("LANG", "C.UTF-8"),),
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
            deadline_monotonic_ns=200_000_000_000,
            termination_grace_ns=1_000_000_000,
            cgroup_name="ts-b02a-0123456789abcdef0123",
            max_processes=64,
        ),
        output=OutputPolicyV1(
            structured_result_byte_limit=262_144,
            file_output_byte_limit=1_048_576,
        ),
    )


def _observed_source(expected: ExpectedFileIdentityV1) -> ObservedFileIdentityV1:
    return ObservedFileIdentityV1(
        path=expected.source_path,
        device=expected.device,
        inode=expected.inode,
        mode=expected.mode,
        size=expected.size,
        sha256=expected.sha256,
    )


def _sealed(
    expected: ExpectedFileIdentityV1, *, device: int, inode: int
) -> ObservedFileIdentityV1:
    return ObservedFileIdentityV1(
        path=expected.private_path,
        device=device,
        inode=inode,
        mode=expected.mode,
        size=expected.size,
        sha256=expected.sha256,
    )


def _actual(
    sealed: ObservedFileIdentityV1, *, observed_path: str
) -> ObservedFileIdentityV1:
    return replace(sealed, path=observed_path)


def _valid_evidence_kwargs(
    request: IsolationRequestV1,
) -> dict[str, object]:
    selected_entrypoint = _observed_source(request.executable.entrypoint)
    sealed_entrypoint = _sealed(
        request.executable.entrypoint, device=1, inode=501
    )
    requested_loader = request.executable.loader
    assert requested_loader is not None
    selected_loader = _observed_source(requested_loader)
    sealed_loader = _sealed(requested_loader, device=1, inode=502)
    effective_argv = request.executable.argv
    effective_environment = request.executable.environment
    cleanup = CleanupEvidenceV1(
        cgroup_populated_zero=True,
        cgroup_removed=True,
        namespace_fds_closed=True,
        mounts_removed=True,
        cwd_root_fds_clear=True,
        processes_gone=True,
        pidfds_exit_observed=True,
        temporary_root_removed=True,
        residue=(),
    )
    zero_stdout = StreamCountV1(0, 0, 0, request.streams.stdout_raw_byte_limit, False)
    zero_stderr = StreamCountV1(0, 0, 0, request.streams.stderr_raw_byte_limit, False)
    zero_combined = StreamCountV1(
        0, 0, 0, request.streams.combined_raw_byte_limit, False
    )
    scratch_quota = PrivateMountQuotaEvidenceV1(
        filesystem_type="tmpfs",
        mount_options=("nodev", "noexec", "nosuid", "rw"),
        byte_ceiling=request.filesystem.scratch_byte_limit,
        inode_ceiling=request.filesystem.scratch_inode_limit,
        fragment_size=4_096,
    )
    output_quota = PrivateMountQuotaEvidenceV1(
        filesystem_type="tmpfs",
        mount_options=("nodev", "noexec", "nosuid", "rw"),
        byte_ceiling=request.filesystem.output_byte_limit,
        inode_ceiling=request.filesystem.output_inode_limit,
        fragment_size=4_096,
    )
    values: dict[str, object] = {
        "correlation": CorrelationEvidenceV1(
            schema_version=ISOLATION_EVIDENCE_SCHEMA_V1,
            profile=ISOLATION_PROFILE_V1,
            execution_id=request.execution_id,
            request_sha256=request.request_sha256,
            **request.identity.to_record(),
            backend_profile=LINUX_NATIVE_SUPERVISOR_V1,
            backend_configuration_sha256=request.identity.configuration_sha256,
            required_capability_set_sha256=REQUIRED_CAPABILITY_SET_SHA256_V1,
            os_name="Linux",
            architecture="x86_64",
            started_monotonic_ns=1_000,
            deadline_monotonic_ns=request.process.deadline_monotonic_ns,
            finished_monotonic_ns=1_000_003_000,
        ),
        "capability_stages": tuple(
            EvidenceStageV1(stage_id, index, EvidenceStageStatusV1.PASS)
            for index, (stage_id, _) in enumerate(
                REQUIRED_STAGE_DEPENDENCIES_V1, start=1
            )
        ),
        "stage_dependencies": tuple(
            StageDependencyV1(stage_id, dependencies)
            for stage_id, dependencies in REQUIRED_STAGE_DEPENDENCIES_V1
        ),
        "observations": (),
        "exec_chain": ExecChainEvidenceV1(
            requested_entrypoint=request.executable.entrypoint,
            selected_entrypoint=selected_entrypoint,
            sealed_entrypoint=sealed_entrypoint,
            actual_entrypoint=_actual(
                sealed_entrypoint, observed_path="/proc/314/exe"
            ),
            requested_interpreter=None,
            selected_interpreter=None,
            sealed_interpreter=None,
            actual_interpreter=None,
            requested_loader=requested_loader,
            selected_loader=selected_loader,
            sealed_loader=sealed_loader,
            actual_loader=_actual(
                sealed_loader, observed_path="/proc/314/map_files/loader"
            ),
            entrypoint_seals=REQUIRED_MEMFD_SEALS_V1,
            interpreter_seals=(),
            loader_seals=REQUIRED_MEMFD_SEALS_V1,
            effective_argv_sha256=canonical_sha256(list(effective_argv)),
            effective_argv_count=len(effective_argv),
            effective_environment_sha256=canonical_sha256(
                [list(item) for item in effective_environment]
            ),
            effective_environment_count=len(effective_environment),
            open_sequence=1,
            seal_sequence=2,
            recheck_sequence=3,
            exec_sequence=4,
            ptrace_exec_sequence=5,
        ),
        "process": ProcessEvidenceV1(
            cgroup_name=request.process.cgroup_name,
            initial_pid=314,
            initial_starttime_ticks=2718,
            initial_pidfd_opened=True,
            observed_uid=request.workload.uid,
            observed_gid=request.workload.gid,
            observed_uid_tuple=(request.workload.uid,) * 4,
            observed_gid_tuple=(request.workload.gid,) * 4,
            observed_supplementary_groups=(),
            observed_effective_capability_mask=0,
            observed_no_new_privs=True,
            observed_pids_max=request.process.max_processes,
            member_observations=(
                ProcessMemberEvidenceV1(
                    pid=314,
                    starttime_ticks=2718,
                    cgroup_path=f"/{request.execution_id}/composition",
                    pidfd_opened=True,
                    identity_revalidated=True,
                    observed_before_grace=True,
                    observed_before_kill=True,
                    pidfd_unreadable_before_kill=True,
                    pidfd_exit_observed=True,
                ),
            ),
            member_count_observed=1,
            all_members_pidfd_bound=True,
            event_classes=("exec", "exit", "exit_stop"),
            secondary_exec_denials=(),
            timeout_triggered=False,
            limit_triggered=False,
            workload_exit_monotonic_ns=1_900,
            timeout_trigger_monotonic_ns=None,
            termination_grace_ns=request.process.termination_grace_ns,
            grace_started_monotonic_ns=2_000,
            grace_finished_monotonic_ns=1_000_002_000,
            force_kill_after_grace=True,
            cgroup_kill_written=True,
            populated_before_kill=1,
            populated_after_cleanup=0,
            pidfd_exit_observed=True,
            survivor_observation_available=True,
            current_execution_survivor_count=0,
        ),
        "filesystem": FilesystemEvidenceV1(
            effective_read_only_inputs=request.filesystem.read_only_inputs,
            read_only_input_scans=tuple(
                ReadOnlyRootScanEvidenceV1(
                    root=root,
                    observed_device=root.device,
                    observed_inode=root.inode,
                    entries_scanned=3,
                    entry_limit=READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1,
                    allowed_inode_types=READ_ONLY_ALLOWED_INODE_TYPES_V1,
                    fd_relative=True,
                    nofollow=True,
                    no_xdev=True,
                    identity_revalidated=True,
                    stable_during_scan=True,
                )
                for root in request.filesystem.read_only_inputs
            ),
            cwd_private_path=request.filesystem.cwd_private_path,
            scratch_private_path=request.filesystem.scratch_private_path,
            output_private_path=request.filesystem.output_private_path,
            scratch_used_bytes=0,
            scratch_used_inodes=0,
            scratch_byte_limit=request.filesystem.scratch_byte_limit,
            scratch_inode_limit=request.filesystem.scratch_inode_limit,
            output_used_bytes=0,
            output_used_inodes=0,
            output_byte_limit=request.filesystem.output_byte_limit,
            output_inode_limit=request.filesystem.output_inode_limit,
            structured_result_bytes=1024,
            structured_result_byte_limit=request.output.structured_result_byte_limit,
            file_output_byte_limit=request.output.file_output_byte_limit,
            quota_observed_before_release=True,
            scratch_quota_before_release=scratch_quota,
            output_quota_before_release=output_quota,
            quota_observed_after_kill=True,
            scratch_observed_byte_ceiling=request.filesystem.scratch_byte_limit,
            scratch_observed_inode_ceiling=request.filesystem.scratch_inode_limit,
            output_observed_byte_ceiling=request.filesystem.output_byte_limit,
            output_observed_inode_ceiling=request.filesystem.output_inode_limit,
            declared_output_allowlist=request.filesystem.retained_output_paths,
            observed_output_paths=(),
            undeclared_output_blocked=True,
            output_parent_directories_nonwritable=True,
            limit_observation=None,
            rejected_boundary_attempts=REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1,
            retained_outputs=(),
            teardown_observed=True,
        ),
        "network": NetworkEvidenceV1(
            namespace_inode=42,
            flags_after_up=1,
            flags_after_down=0,
            operstate_after_up_json=canonical_json_bytes({"value": "unknown"}),
            operstate_after_down_json=canonical_json_bytes({"value": "unknown"}),
            live_endpoint_positive_control=True,
            live_endpoint_denial_control=True,
            inherited_network_fd_absent_at_exec=True,
            seccomp_filter_sha256=SOCKET_DENIAL_FILTER_SHA256_V1,
            socket_denial_errno=errno.EPERM,
            denied_attempt_classes=REQUIRED_NETWORK_DENIAL_CLASSES_V1,
        ),
        "streams": StreamEvidenceV1(
            stdout=zero_stdout,
            stderr=zero_stderr,
            combined=zero_combined,
            retained_byte_limit=request.streams.retained_byte_limit,
            pipe_capacity_bytes=STREAM_PIPE_CAPACITY_BYTES_V1,
            decoding_status=StreamDecodingStatusV1.UTF8_VALID,
            overflow=False,
            observer_loss=False,
        ),
        "completeness": EvidenceCompletenessV1(
            required_observation_classes=REQUIRED_OBSERVATION_CLASSES_V1,
            observed_observation_classes=REQUIRED_OBSERVATION_CLASSES_V1,
            missing_observation_classes=(),
            sequence_gaps=(),
            provider_errors=(),
            observer_errors=(),
            buffer_loss=False,
            teardown_observed=True,
            cleanup=cleanup,
        ),
        "outcome": ExecutionOutcomeV1.SUCCESS,
        "workload_released": True,
        "workload_exit_code": 0,
    }
    chain = values["exec_chain"]
    process = values["process"]
    filesystem = values["filesystem"]
    network = values["network"]
    streams = values["streams"]
    assert isinstance(chain, ExecChainEvidenceV1)
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(filesystem, FilesystemEvidenceV1)
    assert isinstance(network, NetworkEvidenceV1)
    assert isinstance(streams, StreamEvidenceV1)
    cgroup_root = f"/sys/fs/cgroup/{request.execution_id}"
    cgroup_paths = [
        cgroup_root,
        f"{cgroup_root}/composition",
        f"{cgroup_root}/combined-stream",
        f"{cgroup_root}/timeout",
    ]
    namespace_ids = {
        name: f"{name}:[2]" for name in ("mnt", "pid", "net", "ipc", "uts")
    }
    parent_namespace_ids = {
        name: f"{name}:[1]" for name in ("mnt", "pid", "net", "ipc", "uts")
    }
    seccomp_controls = {
        "network": {
            name: errno.EPERM
            for name in ("dns", "ipv4", "ipv6", "namespace_bridge", "netlink", "packet")
        },
        "filter_syscalls": {
            name: errno.EPERM
            for name, _ in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1
        },
        "clone_control_flags_errno": errno.EPERM,
        "clone_flag_controls": {
            "namespace": errno.EPERM,
            "thread": errno.EPERM,
            "untraced": errno.EPERM,
            "vm": errno.EPERM,
            "fs": errno.EPERM,
            "files": errno.EPERM,
            "sighand": errno.EPERM,
        },
        "ordinary_fork_positive": True,
        "ordinary_vfork_positive": True,
        "x32_kill_control": True,
        "native_syscall_exclusive_ceiling": (
            NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
        ),
        "ceiling_syscall_errno": errno.EPERM,
        "fcntl_command_controls": {
            name: errno.EPERM for name, _ in FCNTL_DENIED_COMMANDS_V1
        },
        "futex_controls": {
            "shared_wake_errno": errno.EPERM,
            "private_wake_result": 0,
        },
        "pipe2_controls": {
            "direct_errno": errno.EPERM,
            "notification_errno": errno.EPERM,
            "ordinary": True,
        },
        "control_scope": "outer_supervisor_pre_workload_release",
        "observed_filter_sha256": SOCKET_DENIAL_FILTER_SHA256_V1,
    }
    payloads: dict[str, dict[str, object]] = {
        "host.gate": {
            "os": "Linux",
            "architecture": "x86_64",
            "effective_uid": 0,
            "cgroup_v2": True,
            "openat2": True,
            "pidfd": True,
            "monotonic": True,
            "fallback": False,
            "core_pipe_helper_absent": True,
            "cgroup2_gate": {
                "filesystem_type": "cgroup2",
                "mount_root": "/",
                "mountpoint": "/sys/fs/cgroup",
                "current_unified_cgroup": "/",
                "mount_id": 42,
                "writable": True,
            },
            "mandatory_abi_control": {
                "pidfd_send_signal": True,
                "ptrace_exec_event": True,
                "execveat": True,
                "synthetic_only": True,
            },
        },
        "identity.seal": {
            "entrypoint": {
                "source_identity": chain.selected_entrypoint.to_record(),
                "sealed_identity": chain.sealed_entrypoint.to_record(),
            },
            "interpreter": None,
            "loader": {
                "source_identity": chain.selected_loader.to_record(),
                "sealed_identity": chain.sealed_loader.to_record(),
            },
            "seals": list(REQUIRED_MEMFD_SEALS_V1),
        },
        "cgroup.claim": {
            "exact_paths": cgroup_paths,
            "identity_count": 4,
            "observed_pids_max": process.observed_pids_max,
            "nonce_sha256": _sha("9"),
        },
        "namespace.setup": {
            "namespace_ids": namespace_ids,
            "parent_namespace_ids": parent_namespace_ids,
            "all_distinct_from_parent": True,
            "host_mounts_during_live_namespace": [],
            "private_mount_propagation": True,
        },
        "filesystem.gate": {
            "rejected_boundary_attempts": list(
                REQUIRED_FILESYSTEM_DENIAL_CLASSES_V1
            ),
            "quota_controls": {"byte_enospc": True, "inode_enospc": True},
            "private_quota_observations": {
                "observed_before_release": True,
                "scratch": filesystem.scratch_quota_before_release.to_record(),
                "output": filesystem.output_quota_before_release.to_record(),
            },
            "read_only_mount_observations": [
                {
                    "target": request.filesystem.read_only_inputs[0].private_path,
                    "mount_options": ["nodev", "nosuid", "ro"],
                    "statvfs_read_only": True,
                    "write_denial_errno": errno.EROFS,
                    "device": request.filesystem.read_only_inputs[0].device,
                    "inode": request.filesystem.read_only_inputs[0].inode,
                    "mode": request.filesystem.read_only_inputs[0].mode,
                    "tree_control": {
                        key: value
                        for key, value in filesystem.read_only_input_scans[
                            0
                        ].to_record().items()
                        if key != "root"
                    },
                },
                {
                    "target": chain.sealed_entrypoint.path,
                    "mount_options": ["nodev", "nosuid", "ro"],
                    "statvfs_read_only": True,
                    "write_denial_errno": errno.EROFS,
                    "device": chain.sealed_entrypoint.device,
                    "inode": chain.sealed_entrypoint.inode,
                    "mode": chain.sealed_entrypoint.mode,
                    "tree_control": None,
                },
                {
                    "target": chain.sealed_loader.path,
                    "mount_options": ["nodev", "nosuid", "ro"],
                    "statvfs_read_only": True,
                    "write_denial_errno": errno.EROFS,
                    "device": chain.sealed_loader.device,
                    "inode": chain.sealed_loader.inode,
                    "mode": chain.sealed_loader.mode,
                    "tree_control": None,
                },
            ],
            "read_only_input_scans": [
                item.to_record() for item in filesystem.read_only_input_scans
            ],
            "declared_output_control": {
                "declared_output_allowlist": list(
                    filesystem.declared_output_allowlist
                ),
                "undeclared_output_blocked": True,
                "output_parent_directories_nonwritable": True,
                "creation_denial_errno": errno.EACCES,
            },
            "provider_view_controls": {
                "proc_view": {
                    "absent": True,
                    "access_errno": errno.ENOENT,
                    "private_pid_namespace": True,
                    "provider_sensitive_paths_denied": True,
                    "provider_private_access_errno": errno.EACCES,
                },
                "sys_view": {"absent": True, "access_errno": errno.ENOENT},
                "device_view": {"absent": True, "access_errno": errno.ENOENT},
            },
            "private_root_mount_observation": {
                "filesystem_type": "tmpfs",
                "mount_options": ["nodev", "nosuid", "rw"],
                "mode": stat.S_IFDIR | 0o755,
                "root_device_changed": True,
                "old_root_removed": True,
            },
        },
        "network.gate": {
            "network": {
                "namespace_inode": network.namespace_inode,
                "flags_after_up": network.flags_after_up,
                "flags_after_down": network.flags_after_down,
                "operstate_after_up": {"value": "unknown"},
                "operstate_after_down": {"value": "unknown"},
                "positive": True,
                "negative": True,
                "denial_errno": errno.ENETUNREACH,
            },
            "socket_denial_errno": errno.EPERM,
            "seccomp_filter_sha256": network.seccomp_filter_sha256,
            "seccomp_controls": seccomp_controls,
        },
        "stream.control": {
            "mode": "stream",
            "observed_bytes": 12_288,
            "monotonic_elapsed_ns": 1,
            "populated_before_kill": 1,
            "freeze_positive_control": True,
            "unfreeze_positive_control": True,
            "cgroup_kill_written": True,
            "pidfd_exit_observed": True,
            "populated_zero": True,
        },
        "timeout.control": {
            "mode": "timeout",
            "observed_bytes": 0,
            "monotonic_elapsed_ns": 25_000_000,
            "populated_before_kill": 1,
            "freeze_positive_control": True,
            "unfreeze_positive_control": True,
            "cgroup_kill_written": True,
            "pidfd_exit_observed": True,
            "populated_zero": True,
        },
        "deadline.release_recheck": {
            "release_recheck_monotonic_ns": 1_500,
            "deadline_monotonic_ns": request.process.deadline_monotonic_ns,
            "termination_grace_ns": request.process.termination_grace_ns,
            "eligible": True,
        },
        "workload.release": {"released": True},
        "exec.ptrace": {
            "kind": "ptrace_exec",
            "actual_entrypoint": chain.actual_entrypoint.to_record(),
            "actual_interpreter": None,
            "actual_loader": chain.actual_loader.to_record(),
            "loader_map_identity_match": True,
            "uid": "65534 65534 65534 65534",
            "gid": "65534 65534 65534 65534",
            "groups": "",
            "cap_eff": "0000000000000000",
            "no_new_privs": "1",
            "fd_set": [0, 1, 2],
            "stdio_pipe_identities": {
                str(descriptor): {
                    "device": 1,
                    "inode": 700 + descriptor,
                    "mode": stat.S_IFIFO | 0o600,
                }
                for descriptor in (0, 1, 2)
            },
            "stdio_provider_match": True,
            "file_size_soft_limit": max(
                request.filesystem.scratch_byte_limit,
                request.output.file_output_byte_limit,
            ),
            "file_size_hard_limit": max(
                request.filesystem.scratch_byte_limit,
                request.output.file_output_byte_limit,
            ),
            "core_soft_limit": 0,
            "core_hard_limit": 0,
            "seccomp_mode": "2",
            "seccomp_filters": "2",
            "baseline_seccomp_filters": 1,
            "seccomp_filter_delta": 1,
            "inherited_network_fd_absent": True,
            "effective_argv_sha256": chain.effective_argv_sha256,
            "effective_argv_count": chain.effective_argv_count,
            "effective_environment_sha256": (
                chain.effective_environment_sha256
            ),
            "effective_environment_count": chain.effective_environment_count,
            "exec_pid": 314,
            "namespace_exec_pid": 2,
            "exec_starttime_ticks": 2718,
            "exec_cgroup": f"/{request.execution_id}/composition",
            "secondary_exec_policy": {
                "execve": 59,
                "execveat": 322,
                "ptrace_entry_denial": True,
                "ptrace_event_exec_backstop": True,
            },
        },
        "process.contain": {
            "initial_pid": process.initial_pid,
            "initial_starttime_ticks": process.initial_starttime_ticks,
            "initial_pidfd_opened": process.initial_pidfd_opened,
            "member_observations": [
                item.to_record() for item in process.member_observations
            ],
            "member_count": process.member_count_observed,
            "observed_pids_max": process.observed_pids_max,
            "all_members_pidfd_bound": process.all_members_pidfd_bound,
            "workload_exit_monotonic_ns": process.workload_exit_monotonic_ns,
            "timeout_trigger_monotonic_ns": process.timeout_trigger_monotonic_ns,
            "limit_triggered": process.limit_triggered,
            "timeout_triggered": process.timeout_triggered,
            "grace_started_monotonic_ns": process.grace_started_monotonic_ns,
            "grace_finished_monotonic_ns": process.grace_finished_monotonic_ns,
            "force_kill_after_grace": True,
            "cgroup_kill_written": True,
            "populated_before_kill": 1,
            "populated_after_kill": 0,
            "pidfd_exit_observed": True,
            "survivor_count": 0,
            "event_classes": list(process.event_classes),
            "secondary_exec_denials": [
                item.to_record() for item in process.secondary_exec_denials
            ],
            "retained_outputs": [
                item.to_record() for item in filesystem.retained_outputs
            ],
            "workload_exit_code": values["workload_exit_code"],
            "quota_observed_after_kill": True,
            "scratch_observed_byte_ceiling": filesystem.scratch_observed_byte_ceiling,
            "scratch_observed_inode_ceiling": filesystem.scratch_observed_inode_ceiling,
            "output_observed_byte_ceiling": filesystem.output_observed_byte_ceiling,
            "output_observed_inode_ceiling": filesystem.output_observed_inode_ceiling,
            "scratch_used_bytes": filesystem.scratch_used_bytes,
            "scratch_used_inodes": filesystem.scratch_used_inodes,
            "output_used_bytes": filesystem.output_used_bytes,
            "output_used_inodes": filesystem.output_used_inodes,
            "declared_output_allowlist": list(
                filesystem.declared_output_allowlist
            ),
            "observed_output_paths": list(filesystem.observed_output_paths),
            "undeclared_output_blocked": True,
            "output_parent_directories_nonwritable": True,
            "filesystem_limit_observation": None,
        },
        "streams.final": {
            "raw_bytes": {"stdout": 0, "stderr": 0},
            "combined_raw_bytes": 0,
            "retained_bytes": {"stdout": 0, "stderr": 0},
            "discarded_bytes": {"stdout": 0, "stderr": 0},
            "trigger": None,
            "observer_loss": False,
            "decoding_status": "utf8_valid",
            "pipe_capacity_bytes": STREAM_PIPE_CAPACITY_BYTES_V1,
        },
        "cleanup.final": {
            "cgroup_release": {
                "exact_paths": cgroup_paths,
                "released_paths": list(reversed(cgroup_paths)),
                "populated_zero": True,
                "failures": [],
            },
            "mounts": [],
            "process_residue": [],
            "temporary_root_removed": True,
            "pidfd_exit_observed": True,
            "failures": [],
        },
    }
    values["observations"] = tuple(
        OSObservationV1.from_payload(
            sequence=index,
            observation_class=observation_class,
            event_id=event_id,
            os_source=os_source,
            monotonic_ns=1_000 + index,
            payload={"execution_id": request.execution_id, **payloads[event_id]},
        )
        for index, (event_id, observation_class, os_source) in enumerate(
            REQUIRED_OBSERVATION_EVENTS_V1, start=1
        )
    )
    return values


def _valid_evidence(request: IsolationRequestV1) -> ExecutionEvidenceV1:
    return _build_execution_evidence_v1(**_valid_evidence_kwargs(request))  # type: ignore[arg-type]


def _update_observation(
    kwargs: dict[str, object],
    event_id: str,
    updates: dict[str, object],
    *,
    monotonic_ns: int | None = None,
) -> None:
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    updated: list[OSObservationV1] = []
    for observation in observations:
        if observation.event_id != event_id:
            updated.append(observation)
            continue
        payload = observation.payload()
        assert isinstance(payload, dict)
        payload.update(updates)
        updated.append(
            OSObservationV1.from_payload(
                sequence=observation.sequence,
                observation_class=observation.observation_class,
                event_id=observation.event_id,
                os_source=observation.os_source,
                monotonic_ns=(
                    observation.monotonic_ns
                    if monotonic_ns is None
                    else monotonic_ns
                ),
                payload=payload,
            )
        )
    kwargs["observations"] = tuple(updated)


def _set_immediate_limit_teardown(kwargs: dict[str, object]) -> None:
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    started = process.grace_started_monotonic_ns
    assert started is not None
    kwargs["process"] = replace(
        process,
        grace_finished_monotonic_ns=started,
    )
    kwargs["workload_exit_code"] = None
    _update_observation(
        kwargs,
        "process.contain",
        {
            "grace_started_monotonic_ns": started,
            "grace_finished_monotonic_ns": started,
            "workload_exit_code": None,
        },
    )


def _drop_observation(kwargs: dict[str, object], event_id: str) -> None:
    observations = kwargs["observations"]
    completeness = kwargs["completeness"]
    assert isinstance(observations, tuple)
    assert isinstance(completeness, EvidenceCompletenessV1)
    remaining = tuple(
        replace(item, sequence=index)
        for index, item in enumerate(
            (item for item in observations if item.event_id != event_id), start=1
        )
    )
    observed_classes = tuple(
        item
        for item in REQUIRED_OBSERVATION_CLASSES_V1
        if any(obs.observation_class is item for obs in remaining)
    )
    missing_classes = tuple(
        item
        for item in REQUIRED_OBSERVATION_CLASSES_V1
        if item not in observed_classes
    )
    kwargs["observations"] = remaining
    kwargs["completeness"] = replace(
        completeness,
        observed_observation_classes=observed_classes,
        missing_observation_classes=missing_classes,
    )


def test_valid_request_is_immutable_canonical_and_has_no_fallback() -> None:
    request = _valid_request()

    assert validate_isolation_request_v1(request).ok
    assert request.backend_profile is BackendProfileV1.LINUX_NATIVE_SUPERVISOR
    assert list(BackendProfileV1) == [BackendProfileV1.LINUX_NATIVE_SUPERVISOR]
    assert request.to_record()["request_sha256"] == request.request_sha256
    assert len(request.request_sha256) == 64
    assert canonical_json_bytes(request.canonical_record()) == canonical_json_bytes(
        request.canonical_record()
    )
    assert "fallback" not in json.dumps(request.to_record()).lower()
    with pytest.raises(FrozenInstanceError):
        request.execution_id = "changed"  # type: ignore[misc]


def test_seccomp_identity_freezes_full_control_surface_and_clone_rule() -> None:
    assert {
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
        "native_syscall_abi_ceiling_denial",
        "core_pipe_helper_gate",
        "zero_core_rlimit",
        "historical_pidfd_member_ack",
        "stream_pipe_capacity_mutation_denial",
        "packet_pipe_denial",
    }.issubset(REQUIRED_CAPABILITIES_V1)
    assert {
        "core_dump_control",
        "anonymous_memory_file_control",
        "filesystem_lock_and_lease_control",
        "filesystem_global_sync_control",
        "filesystem_ioctl_control",
        "shared_futex_control",
        "cross_process_memory_barrier_control",
        "host_uid_scope_priority_control",
        "host_system_perf_event_control",
        "filesystem_xattr_control",
        "keyring_control",
        "resource_limit_control",
        "secondary_exec_control",
        "stream_pipe_capacity_control",
        "packet_pipe_control",
    }.issubset(DENIED_CONTROL_OPERATIONS_V1)
    assert tuple(name for name, _ in SOCKET_DENIAL_UNCONDITIONAL_SYSCALLS_V1) == (
        "socket",
        "socketpair",
        "ptrace",
        "process_vm_readv",
        "process_vm_writev",
        "mount",
        "umount2",
        "pivot_root",
        "unshare",
        "setns",
        "bpf",
        "perf_event_open",
        "open_tree",
        "open_tree_attr",
        "move_mount",
        "fsopen",
        "fsconfig",
        "fsmount",
        "fspick",
        "mount_setattr",
        "clone3",
        "io_setup",
        "io_destroy",
        "io_getevents",
        "io_submit",
        "io_cancel",
        "io_pgetevents",
        "io_uring_setup",
        "add_key",
        "request_key",
        "keyctl",
        "setrlimit",
        "prlimit64",
        "memfd_create",
        "memfd_secret",
        "setxattr",
        "lsetxattr",
        "fsetxattr",
        "setxattrat",
        "removexattr",
        "lremovexattr",
        "fremovexattr",
        "removexattrat",
        "file_setattr",
        "flock",
        "sync",
        "syncfs",
        "quotactl",
        "quotactl_fd",
        "futex_waitv",
        "futex_wake",
        "futex_wait",
        "futex_requeue",
        "membarrier",
        "ioctl",
        "getpriority",
        "setpriority",
        "ioprio_set",
        "ioprio_get",
    )
    assert FCNTL_DENIED_COMMANDS_V1 == (
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
    assert CLONE_NAMESPACE_FLAGS_MASK_V1 == 0x7E830F80
    assert FUTEX_PRIVATE_FLAG_V1 == 0x80
    assert PIPE2_DENIED_FLAGS_V1 == (
        ("O_DIRECT", 0x4000),
        ("O_NOTIFICATION_PIPE", 0x80),
    )
    assert X32_SYSCALL_BIT_V1 == 0x40000000
    assert NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1 == 470
    assert SOCKET_DENIAL_FILTER_ROWS_V1[:8] == (
        (0x20, 0, 0, 4),
        (0x15, 1, 0, AUDIT_ARCH_X86_64_V1),
        (0x06, 0, 0, 0x80000000),
        (0x20, 0, 0, 0),
        (0x45, 0, 1, X32_SYSCALL_BIT_V1),
        (0x06, 0, 0, 0x80000000),
        (0x35, 0, 1, NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1),
        (0x06, 0, 0, 0x00050001),
    )
    expected_conditional_tail = (
        (0x15, 0, 3, 202),
        (0x20, 0, 0, 24),
        (0x45, 1, 0, FUTEX_PRIVATE_FLAG_V1),
        (0x06, 0, 0, 0x00050001),
        (0x20, 0, 0, 0),
        (0x15, 0, 5, 293),
        (0x20, 0, 0, 24),
        (0x45, 0, 1, PIPE2_DENIED_FLAGS_V1[0][1]),
        (0x06, 0, 0, 0x00050001),
        (0x45, 0, 1, PIPE2_DENIED_FLAGS_V1[1][1]),
        (0x06, 0, 0, 0x00050001),
        (0x20, 0, 0, 0),
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
    assert SOCKET_DENIAL_FILTER_ROWS_V1[-len(expected_conditional_tail) :] == (
        expected_conditional_tail
    )
    assert SOCKET_DENIAL_FILTER_SHA256_V1 == canonical_sha256(
        {
            "version": "tool-system-seccomp-cbpf-v1",
            "native_syscall_exclusive_ceiling_x86_64": (
                NATIVE_SYSCALL_EXCLUSIVE_CEILING_X86_64_V1
            ),
            "rows": [list(row) for row in SOCKET_DENIAL_FILTER_ROWS_V1],
        }
    )


def test_expected_exec_chain_modes_are_usable_by_the_dropped_identity() -> None:
    request = _valid_request()
    for field_name in ("entrypoint", "loader"):
        selected = getattr(request.executable, field_name)
        assert isinstance(selected, ExpectedFileIdentityV1)
        forged = replace(selected, mode=stat.S_IFREG | 0o444)
        executable = replace(request.executable, **{field_name: forged})
        validation = validate_isolation_request_v1(
            replace(request, executable=executable)
        )
        assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
        assert any("unprivileged workload" in reason for reason in validation.reasons)

    set_id = replace(
        request.executable.entrypoint,
        mode=request.executable.entrypoint.mode | stat.S_ISUID,
    )
    validation = validate_isolation_request_v1(
        replace(
            request,
            executable=replace(request.executable, entrypoint=set_id),
        )
    )
    assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
    assert any("set-id" in reason for reason in validation.reasons)

    script = _expected_file(
        source_path="/srv/input/task.py",
        private_path="/runtime/script",
        file_type=ExpectedFileTypeV1.SCRIPT,
        device=8,
        inode=301,
        sha256=_sha("3"),
    )
    interpreter = _expected_file(
        source_path="/srv/input/bin/python3",
        private_path="/runtime/interpreter",
        file_type=ExpectedFileTypeV1.INTERPRETER,
        device=8,
        inode=302,
        sha256=_sha("4"),
    )
    script_request = replace(
        request,
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.SCRIPT,
            entrypoint=script,
            interpreter=interpreter,
            loader=request.executable.loader,
            parsed_interpreter_path=interpreter.private_path,
            argv=(script.private_path,),
            environment=(),
        ),
    )
    unreadable_script = replace(script, mode=stat.S_IFREG | 0o111)
    validation = validate_isolation_request_v1(
        replace(
            script_request,
            executable=replace(
                script_request.executable,
                entrypoint=unreadable_script,
            ),
        )
    )
    assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
    assert any("readable" in reason for reason in validation.reasons)

    nonexecutable_interpreter = replace(
        interpreter,
        mode=stat.S_IFREG | 0o444,
    )
    validation = validate_isolation_request_v1(
        replace(
            script_request,
            executable=replace(
                script_request.executable,
                interpreter=nonexecutable_interpreter,
            ),
        )
    )
    assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
    assert any("executable" in reason for reason in validation.reasons)


def test_expected_exec_chain_sizes_cover_the_minimum_parseable_headers() -> None:
    request = _valid_request()
    for field_name in ("entrypoint", "loader"):
        selected = getattr(request.executable, field_name)
        assert isinstance(selected, ExpectedFileIdentityV1)
        too_short = replace(selected, size=63)
        validation = validate_isolation_request_v1(
            replace(
                request,
                executable=replace(request.executable, **{field_name: too_short}),
            )
        )
        assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
        assert any("64 bytes" in reason for reason in validation.reasons)

        boundary = replace(selected, size=64)
        assert validate_isolation_request_v1(
            replace(
                request,
                executable=replace(request.executable, **{field_name: boundary}),
            )
        ).ok

    script = _expected_file(
        source_path="/srv/input/task.py",
        private_path="/runtime/script",
        file_type=ExpectedFileTypeV1.SCRIPT,
        device=8,
        inode=301,
        sha256=_sha("3"),
    )
    interpreter = _expected_file(
        source_path="/srv/input/bin/python3",
        private_path="/runtime/interpreter",
        file_type=ExpectedFileTypeV1.INTERPRETER,
        device=8,
        inode=302,
        sha256=_sha("4"),
    )
    script_request = replace(
        request,
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.SCRIPT,
            entrypoint=script,
            interpreter=interpreter,
            loader=request.executable.loader,
            parsed_interpreter_path=interpreter.private_path,
            argv=(script.private_path,),
            environment=(),
        ),
    )
    assert validate_isolation_request_v1(
        replace(
            script_request,
            executable=replace(
                script_request.executable,
                entrypoint=replace(script, size=4),
            ),
        )
    ).ok
    validation = validate_isolation_request_v1(
        replace(
            script_request,
            executable=replace(
                script_request.executable,
                entrypoint=replace(script, size=3),
            ),
        )
    )
    assert validation.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
    assert any("4 bytes" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    [
        (
            lambda value: replace(value, schema_version="wrong"),
            IsolationRequestErrorCodeV1.INVALID_REQUEST,
        ),
        (
            lambda value: replace(value, backend_profile="ordinary_host"),
            IsolationRequestErrorCodeV1.CAPABILITY_MISMATCH,
        ),
        (
            lambda value: replace(value, required_capability_set_sha256=_sha("0")),
            IsolationRequestErrorCodeV1.CAPABILITY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                identity=replace(value.identity, policy_sha256="A" * 64),
            ),
            IsolationRequestErrorCodeV1.IDENTITY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                filesystem=replace(
                    value.filesystem,
                    read_only_inputs=(
                        replace(
                            value.filesystem.read_only_inputs[0],
                            source_path="/proc",
                        ),
                    ),
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                executable=replace(
                    value.executable,
                    environment=(("PATH", "/tmp"),),
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                executable=replace(
                    value.executable,
                    entrypoint=replace(
                        value.executable.entrypoint,
                        source_path="/outside/tool",
                    ),
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                executable=replace(
                    value.executable,
                    parsed_interpreter_path=value.executable.loader.source_path,
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                executable=replace(
                    value.executable,
                    entrypoint=replace(
                        value.executable.entrypoint,
                        private_path="/scratch/tool",
                    ),
                    argv=("/scratch/tool",),
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                executable=replace(
                    value.executable,
                    environment=(("MALFORMED",),),  # type: ignore[arg-type]
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                workload=replace(value.workload, effective_capability_mask=1),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                network=replace(value.network, loopback_admin_up=True),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                streams=replace(value.streams, continuous_drain=False),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                process=replace(value.process, cgroup_name="different"),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
        (
            lambda value: replace(
                value,
                output=replace(
                    value.output,
                    required_observation_classes=(ObservationClassV1.CLEANUP,),
                ),
            ),
            IsolationRequestErrorCodeV1.POLICY_MISMATCH,
        ),
    ],
)
def test_request_validation_rejects_every_core_weakening(
    mutation, error_code: IsolationRequestErrorCodeV1
) -> None:
    result = validate_isolation_request_v1(mutation(_valid_request()))

    assert not result.ok
    assert result.error_code is error_code
    assert result.reasons


def test_request_validation_is_total_for_malformed_nested_values() -> None:
    request = _valid_request()
    malformed = (
        replace(
            request,
            executable=replace(
                request.executable,
                entrypoint=replace(request.executable.entrypoint, source_path=7),
            ),
        ),
        replace(
            request,
            filesystem=replace(request.filesystem, read_only_inputs=object()),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                read_only_inputs=(request.filesystem.read_only_inputs[0], 7),
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                retained_output_paths=([],),
            ),
        ),
        replace(
            request,
            executable=replace(request.executable, argv=("\ud800",)),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                environment=(("LANG", "\ud800"),),
            ),
        ),
        replace(
            request,
            filesystem=replace(request.filesystem, output_private_path="//output"),
        ),
        replace(
            request,
            filesystem=replace(request.filesystem, scratch_private_path="///"),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                entrypoint=replace(
                    request.executable.entrypoint, inode=10**5_000
                ),
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem, cwd_private_path="/scratch/work"
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem, cwd_private_path="/inputs/source/work"
            ),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                loader=replace(
                    request.executable.loader,
                    private_path="/runtime/entrypoint/loader",
                ),
            ),
        ),
    )

    for value in malformed:
        result = validate_isolation_request_v1(value)
        assert not result.ok
        assert result.reasons


def test_request_bounds_memfd_inputs_paths_pages_and_result_record() -> None:
    request = _valid_request()
    oversized_identity = replace(
        request.executable.entrypoint,
        size=64 * 1024 * 1024 + 1,
    )
    cases = (
        replace(
            request,
            executable=replace(request.executable, entrypoint=oversized_identity),
        ),
        replace(
            request,
            filesystem=replace(request.filesystem, scratch_byte_limit=4_097),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                retained_output_paths=tuple(
                    f"result-{index}.json" for index in range(65)
                ),
            ),
        ),
        replace(
            request,
            output=replace(request.output, structured_result_byte_limit=262_143),
        ),
        replace(
            request,
            output=replace(request.output, file_output_byte_limit=524_288),
        ),
        replace(
            request,
            process=replace(request.process, max_processes=257),
        ),
        replace(
            request,
            process=replace(request.process, max_processes=2),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                scratch_byte_limit=MAX_PRIVATE_FILESYSTEM_BYTES_V1 + 4_096,
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                output_inode_limit=MAX_PRIVATE_FILESYSTEM_INODES_V1 + 1,
            ),
        ),
        replace(
            request,
            streams=replace(
                request.streams,
                stdout_raw_byte_limit=MAX_RAW_STREAM_BYTES_V1 + 1,
            ),
        ),
        replace(
            request,
            streams=replace(
                request.streams,
                retained_byte_limit=MAX_RETAINED_STREAM_BYTES_V1 + 1,
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                retained_output_paths=("nested", "nested/file.json"),
            ),
        ),
    )

    for value in cases:
        validation = validate_isolation_request_v1(value)
        assert not validation.ok
        assert validation.reasons


def test_process_maximum_includes_provider_supervisors_and_workload_union() -> None:
    request = _valid_request()
    minimum = replace(
        request,
        process=replace(request.process, max_processes=3),
    )
    below_minimum = replace(
        request,
        process=replace(request.process, max_processes=2),
    )

    assert validate_isolation_request_v1(minimum).ok
    validation = validate_isolation_request_v1(below_minimum)
    assert not validation.ok
    assert any("two provider supervisors" in reason for reason in validation.reasons)
    assert minimum.request_sha256 != below_minimum.request_sha256


@pytest.mark.parametrize(
    ("retained_paths", "minimum_inodes"),
    (
        ((), 1),
        (("first", "second"), 3),
        (("shared/first", "shared/second"), 4),
        (("one/two/three/result",), 5),
    ),
)
def test_output_inode_limit_covers_precreated_allowlist_layout(
    retained_paths: tuple[str, ...],
    minimum_inodes: int,
) -> None:
    request = _valid_request()
    exact = replace(
        request,
        filesystem=replace(
            request.filesystem,
            retained_output_paths=retained_paths,
            output_inode_limit=minimum_inodes,
        ),
    )
    below = replace(
        exact,
        filesystem=replace(
            exact.filesystem,
            output_inode_limit=minimum_inodes - 1,
        ),
    )

    assert validate_isolation_request_v1(exact).ok
    validation = validate_isolation_request_v1(below)
    assert not validation.ok
    if retained_paths:
        assert any("cannot pre-create" in reason for reason in validation.reasons)
    else:
        assert any("positive" in reason for reason in validation.reasons)


def test_linux_path_limits_include_nul_and_component_bounds() -> None:
    request = _valid_request()
    maximum_absolute = "/srv/input/" + "/".join(
        ["a" * 255] * 15 + ["b" * 244]
    )
    overlong_absolute = "/srv/input/" + "/".join(
        ["a" * 255] * 15 + ["b" * 245]
    )
    maximum_relative = "/".join(["a" * 255] * 16)
    overlong_relative = "/".join(["a" * 254] * 16 + ["b" * 16])
    assert len(maximum_absolute.encode("utf-8")) == 4_095
    assert len(overlong_absolute.encode("utf-8")) == 4_096
    assert len(maximum_relative.encode("utf-8")) == 4_095
    assert len(overlong_relative.encode("utf-8")) == 4_096

    valid = replace(
        request,
        filesystem=replace(
            request.filesystem, retained_output_paths=(maximum_relative,)
        ),
        executable=replace(
            request.executable,
            entrypoint=replace(
                request.executable.entrypoint, source_path=maximum_absolute
            ),
        ),
    )
    assert validate_isolation_request_v1(valid).ok

    for invalid in (
        replace(
            request,
            executable=replace(
                request.executable,
                entrypoint=replace(
                    request.executable.entrypoint, source_path=overlong_absolute
                ),
            ),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                entrypoint=replace(
                    request.executable.entrypoint,
                    source_path="/srv/input/" + "a" * 256,
                ),
            ),
        ),
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                retained_output_paths=(overlong_relative,),
            ),
        ),
    ):
        validation = validate_isolation_request_v1(invalid)
        assert not validation.ok
        assert validation.reasons


def test_linux_path_depth_is_capped_before_backend_tree_operations() -> None:
    request = _valid_request()
    maximum_depth = "/".join("a" for _ in range(MAX_LINUX_PATH_COMPONENTS_V1))
    excessive_depth = maximum_depth + "/a"
    valid = replace(
        request,
        filesystem=replace(
            request.filesystem,
            retained_output_paths=(maximum_depth,),
        ),
    )
    validation = validate_isolation_request_v1(valid)
    assert validation.ok
    assert len(valid.request_sha256) == 64

    invalid = replace(
        request,
        filesystem=replace(
            request.filesystem,
            retained_output_paths=(excessive_depth,),
        ),
    )
    validation = validate_isolation_request_v1(invalid)
    assert not validation.ok
    assert any("safe relative paths" in reason for reason in validation.reasons)


@pytest.mark.parametrize("control", ("\n", "\r", "\t", "\x1f", "\x7f"))
def test_request_paths_argv_and_environment_reject_control_characters(
    control: str,
) -> None:
    request = _valid_request()
    invalid_values = (
        replace(
            request,
            filesystem=replace(
                request.filesystem,
                retained_output_paths=(f"result{control}.json",),
            ),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                argv=(request.executable.entrypoint.private_path, f"arg{control}"),
            ),
        ),
        replace(
            request,
            executable=replace(
                request.executable,
                environment=(("LANG", f"C{control}"),),
            ),
        ),
    )
    for invalid in invalid_values:
        validation = validate_isolation_request_v1(invalid)
        assert not validation.ok
        assert validation.error_code is IsolationRequestErrorCodeV1.POLICY_MISMATCH


def test_oversized_argv_and_environment_tuples_are_not_iterated() -> None:
    class IterationBombTuple(tuple):
        def __iter__(self):
            raise AssertionError("oversized tuple must not be traversed")

    request = _valid_request()
    oversized_argv = IterationBombTuple(("x",) * 1_025)
    oversized_environment = IterationBombTuple((("A", "B"),) * 129)
    for executable in (
        replace(request.executable, argv=oversized_argv),
        replace(request.executable, environment=oversized_environment),
    ):
        validation = validate_isolation_request_v1(
            replace(request, executable=executable)
        )
        assert not validation.ok
        assert validation.error_code is IsolationRequestErrorCodeV1.POLICY_MISMATCH


def test_exec_argument_environment_footprint_is_preflight_bounded() -> None:
    request = _valid_request()
    entrypoint = request.executable.entrypoint.private_path
    environment = request.executable.environment
    fixed = (
        len(entrypoint.encode("utf-8"))
        + 1
        + sum(
            len(name.encode("utf-8")) + len(value.encode("utf-8")) + 2
            for name, value in environment
        )
        + (2 + len(environment) + 2) * 8
        + 1
    )
    exact_argument = "a" * (MAX_EXEC_ARGUMENT_ENVIRONMENT_BYTES_V1 - fixed)
    exact = replace(
        request,
        executable=replace(
            request.executable, argv=(entrypoint, exact_argument)
        ),
    )
    assert validate_isolation_request_v1(exact).ok

    over = replace(
        exact,
        executable=replace(
            exact.executable, argv=(entrypoint, exact_argument + "a")
        ),
    )
    wrong_argv0 = replace(
        request,
        executable=replace(request.executable, argv=("different",)),
    )
    for invalid in (over, wrong_argv0):
        validation = validate_isolation_request_v1(invalid)
        assert not validation.ok
        assert validation.error_code is IsolationRequestErrorCodeV1.POLICY_MISMATCH


def test_script_requires_separate_interpreter_and_loader_seals() -> None:
    request = _valid_request()
    script = _expected_file(
        source_path="/srv/input/task.py",
        private_path="/runtime/script",
        file_type=ExpectedFileTypeV1.SCRIPT,
        device=8,
        inode=301,
        sha256=_sha("3"),
    )
    invalid = replace(
        request,
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.SCRIPT,
            entrypoint=script,
            interpreter=None,
            loader=request.executable.loader,
            parsed_interpreter_path="/runtime/interpreter",
            argv=(script.private_path,),
            environment=(),
        ),
    )
    result = validate_isolation_request_v1(invalid)

    assert result.error_code is IsolationRequestErrorCodeV1.IDENTITY_MISMATCH
    assert any("interpreter" in reason for reason in result.reasons)

    interpreter = _expected_file(
        source_path="/srv/input/bin/python3",
        private_path="/runtime/interpreter",
        file_type=ExpectedFileTypeV1.INTERPRETER,
        device=8,
        inode=302,
        sha256=_sha("4"),
    )
    valid = replace(
        request,
        executable=ExecutablePolicyV1(
            format=ExecutableFormatV1.SCRIPT,
            entrypoint=script,
            interpreter=interpreter,
            loader=request.executable.loader,
            parsed_interpreter_path=interpreter.private_path,
            argv=(script.private_path, "--flag"),
            environment=(("LANG", "C.UTF-8"),),
        ),
    )
    assert validate_isolation_request_v1(valid).ok
    assert effective_exec_argv_v1(valid) == (
        interpreter.private_path,
        script.private_path,
        "--flag",
    )
    assert effective_exec_environment_v1(valid) == valid.executable.environment


def test_complete_evidence_exactly_matches_the_current_request() -> None:
    request = _valid_request()
    evidence = _valid_evidence(request)

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.ok
    assert evidence.complete
    assert evidence.process.secondary_exec_denials == ()
    assert "exec_denied" not in evidence.process.event_classes
    assert len(evidence.record_sha256) == 64
    assert evidence.to_record()["record_sha256"] == evidence.record_sha256
    assert evidence.exec_chain.selected_entrypoint is not None
    assert evidence.exec_chain.sealed_entrypoint is not None
    assert (
        evidence.exec_chain.selected_entrypoint.inode
        != evidence.exec_chain.sealed_entrypoint.inode
    )
    changed_kwargs = _valid_evidence_kwargs(request)
    changed_streams = changed_kwargs["streams"]
    assert isinstance(changed_streams, StreamEvidenceV1)
    changed_kwargs["streams"] = replace(
        changed_streams,
        decoding_status=StreamDecodingStatusV1.UTF8_REPLACED,
    )
    changed_evidence = _build_execution_evidence_v1(  # type: ignore[arg-type]
        **changed_kwargs
    )
    assert changed_evidence.record_sha256 != evidence.record_sha256

    wrong_request = replace(
        request,
        identity=replace(request.identity, policy_sha256=_sha("0")),
    )
    mismatch = validate_execution_evidence_v1(wrong_request, evidence)
    assert mismatch.error_code is EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH
    assert not mismatch.matching


def test_application_cannot_use_the_public_type_as_an_evidence_factory() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)

    with pytest.raises(TypeError, match="_producer_token"):
        ExecutionEvidenceV1(**kwargs)  # type: ignore[arg-type]
    assert "_build_execution_evidence_v1" not in isolated_execution.__all__


@pytest.mark.parametrize(
    "mutate_request",
    (
        lambda request: replace(
            request,
            identity=replace(request.identity, task_sha256=_sha("0")),
        ),
        lambda request: replace(
            request,
            identity=replace(request.identity, source_sha256=_sha("0")),
        ),
        lambda request: replace(
            request,
            identity=replace(request.identity, candidate_sha256=_sha("0")),
        ),
        lambda request: replace(
            request,
            identity=replace(request.identity, workspace_sha256=_sha("0")),
        ),
        lambda request: replace(
            request,
            identity=replace(request.identity, configuration_sha256=_sha("0")),
        ),
    ),
)
def test_evidence_rejects_wrong_request_identity(mutate_request) -> None:
    request = _valid_request()
    evidence = _valid_evidence(request)
    validation = validate_execution_evidence_v1(mutate_request(request), evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH
    assert not validation.matching


def test_evidence_rejects_wrong_executable_and_cgroup_projection() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    chain = kwargs["exec_chain"]
    assert isinstance(chain, ExecChainEvidenceV1)
    requested = chain.requested_entrypoint
    assert requested is not None
    kwargs["exec_chain"] = replace(
        chain,
        requested_entrypoint=replace(requested, sha256=_sha("0")),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(process, cgroup_name="wrong-execution")
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE


def test_workload_self_report_cannot_substitute_for_os_source() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    kwargs["observations"] = (
        replace(observations[0], os_source="workload self-report"),
        *observations[1:],
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert not evidence.complete


def test_identity_seal_provenance_is_pre_exec_descriptor_evidence() -> None:
    request = _valid_request()
    evidence = _valid_evidence(request)
    identity_seal = next(
        item for item in evidence.observations if item.event_id == "identity.seal"
    )
    assert identity_seal.os_source == (
        "openat2, fstat, SHA-256, and memfd seals"
    )
    exec_observation = next(
        item for item in evidence.observations if item.event_id == "exec.ptrace"
    )
    assert exec_observation.os_source == "ptrace exec-stop and procfs"


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("native_syscall_exclusive_ceiling", 471),
        ("ceiling_syscall_errno", errno.ENOSYS),
    ),
)
def test_native_syscall_ceiling_control_is_exact_evidence(
    field: str, replacement: int
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    network_payload = next(
        item.payload() for item in observations if item.event_id == "network.gate"
    )
    seccomp_controls = network_payload["seccomp_controls"]
    assert isinstance(seccomp_controls, dict)
    seccomp_controls[field] = replacement
    _update_observation(
        kwargs, "network.gate", {"seccomp_controls": seccomp_controls}
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("seccomp" in reason for reason in validation.reasons)


def test_stage_graph_rejects_ambiguous_or_falsely_passing_cascades() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    kwargs["capability_stages"] = (
        EvidenceStageV1(
            "capability.gate",
            1,
            EvidenceStageStatusV1.FAIL,
            failure_code="CAPABILITY_MISSING",
        ),
        EvidenceStageV1("workload.release", 2, EvidenceStageStatusV1.PASS),
    )
    kwargs["stage_dependencies"] = (
        StageDependencyV1("capability.gate", ()),
        StageDependencyV1("workload.release", ("capability.gate",)),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("frozen backend" in reason for reason in validation.reasons)


def test_exact_stage_dag_preserves_direct_failure_and_dependent_cascade() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    stages = list(kwargs["capability_stages"])
    by_name = {stage.stage_id: index for index, stage in enumerate(stages)}
    stages[by_name["network.setup"]] = replace(
        stages[by_name["network.setup"]],
        status=EvidenceStageStatusV1.FAIL,
        failure_code="NETWORK_CONTROL_FAILED",
    )
    blocker = "network.setup"
    for stage_id in ("workload.release", "exec.observe", "process.contain"):
        stages[by_name[stage_id]] = replace(
            stages[by_name[stage_id]],
            status=EvidenceStageStatusV1.NOT_REACHED,
            blocked_by=blocker,
        )
        blocker = stage_id
    kwargs["capability_stages"] = tuple(stages)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert not evidence.complete

    stages[by_name["exec.observe"]] = replace(
        stages[by_name["exec.observe"]], blocked_by="network.setup"
    )
    stages[by_name["workload.release"]] = replace(
        stages[by_name["workload.release"]], blocked_by="exec.observe"
    )
    kwargs["capability_stages"] = tuple(stages)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("blocker" in reason for reason in validation.reasons)

    kwargs["capability_stages"] = (
        EvidenceStageV1(
            "capability.gate",
            1,
            EvidenceStageStatusV1.FAIL,
            failure_code="CAPABILITY_MISSING",
        ),
        EvidenceStageV1(
            "workload.release",
            2,
            EvidenceStageStatusV1.NOT_REACHED,
            blocked_by="unknown.stage",
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("frozen backend" in reason for reason in validation.reasons)


def test_stage_dependencies_must_be_bounded_and_strictly_preceding() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    kwargs["capability_stages"] = (
        EvidenceStageV1("first", 1, EvidenceStageStatusV1.PASS),
        EvidenceStageV1("second", 2, EvidenceStageStatusV1.PASS),
    )
    kwargs["stage_dependencies"] = (
        StageDependencyV1("first", ("second",)),
        StageDependencyV1("second", ()),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("strictly precede" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    kwargs["capability_stages"] = tuple(
        EvidenceStageV1(f"stage.{index}", index, EvidenceStageStatusV1.PASS)
        for index in range(1, 258)
    )
    kwargs["stage_dependencies"] = tuple(
        StageDependencyV1(f"stage.{index}", ()) for index in range(1, 258)
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("count exceeds" in reason for reason in validation.reasons)


def test_single_generic_stage_and_duplicate_os_event_cannot_be_complete() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    kwargs["capability_stages"] = (
        EvidenceStageV1("capability.gate", 1, EvidenceStageStatusV1.PASS),
    )
    kwargs["stage_dependencies"] = (StageDependencyV1("capability.gate", ()),)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("frozen backend" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    kwargs["observations"] = observations[:-1] + (
        replace(observations[-1], event_id=observations[0].event_id),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("event IDs must be unique" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "field",
    ("event_classes", "rejected_boundary_attempts", "denied_attempt_classes"),
)
def test_empty_process_or_boundary_control_sets_are_incomplete(field: str) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    if field == "event_classes":
        kwargs["process"] = replace(kwargs["process"], event_classes=())
    elif field == "rejected_boundary_attempts":
        kwargs["filesystem"] = replace(
            kwargs["filesystem"], rejected_boundary_attempts=()
        )
    else:
        kwargs["network"] = replace(kwargs["network"], denied_attempt_classes=())
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert not evidence.complete


def test_event_specific_os_payload_cannot_be_empty_or_disagree_with_typed_facts() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    host = observations[0]
    kwargs["observations"] = (
        OSObservationV1.from_payload(
            sequence=host.sequence,
            observation_class=host.observation_class,
            event_id=host.event_id,
            os_source=host.os_source,
            monotonic_ns=host.monotonic_ns,
            payload={"execution_id": request.execution_id},
        ),
        *observations[1:],
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("host.gate" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    network = kwargs["network"]
    assert isinstance(network, NetworkEvidenceV1)
    kwargs["network"] = replace(network, flags_after_up=3)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("network.gate" in reason for reason in validation.reasons)


def test_identity_seal_payload_binds_selected_source_and_sealed_identity() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload() for item in observations if item.event_id == "identity.seal"
    )
    assert isinstance(payload, dict)
    entrypoint = payload["entrypoint"]
    assert isinstance(entrypoint, dict)
    source = entrypoint["source_identity"]
    assert isinstance(source, dict)
    source["inode"] = source["inode"] + 1
    _update_observation(kwargs, "identity.seal", {"entrypoint": entrypoint})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("identity.seal entrypoint" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload() for item in observations if item.event_id == "identity.seal"
    )
    assert isinstance(payload, dict)
    entrypoint = payload["entrypoint"]
    assert isinstance(entrypoint, dict)
    sealed = entrypoint["sealed_identity"]
    assert isinstance(sealed, dict)
    sealed["sha256"] = _sha("0")
    _update_observation(kwargs, "identity.seal", {"entrypoint": entrypoint})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("identity.seal entrypoint" in reason for reason in validation.reasons)


def test_retained_output_identity_is_bound_to_process_os_payload() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    filesystem = kwargs["filesystem"]
    assert isinstance(filesystem, FilesystemEvidenceV1)
    retained = ObservedFileIdentityV1(
        path="/output/result.json",
        device=51,
        inode=52,
        mode=stat.S_IFREG | 0o400,
        size=2,
        sha256=_sha("7"),
    )
    kwargs["filesystem"] = replace(
        filesystem,
        observed_output_paths=("result.json",),
        retained_outputs=(retained,),
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "observed_output_paths": ["result.json"],
            "retained_outputs": [retained.to_record()],
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, evidence).ok

    kwargs = _valid_evidence_kwargs(request)
    filesystem = kwargs["filesystem"]
    assert isinstance(filesystem, FilesystemEvidenceV1)
    kwargs["filesystem"] = replace(
        filesystem,
        observed_output_paths=("result.json",),
        retained_outputs=(retained,),
    )
    forged = retained.to_record()
    forged["sha256"] = _sha("8")
    _update_observation(
        kwargs,
        "process.contain",
        {
            "observed_output_paths": ["result.json"],
            "retained_outputs": [forged],
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("process.contain" in reason for reason in validation.reasons)


def test_workload_exit_code_is_bound_to_process_os_payload_and_outcome() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    kwargs["outcome"] = ExecutionOutcomeV1.WORKLOAD_FAILURE
    kwargs["workload_exit_code"] = 7
    _update_observation(kwargs, "process.contain", {"workload_exit_code": 7})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, evidence).ok

    kwargs["workload_exit_code"] = 8
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("process.contain" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(process, workload_exit_monotonic_ns=None)
    kwargs["workload_exit_code"] = 0
    _update_observation(
        kwargs,
        "process.contain",
        {"workload_exit_monotonic_ns": None, "workload_exit_code": 0},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("present together" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    kwargs["outcome"] = ExecutionOutcomeV1.WORKLOAD_FAILURE
    kwargs["workload_exit_code"] = -1
    _update_observation(kwargs, "process.contain", {"workload_exit_code": -1})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("wait-status" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "changes",
    (
        {"entries_scanned": READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1 + 1},
        {"entry_limit": READ_ONLY_ROOT_SCAN_ENTRY_LIMIT_V1 - 1},
        {"nofollow": False},
        {"no_xdev": False},
        {"identity_revalidated": False},
        {"stable_during_scan": False},
        {"allowed_inode_types": ("directory", "regular", "fifo")},
    ),
)
def test_read_only_input_scan_evidence_is_exact_and_bounded(
    changes: dict[str, object]
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    filesystem = kwargs["filesystem"]
    assert isinstance(filesystem, FilesystemEvidenceV1)
    scan = replace(filesystem.read_only_input_scans[0], **changes)
    kwargs["filesystem"] = replace(filesystem, read_only_input_scans=(scan,))
    _update_observation(
        kwargs,
        "filesystem.gate",
        {"read_only_input_scans": [scan.to_record()]},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE


@pytest.mark.parametrize(
    ("event_id", "updates"),
    (
        (
            "host.gate",
            {"mandatory_abi_control": {"execveat": True}},
        ),
        (
            "cgroup.claim",
            {"observed_pids_max": 255},
        ),
        (
            "filesystem.gate",
            {"provider_view_controls": {}},
        ),
        (
            "filesystem.gate",
            {"read_only_input_scans": []},
        ),
        (
            "filesystem.gate",
            {
                "private_root_mount_observation": {
                    "filesystem_type": "tmpfs",
                    "mount_options": ["nodev", "nosuid", "rw"],
                    "mode": stat.S_IFDIR | 0o777,
                    "root_device_changed": True,
                    "old_root_removed": True,
                }
            },
        ),
        (
            "network.gate",
            {
                "seccomp_controls": {
                    "observed_filter_sha256": _sha("0")
                }
            },
        ),
        (
            "stream.control",
            {"freeze_positive_control": False},
        ),
    ),
)
def test_preflight_os_control_payloads_are_not_echo_only(
    event_id: str, updates: dict[str, object]
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(kwargs, event_id, updates)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert not validation.complete


def test_evidence_validation_is_total_and_strict_for_malformed_groups() -> None:
    request = _valid_request()
    cases: list[dict[str, object]] = []

    kwargs = _valid_evidence_kwargs(request)
    kwargs["outcome"] = "unrecognized"
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    kwargs["workload_released"] = 1
    kwargs["workload_exit_code"] = True
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    chain = kwargs["exec_chain"]
    assert isinstance(chain, ExecChainEvidenceV1)
    selected = chain.selected_entrypoint
    assert selected is not None
    kwargs["exec_chain"] = replace(
        chain,
        selected_entrypoint=replace(selected, inode=True, mode=0, sha256="bad"),
    )
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(
        process,
        initial_pid=True,
        initial_starttime_ticks=0,
        initial_pidfd_opened=1,
    )
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(process, initial_pid=10**5_000)
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    network = kwargs["network"]
    assert isinstance(network, NetworkEvidenceV1)
    kwargs["network"] = replace(
        network,
        namespace_inode=True,
        flags_after_up=-1,
        live_endpoint_positive_control=1,
    )
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    completeness = kwargs["completeness"]
    assert isinstance(completeness, EvidenceCompletenessV1)
    kwargs["completeness"] = replace(
        completeness,
        cleanup=replace(completeness.cleanup, cgroup_removed=1),
    )
    cases.append(kwargs)

    kwargs = _valid_evidence_kwargs(request)
    kwargs["exec_chain"] = object()
    cases.append(kwargs)

    for values in cases:
        evidence = _build_execution_evidence_v1(**values)  # type: ignore[arg-type]
        validation = validate_execution_evidence_v1(request, evidence)
        assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
        assert not validation.ok
        assert not evidence.complete


def test_deeply_nested_observation_json_is_total_and_invalid() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    nested = b"[" * 2_000 + b"0" + b"]" * 2_000
    kwargs["observations"] = (
        replace(observations[0], payload_json=nested),
        *observations[1:],
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert not validation.ok
    assert not evidence.complete


def test_exec_provider_sequence_is_strictly_increasing() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    chain = kwargs["exec_chain"]
    assert isinstance(chain, ExecChainEvidenceV1)
    kwargs["exec_chain"] = replace(chain, seal_sequence=1)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("exec open/seal" in reason for reason in validation.reasons)


def test_effective_exec_digest_is_bound_to_request_and_ptrace_payload() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    chain = kwargs["exec_chain"]
    assert isinstance(chain, ExecChainEvidenceV1)
    kwargs["exec_chain"] = replace(chain, effective_argv_sha256=_sha("0"))
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.CORRELATION_MISMATCH

    kwargs = _valid_evidence_kwargs(request)
    _update_observation(
        kwargs, "exec.ptrace", {"effective_environment_count": 99}
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("exec.ptrace" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("seccomp_mode", "0"),
        ("seccomp_filters", "1"),
        ("seccomp_filter_delta", 0),
        ("file_size_soft_limit", 0),
        ("file_size_hard_limit", 0),
        ("core_soft_limit", 1),
        ("core_hard_limit", 1),
        (
            "secondary_exec_policy",
            {
                "execve": 59,
                "execveat": 322,
                "ptrace_entry_denial": False,
                "ptrace_event_exec_backstop": True,
            },
        ),
        ("stdio_provider_match", False),
        ("fd_set", [0, 1]),
        ("stdio_pipe_identities", {}),
    ),
)
def test_exec_ptrace_security_projection_is_exact(
    field: str, replacement: object
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(kwargs, "exec.ptrace", {field: replacement})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("exec.ptrace" in reason for reason in validation.reasons)


@pytest.mark.parametrize("command_name", tuple(name for name, _ in FCNTL_DENIED_COMMANDS_V1))
def test_fcntl_mutation_controls_are_required(command_name: str) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    network_payload = next(
        item.payload() for item in observations if item.event_id == "network.gate"
    )
    assert isinstance(network_payload, dict)
    seccomp_controls = network_payload["seccomp_controls"]
    assert isinstance(seccomp_controls, dict)
    fcntl_controls = seccomp_controls["fcntl_command_controls"]
    assert isinstance(fcntl_controls, dict)
    fcntl_controls[command_name] = 0
    _update_observation(
        kwargs, "network.gate", {"seccomp_controls": seccomp_controls}
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert not validate_execution_evidence_v1(request, evidence).ok


@pytest.mark.parametrize(
    ("field", "replacement"),
    (("shared_wake_errno", 0), ("private_wake_result", -1)),
)
def test_futex_isolation_controls_are_required(
    field: str, replacement: int
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    network_payload = next(
        item.payload() for item in observations if item.event_id == "network.gate"
    )
    assert isinstance(network_payload, dict)
    seccomp_controls = network_payload["seccomp_controls"]
    assert isinstance(seccomp_controls, dict)
    futex_controls = seccomp_controls["futex_controls"]
    assert isinstance(futex_controls, dict)
    futex_controls[field] = replacement
    _update_observation(
        kwargs, "network.gate", {"seccomp_controls": seccomp_controls}
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert not validate_execution_evidence_v1(request, evidence).ok


def test_core_pipe_gate_is_required() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(kwargs, "host.gate", {"core_pipe_helper_absent": False})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert not validate_execution_evidence_v1(request, evidence).ok


@pytest.mark.parametrize("syscall_name", ("setrlimit", "prlimit64"))
def test_resource_limit_mutation_seccomp_control_is_required(
    syscall_name: str,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    network_payload = next(
        item.payload() for item in observations if item.event_id == "network.gate"
    )
    assert isinstance(network_payload, dict)
    seccomp_controls = network_payload["seccomp_controls"]
    assert isinstance(seccomp_controls, dict)
    filter_syscalls = seccomp_controls["filter_syscalls"]
    assert isinstance(filter_syscalls, dict)
    assert filter_syscalls[syscall_name] == errno.EPERM
    filter_syscalls[syscall_name] = 0
    _update_observation(
        kwargs,
        "network.gate",
        {"seccomp_controls": seccomp_controls},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("seccomp" in reason for reason in validation.reasons)


def test_secondary_exec_attempt_is_strictly_os_bound() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    denial = SecondaryExecDenialEvidenceV1(
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        syscall_number=59,
        errno=errno.EPERM,
        monotonic_ns=1_011,
    )
    event_classes = tuple(sorted((*process.event_classes, "exec_denied")))
    kwargs["process"] = replace(
        process,
        event_classes=event_classes,
        secondary_exec_denials=(denial,),
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "event_classes": list(event_classes),
            "secondary_exec_denials": [denial.to_record()],
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    assert validate_execution_evidence_v1(request, evidence).ok
    assert evidence.process.secondary_exec_denials == (denial,)


@pytest.mark.parametrize(
    "changes",
    (
        {"pid": 999},
        {"cgroup_path": "/other/composition"},
        {"syscall_number": 58},
        {"errno": 0},
        {"monotonic_ns": 1_000},
    ),
)
def test_secondary_exec_denial_rejects_forged_identity_or_control(
    changes: dict[str, object],
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    denial = SecondaryExecDenialEvidenceV1(
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        syscall_number=322,
        errno=errno.EPERM,
        monotonic_ns=1_011,
    )
    denial = replace(denial, **changes)
    event_classes = tuple(sorted((*process.event_classes, "exec_denied")))
    kwargs["process"] = replace(
        process,
        event_classes=event_classes,
        secondary_exec_denials=(denial,),
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "event_classes": list(event_classes),
            "secondary_exec_denials": [denial.to_record()],
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    assert not validate_execution_evidence_v1(request, evidence).ok


@pytest.mark.parametrize(
    ("event_classes", "denials"),
    (
        (("exec", "exec_denied", "exit", "exit_stop"), ()),
        (
            ("exec", "exit", "exit_stop"),
            (
                SecondaryExecDenialEvidenceV1(
                    pid=314,
                    starttime_ticks=2718,
                    cgroup_path="/ts-b02a-0123456789abcdef0123/composition",
                    syscall_number=59,
                    errno=errno.EPERM,
                    monotonic_ns=1_011,
                ),
            ),
        ),
    ),
)
def test_secondary_exec_event_class_is_bidirectional(
    event_classes: tuple[str, ...],
    denials: tuple[SecondaryExecDenialEvidenceV1, ...],
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(
        process,
        event_classes=event_classes,
        secondary_exec_denials=denials,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "event_classes": list(event_classes),
            "secondary_exec_denials": [item.to_record() for item in denials],
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE


@pytest.mark.parametrize(
    "claim_key",
    (
        "zero_effect",
        "zeroEffect",
        "zero effect",
        "zero-effect",
        "hardZero",
        "absolute_zero_effect",
        "guaranteedZeroEffect",
        "absolutely_no_effect",
        "unconditional-no-side-effect",
    ),
)
def test_payloads_reject_absolute_claim_key_variants(claim_key: str) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(kwargs, "stream.control", {claim_key: True})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("prohibited absolute-claim" in reason for reason in validation.reasons)


def test_every_os_event_payload_rejects_unknown_extra_keys() -> None:
    request = _valid_request()
    for event_id, _, _ in REQUIRED_OBSERVATION_EVENTS_V1:
        kwargs = _valid_evidence_kwargs(request)
        _update_observation(kwargs, event_id, {"unrecognized_security_fact": True})
        evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

        validation = validate_execution_evidence_v1(request, evidence)
        assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
        assert any("payload key set" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    ("event_id", "nested_path"),
    (
        ("identity.seal", ("entrypoint",)),
        ("filesystem.gate", ("declared_output_control",)),
        ("filesystem.gate", ("private_quota_observations",)),
        ("filesystem.gate", ("private_quota_observations", "scratch")),
        ("filesystem.gate", ("private_quota_observations", "output")),
        ("filesystem.gate", ("read_only_mount_observations", 0)),
        ("network.gate", ("network",)),
        ("network.gate", ("seccomp_controls",)),
        ("network.gate", ("seccomp_controls", "network")),
        ("network.gate", ("seccomp_controls", "filter_syscalls")),
        ("network.gate", ("seccomp_controls", "clone_flag_controls")),
        ("network.gate", ("seccomp_controls", "fcntl_command_controls")),
        ("network.gate", ("seccomp_controls", "futex_controls")),
        ("network.gate", ("seccomp_controls", "pipe2_controls")),
        ("cleanup.final", ("cgroup_release",)),
    ),
)
def test_os_payload_nested_security_objects_reject_extra_keys(
    event_id: str, nested_path: tuple[str | int, ...]
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    observation = next(item for item in observations if item.event_id == event_id)
    payload = observation.payload()
    assert isinstance(payload, dict)
    current: object = payload
    for component in nested_path:
        if isinstance(component, int):
            assert isinstance(current, list)
            current = current[component]
        else:
            assert isinstance(current, dict)
            current = current[component]
    assert isinstance(current, dict)
    current["unexpected_security_fact"] = True
    _update_observation(kwargs, event_id, payload)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert not validation.complete


@pytest.mark.parametrize(
    ("quota_field", "payload_name"),
    (
        ("scratch_quota_before_release", "scratch"),
        ("output_quota_before_release", "output"),
    ),
)
def test_private_tmpfs_mount_options_require_exact_v1_projection(
    quota_field: str,
    payload_name: str,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    filesystem = kwargs["filesystem"]
    assert isinstance(filesystem, FilesystemEvidenceV1)
    quota = getattr(filesystem, quota_field)
    assert isinstance(quota, PrivateMountQuotaEvidenceV1)
    forged = replace(
        quota,
        mount_options=(
            "absolute_zero_effect",
            "nodev",
            "noexec",
            "nosuid",
            "rw",
        ),
    )
    kwargs["filesystem"] = replace(filesystem, **{quota_field: forged})
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload()
        for item in observations
        if item.event_id == "filesystem.gate"
    )
    assert isinstance(payload, dict)
    private_quota = payload["private_quota_observations"]
    assert isinstance(private_quota, dict)
    private_quota[payload_name] = forged.to_record()
    _update_observation(
        kwargs,
        "filesystem.gate",
        {"private_quota_observations": private_quota},
    )

    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("exact v1 projection" in reason for reason in validation.reasons)


def test_read_only_mount_options_require_exact_v1_projection() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload()
        for item in observations
        if item.event_id == "filesystem.gate"
    )
    assert isinstance(payload, dict)
    mounts = payload["read_only_mount_observations"]
    assert isinstance(mounts, list)
    first = mounts[0]
    assert isinstance(first, dict)
    first["mount_options"] = [
        "absolute_zero_effect",
        "nodev",
        "nosuid",
        "ro",
    ]
    _update_observation(
        kwargs,
        "filesystem.gate",
        {"read_only_mount_observations": mounts},
    )

    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("read-only mount payload" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "forged_value",
    ("absolute zero effect", "hard zero", "guaranteed no side effect"),
)
def test_operstate_diagnostic_rejects_free_text_claim_values(
    forged_value: str,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    network = kwargs["network"]
    assert isinstance(network, NetworkEvidenceV1)
    forged = {"value": forged_value}
    kwargs["network"] = replace(
        network,
        operstate_after_up_json=canonical_json_bytes(forged),
    )
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    network_payload = next(
        item.payload() for item in observations if item.event_id == "network.gate"
    )
    assert isinstance(network_payload, dict)
    control = network_payload["network"]
    assert isinstance(control, dict)
    control["operstate_after_up"] = forged
    _update_observation(kwargs, "network.gate", {"network": control})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("operstate_after_up" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "forged_namespace",
    (
        "absolute zero effect",
        "hard zero",
        "mnt:[0]",
        "pid:[42]",
        "mnt:[99999999999999999999]",
    ),
)
def test_namespace_identity_requires_exact_procfs_readlink_form(
    forged_namespace: str,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload() for item in observations if item.event_id == "namespace.setup"
    )
    assert isinstance(payload, dict)
    namespace_ids = payload["namespace_ids"]
    assert isinstance(namespace_ids, dict)
    namespace_ids["mnt"] = forged_namespace
    _update_observation(kwargs, "namespace.setup", {"namespace_ids": namespace_ids})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("namespace.setup" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "forged_path",
    (
        "relative",
        "//provider",
        "/provider/../escape",
        "/provider//escape",
        "/provider\x00control",
        "/provider\ncontrol",
    ),
)
def test_host_cgroup_paths_require_bounded_canonical_absolute_form(
    forged_path: str,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    observations = kwargs["observations"]
    assert isinstance(observations, tuple)
    payload = next(
        item.payload() for item in observations if item.event_id == "host.gate"
    )
    assert isinstance(payload, dict)
    gate = payload["cgroup2_gate"]
    assert isinstance(gate, dict)
    gate["current_unified_cgroup"] = forged_path
    _update_observation(kwargs, "host.gate", {"cgroup2_gate": gate})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("host.gate" in reason for reason in validation.reasons)


def test_success_deadline_uses_exit_observation_not_cleanup_finish() -> None:
    base = _valid_request()
    deadline = 2_000_000_000
    request = replace(
        base,
        process=replace(base.process, deadline_monotonic_ns=deadline),
    )
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    correlation = kwargs["correlation"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(correlation, CorrelationEvidenceV1)
    process = replace(
        process,
        workload_exit_monotonic_ns=deadline - 1,
        grace_started_monotonic_ns=deadline,
        grace_finished_monotonic_ns=deadline + process.termination_grace_ns,
    )
    kwargs["process"] = process
    kwargs["correlation"] = replace(
        correlation,
        finished_monotonic_ns=process.grace_finished_monotonic_ns + 1_000,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "workload_exit_monotonic_ns": process.workload_exit_monotonic_ns,
            "grace_started_monotonic_ns": process.grace_started_monotonic_ns,
            "grace_finished_monotonic_ns": process.grace_finished_monotonic_ns,
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, evidence).ok
    assert evidence.correlation.finished_monotonic_ns > deadline

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(
        process, workload_exit_monotonic_ns=deadline
    )
    _update_observation(
        kwargs,
        "process.contain",
        {"workload_exit_monotonic_ns": deadline},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("success outcome" in reason for reason in validation.reasons)


def test_filesystem_limit_requires_typed_ptrace_observation() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    filesystem = kwargs["filesystem"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(filesystem, FilesystemEvidenceV1)
    observation = FilesystemLimitObservationV1(
        kind=FilesystemLimitKindV1.SYSCALL_ERRNO,
        scope=FilesystemLimitScopeV1.OUTPUT,
        target_path="/output/artifact.bin",
        target_fd=3,
        syscall_number=1,
        errno=errno.EFBIG,
        signal_number=None,
        signal_code=None,
        fault_address=None,
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        monotonic_ns=1_800,
    )
    kwargs["process"] = replace(
        process,
        limit_triggered=True,
        workload_exit_monotonic_ns=None,
    )
    kwargs["filesystem"] = replace(filesystem, limit_observation=observation)
    kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
    _set_immediate_limit_teardown(kwargs)
    _update_observation(
        kwargs,
        "process.contain",
        {
            "limit_triggered": True,
            "workload_exit_monotonic_ns": None,
            "filesystem_limit_observation": observation.to_record(),
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, evidence).ok

    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    kwargs["process"] = replace(
        process,
        limit_triggered=True,
        workload_exit_monotonic_ns=None,
    )
    kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
    _set_immediate_limit_teardown(kwargs)
    _update_observation(
        kwargs,
        "process.contain",
        {"limit_triggered": True, "workload_exit_monotonic_ns": None},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("limit signal" in reason for reason in validation.reasons)


def test_efbig_limit_is_bound_to_the_scope_matching_process_rlimit_fsize() -> None:
    base = _valid_request()
    request = replace(
        base,
        filesystem=replace(base.filesystem, scratch_byte_limit=2_097_152),
    )

    def limit_evidence(
        scope: FilesystemLimitScopeV1,
        target_path: str,
    ) -> ExecutionEvidenceV1:
        kwargs = _valid_evidence_kwargs(request)
        process = kwargs["process"]
        filesystem = kwargs["filesystem"]
        assert isinstance(process, ProcessEvidenceV1)
        assert isinstance(filesystem, FilesystemEvidenceV1)
        observation = FilesystemLimitObservationV1(
            kind=FilesystemLimitKindV1.SYSCALL_ERRNO,
            scope=scope,
            target_path=target_path,
            target_fd=3,
            syscall_number=1,
            errno=errno.EFBIG,
            signal_number=None,
            signal_code=None,
            fault_address=None,
            pid=314,
            starttime_ticks=2718,
            cgroup_path=f"/{request.execution_id}/composition",
            monotonic_ns=1_800,
        )
        kwargs["process"] = replace(
            process,
            limit_triggered=True,
            workload_exit_monotonic_ns=None,
        )
        kwargs["filesystem"] = replace(
            filesystem,
            limit_observation=observation,
        )
        kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
        _set_immediate_limit_teardown(kwargs)
        _update_observation(
            kwargs,
            "process.contain",
            {
                "limit_triggered": True,
                "workload_exit_monotonic_ns": None,
                "filesystem_limit_observation": observation.to_record(),
            },
        )
        return _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    scratch = limit_evidence(FilesystemLimitScopeV1.SCRATCH, "/scratch/file")
    assert validate_execution_evidence_v1(request, scratch).ok

    output = limit_evidence(FilesystemLimitScopeV1.OUTPUT, "/output/file")
    validation = validate_execution_evidence_v1(request, output)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("file-size limit" in reason for reason in validation.reasons)


def test_sigbus_never_qualifies_as_a_complete_v1_quota_limit() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    filesystem = kwargs["filesystem"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(filesystem, FilesystemEvidenceV1)
    observation = FilesystemLimitObservationV1(
        kind=FilesystemLimitKindV1.SIGNAL,
        scope=FilesystemLimitScopeV1.OUTPUT,
        target_path="/output/mapped.bin",
        target_fd=None,
        syscall_number=None,
        errno=None,
        signal_number=signal.SIGBUS,
        signal_code=2,
        fault_address=0x1000,
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        monotonic_ns=1_800,
    )
    kwargs["process"] = replace(
        process,
        limit_triggered=True,
        workload_exit_monotonic_ns=None,
    )
    kwargs["filesystem"] = replace(filesystem, limit_observation=observation)
    kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
    _set_immediate_limit_teardown(kwargs)
    _update_observation(
        kwargs,
        "process.contain",
        {
            "limit_triggered": True,
            "workload_exit_monotonic_ns": None,
            "filesystem_limit_observation": observation.to_record(),
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("not attributable" in reason for reason in validation.reasons)

    kwargs["filesystem"] = replace(
        kwargs["filesystem"],  # type: ignore[arg-type]
        output_used_bytes=request.filesystem.output_byte_limit,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {"output_used_bytes": request.filesystem.output_byte_limit},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert not validation.ok
    assert any("not attributable" in reason for reason in validation.reasons)


def test_space_errno_limit_requires_full_byte_or_inode_quota() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    filesystem = kwargs["filesystem"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(filesystem, FilesystemEvidenceV1)
    observation = FilesystemLimitObservationV1(
        kind=FilesystemLimitKindV1.SYSCALL_ERRNO,
        scope=FilesystemLimitScopeV1.SCRATCH,
        target_path="/scratch/work.bin",
        target_fd=3,
        syscall_number=1,
        errno=errno.ENOSPC,
        signal_number=None,
        signal_code=None,
        fault_address=None,
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        monotonic_ns=1_800,
    )
    kwargs["process"] = replace(
        process,
        limit_triggered=True,
        workload_exit_monotonic_ns=None,
    )
    kwargs["filesystem"] = replace(filesystem, limit_observation=observation)
    kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
    _set_immediate_limit_teardown(kwargs)
    _update_observation(
        kwargs,
        "process.contain",
        {
            "limit_triggered": True,
            "workload_exit_monotonic_ns": None,
            "filesystem_limit_observation": observation.to_record(),
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("full private tmpfs" in reason for reason in validation.reasons)

    kwargs["filesystem"] = replace(
        kwargs["filesystem"],  # type: ignore[arg-type]
        scratch_used_inodes=request.filesystem.scratch_inode_limit,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {"scratch_used_inodes": request.filesystem.scratch_inode_limit},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, evidence).ok


def test_path_backed_limit_evidence_is_not_a_valid_public_kind() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    filesystem = kwargs["filesystem"]
    assert isinstance(filesystem, FilesystemEvidenceV1)
    observation = FilesystemLimitObservationV1(
        kind="path_syscall_errno",  # type: ignore[arg-type]
        scope=FilesystemLimitScopeV1.SCRATCH,
        target_path="/scratch/new-entry",
        target_fd=None,
        syscall_number=257,
        errno=errno.ENOSPC,
        signal_number=None,
        signal_code=None,
        fault_address=None,
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        monotonic_ns=1_800,
    )
    kwargs["filesystem"] = replace(filesystem, limit_observation=observation)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("kind must use the v1 enum" in reason for reason in validation.reasons)
    with pytest.raises(ValueError):
        FilesystemLimitKindV1("path_syscall_errno")

@pytest.mark.parametrize(
    "mutate",
    [
        lambda kwargs: kwargs.update(
            capability_stages=kwargs["capability_stages"][:-1]
            + (
                EvidenceStageV1(
                    "cleanup",
                    len(REQUIRED_STAGE_DEPENDENCIES_V1),
                    EvidenceStageStatusV1.FAIL,
                    failure_code="OBSERVATION_FAILED",
                ),
            )
        ),
        lambda kwargs: kwargs.update(
            completeness=replace(
                kwargs["completeness"], observer_errors=("ptrace event lost",)
            )
        ),
        lambda kwargs: kwargs.update(
            process=replace(
                kwargs["process"], current_execution_survivor_count=1
            )
        ),
        lambda kwargs: kwargs.update(
            completeness=replace(
                kwargs["completeness"],
                cleanup=replace(
                    kwargs["completeness"].cleanup,
                    temporary_root_removed=False,
                    residue=("temporary_root",),
                ),
            )
        ),
        lambda kwargs: kwargs.update(
            streams=replace(kwargs["streams"], observer_loss=True)
        ),
        lambda kwargs: _drop_observation(kwargs, "network.gate"),
        lambda kwargs: kwargs.update(
            completeness=replace(kwargs["completeness"], sequence_gaps=(7,))
        ),
        lambda kwargs: kwargs.update(
            completeness=replace(kwargs["completeness"], buffer_loss=True)
        ),
        lambda kwargs: kwargs.update(
            completeness=replace(kwargs["completeness"], teardown_observed=False)
        ),
        lambda kwargs: kwargs.update(
            process=replace(kwargs["process"], survivor_observation_available=False)
        ),
        lambda kwargs: kwargs.update(
            filesystem=replace(kwargs["filesystem"], teardown_observed=False)
        ),
        lambda kwargs: _drop_observation(kwargs, "cleanup.final"),
    ],
)
def test_loss_failure_survivor_or_cleanup_residue_forces_incomplete(mutate) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    mutate(kwargs)
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert not evidence.complete
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert validation.matching
    assert not validation.complete


@pytest.mark.parametrize(
    "cleanup_field",
    (
        "cgroup_populated_zero",
        "cgroup_removed",
        "namespace_fds_closed",
        "mounts_removed",
        "cwd_root_fds_clear",
        "processes_gone",
        "pidfds_exit_observed",
        "temporary_root_removed",
    ),
)
def test_each_cleanup_domain_overrides_prior_passes(cleanup_field: str) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    completeness = kwargs["completeness"]
    assert isinstance(completeness, EvidenceCompletenessV1)
    kwargs["completeness"] = replace(
        completeness,
        cleanup=replace(
            completeness.cleanup,
            **{cleanup_field: False, "residue": (cleanup_field,)},
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert not evidence.complete


def test_stream_accounting_is_raw_exact_and_tamper_detected() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    kwargs["streams"] = replace(
        streams,
        stdout=StreamCountV1(10, 4, 5, 100, False),
        combined=StreamCountV1(10, 4, 5, 100, False),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("retained plus discarded" in reason for reason in validation.reasons)


def test_stream_pipe_capacity_is_typed_payload_bound_and_limits_overshoot() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    kwargs["streams"] = replace(
        streams,
        pipe_capacity_bytes=STREAM_PIPE_CAPACITY_BYTES_V1 * 2,
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("pipe capacity" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    _update_observation(
        kwargs,
        "streams.final",
        {"pipe_capacity_bytes": STREAM_PIPE_CAPACITY_BYTES_V1 * 2},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("raw accounting" in reason for reason in validation.reasons)

    kwargs = _valid_evidence_kwargs(request)
    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    emitted = (
        request.streams.stdout_raw_byte_limit
        + STREAM_PIPE_CAPACITY_BYTES_V1
        + 1
    )
    kwargs["streams"] = replace(
        streams,
        stdout=StreamCountV1(
            emitted,
            1,
            emitted - 1,
            request.streams.stdout_raw_byte_limit,
            True,
        ),
        combined=StreamCountV1(
            emitted,
            1,
            emitted - 1,
            request.streams.combined_raw_byte_limit,
            False,
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert not any("pipe overshoot" in reason for reason in validation.reasons)

    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    emitted += 1
    kwargs["streams"] = replace(
        streams,
        stdout=StreamCountV1(
            emitted,
            1,
            emitted - 1,
            request.streams.stdout_raw_byte_limit,
            True,
        ),
        combined=StreamCountV1(
            emitted,
            1,
            emitted - 1,
            request.streams.combined_raw_byte_limit,
            False,
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("pipe overshoot" in reason for reason in validation.reasons)


def test_combined_stream_overshoot_includes_both_pipes_and_crossing_byte() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    combined = (
        request.streams.combined_raw_byte_limit
        + 2 * STREAM_PIPE_CAPACITY_BYTES_V1
        + 1
    )
    stdout = combined // 2 + combined % 2
    stderr = combined // 2
    kwargs["streams"] = replace(
        streams,
        stdout=StreamCountV1(
            stdout,
            0,
            stdout,
            request.streams.stdout_raw_byte_limit,
            False,
        ),
        stderr=StreamCountV1(
            stderr,
            0,
            stderr,
            request.streams.stderr_raw_byte_limit,
            False,
        ),
        combined=StreamCountV1(
            combined,
            0,
            combined,
            request.streams.combined_raw_byte_limit,
            True,
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert not any("pipe overshoot" in reason for reason in validation.reasons)

    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    kwargs["streams"] = replace(
        streams,
        stdout=replace(
            streams.stdout,
            emitted_bytes=stdout + 1,
            discarded_bytes=stdout + 1,
        ),
        combined=replace(
            streams.combined,
            emitted_bytes=combined + 1,
            discarded_bytes=combined + 1,
        ),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.INVALID_EVIDENCE
    assert any("pipe overshoot" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    "forged_trigger",
    (
        "absolute zero effect",
        "hard_zero",
        ["stdout_raw_byte_limit"],
    ),
)
def test_stream_final_trigger_is_a_total_exact_enum(
    forged_trigger: object,
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(kwargs, "streams.final", {"trigger": forged_trigger})
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert not validation.ok
    assert not validation.complete
    assert any("raw accounting payload" in reason for reason in validation.reasons)


def test_stream_final_trigger_matches_the_corresponding_typed_count() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    _update_observation(
        kwargs,
        "streams.final",
        {"trigger": "stdout_raw_byte_limit"},
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("raw accounting payload" in reason for reason in validation.reasons)


def test_output_limit_signal_requires_limit_outcome_and_process_trigger() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    streams = kwargs["streams"]
    assert isinstance(streams, StreamEvidenceV1)
    kwargs["streams"] = replace(
        streams,
        stdout=StreamCountV1(65_537, 1, 65_536, 65_536, True),
        combined=StreamCountV1(65_537, 1, 65_536, 98_304, False),
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("limit" in reason for reason in validation.reasons)


@pytest.mark.parametrize(
    ("outcome", "exit_code"),
    (
        (ExecutionOutcomeV1.SUCCESS, 0),
        (ExecutionOutcomeV1.WORKLOAD_FAILURE, 7),
        (ExecutionOutcomeV1.TIMEOUT, None),
    ),
)
def test_non_limit_force_kill_requires_a_full_observed_monotonic_grace(
    outcome: ExecutionOutcomeV1, exit_code: int | None
) -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    correlation = kwargs["correlation"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(correlation, CorrelationEvidenceV1)
    kwargs["outcome"] = outcome
    kwargs["workload_exit_code"] = exit_code
    if outcome is ExecutionOutcomeV1.TIMEOUT:
        grace_start = request.process.deadline_monotonic_ns
        process = replace(
            process,
            timeout_triggered=True,
            workload_exit_monotonic_ns=None,
            timeout_trigger_monotonic_ns=grace_start,
            grace_started_monotonic_ns=grace_start,
            grace_finished_monotonic_ns=(
                grace_start + process.termination_grace_ns
            ),
        )
        kwargs["correlation"] = replace(
            correlation,
            finished_monotonic_ns=(
                grace_start + process.termination_grace_ns + 1
            ),
        )
        _update_observation(
            kwargs,
            "process.contain",
            {
                "timeout_triggered": True,
                "workload_exit_monotonic_ns": None,
                "timeout_trigger_monotonic_ns": grace_start,
                "grace_started_monotonic_ns": grace_start,
                "grace_finished_monotonic_ns": process.grace_finished_monotonic_ns,
            },
        )
    kwargs["process"] = replace(
        process,
        grace_finished_monotonic_ns=process.grace_started_monotonic_ns,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {
            "grace_finished_monotonic_ns": process.grace_started_monotonic_ns,
        },
    )
    evidence = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]

    validation = validate_execution_evidence_v1(request, evidence)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("termination grace" in reason for reason in validation.reasons)


def test_limit_force_kill_requires_an_exact_zero_length_grace_interval() -> None:
    request = _valid_request()
    kwargs = _valid_evidence_kwargs(request)
    process = kwargs["process"]
    filesystem = kwargs["filesystem"]
    assert isinstance(process, ProcessEvidenceV1)
    assert isinstance(filesystem, FilesystemEvidenceV1)
    observation = FilesystemLimitObservationV1(
        kind=FilesystemLimitKindV1.SYSCALL_ERRNO,
        scope=FilesystemLimitScopeV1.OUTPUT,
        target_path="/output/artifact.bin",
        target_fd=3,
        syscall_number=1,
        errno=errno.EFBIG,
        signal_number=None,
        signal_code=None,
        fault_address=None,
        pid=314,
        starttime_ticks=2718,
        cgroup_path=f"/{request.execution_id}/composition",
        monotonic_ns=1_800,
    )
    kwargs["process"] = replace(
        process,
        limit_triggered=True,
        workload_exit_monotonic_ns=None,
    )
    kwargs["filesystem"] = replace(filesystem, limit_observation=observation)
    kwargs["outcome"] = ExecutionOutcomeV1.LIMIT
    kwargs["workload_exit_code"] = None
    _update_observation(
        kwargs,
        "process.contain",
        {
            "limit_triggered": True,
            "workload_exit_monotonic_ns": None,
            "filesystem_limit_observation": observation.to_record(),
        },
    )

    _set_immediate_limit_teardown(kwargs)
    immediate = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    assert validate_execution_evidence_v1(request, immediate).ok

    for trigger_updates in (
        {"workload_exit_monotonic_ns": 1_800},
        {"timeout_triggered": True, "timeout_trigger_monotonic_ns": 1_800},
    ):
        competing_kwargs = dict(kwargs)
        immediate_process = competing_kwargs["process"]
        assert isinstance(immediate_process, ProcessEvidenceV1)
        competing_kwargs["process"] = replace(
            immediate_process,
            **trigger_updates,
        )
        _update_observation(
            competing_kwargs,
            "process.contain",
            trigger_updates,
        )
        competing = _build_execution_evidence_v1(  # type: ignore[arg-type]
            **competing_kwargs
        )
        validation = validate_execution_evidence_v1(request, competing)
        assert validation.error_code in {
            EvidenceValidationErrorCodeV1.INVALID_EVIDENCE,
            EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE,
        }
        assert any(
            "mutually exclusive" in reason
            or "limit outcome" in reason
            or "present together" in reason
            for reason in validation.reasons
        )

    process = kwargs["process"]
    assert isinstance(process, ProcessEvidenceV1)
    delayed_finish = (
        process.grace_started_monotonic_ns + process.termination_grace_ns
    )
    kwargs["process"] = replace(
        process,
        grace_finished_monotonic_ns=delayed_finish,
    )
    _update_observation(
        kwargs,
        "process.contain",
        {"grace_finished_monotonic_ns": delayed_finish},
    )
    delayed = _build_execution_evidence_v1(**kwargs)  # type: ignore[arg-type]
    validation = validate_execution_evidence_v1(request, delayed)
    assert validation.error_code is EvidenceValidationErrorCodeV1.EVIDENCE_INCOMPLETE
    assert any("termination grace" in reason for reason in validation.reasons)


def test_public_records_are_scoped_and_never_claim_absolute_zero_effect() -> None:
    request = _valid_request()
    evidence = _valid_evidence(request)
    rendered = json.dumps(evidence.to_record(), sort_keys=True).lower()

    assert request.execution_id in rendered
    assert request.identity.policy_sha256 in rendered
    assert "started_monotonic_ns" in rendered
    assert "finished_monotonic_ns" in rendered
    assert "zero_effect" not in rendered
    assert "hard_zero" not in rendered
    assert "attestation" not in rendered
    assert "anti_replay" not in rendered
    assert "receipt" not in rendered


def test_public_interface_exports_exact_core_types_and_sole_backend_names() -> None:
    for name in (
        "IsolationRequestV1",
        "ExecutionEvidenceV1",
        "ReadOnlyRootV1",
        "ExpectedFileIdentityV1",
        "FCNTL_DENIED_COMMANDS_V1",
        "FUTEX_PRIVATE_FLAG_V1",
        "PIPE2_DENIED_FLAGS_V1",
        "SecondaryExecDenialEvidenceV1",
        "validate_isolation_request_v1",
        "validate_execution_evidence_v1",
        "LinuxNativeSupervisorV1",
        "execute_isolation_request_v1",
    ):
        assert name in isolated_execution.__all__
    assert not any("fallback" in name.lower() for name in isolated_execution.__all__)
    assert list(NetworkModeV1) == [NetworkModeV1.DENY_ALL]
