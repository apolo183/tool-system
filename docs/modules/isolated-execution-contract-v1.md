# Isolated Execution Module Compound Contract v1

This contract owns the sole TS-B02A local Linux isolation backend. It accepts
one already selected, immutable request; validates and identity-pins every
boundary, separately seals the executable chain; runs only the exact
Linux/x86_64 native profile; and returns current-run OS-derived evidence after
complete cleanup. It has no
current runtime consumer and grants no worker, repository, provider, cleanup,
production, or public-acceptance authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/isolated-execution-contract-v1.md
  identity:
    canonical_module_id: isolated-execution
    current_module_id: isolated_execution
    module_version: 1.0.0
    aggregate_interface:
      interface_id: isolated-execution-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@fd145b8efa1d46bf864b5ac1d42e5916f897b959:isolated_execution@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.isolated_execution
  role:
    summary: enforce one fail-closed Linux/x86_64 local OS isolation profile and emit matching current-run OS-derived execution evidence
    responsibility_boundary: Validate one immutable IsolationRequestV1, reject unsupported hosts or capability loss before workload release, construct private namespace, cgroup, filesystem, identity, executable, network, stream, timeout, observation, and cleanup boundaries, execute only through sealed descriptors, and return one conjunctively complete ExecutionEvidenceV1 without ordinary-host or alternate-backend fallback or any absolute zero-effect or hard-zero conclusion.
  natural_owner_evidence_paths:
    - src/tool_system/isolated_execution/__init__.py
    - src/tool_system/isolated_execution/contract.py
    - src/tool_system/isolated_execution/evidence.py
    - src/tool_system/isolated_execution/linux_backend.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - IsolationRequestV1
      - linux_native_supervisor_v1_capability_set
    boundary: Accept one immutable, canonically digested request binding the execution, task, source, candidate, workspace, configuration, and policy identities; the sole backend profile; canonical read-only inputs, a private scratch path, and a private output path whose retained_output_paths are the complete writable-file allowlist; byte and inode quotas; exact executable, script, interpreter, and loader identities; unprivileged workload identity; deny-all network controls; a Linux v6.18 x86_64 native syscall ABI exclusive ceiling of 470 bound into the exact filter identity, so every native number at or above 470 fails with EPERM until a new profile audits it; raw stream limits with OS-read-back 4096-byte pipes and maximum final overshoot of 4097 bytes per stream or 8193 combined bytes; monotonic timeout and an exact whole-composition process limit of at least three members, including two fixed provider supervisors; denial of secondary exec, shared VM/filesystem/file-table/signal-handler clone state, pathless writable memfd resources, legacy and at-family xattr mutation, host-inode locks/leases/write-hints/delegation, filesystem-wide sync and quota sync, every ioctl, shared legacy futex and every futex2 operation, membarrier, same-UID host-scope priority inspection or mutation, system-wide perf events, keyring access, file-status and pipe-capacity mutation, packet or notification pipes, and resource-limit mutation; core-dump suppression; and required completeness classes. Selection and construction remain outside this module.
  output_contract:
    registered_outputs:
      - ExecutionEvidenceV1
    boundary: Return one immutable current-run record that correlates every request digest with ordered capability, exec-chain, process, filesystem, network, stream, completeness, outcome, and cleanup observations. Event-specific provenance identifies identity.seal as openat2/fstat/SHA-256/memfd-seal evidence created before release and identifies exec.ptrace separately as ptrace/procfs evidence; it also retains the exact syscall-ceiling number, EPERM control, and filter identity. Historical members may exit normally only after an acknowledged namespace-PID/starttime/cgroup report is mapped, pidfd-bound and revalidated by the outer supervisor; their records are merged with the frozen live set and the cumulative union remains within max_processes. Stream retention is represented only by bounded counts and retained-file observation only by pre-cleanup identities; no stdout, stderr, structured-result, or file payload is returned or durably retained. No field carries an absolute zero-effect or hard-zero conclusion; caller-supplied names and paths are typed data and are not interpreted as conclusions. Evidence is neither independently attested nor durable anti-replay proof.
  error_contract:
    registered_error_semantics:
      - invalid_request_or_unsupported_capability_blocks_before_workload_release
      - policy_identity_observation_limit_timeout_or_cleanup_failure_fails_closed
      - missing_or_not_reached_observation_forces_incomplete_evidence
    boundary: Invalid identity, digest, path, quota, executable chain, profile, host, privilege, namespace, cgroup, mount, capability, seccomp, descriptor, observation, stream, timeout, process-tree, survivor, or cleanup state blocks or produces the exact non-success outcome. Any observation loss, sequence gap, provider error, survivor, cleanup residue, FAIL, or NOT_REACHED stage forces complete=false; no fallback backend or caller assertion may turn it into success.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes:
      - data_write
      - generated_artifact_write
      - database_write
    direct_effects:
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/isolated_execution/linux_backend.py
        boundary: Create only execution-ID-owned private roots, namespace mounts, quota-bound tmpfs objects, cgroup controls, sealed executable-chain objects, bounded stream buffers, retained outputs, and cleanup journal state; remove every creator-owned transient resource before return.
    delegated_effects:
      - capability_id: bounded-isolated-workload-private-output
        capability_state: conditional-delegated-maximum
        effect_classes:
          - data_write
          - database_write
        evidence_paths:
          - src/tool_system/isolated_execution/linux_backend.py
        activation_condition: A separately authorized caller supplies a valid IsolationRequestV1 and invokes the sole Linux native supervisor on a host that passes every frozen capability gate.
        boundary: The unprivileged workload may read only the request-approved input roots, may write arbitrary quota-bound scratch data including a database, and may write output bytes only to the exact pre-created regular files named by retained_output_paths beneath non-writable parent directories. Every request-declared root, execution-owned boundary, retained-output, and executable-chain interface path is limited to 64 components; input-tree and workload-private descendants remain bounded by scan or byte/inode and cleanup traversal limits rather than an asserted depth. Each input root is identity-pinned and bind-mounted read-only, and an fd-relative no-follow, no-cross-device pre-release scan accepts only directory, regular-file and symlink entries, with at most 4096 entries per root and 16384 across the request; it rejects FIFO, socket, character-device, block-device, unknown, raced, or over-limit entries. Input content is not claimed to be an immutable snapshot of the trusted host. Every undeclared output object and all write access to input roots block; provider controls, the rest of the host, undeclared repositories, network, external services, and production remain unavailable. Classification grants no execution authority.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve every IsolationRequestV1 and ExecutionEvidenceV1 field and digest, exact Linux/x86_64 profile, capability-set gate, Linux v6.18 native syscall exclusive ceiling 470 and its exact EPERM evidence, event-specific identity-seal versus ptrace provenance, namespace and cgroup ownership, root-identity and special-inode input gates, private-root and quota enforcement, deny-all network, sealed descriptor exec chain, executable-chain TOCTOU observation, denial of every secondary exec and shared VM/filesystem/file-table/signal-handler clone state while ordinary fork/vfork and parent-wait semantics remain available through acknowledged historical pidfd records, pathless writable memfd, legacy and at-family xattr, host-inode lock/lease/write-hint/delegation, filesystem-wide and quota sync, every ioctl, shared legacy futex and futex2, membarrier, same-UID host-scope priority, system-wide perf events, keyring, core-dump, file-status, pipe-capacity, packet-pipe, and resource-limit controls, FD-bound filesystem-limit attribution, exact whole-composition process accounting, incremental raw-byte stream limits with the frozen pipe/overshoot bounds, immediate frozen whole-cgroup limit termination, full non-limit grace, monotonic timeout, conjunctive completeness, outcome taxonomy, no-fallback rule, and no-absolute-zero rule.
    interface_incompatible_change: Any new backend, supported OS or architecture, request/evidence field removal, weaker identity or cleanup check, ordinary-host fallback, external service, new dependency, or authority-bearing conclusion requires a new aggregate interface version and separate authorization.
  rollback_contract:
    rollback_identity: tool-system@fd145b8efa1d46bf864b5ac1d42e5916f897b959:isolated_execution@absent
    method: Revert the module through a separately audited pull request; remove only exact execution-ID-owned runtime resources after ownership verification, never an unresolved or foreign resource.
  replacement_contract:
    activation_rule: Replace only after request and evidence schema tests, real Linux/x86_64 Hosted capability and backend tests, the complete frozen filesystem, quota, process, network, race, stream, timeout, evidence, cascade, and cleanup adversarial matrix, module-registry closure, repository-manifest closure, and full unchanged Hosted CI pass without skip, xfail, mock, unexpected observation loss, residue, or fallback. Every record claimed complete must contain no observation loss; expected adversarial SIGBUS, positive-short-counted-FD-write, and pathname-backed-quota-errno cases must instead prove the exact fail-closed observation-incomplete outcome.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: request-bound-read-only-input
      contract: A repository, if explicitly supplied as an input root, has its root device, inode, and mode pinned and rechecked, is scanned fd-relatively without following links or crossing devices within the exact 4096-entry per-root and 16384-entry per-request bounds, accepts only directory, regular-file and symlink entries, and is mounted read-only inside the private root; its ordinary contents are not copied, hashed, or claimed as an immutable snapshot. No repository path is assumed, selected, or made writable by this module.
    data:
      mode: immutable-request-current-run-evidence
      contract: Request and evidence values are immutable and bounded; scratch data and declared output-file bytes exist only under request quotas and exact current-run correlation, undeclared output objects block, and only frozen counts or identities enter evidence before all private bytes are removed.
    artifact:
      mode: execution-owned-private-and-fully-cleaned
      contract: The supervisor creates only execution-ID-owned private roots, mounts, cgroups, namespace references, sealed objects, buffers, journals, and bounded outputs, and authenticates ownership before cleanup. Cleanup failure overrides every earlier success.
    database:
      mode: no-provider-schema-private-workload-only
      contract: The module owns no database, schema, migration, or durable anti-replay store; an approved workload may create arbitrary database objects only inside private scratch and may write database bytes in output only when the exact regular-file path is declared by retained_output_paths.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: request-bound-read-only-inputs-and-executable-chain
        access: read-only
        evidence_paths:
          - src/tool_system/isolated_execution/contract.py
          - src/tool_system/isolated_execution/linux_backend.py
        evidence_symbols:
          - IsolationRequestV1
          - ReadOnlyRootV1
          - ExpectedFileIdentityV1
          - LinuxNativeSupervisorV1
        boundary_parameters:
          - read_only_inputs
          - source_path
          - private_path
          - entrypoint
          - interpreter
          - loader
        constraint: Resolve only caller-bound canonical roots and executable-chain objects with no Linux path exceeding 64 components. Pin and recheck each root device, inode, and mode; accept only directory, regular-file and symlink entries within 4096 entries per root and 16384 across the request through an fd-relative no-follow and no-cross-device scan; reject every special IPC/device, unknown, raced or over-limit entry; and expose trusted-host content only through the request-bound read-only mount. Separately reject executable-chain symlink or magic-link ambiguity and identity drift, copy each executable-chain object to a write-sealed descriptor, and expose only those sealed bytes at the immutable private paths.
      - root_id: execution-owned-private-runtime-roots
        access: read-write
        evidence_paths:
          - src/tool_system/isolated_execution/linux_backend.py
        evidence_symbols:
          - LinuxNativeSupervisorV1
          - execute_isolation_request_v1
        boundary_parameters:
          - execution_id
          - cwd_private_path
          - scratch_private_path
          - output_private_path
        constraint: Create and clean only exact execution-ID-owned temporary, cgroup, namespace, scratch, and output resources; never claim, traverse for cleanup, or remove a foreign or unresolved path.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: linux-kernel-isolation-abi
        mode: trusted-local-linux-x86-64-supervisor
        evidence_paths:
          - src/tool_system/isolated_execution/linux_backend.py
        boundary: Use CPython standard-library bindings to the Linux kernel ABI for namespaces, private propagation, pivot_root, tmpfs quotas, cgroup v2, openat2, execveat, ptrace, pidfds, seccomp, monotonic deadlines, stream drainage, cgroup.kill, populated=0, and ownership-authenticated cleanup. The v1 filter is audited through Linux v6.18 x86_64 syscall 469 and fails every native number at or above its exclusive ceiling 470 with EPERM; advancing that ceiling requires a newly audited profile. No container runtime, daemon, helper binary, package, or external service is a fallback.
      - system_id: sealed-local-workload-process
        mode: approved-unprivileged-private-root-execution
        evidence_paths:
          - src/tool_system/isolated_execution/linux_backend.py
        boundary: Release only the exact sealed executable chain after every gate passes, with empty supplementary groups, zero effective capabilities, no_new_privs, closed inherited descriptors, deny-all network, every secondary exec denied at its ptrace syscall-entry, and CLONE_VM, CLONE_FS, CLONE_FILES, CLONE_SIGHAND, CLONE_THREAD, CLONE_UNTRACED, and namespace-sharing clone flags denied while ordinary fork, vfork and parent wait remain permitted through acknowledged historical pidfd records. Deny memfd_create/memfd_secret, legacy setxattr/removexattr and setxattrat/removexattrat mutation, open_tree_attr, file_setattr, flock, every ioctl, sync/syncfs, quotactl/quotactl_fd, every futex2 syscall, shared legacy-futex operations while preserving process-private legacy futex use, membarrier, getpriority/setpriority/ioprio_get/ioprio_set, system-wide perf_event_open, keyring access, setrlimit, and prlimit64; deny every native x86_64 syscall number at or above the Linux v6.18 exclusive ceiling 470; deny the exact fcntl file-status/lock/lease/pipe-size/inode-write-hint/delegation commands and pipe2 packet/notification modes while preserving ordinary pipes. The exact-filter controls run in gated outer-supervisor processes before workload release; filtered fork/vfork positives are additionally pidfd-bound inside an execution-owned auxiliary cgroup, and the evidence scope is outer_supervisor_pre_workload_release. Require a non-pipe core_pattern and immutable RLIMIT_CORE=0; retain a whole-composition process limit of at least three including two fixed provider supervisors, OS-read-back 4096-byte stream pipes with maximum final overshoot of 4097 bytes per stream or 8193 combined bytes, FD-only exact-scope RLIMIT_FSIZE correlation, bounded time/filesystem resources, complete exec observation, immediate frozen whole-cgroup limit termination, full non-limit grace, and whole-cgroup cleanup. Any pathname-backed quota errno, any observed positive short result from the counted FD-target write ABIs write, pwrite64, writev, sendfile, splice, pwritev, copy_file_range, or pwritev2, or any SIGBUS forces observation-incomplete evidence and never forms a complete LIMIT or SUCCESS conclusion. This profile denies global and host-cross-process control surfaces but makes no absolute claim that private-workload fsync, fdatasync, msync, page-cache, atime, or host-I/O scheduling effects are zero.
  non_claims:
    provider_execution_authorized: false
    target_repo_mutation_authorized: false
    cleanup_execution_authorized: false
    production_operation_authorized: false
  authority_boundary:
    execution_authority: false
    downstream_authority: false
    evidence_role: tool-system-module-contract
    change_boundary: separately-audited-module-change
~~~
<!-- MODULE-COMPOUND-CONTRACT:END -->
