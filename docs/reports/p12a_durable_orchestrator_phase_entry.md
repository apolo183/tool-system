# P12A Durable Orchestrator Phase Entry and Implementation Packet

status: ACTIVE
phase: P12_DURABLE_ORCHESTRATOR
parent: docs/reports/p11e_real_worker_runtime_acceptance_closure.md
authorized_by: user_continue_until_next_major_milestone

## Single objective

Enter P12 and lock the durable orchestration design, implementation owners, stage boundaries, evidence requirements, and stop condition. P12A changes governance only and creates no database or runtime state.

## Problem statement

P11 can run a bounded local fixture process, but orchestration state remains process-local. A crash can lose task status and can cause an external action to be repeated after restart. P12 must make state recovery and side-effect deduplication explicit before broader runtime use.

## Persistence boundary

P12 uses Python's standard-library `sqlite3` with local files created only under test or explicitly supplied local fixture roots. The natural owner is:

```text
src/tool_system/orchestrator/durable.py
```

SQLite must enable foreign keys, WAL journaling, busy timeout, explicit transactions, and a schema-version record. P12 does not introduce a network database, remote queue, target-repository write, provider call, or production service.

## P12B durable state foundation

Required tables and semantics:

- runs: stable run id, status, blueprint/manifest references, timestamps;
- tasks: run/task identity, status, attempt number, max attempts, idempotency key, checkpoint, expected precondition SHA;
- leases: owner and expiry bound transactionally to task claim;
- claim increments attempt exactly once;
- checkpoint/complete/fail requires the active lease owner;
- expired leases recover to READY only while attempts remain, otherwise FAILED;
- reopening the same database reconstructs state without in-memory authority.

P12B exact candidate paths:

```text
src/tool_system/orchestrator/__init__.py
src/tool_system/orchestrator/durable.py
tests/test_durable_orchestrator_state.py
docs/reports/p12b_durable_state_foundation.md
examples/task_manifests/tool_system_p12b_durable_state_foundation.yaml
examples/change_plans/tool_system_p12b_durable_state_foundation.yaml
examples/active_gates.yaml
```

## P12C side-effect and outbox foundation

Required semantics:

- globally unique idempotency key per logical side effect;
- side-effect ledger states PLANNED, IN_PROGRESS, COMPLETED, and FAILED;
- attempt number and expected precondition SHA stored with the effect;
- a completed-side-effect marker prevents a repeated callback;
- completion and outbox insertion occur in one SQLite transaction;
- outbox events have deterministic ids/idempotency keys and PENDING/PUBLISHED states;
- reconciliation may replay pending local fixture delivery but may not repeat completed side effects;
- mismatched payload, repository, action, or precondition SHA blocks deterministically.

P12C may modify the same natural owner and add focused ledger/outbox tests and stage records. Any unlisted natural owner requires a packet revision before writing.

## P12D execution evidence

Only local temporary SQLite and in-memory/local-file fixture sinks are allowed. Evidence must prove:

1. close/reopen preserves run, task, attempt, checkpoint, and lease state;
2. an expired lease is recovered and reclaimed with the next attempt number;
3. retry exhaustion becomes terminal FAILED;
4. duplicate idempotency registration returns the same logical record without duplicate effect;
5. mismatched duplicate content or expected SHA blocks;
6. a simulated crash after transactional effect completion but before outbox publication resumes pending delivery;
7. repeated reconciliation publishes an event at most once and never re-executes the completed effect;
8. no target repository, provider, network service, or production resource is touched.

## Stage sequence

```text
P12A phase entry and packet
  -> P12B durable run/task state
  -> P12C ledger/outbox/reconciliation
  -> P12D crash/replay fixture evidence
  -> P12E acceptance and closure
  -> stop at P13 authorization boundary
```

## Acceptance limits

P12 will not prove distributed consensus, multi-host leases, production database operation, hostile-node fault tolerance, remote side-effect safety, target-repository execution, or production readiness. Those claims remain outside P12.

## Rollback

Each stage uses one branch and squash PR. Rollback after merge requires a named revert PR. Database artifacts are temporary fixtures and must be cleaned by their creator. Branch cleanup remains separately gated.
