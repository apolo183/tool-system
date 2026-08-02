# P14F Autonomous Patch-Test-Repair-Review Acceptance

## Decision

Status: `P14F_ACCEPTED_ISOLATED_FIXTURE_ONLY`.

P14F is accepted only for deterministic execution against caller-owned
in-memory fixture repositories and injected fixture callbacks. It does not
authorize or implement provider, credential, filesystem, command, Git,
database, GitHub, downstream, production, cleanup, or rollback operations.

## Accepted capability

- Freeze task digest, baseline tree, exact scope, acceptance set, validation
  set, terminal predicate, and finite cycle/call/time/cost/patch budgets.
- Apply add, replace, and delete operations atomically after exact path and
  content-SHA preconditions pass.
- Feed bounded validation diagnostics and blockers into the next fixture worker
  call without allowing the worker to redefine acceptance or authority.
- Require exact validation-set results and two independent reviews; suggestions
  outside frozen acceptance remain non-blocking.
- Record caller-persistable per-cycle state and recurrence fingerprints that
  exclude attempt number, timestamps, receipts, PR metadata, and status text.
- Stop on repeated state, two completed no-progress cycles, or any finite budget.
- Seal candidates only after frozen acceptance, validation, and reviews pass;
  stale evidence cannot reopen a sealed candidate.

## Evidence boundary

Tests cover a successful patch, initially failing validation followed by repair,
atomic scope and SHA blocking, recurrence termination, review closure, evidence
non-reopening, sealed-state resume, and worker authority-expansion blocking.
All operations remain in memory. Persistent SQLite/Git orchestration and crash
recovery belong to P14G and are not claimed here.

## Rollback point and non-claims

The rollback identity is
`tool-system@0b5110a2eea79ebde650e1088b787c781ddab171`. Rollback execution is not
authorized. P14G remains the next unauthorized stage. No provider, credential,
real repository, production, cleanup, branch deletion, PR #119, or Codex
replacement action or claim is included.
