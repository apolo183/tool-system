# TS-B02A core local-OS isolation Hosted capability probe observation and cascade repair v1

## 1. Authority, clean base, and result boundary

Task identity:
`TOOL-SYSTEM-TS-B02A-CORE-LOCAL-OS-ISOLATION-HOSTED-CAPABILITY-PROBE-OBSERVATION-AND-CASCADE-REPAIR-v1`.

Before any repository write, the authenticated GitHub App read
`refs/heads/main` and then the referenced Git commit object in that order. The
observed clean canonical input exactly matched:

- commit: `71544c0c3bb37b1f4cb8bacbf4dc332477c94ccc`;
- tree: `27bea1f06a51c3f416963724ac132aebd8c16a1f`.

The repaired probe source is frozen at SHA-256
`1b51c92fa54585c95d304b32a41437a4e8c0f12f4f4f3701e32f30706d895990`;
the governance alignment below does not alter that test file.

This is a separately authorized clean-base repair package. It does not amend,
close, ready, merge, rerun, or move the failed package's Draft PR #227 or its
branch. PR #227 remains a retained read-only failure witness at head
`daad39047e4ad05443a1eb0776f9a1ff38239af4`; its Hosted run `31711740297` and
job `94486178632` remain the causal input to this repair.

The complete write surface is one repaired synthetic test, this report and its
task pair, plus the two exact repository-manifest registration updates. No
workflow, runner, permission, dependency, supply-chain, source runtime, module
registry, project state, public acceptance, audit finding, external security
service, infrastructure, or business target changes.

The test retains exactly three top-level dispositions:

| Disposition | Meaning |
| --- | --- |
| `NOT_EXECUTED` | The process is not running on an identified GitHub-hosted Actions runner. It is not capability evidence and never becomes capability PASS. |
| `HOSTED_CAPABILITY_PASS` | One actual GitHub-hosted `ubuntu-latest` job completed every required stage and cleanup assertion without skip, xfail, mock, fallback, `FAIL`, or `NOT_REACHED`. |
| `HOSTED_CAPABILITY_BLOCKER` | Any required identity, stage, observation, positive control, denial, resource limit, termination, or cleanup assertion failed or was not reached. The new PR remains Draft and work stops. |

`HOSTED_CAPABILITY_PASS` proves only that the selected backend design has no
known blocker on the exact observed Hosted job. It does not prove integrated
TS-B02A conformance, implement `isolated-execution`, correct TS-B02, reaccept a
public entry, or authorize any successor package.

## 2. Failed-package evidence and exact causal disposition

The failed package correctly stopped with `HOSTED_CAPABILITY_BLOCKER`; it is not
retroactively weakened or relabelled. Its actual Hosted job ended with
`1 failed, 875 passed`. Its structured result showed that namespace set,
private propagation, `openat2`, quota probes, combined stream limit, monotonic
timeout, inner cleanup, and outer cleanup succeeded. The first recorded direct
exception was:

```text
AssertionError('loopback did not become down: unknown')
```

The failed test issued `ip link set lo down`, then required the diagnostic
`/sys/class/net/lo/operstate` text to equal the single literal `down`. The
observed value was `unknown`. That assertion occurred before private-root
construction, `pivot_root`, path replacement, native exec, interpreter exec,
loader observation, detached descendant creation, and per-stream emission.
The namespace helper caught that exception and returned immediately, so those
dependent stages were not executed.

The outer collector then represented missing dependent observations as flat
`false` capability values and attempted the per-stream check against the
already terminated composition process. That produced zero per-stream bytes,
a missing descendant, an empty complete-tree positive control, and additional
flat failures for network, pivot-root, path-swap, native exec, interpreter exec,
and stream limit. Those entries are evidence of cascade and missing execution,
not evidence that each underlying Hosted primitive independently failed.

The retained Hosted failure exposed two immediate causal defects to correct:

1. replace the invalid loopback administrative-state observation with the
   kernel interface `IFF_UP` flag while retaining `operstate` only as
   diagnostic context; and
2. replace flat cascade booleans with ordered `PASS`, `FAIL`, and `NOT_REACHED`
   stage results whose `blocked_by` relation preserves the first direct cause.

