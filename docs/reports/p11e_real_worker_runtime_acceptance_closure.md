# P11E Real Worker Runtime Acceptance and Closure

status: ACCEPTED_CLOSED
phase: P11_REAL_WORKER_RUNTIME
parent: docs/reports/p11d2_termination_path_execution_evidence.md
validated_main: a9dc1a93d0b40e47efb82037b65bd5425bdd19f8

## Accepted objective

P11 is accepted only as a real local Python process-backed worker for allowlisted fixtures inside ephemeral workspaces with a fail-closed application-level safety baseline. P11 is closed after successful and abnormal execution evidence.

## Merged evidence chain

```text
P11A_roadmap_phase_entry: 4fa2738bce9316d46348bb20a9d5856930a88950
P11B_implementation_packet: 6d9c915350aed0b656a15d5f7efae59f51a5ec39
P11C_safety_implementation: e1a4d165a406ac834db48edf9fca4550bb3af46a
P11D_successful_fixture_evidence: 50f7d4efce0e673fcca3c3825598ae77d2fd778c
P11D2_termination_evidence: a9dc1a93d0b40e47efb82037b65bd5425bdd19f8
```

## Acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| exact allowlisted Python executable and argv, no shell | P11C preflight and source | PASS |
| regular non-symlink fixture under exact root | P11C preflight tests | PASS |
| ephemeral workspace outside forbidden repositories | P11D execution | PASS |
| scrubbed environment without secret-like names, HOME, or PATH | P11D fixture payload | PASS |
| network and child-process application guard | socket/subprocess imports blocked in P11D | PASS |
| outside-workspace read denied | `/etc/passwd` fixture probe blocked | PASS |
| CPU, memory, process, open-file, file-size, and core limits | P11C source and preflight record | PASS |
| bounded stdout/stderr | P11D2 output-overflow execution | PASS |
| wall timeout and process-group kill | P11D2 timeout execution | PASS |
| cancellation and process-group kill | P11D2 cancellation execution | PASS |
| workspace deletion on success and abnormal termination | P11D/P11D2 execution | PASS |
| existing no-mutation worker remains default | P11C regression test | PASS |
| finance-us and other remote targets unchanged | remote fresh-state checks | PASS |
| no production deployment | execution manifests and evidence | PASS |

## Final validation

```text
post_P11D2_full_pytest: PASS_193
active_gates: PASS
tool_system_main_matches_origin_main: PASS
finance_us_main: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
dummy_unused_disposition: retain_pending_cleanup_approval
worker_workspace_residue: none
```

## Acceptance limits

P11 does not accept or claim:

- hostile or untrusted code containment;
- OS network namespaces, containers, or virtual-machine isolation;
- arbitrary executable support;
- remote agent/provider calls;
- finance-us or other target-repository execution;
- durable state, leases, retries, resume, idempotency, or side-effect ledgers;
- multi-repository benchmark readiness;
- production readiness or deployment;
- Codex replacement.

## P12 boundary

```text
P11_status: accepted_and_closed
P12_roadmap_defined: true
P12_phase_entry_authorized: false
P12_implementation_authorized: false
```

The next possible milestone is P12 Durable Orchestrator. Entry requires a new explicit user authorization and a documentation-first P12 phase-entry record. This closure grants neither.

## Rollback

Rollback requires a named revert packet and revert PR. Do not reset or force-push main. Branch cleanup, including `dummy-unused`, remains separately gated.
