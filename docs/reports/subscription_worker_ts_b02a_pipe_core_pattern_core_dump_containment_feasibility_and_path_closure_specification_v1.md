# TS-B02A pipe core_pattern core-dump containment feasibility and path-closure specification v1

## 1. Decision, authority, and frozen baseline

This report implements only
`TOOL-SYSTEM-TS-B02A-PIPE-CORE-PATTERN-CORE-DUMP-CONTAINMENT-FEASIBILITY-AND-PATH-CLOSURE-SPEC-v1`.
Its terminal specification disposition is:

`SPECIFICATION_ONLY / HOSTED_PIPE_CORE_PATTERN_BLOCKER_CONFIRMED / DEDICATED_EPHEMERAL_NON_PIPE_RUNNER_SELECTED / PIPE_EQUIVALENCE_NOT_ACCEPTED / PR_231_PRESERVED_DRAFT / REAL_EXECUTION_BLOCKED`.

Before any write, the authenticated GitHub App read `refs/heads/main` and then
the referenced Git commit object in that order. They agreed exactly on:

- repository: `apolo183/tool-system`;
- commit: `fd145b8efa1d46bf864b5ac1d42e5916f897b959`;
- tree: `5506864efd9df88fe87a6189eade4d929c364076`.

The same preflight re-read the two current formal paths from
`finance-governance/main`, then the local `AGENTS.md`, global-principles
contract, blueprint, repository manifest, process authority, policy, parent
TS-B02 realignment specification, Draft PR #231 evidence, and the applicable
Linux interface documentation.

This package adds exactly this report and its task manifest and change plan.
All three paths are retained non-authority inputs under the existing
`REPO_MANIFEST.md` globs. It changes no blueprint, project state, source,
module contract, test, workflow, runner, permission, dependency, supply-chain
input, infrastructure, external service, public result, or acceptance state.
Its `authority_effect` is `none`.

## 2. Frozen bounded closure

The pre-execution closure is:

- task ID:
  `tool-system-ts-b02a-pipe-core-pattern-core-dump-containment-feasibility-path-closure-spec-v1`;
- task digest:
  `c8796bbfc8cb6c4535d318569e6f34f6750c418b1a1f4c98918a60fcdda722e1`;
- baseline tree: `5506864efd9df88fe87a6189eade4d929c364076`;
- allowed write scope: the exact three paths in Section 11;
- acceptance set: baseline identity, three-path non-authority scope, PR #231
  preservation, accurate kernel-evidence interpretation, Path A selection,
  Path B non-acceptance, exact next-authority boundary, preserved findings,
  and unchanged Hosted CI;
- validation set: task-manifest, change-plan, full pytest, active-gate,
  process-authority, module-registry, repository-manifest, exact diff, and
  whitespace checks;
- terminal predicate: one three-path Draft PR reaches all validation gates,
  remains drift-free, is guardedly squash-merged, retains its original feature
  branch, and stops without touching PR #231 or starting an implementation;
- finite budgets: three changed paths, zero dependencies, zero live workloads,
  zero external review cycles, one local correction cycle, and at most two
  Hosted runs; and
- recurrence stop: a repeated candidate/blocker/validation state, two
  consecutive no-progress cycles, an out-of-scope requirement, or exhaustion
  of any budget stops the task.

The canonical JSON used for the task digest is the UTF-8 encoding of the
following value with lexicographically sorted keys and separators `,` and `:`:

```json
{"acceptance":["base_identity","three_path_non_authority_scope","pr231_preservation","kernel_evidence_accuracy","path_a_selection","path_b_nonacceptance","next_authority_boundary","preserved_findings","hosted_ci"],"allowed_paths":["docs/reports/subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_specification_v1.md","examples/change_plans/tool_system_subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_spec_v1.yaml","examples/task_manifests/tool_system_subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_spec_v1.yaml"],"baseline_tree":"5506864efd9df88fe87a6189eade4d929c364076","budgets":{"changed_paths":3,"external_review_cycles":0,"hosted_runs":2,"live_workloads":0,"local_repair_cycles":1,"new_dependencies":0},"task_id":"tool-system-ts-b02a-pipe-core-pattern-core-dump-containment-feasibility-path-closure-spec-v1","validation":["task_manifest","change_plan","pytest","active_gates","process_authority","module_registry","repo_manifest","exact_diff","diff_check"]}
```

