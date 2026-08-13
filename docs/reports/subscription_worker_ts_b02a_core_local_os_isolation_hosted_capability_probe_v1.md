# TS-B02A core local-OS isolation Hosted capability probe v1

## 1. Authority, canonical input, and result boundary

Task identity:
`TOOL-SYSTEM-TS-B02A-CORE-LOCAL-OS-ISOLATION-HOSTED-CAPABILITY-PROBE-v1`.

Before any repository write, the authenticated GitHub App read
`refs/heads/main` and then the referenced Git commit object in that order. The
observed canonical input exactly matched:

- commit: `71544c0c3bb37b1f4cb8bacbf4dc332477c94ccc`;
- tree: `27bea1f06a51c3f416963724ac132aebd8c16a1f`.

This report, its task pair, the one synthetic test, and the two exact repository-
manifest registration updates are the whole authorized repository surface. The
GitHub App is the authorized publication control plane because the construction
environment has no `gh`. No workflow, runner, permission, dependency, supply-
chain, source-runtime, module-registry, project-state, public-acceptance, finding,
external-security-service, infrastructure, or business target is changed.

The test has exactly three semantic dispositions:

| Disposition | Meaning |
| --- | --- |
| `NOT_EXECUTED` | The process is not running on an identified GitHub-hosted Actions runner. It is not capability evidence and never becomes capability PASS. |
| `HOSTED_CAPABILITY_PASS` | One actual GitHub-hosted `ubuntu-latest` job completed every conjunctive primitive, composition, observation, limit, termination, and cleanup assertion without skip, xfail, mock, or fallback. |
| `HOSTED_CAPABILITY_BLOCKER` | Any required identity, primitive, composition, observation, positive control, denial, resource limit, termination, or cleanup assertion was absent or failed. The PR remains Draft and work stops. |

`HOSTED_CAPABILITY_PASS` proves only that the selected backend design has no
known blocker on the exact observed Hosted job. It does **not** prove integrated
TS-B02A conformance, implement `isolated-execution`, correct TS-B02, reaccept a
public entry, or authorize any successor package.

## 2. Parent and blueprint alignment

The controlling parent is Section 6.1 of
`subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_specification_v1.md`.
It requires a separately authorized, bounded, non-live feasibility surface
before TS-B02A runtime work. The active blueprint still excludes an arbitrary
untrusted-code containment service. The profile here instead contains a bounded,
approved, unprivileged workload under a trusted operator, host, kernel, and
provider supervisor.

The probe therefore answers a narrow question: can a project-owned local Linux
supervisor assemble and observe the frozen TS-B02 core-isolation controls on the
supported host class? It does not test a malicious host, kernel, operator, or
provider, and it creates no caller-independent attestation, durable anti-replay,
or external trust claim.

## 3. Frozen backend selection

The sole candidate for core v1 is `linux_native_supervisor_v1`:

- a project-owned, host-local supervisor;
- implemented behind the future `isolated-execution-api` v1 boundary;
- using CPython standard-library control code and direct Linux syscall/ioctl/file
  interfaces rather than Docker, runc, bubblewrap, or an external service;
- starting with the host privileges required to create the execution boundary;
- dropping the synthetic workload to an unprivileged UID/GID with zero effective
  capabilities and `no_new_privs` before the sealed exec;
- using one private cgroup v2 subtree as the process membership, termination, and
  survivor authority;
- using mount, PID, network, IPC, and UTS namespaces; private mount propagation;
  `pivot_root`; read-only executable/interpreter/loader objects; quota-bound
  tmpfs; a loopback-down network namespace plus seccomp socket denial and a
  closed inherited-FD set; and
- using `openat2`, `execveat`, `PTRACE_EVENT_EXEC`, `/proc` identity observation,
  pidfds, monotonic deadlines, incremental raw-byte drainage, `cgroup.kill`, and
  `cgroup.events populated=0` to form current-run evidence.

Bubblewrap is not selected because its own security model leaves policy assembly
to the caller and does not itself provide the complete TS-B02 evidence boundary.
runc and Docker are not selected because their OCI/container-daemon boundaries
do not directly own the requested descriptor-sealed exec, interpreter/loader
identity match, stream accounting, or `ExecutionEvidenceV1` semantics. They may
not be used as a fallback.

## 4. Supported host and fail-before-workload capability gate

Core v1 support is frozen to `Linux/x86_64`. The first empirically qualified host
class must be an actual GitHub-hosted `ubuntu-latest` x64 VM reached through the
unchanged repository workflow. A moving runner label or package inventory is
not evidence by itself; the test rechecks the observed environment and kernel
effects on every run.

