# TS-B02 isolated-execution boundary correction specification v1

## Decision and frozen base

This package is the non-executing specification
TOOL-SYSTEM-TS-B02-ISOLATED-EXECUTION-BOUNDARY-CORRECTION-SPEC-v1.
Its canonical parent is tool-system commit
3a37fdb28140c73471fb96000a95e37f076792bf with tree
6f2d784a4bb35ca6be5f72cab2df73079cf9e3e0.

The frozen starting disposition is:

- TS-B01 is corrected_pending_reacceptance and its execution-binding v2 and
  semantic evidence remain unchanged.
- The subscription-worker public entry has not been reaccepted.
- Real-repository execution remains blocked by TS-B02.
- This package has authority_effect: none. It specifies later packages; it
  implements none of them.

The decision is TS_B02_SPECIFIED_NO_RUNTIME_IMPLEMENTATION. The correction
must use a new narrow durable module and versioned interface named
isolated-execution / isolated-execution-api. None of the three existing
natural owners can absorb the shared boundary without responsibility drift.

## Complete fresh-state evidence ledger

Every source below was reread from the exact canonical commit before this
specification was written. Blob identities make the cited evidence
content-addressed.

| Source | Canonical blob | Evidence used |
| --- | --- | --- |
| AGENTS.md | d6e09fa4fc51370a212bec4cd7a087f9b99a2437 | Requires current central-main consumption, docs-first bounded closure, exact process authority, one durable module or versioned interface per milestone, fail-closed side-effect preflight, and descriptive project state. |
| REPO_MANIFEST.md | efcde3b3ac5afb4fa34407a46eca9e26a42b9058 | Registers docs/reports, examples/task_manifests, and examples/change_plans as retained non-authority sets, so this exact three-path specification needs no fourth registration path. |
| blueprint/tool_system_v0.yaml | c86640ec5bf3b89181ee62967d76b951e29bc3fe | Requires isolated workspaces and the durable-module invariant, while explicitly excluding arbitrary untrusted-code containment from the current product claim. |
| docs/tool_system_global_development_principles_v1.md | df8f7d1cb576057bd176280b090b052686012648 | Requires explicit authorization, frozen acceptance, finite closure, natural ownership, failure isolation, and affected-closure revalidation. |
| docs/tool_system_project_state_v1.yaml | 8e64f40a14a34df3b3e98cee2be8df9bf3c3fd21 | Records TS-B01 as corrected_pending_reacceptance, TS-B02 as the remaining blocker, public acceptance false, and real-repository execution blocked. |
| docs/reports/independent_audit_acceptance_reopen_v1.md | af5af782ac2bdb4f40e1d505d07195c741880139 | Confirms that ordinary host subprocess execution, command-name worker identity, and constructed zero-effect fields do not prove isolation or observation. |
| docs/reports/subscription_worker_semantic_acceptance_evidence_correction_v1.md | 7adf56ab9b68f794dd1bf2c9eb738fa4b7c1a7d3 | Freezes TS-B01 execution-binding v2 and explicitly leaves OS validation isolation, resolved worker identity, and OS-derived effect observation to TS-B02. |
| config/module_registry_v1.yaml | 12c0c0f38bce98b8c3a780f75205d05e8b97dbcc | Registers 26 current modules, no isolated-execution provider, fixture-only agent-worker-runtime, worker-adapter as task-runner provider, and command_runner.py under task-runner ownership. |
| docs/tool_system_module_registry_contract_v1.md | a41eddf307f3ee5b8a5d858357f6e3029ac45045 | Confirms the provider-to-consumer DAG, one active owner per source path, versioned aggregate interfaces, effect taxonomy, and separate audit for identity or dependency changes. |
| docs/modules/agent-worker-runtime-contract-v1.md | 8dbff37312c2cc8c60c26ad8f66c857288a72ee9 | Limits the module to approved Python fixture execution in an ephemeral workspace with application-level guards; it is not a hostile-process sandbox. |
| docs/modules/worker-adapter-contract-v1.md | 80444e59cd6ad2072ff0e64a56d7fb4cea9d7f5b | Defines fixed shell-free Codex argv, self-declared read-only mode, timeout handling, and structured output, but no absolute binary seal or trusted OS effect receipt. |
| docs/modules/task-runner-contract-v1.md | 33ab5e56887ba223cb3839d79680f11b8ce2e415 | Owns configured validation and public result composition, but currently has no independently enforced isolation provider or OS observation receipt. |
| src/tool_system/gate/command_runner.py | 1bb190e88c0d74c22b656c483811ef0abbe4e80a | Calls subprocess.run with shlex-split argv, shell=False, caller cwd, and inherited host environment; it supplies no OS filesystem, process, or network boundary. |
| src/tool_system/worker_adapter/contract.py | 57a6927d8c1c245ad18bcbfcd2271e0c0a75f4e6 | Requires a slash-free executable command name, starts that name through the host, and reports a configured sandbox_mode string without resolving or sealing the executed binary. |
| src/tool_system/runner/task_runner.py | 1e1b642debb391b896b3e64fec99a2a6687791ea | Runs validation through command_runner and directly constructs provider, credential, target, remote, production, cleanup, and rollback zero fields. |
| tests/test_agent_worker_interface.py | 83323fc8fd942f35db61a15d5b031244deb958b1 | Covers the bounded fixture interface, not hostile arbitrary processes. |
| tests/test_process_worker_runtime_preflight.py | 394e2fa1b74c594fa973734caac865108e29d412 | Covers fixture path, identity, permission, environment, and preflight guards. |
| tests/test_process_worker_runtime_execution.py | 58ce5506a12313590fe09998d4f08d580fb97b42 | Covers approved fixture execution and application-level result behavior. |
| tests/test_process_worker_runtime_adversarial.py | d5646015d3916cac8d7df42928fee11c8437c682 | Covers Python audit-hook fixture attacks, not an independently enforced OS sandbox for arbitrary binaries. |
| tests/test_command_runner.py | 0216d9d61001344116246b69387b0866e67b60b5 | Covers ordinary command success, failure, timeout, output, and environment behavior without a real isolation backend. |
| tests/test_worker_adapter_contract.py | 292c538403e6cbf4b53b0cffaec514528f03866b | Uses fake process runners and accepts the command name codex and configured read-only string; it does not prove actual binary identity or OS effects. |
| tests/test_worker_adapter_orchestration.py | 445e857ff466ffbaa10c882f17c27ff01a9f06a1 | Covers bridge mapping through a fixture adapter and no direct target mutation. |
| tests/test_task_runner.py | 50677a3b27c78115dc38a21d3adc96ccbe164542 | Uses fake worker processes and ordinary host validation commands, and asserts directly returned hard-zero fields. |
| tests/test_milestone_module_invariant.py | 36caaa2b856a120b8fff5363e6b1757e7c39a55b | Enforces one durable module or versioned interface per milestone, single responsibility, an acyclic dependency graph, and affected-closure revalidation. |
| tests/test_module_contracts.py | bdaf9aef4677e3b29f0af968d4e50a77bdad2748 | Seals the 26 module contracts, natural owners, dependency edges, and direct/delegated effect classifications. |
| tests/test_module_import_graph.py | e73fc86cfc347d95795d7636e4fd99406bb5358f | Requires observed managed imports to equal declared provider-to-consumer edges and rejects hidden dependencies. |
| tests/test_module_registry.py | 610d848d6982c6a4e33930d5b8a41df7d0b9cacf | Seals the current 26-row registry and exact module/interface ownership and dependency graph. |
| tests/test_phase_alignment.py | cb6860c46ab373c8eb1339d65ec5473ebfbe3807 | Enforces the reopened public-entry disposition, TS-B01 pending reacceptance, TS-B02 blocker, and zero-authority boundaries. |

