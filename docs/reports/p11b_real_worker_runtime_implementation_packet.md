# P11B Real Worker Runtime Implementation Packet

status: AUTHORIZED_FOR_P11C_IMPLEMENTATION
phase: P11_REAL_WORKER_RUNTIME
parent: docs/reports/p11a_successor_roadmap_phase_entry.md
implementation_base: fresh main after P11B merge

## Single objective

Define the exact natural-owner design, safety preconditions, file scope, tests, evidence, and stop conditions for P11C. P11B is documentation-only and executes no worker.

## Runtime boundary

P11 implements one local Python process-backed fixture worker. It is not a general hostile-code sandbox, a remote agent provider, a target-repository executor, or a production runtime.

The natural owner is `src/tool_system/agent_worker/process_runtime.py`. Existing `NoMutationAgentWorker` behavior remains the default and is not silently replaced.

## Required request contract

The request must bind:

```text
request_id
entrypoint
allowed_fixture_root
workspace_root
forbidden_roots
network_mode=disabled
writes_target_repo=false
executes_target_repo_mutation=false
production=false
limits
```

Missing or mismatched fields block before `Popen`.

## Minimum safety baseline

### Workspace and path controls

- create one ephemeral workspace under an explicit workspace root;
- reject a workspace root inside the repository or any forbidden root;
- accept only regular, non-symlink entrypoints resolved under the exact fixture root;
- copy the approved fixture into the workspace under a generated safe name;
- use the workspace as cwd and delete it after every result, including failure, timeout, cancellation, or overflow;
- reject path traversal, symlink escape, device files, and oversized fixture input.

### Executable, environment, and secret controls

- execute an argv list with `shell=False`;
- use only the exact resolved Python executable configured by the runtime;
- start Python in isolated, no-site, no-bytecode mode;
- build a new minimal environment instead of inheriting `os.environ`;
- expose no caller-provided environment override in P11;
- reject or omit secret-like environment names and record the emitted environment-name allowlist.

### Network and child-process controls

- require `network_mode=disabled`;
- install a Python audit guard before loading the fixture;
- deny socket, subprocess, `os.system`, spawn, fork, and exec audit events;
- deny worker file opens outside its workspace except runtime-required read-only standard-library roots;
- fail closed if the guard cannot be installed;
- report this as an application-level Python guard, not an OS namespace or hostile-code sandbox.

### Resource, output, timeout, and cancellation controls

- apply RLIMIT_CPU, RLIMIT_AS, RLIMIT_NPROC, RLIMIT_NOFILE, RLIMIT_FSIZE, and RLIMIT_CORE where supported;
- create a new process session and restrictive umask;
- drain stdout and stderr incrementally with independent byte caps;
- kill the process group on timeout, cancellation, or output overflow;
- wait for termination and return deterministic `PASS`, `BLOCK`, `TIMEOUT`, `CANCELLED`, or `OUTPUT_LIMIT` status;
- record duration, exit code, byte counts, hashes, enforced limits, guard mode, and workspace deletion without recording secrets.

## P11C exact implementation allowlist

```text
src/tool_system/agent_worker/process_runtime.py
src/tool_system/agent_worker/__init__.py
tests/test_process_worker_runtime_preflight.py
docs/reports/p11c_isolated_process_worker_implementation.md
examples/task_manifests/tool_system_p11c_isolated_process_worker.yaml
examples/change_plans/tool_system_p11c_isolated_process_worker.yaml
examples/active_gates.yaml
```

P11C tests may mock the process launcher but must not start the real fixture worker. If another source owner is required, revise this packet before writing it.

## P11D execution stage

P11D may add the exact fixture and real-execution tests only after P11C is merged and fresh-state validation proves the baseline source is on main. P11D must first run the preflight-only tests, then perform one bounded fixture execution. It must not point the runtime at repository source, finance-us, another remote target checkout, or production data.

Planned P11D paths:

```text
tests/fixtures/p11_worker_fixture.py
tests/test_process_worker_runtime_execution.py
docs/reports/p11d_fixture_worker_execution_evidence.md
examples/task_manifests/tool_system_p11d_fixture_worker_execution.yaml
examples/change_plans/tool_system_p11d_fixture_worker_execution.yaml
examples/active_gates.yaml
```

## Required P11C tests

At minimum prove without starting a real worker:

1. valid fixture roots and safe entrypoints pass preflight;
2. traversal, symlink, non-file, outside-root, repository-root, and oversized entrypoints block;
3. target mutation, production, or enabled network flags block;
4. executable is exact and argv uses no shell;
5. the environment is rebuilt and secret-like names are absent;
6. all required resource limits are represented;
7. timeout, cancellation, and output overflow select process-group termination;
8. workspace cleanup is mandatory for every terminal status;
9. audit events for network, child process, and outside-workspace file access block;
10. existing no-mutation worker remains the default.

## P11C verification

```text
git diff --check
python -m compileall src/tool_system tests
python -m pytest -q tests/test_process_worker_runtime_preflight.py
python -m pytest -q
python -m tool_system.cli.validate_active_gates examples/active_gates.yaml
```

## Preserved boundaries

- no real worker process in P11B or P11C;
- no finance-us or other remote target mutation;
- no remote worker/provider call;
- no production deployment;
- no P12 implementation;
- no cleanup or branch deletion;
- no hostile-code sandbox, Codex-replacement, or production-readiness claim.

## Rollback and stop

Each stage uses one branch and squash PR. Before merge, rollback is PR closure with retained head evidence. After merge, rollback requires a named revert PR. After P11B merge, proceed to P11C only; do not execute the fixture worker until P11C is merged and P11D preflight passes.