The future provider capability gate is conjunctive and must finish before it
releases the first approved workload instruction. A tiny trusted gate process
may exist solely to stop before exec and accept cgroup attachment; it is not the
workload. The gate requires:

1. Linux, x86_64, unified cgroup v2, and the required syscall ABI;
2. trusted-supervisor privilege sufficient for namespace, mount, cgroup, ptrace,
   UID/GID, and seccomp setup;
3. simultaneous mount/PID/network/IPC/UTS namespaces with IDs distinct from the
   provider namespace;
4. recursive private mount propagation;
5. a unique writable provider-created cgroup with `cgroup.kill` and observable
   `cgroup.events`;
6. private-root construction, `pivot_root`, read-only identity objects, and
   separate scratch/output byte and inode quotas;
7. loopback down, no usable inherited network descriptor, and a seccomp filter
   that returns `EPERM` for `socket(2)` in the fixed ABI;
8. working `openat2`, `execveat`, ptrace exec-stop observation, `/proc` executable
   and loader identity reads, pidfds, and monotonic time;
9. independent stdout/stderr nonblocking drainage with per-stream and combined
   raw-byte limits; and
10. a cleanup path able to kill the exact cgroup, observe `populated=0`, remove
    its directories, and demonstrate absence of execution-specific namespace,
    mount, process, FD, and temporary-root residue.

Any missing item is `HOSTED_CAPABILITY_BLOCKER`. There is no ordinary-host,
container-engine, weaker-network, hash-only, self-report, skip, xfail, mock, or
best-effort fallback.

## 5. Empirical Hosted proof shape

`tests/test_ts_b02a_core_local_os_isolation_backend_feasibility.py` is discovered
by the existing `python -m pytest -q` step. It does not alter the workflow. On a
non-Actions environment it returns one explicit `NOT_EXECUTED` observation and
does not invoke sudo or any privileged probe.

On an identified GitHub-hosted job, it requires the repository identity,
`GITHUB_RUN_ID`, Linux/X64 runner variables, `uname`, and `sudo -n id -u == 0`.
It then creates one unpredictable execution ID and creator-owned temporary root.
The root helper uses only bounded synthetic material: a temporary compiled ELF,
a shebang script, `true`/`false`, `sleep`, finite raw bytes, tiny tmpfs mounts,
and finite process trees. It never reads or executes a target repository or a
business workload.

Independent primitive probes are combined with one same-execution-ID smoke. The
combination creates all five namespaces, private mount propagation, a private
root, an unprivileged/capability-free exec, a private cgroup, sealed descriptor
execution, ptrace identity observation, finite output, a detached TERM-ignoring
descendant, cgroup termination, pidfd observation, `populated=0`, and exhaustive
cleanup. This is deliberately stronger than a list of unrelated syscall-exists
checks, but remains weaker than a complete implemented provider conformance run.

| Hosted capability | Positive control and required effect |
| --- | --- |
| runner/root gate | Exact GitHub-hosted identity plus real passwordless root execution. |
| namespaces | Each of mount/PID/net/IPC/UTS has a current-run inode different from the parent. |
| mount propagation | Root propagation becomes recursive private and the probe mount never appears in host mountinfo. |
| cgroup tree | Gated initial process, PID-namespace descendants, `setsid`, double-fork, reparent, and TERM-ignore remain members; `cgroup.kill` makes `populated=0`; exact directories are removed. |
| private root | `pivot_root` succeeds; old-root/host sentinel is unavailable; executable objects are read-only and scratch is separate. |
| quotas | Separate tiny tmpfs byte and inode probes each perform writes/creates until the kernel returns `ENOSPC`. |
| network | Loopback-up TCP exchange is the positive control; every inherited network FD is closed before exec; loopback is then down; connectivity fails; seccomp makes a new socket syscall return `EPERM`. |
| `openat2` | In-bound file open succeeds; `..`, ordinary symlink, proc magic link, and cross-mount attempts receive only the expected safe rejection. |
| native identity | Open and digest a temporary ELF, replace its selection path, execute the sealed FD with `execveat`, and match the exec-stop `/proc/PID/exe` device/inode. |
| script/interpreter | Parse and seal the script and interpreter separately; place the script in the private immutable root; explicitly `execveat` the sealed interpreter; match its actual exec identity. Direct shebang-FD exec is not treated as safe proof. |
| dynamic loader | Parse `PT_INTERP`, seal the loader object in the private read-only root, and at `PTRACE_EVENT_EXEC` match the actual `/proc/PID/maps` device/inode. A pre-exec digest alone cannot pass. |
| streams | Drain stdout/stderr concurrently as bytes; trigger the combined limit; preserve bounded emitted/retained/discarded counts. |
| timeout | Use a monotonic deadline, kill the exact timeout cgroup, observe its pidfd exit and `populated=0`. |
| cleanup | Cleanup runs even after failure and overrides every earlier PASS; no exact cgroup, namespace reference, host mount, process cwd/root/fd, pidfd-live process, or creator-owned temporary root may remain. |

