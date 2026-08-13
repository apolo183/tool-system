# TS-B02A hosted isolation backend and trust enablement prerequisite specification v1

Status: SPECIFICATION_ONLY_NO_ENABLEMENT_OR_IMPLEMENTATION

Authority effect: none

Feasibility disposition: NO_VERIFIABLE_ARCHITECTURE

This prerequisite records a fresh-state blocker. It does not select architecture (a) or
(b), because the current evidence does not identify a governed natural owner,
canonical implementation repository, deployed trust domain, trust-root custody,
persistent verifier authority, exact enablement path closure, or cost authority for
either candidate. It does not enable a backend, implement isolated-execution, change
CI, or authorize any workload.

## 1. Frozen base, scope, and retained status

The canonical base was read through the GitHub App before this specification was
constructed:

- repository: apolo183/tool-system
- refs/heads/main commit:
  be9e9db8a48b6a18c006aa9f377296b506b30da7
- Git commit tree:
  e1cbd597ce6bcba376c9049414a16665fb869128
- expected parent:
  3a37fdb28140c73471fb96000a95e37f076792bf
- commit subject:
  Specify TS-B02 isolated execution correction (#224)

Only this report and its task manifest and change plan are in scope. The current
REPO_MANIFEST retained non-authority globs already classify all three paths; no
fourth path is required. Any contrary validation result is a hard stop before write.

The following facts remain unchanged:

- TS-B01 execution-binding v2 and its semantic evidence remain
  corrected_pending_reacceptance, not reaccepted.
- The public entry remains not reaccepted.
- Real-repository execution remains blocked by TS-B02.
- worker-adapter, task-runner, agent-worker-runtime, module registry, module
  contracts, project state, existing tests, CI, supply chain, policy, blueprint,
  README, and lifecycle/status enums are unchanged.
- TS-H01, TS-H02, TS-H03, TS-M01, TS-M02, and TS-L01 are not corrected.
- This package is not a durable milestone and adds no module or versioned interface.

## 2. Complete fresh-state evidence ledger

All repository paths in this section were read at the frozen commit and tree above.

### 2.1 Governing and state inputs

| Path | Blob | Finding consumed |
| --- | --- | --- |
| AGENTS.md | d6e09fa4fc51370a212bec4cd7a087f9b99a2437 | Direct governance consumption, bounded authority, natural ownership, and one durable module/interface per milestone. |
| REPO_MANIFEST.md | efcde3b3ac5afb4fa34407a46eca9e26a42b9058 | The three authorized locations are retained non-authority evidence paths. |
| blueprint/tool_system_v0.yaml | c86640ec5bf3b89181ee62967d76b951e29bc3fe | Product objective, isolation non-claim, and milestone-module invariant. |
| docs/tool_system_global_development_principles_v1.md | df8f7d1c3c4015660fe96017d59d93c319ea3422 | Fail-closed evidence, bounded closure, natural ownership, and dependency revalidation. |
| docs/tool_system_project_state_v1.yaml | 8e64f40a14a34df3b3e98cee2be8df9bf3c3fd21 | TS-B01 remains pending reacceptance, public acceptance is false, and TS-B02 blocks real-repository execution. |
| docs/reports/independent_audit_acceptance_reopen_v1.md | af5af782535996ecb7c8df6b12560d7fa38e8e32 | TS-B02 is a confirmed blocker and ordinary host subprocess evidence is insufficient. |
| docs/reports/subscription_worker_ts_b02_isolated_execution_boundary_correction_specification_v1.md | 4eb321fd8950e36f9243da16805ef7a9c8747e06 | Frozen TS-B02 ownership, isolation, receipt, adversarial, and A/B/C/D ordering contract. |
| config/module_registry_v1.yaml | 12c0c0f6542838b5ba8b4ee04a5659314d9669ae | Twenty-six current modules, no isolated-execution provider, and current natural-owner edges. |
| docs/tool_system_module_registry_contract_v1.md | a41eddf2b9033fc8322b06ab00b2dfa8035bd78b | Registry mapping and dependency-direction contract. |
| docs/reports/p14mr_milestone_module_invariant.md | 54847260d39034325bec44101f383520f2cb86a9 | One durable module or versioned public interface per milestone. |
| docs/modules/agent-worker-runtime-contract-v1.md | 8dbff373f51656fe9d0a44aa5b7bdf12b29e374 | Fixture-only application guard, not a hostile-process sandbox. |
| docs/modules/worker-adapter-contract-v1.md | 80444e59be27f4d11ee12d02609bc8845374ac55 | Current worker selection lacks a sealed executable identity and OS observation receipt. |
| docs/modules/task-runner-contract-v1.md | 33ab5e5626a227412e10a49f9b47371a7f58fe03 | Validation and public aggregation are task-runner responsibilities. |
| .github/workflows/tool-system-ci.yml | b91fb92f1880bb97d42f63209137ae8b17a7a88e | Standard ubuntu-latest, contents read, Python 3.11, pytest, and four current validators only. |
| pyproject.toml | 85fffd525536882ec0b13a3eb3863f5bbadd0da7 | No isolation client, receipt cryptography, attestation, or external-service dependency. |

The current finance-governance main was also read at commit
518c77dd4203d739380f774fdc67a18f38237dfd. Its global principles blob is
e7642315ed52e53532cfd28e770c970441ced441. Its repository registry blob is
20c9ec3cbece25f2e60129064ace47a4149a0a54 and registers only the six current
repositories; it registers no hardened-runner, isolation-service, audit-service, or
infrastructure natural owner.

### 2.2 Current implementation and tests

The complete current implementations related to process execution, agent worker,
worker adapter, task runner, registries, manifests, and gates were read at the frozen
commit, including:

- src/tool_system/agent_worker/__init__.py
- src/tool_system/agent_worker/interface.py
- src/tool_system/agent_worker/process_runtime.py
- src/tool_system/architecture/module_registry.py
- src/tool_system/architecture/repo_manifest.py
- src/tool_system/gate/alignment.py
- src/tool_system/gate/change_plan.py
- src/tool_system/gate/command_runner.py
- src/tool_system/gate/test_gate.py
- src/tool_system/manifest/task_manifest.py
- src/tool_system/process_authority/contract.py
- src/tool_system/runner/task_runner.py
- src/tool_system/worker_adapter/contract.py

The complete corresponding current test set was read at the same commit, including
the task/change-plan policy tests, command-runner tests, agent-worker interface and
preflight/execution/adversarial tests, worker-adapter contract/orchestration tests,
task-runner tests, module-contract/import-graph/registry tests,
milestone-module-invariant tests, phase-alignment tests, and repository-manifest
tests.

Critical implementation observations remain:

- command_runner invokes subprocess.run after shlex.split with shell false on the
  ordinary host and does not establish OS filesystem, process-tree, or network
  isolation.
- process_runtime uses a Python audit hook and application checks for fixtures; it
  does not create a general hostile-process security boundary.
- worker_adapter accepts a command name and a self-reported Codex sandbox mode; it
  does not seal absolute binary/interpreter identity at exec or return independent
  OS observations.
- task_runner constructs public zero-effect fields from application data; it does
  not verify an independent effect receipt.

### 2.3 Official platform material

The following current official material was read on 2026-08-13:

1. GitHub, GitHub-hosted runners reference:
   https://docs.github.com/en/actions/reference/runners/github-hosted-runners
   Linux and macOS hosted VMs run with passwordless sudo; standard Linux jobs use
   newly provisioned hosted VMs.

2. GitHub, OpenID Connect reference:
   https://docs.github.com/en/actions/reference/security/oidc
   A job must grant id-token write to request a GitHub OIDC token; the current
   workflow grants only contents read.

3. GitHub, actions/runner-images:
   https://github.com/actions/runner-images
   ubuntu-latest is a mutable label for the current GA Ubuntu image and runner
   images are updated regularly.

4. Docker, Linux post-installation:
   https://docs.docker.com/engine/install/linux-postinstall
   The Docker daemon normally runs as root and membership in the docker group
   grants root-level privileges.

5. Docker, none network driver:
   https://docs.docker.com/engine/network/drivers/none/
   network none still creates a loopback device; component presence is not proof
   of the frozen network and receipt contract.

6. Firecracker, design and production host setup:
   https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md
   https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md
   Firecracker supplies microVM barriers, but production security depends on a
   correctly configured host; the operator, jailer inputs, host filtering, and
   lifecycle controls remain trusted responsibilities.

7. AWS, Nitro Enclaves security and KMS conditions:
   https://docs.aws.amazon.com/enclaves/latest/user/security.html
   https://docs.aws.amazon.com/kms/latest/developerguide/conditions-nitro-enclave.html
   Nitro Enclaves provide CPU/memory isolation, no external network or persistent
   storage, and attestation-gated KMS operations, but these component properties do
   not identify or instantiate this project's supervisor, auditor, signer, or
   durable replay authority.

8. AWS, DynamoDB transactions:
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html
   Transactional conditional writes and client-token idempotency are building
   blocks; no table, IAM separation, retention policy, or verifier state exists for
   this project.

9. AWS, Nitro Enclaves pricing:
   https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html#pricing
   Enclaves have no separate charge, while EC2 and all other services are billed.
   No project account, budget, cost ceiling, or payer owner is authorized here.

These official sources prove individual capabilities and prerequisites. They do not
prove a complete project-owned isolation backend or an authenticated OS-effect
receipt system. Treating them as integrated acceptance evidence would fill material
gaps by assumption.

## 3. Why the unchanged standard ubuntu-latest workflow is infeasible

The current job caller can execute arbitrary repository steps with passwordless
sudo. It can therefore replace local binaries, alter namespaces, daemon state,
audit configuration, files, clocks, keys, logs, and any local replay database. If it
uses the root Docker daemon, the caller retains root-equivalent control of the
backend. network none retains loopback and supplies no independent receipt signer.

The current job has no caller-inaccessible supervisor or auditor, no TPM/HSM/KMS
key custody, no attested code identity, no durable independent challenge/sequence
store, no atomic receipt-consumption authority, and no configured external
execution service. The job is ephemeral, and the workflow grants neither OIDC
id-token permission nor any bound service invocation. This is an inference from
the exact current workflow plus the official runner and OIDC contracts.

Therefore all of these remain unproved on the unchanged runner:

| Required property | Current evidence | Result |
| --- | --- | --- |
| Caller cannot control the enforcement backend | caller has passwordless sudo and can control local privileged state | BLOCK |
| OS filesystem boundary | no independent mount/microVM policy or observation | BLOCK |
| Complete process-tree and survivor boundary | ordinary host subprocess; no independently observed execution unit | BLOCK |
| Default-deny network | no independent egress boundary or complete audit | BLOCK |
| Workload-before-PID capability preflight | no backend capability protocol | BLOCK |
| Exec-critical identity seal | no absolute file/interpreter identity sealed at exec | BLOCK |
| Independent effect receipt signer | no caller-inaccessible key or signer | BLOCK |
| Durable anti-replay and atomic consume | no independent persistent verifier state | BLOCK |
| Audit completeness | no independently authenticated complete event stream | BLOCK |
| Real Hosted adversarial proof | current CI runs ordinary pytest only | BLOCK |

shell false, Python audit hooks, Codex self-reported read-only sandbox mode, a mock
backend, a fake receipt, skip, or xfail cannot change any BLOCK result.

## 4. Single architecture disposition

    feasibility_disposition: NO_VERIFIABLE_ARCHITECTURE
    selected_architecture: none
    ts_b02a_execution_authorized: false

Candidate (a), a hardened runner with caller denied sudo/daemon access and an
independent root supervisor, is not selected. No such runner label, image,
provisioning owner, supervisor build, TPM/HSM/KMS trust root, persistent verifier
state, permission boundary, cost owner, or exact implementation repository/path
set exists in the fresh state.

Candidate (b), an external independent execution/audit service, is not selected.
Nitro Enclaves, Firecracker, KMS, and transactional storage are plausible building
blocks, but there is no registered service natural owner, canonical service
repository and base, cloud tenancy, service protocol, audited supervisor image,
signer role, verifier state, IAM/SCP separation, cost authority, deployment path,
or rollback owner. Selecting it would invent the missing integrated system.

The two candidates are evaluated and rejected; they are not retained as alternatives
for an implementer to choose. A later user authorization must supply one candidate
and all missing identities before any new fresh-state planning.

## 5. Frozen trust-domain requirements

These requirements define the minimum acceptance contract for a future separately
authorized architecture. They do not instantiate a trust domain now.

| Domain | Permitted control | Forbidden access or control |
| --- | --- | --- |
| caller | submit one content-addressed request and receive a receipt | sudo/daemon/backend policy, signer key, raw audit state, verifier state, sequence mutation, receipt consumption |
| workload | read only its sealed input and declared workspace; write only declared scratch/output | host filesystem, backend control socket, auditor channel, signer material, verifier state, external network |
| supervisor | establish and destroy the execution unit and enforce the sealed policy | caller-controlled code/config after capability seal; public-result construction |
| auditor | observe independently derived backend, exec, filesystem, process, network, and teardown facts | workload/caller mutation, unauthenticated event substitution, silent event loss |
| verifier | validate chain, policy/identity match, freshness, sequence, revocation, and atomically consume one challenge | caller/workload state writes, accepting an already consumed or incomplete receipt |
| trust root | attest authorized supervisor/auditor identity and protect signing authority | key export to caller, workload, job filesystem, logs, environment, artifacts, or service operator without separately governed break-glass authority |

The caller, workload, supervisor, auditor, verifier, and trust root must not collapse
into the same credential or mutable process domain. Capability or separation
incompleteness must fail before any workload PID exists.

## 6. OS enforcement and exec-critical-point contract

A future backend must independently enforce all of the following:

### 6.1 Filesystem

- expose only a content-addressed read-only base, sealed input, declared workspace,
  bounded scratch, and explicit output;
- expose no host path, socket, device, credential, workspace parent, or unrelated
  repository;
- reject symlink, hardlink, mount, proc-fd, device, namespace, and traversal escape;
- make teardown and write observations complete and attributable to one execution
  identity.

### 6.2 Processes

- place the initial process and every child, grandchild, reparented, detached,
  double-forked, daemonized, and timeout-surviving descendant in one independently
  enforced execution unit;
- prevent escape to another PID/user/cgroup/VM boundary;
- on timeout or cancellation, kill and observe the entire unit;
- issue no success or zero-effect receipt until the auditor proves no survivor.

### 6.3 Network

- deny external and local IP networking by default, including IPv4, IPv6, packet,
  netlink, loopback, inherited sockets, namespace changes, metadata endpoints, and
  covert reuse of caller-owned proxies;
- separately model a future subscription-only transport, which remains absent and
  unauthorized here;
- never interpret that future transport as API/provider, downstream, remote
  repository, production, deployment, cleanup, or rollback authority.

### 6.4 Exec seal

Before workload creation, the supervisor must resolve and seal:

- an absolute executable path;
- a non-symlink regular executable opened without path traversal;
- content SHA-256;
- stat and file identity including device, inode, mode, size, ctime and mtime or an
  equivalently stronger immutable object identity;
- every interpreter, dynamic loader, library/runtime image, and script identity;
- policy, backend version/image, source tree, environment, working directory,
  resource limits, and normalized argv.

At the exec critical point it must execute the already verified object by descriptor
or an equivalently race-free primitive and independently observe the executed
identity. PATH replacement, symlink changes, binary or interpreter replacement,
TOCTOU, environment, policy, backend, source, or configuration drift must block.

### 6.5 Audit completeness

The auditor must authenticate its event source and prove start/end sequence
continuity for backend capability, policy load, exec identity, filesystem exposure
and writes, process lifecycle, network policy and attempts, timeout/cancellation,
teardown, and signer handoff. Lost events, counter gaps, buffer overflow, auditor
restart, clock uncertainty, unsupported event class, or incomplete teardown block
before receipt issuance.

## 7. Receipt trust and consumption model

A future receipt must be OS- or independently-auditor-derived, canonicalized, and
content addressed. It must bind at least:

- receipt schema/version and issuer key id;
- request id, unpredictable verifier challenge, monotonic sequence, issued-at,
  not-before, expires-at, and one-use consumption key;
- repository, source commit/tree, candidate tree, task/plan identity;
- caller OIDC or equivalent identity and workflow/run/job identity;
- supervisor/auditor/backend build and attestation identities;
- normalized policy and configuration digests;
- executable, interpreter/loader, argv, environment and working-directory digests;
- execution-unit identity and complete descendant lifecycle;
- filesystem, process, network, timeout, cancellation and audit-completeness facts;
- terminal result and teardown/no-survivor proof;
- hash of every referenced evidence object.

The signer key must be non-exportable in TPM/HSM/KMS or encrypted for release only
to an attested supervisor/auditor identity. Caller and workload may not request
arbitrary signing, decrypt/export the key, change attestation policy, or read signing
material. Rotation must use an overlap window with explicit old/new key ids.
Revocation must be independently published and checked at verification time.
Receipts under revoked, unknown, expired, debug, or mismatched attestation chains
block.

The verifier must create the unpredictable challenge and next sequence in durable
state before execution. Receipt verification and challenge consumption must be one
conditional atomic transaction: require unconsumed challenge, exact request and
identity match, sequence monotonicity, valid time window and non-revoked key, then
mark consumed and persist the receipt hash. A failed transaction is a block. A
receipt is never reusable across request, commit/tree, workflow, configuration,
backend, key, or time window.

Missing, fabricated, replayed, tampered, stale, expired, incomplete, or
identity-mismatched receipts block. Public hard-zero fields can only be a verified
projection of a consumed receipt matching the current execution and configuration.
Application code cannot construct or default those values.

## 8. Required enablement surfaces and exact future package ledger

No implementation package is plannable at this fresh state. The exact empty path
lists below are not claims that no write is needed. They mean that no canonical
owner/base/path closure exists and authorized writes are zero.

| Package | Disposition | Repository/base/branch/commit | Exact paths | Authorized writes |
| --- | --- | --- | --- | --- |
| BACKEND_TRUST_ENABLEMENT | BLOCKED_UNPLANNABLE_NO_OWNER | null | [] | 0 |
| HOSTED_PROOF_OF_CAPABILITY | BLOCKED_UNPLANNABLE_NO_OWNER | null | [] | 0 |
| TOOL_SYSTEM_CI_CONSUMER_ENABLEMENT | BLOCKED_UNPLANNABLE_NO_OWNER | null | [] | 0 |

Before any one of these can become a write package, a later user authorization must
freeze all of the following:

- exactly one architecture, natural owner, canonical repository/remote, exact base
  commit/tree, branch, commit message, and exact path list;
- runner image/labels or external service endpoint and control-plane owner;
- supervisor/auditor/verifier implementations and their independent operator
  boundaries;
- TPM/HSM/KMS key, attestation policy, rotation/revocation owner, and break-glass
  procedure;
- durable challenge/sequence/consumption store and its rollback/delete denial;
- workflow permissions, OIDC audience/subject and exact least-privilege role;
- pinned supply-chain identities and dependency lock/update owner;
- configuration and trust-root distribution paths;
- cost account, payer, hard ceiling, per-run budget, alarm, and stop owner;
- deployment, cleanup, rollback, retention, incident, and evidence owners.

The current finance-governance registry has no owner for these surfaces, and the
tool-system tree has no infra or service implementation root. This specification
therefore forbids inventing an isolation-service repository, adding tool-system
infra paths, modifying the current workflow or pyproject, provisioning cloud
resources, or assigning credentials. If future analysis requires any such path, it
must first be named and separately authorized.

### 8.1 Conditional TS-B02A closure only

TS-B02A may be reconsidered only after all three blocked prerequisite packages have
become separately authorized, merged, and accepted with real capability evidence,
and a new fresh-state analysis proves that no client, cryptography dependency,
trust configuration, workflow, fixture, CLI, or additional path is needed.

At the current base, the conditional twenty-path TS-B02A closure is:

Modify exactly nine:

1. README.md
2. REPO_MANIFEST.md
3. config/module_registry_v1.yaml
4. docs/tool_system_module_registry_contract_v1.md
5. docs/tool_system_project_state_v1.yaml
6. tests/test_module_contracts.py
7. tests/test_module_registry.py
8. tests/test_repo_manifest.py
9. tests/test_phase_alignment.py

Add exactly eleven:

1. docs/modules/isolated-execution-contract-v1.md
2. docs/reports/subscription_worker_ts_b02a_isolated_execution_implementation_v1.md
3. examples/task_manifests/tool_system_subscription_worker_ts_b02a_isolated_execution_v1.yaml
4. examples/change_plans/tool_system_subscription_worker_ts_b02a_isolated_execution_v1.yaml
5. src/tool_system/isolated_execution/__init__.py
6. src/tool_system/isolated_execution/contract.py
7. src/tool_system/isolated_execution/linux_backend.py
8. src/tool_system/isolated_execution/receipt.py
9. tests/test_isolated_execution.py
10. tests/test_isolated_execution_receipt.py
11. tests/test_isolated_execution_adversarial.py

Conditional branch:
agent/subscription-worker-ts-b02a-isolated-execution-v1

Conditional commit:
Implement TS-B02A isolated execution module

This is not an implementation authorization. If the selected backend makes
linux_backend.py inaccurate, or requires a client, dependency, trust config,
workflow, pyproject, fixture, CLI, or twenty-first path, TS-B02A must stop before
write and request a newly derived path authorization.

## 9. Required real Hosted proof-of-capability matrix

A later proof package must run from a real GitHub-hosted job against the actually
enabled independent backend. Backend absence or any unverifiable result is FAIL,
not skip or xfail.

| Case | Required attack | Required accepting observation |
| --- | --- | --- |
| filesystem escape | traversal, symlink/hardlink, proc-fd, mount/device and host-path probes | every outside access denied; exposure/write evidence complete and receipt-bound |
| network escape | IPv4/IPv6/packet/netlink/loopback, DNS, metadata, inherited socket and proxy probes | all denied by independent boundary with complete attempt evidence |
| child-process escape | fork, double-fork, setsid, reparent, namespace/cgroup move and timeout survivor | one execution unit, complete lineage, forced teardown, zero survivor |
| PATH substitution | replace PATH entry before and during launch | sealed absolute identity executes or request blocks |
| binary replacement | replace executable/interpreter/loader by symlink, rename, in-place write or inode swap | digest/stat/descriptor and exec observation match or block |
| backend unavailable | endpoint, supervisor, auditor, signer, verifier state or capability disabled | failure before workload PID |
| receipt tamper/replay | alter fields/signature, reuse challenge/sequence, stale key/time, cross-run receipt | signature/identity/freshness check or atomic consumption blocks |
| false-zero fabrication | application submits zero fields without matching receipt, or edits projection | public result construction blocks |
| TOCTOU/config drift | mutate source, policy, environment, limits, image, endpoint or trust config after seal | exec is prevented or drift receipt is non-accepting |
| audit incompleteness | drop/reorder events, overflow buffer, restart auditor, omit teardown or event class | completeness gate blocks receipt and result |

Hosted acceptance also requires:

- caller cannot use sudo, daemon control, signer, verifier state, or service-admin
  authority against the backend;
- workload cannot reach supervisor/auditor control, key custody, verifier state, or
  any external network;
- exact backend/supervisor/auditor/verifier/key/config/source identities match;
- audit sequence has no gap and all descendants are gone;
- focused and full pytest plus all current governance validators pass;
- skip count, xfail count, mock backend count, and fake receipt count are all zero.

## 10. Dependency and publication order

The only permitted order is:

1. a new user authorization supplies one architecture and the missing natural owner,
   repository/base, trust, permission, cost, and path identities;
2. a separately authorized BACKEND_TRUST_ENABLEMENT package;
3. a separately authorized HOSTED_PROOF_OF_CAPABILITY package;
4. a separately authorized TOOL_SYSTEM_CI_CONSUMER_ENABLEMENT package;
5. a fresh-state TS-B02A implementation authorization with one isolated-execution
   durable module/interface;
6. separately authorized TS-B02B worker-adapter only;
7. separately authorized TS-B02C task-runner only;
8. separately authorized TS-B02D affected-closure revalidation only;
9. a later, separately authorized public-entry reacceptance package.

No step can be combined with its successor. One milestone changes at most one
durable module or versioned public interface. TS-B02D can conclude only
corrected_pending_reacceptance; it cannot reaccept the public entry.

## 11. Preserved operational boundary and stop

This package performs no real Codex or ChatGPT Web automation, API/provider call,
credential access, subscription transport, real downstream access, runtime remote
repository action, infrastructure/service operation, production action, deployment,
cleanup, or rollback. It modifies no runner, workflow permission, CI, supply chain,
external service, cloud resource, trust root, project status, module, contract,
runtime source, or existing test.

Publication is limited to one exact three-new-path commit on the authorized branch,
first as a Draft PR. Ready and squash merge are permitted only when Hosted CI is
successful and the canonical base, exact head, one-commit count, exact three paths,
comments, reviews, and review threads remain unchanged. The original feature branch
must be retained at the original PR head, restoring the same name after automatic
deletion if necessary.

After guarded merge, stop. Do not start backend enablement, proof, CI consumer
enablement, TS-B02A, TS-B02B, TS-B02C, TS-B02D, or public-entry reacceptance.
