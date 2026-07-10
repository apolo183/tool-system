# P10B2 Finance-US Pilot Target and Objective

repo_rel_path: docs/reports/p10b2_finance_us_pilot_target_objective.md  
role: P10 target-repository objective-change and candidate-selection record  
purpose: replace the prior finance-cn pilot choice with finance-us as the controlled test bed for tool-system capability validation  
status: FINANCE_US_SELECTED_FOR_READONLY_P10C_PACKET_PREPARATION  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-10 UTC+08:00

## 1. User objective change

The user changed the P10 pilot objective:

```text
需要介入的是finance-us，我的目标变了，将把美股作为tool-system的试验场来检验tool-system的功能
```

This record therefore supersedes only the target-selection decision in:

```text
docs/reports/p10b1_target_repo_identity_correction.md
```

P10B1 remains valid for the canonical-name versus remote-slug mapping. Its selection of `finance-cn` is replaced by this record.

## 2. Selected identity

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-os
prior_project_name: finance-os
default_branch: main
observed_base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
observed_base_commit: chore: add finance-os evaluation contract
selection_scope: read-only P10C execution-approval packet preparation only
```

The canonical project name and GitHub remote slug must remain separate in every later P10 record.

## 3. Parent and global alignment

Parent document:

```text
docs/reports/p10b1_target_repo_identity_correction.md
```

Parent alignment: P10B1 established the canonical/remote identity mapping and the rule that target selection does not grant write authority. P10B2 changes the selected pilot target from `finance-cn` to `finance-us` while preserving that rule.

Global blueprint alignment:

```text
blueprint/tool_system_v0.yaml :: milestones.P10_CONTROLLED_TARGET_REPO_PR_PILOT
```

Global alignment: finance-us is selected only as a controlled downstream PR pilot target. Every real target write remains behind a later named execution approval packet.

## 4. Target-repository contract evidence

The selected remote currently exposes:

- `README.md` defining finance-os as a business system and stating that agent orchestration, CI orchestration, and repository mutation belong to tool-system;
- `AGENTS.md` stating that finance-os may be modified by tool-system only through approved workflows, tests, and review gates;
- `blueprint/finance_os_phase_1_v0.yaml` defining current phase `P1_SHADOW_TOP10`;
- `contracts/evaluation_contract.yaml` limiting Phase 1 evaluation to structural, coverage, stability, schema, cutoff, and deterministic-output checks.

The target explicitly forbids live trading, broker connectivity, autonomous strategy mutation, investment recommendations, and model-quality claims without complete evidence.

## 5. Pilot purpose

The P10 pilot will use finance-us to validate tool-system capabilities, not to validate investment performance.

Tool-system capability areas to evaluate:

1. target-repository identity resolution;
2. target blueprint and contract parsing;
3. evidence-first target-state collection;
4. bounded task decomposition;
5. file allowlist and forbidden-path enforcement;
6. branch and PR command planning;
7. test and CI gate enforcement;
8. review and audit record generation;
9. rollback reference generation;
10. post-pilot cleanup and residue verification.

Pilot success must be measured by engineering-control evidence, not by expected return, alpha, Sharpe ratio, hit rate, investment recommendation quality, or production readiness.

## 6. First candidate pilot task

The target blueprint defines:

```text
P1B_MINIMAL_RANKING_CODE
```

Objective:

```text
implement deterministic in-memory ranking over a validated input frame
```

Required outputs:

```text
ranking function
smoke test
```

Read-only code search found no ranking implementation or smoke test. Therefore P1B is the preferred first P10 pilot task, subject to a fresh P10C preflight.

The proposed pilot must remain minimal:

- deterministic in-memory logic only;
- no market-data download;
- no database, lake, raw-data, or artifact writes;
- no scheduler;
- no training, backtest, portfolio, broker, or production path;
- no investment or performance claims.

## 7. P10C entry condition

P10C may prepare a named execution-approval packet for:

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-os
target_business_phase: P1_SHADOW_TOP10
candidate_target_milestone: P1B_MINIMAL_RANKING_CODE
```

Before finalizing the packet, P10C must:

- refresh the target `main` SHA;
- re-read `README.md`, `AGENTS.md`, and `blueprint/finance_os_phase_1_v0.yaml`;
- inspect the current target tree for existing implementation and tests;
- choose a non-main target branch;
- define exact allowed and forbidden files;
- define validation commands;
- define rollback and post-action checks;
- stop on drift, ambiguity, or conflicting target contracts.

P10C packet creation alone grants no target write authority. A later explicit execution approval remains required before branch creation, file changes, or PR creation in finance-us.

## 8. Boundary

P10B2 selects finance-us as the tool-system pilot test bed and selects P1B as the preferred packet objective. It does not create a target branch, modify target files, open a target PR, run target code, download data, train or evaluate models, execute backtests, deploy to production, execute rollback, delete branches, call a real external worker, or claim Codex replacement.