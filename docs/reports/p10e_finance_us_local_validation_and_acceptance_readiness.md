# P10E Finance-US Local Validation and Acceptance Readiness

repo_rel_path: docs/reports/p10e_finance_us_local_validation_and_acceptance_readiness.md  
role: target-local validation evidence and P1A acceptance-readiness review  
purpose: record the user-supplied target-local validation PASS, refresh target PR state, and identify acceptance blockers before any ready transition or merge  
status: LOCAL_VALIDATION_PASS_P1A_ACCEPTANCE_BLOCKED  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-11 UTC+08:00

## 1. Parent alignment

Parent record:

```text
docs/reports/p10d_finance_us_pr_execution_evidence.md
```

P10D recorded target-local validation as pending. The user subsequently ran the required target-local commands on the target branch and supplied their outputs. P10E records that evidence and performs a fresh acceptance-readiness review. This record does not modify finance-us, mark its PR ready, merge it, accept P1A, enter P1B, execute cleanup, or delete a branch.

## 2. Target identity and refreshed PR state

```text
canonical_project_name: finance-us
current_github_repository_full_name: apolo183/finance-us
target_pr: 1
target_branch: p1a-us-equity-contract-realignment
target_head: 679af8d0775a4acf8f469a8bf5c345d694e93d6e
base_branch: main
approved_base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
pr_state: open
pr_draft: true
pr_merged: false
changed_files: 8
commits: 8
```

Fresh connector checks confirm the PR remains draft and unmerged, its head SHA is unchanged, and target `main` remains identical to the approved base SHA.

## 3. User-supplied target-local validation evidence

The user ran the following class of checks from `/home/rich/projects/finance-us` on branch `p1a-us-equity-contract-realignment`:

```text
git fetch origin --prune
git checkout p1a-us-equity-contract-realignment
git pull --ff-only origin p1a-us-equity-contract-realignment
git diff --check
contract file and required/forbidden term validator
git status -sb --untracked-files=all
git diff --stat origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Observed results:

```text
branch up to date: PASS
git diff --check: PASS
US-equity contract realignment validator: PASS
worktree status: clean
changed files: 8
additions: 609
deletions: 268
```

Exact changed paths:

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

The changed-path list exactly matches the approved P10C allowlist. No source, test, data, dependency, Makefile, CI, runtime, or artifact path changed.

## 4. Validation disposition

```text
target_local_validation: PASS
allowlist_match: PASS
worktree_clean: PASS
legacy_blueprint_absent: PASS
required_us_equity_terms: PASS
residual_a_share_terms_check: PASS
target_main_unchanged: PASS
```

The local validation gap recorded in P10D is therefore closed.

## 5. Acceptance blocker 1: repository identity drift

The GitHub repository has now been renamed to:

```text
apolo183/finance-us
```

The target PR branch still declares the former remote slug in active files:

```text
github_repository_full_name: apolo183/finance-os
remote_slug_is_legacy_name: true
```

This stale value remains in at least:

- `README.md`;
- `AGENTS.md`;
- `blueprint/finance_us_phase_1_v0.yaml`.

Because the current GitHub repository full name is now `apolo183/finance-us`, P1A cannot be accepted while active identity contracts still declare `apolo183/finance-os` as the repository full name.

## 6. Acceptance blocker 2: NYSE Arca calendar mapping ambiguity

The blueprint and cutoff contract allow:

```text
NYSE
NASDAQ
NYSE_ARCA
```

but the approved calendar identifiers are only:

```text
XNYS
XNAS
```

The cutoff contract requires every exchange policy to map to an approved calendar, but the active contracts do not explicitly state the mapping for `NYSE_ARCA`. The contract must either:

- define an explicit, reviewed mapping for `NYSE_ARCA`; or
- remove `NYSE_ARCA` from the Phase 1 allowlist until a dedicated mapping is approved.

This ambiguity conflicts with the fail-closed market-identity boundary and blocks strict P1A acceptance.

## 7. Acceptance-readiness result

```text
P1A_US_EQUITY_CONTRACT_REALIGNMENT:
  target_local_validation: PASS
  contract_review: BLOCKED
  acceptance_ready: false
  p1b_entry_allowed: false
  target_pr_ready_transition: not_approved
  target_pr_merge: not_approved
```

The first controlled downstream PR pilot has demonstrated branch creation, bounded file mutation, allowlist enforcement, local validation, draft PR creation, unchanged main, audit evidence, and rollback references. However, P10 final acceptance and finance-us P1A acceptance remain blocked until the two contract issues above are corrected and revalidated.

## 8. Required next packet

A later named correction packet should be limited to the existing draft target branch and the minimum active identity/calendar files required to:

1. replace stale `apolo183/finance-os` repository-full-name declarations with `apolo183/finance-us`;
2. resolve the `NYSE_ARCA` calendar mapping ambiguity;
3. rerun target-local validation;
4. keep PR #1 draft and unmerged unless separately approved.

No target mutation is authorized by this P10E record.

## 9. Boundary

This record grants no finance-us file write, PR ready transition, PR merge, P1A acceptance, P1B implementation, production deployment, data/model operation, rollback execution, cleanup, branch deletion, real external worker call, or Codex replacement claim.
