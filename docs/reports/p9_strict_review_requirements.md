# P9 Strict Review Requirements

repo_rel_path: docs/reports/p9_strict_review_requirements.md  
role: strict milestone review requirements  
purpose: define the highest-evidence path before P9 acceptance or any P10 entry decision  
status: P9_STRICT_REVIEW_REQUIRED  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00  
updated_at: 2026-07-09 UTC+08:00

## 1. Disposition

User requested continuing under the highest requirements. This document therefore does not accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, or claim Codex replacement.

The highest-evidence path requires P9 to remain in review until the checklist below is satisfied or explicitly waived by the user.

## 2. Required evidence before P9 acceptance

P9 acceptance requires all of the following evidence categories:

| Category | Required evidence | Current status |
|---|---|---|
| Main state | `main..main` identical and current main commit recorded | GitHub evidence exists |
| CI | P9 entry, P9A, P9B, P9C, and P9D PRs passed CI | GitHub evidence exists |
| Active gates | Active gate validation passed after P9D | GitHub evidence exists |
| Boundary | No external worker calls, downstream writes, target mutation, production deployment, business-domain logic, or Codex replacement claim | GitHub/document evidence exists |
| Local status | DGX/local `git status -sb --untracked-files=all` captured | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Local diff | DGX/local `git diff --stat` captured and reviewed | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Local tests | DGX/local focused or full test command captured | Captured in `docs/reports/p9f_dgx_local_validation_evidence.md` |
| Rollback rehearsal | Throwaway-branch rollback rehearsal captured and aborted | Missing |
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

## 4. Required DGX/local read-only evidence commands

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
- latest main includes P9E strict review requirements commit;
- no unreviewed local diff;
- focused P9 tests pass;
- active gates validate.

## 5. Required rollback rehearsal

Rollback rehearsal must use a throwaway branch and must not be pushed unless separately approved.

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout -B p9-rollback-rehearsal origin/main
git revert --no-commit \
  788806b5167973a411e6360ab595ce3b0d3b4706 \
  a20e4870715b1bf76a58ab1a7219251bab53d746 \
  981ba4acb74116575211f86269f93af5e9148171 \
  50a3319c8d1d179a90d9514d1b83838fdfe8dfa6 \
  3507ef51cec70682722d7fcf5096208da34c3539 \
  020dc11318883c0207575bcaf51fbac6a715ef58
git diff --stat
git revert --abort
git checkout main
git status -sb --untracked-files=all
```

Expected outcome:

- revert plan applies or conflicts are recorded;
- diff stat is captured;
- revert is aborted;
- main is restored;
- no rollback execution occurs without a separate PR and explicit approval.

## 6. Hard prohibitions before separate approval

The following remain prohibited even if P9 is later accepted:

- real external worker calls;
- downstream target-repository mutation;
- production deployment;
- business-domain implementation;
- destructive cleanup execution;
- Codex replacement claims.

## 7. P9 acceptance rule

Under the highest requirements, P9 may be accepted only after:

1. this strict review requirements record is merged;
2. GitHub CI remains green;
3. DGX/local status, diff, tests, and active-gate evidence are captured;
4. rollback rehearsal evidence is captured;
5. the user explicitly accepts P9 and defines or approves P10 boundaries.

## 8. P10 non-entry rule

This record does not authorize P10. P10 remains blocked until a later explicit acceptance decision.
