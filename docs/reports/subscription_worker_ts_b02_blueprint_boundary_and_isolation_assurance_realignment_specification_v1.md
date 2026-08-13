# TS-B02 blueprint boundary and isolation assurance realignment specification v1

## Decision and frozen base

This report implements only
`TOOL-SYSTEM-TS-B02-BLUEPRINT-BOUNDARY-AND-ISOLATION-ASSURANCE-REALIGNMENT-SPEC-v1`.
Its disposition is:

`SPECIFICATION_ONLY / TS_B02_CORE_ASSURANCE_BOUNDARY_REALIGNED / IMPLEMENTATION_NOT_STARTED / ACCEPTANCE_UNCHANGED`.

Before work began, the GitHub App re-read `refs/heads/main` and the referenced
Git commit object. The immutable base is:

- repository: `apolo183/tool-system`;
- commit: `d99afa8f2835fb663c7db958b0060d45ab9dd349`;
- tree: `d7c4b97a16986d762d79f2c05b69ce9573a086b5`.

This package adds exactly this report and its paired task manifest and change
plan. All three paths are retained non-authority evidence under the existing
`REPO_MANIFEST.md`. It modifies no blueprint, project-state record, module,
contract, source, test, workflow, runner, permission, supply-chain input,
external service, infrastructure, or public acceptance surface. Its
`authority_effect` is `none`.

This report narrows the assurance target for the future TS-B02 package chain;
it does not claim that TS-B02, TS-M01, or any other finding is corrected. The
earlier TS-B02 and TS-B02A reports remain retained historical planning
evidence. Where they make caller-independent attestation, an external trust
root, an external verifier, or persistent cross-run receipt consumption a
mandatory precondition for blueprint completion, that higher-assurance
profile is no longer a TS-B02 blueprint-aligned core-isolation gate under this
realigned package.

## 1. The scope tension and its formal resolution

### 1.1 Governing boundary

`blueprint/tool_system_v0.yaml` defines a bounded, blueprint-driven development
system that runs approved work in an isolated repository workspace. It also
states that `arbitrary_untrusted_code_containment` is a non-goal and limits the
completion claim to the approved bounded blueprint and isolated repository
fixture.

The original TS-B02 correction specification correctly identified defects in
ordinary host subprocess execution, command-name identity, descendant control,
network control, and application-constructed zero-effect fields. Its later
TS-B02A prerequisite expanded the proposed proof profile so that the caller,
host supervisor, signer, verifier, and durable replay authority had to be
independent trust domains. That expansion would make cloud/service ownership,
KMS or HSM custody, external attestation, and persistent one-use receipt
consumption prerequisites to the core blueprint even though the blueprint does
not claim containment against a malicious operator, host administrator, or
kernel.

The resolution is to separate two assurance profiles:

| Profile | Purpose | Required for TS-B02 blueprint-aligned core isolation |
| --- | --- | --- |
| `ts_b02_core_local_os_v1` | Enforce and observe a bounded approved development workload using OS controls on a trusted host/control plane. | Yes. This is the frozen TS-B02 target. |
| future independent-attestation profile | Add trust separation, independent non-repudiation, persistent replay resistance, or verification across hosts/runs. | No. It is a future optional higher-assurance security module. |

The first profile must be real OS enforcement, not an application convention,
mock, Python audit hook, shell setting, or self-reported sandbox label. The
second profile must not be represented as present merely because the first
profile passes.

### 1.2 Core trust and threat model

For `ts_b02_core_local_os_v1`, the trusted computing and control boundary is
the authorized tool-system operator, the selected supported host, its kernel
and OS isolation primitives, and the isolation provider configuration approved
for the current run. Application orchestration is within that control plane,
but its assertions are not evidence of OS effects.

The contained subject is one approved, bounded, unprivileged development
workload plus every process and resource it creates. Repository content and
the workload may be faulty or may exercise adversarial boundary cases. That is
necessary to test the controls; it does not turn the product into a general
service for arbitrary hostile code.

The TS-B02 core-isolation claim explicitly excludes:

- a malicious or compromised operator, host administrator, kernel, hypervisor,
  isolation provider, or CI control plane;
- arbitrary attacker-supplied code outside an approved bounded task and
  executable policy;
