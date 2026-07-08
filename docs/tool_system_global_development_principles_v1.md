# tool-system Global Development Principles v1

## Metadata

- repo_rel_path: `docs/tool_system_global_development_principles_v1.md`
- role: active project-wide engineering discipline contract for tool-system
- purpose: define mandatory evidence, scope, file disposition, cleanup, validation, rollback, and claims rules for tool-system work
- author: ChatGPT / apolo183
- created_at: 2026-07-08 09:20 UTC+08:00

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

## 13. Final state

Status: ACTIVE. Applies to tool-system docs, source, tests, examples, policies, cleanup planning, repository-control work, and target-repository adapters.
