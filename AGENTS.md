# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-13 UTC+09:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

The permanent product objective is bounded blueprint-driven autonomous software development. An approved blueprint must ultimately be convertible into durable, versioned, replaceable single-responsibility modules, milestone-to-module change bindings, advisory task-complexity/risk/critical-path profiles, deterministic authorized provider-model route decisions, an executable task DAG, controlled AI-assisted code changes, test/repair/review evidence, bounded local Git commits, provider/model economic evidence, and an acceptance record without silent scope or authority expansion.

## 2. Mandatory first step

Before material tool-system engineering work, read:

```text
docs/tool_system_global_development_principles_v1.md
REPO_MANIFEST.md
```

These repository-local principles currently govern only tool-system. `config/governance_reference_v1.yaml` pins candidate finance-governance commit `f039a5355e1e5ea3fa865b827947b0c1153a2745` as a five-field immutable pointer. The reference does not activate group governance, report cutover state, or replace current tool-system-local authority before the required central `repo-check` and cutover confirmation. After activation, local rules may add constraints but may not override the pinned group governance. No copied finance-governance constitution is local authority.

Before provider/model selection, qualification, billing, credential-reference, or development-economics work, also read:

```text
docs/model_provider_portfolio_and_economics_contract_v1.md
```

## 3. Documentation-first execution loop

Agents must not rely on long conversation context as execution authority. Every stage follows the documentation-first loop:

1. read the active blueprint, global principles, milestone document, task manifest, and change plan;
2. design or update the narrow current-stage document;
3. verify the current-stage document against its immediate parent, the active blueprint or requirement source, and global principles;
4. execute only the documented stage scope;
5. create or update evidence showing what actually happened;
6. compare execution evidence against the stage document and change plan;
7. compare the stage document against both its immediate parent and the active blueprint or requirement source before designing the next stage.

A stage should be short, have one natural objective, one branch, one change plan, one evidence record, and a clear stop condition. If drift is found, the next action is documentation or process correction, not feature expansion.

The caller and reference audit is complete. `config/process_authority_v1.yaml` requires one explicitly supplied manifest/change-plan pair for current execution, with exact pair binding before commands. Repository-wide implicit task authority is disabled. `config/replay_snapshot_v1.yaml` content-addresses the retained legacy pair set; `examples/active_gates.yaml` is explicit, non-executing replay input only. Existing reports, manifests, plans, and the legacy index remain present and are not claimed finance-governance process-file compliant. Do not delete or reclassify them without the separate cleanup authorization.

## 4. Blueprint alignment invariant

Every major milestone, sub-milestone, task manifest, change plan, evidence record, and acceptance record must prove:

- parent alignment: it follows its immediate parent document;
- global alignment: it still follows the active blueprint or requirement source.

Parent-only alignment is not enough. Small local deviations can accumulate into material blueprint drift. Scripts, CLIs, agents, and repository-control tools execute documents; they do not define scope by themselves.

For P14 and later work, global alignment means explicit alignment to `blueprint/tool_system_v0.yaml:product_objective`, not merely to the current milestone entry. Missing direct-parent or product-objective alignment blocks execution.

## 5. Durable module and milestone invariant

Within tool-system, a module is a persistent, replaceable functional boundary with one responsibility and a versioned public interface. A milestone is a controlled unit of change and acceptance; it does not become a persistent module merely because it existed. As a rule, one milestone adds, modifies, or replaces one durable module or one versioned public interface.

Interface-compatible replacement must leave unaffected modules unchanged; the replacement, its public upstream and downstream boundaries, and the affected downstream dependency closure are revalidated rather than reimplemented by default. Failure, evidence loss, or contract drift isolates the affected module and stops its outputs, pauses dependent consumption pending current revalidation, and preserves unrelated modules and evidence. Hidden dependencies, cross-module internal-state access, parallel active mainlines, and undocumented whole-project rewrites are prohibited.

This rule does not define new machine lifecycle or status values. Isolation, paused consumption, replacement, and revalidation are ordinary rule language unless a separately authorized applicable schema registers corresponding values.

tool-system may offer tools and recommendations to a downstream repository under that repository's own authority. A tool-system local rule cannot change another repository's owner, authority, status, responsibility, or write authorization.

## 6. Provider portfolio and economics rule

Provider integrations are independently replaceable adapters behind the versioned `AIWorkerProvider` interface. Candidate adapters are not enabled providers. Every live provider call requires an authorized exact provider/model, supported authorization surface, credential reference, network route, data policy, token/time/cost envelope, retry/cancellation controls, and redacted audit contract. ChatGPT/Codex subscription access must not be treated as API credit, automated through browser-session scraping, or used to extract authentication material.

The task-complexity assessor is advisory. A deterministic policy engine owns the final route decision from the exact task profile, authorization envelope, and provider/model catalog snapshot. Complexity, risk, data sensitivity, capability floors, verification burden, and critical-path impact remain separate. Safety, quality, data, authorization, and precondition controls cannot be weakened for cost or speed.

