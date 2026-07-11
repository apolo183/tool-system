# P11C Isolated Process Worker Implementation

status: IMPLEMENTED_NOT_EXECUTED
phase: P11_REAL_WORKER_RUNTIME
parent: docs/reports/p11b_real_worker_runtime_implementation_packet.md

## Single objective

Implement the fail-closed P11 process-worker safety baseline and prove its preflight behavior without starting a real worker process.

## Implementation

- `ProcessWorkerRequest`, limits, preflight, result, and execution contracts are owned by `src/tool_system/agent_worker/process_runtime.py`.
- Entry points must be regular non-symlink files under an exact fixture root.
- Workspaces are ephemeral and must be outside explicit forbidden roots.
- Python execution uses exact argv, isolated/no-site/no-bytecode flags, `shell=False`, a rebuilt environment, process session, and resource limits.
- The generated Python audit guard denies network, child process, blocked imports, and outside-workspace file access.
- Output is drained incrementally with caps; timeout, cancellation, or overflow kills the process group.
- The existing `NoMutationAgentWorker` remains the default.

## Claim boundary

The guard is an application-level Python safety control for an allowlisted fixture, not an OS namespace, virtual machine, container boundary, hostile-code sandbox, production runtime, or remote target executor.

## P11C evidence target

```text
real_worker_process_started: false
preflight_tests: PASS
full_tests: PASS
active_gates: PASS
finance_us_mutated: false
other_remote_target_mutated: false
production_deployed: false
```

## Stop condition

After this exact implementation PR passes CI and merges, P11D must fresh-state verify the source on main, run preflight-only tests first, and only then execute the allowlisted fixture worker.
