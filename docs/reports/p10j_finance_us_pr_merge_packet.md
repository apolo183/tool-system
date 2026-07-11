# P10J Finance-US PR #1 Merge Packet

status: EXECUTION_APPROVAL_REQUIRED
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
phase_status: accepted
parent: docs/reports/p10i_p10_p1a_acceptance_closure.md
created_at: 2026-07-11 UTC+08:00

## Purpose

Define a separately approvable merge lifecycle for the accepted finance-us P1A content. This packet does not update the target PR, mark it ready, merge it, modify target files, or open P1B.

## Locked target state

```text
repository: apolo183/finance-us
pull_request: 1
title: P1A realign finance-us contracts to US equities
base_branch: main
base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
head_branch: p1a-us-equity-contract-realignment
expected_head_sha: dbf43976d0b336c0df961a651f35e8b3ceca0255
state: open
draft: true
merged: false
mergeable: true
commits: 14
changed_files: 8
ahead_by: 14
behind_by: 0
merge_method: squash
```

The repository permits squash merge. Squash is selected so the accepted P1A contract milestone lands on target main as one commit.

## Exact accepted changed paths

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

No other target path may be present at execution time.

## Current review and CI state

```text
review_submissions: none
unresolved_review_threads: none
hosted_workflow_runs: none
commit_status_checks: none
```

Target-local validation at the exact head passed and is recorded in P10G. The absence of hosted checks requires exact-head preflight and post-merge validation; it must not be represented as hosted CI success.

## Accepted content invariants

The target head must retain:

- `finance-us` and `apolo183/finance-us` identity;
- NYSE and NASDAQ common-stock Phase 1 scope;
- XNYS and XNAS calendars;
- USD and `America/New_York`;
- deterministic `observation_only` output;
- fail-closed cutoff, snapshot, identity, and reproducibility rules;
- no live trading, broker, production, return, alpha, Sharpe, or recommendation claims.

The accepted active files must not contain the former repository slug, `NYSE_ARCA`, A-share timezone, ST, or price-limit semantics.

## Permitted future PR metadata change

The existing PR body contains the former repository slug. If P10J execution is separately approved, the only permitted metadata update is replacing the PR body with a canonical summary of:

- repository `apolo183/finance-us`;
- accepted P1A scope and exact head;
- exact eight-file allowlist;
- target-local validation PASS;
- no source, test, data, dependency, CI, model, backtest, production, broker, or trading execution changes;
- merge subject to expected-head lock.

The PR title, base, head, labels, reviewers, and assignees must not change under this packet.

## Fresh-state preflight

Immediately before any target PR lifecycle mutation, verify:

1. PR #1 is open, draft, unmerged, and mergeable;
2. base is `main@b801326bea5e80ef585be0977e9e493cbfa0c34e`;
3. head is exactly `dbf43976d0b336c0df961a651f35e8b3ceca0255`;
4. head is 14 commits ahead and 0 behind;
5. changed paths exactly match the accepted eight-file set;
6. no requested-changes review or unresolved thread exists;
7. no workflow/status failure exists;
8. accepted content invariants still hold.

Any drift blocks execution and requires an amended packet or new approval.

## Authorized sequence if separately approved

1. run fresh-state preflight;
2. update only the PR body to the canonical summary;
3. confirm the expected head is unchanged;
4. mark PR #1 ready;
5. re-read PR state and confirm open, non-draft, mergeable, and unmerged;
6. squash merge with the expected head lock;
7. capture the resulting target-main SHA;
8. verify PR merged and target main advanced to the resulting SHA;
9. verify the original-base-to-new-main diff contains exactly the accepted eight paths;
10. verify accepted content on target main;
11. run target-local post-merge validation;
12. create a tool-system post-merge evidence and P1B-entry-readiness record;
13. stop without implementing P1B or deleting branches.

## Post-merge validation requirements

The target-local validation must confirm:

- local main equals the resulting remote main SHA;
- diff check passes;
- the original-base-to-main changed paths are exactly the accepted eight paths;
- the canonical blueprint exists and the legacy blueprint is absent;
- required US-equity identity, exchange, calendar, currency, timezone, and observation-only terms remain present;
- former repository slug, `NYSE_ARCA`, A-share timezone, ST, and price-limit terms remain absent;
- the worktree is clean.

## Post-merge disposition

A successful merge and validation means the accepted P1A content is materialized on target main. It does not automatically authorize P1B. P1B requires a separate post-merge closure record and explicit entry decision.

## Rollback

Before merge, any failed check after a ready transition requires converting the PR back to draft and stopping.

After merge:

- do not force-push or reset target main;
- rollback requires a separately approved revert packet and a revert PR against the squash commit;
- branch deletion remains separately approved cleanup work.

## Stop conditions

Stop without merge on base/head/path/state/mergeability drift, a new requested-changes review, unresolved thread, CI/status failure, invariant failure, missing expected-head lock, or missing explicit P10J execution approval.

## Boundary

This packet grants no target lifecycle authority by itself. It does not update the PR, mark it ready, merge it, modify target files, open P1B, run production/data/model/trading operations, execute rollback or cleanup, delete branches, call a real external worker, or support a Codex replacement claim.
