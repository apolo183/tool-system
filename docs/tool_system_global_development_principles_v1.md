# tool-system Global Development Principles v1

## Metadata

- repo_rel_path: `docs/tool_system_global_development_principles_v1.md`
- role: active project-wide engineering discipline contract for tool-system
- purpose: define mandatory evidence, documentation-first execution, blueprint alignment, scope, file disposition, cleanup, validation, rollback, side-effect tool use, and claims rules for tool-system work
- author: ChatGPT / apolo183
- created_at: 2026-07-08 09:20 UTC+08:00
- updated_at: 2026-07-10 UTC+08:00

## 1. Authority

This file is the project-wide discipline contract for tool-system. Narrower task manifests, change plans, tests, runbooks, and PR descriptions may add constraints but must not silently override this file. A conflict stops work until a cross-document disposition is recorded.

## 2. Evidence hierarchy

Fact priority is: current user logs/files/commands/evidence packages > current repo files, branch, commits, PR diffs, CI state, and active docs > active project-wide contracts > active milestone or stage contracts > closed evidence and receipts > history or memory as retrieval hints only. Old drafts, stale branches, prior chat, and search summaries never override current repo evidence.

## 3. Evidence gate

No engineering fact, readiness claim, cleanup decision, implementation plan, or file disposition may be asserted without current repo, commit, diff, PR, command, CI, evidence, or active-contract support. Before modifying or judging a file, read the natural-owner file plus relevant caller, callee, upstream, downstream, and tests. Unread objects are `UNKNOWN`.

## 4. Drift gate

Every material step must verify that it follows the active contract and shortest correct tool-system path, does not switch to a legacy or fallback route, does not use stale output as authority, and does not expand write, deletion, runtime, target-repository, external, or production scope. Unresolved drift stops with a blocker, missing evidence, protected scope at risk, smallest readonly audit needed, and corrected next step.

## 5. Authorization gate

A document, PR, green test, audit, or dry-run authorizes only its explicit scope. Target-repository mutation, production deployment, destructive cleanup, remote writes outside tool-system, and downstream business-system changes require current user authorization plus active contract evidence. No planner or runner output grants execution authority by itself.

## 6. Formal and process file discipline

Formal files are active contracts, source, configs, tests, runbooks, docs, examples, and audit interfaces required to run, validate, operate, audit, or roll back tool-system. Process files are notes, temporary scripts, dry-run outputs, proposal drafts, patch plans, debug logs, and intermediate evidence. Process files must use the narrowest project-local task root such as `tmp/<task_id>/`, `reports/<task_id>/`, or `artifacts/<task_id>/`, unless an explicit exception names path, reason, retention, side effects, and cleanup responsibility.

## 7. File disposition

Allowed dispositions are `KEEP`, `MODIFY`, `REPLACE`, `DELETE`, `ADD`, and `UNKNOWN`. `KEEP` means correct, active, necessary, or valid evidence. `MODIFY` means necessary but stale or wrong. `REPLACE` means superseded by validated replacement and then removed. `DELETE` means obsolete, wrong, duplicate, garbage, superseded, or process-only. `ADD` means a required formal artifact is missing. `UNKNOWN` means unread or impact not verified. Do not preserve invalid objects by moving them to archive, deprecated, fallback, backup, or history directories.

## 8. Simplification and cleanup

Priority is the shortest correct controlled automation path: active contract, natural-owner implementation, focused tests, CI gate, audit record, and rollback reference. Keep one active contract path per responsibility and one natural-owner implementation path per runtime responsibility. Remove or supersede duplicate mainlines, obsolete process docs, transitional scripts, and outdated tests once their replacement and rollback are evidence-backed.

## 9. Reuse and ownership

Prefer `MODIFY` on the natural owner path. Do not create parallel lanes unless a contract proves why replacement is required and defines the deletion or migration point. Reusable tool-system components must parameterize repository, branch, manifest, change plan, graph, output root, and execution options rather than hard-coding downstream business logic.

## 10. Claims boundary

Do not claim Codex replacement, production readiness, autonomous target-repository execution readiness, downstream mutation approval, or milestone closure without current runtime evidence, CI evidence, active closeout criteria, and rollback evidence. Dry-runs, fixtures, planner output, and green unit tests are scoped evidence only.

