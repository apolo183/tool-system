# P12C Side-Effect Ledger and Transactional Outbox

status: IMPLEMENTED_PENDING_CI
phase: P12_DURABLE_ORCHESTRATOR
parent: docs/reports/p12b_durable_state_foundation.md

## Single objective

Add local-fixture side-effect idempotency, completed markers, transactional outbox insertion, delivery leases, replay-safe receipts, and reconciliation without granting remote side-effect authority.

## Safety semantics

- schema version migrates from 1 to 2;
- side effects require the active task lease and exact expected precondition SHA;
- `resource_scope` is machine-limited to `local_fixture`;
- one idempotency key maps to exactly one effect content tuple;
- COMPLETED effect and PENDING outbox event commit in the same SQLite transaction;
- completed replay returns the stored record and never requests callback execution;
- IN_PROGRESS replay is ambiguous and fails closed for idempotency-key reconciliation;
- outbox delivery uses leases, durable attempt numbers, immutable receipts, and PENDING recovery;
- delivery callbacks receive the durable idempotency key and are limited by P12 evidence to local fixtures.

## Claim boundary

P12C does not make arbitrary external effects exactly-once. A crash after an external provider applies an action but before the local completion marker remains an ambiguity that requires provider idempotency or state lookup. P12 records and gates that ambiguity instead of blindly repeating it.

## Stop condition

After focused tests, full tests, active gates, CI, and merge pass, P12D may run only local crash/reopen/reconciliation fixtures.
