# P10L Finance-US Local Post-Merge Validation

status: CORRECTION_REQUIRED
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
phase_status: accepted
parent: docs/reports/p10k_finance_us_pr_merge_execution_evidence.md
created_at: 2026-07-11 UTC+08:00

## Purpose

Record the user-supplied target-local validation performed after finance-us PR #1 was squash merged. This record does not modify finance-us, authorize P1B, execute rollback, or delete branches.

## Locked target state

```text
repository: apolo183/finance-us
original_base: b801326bea5e80ef585be0977e9e493cbfa0c34e
merged_main: bfad12148e80c5f712b150851e9374db3a15a80b
pull_request: 1
merge_method: squash
```

## User-supplied local results

```text
local_HEAD: bfad12148e80c5f712b150851e9374db3a15a80b
origin_main: bfad12148e80c5f712b150851e9374db3a15a80b
local_main_equals_remote_main: PASS
current_worktree_diff_check: PASS
original_base_to_main_diff_check: FAIL
contract_assertions: PASS
changed_paths: exact_accepted_eight_file_set
worktree_clean: PASS
```

The base-to-main diff check reported only these formatting defects:

```text
AGENTS.md:5: trailing whitespace
README.md:5: trailing whitespace
```

The affected added lines are the `purpose:` metadata lines. No content, schema, identity, exchange, calendar, currency, cutoff, or safety assertion failed.

## Contract and path validation

The local Python assertions passed for:

- canonical `finance-us` identity;
- repository identity `apolo183/finance-us`;
- NYSE and NASDAQ scope;
- XNYS and XNAS calendars;
- USD and `America/New_York`;
- `common_stock`, `observation_only`, and `fail_closed` terms;
- absence of the legacy blueprint;
- absence of the former repository slug, `NYSE_ARCA`, A-share timezone, ST, and price-limit terms.

The original-base-to-main path set remained exactly:

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

## Validation disposition

```text
P1A_content_merged_to_main: true
connector_post_merge_validation: PASS
local_contract_validation: PASS
local_sha_and_path_validation: PASS
local_base_to_main_diff_check: FAIL_TRAILING_WHITESPACE_ONLY
target_local_post_merge_validation: BLOCKED
P1B_entry_authorized: false
```

The trailing whitespace is a real validation failure and must not be waived. It requires a separately approved two-file correction PR against finance-us main, followed by another local post-merge validation and closure record.

## Local repository note

The local checkout still reports the redirecting remote URL `github.com:apolo183/finance-os`. This is a local Git remote configuration residue, not target repository content drift. It does not change the merge result, but the local remote URL should be normalized separately to `apolo183/finance-us` before future implementation work.

## Boundary

This record grants no authority to modify finance-us, amend the merged PR, enter or implement P1B, execute rollback or cleanup, delete branches, deploy production, run data/model/trading operations, call a real external worker, or claim Codex replacement.