The final deterministic and security review also closes the bounded probe's
evidence-integrity edges: exact four-path cgroup ownership and no-kill release,
root-helper lifecycle identity and pidfd-first termination, live host-mount
negative observation, strict ENOENT-only inheritable-FD absence at exec stops,
inside-report schema and rooted causal DAG validation, pidfd-bound process-tree
identity and TERM-ignore control, three independent finite stream controls and
exact output accounting, inside-report delivery before composition kill, one
public result, and cleanup-blocker precedence.
These are assurance corrections inside the same synthetic probe; none selects a
weaker backend, widens the repository scope, or changes the completion claim.

No prior passing primitive is removed, mocked, skipped, or accepted by
fallback. Any `FAIL` or `NOT_REACHED` still makes the overall Hosted result a
blocker. The distinction prevents false causal claims; it does not make the
acceptance predicate weaker.

## 3. Parent and blueprint alignment

The stable parent remains Section 6.1 of
`subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_specification_v1.md`.
It requires a separately authorized, bounded, non-live feasibility surface
before TS-B02A runtime work. The immediate repair input is the explicitly
preserved failed probe package and its Hosted evidence; neither Draft content
nor CI metadata grants authority.

The active blueprint excludes an arbitrary untrusted-code containment service.
The profile here contains only a bounded, approved, unprivileged workload under
a trusted operator, host, kernel, and provider supervisor. It does not test a
malicious host, kernel, operator, provider, or CI control plane, and it creates
no caller-independent attestation, durable anti-replay, or external trust claim.

## 4. Frozen backend selection

The sole candidate remains `linux_native_supervisor_v1`:

- a project-owned, host-local supervisor behind the future
  `isolated-execution-api` v1 boundary;
- CPython standard-library control code plus direct Linux syscall, ioctl, and
  filesystem interfaces, with no Docker, runc, bubblewrap, or external service;
- a trusted privileged supervisor that drops the workload to an unprivileged
  UID/GID with zero effective capabilities and `no_new_privs` before sealed
  exec;
- one execution-ID-scoped private cgroup v2 tree containing exactly four claimed
  paths: `/sys/fs/cgroup/<execution_id>`,
  `/sys/fs/cgroup/<execution_id>/composition`,
  `/sys/fs/cgroup/<execution_id>/combined-stream`, and
  `/sys/fs/cgroup/<execution_id>/timeout`; every path is claimed before use,
  identity-checked before cleanup, reaches `populated=0`, and is journaled as
  released;
- mount, PID, network, IPC, and UTS namespaces, private mount propagation,
  `pivot_root`, read-only executable/interpreter/loader objects, quota-bound
  tmpfs, loopback administratively down, seccomp socket denial, and a closed
  inherited-FD set; and
- `openat2`, `execveat`, `PTRACE_EVENT_EXEC`, `/proc` identity observation,
  pidfds, monotonic deadlines, incremental raw-byte drainage, `cgroup.kill`, and
  `cgroup.events populated=0` for current-run evidence.

Bubblewrap, runc, and Docker remain unselected and cannot be fallback backends.
They do not own the complete request/evidence semantics frozen here.

## 5. Supported host and fail-before-workload capability gate

Core v1 support remains exactly `Linux/x86_64`. The first empirically qualified
host class must be an actual GitHub-hosted `ubuntu-latest` x64 VM reached through
the unchanged repository workflow. The future provider gate remains
conjunctive and must establish, before releasing an approved workload:

1. Linux, x86_64, unified cgroup v2, and required syscall ABI;
2. supervisor privilege for namespace, mount, cgroup, ptrace, UID/GID, and
   seccomp setup;
3. simultaneous mount/PID/network/IPC/UTS namespaces distinct from the provider;
4. recursive private mount propagation;
5. the exact four-path execution cgroup tree described above, with a writable
   provider-created parent and `composition`, `combined-stream`, and `timeout`
   children, `cgroup.kill`, observable `cgroup.events`, collision refusal, and
   claim/release evidence for every path;
6. private-root construction, `pivot_root`, immutable identity objects, and
   separate scratch/output byte and inode quotas;
7. loopback administratively down, no usable inherited network descriptor, and
   seccomp `EPERM` for the fixed socket ABI;
8. working `openat2`, `execveat`, ptrace exec-stop observation, executable and
   loader identity reads, pidfds, and monotonic time;
9. three independent finite stream controls named `stdout_probe`,
   `stderr_probe`, and `combined_probe`: the first two trigger their respective
   per-stream raw-byte limits and the third triggers the combined raw-byte
   limit, each with nonblocking drainage, exact accounting, cgroup kill, pidfd
   exit, and `populated=0`; and
10. exact-cgroup kill, `populated=0`, directory removal, and no execution-specific
    namespace, mount, process, FD, or temporary-root residue.

