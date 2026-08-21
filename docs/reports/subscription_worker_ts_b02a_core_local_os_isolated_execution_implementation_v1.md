# TS-B02A core local OS isolated execution implementation v1

## 1. Authority and exact clean base

Task identity:
`TOOL-SYSTEM-TS-B02A-CORE-LOCAL-OS-ISOLATED-EXECUTION-IMPLEMENTATION-v1`.

Before any repository write, the authenticated GitHub App read
`refs/heads/main` and then the referenced Git commit object in that order. The
two observations and the independent local checkout agreed exactly on:

- commit: `fd145b8efa1d46bf864b5ac1d42e5916f897b959`;
- tree: `5506864efd9df88fe87a6189eade4d929c364076`.

The authorized branch is
`agent/subscription-worker-ts-b02a-core-local-os-isolated-execution-v1`; the
only authorized commit message is
`Implement TS-B02A core local OS isolated execution`.

This package implements only the new `isolated-execution` durable module and
its version-1 request/evidence interface. It neither integrates an existing
worker or runner nor runs a real repository, business workload, Codex,
subscription transport, provider, or API.

## 2. Parent and blueprint alignment

The immediate parent is Sections 9 through 13 of
`subscription_worker_ts_b02a_core_local_os_isolation_hosted_capability_probe_observation_and_cascade_repair_v1.md`.
Those sections freeze `IsolationRequestV1`, `ExecutionEvidenceV1`, the sole
`linux_native_supervisor_v1` backend, the exact 17-path implementation closure,
the zero-consumer start state, standard-library/Linux-ABI dependency boundary,
and the complete adversarial matrix.

The global anchor remains `blueprint/tool_system_v0.yaml:product_objective`.
This module advances the approved bounded local-workload flow while retaining
`arbitrary_untrusted_code_containment` as a non-goal. The trusted operator,
host, kernel, and provider supervisor remain outside the workload threat
boundary. The record is current-run OS-derived evidence, not caller-independent
attestation, a second trust root, or durable cross-run anti-replay proof.

## 3. Durable module and ownership boundary

The registry adds exactly one module:

| Property | Frozen value |
| --- | --- |
| canonical module | `isolated-execution` |
| Python identity | `isolated_execution` / `tool_system.isolated_execution` |
| module version | `1.0.0` |
| public interface | `isolated-execution-api` `1.0.0` |
| backend | `linux_native_supervisor_v1` only |
| supported host | Linux/x86_64 only |
| runtime dependencies | supported CPython standard library and Linux kernel ABI |
| direct providers | none |
| direct consumers | none |
| rollback identity | `tool-system@fd145b8efa1d46bf864b5ac1d42e5916f897b959:isolated_execution@absent` |

Isolated-execution owns request validation, capability gating, object sealing,
enforcement, execution, bounded output accounting and identity observation,
exact-owned cleanup, and construction of `ExecutionEvidenceV1`. Future TS-B02B owns worker
selection and request construction. Future TS-B02C owns independent record
matching and the TS-B01/TS-B02 join. This package creates neither edge.

## 4. `IsolationRequestV1`

The public request is an immutable typed value with a canonical JSON SHA-256
identity derived by the implementation rather than trusted from a caller. Its
frozen groups are:

- request schema, execution identity, task/source/candidate/workspace,
  configuration and policy digests;
- the exact backend and required-capability-set digest, with no fallback field;
- canonical identity-bound read-only roots, request-declared boundary,
  retained-output and executable-chain interface paths capped at 64
  components, distinct private cwd, scratch and output paths, byte/inode
  quotas, bounded retained outputs, and the fixed pre-release scan policy that
  accepts only directories, regular files and symlinks within 4096 entries per
  root and 16384 entries across the request;
- executable format, exact device/inode/mode/size/SHA-256 identity, argv and a
  sorted bounded environment without PATH or dynamic-loader injection;
- separately sealed script, interpreter and ELF `PT_INTERP` loader identities;
- non-root UID/GID, empty supplementary groups, zero effective capabilities,
  `no_new_privs`, denial of secondary exec, shared VM/filesystem/file-table/
  signal-handler clone state, pathless memfd resources, xattr mutation,
  host-inode locks/leases/write hints/delegation, filesystem-wide and quota
  sync, every ioctl, shared legacy futex and every futex2 operation,
  `membarrier`, same-UID host-process priority inspection/mutation,
  system-wide perf events, keyring access,
  file-status and pipe-capacity mutation, packet/notification pipes and
  resource-limit mutation, plus core-dump suppression;