Availability failures may use bounded failover only among already eligible authorized routes. Quality failures may use bounded same-route repair and evidence-backed escalation. Policy, data, hard-budget, authorization, or stale-precondition failures block and must not be bypassed by switching providers. All attempts, failovers, escalations, and stop decisions require redacted reproducible evidence.

Model qualification is per task class and uses exact version IDs plus dated price, policy, availability, reliability, and benchmark evidence. Discovery does not activate a model. A new version does not replace an accepted route until qualification and atomic publication pass. Repeated task-class failures cause scoped demotion; unrelated eligible classes need not be discarded.

Optimize expected total economic cost per accepted module, with critical-path time as the largest configurable soft cost driver. Include provider usage, avoidable future renewals, critical-path personnel/rent/operating burn, local compute/electricity, verification, retry, rework, recovery, rollback, and opportunity cost without double counting. Never commit private salaries, rent, rates, billing details, renewal dates, revenue assumptions, credentials, or secret values to the public repository.

This rule is a product and roadmap contract. It grants no live-provider execution, credential, P15/P16 phase entry, target-repository mutation, cleanup, or production authority.

## 7. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

Material engineering work follows the evidence hierarchy, documentation-first loop, blueprint alignment invariant, drift gate, authorization gate, side-effect preflight, file disposition, cleanup, rollback, and claims rules in `docs/tool_system_global_development_principles_v1.md`.

## 8. Side-effect tool discipline

Before any tool call that creates, updates, deletes, merges, labels, or otherwise mutates GitHub state, the agent must internally verify:

- intent;
- target repository;
- target branch or PR;
- expected side effect;
- duplicate check;
- parent alignment;
- global blueprint or requirement alignment;
- stop condition;
- whether the tool matches the documented action.

If the intended action is file update but the selected tool is branch creation, merge, deletion, or cleanup, work stops before the tool call. A task may create at most one branch unless a later active document explicitly authorizes a replacement branch and records disposition of the prior branch.

## 9. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, milestone acceptance, cleanup execution, first real downstream target-repository mutation, target PR lifecycle transitions, and production deployment.

## 10. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

## 11. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 12. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 13. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 14. Current phase state

Current phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT.

Status: `active`.

P10, P11, P12, and P13 are accepted and closed at their recorded scopes. P14B Provider-Neutral AI Worker Contract is accepted and closed. P14 remains active while the accepted P14MR evidence is retained, its durable local module rules are owned by `blueprint/tool_system_v0.yaml` and `docs/tool_system_global_development_principles_v1.md`, and its current module inventory is registered in `config/module_registry_v1.yaml`. The registry enforces declared structure, natural owners, dependency versions, reciprocal edges, and DAG validity; it does not claim source-import enforcement, runtime isolation, compatibility proof, or automatic replacement. Live model/provider execution, project benchmarks, and target mutations are not authorized. P15-P16 remain roadmap-only.

Allowed now:

- local durable-module authority semantics owned by the blueprint and local principles; `docs/reports/p14mr_milestone_module_invariant.md` is existing acceptance evidence only;
- local validation of `config/module_registry_v1.yaml` within its registered structural and no-target-mutation authority envelope;
- explicit current-task pair validation through `config/process_authority_v1.yaml`; legacy active-gate input is replay-only and cannot authorize commands;
- local `REPO_MANIFEST.md` validation proving every tracked path is classified exactly once as formal or retained non-authority, without claiming process-file compliance or cleanup authority;
- read-only verification of the accepted P14A and P14B contracts and evidence;
- read-only verification of the accepted P13 security and reliability evidence;
- read-only verification of accepted P12 durable-orchestrator state and evidence;
- read-only verification of the accepted P11 runtime;
- read-only verification of accepted target state;
- preparation of separately approvable downstream target lifecycle packets.

Not allowed now:

- target PR metadata changes, ready transition, or merge without a named merge packet and separate approval;
- target-repository main-branch mutation outside the approved merge flow;
- finance-us P1B target implementation without a named, action-scoped target execution approval;
- treating a P1B implementation approval as ready or merge approval;
- further P14B source expansion under the accepted and closed milestone scope;
- P14C or later P14 source implementation before a named authorization;
- any live model/provider call before a named provider, model, credential, network, cost, and execution packet is authorized;
- P15 or later phase entry or implementation before a named authorization;
- further P13 runtime, orchestrator, or evidence expansion under the closed milestone;
- further P12 runtime expansion under the closed milestone;
- P12 fixtures that call a real external side effect, remote provider, or target repository;
- P13 fixtures that call a real external side effect, remote provider, or target repository;
- any P11 worker execution before minimum safety controls pass;
- worker execution against finance-us or any other remote target repository;
- broad or unspecified downstream repository mutation;
- production deployment;
- business-domain implementation by tool-system;
- real external worker calls without an execution packet and approval;
- cleanup execution without a cleanup gate;
- branch deletion without a cleanup gate;
- rollback execution without a rollback gate;
- Codex replacement claims.
