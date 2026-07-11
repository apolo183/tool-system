# P12D Crash, Reopen, and Replay Fixture Evidence

status: IMPLEMENTED_PENDING_CI
phase: P12_DURABLE_ORCHESTRATOR
parent: docs/reports/p12c_side_effect_ledger_outbox.md

## Single objective

Produce executable local-fixture evidence that P12 durable task state, lease recovery, retry exhaustion, completed-side-effect markers, and transactional-outbox reconciliation survive process loss without duplicating a completed logical effect.

## Evidence scenarios

1. Reopen the same temporary SQLite database and recover the run, task, attempt, checkpoint, and live lease.
2. Advance a deterministic fixture clock past a task lease, recover it, and reclaim it with the next attempt number.
3. Exhaust the configured attempt budget and prove the task becomes terminal `FAILED`.
4. Reopen after effect completion but before outbox publication and prove the completed marker and `PENDING` event remain durable.
5. Simulate a publisher crash after an idempotent local sink applies an event but before the outbox is marked published; expire the delivery lease, reopen, reconcile, and prove the sink's application count remains one.
6. Reconcile again and prove no published event is delivered again.
7. Reopen an ambiguous `IN_PROGRESS` effect and prove replay remains fail-closed.

## Fixture boundary

All databases and sink receipts live under pytest temporary directories. The sink is a local JSON receipt file keyed by the durable event idempotency key. No network client, provider, remote repository, finance-us path, production resource, or P11 process worker is invoked.

## Claim boundary

The fixture proves single-host SQLite recovery plus idempotent local-sink reconciliation. It does not prove arbitrary external exactly-once effects, distributed consensus, multi-host operation, production readiness, or P13 hardening.

## Execution evidence

```text
focused_recovery_tests: 7 passed
full_repository_tests: 219 passed
active_gate_validation: PASS
run_task_checkpoint_lease_survive_reopen: true
expired_task_lease_reclaimed_at_next_attempt: true
retry_exhaustion_terminal: true
completed_effect_and_pending_event_survive_reopen: true
publisher_crash_fixture_callback_attempts: 2
publisher_crash_fixture_logical_sink_applications: 1
published_event_second_reconciliation: no_delivery
ambiguous_in_progress_replay: fail_closed
runtime_source_modified: false
remote_side_effect: false
target_repo_mutation: false
production_resource: false
```

## Stop condition

After focused tests, full tests, active gates, CI, and merge pass, P12E may perform acceptance and closure only. P13 remains unauthorized.