Any missing item is `HOSTED_CAPABILITY_BLOCKER`. There is no ordinary-host,
container-engine, weaker-network, hash-only, self-report, skip, xfail, mock, or
best-effort fallback.

## 6. Repaired network observation and live endpoint controls

The loopback proof is refrozen as one ordered positive/negative control:

1. set loopback administratively up and require `IFF_UP` to be set;
2. create one exact bound and listening TCP endpoint on loopback after that
   administrative-up observation and keep it open through both halves of the
   probe;
3. connect to that live endpoint and complete a bounded payload round trip;
4. retain a duplicate connected network descriptor solely for the later
   inherited-FD closure denial;
5. set loopback administratively down and require `IFF_UP` to be clear;
6. while the same listener remains open, require a new bounded connection to
   that exact endpoint to fail; and
7. record `operstate` before and after only as a bounded diagnostic object:
   either `{value: <label>}` or `{unavailable: true, error_type: <type>}`.
   `unknown`, `down`, another label, or read unavailability neither proves nor
   disproves the administrative state by itself.

The positive control deliberately makes the duplicated network FD inheritable.
At each native and interpreter `PTRACE_EVENT_EXEC` stop, the supervisor must
use explicit `lstat`/`readlink` observation of that exact
`/proc/<pid>/fd/<descriptor>` entry. Only `ENOENT` proves absence; permission
denial or any other observation error is a blocker, and `lexists` is forbidden
because it can collapse such errors into false absence. The two explicit fields
`native_inherited_network_fd_absent_at_exec` and
`interpreter_inherited_network_fd_absent_at_exec` must both be true before the
aggregate `inherited_network_fd_absent_at_exec=true`; the sealed exec must also
prove a new socket syscall returns `EPERM` under the fixed seccomp filter. A
connection attempt to an arbitrary closed port is not a valid negative control.

## 7. Ordered stage and cascade semantics

Every required Hosted capability has one stage record with:

- stable stage identity;
- status exactly `PASS`, `FAIL`, or `NOT_REACHED`;
- bounded OS observations when reached;
- one direct failure when status is `FAIL`; and
- `blocked_by` naming the exact failed prerequisite when status is
  `NOT_REACHED`.

`FAIL` means the stage ran and its frozen predicate failed. `NOT_REACHED` means
the stage did not run because a named prerequisite failed. A stage cannot carry
both meanings. Independent probes may continue only when they do not consume a
failed prerequisite and cleanup safety remains intact.

The result is `HOSTED_CAPABILITY_PASS` only if every required stage is `PASS`,
all observations are present, and cleanup is complete. Any `FAIL`, any
`NOT_REACHED`, observation loss, or cleanup residue produces
`HOSTED_CAPABILITY_BLOCKER`. The structured result must preserve the direct
failure and the dependency cascade without adding flat synthetic failures for
unreached stages.

The namespace helper publishes these records under `stage_results`; the root
collector publishes its composed verdicts under `check_results`. A `FAIL`
record carries `failure`, and a `NOT_REACHED` record carries `blocked_by`.
The same structured result publishes complete `stage_dependencies` and
`check_dependencies` maps. Cascades follow only those declared edges: the
composition, stream-limit, timeout, ownership, and cleanup domains do not
inherit an unrelated capability failure, although an ownership or cleanup
failure may safely prevent later resource creation. Missing, extra, cyclic, or
status-inconsistent dependency entries are blockers.

The inside report is schema-validated by `_validate_inside_stage_schema` before
any field becomes evidence: it must contain exactly the frozen inside stages,
exact status shapes, at most one bounded direct failure, a consistent `ready`
value, and only the linear dependent cascade from that failure.
`_build_stage_dependencies` then produces the complete cross-domain DAG.
`inside.namespace_set` depends directly on both
`root.composition_setup` and `root.inside_report`; the separately reported
`root.live_host_mount_observation` depends on `root.inside_report`, and
`root.process_tree` depends on that live observation plus
`inside.process_tree_fixture`. The three explicit shared-cgroup safety stages
`root.stdout_stream_safety`, `root.stderr_stream_safety`, and
`root.combined_stream_safety` gate later stream work when cleanup safety is
lost. `root.stream_cgroup_release` depends only on stream-cgroup setup so it
remains reachable for cleanup, while `root.timeout_cgroup_setup` depends on the
parent setup and completed stream release.