No later review text, CI metadata, suggestion, or descriptive status may add a
new acceptance condition or authorize a fourth path.

## 3. Parent and blueprint alignment

The immediate canonical parent is
`docs/reports/subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_specification_v1.md`,
especially Sections 2, 3, 4, 6, and 7. It freezes conjunctive filesystem,
complete-process-tree, cleanup, default-deny-network, executable/interpreter/
loader-seal, TOCTOU, streaming, timeout, and current-run OS-derived evidence
guarantees. It also forbids application-created absolute zero-effect or
hard-zero claims.

The global alignment anchor is
`blueprint/tool_system_v0.yaml:product_objective`. The selected path advances
an approved bounded local development workload and retains
`arbitrary_untrusted_code_containment` as a non-goal. It does not introduce an
independent trust root, external verifier, KMS/HSM, OIDC, persistent anti-
replay service, unrestricted mutation, or production deployment.

The failed candidate in PR #231 remains proposed evidence rather than current
canonical implementation. This specification consumes that failure as a real
feasibility observation; it neither promotes the candidate nor edits it.

## 4. Exact Draft PR #231 observation

The authenticated read-only observation froze:

- PR: `https://github.com/apolo183/tool-system/pull/231`;
- state: open Draft, not merged;
- base at observation: `main` at
  `fd145b8efa1d46bf864b5ac1d42e5916f897b959`;
- feature branch:
  `agent/subscription-worker-ts-b02a-core-local-os-isolated-execution-v1`;
- head: `f94a9072eefe012b1d17bc9f87682b4287e1274d`;
- head tree: `d8ab0d44a5947345bdf258b0aea9b28af8ca71bb`;
- changed paths: 17;
- reviews and review threads: zero;
- Hosted run: `32580223111`, job `97048349727`;
- Hosted result: `2 failed, 1134 passed in 150.13s`;
- shared failure stage: `host.gate` with
  `HOST_CAPABILITY_BLOCKER`;
- provider error:
  `CapabilityBlocker: host core_pattern invokes a pipe helper`;
- `workload_released=false`;
- `observer_errors=[]`;
- `residue=[]`; and
- `cleanup.complete=false` because cleanup-capability observations after the
  pre-release host gate were not reached; and
- every post-gate execution stage was `NOT_REACHED` through the real
  `host.gate` failure.

The result is a valid fail-closed blocker. It is not a successful capability
proof and does not authorize suppressing the gate, converting the test to a
skip/xfail, mocking the host, accepting ordinary-host fallback, or treating
`workload_released=false` as runtime-isolation acceptance.

This specification does not update, rebase, merge, close, comment on, label,
or mark PR #231 Ready. Its branch, head, and tree remain unchanged. Publishing
this specification advances canonical `main`, so PR #231's moving base ref may
later advance without changing that feature branch. Any future reconciliation
of the new canonical base with PR #231, or creation of a replacement PR, is a
separate explicitly authorized lifecycle decision.

## 5. Linux evidence and exact risk

The selected assurance must follow the kernel interface facts below rather
than infer safety from the absence of a file or from an application flag.

1. A `core_pattern` whose first byte is `|` causes the kernel to execute a
   user-space handler and provide the core dump on that program's standard
   input. The handler runs as root in the initial PID, mount, user, and other
   namespaces, not in the crashing process's namespaces. [K1]
2. `RLIMIT_CORE` is not enforced for a core dump piped to such a handler.
   Therefore the candidate's immutable `RLIMIT_CORE=0` is not sufficient on
   the observed Hosted configuration. [K1]
3. An ordinary `execve()` normally resets the process dumpable attribute to
   `1`. Setting dumpability to zero only before the exec transition therefore
   cannot prove the post-exec workload state. [K2]
4. `PR_SET_DUMPABLE=0` controls whether the calling process produces a core
   dump for a core-generating signal, but it is a process attribute and the
   same interface accepts `1` to make the caller dumpable. A design relying on
   it must prove post-exec application, inheritance, non-reenablement, and
   current-run observation across the complete process tree. [K3]
