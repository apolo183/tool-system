# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-11 UTC+08:00

## 1. Mission

tool-system builds and controls automated software-development workflows. It is domain-agnostic infrastructure.

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

## 5. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

Material engineering work follows the evidence hierarchy, documentation-first loop, blueprint alignment invariant, drift gate, authorization gate, side-effect preflight, file disposition, cleanup, rollback, and claims rules in `docs/tool_system_global_development_principles_v1.md`.

## 6. Side-effect tool discipline

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

## 7. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, milestone acceptance, cleanup execution, first real downstream target-repository mutation, target PR lifecycle transitions, and production deployment.

## 8. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

## 9. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 10. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 11. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 12. Current phase state

Current phase: P12_DURABLE_ORCHESTRATOR.

Status: `active`.

P10 and P11 are accepted at their recorded scopes. P12 Durable Orchestrator is authorized and active. P13-P15 remain roadmap-only; P13 phase entry is not authorized.

Allowed now:

- P12 phase-entry, implementation packets, durable-state source, tests, local fixture evidence, review, merge, and closure;
- SQLite-backed local orchestration state under temporary fixture roots;
- lease, checkpoint, retry, crash-resume, idempotency, side-effect-ledger, transactional-outbox, precondition-SHA, and reconciliation work;
- read-only verification of the accepted P11 runtime;
- read-only verification of accepted target state;
- preparation of separately approvable downstream target lifecycle packets.

Not allowed now:

- target PR metadata changes, ready transition, or merge without a named merge packet and separate approval;
- target-repository main-branch mutation outside the approved merge flow;
- finance-us P1B target implementation without a named, action-scoped target execution approval;
- treating a P1B implementation approval as ready or merge approval;
- P13 or later phase entry or implementation before a named authorization;
- P12 fixtures that call a real external side effect, remote provider, or target repository;
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