The final causal validator `_assert_causal_result_graph` rejects key-set drift,
unknown or duplicate edges, cycles, invalid status shapes, a PASS over a failed
dependency, a blocker that is not an ancestor, and any `NOT_REACHED` chain that
does not terminate at a real `FAIL`. `_run_causal_graph_negative_controls`
executes the ten frozen positive/negative graph controls covering parent-setup
and malformed-report failure cascades, stdout/stderr unsafe shared-cgroup
cascades, unknown or falsely PASS blockers, malformed schema, a legal safety
failure cascade, and PASS-over-FAIL rejection. A malformed inside report is
therefore a direct `root.inside_report` FAIL whose declared descendants are
`NOT_REACHED`, never an unrooted synthetic cascade.

The fixture-emission accounting is exact: the two single-stream controls emit
`2 * 64 * 4096 = 524288` theoretical bytes, the combined control emits
`32 * 8192 = 262144`, so stream payload is `786432`; the composition handshake
adds exactly `57`, producing `786489`, which must remain no greater than the
hard synthetic output cap `1048576`. Each number is emitted as structured
evidence and checked, rather than inferred from retained bytes.

Exactly one public line beginning `TS_B02A_HOSTED_PROBE_RESULT=` is emitted per
top-level test execution: `NOT_EXECUTED`, `HOSTED_CAPABILITY_PASS`, or
`HOSTED_CAPABILITY_BLOCKER`. Root-helper records use the distinct captured
`TS_B02A_ROOT_PROBE_RESULT=` prefix and require exactly one match. Hosted
diagnostic context uses the distinct
`TS_B02A_HOSTED_PROBE_DIAGNOSTIC=` prefix, is bounded to 16384 characters, and
cannot substitute for or create a second public result.

The public Hosted PASS projection additionally requires
`root_helper_lifecycle_closed=true`, `host_mounts_during_live_namespace=[]`,
`inherited_network_fd_absent_at_exec=true`, and `cleanup_complete=true`; these
are projections of matching root/OS evidence, not application-constructed
substitutes.

Before privileged creation, a 64-lowercase-hex ownership nonce is bound to the
exact execution ID, creator UID, temporary-parent device/inode, and exact
temporary-root path. A mode-`0600`, `O_EXCL`/`O_NOFOLLOW` ownership marker inside
that root journals each exact cgroup transition through claiming, owned
device/inode, and released state with durable replacement. Cleanup refuses an
absent, unexpected, non-owned, or device/inode-mismatched claim. Any ownership
validation failure, cleanup observation loss, residue, or failed release is the
cleanup blocker and overrides all earlier PASS results.

The outer caller separately creates a creator-owned mode-`0600`,
`O_EXCL`/`O_NOFOLLOW` root-helper lifecycle record before launch. The helper
binds that record to the exact execution ID, its PID and
`/proc/<pid>/stat` starttime, nonce digest, argv digest, source device/inode
identity, and executable identity. Outer
cleanup may signal only that exact still-matching PID/starttime identity; PID
reuse is treated as gone, identity mismatch refuses termination, and lifecycle
removal follows verified termination. Hosted PASS requires
`root_helper_identity_bound`, outer `helper_identity_validated`,
`helper_terminated`, matching `helper_termination` evidence, and
`lifecycle_removed`; the public PASS projects this conjunction as
`root_helper_lifecycle_closed=true`. Outer cleanup validates and terminates this
exact helper before touching any cgroup, mount, or temporary-root resource.
Termination is pidfd-first: open a pidfd for the bound PID, validate the bound
PID/starttime/argv/source/executable identity, signal only through
`pidfd_send_signal`, and require pidfd readability as exit evidence. The
structured termination record freezes `initial_state`, `helper_was_active`,
`helper_pidfd_opened`, `helper_pidfd_open_esrch`,
`helper_pid_reuse_observed`, `helper_sigkill_sent`, `helper_signal_esrch`,
`helper_pidfd_exit_observed`, and `helper_terminated`; no numeric-PID signal is
an accepted termination path.

If the helper exits before the launch handshake is bound, the creator first
fully reaps its `Popen`, reloads the exact unchanged `launching` lifecycle
record, proves the temporary root and all four possible cgroup paths are absent,
then removes only that creator-owned lifecycle record. This pre-gate path sets
`popen_fully_reaped` and `unbound_lifecycle_reaped`; it performs no privileged
resource cleanup and cannot produce capability PASS.