The outer pytest process invokes an exact-ID cleanup helper in `finally`, so an
inner assertion, timeout, or malformed result cannot become PASS. A runner-level
SIGKILL can prevent a test result, but cannot manufacture a successful job.

## 6. `IsolationRequestV1` interface semantics

The future `isolated-execution-api` v1 accepts one immutable
`IsolationRequestV1`. Worker-adapter will own selection, caller expectation, and
construction; isolated-execution will own validation, sealing, enforcement, and
execution. Required semantics are frozen as follows:

| Field group | Required values and rules |
| --- | --- |
| request identity | schema version, unique execution ID, request digest, task/source/candidate/workspace identity, configuration identity, and policy digest |
| backend | exact `linux_native_supervisor_v1` profile and required capability-set digest; no fallback profile |
| filesystem | canonical input roots and read-only binds; execution-owned scratch/output locations; byte and inode quotas; explicit retained outputs; no provider-control path |
| executable | selection object, expected file type, device/inode/mode/size/SHA-256, argv, bounded environment, and PATH-disabled descriptor-exec rule |
| interpreter/loader | parsed format, exact sealed interpreter or `PT_INTERP` loader expectation, device/inode/mode/size/SHA-256, and private-root immutable-path rule |
| workload identity | unprivileged UID/GID, empty supplementary groups, zero effective capability set, `no_new_privs`, and denied privilege/control operations |
| network | `deny_all`, loopback-down, no inherited network descriptors, and socket-denial filter identity |
| streams | stdout/stderr per-stream and combined raw-byte limits, retained byte limit, decoding after accounting, and backpressure-independent continuous drainage |
| time/process | monotonic deadline, finite termination grace, exact cgroup identity, maximum process count, and survivor observation requirement |
| output | explicit structured-result and file-output limits plus completeness classes required for a matched record |

Canonicalization, symlink and magic-link refusal, digest calculation, backend
selection, and policy matching occur before release. The actual executable,
interpreter, loader, mount, cgroup, UID/GID, filter, and limit observations must
then match the request. No caller or workload field may substitute for an OS
observation.

## 7. `ExecutionEvidenceV1` interface semantics

Isolated-execution is the sole natural owner and producer of immutable
`ExecutionEvidenceV1`. The record is a current-run OS-derived enforcement and
observation record, not an independently attested or durable anti-replay receipt.
It contains:

| Field group | Mandatory content |
| --- | --- |
| correlation | schema, unique execution ID, request/task/source/candidate/workspace/config/policy digests, provider profile, start/finish monotonic values |
| capability | supported OS/architecture, actual gate results, namespace IDs, cgroup identity, private-root/mount identities, quota identities, UID/GID/capability/no-new-privileges observations, seccomp policy identity |
| exec chain | requested and actual executable, script, interpreter, and loader device/inode/mode/size/digest values; open/seal/recheck/exec/ptrace sequence; explicit mismatch or denial |
| process | cgroup membership observations, fork/exec/exit/kill classes, pidfd observations, timeout/limit trigger, `cgroup.kill`, `populated` transition, survivor result |
| filesystem | input/read-only boundary, scratch/output byte and inode usage/limits, rejected boundary attempts, retained output identities, teardown result |
| network | namespace identity, loopback state, inherited-FD closure, seccomp socket result, denial observations |
| streams | raw stdout/stderr and combined emitted, retained, discarded, and limit counts; decoding status; overflow/observer-loss flags |
| completeness | required observation-class bitmap, ordered provider sequence, loss/gap/overflow/error flags, cleanup evidence, and one final `complete` boolean |
| outcome | not-executed, success, workload failure, policy denial, capability blocker, limit, timeout, observation incomplete, or cleanup incomplete |