- covert channels, microarchitectural attacks, host-to-host attestation,
  independent non-repudiation, and proof against the trusted control plane;
- durable global replay prevention or atomic receipt consumption across runs,
  machines, services, or disaster-recovery boundaries; and
- unrestricted remote mutation and production deployment.

Failure to make those excluded claims is not a weakening of the TS-B02
blueprint-aligned isolation target. It is the claim boundary imposed by the
blueprint objective and non-goals.

### 1.3 Relation to broader blueprint completion and subscription transport

This report realigns only TS-B02 isolation assurance. It does not by itself
satisfy the blueprint's broader supported-subscription or real-worker
completion requirements.

`deny_all` is the mandatory TS-B02A-through-TS-B02D network baseline. Before
any future live Codex subscription execution, a separately authorized and
versioned functional `subscription_transport_only` network profile must define
the exact permitted endpoints, name resolution, credential/data-transfer
boundary, inherited handles, observation, and fail-closed behavior. That
functional transport gate is not the optional independent-attestation security
module described in Section 5, and neither one authorizes the other.

No transport profile is implemented or accepted by TS-B02A through TS-B02D or
by the public-entry reacceptance decision described here. Public reacceptance
is an evidence/status decision, not live-execution authority. Real execution
therefore remains separately blocked until every applicable functional gate
and explicit execution authorization is complete.

## 2. Frozen TS-B02 blueprint-aligned core isolation guarantees

Every future TS-B02 implementation and acceptance package must implement and
prove all guarantees below on a real supported OS backend. A missing primitive,
incomplete observation, identity mismatch, policy drift, or provider failure
must stop before workload execution when detectable at preflight, otherwise
terminate the complete execution boundary and return a non-success result.

| Guarantee | Normative core requirement |
| --- | --- |
| Filesystem boundary | Run in an execution-specific workspace with canonical cwd and approved roots. Deny writes and prohibited reads outside policy using OS enforcement. Reject symlink, mount, path-rebinding, descriptor inheritance, and cleanup escape cases. |
| Complete process tree | Place the initial process and every child, grandchild, reparented, detached, or double-forked descendant in one OS-enforced and OS-observable containment and accounting boundary. Process-group membership alone is insufficient. |
| Process cleanup | At normal completion, violation, output-limit breach, timeout, or provider error, terminate the whole boundary, wait for teardown, and prove that no tracked descendant survives before reporting a complete result. |
| Default-deny network | Establish an OS-enforced network-deny boundary before the first workload PID. Deny socket, DNS, loopback, inherited network handle, namespace bridge, and equivalent egress unless a future separately approved profile says otherwise. |
| Executable and interpreter identity seal | Bind the launched executable to an absolute non-symlink regular-file identity, content digest, file identity/stat tuple, and the interpreter/loader chain that will actually execute it. A command basename, `PATH`, or preflight-only hash is insufficient. |
| TOCTOU blocking | Hold or revalidate execution-critical objects at the exec transition using an open-descriptor, `execveat`-equivalent, immutable snapshot, or equally race-resistant mechanism. Replacement of a binary, script, interpreter, loader, policy, workspace, or backend configuration must block. |
| Streaming output limit | Drain stdout and stderr incrementally while the process runs, account bytes at the execution boundary, enforce a finite configured limit without unbounded buffering, and terminate the complete tree on breach. Record emitted, retained, and discarded byte counts and the limit event. |
| Timeout termination | Use a monotonic deadline enforced by the isolation provider, not only by the caller. On expiry, perform bounded graceful termination followed by forced termination, then verify no survivor before completing the record. |
| Current-run OS-derived evidence | Produce an execution-matched record from enforcement-layer and OS observations covering preflight, exec identity, process membership, filesystem/network policy, stream limits, deadline, termination, cleanup, and completeness. Application constants or workload self-report cannot satisfy this requirement. |

These guarantees are conjunctive. For example, a filesystem namespace without
complete descendant cleanup, or a process boundary without a sealed
interpreter, does not satisfy TS-B02.

The workload must remain unprivileged relative to the isolation provider. It
must not access provider control sockets or descriptors, namespace/cgroup/mount
control surfaces, supervisor memory through `ptrace` or an equivalent path,
privilege-escalation capabilities, or a mechanism that moves any process or
resource out of the containment boundary. Unavailable control separation is a
capability failure, not an ordinary-host fallback.

