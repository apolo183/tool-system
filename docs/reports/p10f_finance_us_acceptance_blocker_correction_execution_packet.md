# P10F Finance-US Acceptance-Blocker Correction Execution Packet

repo_rel_path: docs/reports/p10f_finance_us_acceptance_blocker_correction_execution_packet.md  
role: named downstream correction execution-approval packet  
purpose: define the minimum amendment to existing finance-us draft PR #1 required to resolve P10E identity and market-calendar acceptance blockers  
status: EXECUTION_APPROVAL_REQUIRED  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-11 UTC+08:00

## 1. Disposition

P10F prepares a correction packet for the existing finance-us draft PR. It does not itself modify finance-us, update PR metadata, mark the PR ready, merge the PR, accept P1A, enter P1B, execute cleanup, or delete a branch.

A later explicit execution approval is required before any target mutation.

## 2. Parent and global alignment

Parent record:

```text
docs/reports/p10e_finance_us_local_validation_and_acceptance_readiness.md
```

P10E closed target-local validation as PASS and identified two strict acceptance blockers:

1. active target files still declare the former repository full name `apolo183/finance-os` after GitHub renamed the repository to `apolo183/finance-us`;
2. `NYSE_ARCA` is allowed while the active calendar set is limited to XNYS/XNAS and no explicit Arca mapping exists.

P10F remains within `blueprint/tool_system_v0.yaml :: milestones.P10_CONTROLLED_TARGET_REPO_PR_PILOT` by defining a named, minimal, no-production correction to the existing draft PR.

## 3. Target state approved for packet preparation

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-us
target_pr: 1
target_pr_state: open
target_pr_draft: true
target_pr_merged: false
target_branch: p1a-us-equity-contract-realignment
target_head: 679af8d0775a4acf8f469a8bf5c345d694e93d6e
base_branch: main
base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
```

This packet authorizes no action unless a fresh execution preflight confirms the same PR state, branch head, and base SHA.

## 4. Correction objective

```text
P1A_US_EQUITY_ACCEPTANCE_BLOCKER_CORRECTION
```

Objective:

```text
Amend the existing draft PR so active repository identity matches the current GitHub repository full name and Phase 1 exchange/calendar policy is unambiguous and fail closed.
```

## 5. Selected fail-closed resolution for NYSE Arca

P10F selects the conservative Phase 1 resolution:

```text
remove NYSE_ARCA from the active Phase 1 exchange allowlist
retain NYSE and NASDAQ only
retain XNYS and XNAS only
```

This is not a permanent exclusion. A later separately approved milestone may add NYSE Arca only with an explicit reviewed venue-to-calendar mapping and validation coverage.

## 6. Exact target file allowlist

Only the following existing files on `p1a-us-equity-contract-realignment` may be modified:

```text
README.md
AGENTS.md
blueprint/finance_us_phase_1_v0.yaml
contracts/data_input_contract.yaml
contracts/cutoff_contract.yaml
contracts/ranking_output_contract.yaml
```

No file may be added or deleted by this correction.

## 7. Required target changes

### 7.1 Current repository identity

In every allowed file where repository identity is declared:

```text
github_repository_full_name: apolo183/finance-us
```

Remove stale declarations or prose that treats `apolo183/finance-os` as the current remote slug, including:

```text
apolo183/finance-os
remote_slug_is_legacy_name: true
```

Historical references outside the active allowed files are not part of this packet.

### 7.2 Exchange/calendar policy

In the blueprint, data-input, cutoff, and ranking-output contracts:

- remove `NYSE_ARCA` from active allowed values;
- keep `NYSE` and `NASDAQ`;
- keep XNYS and XNAS calendar identifiers;
- state or preserve explicit mappings:
  - `NYSE -> XNYS`;
  - `NASDAQ -> XNAS`;
- fail closed for any exchange without an explicit approved mapping.

### 7.3 Draft PR metadata

Update the body of finance-us PR #1 only to:

- replace current-repository references to `apolo183/finance-os` with `apolo183/finance-us`;
- state that Phase 1 temporarily excludes NYSE Arca pending a separately approved mapping;
- preserve all no-merge, no-production, no-data/model-operation boundaries.

Do not change the PR title, base branch, draft status, reviewers, labels, or merge state.

## 8. Explicitly forbidden actions

The correction must not:

- create another target branch;
- create another target PR;
- change target `main`;
- mark PR #1 ready;
- merge or close PR #1;
- modify files outside the exact allowlist;
- add or delete files;
- change source, tests, CI, dependencies, data, runtime, or artifacts;
- run ranking, scoring, selection, evaluation, backtest, training, portfolio, broker, or production operations;
- make investment-performance or recommendation claims;
- execute rollback or cleanup;
- delete any branch;
- call a real external worker;
- claim Codex replacement.

## 9. Required validation commands

Run from the target branch after the correction:

```bash
git diff --check

