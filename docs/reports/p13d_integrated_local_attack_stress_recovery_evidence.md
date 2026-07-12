# P13D Integrated Local Attack, Stress, and Recovery Evidence

status: EXECUTED_PENDING_CI
phase: P13_SECURITY_RELIABILITY_HARDENING
parent: docs/reports/p13a_security_reliability_phase_entry.md
implementation_parents:
  - docs/reports/p13b_adversarial_isolation_hardening.md
  - docs/reports/p13c_durable_orchestrator_fault_resource_hardening.md

## Single objective

Exercise the merged P13B and P13C natural owners together through temporary local attack, resource-pressure, cancellation, concurrency, and durable-recovery fixtures, and record bounded evidence without changing either source owner.

## Exact evidence scope

```text
tests/test_p13_integrated_security_reliability.py
docs/reports/p13d_integrated_local_attack_stress_recovery_evidence.md
examples/task_manifests/tool_system_p13d_integrated_local_attack_stress_recovery_evidence.yaml
examples/change_plans/tool_system_p13d_integrated_local_attack_stress_recovery_evidence.yaml
examples/active_gates.yaml
```

P13D is evidence-only. It must not change process-worker, durable-orchestrator, policy, blueprint, finance-us, remote-target, or production code/state.

## Required scenarios

1. executable substitution, outside-path access, link escape, secret-environment inheritance, network import, and process import remain fail closed;
2. file-size, descriptor, memory, CPU, stdout, and stderr pressure terminate or block the worker within bounded evidence;
3. repeated timeout and cancellation paths remove every ephemeral workspace;
4. concurrent task claims produce exactly one winner per task under repeated contention;
5. task and outbox leases recover after store reopen and expiry;
6. side-effect completion/outbox insertion remains atomic under injected failure;
7. foreign-key and file corruption remain detectable;
8. all P11-P12 regressions, full tests, active gates, and CI pass;
9. temporary artifacts created for local execution are removed by their creator.

## Claim boundary

This stage supplies repeatable local application-level evidence. It does not establish kernel sandboxing, hostile arbitrary-code containment, multi-host correctness, distributed exactly-once effects, remote-target safety, benchmark readiness, production readiness, or deployment authority.

## Execution evidence

```text
integrated_attack_stress_recovery_tests: PASS_15
process_worker_durable_orchestrator_integrated_suite: PASS_89
full_repository_tests: PASS_264
outside_path_link_network_process_probes: fail_closed_exit_126
alternate_executable: preflight_blocked
host_secret_like_environment_inherited: false
file_descriptor_memory_cpu_pressure: bounded_nonzero_exit
stdout_stderr_pressure: bounded_output_limit
timeout_cancellation_repetitions: PASS_3_each
workspace_cleanup_after_every_worker_run: true
concurrent_claim_rounds: 6
concurrent_claim_winners_per_round: exactly_one
task_and_outbox_lease_reopen_recovery: PASS
transactional_outbox_fault_rollback: PASS
foreign_key_and_file_corruption_detection: PASS
active_gates: PASS
dedicated_local_basetemp_removed_by_creator: true
source_changes: none
remote_target_mutation: false
finance_us_mutation: false
production: false
```

## Stop condition

After CI and merge pass, proceed only to P13E acceptance and closure. P14 remains unauthorized.
