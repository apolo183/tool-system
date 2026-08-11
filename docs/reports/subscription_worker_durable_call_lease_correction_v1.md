# Subscription Worker Durable Call and Lease Correction v1

## Objective

Correct the P14G durable boundary so a bounded subscription-worker invocation is
consumed before process start, remains counted through crash and retry, and
retains its safe terminal result while the lease covers every bounded execution
stage through the remote-free local commit.

## Observed failure evidence

The separately authorized isolated acceptance attempt against canonical main
`0c710929e292b340538845a5e9e87c03c36f5794` created a remote-free workspace and
schema-v3 durable state. The task remained `RUNNING` at checkpoint `FROZEN` with
attempt 1, a 60-second expired lease, and no durable worker-call record. About
120 seconds after workspace and state creation, the public result reported
`DURABLE_STATE_CONFLICT`, `worker_invocations: 0`, and zero worker usage.

The timing matches the configured 120-second worker timeout exceeding the fixed
60-second P14G lease. The adapter failure was then followed by a lease-protected
checkpoint transition, so the state conflict replaced both the timeout and the
in-memory call count. This package treats the externally started attempt as one
consumed call; it does not claim whether the remote model completed useful work.

The evidence root `/tmp/tool-system-real-subscription-acceptance-v1` is external
to this repository and is permanently excluded from this package's reads,
writes, deletion, movement, permission changes, cleanup, and rollback.

## Frozen correction design

- SQLite schema v4 adds one ordinal, retry-wide worker-call ledger. `STARTED` is
  committed under the active task lease before the worker callback can dispatch
  its process. A crash leaves the call consumed and ambiguous; reopening or
  reclaiming the task cannot erase or reuse it.
- The frozen `max_worker_calls` limit is checked against durable call records,
  and the development loop begins at the durable count floor. Durable retry may
  use only the remaining total budget.
- The guarded adapter emits stable safe terminal codes, including
  `SUBSCRIPTION_WORKER_TIMEOUT`. The bridge carries a
  blocked terminal envelope, the durable wrapper records it, and all later
  blocked or state-conflict returns retain the durable count and any already
  observed worker terminal code.
- The public task runner derives a deterministic lease interval from the bound
  worker timeout, both finite termination waits, validation commands, validation
  timeout, and bounded local-Git command envelope. P14G renews that interval only
  at durable callback and local-commit stage boundaries.
- All acceptance uses injected fake processes, fake clocks, temporary SQLite,
  and temporary remote-free Git repositories. No actual Codex, API, provider,
  credential, downstream, remote, production, cleanup, or rollback path runs.

## Status

Implementation and deterministic local evidence are complete on the exact
frozen branch: 262 focused tests and the 859-test full suite pass, compilation
and all task-pair, process-authority, module-registry, repository-manifest, and
scope validators pass, and Ruff reports no new diagnostic relative to the
canonical base across changed Python paths. Hosted CI remains external PR-gate
evidence and is intentionally pending at this commit freeze. This report grants
no authority. After an unchanged Draft PR passes Hosted CI, it may become Ready and
squash-merge with its branch retained; work then stops before any new real isolated acceptance.
