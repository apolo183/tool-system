# P9F DGX Local Validation Evidence

repo_rel_path: docs/reports/p9f_dgx_local_validation_evidence.md  
role: local validation evidence record  
purpose: record user-provided DGX local verification results for P9 strict review  
status: PARTIAL_PASS_ROLLBACK_REHEARSAL_MISSING  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-09 UTC+08:00

## 1. Evidence source

Evidence source: user-provided DGX terminal log pasted into the ChatGPT project conversation.

This record summarizes the supplied terminal output. It does not accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, execute rollback, or claim Codex replacement.

## 2. Commands represented in the evidence

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout main
git pull --ff-only origin main
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
git status -sb --untracked-files=all
git log --oneline -8
git diff --stat
python -m pytest -q tests/test_worker_adapter_contract.py tests/test_worker_adapter_orchestration.py tests/test_worker_adapter_policy_gate.py
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
```

## 3. Observed results

| Check | Observed result | Status |
|---|---|---|
| Fetch and fast-forward | local main fast-forwarded from `dfaad9d` to `788806b` | PASS |
| Current main head | `788806b` / `P9E strict review requirements (#58)` shown as `HEAD -> main, origin/main, origin/HEAD` | PASS |
| Local status | `## main...origin/main` with no listed dirty files | PASS |
| Local diff | `git diff --stat` produced no diff output before tests | PASS |
| Dependency installation | `python3.11` was not available; install continued under pyenv Python 3.14.3 and installed editable `tool-system` plus dev deps | PASS_WITH_ENV_VARIANCE |
| Focused P9 tests | `12 passed in 0.25s` | PASS |
| Active gates | validator output ended with top-level `status: PASS` and `reasons: []` | PASS |

## 4. Environment variance

The recommended command attempted to use `python3.11`, but DGX did not have `python3.11` installed. The evidence run proceeded under pyenv Python 3.14.3. This is acceptable for local validation only because:

- package installation succeeded;
- focused P9 tests passed;
- active gate validation passed;
- GitHub CI remains the canonical Python 3.11 evidence.

## 5. Remaining strict-review gap

Rollback rehearsal evidence is still missing. P9 cannot be accepted under the strict requirements until rollback rehearsal is captured and aborted, or until the user explicitly waives that requirement.

## 6. Required next command group

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

Do not push the rollback rehearsal branch. Do not commit the revert.

## 7. Residue note

During this evidence-recording workflow, the assistant accidentally created empty remote branches named `p9f-dgx-local-evidence2` through `p9f-dgx-local-evidence8`. These are cleanup residue and should be handled by a later explicit cleanup gate/PR, not by direct deletion in this record.