Completeness is conjunctive. Any missing observation class, sequence gap,
provider/observer error, buffer loss, missing teardown, surviving process, or
cleanup residue forces `complete=false` and blocks every acceptance claim that
depends on execution or effects. An application cannot construct this record.
Numeric zero is publishable only as a scoped observation from a complete,
matching current-run record; `absolute zero-effect` and `hard-zero` remain
prohibited.

Worker-adapter performs first-level exact validation of the returned worker
record. Task-runner later independently matches every worker and validation
record and joins them with TS-B01 v2 semantic evidence. ExecutionEvidenceV1 does
not prove acceptance semantics, and TS-B01 evidence does not prove OS effects.

## 8. Natural owners and strict interface boundary

| Surface | Natural owner | Boundary |
| --- | --- | --- |
| this Hosted probe | TS-B02 feasibility evidence owner and test maintainers | Non-durable synthetic evidence only; no runtime consumer or public interface. |
| request selection/construction | future worker-adapter TS-B02B change | Select expected worker/identity/policy and construct `IsolationRequestV1`; it does not seal or execute. |
| enforcement/evidence | future isolated-execution TS-B02A change | Validate request, gate, seal, execute, enforce, observe, clean, and return `ExecutionEvidenceV1`. |
| final matching/join | future task-runner TS-B02C change | Independently match all records and perform the TS-B01/TS-B02 join; it does not synthesize OS evidence. |

The current fixture-only agent-worker language remains outside this core claim
and is not migrated or edited here.

## 9. Exact future TS-B02A closure, dependencies, and license boundary

If and only if this exact Hosted job passes and this package is merged, the next
eligible action is a new user decision about an exact TS-B02A implementation
package. This report does not start or authorize it. Its path closure is frozen
to the following 17 paths relative to the then-current successful-probe base.

Modify exactly:

1. `REPO_MANIFEST.md`;
2. `config/module_registry_v1.yaml`;
3. `docs/tool_system_module_registry_contract_v1.md`;
4. `tests/test_module_contracts.py`;
5. `tests/test_module_registry.py`;
6. `tests/test_repo_manifest.py`.

Add exactly:

1. `docs/modules/isolated-execution-contract-v1.md`;
2. `docs/reports/subscription_worker_ts_b02a_core_local_os_isolated_execution_implementation_v1.md`;
3. `examples/task_manifests/tool_system_subscription_worker_ts_b02a_core_local_os_isolated_execution_v1.yaml`;
4. `examples/change_plans/tool_system_subscription_worker_ts_b02a_core_local_os_isolated_execution_v1.yaml`;
5. `src/tool_system/isolated_execution/__init__.py`;
6. `src/tool_system/isolated_execution/contract.py`;
7. `src/tool_system/isolated_execution/evidence.py`;
8. `src/tool_system/isolated_execution/linux_backend.py`;
9. `tests/test_isolated_execution_contract.py`;
10. `tests/test_isolated_execution_linux_backend.py`;
11. `tests/test_isolated_execution_adversarial.py`.

At TS-B02A the new module registers with zero runtime consumers. Worker-adapter
and task-runner edges are added only in B and C when imports actually exist.
README, project state, phase-alignment, workflow, pyproject, lock files, compiled
helpers, fixtures, and current worker/runner code are not in the A closure.

The runtime dependency closure is the existing supported CPython plus its
standard library and Linux kernel ABI; it adds no Python distribution, vendored
code, container runtime, daemon, binary artifact, package install, or external
service. The Hosted test compiles one temporary synthetic ELF with the runner's
existing `/usr/bin/cc`; that compiler is a test-environment capability, not a
runtime dependency or repository artifact. If implementation requires a new
package, helper path, compiler at runtime, workflow/runner change, or privilege
change, the 17-path closure is invalid and the task must stop for new authority.

No third-party source is copied. Linux syscall/UAPI use remains at the syscall
boundary; Linux UAPI headers carry `GPL-2.0 WITH Linux-syscall-note`. Existing
CPython and system runtime licenses remain external installation facts. The
repository currently has no root license file; this package does not invent a
project license. Any distribution/licensing decision for new project source
must be explicitly resolved in the separately authorized TS-B02A package and
cannot expand this path set silently.

Rollback identity for the future module is
`tool-system@<successful-probe-base>:isolated_execution@absent`. Runtime cleanup
may remove only provider-created namespaces, mounts, cgroups, processes, FDs,
and temporary roots carrying the exact execution identity.

## 10. Frozen TS-B02A adversarial matrix

The future A implementation must pass real-backend, non-live tests; this Hosted
probe establishes primitive/composition availability, not all adversarial
conformance.