- `deny_all` networking, loopback administratively down, no inherited network
  descriptors, and the exact socket-denial filter identity, including the
  Linux v6.18 x86_64 audited native syscall range 0 through 469 and an
  exclusive ceiling of 470 whose number and direct `EPERM` control are bound
  into current-run evidence;
- independent raw stdout, stderr, combined and retained-byte limits with
  continuous byte drainage before decoding; and
- a monotonic deadline, finite termination grace, exact cgroup identity,
  process maximum of at least three members (the two fixed provider
  supervisors plus at least one workload member), the v1 single-thread
  policy, output bounds, and the exact required observation classes.

Validation is pure and runs before any workload release. Wrong schema,
profile, capability digest, path, object identity, executable-chain shape,
environment, UID/GID/capability setting, network policy, quota, stream limit,
deadline, cgroup identity, or completeness requirement is a fail-closed
request result rather than a weaker execution route.

## 5. `ExecutionEvidenceV1`

Only isolated-execution constructs the immutable evidence record. It binds the
request digest and all correlation digests to monotonic start/finish values and
records:

- ordered `PASS`, `FAIL`, and `NOT_REACHED` capability stages plus an acyclic
  dependency graph whose blocked chains terminate at a real failure;
- ordered kernel-/proc-/cgroup-derived observations with stable event IDs,
  classes, sources, monotonic times and canonical immutable payload bytes;
- requested and actual entrypoint, script, interpreter and loader identities
  plus open, seal, recheck, exec and ptrace observations;
- exact cgroup membership, pidfd/starttime identity, process events, secondary
  exec denials, FD-bound limit or timeout trigger, `cgroup.kill`,
  `populated=0`, and scoped survivor result;
- effective read-only roots, scratch/output usage and quota observations,
  post-bind root device/inode/mode and bounded special-inode scan observations,
  denied boundary attempts, scratch/output usage and quota observations,
  retained-output identities and teardown;
- network namespace identity, loopback flags, diagnostic-only operstate,
  inherited-FD closure, seccomp identity and denial observations;
- raw emitted, retained and discarded stdout/stderr/combined counts and decode,
  overflow and observer-loss status; and
- every cleanup class, missing-observation class, sequence gap, provider or
  observer error, buffer-loss flag and final outcome.

Completeness is derived, never caller-set. Every required observation class,
contiguous sequence, stage, identity match, teardown, survivor result and
cleanup class must be present. A `FAIL`, `NOT_REACHED`, missing or duplicate
observation, sequence gap, provider/observer error, overflow, survivor or
residue forces `complete=false`. A workload failure, enforced limit, or timeout
may still have complete evidence only when its expected trigger, whole-cgroup
termination and cleanup are fully observed.

No evidence field carries or authorizes an absolute `zero_effect` or
`hard_zero` conclusion. Caller-supplied names and paths remain typed path data
and are never interpreted as conclusions. Numeric zero is scoped only to the
matching execution and matching OS observation interval.

The v1 return surface is evidence-only. Retained stream values are counts and
retained-file values are identities observed after writers are stopped and
before cleanup; stdout, stderr, structured-result and file payload bytes are
not returned or retained. Any future consumer-facing byte transport belongs to
a separately authorized interface extension and is not pre-created for
TS-B02B here.

## 6. Linux native supervisor enforcement

The sole backend fails before workload release unless Linux, x86_64, root
supervisor privilege, unified writable private cgroup v2 and all required
kernel ABIs are present. There is no ordinary-host, Docker, runc, bubblewrap,
container-engine, hash-only, self-report, mock, skip, xfail, or best-effort
fallback.

For an accepted request the supervisor:

1. identity-opens request roots and executable-chain objects with safe
   resolution, keeps each selected root descriptor pinned, rechecks its
   post-bind device/inode/mode, and performs an fd-relative,
   no-follow/no-cross-device scan that accepts only directory, regular-file
   and symlink entries within 4096 entries per root and 16384 across the
   request, rejecting FIFO, socket, device, unknown, raced, or over-limit
   entries; it separately seals executable-chain bytes
   against path replacement and in-place mutation. The `identity.seal` event
   records its actual `openat2`, `fstat`, SHA-256 and memfd-seal provenance;
   ptrace/procfs provenance is reserved for the later `exec.ptrace` event;
