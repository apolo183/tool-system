# P9J Residue Cleanup Plan

repo_rel_path: docs/reports/p9j_residue_cleanup_plan.md  
role: cleanup planning record  
purpose: identify accidental remote branch residue and define a safe cleanup gate without executing deletion  
status: PLAN_ONLY_CLEANUP_EXECUTION_NOT_APPROVED  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-10 UTC+08:00

## 1. Disposition

P9J documents cleanup residue and a proposed cleanup gate. This record does not delete branches, accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, execute rollback, or claim Codex replacement.

## 2. Evidence basis

P9H recorded known cleanup residue and stated that branches should not be deleted directly; cleanup requires a separate cleanup gate/PR.

This plan extends that inventory and defines read-only verification plus a later explicit cleanup execution gate.

## 3. Cleanup residue candidates

Known accidental remote branch residue from side-effect tool misuse:

```text
p9f-dgx-local-evidence2
p9f-dgx-local-evidence3
p9f-dgx-local-evidence4
p9f-dgx-local-evidence5
p9f-dgx-local-evidence6
p9f-dgx-local-evidence7
p9f-dgx-local-evidence8
p9g-rollback-rehearsal-evidence
p9g-rollback-rehearsal-evidence2
p9g-rollback-rehearsal-evidence3
p9g-rollback-rehearsal-evidence4
p9g-rollback-rehearsal-evidence5
p9g-rollback-rehearsal-evidence6
```

`p9g-rollback-rehearsal-evidence` is included because the original branch was created for evidence recording but was never used for a merged evidence PR. Its final disposition must be verified by read-only inspection before deletion.

## 4. Required read-only verification before cleanup execution

Before any deletion, each candidate branch must be inspected using read-only commands or GitHub API equivalents:

```bash
git ls-remote --heads origin <branch>
git log --oneline origin/main..<branch>
git log --oneline <branch>..origin/main
```

Expected cleanup-eligible condition:

- branch exists;
- branch has no unique commits relative to `origin/main`, or any unique commits are documented as invalid residue;
- branch is not referenced by an open PR;
- branch is not a protected branch;
- branch is not the current active stage branch;
- branch is not needed as evidence beyond its listing in this cleanup plan.

## 5. Proposed cleanup execution gate

A later cleanup execution PR or explicit cleanup gate may delete only branches that satisfy the read-only checks above.

Proposed command shape, not authorized by this plan:

```bash
git push origin --delete <branch>
```

or equivalent GitHub API deletion for `refs/heads/<branch>`.

## 6. Prohibited in this stage

P9J does not authorize:

- branch deletion;
- destructive cleanup;
- cleanup execution;
- P9 acceptance;
- P10 entry;
- target-repository mutation;
- production deployment.

## 7. Next short stage

Recommended next stage: P9K cleanup read-only verification, unless the user reaches the P9 acceptance milestone first. P9K should inspect the listed branches, record which are safe to delete, and still avoid deletion without explicit cleanup execution approval.