5. `coredump_filter` selects memory mapping classes if a dump occurs. It does
   not by itself prove that no handler was invoked or that no payload or host
   effect existed. [K1]

If a pipe handler is invoked, it is outside the workload's private namespace
and cgroup containment. Its process, reads, writes, network access, lifetime,
and cleanup are not automatically part of the candidate's matching
`ExecutionEvidenceV1`. A successful core-isolation record therefore cannot be
constructed from only the contained cgroup observations while such an
unexcluded handler remains possible.

The following are explicitly insufficient evidence:

- `RLIMIT_CORE=0` alone under a pipe pattern;
- `coredump_filter=0` or any selected mapping mask;
- no `core` file appearing in the workload cwd;
- a pre-exec-only `PR_SET_DUMPABLE=0` call;
- a self-report from the workload or supervisor;
- a ptrace event without proof of post-exec dumpability and the entire process
  tree;
- cgroup `populated=0` without accounting for an initial-namespace pipe
  helper; or
- a successful ordinary exit that never exercises a core-generating path.

## 6. Path comparison

### 6.1 Path A: dedicated ephemeral non-pipe Linux runner/VM

Path A uses a dedicated, task-scoped, ephemeral Linux/x86_64 runner or VM whose
initial-namespace `core_pattern` is non-pipe before the tool-system job begins.
The runner control plane, kernel, and isolation provider remain in the trusted
TS-B02 core boundary already frozen by the parent; this does not add an
independent-attestation requirement.

The future Path A proof must freeze and demonstrate all of the following:

- one exact runner/VM owner, provider, image, label, lifecycle, and isolation
  boundary;
- Linux/x86_64, kernel release, boot identity, cgroup v2, namespace, mount,
  ptrace, pidfd, seccomp, `openat2`, `execveat`, and quota capabilities required
  by the existing TS-B02A contract;
- raw initial-namespace `core_pattern` bytes that do not begin with `|`, read
  before capability PASS and re-read after workload cleanup;
- a frozen configuration digest binding the image, kernel, boot identity,
  relevant core-dump sysctls, capability set, and cgroup/mount configuration;
- no workload or repository-controlled ability to mutate `core_pattern`, the
  image, runner configuration, or provider controls;
- inherited immutable soft and hard `RLIMIT_CORE=(0,0)`, read back from the
  actual post-exec tracee and every descendant, with `setrlimit` and
  `prlimit64` restoration attempts denied as already required by the candidate
  contract;
- bounded core-generating synthetic fixtures covering sealed static and
  dynamic ELF, the actual loader, shebang/interpreter chains, a first-user-
  instruction crash, fork/vfork descendants, and the required core-generating
  signal classes;
- host-gate drift, supervisor-death, descendant-crash, and cleanup-failure
  injection demonstrating that the complete workload tree terminates and
  cleans up without a core file or process outside the owned execution
  boundary;
- before/after host observations that match the same execution, kernel boot,
  request, policy, backend configuration, and cleanup interval;
- no skip, xfail, mock, fallback, observation loss, or residue; and
- destruction or verified reset of the ephemeral runner/VM under its separately
  authorized infrastructure lifecycle.

No ordinary shared self-hosted machine qualifies merely because an operator
can edit its sysctl. The future package must prove task exclusivity, initial
configuration, non-drift, cleanup, and disposal/reset boundaries.

### 6.2 Path B: retain a pipe pattern and prove equivalent suppression

Path B is not accepted by this specification. It remains a research-only
possibility because no current Hosted observation proves all of the following
conjunctive obligations:

- dumpability is set to and observed as zero after the initial exec transition
  and before the first workload instruction;
- every fork, vfork, clone, thread, reparent, and permitted descendant inherits
  or receives the same state before it can execute a core-generating action;
- the workload cannot call `PR_SET_DUMPABLE` to restore dumpability, change
  credentials or limits to alter the invariant, or perform an unobserved exec;
- all exec, clone and terminal races, including tracer loss and observation
  gaps, fail closed;