2. claims execution-ID-owned cgroups without adopting a collision, applies
   process/resource controls, and gates the child before release;
3. creates distinct mount/PID/network/IPC/UTS namespaces, makes propagation
   recursively private, builds quota-bound private filesystems, binds only
   request-approved read-only roots, and enters the private root with
   `pivot_root`;
4. keeps loopback administratively down, closes inherited descriptors, installs
   the exact cBPF program, denies all socket creation, privileged mount,
   namespace and ptrace operations, legacy AIO and io_uring setup, x32 syscalls,
   `clone3`, and `clone` carrying namespace, `CLONE_VM`, `CLONE_FS`,
   `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, or `CLONE_UNTRACED` flags,
   while retaining ordinary `fork` and `vfork`; after the x32 kill rule, an
   unsigned cBPF comparison denies every native syscall number at or above the
   Linux v6.18 exclusive ceiling 470 with `EPERM`, and a direct raw
   `syscall(470)` pre-release control must observe `EPERM`, never `ENOSYS`; it
   denies pathless `memfd_create`/`memfd_secret`, legacy and at-family xattr
   mutation, `open_tree_attr`, `file_setattr`, `flock`,
   every `ioctl`, `sync`/`syncfs`, `quotactl`/`quotactl_fd`, every futex2 syscall, shared legacy-futex operations while
   retaining process-private legacy futex use, `membarrier`,
   `getpriority`/`setpriority`/`ioprio_get`/`ioprio_set`, system-wide
   `perf_event_open`, keyring access, `setrlimit`, and `prlimit64`. It
   separately denies the exact fcntl
   file-status/lock/lease/pipe-size/inode-write-hint/delegation commands,
   including `F_SETFL`, and `pipe2` packet/notification modes while preserving
   ordinary pipes; it then empties supplementary groups, drops UID/GID and
   capabilities, and sets `no_new_privs`; a host
   pipe-form `core_pattern` blocks before release and the child inherits
   immutable `RLIMIT_CORE=0`;
5. descriptor-executes the sealed ELF or sealed interpreter/private script,
   observes `PTRACE_EVENT_EXEC`, maps the namespace PID to one host PID in the
   exact cgroup, and binds the actual executable/loader maps, argv/environment,
   stdio pipe identities, inherited-FD set, seccomp baseline-plus-one state and
   `RLIMIT_FSIZE=max(scratch_byte_limit,file_output_byte_limit)` to the request;
6. observes workload syscalls and exit stops; before each exec, fork/vfork/
   clone birth, or committed exit resumes, it reports the namespace PID,
   starttime and exact cgroup, waits for the outer supervisor to map, pidfd-bind
   and revalidate that member, and retains the pidfd-backed historical record
   after an ordinary parent-visible exit; every secondary `execve`/`execveat`
   is replaced at syscall entry with an evidenced `EPERM`; a filesystem-limit
   trigger is accepted only from an FD-bound object when the syscall errno
   class and target scope are frozen and the matching private quota or exact
   process file-size limit corroborates it; pathname-backed failures never
   form a complete LIMIT conclusion. Any SIGBUS or observed positive short
   result from the counted FD-target write ABIs `write`, `pwrite64`, `writev`,
   `sendfile`, `splice`, `pwritev`, `copy_file_range`, or `pwritev2` instead
   forces observation-incomplete evidence;
7. continuously drains both raw streams through OS-read-back 4096-byte pipes,
   enforces stdout, stderr and combined limits, applies the monotonic deadline,
   and freezes then terminates the full exact cgroup immediately on a limit;
   the final exact post-kill drain permits at most 4097 bytes of single-stream
   overshoot or 8193 combined bytes, including the first crossing byte;
8. freezes the cgroup, merges every historical member with the live full-set
   snapshot, and pidfd/starttime/cgroup-revalidates the union; non-limit
   outcomes receive the full finite grace, while a limit has an equal start/
   finish zero-length grace interval and proceeds directly to `cgroup.kill`;
   every pidfd exit and `populated=0` is required, and output is snapshotted
   only after all writers are gone; and
9. closes every gate and descriptor, reaps creator-owned children with bounded
   waits, performs a time/node/finding-bounded host residue scan, and unmounts
   and removes only ownership-marker and device/inode matching execution-owned
   resources; workload-private trees are removed within a separately bounded
   depth/node traversal.
   Cleanup failure or residue overrides every earlier success.

The exact-filter synthetic controls are emitted only from gated
outer-supervisor processes before workload release. The ordinary `fork` and
`vfork` positives run after filter installation inside an execution-owned
auxiliary cgroup, are pidfd-bound before release, and are killed, reaped and
observed at `populated=0`; the evidence freezes their shared scope as
`outer_supervisor_pre_workload_release`.

The profile denies global and host-cross-process control surfaces. It does not
claim that private-workload `fsync`, `fdatasync`, `msync`, page-cache, atime,
or host-I/O scheduling effects are zero; no such effect can be promoted to an
absolute zero-effect or hard-zero conclusion.

## 7. Frozen adversarial coverage

The three module-owned suites cover the full parent matrix:

| Domain | Required controls |
| --- | --- |
| capability | unsupported OS/architecture, non-root, missing syscall/cgroup/mount/ptrace/pidfd/seccomp capability blocks before release; exact Linux v6.18 native x86_64 range 0..469, exclusive ceiling 470, filter-identity binding, and direct raw `syscall(470)=EPERM` controls; no fallback |
| filesystem | positive in-root access; post-bind root identity; bounded special-inode scan; FIFO/socket/device, traversal, symlink, magic-link, mount crossing, undeclared-output, provider-control, proc/sys/dev-view and host-sentinel denial; scratch/output byte and inode quotas; pathless memfd, legacy and at-family xattr mutation, `open_tree_attr`, `file_setattr`, host-inode locks/leases/write hints/delegation, global sync, quota-sync through `quotactl`/`quotactl_fd`, every ioctl, `F_SETFL`, packet/notification pipes, same-UID host priority operations, and system-wide `perf_event_open` return `EPERM` while the matching permitted controls remain usable |
| selection and exec | basename/PATH/symlink/rename/in-place races; descriptor-sealed native exec; separately sealed script/interpreter; parsed-loader and exec-map identity |
| process | setsid, double fork, reparent, TERM-ignore, timeout survivor and ptrace cases remain in the exact cgroup; fast exits become pidfd-backed historical members only after an acknowledged identity bind and ordinary fork/vfork plus parent wait remain available; filtered fork/vfork positives run in an owned auxiliary cgroup and freeze the truthful pre-workload-release scope; `CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, `CLONE_UNTRACED`, namespace-sharing clone flags, shared legacy futex, every futex2 syscall, `membarrier`, and secondary exec return `EPERM`; process-private legacy futex remains usable; namespace PIDs map to exact host PID/starttime/cgroup identities; the cumulative historical/live union is bounded by `max_processes`; pidfd identity precedes signals; cleanup reaches `populated=0` |
| network | loopback, DNS, IPv4/IPv6, netlink/packet, inherited-FD and namespace-bridge attempts fail under positive controls |
| output and time | independent stdout, stderr and combined raw limits; OS-read-back 4096-byte pipe capacity, denied `F_SETPIPE_SZ`, final capacity readback, immediate break after the first crossing event, repeated simultaneous dual-pipe pressure, exact post-kill accounting, and safe maximum overshoots of 4097/8193 bytes; FD-backed ENOSPC/EDQUOT require actual private-quota saturation, and FD-backed EFBIG requires both the observed exact `RLIMIT_FSIZE=max(scratch_byte_limit,file_output_byte_limit)` and a target scope whose byte limit equals it; any SIGBUS (including self-raised SIGBUS), observed positive short result from `write`/`pwrite64`/`writev`/`sendfile`/`splice`/`pwritev`/`copy_file_range`/`pwritev2`, or pathname-backed quota errno (ENOSPC/EFBIG/EDQUOT) is observation-incomplete and never a complete LIMIT or SUCCESS proof; `setrlimit`/`prlimit64` cannot mutate provider-frozen limits; limits freeze and kill without a TERM grace, while other terminal states preserve the requested grace; monotonic timeout uses the workload-exit or timeout-trigger timestamp rather than cleanup finish; whole-cgroup kill, output inode-ceiling readback, and bounded retained-output identity observation |
| evidence | wrong/stale/duplicate request, policy, object or cgroup identity; event-specific `identity.seal` descriptor/hash/seal provenance distinct from `exec.ptrace` ptrace/procfs provenance; exact syscall-ceiling number/filter/errno evidence; app/self-report substitution; missing class, gap, overflow, observer loss or malformed cascade blocks |
| cleanup | any cgroup, namespace FD, mount, cwd/root/fd, process, pidfd task, ownership record or temporary-root residue overrides prior passes; deep private trees are removed and every host residue scan is time/node/finding bounded |