A pre-existing parent cgroup collision is never killable cleanup authority.
The journal records `collision`; parent release is explicitly no-kill and
refuses unless the parent is an owned device/inode match, the journal contains
only allowed exact paths, every present child claim is released, every missing
child claim is also absent on disk, no child directory remains, and the parent
is already `populated=0`. This permits a safe parent-only early-exit release
without killing an absent child. A colliding or unexpected parent is preserved
and the result is a cleanup blocker.

While the composition namespace and its process are still live, the host reads
its own `/proc/self/mountinfo` and must observe no mount under the exact
temporary root. `process_tree.host_mounts_during_live_namespace` must equal
`[]`, and `namespace_alive_during_host_mount_observation` must be `true`. A
post-exit absence alone is not the private-propagation negative control.

For the detached process-tree control, the host maps the namespace PID to one
host PID, opens its pidfd first, and then revalidates starttime, `NSpid`, and
exact composition-cgroup membership. PID reuse, identity drift, ambiguity, or
observation loss blocks without a numeric-PID signal. The TERM-ignore positive
control uses only `pidfd_send_signal(SIGTERM)`. Every exact cgroup member is
likewise pidfd-bound across before/after starttime and cgroup rechecks, and all
member pidfds must remain unreadable before `cgroup.kill`. The exact evidence is
`detached_pidfd_bound_before_term`, `detached_identity_revalidated`,
`detached_term_sent_via_pidfd`, `detached_pidfd_unreadable_after_term`,
`all_member_pidfds_identity_bound`, and
`all_member_pidfds_unreadable_before_kill`.

Whether the inside namespace succeeds or fails, it serializes, fsyncs, and
closes its real `stage_results` and failure report, then calls `signal.pause()`
inside the composition cgroup. The root collector consumes that report and propagates
its direct `FAIL`/dependent `NOT_REACHED` graph before issuing the single
composition `cgroup.kill`. The expected transport exit is therefore SIGKILL and
is not reclassified as an independent report-transport failure.

Network observations use `admin_up_observed`, `admin_down_observed`,
`flags_after_up`, `flags_after_down`, diagnostic `operstate_after_up` and
`operstate_after_down`, `listener_endpoint`,
`listener_active_during_denial`, `positive_control`, `connectivity_denied`, and
`denial_errno`, plus `inherited_network_fd_absent_at_exec`. Any retained legacy
`checks` projection is a final convenience
gate only; it cannot erase or replace the causal stage records.

## 8. Empirical Hosted proof matrix

| Hosted capability | Positive control and required effect |
| --- | --- |
| runner/root gate | Exact GitHub-hosted identity plus real passwordless root execution. |
| namespaces | Each mount/PID/net/IPC/UTS namespace has a current-run inode distinct from the parent. |
| mount propagation | Root propagation becomes recursive private and the probe mount never appears in host mountinfo. |
| cgroup tree and ownership | The exact parent, `composition`, `combined-stream`, and `timeout` paths are nonce-journaled before use; all four claims match recorded device/inode, reach released state, and leave no exact directory. |
| root-helper lifecycle | A creator-owned lifecycle record binds execution ID, nonce, PID/starttime, argv, source, and executable identities; outer cleanup opens the pidfd first, validates identity, signals only via pidfd, requires pidfd-readable exit before resource cleanup, removes the lifecycle record, and publishes `root_helper_lifecycle_closed=true`. |
| pre-gate helper exit | An unbound helper is fully reaped; only an unchanged launching record with zero temporary-root/cgroup resources permits creator-side lifecycle removal, and it cannot pass capability. |
| parent collision/early exit | A pre-existing or identity-mismatched parent cgroup is never sent `cgroup.kill`; no-kill release preserves collisions but may remove an owned `populated=0` parent when unclaimed children are absent. |
| live host-mount negative control | During the still-live namespace, host mountinfo contains no mount under the execution temporary root and the namespace process is proven alive at observation time. |
| process-tree identity and TERM-ignore control | The detached namespace PID maps uniquely to a host PID; pidfd-open precedes starttime/NSpid/exact-cgroup revalidation; TERM is sent only through that pidfd; every cgroup member is pidfd-bound and revalidated; every pidfd remains unreadable before `cgroup.kill`. |
| private root | `pivot_root` succeeds; old-root/host sentinel is unavailable; executable objects are read-only and scratch is separate. |
| quotas | Separate tiny tmpfs byte and inode probes reach kernel `ENOSPC`. |
| network | After up plus `IFF_UP` observation, one exact listening endpoint supplies the payload exchange and remains listening while clear `IFF_UP` denies a new connection; bounded operstate objects remain diagnostic only; explicit exec-stop `lstat`/`readlink` accepts only `ENOENT` as inherited-FD absence; seccomp socket denial passes. |
| `openat2` | In-bound open succeeds; traversal, ordinary symlink, proc magic-link, and cross-mount attempts receive only safe rejection. |
| native identity | A sealed temporary ELF executes by FD after path replacement and matches exec-stop executable and loader device/inode observations. |
| script/interpreter | Script and interpreter are separately sealed; the interpreter is descriptor-executed against the immutable private-root script and actual identity matches. |
| dynamic loader | Parsed `PT_INTERP`, immutable private-root loader, and exec-stop map device/inode match; pre-exec digest alone cannot pass. |
| streams | `stdout_probe`, `stderr_probe`, and `combined_probe` independently trigger stdout, stderr, and combined limits with raw-byte drainage, cgroup kill, pidfd exit, `populated=0`, and exact emitted/retained/discarded accounting; three explicit safety stages gate only later shared-cgroup work; `786432 + 57 = 786489 <= 1048576`. |
| timeout | A monotonic deadline kills the exact timeout cgroup and observes pidfd exit plus `populated=0`. |
| public result | Exactly one bounded top-level `TS_B02A_HOSTED_PROBE_RESULT=` line is emitted; captured root results and bounded diagnostics use distinct prefixes. |
| cleanup | Ownership-authenticated cleanup runs after success or failure and overrides every earlier PASS; no exact claimed cgroup, namespace reference, mount, process cwd/root/fd, live pidfd task, ownership journal, or creator-owned temp root remains. |
| cascade | Schema validation and the complete DAG preserve independent domains; a reached failure is `FAIL`, every `NOT_REACHED` blocker is a reachable ancestor whose chain ends at a real `FAIL`, all ten causal controls pass, and either status blocks overall PASS. |
| failure-report transport | Inside success or failure is fsynced before pause; the root propagates those real stages and then cgroup-kills the paused tree, so expected SIGKILL transport cannot fabricate a second capability failure. |

