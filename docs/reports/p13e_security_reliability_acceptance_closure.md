# P13E Security and Reliability Hardening Acceptance and Closure

status: ACCEPTED_CLOSED
phase: P13_SECURITY_RELIABILITY_HARDENING
parent: docs/reports/p13d_integrated_local_attack_stress_recovery_evidence.md
validated_main: 76ae268bb703aec32be15a6214a0edc83c23e390

## Accepted objective

P13 is accepted only as application-guarded local Python fixture-worker hardening and single-host local-fixture SQLite durable-orchestrator hardening, supported by adversarial, resource-pressure, cancellation, fault-injection, concurrency, integrity, and recovery evidence. P13 is closed at this bounded scope.

## Merged evidence chain

```text
P13A_phase_entry_threat_model: aa5722a55ab2d8fb94d8f85c7666573531cdc92d
P13B_process_worker_adversarial_hardening: 6e518c240ff1a23ccbe1ccce9e555328d54a55ba
P13C_durable_orchestrator_fault_resource_hardening: c64ec9419cc450d1072079faea939592ef18972e
P13D_integrated_local_attack_stress_recovery_evidence: 76ae268bb703aec32be15a6214a0edc83c23e390
```

## Acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| threat model and abuse cases | P13A inventory and owner boundaries | PASS |
| exact interpreter and entrypoint identity | P13B resolved interpreter plus no-follow device/inode/size/mtime/SHA binding | PASS |
| path, link, environment, network, and process controls | P13B adversarial probes and P13D integrated probes | PASS |
| immediate uncatchable audit denial | dedicated one-probe worker exits 126 | PASS |
| resource and output limits | P13D file/descriptor/memory/CPU/stdout/stderr pressure | PASS |
| timeout, cancellation, process-group termination, cleanup | repeated P13D execution and empty workspace roots | PASS |
| database parent/file/sidecar identity | P13C substitution, symlink, non-regular, and multi-link tests | PASS |
| bounded finite durable records | P13C text/JSON pre-mutation validation | PASS |
| transaction fault rollback | injected outbox abort retains `IN_PROGRESS` and inserts no event | PASS |
| concurrent claims | six P13D contention rounds, exactly one winner each | PASS |
| lease and outbox recovery | reopen, expiry, reconciliation, and publish evidence | PASS |
| integrity and corruption detection | foreign-key and random-byte corruption fail closed | PASS |
| P11-P12 regression compatibility | integrated owner suite and full repository suite | PASS |
| finance-us, remote targets, and production unchanged | fresh-state and execution-boundary verification | PASS |

## Final validation

```text
post_P13D_integrated_tests: PASS_15
post_P13D_owner_suite: PASS_89
post_P13D_full_pytest: PASS_264
P13E_phase_alignment_tests: PASS_2
P13E_full_pytest: PASS_264
active_gates: PASS
tool_system_main_matches_origin_main: PASS
tool_system_main: 76ae268bb703aec32be15a6214a0edc83c23e390
finance_us_main: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
dummy_unused_disposition: retain_pending_cleanup_approval
dedicated_P13D_basetemp_removed_by_creator: true
P13_session_venv_cache_and_final_basetemp_removed_by_creator: true
remote_side_effect: false
target_repo_mutation: false
production_deployment: false
```

## Acceptance limits

P13 does not accept or claim:

- hostile arbitrary-code containment or kernel-enforced sandboxing;
- OS network namespaces, seccomp, containers, or virtual-machine isolation;
- encrypted durable storage or hostile-filesystem race immunity;
- distributed consensus, multi-host leases, or arbitrary external exactly-once effects;
- remote worker/provider or target-repository execution safety;
- multi-repository benchmark or release-candidate readiness;
- production readiness, sustainable production operations, or deployment;
- Codex replacement.

## P14 boundary

```text
P13_status: accepted_and_closed
P14_roadmap_defined: true
P14_phase_entry_authorized: false
P14_repository_benchmarks_authorized: false
P14_target_mutation_authorized: false
P15_phase_entry_authorized: false
production_deployment_authorized: false
```

The next possible milestone is P14 Multi-repo Benchmark. P14 phase entry requires a new explicit user authorization, and each repository mutation remains separately authorized. This closure grants neither P14 work nor production authority.

## Rollback

Rollback requires a named revert packet and revert PR. Do not reset or force-push main. Branch cleanup, including `dummy-unused`, remains separately gated.