All executable fixtures are bounded synthetic ELF, shebang, finite stream,
sleep and process-tree workloads created under test-owned temporary roots. The
Hosted tests compile temporary bounded synthetic ELF fixtures under those
roots. Their number creates no repository path, runtime dependency or
repository artifact; the compiler remains a test-environment capability only.

The trusted host and provider remain outside the workload threat boundary.
Read-only input roots are root-identity-pinned and special-inode-gated but are
not copied into content-addressed snapshots; this package therefore does not
claim that trusted-host changes to ordinary input content are impossible. The
TOCTOU completion claim is limited to the executable, script, interpreter and
loader chain that is copied to immutable sealed descriptors and matched at the
actual exec stop.

## 8. Exact path and dependency closure

The package modifies exactly six paths and adds exactly eleven paths named in
the authorized task manifest and change plan. The report and task pair remain
retained non-authority inputs; the module contract, four source files and three
tests are registered as exact formal paths. Every added path is a regular
`100644` file.

No third-party source is copied. Linux syscall/UAPI use remains at the syscall
boundary; Linux UAPI headers carry `GPL-2.0 WITH Linux-syscall-note`. Existing
CPython and system-runtime licenses remain external installation facts. No
package, vendored code, binary artifact, daemon, external service, workflow,
runner, permission, dependency or supply-chain change is introduced.

