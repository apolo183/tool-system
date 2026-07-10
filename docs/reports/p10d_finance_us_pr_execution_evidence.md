# P10D Finance-US Draft PR Evidence

repo_rel_path: docs/reports/p10d_finance_us_pr_execution_evidence.md  
role: downstream draft-PR audit record  
status: DRAFT_PR_CREATED_LOCAL_VALIDATION_REQUIRED  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-11 UTC+08:00

## Parent alignment

Parent packet:

```text
docs/reports/p10c_finance_us_us_equity_contract_realignment_execution_packet.md
```

The user approved creating the target branch, changing only the packet allowlist, and opening a draft PR. Target PR merge was not approved.

## Target identity

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-os
approved_base: main@b801326bea5e80ef585be0977e9e493cbfa0c34e
target_branch: p1a-us-equity-contract-realignment
target_head: 679af8d0775a4acf8f469a8bf5c345d694e93d6e
target_pr: 1
```

## Target PR state

```text
state: open
draft: true
merged: false
base: main
commits: 8
changed_files: 8
```

The target PR was not marked ready and was not merged.

## Exact changed paths

```text
AGENTS.md
README.md
blueprint/finance_os_phase_1_v0.yaml
blueprint/finance_us_phase_1_v0.yaml
contracts/cutoff_contract.yaml
contracts/data_input_contract.yaml
contracts/evaluation_contract.yaml
contracts/ranking_output_contract.yaml
```

No source, test, data, dependency, Makefile, or CI path changed.

## Contract verification

Connector-backed inspection confirmed the target branch contains:

- canonical identity `finance-us`;
- US-listed common-equity scope;
- USD currency;
- exchange and security-type identity;
- XNYS/XNAS calendars;
- `America/New_York` timezone and DST-aware session rules;
- observation-only output and evaluation boundaries;
- continued prohibition of return, alpha, Sharpe, best-model, production-readiness, live-trading, and buy/sell claims.

The legacy blueprint path is absent on the target branch.

## Main-branch verification

```text
main: b801326bea5e80ef585be0977e9e493cbfa0c34e
comparison_status: identical
```

Target `main` is unchanged.

## Validation state

GitHub-hosted workflow runs and commit-status checks for the target head are empty. This does not prove target-local validation.

Before any merge-readiness claim, a target checkout must run:

```bash
git diff --check
python -c 'from pathlib import Path; assert Path("blueprint/finance_us_phase_1_v0.yaml").is_file(); assert not Path("blueprint/finance_os_phase_1_v0.yaml").exists()'
git status -sb --untracked-files=all
git diff --name-only origin/main...HEAD
```

The resulting evidence must confirm the same eight changed paths and no residual A-share terms in active contracts.

## Outcome

```text
branch_created: PASS
allowlist_match: PASS
draft_pr_created: PASS
target_main_unchanged: PASS
target_local_validation: PENDING
target_pr_merge: NOT_APPROVED
```

## Boundary

This record does not approve target PR merge, P1A acceptance, P1B entry, production deployment, data/model operations, rollback execution, cleanup, branch deletion, external worker calls, or Codex replacement claims.
