# Subscription Worker Multi-Stack Acceptance v2

## Decision

This package implements package 3 of the accepted public-entry closure specification as a test-and-evidence-only acceptance layer. It validates the canonical `develop-execute` subscription-primary route against isolated Python and TypeScript repositories using injected fake Codex process I/O, temporary remote-free local Git repositories, temporary SQLite state, and bounded local validation commands.

It creates no API, provider, credential, downstream, remote, production, cleanup, or rollback effect and does not change runtime code.

## Predecessor and correction boundary

Draft PR #216 was stopped fail closed because it bundled an unsealed runtime change and exposed completed-run replay ordering failure. PR #217 corrected that defect in the local-Git natural owner, passed Hosted CI, and was squash merged as canonical commit `983e225377fdef23a18368c9e662f8231d6aaec8`.

This v2 package begins from that canonical commit. It reuses only the fake-I/O acceptance scenarios; it does not carry forward PR #216's runtime diff or claim its failed evidence.

## Frozen boundary

The exact package scope is four paths:

1. `docs/reports/subscription_worker_multi_stack_acceptance_v2.md`
2. `examples/change_plans/tool_system_subscription_worker_multi_stack_acceptance_v2.yaml`
3. `examples/task_manifests/tool_system_subscription_worker_multi_stack_acceptance_v2.yaml`
4. `tests/test_task_runner.py`

The direct parent is `docs/reports/subscription_worker_public_entry_closure_specification_v1.md#Implementation packages`, package 3. The global target remains `blueprint/tool_system_v0.yaml:product_objective`.

## Frozen acceptance matrix

| stack | implementation | failing-test repair | scope denial | cancellation | replay | local commit |
|---|---|---|---|---|---|---|
| Python | fake structured patch | current candidate supplied on bounded cycle two | out-of-scope patch blocks | returned patch discarded after cancellation | completed receipt resumes | exactly one, remote-free |
| TypeScript | fake structured patch plus local Node validation | current candidate supplied on bounded cycle two | out-of-scope patch blocks | returned patch discarded after cancellation | completed receipt resumes | exactly one, remote-free |

Every success must retain `api_mode_enabled=false`, zero provider invocations, zero provider-credential accesses, zero target mutations, zero remote operations, and a non-authorizing draft-PR plan. Every denial must occur before an unreceipted branch or commit.

## Validation design

- Python validation runs only against the isolated candidate clone.
- TypeScript validation uses only the Hosted runner's local Node executable; it performs no install, download, or network operation.
- The fake Codex process writes one schema-bound structured patch to a creator-owned temporary result file.
- Repair scenarios require two fake worker calls and prove the second prompt carries the first cycle's candidate bytes.
- Cancellation is observed after the fake worker returns and before its patch is applied.
- Replay reuses the exact manifest-bound workspace and durable state, returns the original commit, and performs no second worker or commit effect.
- An unreceipted advanced workspace remains a negative fail-closed fixture.

## Current status

The exact four-path acceptance package passed Hosted CI run 1301 (job 93646242827): 844 tests passed, followed by active-gate, process-authority, current-registry-authority, and repository-manifest validation. It remains pending final no-drift Ready and squash merge. This report is descriptive evidence only. It does not accept the final public-entry milestone or authorize real Codex execution, ChatGPT Web automation, API/provider calls, credential access, downstream access, remote publication, production, cleanup, or rollback.