### 2.1 Filesystem and resource lifecycle details

The request must identify the exact source/candidate/workspace identities and
the permitted read/write roots. The provider must canonicalize and bind those
identities before execution. The policy must cover cwd, temporary files,
inherited descriptors, proc/sys/device views, mount propagation, symlinks and
hard links where applicable, and teardown of execution-owned resources.

The request must also bind finite quotas for execution-owned scratch space,
declared output files, and other writable filesystem resources. The provider
must enforce them at the OS/filesystem boundary so a workload cannot bypass
stream limits by filling a file or device. Undeclared output paths block; a
quota breach terminates the complete tree. Evidence records bytes written and
retained, any discarded bytes, the configured per-resource and aggregate
limits, and the breach/cleanup result.

Cleanup means removal or verified quarantine of provider-created namespaces,
cgroups, mounts, temporary directories, and process resources. This is
execution-boundary cleanup, not authorization for repository, production, or
remote cleanup operations.

### 2.2 Process, output, and timeout details

The provider must use an OS mechanism that cannot lose a descendant merely
because it calls `setsid`, double-forks, reparents, changes process group, or
outlives the immediate parent. PID identity must be stable against PID reuse,
for example through pidfds, start-time binding, a cgroup identity, or an
equivalent supported mechanism.

Output handling must be streaming and backpressured or drained so that a child
cannot deadlock the supervisor by filling a pipe. A limit breach is a boundary
event, not successful truncation. The provider must terminate the complete
tree, finalize bounded output, and mark the execution non-successful. Byte
accounting occurs on raw bytes before decoding and freezes explicit
per-stream and combined-limit semantics.

The TS-B02A implementation may implement this streaming guarantee for the new
isolated-execution path. Doing so does **not** mark audit finding TS-M01
corrected: TS-M01 retains its present status until a separately authorized
full affected-closure correction and reacceptance explicitly disposes of it.

### 2.3 Executable identity and TOCTOU details

Selection and enforcement have distinct owners. A consumer supplies the
expected absolute executable, content digest, file identity constraints, and
interpreter policy. The isolation provider owns canonicalization, open/seal,
interpreter and loader resolution, exec-critical-point revalidation or
descriptor-based execution, and the OS observation of what executed.

For scripts, the seal covers both script content and the actual interpreter
chain. For native executables, it covers the actual executable and loader
identity where the supported platform exposes one. Any inability to bind the
actual exec identity returns `unsupported` or `identity_mismatch` before a
successful result. The worker-adapter must not reimplement the seal, and the
provider must not choose business-level worker policy.

## 3. Current-run OS-derived evidence contract

The TS-B02 core evidence object is named an **execution evidence record**,
not an independently attested receipt. A future implementation may choose a
versioned type such as `ExecutionEvidenceV1`; the semantic fields below are
mandatory regardless of serialization.

| Field group | Required binding or observation |
| --- | --- |
| Profile and provider | schema version, `ts_b02_core_local_os_v1`, provider/backend identity and configuration digest, capability-preflight result |
| Request | unique current-run execution ID, request digest, task/source/candidate/workspace identities, policy digest, caller-supplied expected executable and interpreter identities |
| Filesystem and network | OS boundary identities, effective read/write roots, cwd, scratch/output quota identities and raw-byte counts, default-deny network establishment, violations and teardown status |
| Exec | actual absolute executable, content digest, stable file identity, interpreter/loader chain, and exec-critical-point match result |
| Processes | initial stable process identity, containment identity, descendant accounting, exit/termination reason, forced-kill result, and survivor check |
| Streams and time | stdout/stderr emitted, retained, and discarded byte counts, limit and breach status, monotonic start/deadline/end observations, timeout result |
| Completeness | required event/observation classes, missing-data list, provider errors, final completeness status, and record digest |

The matching predicate is exact. The record must match the current invocation's
execution ID, request digest, policy digest, workspace/source/candidate
identities, expected and actual executable/interpreter identities, backend
configuration, and terminal cleanup observation. A record from a different
execution, even with identical source content, is not matching evidence.