## 11. Rollback, tests, temp roots, and commands

Non-trivial implementation uses a separate branch and PR. Failed branch state requires a failed branch/base/status/diff record, clean-base return, and redesign. Tests must protect active behavior; tests for obsolete routes are deleted or rewritten. Commands must state directory, environment, purpose, write scope, target-repository impact, deletion status, and rollback when they are material or dangerous.

## 12. Cross-document compliance

Later milestone, planner, runner, cleanup, and target-repository documents must either inherit this file or explicitly record a conflict requiring cross-document disposition. This file grants no implementation, target-repository mutation, destructive cleanup, production deployment, or external-system write authority by itself.

## 13. Documentation-first execution loop

Do not rely on long conversation context as execution authority. Each stage is controlled by active documents and must follow this loop:

1. read the active blueprint, global principles, milestone document, task manifest, and change plan;
2. design or update the narrow current-stage document;
3. verify the current-stage document against the immediate parent document, the active blueprint, active requirements, and this file;
4. execute only the documented scope;
5. create evidence showing what actually happened;
6. compare actual evidence against the stage document and change plan;
7. compare the stage document against both its immediate parent and the active blueprint or requirement source before designing the next stage.

No document means no execution. No evidence means no acceptance. Detected drift stops feature work and requires documentation or process correction first.

## 14. Short-stage rule

A stage should be short, single-objective, and auditable. The default stage unit is one natural objective, one branch, one task manifest, one change plan, one evidence record, one CI result, and one explicit stop condition. If more than one objective appears necessary, split the work into multiple stages unless an active document explains why bundling is safer.

## 15. Blueprint alignment invariant

Every milestone, sub-milestone, task manifest, change plan, evidence record, and acceptance record must prove two alignments:

1. parent alignment: the document follows its immediate parent milestone, stage, manifest, or change plan;
2. global alignment: the document still follows the active blueprint or requirement source.

Parent alignment alone is insufficient. A long chain of small local deviations can accumulate into material blueprint drift. Each stage therefore must explicitly check both its parent and the active blueprint or requirement source, and must stop if either alignment is missing or ambiguous.

For nested work, the expected proof shape is:

```text
blueprint or requirement source
  -> major milestone
    -> sub-milestone
      -> task manifest
        -> change plan
          -> execution evidence
```

Each level must identify its parent, identify the active blueprint or requirement source, and record why the level does not expand or redirect scope beyond either one.

## 16. Script and automation control by documents

Scripts, CLIs, agents, and repository-control tools execute documents; they do not define scope by themselves. A script may only run when the active blueprint or requirement source, milestone document, task manifest, and change plan authorize its purpose, inputs, outputs, side effects, and stop condition. Script output is evidence only after it is compared with the controlling documents and the active blueprint.

## 17. Side-effect tool preflight

Before any tool call that creates, updates, deletes, merges, labels, comments on, or otherwise mutates GitHub or repository state, the agent must verify:

- intent;
- target repository;
- target branch or PR;
- expected side effect;
- duplicate check;
- active manifest/change-plan authorization;
- parent alignment;
- global blueprint or requirement alignment;
- stop condition;
- whether the selected tool matches the documented action.

If the documented action is file creation or file update but the selected tool is branch creation, merge, deletion, cleanup, or any other mismatched mutation, the agent must stop before the tool call. If a duplicate branch, PR, file, or plan exists, reuse or stop; do not create numbered variants unless an active document explicitly authorizes replacement and records disposition.

## 18. Branch single-flight rule

Each stage may create at most one working branch. The branch name must be defined or implied by the stage document. If branch creation succeeds, all later writes for that stage use that branch. If branch creation fails because the branch already exists, the agent must inspect and either reuse it or stop for disposition. Creating branch variants such as `name2`, `name3`, or `retry` is prohibited without an explicit incident or replacement document.

## 19. Incident and residue rule

Any accidental branch, PR, file, label, comment, or other side effect is residue. The next action is an incident or cleanup plan, not continued feature expansion. Residue cleanup must be handled through a separate cleanup gate/PR when it requires deletion, branch deletion, history-affecting action, or any destructive cleanup.

## 20. Final state

Status: ACTIVE. Applies to tool-system docs, source, tests, examples, policies, cleanup planning, repository-control work, side-effect tool use, and target-repository adapters.
