# tool-system Agent Operating Contract

repo_rel_path: AGENTS.md  
role: agent governance contract  
purpose: define how agents inspect, modify, test, and publish tool-system changes  
author: ChatGPT / apolo183  
created_at: 2026-07-05 20:00 UTC+08:00  
updated_at: 2026-07-09 UTC+08:00

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
3. verify the current-stage document against the blueprint and global principles;
4. execute only the documented stage scope;
5. create or update evidence showing what actually happened;
6. compare execution evidence against the stage document and change plan;
7. compare the stage document against earlier blueprint or requirement documents before designing the next stage.

A stage should be short, have one natural objective, one branch, one change plan, one evidence record, and a clear stop condition. If drift is found, the next action is documentation or process correction, not feature expansion.

## 4. Evidence-first rule

Before modifying an existing file, an agent reads the current file and cites the relevant path and content region in its plan.

If evidence is missing, the agent runs read-only inspection or stops at the smallest missing artifact.

Material engineering work follows the evidence hierarchy, documentation-first loop, drift gate, authorization gate, side-effect preflight, file disposition, cleanup, rollback, and claims rules in `docs/tool_system_global_development_principles_v1.md`.

## 5. Side-effect tool discipline

Before any tool call that creates, updates, deletes, merges, labels, or otherwise mutates GitHub state, the agent must internally verify:

- intent;
- target repository;
- target branch or PR;
- expected side effect;
- duplicate check;
- stop condition;
- whether the tool matches the documented action.

If the intended action is file update but the selected tool is branch creation, merge, deletion, or cleanup, work stops before the tool call. A task may create at most one branch unless a later active document explicitly authorizes a replacement branch and records disposition of the prior branch.

## 6. Autonomy model

Human control is placed at blueprint, objective, policy boundary, and milestone review levels.

Routine implementation work inside an authorized milestone is handled by the system after gates pass. Agents do not ask for human review for each ordinary implementation PR once the milestone and manifest are valid.

Human review is required for blueprint changes, objective changes, policy boundary changes, milestone acceptance, cleanup execution, first real downstream target-repository mutation, and production deployment.

## 7. Write boundaries

Agents add or modify files only when the change is tied to an approved blueprint item and a valid task manifest.

tool-system remains separate from business-domain repositories.

## 8. Change record

Every non-trivial change records scope, files touched, reason, verification command, and rollback method.

## 9. Testing policy

Implementation phases include verification before further automation.

Minimum gates include unit tests, format or lint checks where available, type checks where applicable, spec checks, and dry-run patch application.

## 10. Rollback policy

Rollback uses Git history, commit SHAs, pull requests, or patch reversal.

## 11. Current phase

Current phase: P9_WORKER_ADAPTER_ORCHESTRATION.

Allowed now: build and validate no-mutation worker adapter contracts, local or dry-run adapter orchestration, adapter execution records, evidence capture, policy checks, rollback references after P8 acceptance, and process hardening required by the P9 strict review.

Not allowed now: direct target-repository main-branch mutation, direct downstream repository mutation without separate explicit approval, production deployment, business-domain implementation outside a valid approved workflow, cleanup execution without a separate execution gate, branch deletion without a cleanup gate, or autonomous patch execution outside approved tool-system branches.
