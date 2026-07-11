# P10F Finance-US Identity and Calendar Correction Packet

status: EXECUTION_APPROVAL_REQUIRED
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
parent: docs/reports/p10e_finance_us_local_validation_and_acceptance_readiness.md

## Target state

```text
repository: apolo183/finance-us
pull_request: 1
pull_request_state: open_draft_unmerged
target_branch: p1a-us-equity-contract-realignment
correction_base_sha: 679af8d0775a4acf8f469a8bf5c345d694e93d6e
main_base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
```

## Objective

Close the two P10E acceptance blockers without implementing ranking code or changing target main:

1. replace stale `apolo183/finance-os` repository identity with `apolo183/finance-us`;
2. remove `NYSE_ARCA` from the Phase 1 allowlist until a dedicated calendar mapping is separately approved.

Removing `NYSE_ARCA` is the fail-closed choice. Phase 1 remains limited to NYSE and NASDAQ common stocks using XNYS and XNAS calendars.

## Allowed target files

```text
README.md
AGENTS.md
blueprint/finance_us_phase_1_v0.yaml
contracts/data_input_contract.yaml
contracts/cutoff_contract.yaml
contracts/ranking_output_contract.yaml
```

No other target file may change.

## Required changes

- replace every active repository-full-name declaration `apolo183/finance-os` with `apolo183/finance-us`;
- remove or correct statements that the current GitHub slug is legacy;
- remove `NYSE_ARCA` from allowed exchanges in the blueprint and active input, cutoff, and ranking-output contracts;
- retain NYSE, NASDAQ, XNYS, XNAS, USD, America/New_York, common-stock-only, observation-only, and fail-closed boundaries;
- do not alter finance-us PR #1 base, title, draft state, or merge state.

## Forbidden changes

```text
contracts/evaluation_contract.yaml
blueprint/finance_os_phase_1_v0.yaml
src/**
tests/**
data/**
raw/**
lake/**
artifacts/**
reports/**
.github/**
Makefile
pyproject.toml
requirements*.txt
```

No ranking, scoring, selection, evaluation, backtest, data ingestion, production, broker, portfolio, or investment-claim operation is authorized.

## Validation

Run after the correction on the target branch:

```bash
git diff --check

python - <<'PY'
from pathlib import Path

files = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("blueprint/finance_us_phase_1_v0.yaml"),
    Path("contracts/data_input_contract.yaml"),
    Path("contracts/cutoff_contract.yaml"),
    Path("contracts/ranking_output_contract.yaml"),
]
text = "\n".join(p.read_text(encoding="utf-8") for p in files)
assert "apolo183/finance-us" in text
assert "apolo183/finance-os" not in text
assert "NYSE_ARCA" not in text
for term in ["NYSE", "NASDAQ", "XNYS", "XNAS", "USD", "America/New_York", "observation_only"]:
    assert term in text, term
print("PASS: finance-us identity/calendar correction")
PY

git diff --name-only 679af8d0775a4acf8f469a8bf5c345d694e93d6e...HEAD
git status -sb --untracked-files=all
```

The correction diff against `679af8d...` must contain exactly the six allowed files.

## Execution sequence if separately approved

1. refresh finance-us PR #1 and verify its head is still `679af8d...`;
2. verify PR #1 remains open, draft, and unmerged;
3. modify only the six allowed files on the existing target branch;
4. run all validation commands;
5. verify target main remains `b801326...`;
6. collect the updated PR head and correction diff;
7. stop with PR #1 still draft and unmerged.

## Stop conditions

Stop if the target head, PR state, repository identity, approved files, or contract scope has drifted; if any validation fails; or if correction execution has not been explicitly approved.

## Boundary

This packet grants no target write authority by itself. It does not approve PR ready transition, PR merge, P1A acceptance, P1B entry, rollback execution, cleanup, branch deletion, production, data/model operations, external worker calls, or Codex replacement claims.
