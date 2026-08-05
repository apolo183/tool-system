# Durable-orchestrator SQLite sidecar race correction

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_RELIABILITY_CORRECTION`

This record closes one observed single-host SQLite reliability defect without
changing tool-system phase acceptance or execution authority. Hosted CI run
`30973696797` first failed when one authorization-consumption process observed a
WAL sidecar and SQLite removed it before the following `lstat`. A deterministic
local probe reproduced the same uncaught `FileNotFoundError`.

## Frozen baseline and single-module boundary

- repository: `apolo183/tool-system`
- canonical baseline: `783a1bf16c48e717da281d9fefc134e68bf879c4`
- canonical tree: `5d3651587e973b8ac226298bf7c1b65f51838059`
- durable module: `durable_orchestrator` `1.1.0` to `1.2.0`
- aggregate interface: `durable-orchestrator-api` `1.1.0` unchanged
- schema version: `3` unchanged
- natural owner modified: `src/tool_system/orchestrator/durable.py`

The correction is interface-compatible. It changes only validation of SQLite's
optional `-wal`, `-shm`, and `-journal` files. A sidecar that disappears before
one atomic `lstat`, or whose already observed regular-file metadata has zero
remaining directory links during unlink, is treated as absent. Every observed
symlink, non-regular file, or sidecar with more than one hard link still blocks.
The database file itself still requires exactly one hard link and retains its
device/inode identity checks.

## Deterministic and concurrent evidence

Two deterministic tests cover both legal disappearance forms: an `lstat`
`FileNotFoundError` and regular sidecar metadata with `st_nlink == 0`. Existing
negative coverage is extended to prove sidecar symlinks and multi-link sidecars
still fail closed. The original two-process authorization race remains the
integration check and is stressed repeatedly against temporary fixture stores.

This package does not change task, lease, authorization-consumption, outbox,
transaction, database-schema, record-shape, retry, or replay behavior. It does
not claim immunity from a hostile same-user filesystem actor or multi-host
exactly-once operation.

## Authority and phase boundary

The correction consumes no credential or private target, calls no provider or
network, mutates no downstream repository, and performs no benchmark,
production, cleanup, or rollback operation. Recharge and Qwen funding remain
deferred. P15C remains unaccepted, formal P15D remains unentered and unaccepted,
and P15E remains unauthorized.

## Validation and terminal boundary

The candidate must pass deterministic sidecar-race regression tests, repeated
cross-process authorization contention, the durable-orchestrator owner and
consumer closure, module-contract, import-graph, registry, repository-manifest,
project-state and phase-alignment suites, the full pytest suite, Python
compilation, Ruff 0.16.0, exact twelve-path and forbidden-diff checks, Hosted CI,
and unchanged base/head/scope guards before Ready and squash merge.

Pre-freeze diagnosis reproduced the prior failure deterministically. After the
source correction, all 16 durable reliability tests, 25 consecutive
independent-process contention repetitions, 226 focused owner/consumer and
governance tests, and 703 full-suite tests passed. Python compilation and every
governance validator passed. Ruff 0.16.0 differential checking produced exactly
the nine baseline diagnostics and no new diagnostic. Exact-scope, forbidden-
diff, secret, and project-neutrality checks passed. Hosted CI remains the
publication-time gate rather than a local claim in this record.

- provider_invocations: 0
- credential_resolver_invocations: 0
- credential_value_accesses: 0
- network_operations: 0
- private_target_reads: 0
- target_repository_accesses: 0
- target_mutations: 0
- benchmark_executions: 0
- production_operations: 0
- cleanup_operations: 0
- rollback_operations: 0
- p15c_stage_accepted: false
- p15d_stage_entered: false
- p15d_stage_accepted: false
- p15e_authorized: false