- synchronous faults and every core-generating signal path are covered;
- seccomp termination paths that generate a core are covered rather than
  treated as automatically safe;
- `CLONE_UNTRACED`, unobserved `clone3`, multithreaded races, and secondary exec
  cannot escape the observation or injection boundary;
- current-run OS evidence proves that the host pipe helper received no payload
  and did not start for the matching workload; and
- helper absence, complete process-tree cleanup, and evidence completeness are
  proved without modifying an unauthorized host service or trusting an
  application-created zero.

Passing only dumpability tests would not satisfy the last two obligations.
Any future attempt to qualify Path B requires a separately authorized contract
re-freeze and Hosted adversarial probe. It may not be described as a repair of
PR #231 under the current frozen contract, and a failed research result may not
fall back to ordinary-host execution.

### 6.3 Decision matrix

| Criterion | Path A | Path B |
| --- | --- | --- |
| Removes pipe helper from required execution configuration | Yes, by pre-job runner contract | No |
| Preserves existing non-pipe capability gate | Yes | No; requires contract re-freeze |
| Compatible with immutable `RLIMIT_CORE=0` semantics | Yes, subject to real proof | `RLIMIT_CORE` alone is ignored |
| Current Hosted proof available | No; new runner proof required | No |
| Requires workflow/runner/infrastructure authority | Yes | Likely requires new observation/enforcement authority |
| Eligible to resume or replace TS-B02A after a new exact authorization | Yes | No, unless separately proved and re-frozen |
| Selected by this specification | **Yes** | **No; research only** |

Path A is the sole current path to TS-B02A capability acceptance. This is a
path decision, not a runner deployment or capability PASS.

## 7. Exact next prerequisite and authorization boundary

No implementation starts automatically. The next eligible task identity is:

`TOOL-SYSTEM-TS-B02A-DEDICATED-EPHEMERAL-LINUX-X86_64-RUNNER-NON-PIPE-CORE-PATTERN-CAPABILITY-ENABLEMENT-AND-PROBE-v1`.

It cannot start from this report alone. A new explicit user authorization must
first name or approve:

1. the exact dedicated ephemeral runner/VM provider, owner, image, runner label,
   Linux/x86_64/kernel identity policy, tenancy, and lifecycle;
2. the exact repository and external paths to add or modify;
3. every workflow, runner, permission, infrastructure, credential-reference,
   secret, network, and cost surface;
4. the exact pre-job non-pipe `core_pattern` configuration and its immutable
   evidence/cleanup owner;
5. the exact synthetic fixtures, capability/adversarial matrix, evidence
   transport, and no-residue proof;
6. finite local, Hosted, repair, time, and cost budgets;
7. rollback and runner destruction/reset behavior; and
8. the lifecycle disposition for PR #231 after the canonical base advances:
   either explicitly re-align the original feature branch or create one
   explicitly authorized successor and record the non-active status of the
   earlier candidate. Neither choice is authorized here.

If a concrete runner/VM and the required authority surfaces cannot be named,
the next task is blocked as
`DEDICATED_RUNNER_AUTHORITY_AND_IDENTITY_UNAVAILABLE`. It must not silently
switch to Path B or the ordinary Hosted runner.

The Path A task may prove only runner capability and the bounded synthetic
isolation matrix. It may not start TS-B02B, TS-B02C, TS-B02D, public-entry
reacceptance, subscription transport, or real repository/business execution.

## 8. Interface and ownership preservation

This specification does not change the frozen TS-B02 owner split:

| Surface | Natural owner | Preserved boundary |
| --- | --- | --- |
| runner/VM capability and lifecycle | future dedicated-runner capability package plus explicitly named infrastructure owner | Establish and prove the supported host; does not select a business worker or synthesize execution evidence. |
| `IsolationRequestV1` construction | future TS-B02B worker-adapter | Select expected worker, identity, and policy; does not execute or seal. |
| enforcement and `ExecutionEvidenceV1` | TS-B02A isolated-execution | Gate, seal, execute, enforce, observe, clean, and return immutable current-run evidence. |
| independent matching and TS-B01/TS-B02 join | future TS-B02C task-runner | Validate all worker/validation records and publish only scoped evidence-derived results. |
| affected-closure acceptance | future TS-B02D evidence owner | Revalidate the chain; does not implement runtime or enable real execution. |