Current central finance-governance main was also consumed directly at task
start: docs/global_development_principles_v1.md and
config/repo_registry_v1.yaml. Those sources confirm bounded closure and the
tool-system repository identity; they grant no additional write scope.

## Facts that all later TS-B02 packages must preserve

1. shell=False prevents shell parsing. It does not enforce filesystem,
   process-tree, or network isolation.
2. A Python audit hook observes and blocks selected Python runtime events. A
   child can execute a different runtime or kernel syscall path, so the hook
   alone is not OS isolation.
3. Codex reporting --sandbox read-only is a requested application mode and
   self-report. Without independent enforcement and observation it is not
   evidence of an OS boundary.
4. agent-worker-runtime is a fixture-only application guard. It must remain
   so unless a separately authorized module change explicitly replaces its
   contract; TS-B02 must not silently turn it into a generic adversarial
   process sandbox.
5. TS-B02 crosses two existing natural owners. worker-adapter owns the
   resolved absolute worker executable identity, content SHA-256, execution
   critical-point identity recheck, and worker-process observation receipt.
   task-runner owns validation command isolation, OS-derived side-effect
   evidence, receipt verification, and public result aggregation.
6. Each implementation milestone may add, modify, or replace only one
   durable module or one versioned public interface. Cross-owner changes may
   not be collapsed into one package.