Within one run, execution IDs must be unique and stale or duplicate records
must be rejected by the consuming application state. This is ordinary
current-run correlation, not a claim of durable cross-run atomic anti-replay.
The record may be hashed or locally authenticated for corruption detection,
but such protection does not create an independent trust root.

Missing, incomplete, malformed, fabricated, stale, duplicated, or mismatched
evidence fails closed. The application must not fill missing observations with
zeros or infer OS enforcement from process exit code, a configured mode,
provider name, command-line flags, or its own request.

### 3.1 Exact join with TS-B01 semantic evidence

An execution evidence record proves only the scoped OS enforcement and observed
effects of its own execution. TS-B01 execution-binding v2 evidence proves the
acceptance semantics, independent diff/behavior obligations, and candidate
meaning. Neither record can substitute for the other.

Worker-adapter performs the first exact validation of each worker execution
record before returning it. Task-runner is the final aggregator: before any
execution/effect-dependent public projection, it must independently verify the
immutable provider record (or its exact provider-verifiable representation) for
every worker and validation execution and join those records to the applicable
TS-B01 v2 evidence. The join must match task/request and execution identities,
source and candidate identities and digests, configuration and policy identity,
command/obligation identity, and terminal result. A missing or mismatched
worker record, validation record, or TS-B01 semantic record blocks that
projection.

## 4. Public claim and zero-effect rule

Application code may publish an execution/effect-dependent claim only as a
scoped projection of a complete matching execution evidence record. It must
distinguish at least:

- `enforced_and_no_violation_observed_within_execution_boundary`;
- `violation_observed`;
- `incomplete_or_unknown`; and
- `not_executed`.

A numeric zero may be projected only as an observation within the named
execution boundary, time interval, policy, and evidence record. It may not be
described as absolute `zero-effect`, `hard-zero`, “no side effects anywhere,”
or an equivalent universal guarantee. Without matching OS-derived evidence,
the only permitted projection is incomplete/unknown or not-executed, and any
acceptance claim requiring execution or effect proof must block. A
`not_executed` result may support planning or specification evidence but cannot
prove runtime safety or zero effects.

Application code, including task-runner and worker-adapter code, is forbidden
from constructing, defaulting, or publishing an absolute zero-effect/hard-zero
conclusion. It may validate and consume evidence; it may not substitute for
the OS observation producer.

## 5. Optional higher-assurance security module

The following capabilities are explicitly outside the TS-B02 blueprint-aligned
core-isolation completion gate. They may be proposed later as a separately
versioned, separately owned, optional higher-assurance module after a fresh
authorization:

- an independent cloud isolation or audit service;
- a caller-independent supervisor, auditor, signer, or trust root;
- KMS, HSM, TPM, confidential-computing, or hardware-attestation custody;
- OIDC federation, workload identity, or external attestation exchange;
- an external persistent verifier or durable replay database;
- cross-run, cross-host, or cross-service monotonic sequences; and
- atomic one-use receipt consumption across failures or recovery domains.

No provider, repository, cloud account, service, credential, permission, cost,
path, interface name, or deployment design for that optional module is frozen
or authorized here. The earlier TS-B02A disposition
`NO_VERIFIABLE_ARCHITECTURE` remains valid evidence for the independent-
attestation profile examined there; it is not a blocker to planning the
TS-B02 core local-OS profile defined by this report.

The optional profile may consume the core execution evidence record and wrap
it in a separately attested receipt. It must not weaken core enforcement, and
the core product must not advertise the optional profile when it is absent.

## 6. Refrozen owners, interfaces, and strict sequence

Every step requires a new user authorization and a fresh-state base/tree,
path, dependency, and governance check. No step may be combined with its
successor.

