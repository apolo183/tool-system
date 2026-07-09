# P9 Strict Review Requirements

repo_rel_path: docs/reports/p9_strict_review_requirements.md  
role: strict milestone review requirements  
purpose: define the highest-evidence path before P9 acceptance or any P10 entry decision  
status: P9_STRICT_REVIEW_REQUIRED  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00

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
| Local status | DGX/local `git status -sb --untracked-files=all` captured | Missing |
| Local diff | DGX/local `git diff --stat` captured and reviewed | Missing |
| Local tests | DGX/local focused or full test command captured | Missing |
| Rollback rehearsal | Throwaway-branch rollback rehearsal captured and aborted | Missing |
| Review disposition | Human accepts or rejects P9 after evidence review | Missing |

## 3. Required DGX/local read-only evidence commands

These commands are read-only except branch checkout. They should be captured in the review record before P9 acceptance under the highest requirements.

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
- latest main includes P9D evidence commit;
- no unreviewed local diff;
- focused P9 tests pass;
- active gates validate.

## 4. Required rollback rehearsal

Rollback rehearsal must use a throwaway branch and must not be pushed unless separately approved.

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout -B p9-rollback-rehearsal origin/main
git revert --no-commit \
  a20e4870715b1bf76a58ab1a7219251bab53d746 \
  981ba4acb74116575211f86269f93af5e9148171 \
  50a3319c8d1d179a90d9514d1b83838fdfe8dfa6 \
  3507ef51cec70682722d7fcf5096208da34c3539 \
  020dc11318883c0207575bcaf51fbac6a715ef58
git diff --stat
git revert --abort
git checkout main
```

Expected outcome:

- revert plan applies or conflicts are recorded;
- diff stat is captured;
- revert is aborted;
- main is restored;
- no rollback execution occurs without a separate PR and explicit approval.

## 5. Hard prohibitions before separate approval

The following remain prohibited even if P9 is later accepted:

- real external worker calls;
- downstream target-repository mutation;
- production deployment;
- business-domain implementation;
- destructive cleanup execution;
- Codex replacement claims.

## 6. P9 acceptance rule

Under the highest requirements, P9 may be accepted only after:

1. this strict review requirements record is merged;
2. GitHub CI remains green;
3. DGX/local status, diff, tests, and active-gate evidence are captured;
4. rollback rehearsal evidence is captured;
5. the user explicitly accepts P9 and defines or approves P10 boundaries.

## 7. P10 non-entry rule

This record does not authorize P10. P10 remains blocked until a later explicit acceptance decision.