## Natural-owner analysis and required new provider

| Candidate owner | Fresh-state evidence | Why using it as the shared provider would drift responsibility |
| --- | --- | --- |
| agent-worker-runtime | Its contract, source, and registered tests are limited to approved Python fixtures and application guards. | General hostile binary containment would contradict its fixture-only role and the blueprint non-claim. It would also make a narrow fixture runtime a shared infrastructure provider for unrelated validation and Codex execution. |
| worker-adapter | It naturally owns Codex executable selection and worker invocation. | task-runner validation is not worker-adapter behavior. Moving validation launch there would make a worker-specific adapter own generic command isolation and invert or broaden the current DAG. |
| task-runner | It naturally owns validation selection, semantic receipts, and public aggregation. | worker-adapter must establish worker identity and receive execution evidence before task-runner can consume it. Putting the backend in task-runner would make its provider depend on its consumer or duplicate enforcement. |

Therefore TS-B02A must introduce:

- canonical module ID: isolated-execution
- current module ID: isolated_execution
- aggregate interface ID: isolated-execution-api
- initial module and interface version: 1.0.0
- single responsibility: execute one content-identified command inside one
  independently enforced filesystem, process, and network policy and return
  one verifiable observation receipt
- direct consumers after their separately ordered packages: worker-adapter
  and task-runner

The module does not own task acceptance, Codex prompt or output semantics,
subscription transport authorization, validation selection, patching, local
Git, target mutation, provider policy, public result fields, deployment,
cleanup, or rollback.

## Frozen isolated-execution interface requirements

### Request and capability preflight

The request must bind a unique execution ID and one-time verifier challenge to:

- the interface and backend identity and version;
- the complete canonical policy document and its SHA-256;
- the absolute executable path and sealed executable identity;
- the exact argv, cwd, environment allowlist, stdin identity, timeout, output
  limits, and cancellation identity;
- the permitted filesystem roots and access modes;
- the process descendant and survivor policy;
- the network profile;
- the caller configuration identity and current canonical source identity.

Before launch, the provider must prove that a real supported enforcement
backend and its required audit capability are available. Missing, partial,
degraded, unverifiable, or configuration-mismatched capability fails closed
before executing the command. A fallback to ordinary host subprocess,
shell=False, Python audit hooks, self-reported sandbox mode, skip, xfail, or a
caller-fabricated receipt is forbidden.

### Filesystem, process, and network enforcement

The backend must be OS/kernel-enforced or equivalently independently enforced
from both the caller and executed workload:

- Filesystem: deny access outside explicitly mounted roots; enforce declared
  read-only or writable modes; deny symlink, mount, namespace, procfs,
  descriptor, device, and inherited-handle escapes; observe attempted and
  completed effects.
- Process: place the initial process, every child, grandchild, detached
  descendant, and timeout survivor inside the same boundary; deny boundary
  escape, unauthorized privilege or namespace transitions, and unobserved
  process creation; cancellation and timeout must terminate the whole
  bounded process tree and prove no survivor.
- Network: deny all address families, sockets, DNS, loopback, Unix-domain or
  equivalent IPC-to-network bridges, and inherited network handles by
  default; observe denied attempts and any specifically permitted flow.

An implementation may use Linux namespaces, cgroups, seccomp, LSM mediation,
an independently controlled VM, or another supported backend, but process
flags or application promises alone are insufficient. Backend equivalence
must be demonstrated by the same adversarial matrix.

### Executable identity and exec critical point

The interface must reject a basename or PATH-resolved command. The selected
executable must:

- be an absolute canonical path;
- be a regular executable file and not a symlink at any path component;
- have a content SHA-256 and immutable preflight file identity covering at
  least device or volume, inode or file ID, mode, owner, size, and
  high-resolution change metadata;
- include the interpreter or loader executable identity when the selected
  file requires one;
- be pinned by an open descriptor or equivalent safe handle when supported;
- be re-statted and re-hashed or safely executed from the pinned identity at
  the exec critical point; and