| Order | Package | Natural owner and interface boundary | Required result | Explicit exclusions |
| --- | --- | --- | --- | --- |
| 0 | `TOOL-SYSTEM-TS-B02A-CORE-LOCAL-OS-ISOLATION-BACKEND-FEASIBILITY-PROBE-AND-PATH-CLOSURE-v1` | Non-durable tool-system feasibility surface. It selects no business worker and owns no runtime interface. | Use bounded non-live synthetic probes to demonstrate required OS primitives, privileges, architecture, and Hosted availability with no known blocker; freeze exact capability gates, `IsolationRequestV1`/`ExecutionEvidenceV1` semantics, TS-B02A path closure, adversarial matrix, dependency/license risk, and fail-closed design. Full integrated conformance remains TS-B02A/TS-B02D work. | No real repository or business workload, runtime implementation, target/business remote effect, external trust dependency, or automatic TS-B02A start. Any probe/repository/Hosted path or CI change requires exact separate authorization. |
| 1 | TS-B02A | New `isolated-execution` natural owner with its `isolated-execution-api` v1 boundary. | Implement capability preflight, filesystem/process/network enforcement, stream and timeout control, exec/interpreter seal, TOCTOU blocking, cleanup, and current-run OS-derived evidence on a real backend. | No worker-adapter or task-runner change; no external attestation module; no status or public acceptance change. |
| 2 | TS-B02B | Existing `worker-adapter` natural owner consuming `isolated-execution-api` only. | Select the allowed worker and expected identity/policy, construct the isolation request, invoke the provider, perform first-level exact validation of the immutable worker evidence record, and return both bounded result and record to task-runner. | It does not implement the seal, execute directly, synthesize evidence, modify task-runner, or change acceptance. |
| 3 | TS-B02C | Existing `task-runner` natural owner, including its owned validation-command boundary and versioned public result projection. | Route every validation subprocess through isolated-execution; independently exact-match every worker and validation record; join them to TS-B01 v2 semantic evidence; remove ordinary-host fallback; publish only scoped evidence-derived observations. | No provider or worker-adapter enforcement implementation; no direct zeros; no public-entry reacceptance. |
| 4 | TS-B02D | Applicable TS-B02 acceptance-evidence owner, with the descriptive tool-system project-state owner synchronizing only the resulting disposition; no durable runtime interface. | Revalidate isolated-execution, worker-adapter, task-runner, managed import edges, direct consumers, unchanged CLI composition, exact TS-B01/TS-B02 joins, and the real-backend non-live adversarial matrix. If complete, record **TS-B02 only** as `corrected_pending_reacceptance`. | No runtime implementation, TS-M01 correction, other-finding correction, real repository execution, or public reacceptance. |
| 5 | Later public-entry reacceptance | Subscription-worker public-entry acceptance-evidence owner, with the descriptive project-state owner synchronizing the decision; no runtime interface. | Re-evaluate the public entry from the then-current canonical state using completed TS-B01 and TS-B02 evidence, explicitly account for every still-open finding and transport gate, and record only the evidence/status decision. | It must not infer acceptance, correct another finding, enable transport, or start real execution merely because TS-B02D completed. |

The owner split is strict:

- worker-adapter owns worker selection, expected identity, request construction,
  and first-level validation of the worker record;
- isolated-execution owns the actual identity seal, race-resistant exec,
  enforcement, OS observation, and evidence production; and
- task-runner owns validation routing, independent final matching of every
  worker and validation record, the TS-B01/TS-B02 join, aggregation, and the
  scoped public projection.

This removes the former overlap in which both worker-adapter and
isolated-execution appeared to own the exec seal and evidence production.

### 6.1 Exact next implementation prerequisite

After this specification merges, the only next eligible TS-B02 action is the
separately authorized, bounded non-live feasibility package named at order 0.
Before any TS-B02A runtime write it must demonstrate, from the then-current
supported environments, that the required host-local OS primitives,
permissions, backend architecture, and Hosted availability have no known
feasibility blocker. It must freeze the complete conformance matrix and design,
but it does not prove integrated Section 2 conformance; TS-B02A implements that
contract and TS-B02D closes its affected evidence. Static documentation
inspection alone is not sufficient. The probe may create only
creator-owned temporary execution units, namespaces, processes, streams, and
files using synthetic fixtures, must clean them within its bounded lifecycle,
and must never access a real target repository or business workload. It must
freeze:

1. the exact backend and supported OS/architecture matrix;
2. a capability probe that fails before the first workload PID;
3. the exact request/evidence schema and owner boundary;
4. the exact new and modified paths for TS-B02A under the one-module invariant;
5. direct dependencies, licensing, install/runtime availability, cleanup, and
   rollback boundaries, plus the exact separately authorized path and Hosted
   proof method; any CI, runner, supply-chain, permission, or service change is
   a new authority surface and cannot be inferred from this report;
6. the complete core adversarial acceptance matrix and deterministic commands;
   and
