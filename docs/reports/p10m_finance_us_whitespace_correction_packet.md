# P10M Finance-US Whitespace Correction Packet

status: EXECUTION_APPROVAL_REQUIRED
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
phase_status: accepted
parent: docs/reports/p10l_finance_us_local_post_merge_validation.md
created_at: 2026-07-11 UTC+08:00

## Purpose

Define a separately approvable, two-file target correction that removes the trailing whitespace blocking finance-us post-merge validation. This packet grants no target write or merge authority by itself.

## Locked target state

```text
repository: apolo183/finance-us
base_branch: main
base_sha: bfad12148e80c5f712b150851e9374db3a15a80b
proposed_branch: p1a-whitespace-correction
P1B_entry_authorized: false
```

## Exact allowed target changes

Only these files may change:

```text
AGENTS.md
README.md
```

Only these edits are allowed:

- remove trailing whitespace from the `purpose:` metadata line in `AGENTS.md`;
- remove trailing whitespace from the `purpose:` metadata line in `README.md`;
- preserve all visible text, semantics, headings, contracts, and line ordering.

No other line or path may change.

## Forbidden target actions

- no blueprint or contract semantic change;
- no source, tests, data, CI, dependency, model, ranking, backtest, production, broker, or trading change;
- no direct main write;
- no PR ready transition or merge;
- no P1B entry or implementation;
- no rollback, cleanup, or branch deletion.

## Fresh-state preflight

Immediately before execution verify:

1. finance-us `main` is exactly `bfad12148e80c5f712b150851e9374db3a15a80b`;
2. branch `p1a-whitespace-correction` does not exist;
3. no open PR already targets the same correction;
4. `AGENTS.md:5` and `README.md:5` still contain the reported trailing whitespace;
5. no other `git diff --check` defect is present in the original-base-to-main diff.

Any drift blocks execution.

## Authorized sequence if separately approved

1. create `p1a-whitespace-correction` from the locked target main;
2. modify only `AGENTS.md` and `README.md` as specified;
3. verify the correction diff contains exactly two files and whitespace-only changes;
4. run `git diff --check` against the correction branch and against the original P1A base-to-correction-head range;
5. rerun the finance-us contract assertions;
6. open one draft PR against `main`;
7. collect remote and target-local validation evidence;
8. stop without marking ready, merging, entering P1B, or deleting branches.

## Pass conditions

```text
changed_paths: [AGENTS.md, README.md]
semantic_diff: none
trailing_whitespace_defects: zero
contract_assertions: PASS
worktree_clean: PASS
PR_state: open_draft_unmerged
```

## Rollback

Before merge, close the correction PR and retain its head SHA as evidence. Branch deletion requires a separate cleanup approval. After any future merge, rollback requires a separately approved revert packet and revert PR; never reset or force-push main.

## Boundary

This packet does not authorize finance-us mutation, PR lifecycle changes, P1B, production/data/model/trading operations, rollback, cleanup, branch deletion, real external worker calls, or Codex replacement claims.