No runner image, provider, workflow label, repository secret, or credential
reference is invented by this report. Those values remain unknown until the
next authorization supplies current evidence.

## 9. Preserved findings and non-claims

This specification preserves without correction:

- TS-B01: `corrected_pending_reacceptance`;
- TS-B02: confirmed blocker;
- subscription-worker public entry: not accepted;
- real repository execution: blocked;
- Draft PR #231: unaccepted and unmerged;
- TS-H01, TS-H02, TS-H03, TS-H04, and TS-H05: unchanged;
- TS-M01, TS-M02, TS-M03, and TS-M04: unchanged by this package; and
- TS-B02B, TS-B02C, TS-B02D, public reacceptance, functional subscription
  transport, and every real workload: not started.

The package does not claim that a runner exists, that Path A is currently
available, that Path B is impossible on every Linux system, that a core handler
has never run, that the candidate is safe to merge, or that any execution has
absolute zero effect. Only the observed PR #231 attempt is classified, and its
workload was not released.

TS-H04/H05 and TS-M04 remain valid independent follow-up candidates but are not
part of this task. They may not be bundled into the runner or TS-B02A packages
without their own exact authorization and affected-closure plan.

## 10. Validation and publication stop

The exact branch is:

`agent/subscription-worker-ts-b02a-pipe-core-pattern-containment-feasibility-path-closure-spec-v1`.

The exact commit message is:

`Specify TS-B02A pipe core_pattern containment path`.

Validation requires:

- strict validation of this task manifest and its exactly bound change plan;
- full pytest on the canonical base plus the three additions;
- current active-gate, process-authority, module-registry, and
  repository-manifest validators;
- exact three-addition, regular-file `100644` diff closure;
- `git diff --check`; and
- unchanged Hosted CI with no workflow, runner, permission, dependency, or
  supply-chain modification.

One Draft PR is allowed. Only if its base, head, exact three paths, one commit,
checks, comments, reviews, and review threads remain drift-free and every
required Hosted check succeeds may it become Ready and be squash-merged. The
original feature branch must remain at its original PR head. A validation
failure may receive at most one correction within the same three paths and at
most one rerun. An external capability request, fourth path, repeated state,
or second failure stops without weakening the specification.

Both success and failure stop. Success does not start the dedicated runner
task, alter PR #231, or perform any real execution.

## 11. Exact path closure

Add exactly these regular `100644` paths:

1. `docs/reports/subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_specification_v1.md`;
2. `examples/task_manifests/tool_system_subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_spec_v1.yaml`;
3. `examples/change_plans/tool_system_subscription_worker_ts_b02a_pipe_core_pattern_core_dump_containment_feasibility_and_path_closure_spec_v1.yaml`.

No path is modified or deleted. `REPO_MANIFEST.md` already classifies these
three locations through retained non-authority globs and therefore remains
unchanged.

## References

- [K1] Linux `core(5)`, especially pipe-handler namespaces, stdin payload, and
  `RLIMIT_CORE`: <https://man7.org/linux/man-pages/man5/core.5.html>
- [K2] Linux `execve(2)`, effect on the dumpable attribute:
  <https://man7.org/linux/man-pages/man2/execve.2.html>
- [K3] Linux `PR_SET_DUMPABLE(2const)`:
  <https://man7.org/linux/man-pages/man2/PR_SET_DUMPABLE.2const.html>
- Linux kernel `core_pattern` sysctl documentation:
  <https://docs.kernel.org/admin-guide/sysctl/kernel.html#core-pattern>
- PR #231 frozen isolated-execution contract:
  <https://github.com/apolo183/tool-system/blob/f94a9072eefe012b1d17bc9f87682b4287e1274d/docs/modules/isolated-execution-contract-v1.md>
- Draft PR #231: <https://github.com/apolo183/tool-system/pull/231>
- Failed Hosted run: <https://github.com/apolo183/tool-system/actions/runs/32580223111>
