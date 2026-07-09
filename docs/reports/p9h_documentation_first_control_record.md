# P9H Documentation-First Control Record

repo_rel_path: docs/reports/p9h_documentation_first_control_record.md  
role: operation safety hardening and project inventory record  
purpose: record documentation-first execution-loop adoption and current P9 project state  
status: ACTIVE  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00

## 1. Disposition

P9H hardens the operation model after drift was observed in side-effect tool use. This record does not accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, execute cleanup, delete branches, execute rollback, or claim Codex replacement.

## 2. Governance update

P9H updates:

- `AGENTS.md`
- `docs/tool_system_global_development_principles_v1.md`

The global principles document is the project-wide discipline contract. `AGENTS.md` points agents to that file as the mandatory first step before material work.

## 3. Documentation-first execution loop

The adopted control loop is:

1. read active blueprint, global principles, milestone document, manifest, and change plan;
2. design or update the narrow current-stage document;
3. verify the stage document against blueprint, requirements, and global principles;
4. execute only the documented scope;
5. create evidence showing what actually happened;
6. compare actual evidence against the stage document and change plan;
7. compare the stage document against earlier blueprint or requirement documents before designing the next stage.

Operational rule: no document means no execution; no evidence means no acceptance; detected drift stops feature work and requires documentation or process correction first.

## 4. Short-stage rule

Each stage should have one natural objective, one branch, one task manifest, one change plan, one evidence record, one CI result, and one stop condition. Multi-objective work is split unless an active document explicitly explains why bundling is safer.

## 5. Side-effect tool hardening

Before any GitHub or repository side-effect tool call, agents must verify:

- intent;
- target repository;
- target branch or PR;
- expected side effect;
- duplicate check;
- active manifest/change-plan authorization;
- stop condition;
- selected tool matches the documented action.

A stage may create at most one branch. Branch variants such as `name2`, `name3`, or `retry` are prohibited unless a recorded incident or replacement document authorizes them.

## 6. Current P9 state inventory

| Item | State | Notes |
|---|---|---|
| P9A worker adapter contract | Implemented | Merged in #54 |
| P9B orchestration audit | Implemented | Merged in #55 |
| P9C adapter policy gate | Implemented | Merged in #56 |
| P9D milestone evidence | Implemented | Merged in #57 |
| P9E strict review requirements | Implemented | Merged in #58 |
| P9F DGX local validation evidence | Implemented | Merged in #59 |
| Rollback rehearsal evidence | Available from user DGX terminal log, not yet repo-recorded | Next short stage should record it |
| P9 acceptance | Not recorded | Requires explicit user decision |
| P10 | Blocked | Requires explicit P9 acceptance and P10 boundary document |

## 7. Residue inventory

Known cleanup residue from accidental branch creation:

```text
p9f-dgx-local-evidence2
p9f-dgx-local-evidence3
p9f-dgx-local-evidence4
p9f-dgx-local-evidence5
p9f-dgx-local-evidence6
p9f-dgx-local-evidence7
p9f-dgx-local-evidence8
p9g-rollback-rehearsal-evidence2
p9g-rollback-rehearsal-evidence3
p9g-rollback-rehearsal-evidence4
p9g-rollback-rehearsal-evidence5
p9g-rollback-rehearsal-evidence6
```

These branches should not be deleted directly in this record. Cleanup requires a separate cleanup gate/PR.

## 8. Next short stages

Recommended next stages under the new loop:

1. P9I rollback rehearsal evidence record: record the user-provided rollback rehearsal output, update strict review requirements, and keep P9 unaccepted.
2. P9J residue cleanup plan: document and validate cleanup of accidental empty branches without deleting them directly.
3. P9 acceptance decision: after evidence and cleanup plan are reviewed, accept or reject P9.
4. P10 planning document only after P9 acceptance.

## 9. Boundary

P9H is documentation and process hardening only. It grants no execution authority for downstream writes, production deployment, cleanup deletion, target-repository mutation, or P10 entry.