The fixtures remain only temporary ELF/shebang material, `true`, `false`,
`sleep`, exactly `786489` theoretical output bytes under the `1048576` hard
cap, tiny tmpfs mounts, finite process trees, four claimed cgroup paths, and one
creator-owned temporary root and ownership journal. No repository or business
workload is executed.

## 9. `IsolationRequestV1` interface semantics

The future `isolated-execution-api` v1 accepts one immutable
`IsolationRequestV1`. Worker-adapter owns selection, caller expectation, and
construction; isolated-execution owns validation, sealing, enforcement, and
execution.

| Field group | Required values and rules |
| --- | --- |
| request identity | schema version, unique execution ID, request digest, task/source/candidate/workspace identity, configuration identity, and policy digest |
| backend | exact `linux_native_supervisor_v1` profile and required capability-set digest; no fallback |
| filesystem | canonical read-only input roots, execution-owned scratch/output locations, byte/inode quotas, retained outputs, and no provider-control path |
| executable | selection object, expected file type, device/inode/mode/size/SHA-256, argv, bounded environment, and PATH-disabled descriptor exec |
| interpreter/loader | parsed format, sealed interpreter or `PT_INTERP` loader expectation, full identity tuple, and immutable private-root path |
| workload identity | unprivileged UID/GID, empty supplementary groups, zero effective capabilities, `no_new_privs`, and denied control operations |
| network | `deny_all`, clear loopback `IFF_UP`, no inherited network descriptors, socket-denial filter identity, and diagnostic operational state |
| streams | stdout/stderr per-stream and combined raw-byte limits, retained-byte limit, post-accounting decode, and continuous drainage |
| time/process | monotonic deadline, finite grace, exact cgroup identity, maximum process count, and survivor observation |
| output | bounded structured result and file output plus completeness classes required for a matching record |

Canonicalization, symlink/magic-link refusal, digests, backend selection, and
policy matching occur before release. Actual executable, interpreter, loader,
mount, cgroup, identity, filter, and limit observations must match the request.
No caller or workload field substitutes for an OS observation.

## 10. `ExecutionEvidenceV1` interface semantics

Isolated-execution remains the sole natural owner and producer of immutable
`ExecutionEvidenceV1`. It is a current-run OS-derived enforcement and
observation record, not independently attested or durable anti-replay evidence.

