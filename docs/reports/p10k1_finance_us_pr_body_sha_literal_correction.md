# P10K1 Finance-US PR Body SHA Literal Correction

status: CORRECTION_RECORDED
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT
parent: docs/reports/p10k_finance_us_pr_merge_execution_evidence.md

## Facts

```text
PR body literal: dbf43976d0775a4acf8f469a8bf5c345d694e93d6e
actual source head: dbf43976d0b336c0df961a651f35e8b3ceca0255
squash commit: bfad12148e80c5f712b150851e9374db3a15a80b
```

The PR body literal is a manual transcription error.

The merge itself used the correct expected-head lock and the correct PR source head. Target main contains the exact accepted eight-file P1A result, so target-main correctness is unaffected.

P10K wording that the body was canonical is corrected: the body was bounded, but the head literal was not accurate.

Editing the closed merged PR body is not authorized by this record. Such metadata remediation would require separate approval.

```text
target_local_post_merge_validation: PENDING
P1B_entry_authorized: false
```