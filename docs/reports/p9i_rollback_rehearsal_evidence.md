# P9I Rollback Rehearsal Evidence

repo_rel_path: docs/reports/p9i_rollback_rehearsal_evidence.md  
role: rollback rehearsal evidence record  
purpose: record user-provided DGX rollback rehearsal output for P9 strict review  
status: PASS_FOR_P9F_BASELINE_CURRENT_HEAD_ADVANCED_BY_P9H  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-10 UTC+08:00

## 1. Evidence source

Evidence source: user-provided DGX terminal log pasted into the ChatGPT project conversation.

This record summarizes the supplied terminal output. It does not accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, execute cleanup, delete branches, execute rollback, or claim Codex replacement.

## 2. Commands represented in the evidence

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -B p9-rollback-rehearsal origin/main
git rev-parse --short HEAD
git revert --no-commit \
  7b1e043d0f958d9f37dc03e6cd782aca91c5a87f \
  788806b5167973a411e6360ab595ce3b0d3b4706 \
  a20e4870715b1bf76a58ab1a7219251bab53d746 \
  981ba4acb74116575211f86269f93af5e9148171 \
  50a3319c8d1d179a90d9514d1b83838fdfe8dfa6 \
  3507ef51cec70682722d7fcf5096208da34c3539 \
  020dc11318883c0207575bcaf51fbac6a715ef58
git status -sb --untracked-files=all
git diff --cached --stat
git diff --stat
git revert --abort
git checkout main
git pull --ff-only origin main
git status -sb --untracked-files=all
```

## 3. Observed results

| Check | Observed result | Status |
|---|---|---|
| Main fast-forward before rehearsal | local main fast-forwarded from `788806b` to `7b1e043` | PASS |
| Rehearsal branch base | `p9-rollback-rehearsal` set up to track `origin/main` | PASS |
| Rehearsal HEAD | `git rev-parse --short HEAD` returned `7b1e043` | PASS |
| Revert application | `git revert --no-commit` produced staged modified/deleted files without reported conflict | PASS |
| Revert diff stat | cached rollback diff stat captured: `34 files changed, 30 insertions(+), 1884 deletions(-)` | PASS |
| Abort | `git revert --abort` completed and checkout returned to `main` | PASS |
| Final main status | final status showed `## main...origin/main` with no listed dirty files | PASS |
| Push/commit | no push or commit was reported | PASS |

## 4. Scope of this evidence

This evidence validates a rollback rehearsal for the P9 baseline ending at:

```text
7b1e043d0f958d9f37dc03e6cd782aca91c5a87f  P9F DGX local validation evidence (#59)
```

The rehearsal covered these P9 commits in reverse order:

```text
7b1e043d0f958d9f37dc03e6cd782aca91c5a87f  P9F DGX local validation evidence (#59)
788806b5167973a411e6360ab595ce3b0d3b4706  P9E strict review requirements (#58)
a20e4870715b1bf76a58ab1a7219251bab53d746  P9D milestone review evidence (#57)
981ba4acb74116575211f86269f93af5e9148171  P9C adapter policy gate (#56)
50a3319c8d1d179a90d9514d1b83838fdfe8dfa6  P9B adapter orchestration audit (#55)
3507ef51cec70682722d7fcf5096208da34c3539  P9A worker adapter contract (#54)
020dc11318883c0207575bcaf51fbac6a715ef58  P9 phase entry (#53)
```

## 5. Current-head note

After this DGX rehearsal, P9H documentation-first control hardening was merged into `main` as:

```text
5709f2c527bd9dd0d8700597d0e18be608804274  P9H documentation-first control hardening (#60)
```

Therefore, this record must not falsely claim a current-head rollback rehearsal through P9H. Under strict review, either an updated rollback rehearsal including `5709f2c527bd9dd0d8700597d0e18be608804274` is still needed, or the user must explicitly waive that extra rehearsal and accept the P9H PR rollback reference as sufficient.

## 6. Boundary

This record is evidence-only. It grants no execution authority for rollback, cleanup deletion, downstream writes, production deployment, target-repository mutation, or P10 entry.
