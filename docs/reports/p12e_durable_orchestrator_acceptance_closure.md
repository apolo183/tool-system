# P12E Durable Orchestrator Acceptance and Closure

status: ACCEPTED_CLOSED
phase: P12_DURABLE_ORCHESTRATOR
parent: docs/reports/p12d_crash_replay_fixture_evidence.md
validated_main: 3a4afb7ac7f3e922e782a12454e71012b880bf59

## Accepted objective

P12 is accepted as a single-host, local-fixture SQLite durable orchestrator that persists run/task state, leases, checkpoints, retries, expected precondition SHAs, side-effect records, completed markers, and a transactional outbox with reconciliation. P12 is closed only at this bounded scope.

## Merged evidence chain

```text
P12A_phase_entry_and_packet: 4f6731a473d947084b701d262c1d120dd675c51a
P12B_durable_state_foundation: 4a86ce4861f1d19ed553b90c1d2c36f9764a20e3
P12C_side_effect_ledger_outbox: b4180b3022f27922f0189d852858c0167b428348
P12D_crash_replay_fixture_evidence: 3a4afb7ac7f3e922e782a12454e71012b880bf59
```

## Acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| durable run and task state | schema v2 source and reopen fixtures | PASS |
| leases, checkpoints, retry, and crash resume | P12B state tests and P12D recovery tests | PASS |
| idempotency keys and attempt numbers | task/effect/outbox records and replay tests | PASS |
| side-effect ledger and completed markers | P12C ledger tests and P12D reopen evidence | PASS |
| transactional outbox | atomic completion/event test and persisted pending event | PASS |
| expected precondition SHA enforcement | task/effect validation and mismatch tests | PASS |
| reconciliation loop | failure requeue, lease recovery, and publish tests | PASS |
| publisher crash after local sink application | P12D persistent idempotent sink fixture | PASS: 2 callbacks, 1 logical application |
| completed logical effect not re-executed | completed replay and empty second reconciliation | PASS |
| ambiguous in-progress external state | fail-closed replay evidence | PASS |
| local fixture boundary | manifests, `resource_scope`, and tests | PASS |
| finance-us and remote targets unchanged | final fresh-state verification | PASS |

## Final validation

```text
post_P12D_full_pytest: PASS_219
active_gates: PASS
tool_system_main_matches_origin_main: PASS
tool_system_main: 3a4afb7ac7f3e922e782a12454e71012b880bf59
finance_us_main: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
dummy_unused_disposition: retain_pending_cleanup_approval
remote_side_effect: false
target_repo_mutation: false
production_deployment: false
```

## Acceptance limits

P12 does not accept or claim:

- arbitrary external exactly-once effects;
- distributed consensus or multi-host lease safety;
- network database or queue operation;
- hostile-node fault tolerance or P13 adversarial hardening;
- remote worker, provider, finance-us, or target-repository execution;
- multi-repository benchmark readiness;
- production readiness or deployment;
- Codex replacement.

## P13 boundary

```text
P12_status: accepted_and_closed
P13_roadmap_defined: true
P13_phase_entry_authorized: false
P13_implementation_authorized: false
```

The next possible milestone is P13 Security and Reliability Hardening. Entry requires a new explicit user authorization and a documentation-first P13 phase-entry record. This closure grants neither.

## Rollback

Rollback requires a named revert packet and revert PR. Do not reset or force-push main. Branch cleanup, including `dummy-unused`, remains separately gated.