| Field group | Mandatory content |
| --- | --- |
| correlation | schema, execution ID, request/task/source/candidate/workspace/config/policy digests, provider profile, and monotonic start/finish |
| capability | OS/architecture, ordered gate stages, namespace/cgroup/mount/quota identities, UID/GID/capability/no-new-privileges observations, seccomp identity, and `PASS`/`FAIL`/`NOT_REACHED` causality |
| exec chain | requested and actual executable, script, interpreter, and loader identity tuples; open/seal/recheck/exec/ptrace sequence; mismatch or denial |
| process | cgroup membership, fork/exec/exit/kill classes, pidfd observations, timeout/limit trigger, cgroup kill, populated transition, and survivor result |
| filesystem | input boundary, scratch/output usage and limits, rejected boundary attempts, retained-output identities, and teardown |
| network | namespace, `IFF_UP` observations, diagnostic `operstate`, exact live-endpoint controls, inherited-FD closure, seccomp result, and denial observations |
| streams | raw stdout/stderr and combined emitted, retained, discarded and limit counts; decoding status; overflow/observer-loss flags |
| completeness | required observation bitmap, ordered provider sequence, blocked-by graph, loss/gap/error flags, cleanup evidence, and final `complete` |
| outcome | not-executed, success, workload failure, policy denial, capability blocker, limit, timeout, observation incomplete, or cleanup incomplete |

Completeness is conjunctive. Any missing observation, sequence gap, provider or
observer error, buffer loss, missing teardown, survivor, `FAIL`, `NOT_REACHED`,
or cleanup residue forces `complete=false`. Numeric zero is publishable only as
a scoped current-run observation; absolute zero-effect and hard-zero remain
prohibited. Worker-adapter later performs first-level exact validation, and
task-runner later performs the independent TS-B01/TS-B02 join.

## 11. Natural owners and strict interface boundary

| Surface | Natural owner | Boundary |
| --- | --- | --- |
| this repaired Hosted probe | TS-B02 feasibility evidence owner and test maintainers | Non-durable synthetic evidence only; no runtime consumer or public interface. |
| request selection/construction | future worker-adapter TS-B02B change | Select expected worker/identity/policy and construct `IsolationRequestV1`; do not seal or execute. |
| enforcement/evidence | future isolated-execution TS-B02A change | Validate, gate, seal, execute, enforce, observe, clean, and return `ExecutionEvidenceV1`. |
| final matching/join | future task-runner TS-B02C change | Independently match all records and perform the TS-B01/TS-B02 join; do not synthesize OS evidence. |

The current fixture-only agent-worker language remains outside this core claim
and is not migrated or edited here.

## 12. Exact future TS-B02A closure, dependencies, and license boundary

Only if this repaired Hosted package succeeds and is guardedly merged may a new
user decision consider TS-B02A implementation. The future closure remains
exactly 17 paths relative to that then-current successful-probe base.

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

The new module initially registers with zero runtime consumers. Worker-adapter
and task-runner edges arise only in TS-B02B and TS-B02C when imports exist.
README, project state, phase alignment, workflow, pyproject, lock files,
compiled helpers, fixtures, and current worker/runner code remain outside A.

Runtime dependencies remain existing supported CPython, its standard library,
and the Linux kernel ABI. No Python distribution, vendored code, container
runtime, daemon, binary artifact, package install, or external service is added.
The Hosted test may compile one temporary synthetic ELF with the runner's
existing `/usr/bin/cc`; the compiler is a test-environment capability, not a
runtime dependency or repository artifact. Any required package, helper path,
runtime compiler, workflow/runner change, or privilege change invalidates the
17-path closure and requires new authority.

No third-party source is copied. Linux syscall/UAPI use remains at the syscall
boundary; Linux UAPI headers carry `GPL-2.0 WITH Linux-syscall-note`. Existing
CPython and system-runtime licenses remain external installation facts. The
repository has no root license file; this package does not invent one. Any
distribution/licensing decision for future project source must be explicitly
resolved in the separately authorized TS-B02A package.

Rollback identity for the future module remains
`tool-system@<successful-probe-base>:isolated_execution@absent`. Runtime cleanup
may affect only provider-created resources carrying the exact execution ID.

## 13. Frozen TS-B02A adversarial matrix