## 9. Verification and terminal predicate

The frozen terminal predicate requires all of the following on the terminal
candidate:

- the three focused isolated-execution suites and affected module-contract,
  module-registry and repository-manifest suites pass;
- full pytest and the unchanged Hosted active-gate, process-authority,
  module-registry and repository-manifest validators pass;
- the strict task manifest and its bound change plan pass;
- exact six-modification/eleven-addition path and `100644` mode closure passes;
- `git diff --check` passes;
- the real Hosted backend and adversarial executions contain no skip, xfail,
  mock, fallback, unexpected observation loss or cleanup residue; every record
  claimed complete has no observation loss, while the explicitly adversarial
  SIGBUS, positive-short-counted-FD-write and pathname-backed-quota-errno cases reach their
  required fail-closed observation-incomplete outcomes; and
- base, head, path, commit, review and thread state remain unchanged before
  Draft-to-Ready and squash merge.

Failure of any Hosted capability or cleanup predicate leaves the pull request
Draft and stops this task. Success permits only the authorized Ready transition
and squash merge while retaining the original feature branch. Neither outcome
starts TS-B02B, TS-B02C, TS-B02D or real execution.

## 10. Preserved state and non-claims

- TS-B01 remains `corrected_pending_reacceptance`.
- TS-B02 remains blocking and is not corrected by this zero-consumer module.
- The subscription-worker public entry remains unreaccepted.
- Real repository and business execution remain blocked.
- TS-H01, TS-H02, TS-H03, TS-M01, TS-M02 and TS-M03 remain unchanged.
- README, project state, phase alignment and public acceptance are unchanged.
- `integrated_conformance_proved=false`.
- `public_acceptance_changed=false`.
- No independent cloud service, verifier, KMS/HSM, OIDC, durable anti-replay,
  cross-run atomic receipt consumption, external infrastructure or production
  operation is implemented or claimed.

## References

- Active blueprint: `blueprint/tool_system_v0.yaml`
- Immediate parent:
  `docs/reports/subscription_worker_ts_b02a_core_local_os_isolation_hosted_capability_probe_observation_and_cascade_repair_v1.md`
- Module contract: `docs/modules/isolated-execution-contract-v1.md`
- Linux cgroup v2: <https://docs.kernel.org/admin-guide/cgroup-v2.html>
- Linux `openat2(2)`: <https://man7.org/linux/man-pages/man2/openat2.2.html>
- Linux `execveat(2)`: <https://man7.org/linux/man-pages/man2/execveat.2.html>
- Linux `ptrace(2)`: <https://man7.org/linux/man-pages/man2/ptrace.2.html>