7. a new explicit user authorization for the exact TS-B02A write package.

If any prerequisite item cannot be demonstrated, the feasibility package stops
with a TS-B02 core-backend blocker. It must not silently weaken a guarantee,
persist an unapproved environment change, select an external service, or
promote the optional higher-assurance profile to a core prerequisite.

## 7. Core adversarial acceptance matrix

The implementation chain must ultimately pass non-live tests on the real
selected local-OS backend. Backend absence is a failure. A mock provider may be
used in lower-level unit tests but cannot satisfy the TS-B02 acceptance cases;
skip, xfail, fake evidence, or application-constructed evidence cannot replace
them.

| Case | Required disposition |
| --- | --- |
| filesystem escape | Denied by the OS boundary; violation and teardown are present in matching evidence. |
| child/detach escape | Child, grandchild, reparented, detached, and timeout-surviving attempts remain accounted for; survivor check is clear. |
| network escape | Socket, DNS, loopback, inherited handle, and namespace-bridge attempts are denied under the default profile. |
| PATH/symlink replacement | Basename execution, symlink traversal, PATH substitution, and file replacement block before a successful exec. |
| interpreter/loader replacement | Script interpreter and native loader identity drift block and appear in the record. |
| exec TOCTOU | Rename, in-place mutation, policy/workspace/backend drift, and race attempts cannot produce a matched successful record. |
| output flood | Output is drained incrementally, the finite limit triggers, the full process boundary terminates, and counts remain bounded. |
| timeout/survivor | Monotonic timeout terminates and tears down the complete containment boundary and observes no survivor; a surviving descendant blocks completeness. |
| evidence fabrication or mismatch | Missing, app-built, stale-current-run, duplicate, incomplete, wrong-request, wrong-policy, or wrong-executable evidence blocks. |
| observation loss or incompleteness | A dropped/missing observation class, buffer overflow, provider/observer failure, sequence gap, missing teardown event, or unavailable survivor observation marks the record incomplete and blocks. |
| backend/capability loss | Capability failure blocks before workload PID when detectable and never falls back to ordinary host execution. |

Persistent cross-run replay, external verifier availability, independent signer
compromise, OIDC, and KMS/HSM cases belong only to a future optional profile and
are not TS-B02 core acceptance cases.

## 8. Preserved audit and operational state

This specification deliberately leaves the canonical state unchanged:

| Item | Preserved disposition |
| --- | --- |
| TS-B01 | `corrected_pending_reacceptance`; not reaccepted here. |
| TS-B02 | Confirmed blocker; no correction or acceptance upgrade in this package. |
| Public subscription-worker entry | Not reaccepted. |
| Real-repository execution | Blocked. No real execution occurs. |
| TS-H01 / TS-H02 / TS-H03 | Unchanged and uncorrected. |
| TS-M01 / TS-M02 | Unchanged and uncorrected. |

No undefined or historical finding identifier is silently added to the
authoritative finding set. This report does not change the project-state file,
the audit register, or any public acceptance mapping.

No real Codex or ChatGPT Web automation, API/provider call, credential access,
subscription transport, downstream repository access, runtime remote
operation, production action, deployment, infrastructure operation,
runtime/security external-service operation beyond the authorized GitHub
publication, cleanup, or rollback is performed or authorized.

## 9. Publication boundary and terminal stop

Publication is limited to exactly these three new regular files:

1. `docs/reports/subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_specification_v1.md`;
2. `examples/task_manifests/tool_system_subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_spec_v1.yaml`;
3. `examples/change_plans/tool_system_subscription_worker_ts_b02_blueprint_boundary_and_isolation_assurance_realignment_spec_v1.yaml`.

The exact branch is
`agent/subscription-worker-ts-b02-blueprint-boundary-isolation-assurance-realignment-spec-v1`
and the exact commit message is
`Specify TS-B02 blueprint boundary and isolation assurance realignment`.

After deterministic validation, one Draft PR, successful unchanged Hosted CI,
exact base/head/path/commit and comment/review/thread no-drift checks, guarded
Ready transition, squash merge, and retention of the original feature branch
at the original PR head, work stops. Do not start the order-0 feasibility probe,
TS-B02A, TS-B02B, TS-B02C, TS-B02D, public-entry reacceptance, or any real
execution.
