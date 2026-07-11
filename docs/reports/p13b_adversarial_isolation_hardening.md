# P13B Process-Worker Adversarial Isolation Hardening

status: IMPLEMENTED_PENDING_CI
phase: P13_SECURITY_RELIABILITY_HARDENING
parent: docs/reports/p13a_security_reliability_phase_entry.md

## Single objective

Harden the accepted local Python process worker against executable substitution, entrypoint replacement, filesystem/link escape, environment leakage, network/process side effects, and over-broad library reads while preserving its bounded fixture-only behavior.

## Required implementation

- pin execution to the resolved current Python interpreter;
- require disjoint fixture and workspace roots;
- snapshot the entrypoint through a no-follow descriptor and bind runtime execution to its preflight device, inode, size, modification time, link count, and SHA-256;
- reject symlink and multi-link entrypoints;
- read only the `stdlib` and `platstdlib` roots required by isolated Python;
- upgrade the generated audit guard to interpret both mode and flags for `open`;
- terminate immediately on a denied audit event so worker code cannot catch the denial and inspect the audit-hook traceback;
- allow writes and filesystem mutation only inside the ephemeral workspace;
- deny symlink and hard-link creation;
- deny outside directory enumeration and path mutation;
- deny process signalling, process creation, remote debugging, system logging, and network/library events;
- retain the constructed secret-free environment, hard resource limits, process-group termination, bounded output, and workspace deletion.

## Exact file scope

```text
src/tool_system/agent_worker/process_runtime.py
tests/test_process_worker_runtime_preflight.py
tests/test_process_worker_runtime_execution.py
tests/test_process_worker_runtime_adversarial.py
tests/fixtures/p11_worker_fixture.py
docs/reports/p13b_adversarial_isolation_hardening.md
examples/task_manifests/tool_system_p13b_adversarial_isolation_hardening.yaml
examples/change_plans/tool_system_p13b_adversarial_isolation_hardening.yaml
examples/active_gates.yaml
```

## Acceptance evidence

The accepted success fixture is updated to exercise permitted behavior only; denied behavior moves to dedicated one-probe-per-process adversarial fixtures because a denial now terminates the worker immediately. Focused tests must prove the safe fixture still passes and each of the following fails closed: alternate executable, nested roots, symlink/multi-link entrypoint, post-preflight replacement, outside list/remove/write, `os.open` write flags against a library path, link escape, process signal, socket/process import, and secret-like environment inheritance.

## Claim boundary

P13B is application-level CPython audit and Unix resource hardening. It is not kernel-enforced hostile-code containment, a container, namespace, seccomp profile, VM, remote worker, target-repository executor, or production service.

## Execution evidence

```text
guard_mode: python_audit_guard_v2
approved_interpreter_pinned: true
entrypoint_no_follow_identity_and_sha_binding: true
multi_link_entrypoint_blocked: true
fixture_workspace_roots_disjoint: true
readable_library_roots: stdlib_and_platstdlib_only
open_mode_and_write_flags_enforced: true
link_creation: denied
outside_enumeration_and_mutation: denied
network_process_signal_remote_debug_and_syslog: denied
denial_catchable_by_worker: false_process_exits_126
host_secret_like_environment_inherited: false
focused_tests: PASS_35
full_repository_tests: PASS_236
active_gates: PASS
remote_side_effect: false
target_repo_mutation: false
production: false
```

The first local focused execution exposed that Python 3.12 `runpy` legitimately emits `sys._getframemodulename` before worker code. P13B permitted that module-name-only event while retaining immediate termination for frame-object access such as `sys._getframe`; local tests then passed.

GitHub CI #913 subsequently proved Python 3.11 `runpy.run_path` calls `sys._getframe` during its own bootstrap. All 15 CI failures exited 126 before fixture behavior, active gates were skipped, and no external state changed. P13B did not weaken the frame-object denial. Instead, the guard now reads and compiles the already no-follow/SHA-bound local worker snapshot before installing the audit hook, then directly executes that code after the hook is active.

Replacement CI #915 then passed 235 of 236 tests and proved that Python 3.11's `json` import also uses `sys._getframe`. All dedicated adversarial tests passed. Allowing stdlib-originated frame access would let worker code call a stdlib helper to obtain a frame, so P13B again retained the denial. The success fixture now verifies its permitted environment with builtins and the already-preloaded `os` module, then emits fixed JSON without importing `json`; import and denial behaviors remain isolated in one-probe-per-process tests. Final local and replacement CI results supersede both failed runs.

## Stop condition

After focused tests, full tests, gates, CI, and merge pass, proceed to P13C durable-orchestrator hardening only. P14 remains unauthorized.