| Case | Required TS-B02A result |
| --- | --- |
| capability loss | Block before workload release; no ordinary-host or alternate backend fallback. |
| filesystem escape | `openat2`/private-root denial with positive in-root controls; host sentinel and provider controls unavailable. |
| quota bypass | Stream, scratch, structured-result, explicit-output byte/inode limits are OS enforced and appear in evidence. |
| process escape | setsid, double-fork, reparent, signal-ignore, timeout survivor, and ptrace-stop remain in the cgroup; cleanup reaches `populated=0`. |
| network escape | loopback, DNS, IPv4/IPv6, netlink/packet, inherited descriptor, and namespace bridge attempts are denied; positive controls show attacks were attempted. |
| selection/path race | basename, PATH, symlink, magic-link, mount-crossing, rename, and in-place mutation cannot produce a matched success. |
| native exec race | actual exec-stop device/inode/digest matches the sealed descriptor after selection-path replacement. |
| script/interpreter race | script and interpreter are separately sealed; interpreter is explicitly descriptor-executed against a private immutable script; actual interpreter identity matches. |
| loader race | private immutable loader path plus exec-stop map identity matches parsed `PT_INTERP`; hash-only evidence blocks. |
| output flood | both pipes drain continuously as raw bytes; per-stream/combined limits terminate the full cgroup; counts are bounded. |
| timeout | monotonic deadline, finite grace, cgroup kill, pidfd exit, populated zero, and no survivor are observed. |
| evidence fabrication/mismatch | missing, duplicate, stale, wrong-request/policy/executable, app-built, or workload-self-reported evidence blocks. |
| observation loss | dropped class, buffer overflow, sequence gap, observer error, missing teardown, or unavailable survivor check marks evidence incomplete. |
| cleanup failure | Any cgroup, namespace FD, mount, cwd/root/fd, process, pidfd-live task, or temp-root residue overrides all earlier passes. |

## 11. Preserved state and explicit non-claims

- TS-B01 remains `corrected_pending_reacceptance`.
- TS-B02 remains blocking and is not corrected here.
- The subscription-worker public entry remains unreaccepted.
- Real-repository and real business execution remain blocked.
- TS-H01, TS-H02, TS-H03, TS-M01, and TS-M02 remain unchanged.
- `integrated_conformance_proved=false`.
- `ts_b02a_implementation_authorized=false`.
- `public_acceptance_changed=false`.
- No true zero-effect/hard-zero claim is constructed.
- No live Codex, subscription transport, provider/API call, credential, target
  repository, external verifier, KMS/HSM/OIDC, infrastructure, deployment, or
  runtime/security external-service operation occurs. Authorized GitHub
  publication and the synthetic Hosted job are the only remote control-plane
  effects.

The existing strict JSON task-manifest schema does not describe several
governance extensions already consumed by current canonical task pairs, while
the current CLI validator accepts them. That pre-existing schema/CLI mismatch is
not corrected or claimed as strict-schema PASS here; doing so would require an
unauthorized seventh path.

## 12. Exact publication and terminal stop

Publication contains exactly four additions and two modifications named in the
task pair, all regular mode `100644`, in one commit with message
`Probe TS-B02A local OS isolation capability on Hosted CI` on branch
`agent/subscription-worker-ts-b02a-core-local-os-isolation-hosted-capability-probe-v1`.
One Draft PR is allowed.

If the actual Hosted job produces `HOSTED_CAPABILITY_BLOCKER`, including backend
absence, skip, xfail, mock, fallback, observation loss, or cleanup residue, the
PR remains Draft, no assertion or path is weakened, and work stops. If and only
if every unchanged Hosted check succeeds and base, head, six-path/mode scope,
one-commit identity, comments, reviews, and threads remain unchanged, the PR may
be marked Ready and squash-merged through the GitHub App. The original feature
branch must remain at the original PR head. Both terminal outcomes stop. Neither
outcome starts TS-B02A or any real execution.

## References

- Linux cgroup v2: <https://docs.kernel.org/admin-guide/cgroup-v2.html>
- `openat2(2)`: <https://man7.org/linux/man-pages/man2/openat2.2.html>
- `execveat(2)`: <https://man7.org/linux/man-pages/man2/execveat.2.html>
- `ptrace(2)`: <https://man7.org/linux/man-pages/man2/ptrace.2.html>
- GitHub-hosted runners: <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>
- Ubuntu 24.04 runner inventory: <https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md>
