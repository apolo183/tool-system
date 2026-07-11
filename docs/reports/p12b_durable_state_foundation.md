# P12B Durable State Foundation

status: IMPLEMENTED_PENDING_CI
phase: P12_DURABLE_ORCHESTRATOR
parent: docs/reports/p12a_durable_orchestrator_phase_entry.md

## Single objective

Implement SQLite-backed run/task state, lease ownership, checkpoints, retries, expired-lease recovery, and reopen/resume semantics without side effects or outbox behavior.

## Implementation evidence target

```text
schema_version: 1
foreign_keys: enabled
journal_mode: WAL
synchronous: FULL
busy_timeout: configured
run_task_state_survives_reopen: true
claim_increments_attempt_once: true
active_lease_owner_required: true
expired_lease_recovery: true
retry_exhaustion_terminal: true
expected_precondition_sha_persisted: true
remote_side_effect: false
target_repo_mutation: false
production: false
```

## Boundaries

P12B has no side-effect ledger, outbox publishing, reconciliation callback, remote worker, target repository, network database, or production service. P12C owns the next objective.

## Stop condition

After focused tests, full tests, active gates, CI, and merge pass, proceed to P12C only.
