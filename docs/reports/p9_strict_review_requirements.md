# P9 Strict Review Requirements

repo_rel_path: docs/reports/p9_strict_review_requirements.md  
role: strict milestone review requirements  
purpose: define the highest-evidence path before P9 acceptance or any P10 entry decision  
status: P9_STRICT_REVIEW_REQUIRED  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00  
updated_at: 2026-07-10 UTC+08:00

## 1. Disposition

User requested continuing under the highest requirements. This document therefore does not accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, or claim Codex replacement.

The highest-evidence path requires P9 to remain in review until the checklist below is satisfied or explicitly waived by the user.

## 2. Required evidence before P9 acceptance

P9 acceptance requires all of the following evidence categories:

| Category | Required evidence | Current status |
|---|---|---|
| Main state | `main..main` identical and current main commit recorded | GitHub evidence exists |
| CI | P9 entry through P9H PRs passed CI | GitHub evidence exists |
| Active gates | Active gate validation passed after P9H | GitHub evidence exists |
| Boundary | No external worker calls, downstream writes, target mutation, production deployment, business-domain logic, or Codex replacement claim | GitHub/document evidence exists |
| Local status | DGX/local `git status -sb --untracked-files=all` captured | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Local diff | DGX/local `git diff --stat` captured and reviewed | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Local tests | DGX/local focused or full test command captured | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Rollback rehearsal | Throwaway-branch rollback rehearsal captured and aborted | Captured for P9F baseline in `docs/reports/p9i_rollback_rehearsal_evidence.md`; current-head P9H refresh or waiver still required |
| Review disposition | Human accepts or rejects P9 after evidence review | Missing |

## 3. Captured DGX/local evidence

DGX/local validation evidence is recorded in:

```text
docs/reports/p9f_dgx_local_validation_evidence.md
```

Captured outcomes:

- local main fast-forwarded to `788806b5167973a411e6360ab595ce3b0d3b4706`;
- local status showed `## main...origin/main` with no listed dirty files;
- local diff stat had no output before tests;
- focused P9 tests passed: `12 passed in 0.25s`;
- active gate validation returned top-level `status: PASS` with no reasons.

## 4. Captured rollback rehearsal evidence

Rollback rehearsal evidence is recorded in:

```text
docs/reports/p9i_rollback_rehearsal_evidence.md
```

Captured outcomes:

- local main fast-forwarded to `7b1e043d0f958d9f37dc03e6cd782aca91c5a87f` before rehearsal;
- rehearsal branch `p9-rollback-rehearsal` was created from `origin/main`;
- rehearsal HEAD was `7b1e043`;
- `git revert --no-commit` produced staged rollback changes without reported conflict;
- cached rollback diff stat was captured as `34 files changed, 30 insertions(+), 1884 deletions(-)`;
- `git revert --abort` completed;
- final `main` status returned to `## main...origin/main` with no listed dirty files;
- no push or commit was reported.

This validates rollback rehearsal for the P9 baseline through `P9F DGX local validation evidence (#59)`.

## 5. Current-head refresh requirement

After the captured rollback rehearsal, P9H documentation-first control hardening merged as:

```text
5709f2c527bd9dd0d8700597d0e18be608804274  P9H documentation-first control hardening (#60)
```

Strict P9 acceptance therefore still requires either:

1. an updated DGX rollback rehearsal that includes `5709f2c527bd9dd0d8700597d0e18be608804274`, or
2. an explicit user waiver accepting the P9H PR rollback reference as sufficient.

## 6. Required DGX/local read-only evidence commands

These commands were captured in the P9F evidence record. They remain the reference command set for any re-run.

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout main
git status -sb --untracked-files=all
git log --oneline -8
git diff --stat
python -m pytest -q tests/test_worker_adapter_contract.py tests/test_worker_adapter_orchestration.py tests/test_worker_adapter_policy_gate.py
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
```

Expected outcome:

- working tree clean or all residue explicitly dispositioned;
- latest main includes current P9 evidence and governance commits;
- no unreviewed local diff;
- focused P9 tests pass;
- active gates validate.

## 7. Required current-head rollback rehearsal command, unless waived

Rollback rehearsal must use a throwaway branch and must not be pushed unless separately approved.

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -B p9-rollback-rehearsal origin/main
git rev-parse --short HEAD
git revert --no-commit \
  5709f2c527bd9dd0d8700597d0e18be608804274 \
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

Expected outcome:

- current-head revert plan applies or conflicts are recorded;
- cached diff stat is captured;
- revert is aborted;
- main is restored;
- no rollback execution occurs without a separate PR and explicit approval.

## 8. Hard prohibitions before separate approval

The following remain prohibited even if P9 is later accepted:

- real external worker calls;
- downstream target-repository mutation;
- production deployment;
- business-domain implementation;
- destructive cleanup execution;
- Codex replacement claims.

## 9. P9 acceptance rule

Under the highest requirements, P9 may be accepted only after:

1. this strict review requirements record is merged;
2. GitHub CI remains green;
3. DGX/local status, diff, tests, and active-gate evidence are captured;
4. rollback rehearsal evidence is captured for current head or explicitly waived for the post-rehearsal governance-only commit;
5. the user explicitly accepts P9 and defines or approves P10 boundaries.

## 10. P10 non-entry rule

This record does not authorize P10. P10 remains blocked until a later explicit acceptance decision.
