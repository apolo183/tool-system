# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-12 UTC+09:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

The permanent product objective is bounded blueprint-driven autonomous software development. An approved blueprint must ultimately be convertible into versioned replaceable milestone modules, an executable task DAG, controlled AI-assisted code changes, test/repair/review evidence, bounded local Git commits, and an acceptance record without silent scope or authority expansion.

## 2. Mandatory first step

Before material tool-system engineering work, read:

```text
docs/tool_system_global_development_principles_v1.md
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

## 4. Blueprint alignment invariant

Every major milestone, sub-milestone, task manifest, change plan, evidence record, and acceptance record must prove:

- parent alignment: it follows its immediate parent document;
- global alignment: it still follows the active blueprint or requirement source.

Parent-only alignment is not enough. Small local deviations can accumulate into material blueprint drift. Scripts, CLIs, agents, and repository-control tools execute documents; they do not define scope by themselves.

For P14 and later work, global alignment means explicit alignment to `blueprint/tool_system_v0.yaml:product_objective`, not merely to the current milestone entry. Missing direct-parent or product-objective alignment blocks execution.

## 5. Milestone module invariant

Every project controlled, generated, or adopted by tool-system is a DAG of versioned replaceable capability modules. Every major milestone and sub-milestone is one module with a public input/output interface, explicit dependency versions, natural owners, content hashes, acceptance evidence, invalidation conditions, rollback, cleanup, and replacement disposition.

Interface-compatible replacement must leave unaffected modules unchanged; direct dependents are revalidated rather than reimplemented by default. Contract or blueprint drift invalidates and isolates the module, blocks its dependents, preserves unrelated modules, and requires an accepted replacement before atomic reactivation. Hidden dependencies, cross-module internal-state access, parallel active mainlines, and undocumented whole-project rewrites are prohibited.

Every controlled project must inherit `blueprint/tool_system_v0.yaml:milestone_module_invariant` or embed an equivalent machine-readable contract before its next phase entry or controlled write.

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

P10, P11, P12, and P13 are accepted and closed at their recorded scopes. P14B Provider-Neutral AI Worker Contract and P14MR Milestone Module Invariant are accepted and closed. P14 is active at the exact P14C bounded real-provider module. Only the named synthetic OpenAI execution packet is authorized; repository benchmarks and target mutations are not authorized. P15-P16 remain roadmap-only.

Allowed now:

- P14C documents, source, injected-transport tests, one exact synthetic live execution, internal pull-request lifecycle, merge, and bounded closure under `docs/reports/p14c_bounded_real_model_provider_execution.md`;
- provider `openai`, model `gpt-5.6-luna`, endpoint `api.openai.com:443/v1/responses`, credential reference `env:OPENAI_API_KEY`, and the exact token/time/cost/retry/cancellation/redaction envelope recorded by `p14c-openai-gpt56-luna-v1`;
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
- changing the accepted P14B public contract or fixture-only default beyond the interface-compatible execution-guard extension recorded by P14C;
- any provider, model, endpoint, credential reference, input, budget, price, retry, or fallback outside `p14c-openai-gpt56-luna-v1`;
- any repository content, target state, business data, personal data, or secret in a P14C provider request;
- P14D or later P14 source implementation before a named authorization;
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
