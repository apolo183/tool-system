# P13A Security and Reliability Hardening Phase Entry

status: ACTIVE
phase: P13_SECURITY_RELIABILITY_HARDENING
parent: docs/reports/p12e_durable_orchestrator_acceptance_closure.md
authorized_by: user_explicit_p13_full_lifecycle_authorization

## Single objective

Enter P13 and lock the threat model, abuse cases, implementation owners, short-stage sequence, evidence requirements, claim boundary, and P14 stop condition. P13A changes governance only and runs no worker or fault fixture.

## Protected assets and trust boundary

P13 protects:

- the host filesystem outside an ephemeral worker workspace;
- repository, credential, environment, and provider data unavailable to fixture workers;
- the exact allowlisted Python interpreter and snapshotted fixture entrypoint;
- worker process, output, file, memory, descriptor, process-count, CPU, time, cancellation, and cleanup limits;
- durable SQLite path identity, state transitions, transaction atomicity, bounded records, leases, and reconciliation state;
- the existing no-remote-target, no-finance-us, no-production boundary.

The worker remains trusted only for bounded fixture execution. Python audit hooks and resource limits are application-level defense in depth, not a hostile-code OS sandbox. P13 does not claim container, namespace, seccomp, VM, distributed-database, or production isolation.

## Read-only baseline findings

Current audit of `src/tool_system/agent_worker/process_runtime.py` found the P11 minimum baseline, plus specific P13 gaps:

1. the caller can override `python_executable` with any executable regular file;
2. entrypoint metadata is checked before a later pathname copy, leaving a replacement window;
3. the generated audit guard constrains `open` but does not comprehensively constrain filesystem mutation and directory-enumeration events;
4. `os.open` write flags are not interpreted by the current mode-only write check;
5. link creation is not denied, so a hard-link escape must be blocked;
6. `sysconfig.get_paths()` permits broader roots than the standard-library roots strictly required;
7. adversarial executable, link, environment, network, resource-exhaustion, cancellation-race, and cleanup evidence is incomplete.

Current audit of `src/tool_system/orchestrator/durable.py` found the accepted P12 single-host foundation, plus P13 reliability gaps:

1. database path and parent identity are checked at construction but not revalidated before every connection;
2. durable text and JSON records have no explicit byte bound;
3. schema initialization uses `executescript` inside a wrapper transaction without explicit fault-injection evidence;
4. transaction rollback, concurrent claim, database-integrity, lease-expiry race, and callback-failure recovery need stronger executable evidence.

These are bounded findings from the inspected natural owners and tests; they are not claims about uninspected OS-level containment.

## Abuse cases and required dispositions

| Abuse or fault | Required P13 disposition |
| --- | --- |
| substitute `/bin/sh` or another executable | pin to the resolved approved interpreter and block mismatch |
| replace/symlink entrypoint after preflight | no-follow snapshot with regular-file and size revalidation |
| read/list/mutate outside workspace through `os` APIs | comprehensive path-aware audit denial |
| hard-link or symlink escape | deny link creation in the worker |
| write through `os.open` flags | detect write flags and enforce workspace-only writes |
| import/use socket, subprocess, ctypes, or multiprocessing | preserve fail-closed import and audit denial with execution evidence |
| inherit or expose secret-like environment names | preserve minimal constructed environment and adversarially verify it |
| consume output, disk, descriptors, memory, CPU, processes, or wall time | bounded termination and cleanup evidence |
| race cancellation with process exit/output termination | one terminal status, process-group termination, bounded wait, cleanup |
| replace durable DB with symlink or different parent | revalidate path and parent identity before connection |
| oversized durable identifiers or JSON | deterministic byte bounds before SQLite write |
| fail between effect completion and outbox insert | rollback leaves no false completed marker |
| concurrent claim or expired-lease race | at most one active owner and deterministic recovery |
| corrupted SQLite file | integrity check fails closed with bounded evidence |

## Stage sequence

```text
P13A phase entry and threat model
  -> P13B process-worker adversarial isolation hardening
  -> P13C durable-orchestrator fault and resource hardening
  -> P13D integrated attack, stress, cancellation, and recovery evidence
  -> P13E security/reliability acceptance and closure
  -> stop at P14 authorization boundary
```

Each implementation stage may split a corrective substage if its evidence exposes a real gap. Such a correction must stay within the same P13 objective and use a new documented single-flight branch only after the prior branch is merged or formally disposed.

## P13B exact owner boundary

Candidate natural owners:

```text
src/tool_system/agent_worker/process_runtime.py
tests/test_process_worker_runtime_preflight.py
tests/test_process_worker_runtime_execution.py
tests/test_process_worker_runtime_adversarial.py
```

P13B must pin the interpreter, snapshot the entrypoint without following links, narrow readable library roots, enforce path-aware filesystem audit rules, deny links, preserve secret/network controls, and retain resource/cancellation cleanup. It may not introduce arbitrary executables, target repositories, remote providers, containers, privileged helpers, or production services.

## P13C exact owner boundary

Candidate natural owners:

```text
src/tool_system/orchestrator/durable.py
tests/test_durable_orchestrator_state.py
tests/test_durable_orchestrator_side_effects.py
tests/test_durable_orchestrator_reliability.py
```

P13C must revalidate database path identity, bound durable record size, expose a fail-closed integrity check, and prove transaction/concurrency/recovery behavior. It remains single-host and local-fixture only.

## P13D evidence boundary

P13D may execute only temporary local fixtures. Required evidence includes adversarial paths, executable substitution, link escape, environment/secret probes, network/process probes, file/descriptor/memory/CPU/output pressure, timeout/cancellation races, workspace cleanup, SQLite rollback injection, concurrent claims, integrity failure, lease recovery, and outbox reconciliation recovery.

## Acceptance and claim limits

P13 acceptance requires all P11-P12 regression tests, new adversarial/fault tests, active gates, CI, evidence records, and clean temporary-resource disposition. It accepts only application-guarded local fixture runtime and single-host local SQLite reliability hardening.

P13 does not prove hostile arbitrary-code containment, kernel-enforced network isolation, distributed consensus, remote target safety, multi-repository benchmark readiness, production readiness, production deployment, or Codex replacement.

## Rollback and stop condition

Each stage uses one branch and squash PR. Rollback after merge requires a named revert packet and PR; no reset or force-push. Test-created temporary roots are removed by their creator. Branch cleanup, including `dummy-unused`, remains separately gated.

After P13E is accepted and merged, stop. P14 phase entry, repository benchmarks, every target mutation, and production deployment require new explicit authorization.
