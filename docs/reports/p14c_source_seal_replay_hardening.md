# P14C Current-Source Seal and Replay Hardening Evidence

Status: `SOURCE_HARDENED_FAKE_IO_ONLY_NO_EXECUTION_NOT_ACCEPTED`

## Authority and alignment

- authorization: `P14C-SOURCE-SEAL-REPLAY-LIFECYCLE-v1`
- repository: `apolo183/tool-system`
- implementation base: `2c325f20f4c7a2b531725463b98572dee5f70967`
- implementation base tree: `d0f5d0d2aed812e4478752b828c0d1772ae93ea7`
- parent: `docs/reports/p14c_live_issuer_implementation.md`, residual
  current-source and cross-process replay blockers
- global objective: `blueprint/tool_system_v0.yaml:product_objective`
- P14C objective: one bounded provider path with exact authorization, secret,
  network, budget, validation, and audit controls and no repository mutation

This evidence covers source hardening only. It does not create external
authority, execute a provider, accept P14C, or enter P14D.

## Implemented boundary

Approval schema `p14c-live-execution-approval-v2` fails approval v1 closed and
binds all existing packet, request, provider, transport, budget, and denied
authority fields plus:

- the exact clean execution commit and tree;
- a canonical SHA-256 manifest over the fixed P14C critical runtime sources;
- `clean_worktree: true` measured from Git rather than supplied as PASS input;
- the actual execution host name;
- one immutable random durable-ledger instance identity.

The issuer validates the canonical tool-system origin, exact Git top level,
commit, tree, clean status, and regular non-symlink critical files before any
GitHub approval read. The provider capability remeasures the same seal during
binding and immediately before every credential access. Missing files,
symlinks, dirty state, source-byte drift, wrong commit or tree, a different
host, or a different ledger fails closed.

## Durable replay semantics

`durable-orchestrator-api@1.1.0` owns SQLite schema v3 and a generic
authorization-consumption record. Each record binds approval source,
repository, external record ID, authorization ID, approval digest, binding
digest, execution host, ledger identity, expiry, and consumption time.

Consumption uses one `BEGIN IMMEDIATE` transaction and a unique external-record
identity. A committed claim is deliberately not released: if capability
construction or the caller crashes afterward, the approval stays burned and a
fresh external approval is required. Reopen and two-process race tests prove
single-host at-most-once authorization consumption. They do not prove
multi-host global replay prevention, exactly-once provider completion, or
recovery of an already burned approval.

## Validation and side-effect evidence

All approval and provider I/O in this change is injected fake I/O. SQLite files
are created only beneath pytest temporary directories. Source-seal tests use
temporary local Git fixtures with no fetch or push.

- real approval comments created or edited: `0`
- real GitHub approval reads: `0`
- credential-value accesses: `0`
- real provider calls: `0`
- downstream repository reads or writes: `0`
- production operations: `0`
- cleanup, rollback, or branch-deletion operations: `0`

The focused suite covers approval v2 exactness, source commit/tree/manifest,
dirty/missing/symlink drift, host and ledger mismatch, schema v2-to-v3
migration, reopen replay, cross-process race, burn-on-claim behavior, and
pre-credential revalidation. The full repository suite and machine validators
remain required gates for publication; their exact run results belong to the
pull-request and CI evidence, not to execution authority.

## Remaining blockers

- no real GitHub owner approval record has been created or read;
- no credential value has been accessed;
- no real provider call or provider receipt exists;
- the single-host ledger is not a distributed replay service;
- hostile in-process code, host-name spoofing, and a compromised local machine
  remain outside this source-only threat model;
- P14C acceptance, P14D, downstream mutation, production, cleanup, rollback,
  and branch deletion remain unauthorized.

Therefore this hardening closes the previously identified source-binding and
single-host cross-process replay gaps but does not accept P14C or establish live
execution evidence.
