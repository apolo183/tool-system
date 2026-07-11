# P10G Finance-US Correction Execution Evidence

status: CORRECTION_VALIDATED_P1A_ACCEPTANCE_READY
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
parent: docs/reports/p10f_finance_us_identity_calendar_correction_packet.md
created_at: 2026-07-11 UTC+08:00

## Target state

```text
repository: apolo183/finance-us
pull_request: 1
pull_request_state: open_draft_unmerged
target_branch: p1a-us-equity-contract-realignment
correction_base_sha: 679af8d0775a4acf8f469a8bf5c345d694e93d6e
validated_head_sha: dbf43976d0b336c0df961a651f35e8b3ceca0255
main_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
```

## Approved correction scope

The P10F execution approval permitted changes only to:

```text
README.md
AGENTS.md
blueprint/finance_us_phase_1_v0.yaml
contracts/data_input_contract.yaml
contracts/cutoff_contract.yaml
contracts/ranking_output_contract.yaml
```

The correction diff from `679af8d...` to `dbf4397...` contains exactly these six files, is six commits ahead, and is zero commits behind.

## Correction results

The two P10E acceptance blockers are resolved:

1. active repository identity now declares `apolo183/finance-us` and no longer declares `apolo183/finance-os` in the approved correction files;
2. `NYSE_ARCA` is absent from the Phase 1 exchange allowlists, leaving NYSE and NASDAQ with XNYS and XNAS calendars.

The correction preserves USD, `America/New_York`, common-stock-only, observation-only, deterministic-output, fail-closed, no-live-trading, and no-investment-recommendation boundaries.

## User-supplied target-local validation

The user refreshed the target branch to `dbf4397...` and supplied the following results:

```text
head_matches_validated_sha: PASS
origin_main_matches_approved_sha: PASS
git_diff_check: PASS
identity_calendar_validator: PASS
correction_changed_paths: exact_six_file_allowlist
worktree_clean: PASS
```

The local validator confirmed:

- `apolo183/finance-us` is present;
- `apolo183/finance-os` is absent;
- `NYSE_ARCA` is absent;
- NYSE, NASDAQ, XNYS, XNAS, USD, `America/New_York`, and `observation_only` remain present.

## Connector verification

Fresh connector checks confirm:

```text
pr_state: open
pr_draft: true
pr_merged: false
pr_head: dbf43976d0b336c0df961a651f35e8b3ceca0255
target_main_unchanged: true
hosted_workflow_runs: none
commit_status_checks: none
```

The complete target PR still contains the original eight approved P10C paths. The P10F correction itself is limited to the six-file correction allowlist.

## Acceptance-readiness disposition

```text
P1A_US_EQUITY_CONTRACT_REALIGNMENT:
  correction_execution: PASS
  target_local_validation: PASS
  identity_blocker: RESOLVED
  calendar_scope_blocker: RESOLVED
  contract_review: PASS
  acceptance_ready: true
  accepted: false
  target_pr_ready_transition: not_approved
  target_pr_merge: not_approved
  p1b_entry_allowed: false
```

P1A acceptance is now a human milestone decision. P1B entry remains blocked until P1A is explicitly accepted. The target PR must remain draft and unmerged unless separately approved.

## Next boundary

The next tool-system stage should prepare the P10 post-pilot evidence bundle and acceptance decision record. It must not mark finance-us PR #1 ready, merge it, accept P1A, enter P1B, execute cleanup, delete branches, run data/model operations, deploy production, call a real external worker, or claim Codex replacement without separate approval.
