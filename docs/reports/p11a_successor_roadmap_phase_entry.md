# P11A Successor Roadmap and Phase Entry

status: ACTIVE
phase: P11_REAL_WORKER_RUNTIME
parent: docs/reports/p10r_c_post_merge_closure.md
requirement_source: user authorization on 2026-07-11

## Single objective

Register P11-P15 as the authorized successor roadmap and enter P11 only. This stage changes governance contracts; it does not implement or execute a worker.

## Roadmap

1. P11 Real Worker Runtime: one local process-backed worker, fixture-only, after a fail-closed minimum safety baseline passes.
2. P12 Durable Orchestrator: durable state, leases, resume, idempotency, side-effect ledger, transactional outbox, precondition SHA, and reconciliation.
3. P13 Security and Reliability Hardening: adversarial testing, stronger isolation, resource stress, and fault injection.
4. P14 Multi-repo Benchmark: separately authorized non-production repository benchmarks and release-candidate evidence.
5. P15 Production Operations and Acceptance: releases, migrations, recovery, SLOs, incidents, retention, cost, outage fallback, runbooks, and final acceptance decision.

Only P11 is active. Each later milestone requires separate phase-entry authorization.

## P11 minimum safety gate

Before the first real worker process starts, evidence must show:

- an ephemeral workspace outside every target repository;
- an exact executable and input allowlist;
- a scrubbed environment with no inherited secrets;
- cwd, path traversal, regular-file, and symlink controls;
- network disabled by a fail-closed worker policy;
- CPU, memory, process, open-file, file-size, runtime, and output limits;
- cancellation and process-group force termination;
- no remote target-repository mutation capability;
- no production deployment capability.

If the host cannot provide a claimed isolation control, runtime execution must fail closed or the claim must be narrowed before execution. P11 does not claim hostile-code sandboxing or production readiness.

## P11 staged path

```text
P11A roadmap and phase entry
  -> P11B implementation packet and safety acceptance contract
  -> P11C isolated process worker implementation
  -> P11D fixture-only real execution evidence
  -> P11E acceptance and closure
  -> stop at P12 authorization boundary
```

## Preserved boundaries

- no finance-us mutation, branch, PR, ready, or merge;
- no mutation of any remote target repository;
- no production deployment;
- no P12-P15 implementation;
- no cleanup or branch deletion;
- no Codex-replacement or production-readiness claim.

## Stop condition

After this governance-only PR passes tests and CI, merge it through the routine tool-system flow and proceed to P11B. Do not execute a real worker in P11A.