python - <<'PY'
from pathlib import Path

active_files = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("blueprint/finance_us_phase_1_v0.yaml"),
    Path("contracts/data_input_contract.yaml"),
    Path("contracts/cutoff_contract.yaml"),
    Path("contracts/ranking_output_contract.yaml"),
    Path("contracts/evaluation_contract.yaml"),
]

for path in active_files:
    if not path.is_file():
        raise SystemExit(f"BLOCK: missing active file {path}")

combined = "\n".join(path.read_text(encoding="utf-8") for path in active_files)

required_terms = [
    "apolo183/finance-us",
    "NYSE",
    "NASDAQ",
    "XNYS",
    "XNAS",
    "America/New_York",
    "USD",
    "observation_only",
]
for term in required_terms:
    if term not in combined:
        raise SystemExit(f"BLOCK: required term missing: {term}")

forbidden_terms = [
    "apolo183/finance-os",
    "remote_slug_is_legacy_name",
    "NYSE_ARCA",
    "Asia/Shanghai",
    "is_st",
    "limit_up_down_status",
    "st_filter_policy",
]
for term in forbidden_terms:
    if term in combined:
        raise SystemExit(f"BLOCK: forbidden term present: {term}")

blueprint = Path("blueprint/finance_us_phase_1_v0.yaml").read_text(encoding="utf-8")
cutoff = Path("contracts/cutoff_contract.yaml").read_text(encoding="utf-8")
for mapping in ["NYSE", "XNYS", "NASDAQ", "XNAS"]:
    if mapping not in blueprint + cutoff:
        raise SystemExit(f"BLOCK: exchange-calendar mapping term missing: {mapping}")

print("PASS: finance-us P1A acceptance blockers corrected")
PY

git status -sb --untracked-files=all
git diff --name-only origin/main...HEAD
```

Pass conditions:

- every command exits zero;
- worktree is clean after committed correction;
- PR #1 remains open and draft;
- target `main` remains at the approved base SHA;
- the full PR changed-path set remains the original eight P10C paths;
- no stale repository identity or NYSE Arca active allowlist remains;
- no forbidden operation occurred.

## 10. Target mutation sequence if separately approved

A later executor may perform only this sequence:

1. refresh repository metadata and PR #1 state;
2. stop if PR #1 is not open/draft, target head differs, or main differs;
3. modify only the six allowed files on the existing target branch;
4. run all validation commands;
5. inspect the complete PR changed-path set;
6. update only the PR body as described in Section 7.3;
7. collect the new target head SHA and validation evidence;
8. stop with PR #1 still draft and unmerged.

## 11. Stop conditions

Stop before mutation or PR-body update if:

- current repository full name is not `apolo183/finance-us`;
- target head is not `679af8d0775a4acf8f469a8bf5c345d694e93d6e`;
- target main is not `b801326bea5e80ef585be0977e9e493cbfa0c34e`;
- PR #1 is not open and draft;
- another process has changed any allowed target file;
- any required change falls outside the allowlist;
- validation fails;
- execution approval has not been explicitly granted.

## 12. Rollback and recovery

Before target PR merge, correction recovery is limited to:

- retain PR #1 as draft;
- record correction commit SHAs;
- use Git revert on exact correction commits only after separate rollback approval;
- do not delete the branch without a separate cleanup gate.

## 13. Approval boundary

This packet is ready for human execution approval only after it is merged into tool-system with green CI.

Approval must explicitly authorize amendment of the existing finance-us branch and PR #1 body under this packet. It does not authorize ready transition, target PR merge, P1A acceptance, P1B entry, production, data/model operations, rollback, cleanup, branch deletion, external worker calls, or Codex replacement claims.