| Case | Required TS-B02A result |
| --- | --- |
| capability loss | Block before workload release; no ordinary-host or alternate-backend fallback. |
| filesystem escape | `openat2`/private-root denial with positive in-root controls; host sentinel and provider controls unavailable. |
| quota bypass | Stream, scratch, structured-result, and explicit-output byte/inode limits are OS enforced and evidenced. |
| process escape | setsid, double-fork, reparent, signal-ignore, timeout survivor, and ptrace-stop remain in the cgroup; every observed member is pidfd-bound with starttime and exact-cgroup revalidation, the detached TERM-ignore control is signalled only through its pidfd, all pidfds remain unreadable before `cgroup.kill`, and cleanup reaches `populated=0`. |
| network escape | loopback, DNS, IPv4/IPv6, netlink/packet, inherited descriptor, and namespace-bridge attempts are denied with valid positive controls. |
| selection/path race | basename, PATH, symlink, magic-link, mount crossing, rename, and in-place mutation cannot produce matched success. |
| native exec race | exec-stop device/inode/digest matches the sealed descriptor after selection-path replacement. |
| script/interpreter race | script and interpreter are separately sealed; descriptor-executed interpreter and immutable script identities match. |
| loader race | immutable loader path plus exec-stop map identity matches parsed `PT_INTERP`; hash-only evidence blocks. |
| output flood | both pipes drain as raw bytes; per-stream and combined limits terminate the full cgroup with bounded counts. |
| timeout | monotonic deadline, finite grace, cgroup kill, pidfd exit, populated zero, and no survivor are observed. |
| evidence fabrication/mismatch | missing, duplicate, stale, wrong-request/policy/executable, app-built, or workload-self-reported evidence blocks. |
| observation loss | dropped class, overflow, sequence gap, observer error, missing teardown, or unavailable survivor check marks evidence incomplete. |
| cascade ambiguity | Direct `FAIL` and dependent `NOT_REACHED` remain distinct; an absent or cyclic `blocked_by` relation blocks. |
| cleanup failure | Any cgroup, namespace FD, mount, cwd/root/fd, process, live pidfd task, or temp-root residue overrides all earlier passes. |

## 14. Preserved state and non-claims

- TS-B01 remains `corrected_pending_reacceptance`.
- TS-B02 remains blocking and is not corrected here.
- The subscription-worker public entry remains unreaccepted.
- Real repository and business execution remain blocked.
- TS-H01, TS-H02, TS-H03, TS-M01, and TS-M02 remain unchanged.
- `integrated_conformance_proved=false`.
- `ts_b02a_implementation_authorized=false`.
- `public_acceptance_changed=false`.
- No absolute zero-effect or hard-zero conclusion is constructed.
- No live Codex, subscription transport, provider/API call, credential, target
  repository, external verifier, KMS/HSM/OIDC, infrastructure, deployment, or
  runtime/security external-service operation occurs.

The existing strict JSON task-manifest schema does not describe several
governance extensions already consumed by current canonical task pairs, while
the current CLI validator accepts them. That pre-existing mismatch is not
corrected or claimed as strict-schema PASS because it is outside the six paths.

## 15. Publication and terminal stop

Publication contains exactly four additions and two modifications, all regular
mode `100644`, in one commit with exact message
`Repair TS-B02A Hosted capability probe observation cascade` on branch
`agent/subscription-worker-ts-b02a-hosted-capability-probe-observation-cascade-repair-v1`.
One new Draft PR is allowed. PR #227 and its original branch remain untouched.

If the one actual Hosted run produces any blocker, including `FAIL`,
`NOT_REACHED`, backend absence, skip, xfail, mock, fallback, observation loss,
or cleanup residue, the new PR remains Draft and the task stops with
`HOSTED_CAPABILITY_BLOCKER`. No Hosted repair cycle is authorized.

Only if every unchanged Hosted check succeeds and base, head, six-path/mode
scope, one-commit identity, comments, reviews, and threads remain unchanged may
the new PR become Ready and be squash-merged through the authenticated GitHub
App. The new original feature branch must remain at its original PR head. Both
terminal outcomes stop. Neither starts TS-B02A or real execution.

## References

- Failed Draft PR #227: <https://github.com/apolo183/tool-system/pull/227>
- Failed Hosted run: <https://github.com/apolo183/tool-system/actions/runs/31711740297>
- Linux interface operational states:
  <https://docs.kernel.org/networking/operstates.html>
- Linux cgroup v2: <https://docs.kernel.org/admin-guide/cgroup-v2.html>
- `openat2(2)`: <https://man7.org/linux/man-pages/man2/openat2.2.html>
- `execveat(2)`: <https://man7.org/linux/man-pages/man2/execveat.2.html>
- `ptrace(2)`: <https://man7.org/linux/man-pages/man2/ptrace.2.html>