- produce an OS observation of the executable actually entered by the new
  process.

The observed exec identity must exactly equal the authorized request
identity. PATH substitution, symlink substitution, binary replacement,
in-place content change, rename swap, interpreter swap, TOCTOU, policy
change, environment drift, backend drift, and caller configuration drift
must block. No mismatch may be downgraded to a warning.

### OS-derived effect receipt

Successful or blocked execution returns a canonical content-addressed receipt
issued by the trusted backend or independent audit component, never by the
executed process or a caller convenience constructor. It must include:

- execution ID, one-time challenge, issue and expiry times, monotonic sequence
  or anti-replay identity, interface/backend/auditor identities and versions;
- request, source, caller configuration, policy, argv, environment, cwd,
  stdin, timeout, and output-limit digests;
- authorized preflight executable identity and observed exec-critical-point
  executable identity, including content SHA-256 and file identity;
- initial process identity; complete observed descendant identities and
  lifecycle; timeout/cancellation disposition; and proof of no surviving
  descendant when completion is claimed;
- observed filesystem accesses and effects, denied filesystem attempts,
  network attempts and permitted flows, and process-boundary attempts;
- exit, signal, timeout, cancellation, truncation, backend failure, and audit
  completeness dispositions;
- the canonical receipt body SHA-256 and a verifier-trusted authenticator or
  equivalent attestation whose signing secret or authority is unavailable to
  the caller and workload.

Verification must check the authenticator, canonical digest, one-time
challenge, freshness, expiry, anti-replay state, complete audit marker, and
exact identity/configuration/policy match. A missing, fabricated, replayed,
tampered, expired, incomplete, or mismatched receipt blocks the consuming
operation. In short: missing, fabricated, replayed, tampered, expired,
incomplete, or mismatched receipt evidence always blocks. Receipt verification
itself must fail closed if its trust root or anti-replay state is unavailable.

### Public hard-zero derivation

task-runner must never directly construct public hard-zero claims. A zero may
be emitted only by a receipt-to-result aggregator after it verifies receipts
for every relevant worker and validation execution against the current
execution identity and configuration.

The aggregator may derive provider_invocations,
provider_credential_value_accesses, target_repo_mutations,
remote_repository_operations, production_operations, cleanup_operations, and
rollback_operations as zero only when the matched receipt proves the
corresponding capability was absent or independently denied and no observed
effect belongs to that class. api_mode_enabled may be reported false only
from the same matched configuration and receipt evidence. Missing evidence
is BLOCK or unknown, never zero.

Receipt content must be joined to the TS-B01 execution-binding v2 candidate
and semantic evidence identities without altering v2. OS receipts prove the
execution/effect boundary; TS-B01 receipts continue to prove acceptance
semantics. Neither substitutes for the other.

## Network profiles and future subscription transport

deny_all is the mandatory default profile and the only profile whose behavior
is accepted by the non-live TS-B02 adversarial matrix.

A possible subscription_transport_only profile is a future, separately
authorized and versioned capability. This specification does not enable or
implement it. If later authorized, it must use independently enforced exact
destination and protocol mediation, record every flow, and distinguish
ChatGPT/Codex subscription transport from:

- large-model API/provider mode;
- arbitrary downstream or target-repository access;
- GitHub or other remote repository mutation;
- credential-value disclosure beyond a separately authorized opaque
  subscription session boundary;
- production, deployment, cleanup, rollback, or any other remote effect.

No network permission may be inferred from executable identity, a configured
Codex mode, subscription data-transfer intent, API key presence, or prior
acceptance. An unrecognized or unavailable profile fails closed.

## Strict package order

Each package starts only after a separately authorized fresh-state check and
uses the exact accepted merge of its predecessor as its base.

