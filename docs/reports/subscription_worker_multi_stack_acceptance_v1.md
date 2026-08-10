# Subscription Worker Multi-Stack Acceptance v1

## Decision

This package validates the canonical `develop-execute` subscription-primary route against isolated Python and TypeScript repositories. It uses only injected fake Codex process I/O, temporary local Git repositories, temporary SQLite state, and bounded local validation commands. It creates no remote, provider, credential, downstream, production, cleanup, or rollback effect.

The exact package scope is five paths:

1. `src/tool_system/local_git/orchestrator.py`
2. `tests/test_task_runner.py`
3. `docs/reports/subscription_worker_multi_stack_acceptance_v1.md`
4. `examples/task_manifests/tool_system_subscription_worker_multi_stack_acceptance_v1.yaml`
5. `examples/change_plans/tool_system_subscription_worker_multi_stack_acceptance_v1.yaml`

## Parent and global alignment

The direct parent is `docs/reports/subscription_worker_public_entry_closure_specification_v1.md#Implementation packages`, package 3. The global target is `blueprint/tool_system_v0.yaml:product_objective`: bounded subscription-primary blueprint-to-code development with APIs default off and every remote or production effect separately authorized.

## Frozen acceptance matrix

| stack | implementation | failing-test repair | scope denial | cancellation | replay | local commit |
|---|---|---|---|---|---|---|
| Python | fake structured patch | current candidate supplied to bounded repair | out-of-scope patch blocks | returned patch discarded after cancellation | completed durable receipt resumes | exactly one, remote-free |
| TypeScript | fake structured patch plus local Node validation | current candidate supplied to bounded repair | out-of-scope patch blocks | returned patch discarded after cancellation | completed durable receipt resumes | exactly one, remote-free |

Every success must retain `api_mode_enabled=false`, zero provider invocations, zero provider-credential accesses, zero target mutations, zero remote operations, and a non-authorizing draft-PR plan. Every denial must occur before an unreceipted branch or commit.

## Replay correction boundary

The current public-entry preflight admits only creator-owned, clean, remote-free local workspaces. A clean workspace whose HEAD advanced beyond the frozen base may proceed only as `EXISTING_RECEIPT_RECONCILIATION_REQUIRED`; it receives no authority from that state. The durable local-Git owner must then match the exact completed branch and commit receipts. Missing, ambiguous, or mismatched receipts fail closed before a new branch or commit. Baseline workspaces retain their existing exact-head/tree path.

## Validation design

- Python validation runs only against the isolated candidate clone.
- TypeScript validation uses the Hosted runner's local Node executable and reads only the isolated candidate file; it performs no package install or network access.
- The fake Codex process writes one schema-bound structured patch to its creator-owned temporary result file.
- Repair scenarios require two worker calls and prove the second prompt carries the first cycle's candidate bytes.
- Cancellation is observed after the fake worker returns and before its patch is applied.
- Replay reuses the same manifest-bound workspace and durable state and must return the original commit without another worker call or commit.
- An unreceipted clean advanced workspace is a negative fixture and must block.

## Current status

The five-path acceptance package is frozen and pending implementation plus Hosted CI. This report is descriptive evidence only. It does not accept the public-entry milestone or authorize real Codex, ChatGPT Web automation, API/provider execution, credential access, downstream access, remote publication, production, cleanup, or rollback.
