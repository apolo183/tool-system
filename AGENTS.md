# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-12 UTC+09:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

The permanent product objective is bounded blueprint-driven autonomous software development. An approved blueprint must ultimately be convertible into durable, versioned, replaceable single-responsibility modules, milestone-to-module change bindings, an executable task DAG, controlled AI-assisted code changes, test/repair/review evidence, bounded local Git commits, and an acceptance record without silent scope or authority expansion.

## 2. Mandatory first step

Before material tool-system engineering work, read:

```text
docs/tool_system_global_development_principles_v1.md
```

These repository-local principles govern only tool-system. If a later authorized cutover creates a registered immutable finance-governance reference, the governance commit pinned by that reference is upstream and local rules may add constraints but may not override it. This contract does not create that reference or complete cutover.

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

Existing reports, task manifests, change plans, and `examples/active_gates.yaml` remain legacy machine inputs pending a separately authorized caller and reference migration audit. Their presence is not a claim of finance-governance process-file compliance, and unread objects must not be deleted or reclassified in this reconciliation.

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

## 6. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

Material engineering work follows the evidence hierarchy, documentation-first loop, blueprint alignment invariant, drift gate, authorization gate, side-effect preflight, file disposition, cleanup, rollback, and claims rules in `docs/tool_system_global_development_principles_v1.md`.

## 7. Side-effect tool discipline

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

## 8. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, milestone acceptance, cleanup execution, first real downstream target-repository mutation, target PR lifecycle transitions, and production deployment.

## 9. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

## 10. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 11. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 12. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 13. Current phase state

Current phase: P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT.

Status: `active`.

P10, P11, P12, and P13 are accepted and closed at their recorded scopes. P14B Provider-Neutral AI Worker Contract is accepted and closed. P14 remains active while the accepted P14MR evidence is retained and its durable local module rules are owned by `blueprint/tool_system_v0.yaml` and `docs/tool_system_global_development_principles_v1.md`. Live model/provider execution, project benchmarks, and target mutations are not authorized. P15-P16 remain roadmap-only.

Allowed now:

- local durable-module authority semantics owned by the blueprint and local principles; `docs/reports/p14mr_milestone_module_invariant.md` is existing acceptance evidence only;
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