| Package | Sole durable owner or interface change | Required result | Explicit exclusions |
| --- | --- | --- | --- |
| TS-B02A | Add only isolated-execution and isolated-execution-api 1.0.0, including its registry/contract ownership surfaces and real-backend non-live tests. | Enforce the frozen request, backend, identity, descendant, network, and receipt contract and pass the adversarial matrix in Hosted CI. | No worker-adapter or task-runner change; no public entry; no live transport. |
| TS-B02B | Modify only worker-adapter and its versioned interface as needed to consume isolated-execution-api. | Require absolute sealed worker identity, SHA-256, exec-point recheck, exact configuration binding, and a verified worker execution receipt. | No task-runner change; no ordinary-host fallback; no TS-B01 change. |
| TS-B02C | Modify only task-runner and its owned command_runner boundary and versioned interface as needed. | Replace ordinary host validation subprocess, verify and bind OS-derived receipts, constrain all validation descendants, and derive public hard-zero fields only from matched receipts. | No worker-adapter implementation change; no direct zero construction; no public reacceptance. |
| TS-B02D | Revalidate only the TS-B02 affected dependency closure and record the correction conclusion. | Re-run real-backend non-live adversarial and consumer-closure evidence. If complete, record TS-B02 only as corrected_pending_reacceptance. | No runtime implementation, no real Codex or downstream operation, and no public-entry reacceptance. |
| Later separately authorized package | Public-entry reacceptance only. | Decide whether the corrected public entry can be accepted using the completed TS-B01 and TS-B02 evidence. | It is not part of TS-B02D and is not authorized by this specification. |

The affected closure for TS-B02D includes isolated-execution,
worker-adapter, task-runner, their declared public interfaces, managed import
edges, direct consumer boundaries, and unchanged CLI composition evidence.
Closure revalidation does not itself accept the subscription public entry.
Public-entry reacceptance remains a later separately authorized package.

## Hosted CI and adversarial acceptance matrix

Hosted CI must execute non-live tests on a real supported isolation backend.
Backend absence is a test failure and correction blocker. The forbidden
substitutions are skip, xfailed, mock-backend, and fake-receipt outcomes: no
case may be skipped, xfailed, replaced with a mock backend, or satisfied by a
fake or caller-constructed receipt.

No CI or supply-chain configuration change is authorized. The implementation
packages must use a real capability already supported by the Hosted runner; if
that capability is absent, the package stops for separate authorization
instead of editing a workflow or weakening the matrix.

At minimum the matrix must prove:

| Case | Required disposition |
| --- | --- |
| filesystem escape | Access/effect outside policy is denied, observed, receipted, and blocks acceptance. |
| network escape | All default-profile socket, DNS, loopback, IPC bridge, and inherited-handle attempts are denied and observed. |
| child-process escape | Child, grandchild, detached, and timeout-surviving process attempts remain bounded; no-survivor proof is required. |
| PATH substitution | A basename or changed PATH cannot select an executable and blocks before exec. |
| binary replacement | Symlink, rename, in-place replacement, interpreter swap, and exec-point identity mismatch block. |
| backend unavailable | Launch fails closed before workload execution. |
| receipt tamper/replay | Digest, authenticator, challenge, freshness, sequence, expiry, and identity mismatches block. |
| false-zero fabrication | Caller/workload attempts to construct zero-effect fields or a fake receipt cannot reach a public PASS result. |
| TOCTOU and configuration drift | Any executable, policy, backend, environment, cwd, source, or caller-configuration drift blocks. |
| audit incompleteness | Dropped events, auditor failure, overflow, lost descendant, or unverifiable completeness blocks. |

The tests remain non-live: no real Codex, ChatGPT Web automation, API/provider,
credential access, real downstream repository, runtime remote operation,
production, deployment, cleanup, or rollback occurs.

## Preserved boundaries

This specification and all later packages must preserve:

- TS-B01 execution-binding v2 and its semantic evidence unchanged;
- TS-H01, TS-H02, TS-H03, TS-M01, and TS-M02 without correction or acceptance
  upgrade;
- CI and supply-chain configuration unchanged by this specification;
- no new runtime lifecycle or status enum;
- no public-entry reacceptance in TS-B02A through TS-B02D;
- no actual subscription transport, Codex, ChatGPT Web, API/provider,
  credential, downstream, remote, production, deployment, cleanup, or
  rollback operation under this package; and
- authority_effect: none.

## This package's publication and stop

Only the report, task manifest, and change plan named by this specification
may be added. They are retained non-authority artifacts, not runtime defaults.
The exact branch is
agent/subscription-worker-ts-b02-isolated-execution-boundary-correction-spec-v1
and the exact commit message is
Specify TS-B02 isolated execution correction.

After one Draft PR, successful Hosted CI, exact base/head/path and
comment/review/thread no-drift checks, guarded Ready transition, and squash
merge with the original feature branch retained at the original PR head, work
stops. TS-B02A, runtime code, public-entry reacceptance, and every other
finding remain unstarted and unauthorized.
