# P13C Durable-Orchestrator Fault and Resource Hardening

status: IMPLEMENTED_PENDING_CI
phase: P13_SECURITY_RELIABILITY_HARDENING
parent: docs/reports/p13b_adversarial_isolation_hardening.md

## Single objective

Harden the accepted single-host local SQLite durable orchestrator against database-path replacement, unsafe parent or sidecar objects, unbounded durable records, partial transaction failure, concurrent claims, and detectable integrity violations.

## Required implementation

- bind the database parent to its initial device/inode identity and reject later replacement;
- reject group/world-writable database parents, database symlinks, non-regular files, multi-link database files, and unsafe WAL/SHM/journal sidecars;
- revalidate path and file identity before and immediately after every SQLite connection, before any write-affecting PRAGMA;
- retain the first created database device/inode identity and reject regular-file substitution;
- add positive integer limits for durable text and canonical JSON byte size;
- require strings for text identifiers and finite JSON mappings with `allow_nan=false`;
- apply bounds before SQLite writes to ids, references, lease owners, checkpoints, payloads, results, events, and receipts;
- make schema creation/version update one explicit SQLite transaction while retaining schema version 2;
- expose a fail-closed integrity check covering both SQLite integrity and foreign-key consistency;
- preserve existing lease, retry, side-effect, outbox, expected-SHA, and reconciliation behavior.

## Exact file scope

```text
src/tool_system/orchestrator/durable.py
tests/test_durable_orchestrator_reliability.py
docs/reports/p13c_durable_orchestrator_fault_resource_hardening.md
examples/task_manifests/tool_system_p13c_durable_orchestrator_fault_resource_hardening.yaml
examples/change_plans/tool_system_p13c_durable_orchestrator_fault_resource_hardening.yaml
examples/active_gates.yaml
```

## Required evidence

Focused tests must prove:

1. normal state, side-effect, outbox, and reopen behavior remains compatible;
2. database symlink replacement, regular-file replacement, multi-link aliasing, parent replacement, and unsafe sidecars fail closed before state access;
3. oversized text/JSON, non-string text, non-mapping JSON, non-finite values, and invalid limits fail before SQLite mutation;
4. an injected outbox-insert abort rolls effect completion back to `IN_PROGRESS` with no event;
5. two concurrent claims yield exactly one active lease owner;
6. expired-lease recovery remains deterministic;
7. foreign-key corruption is detected by the integrity check;
8. random-byte database corruption fails closed;
9. no remote target, provider, finance-us, or production resource is touched.

## Claim boundary

P13C proves local single-host defensive checks and SQLite transaction behavior. It does not prove hostile filesystem-race immunity, encrypted storage, multi-host leases, distributed consensus, network database operation, arbitrary external exactly-once effects, or production readiness.

## Execution evidence

```text
database_parent_device_inode_bound: true
database_device_inode_bound: true
database_and_sidecar_symlink_nonregular_multilink_denial: true
regular_file_and_parent_substitution_denial: true
group_world_writable_parent_denial: true
max_text_bytes: enforced_before_mutation
max_record_bytes: enforced_before_mutation
canonical_json_mapping_and_finite_only: true
schema_initialization_transaction: explicit_begin_immediate
integrity_and_foreign_key_check: fail_closed
outbox_insert_fault_rolls_back_effect_completion: true
concurrent_claim_active_lease_winners: exactly_one
focused_tests: PASS_39
full_repository_tests: PASS_249
active_gates: PASS
remote_side_effect: false
target_repo_mutation: false
finance_us_mutation: false
production: false
```

The full local test run used the real resolved Python interpreter with the temporary environment's site-packages on `PYTHONPATH`. The environment manager's generated interpreter link resolved through a non-existent mount prefix and caused 23 infrastructure-only failures in subprocess and pinned-interpreter tests; the real-interpreter rerun passed all 249 tests without source changes.

## Stop condition

After focused tests, full tests, active gates, CI, and merge pass, proceed only to P13D integrated local attack/stress/recovery evidence. P14 remains unauthorized.
