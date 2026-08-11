# Subscription Worker Real Isolated Acceptance v2 Descriptive Closeout

## Authority and evidence boundary

`P14G-SUBSCRIPTION-WORKER-REAL-ISOLATED-ACCEPTANCE-v2-DESCRIPTIVE-CLOSEOUT-v1`
authorizes only a descriptive closeout from canonical
`main@027dbb3fb83c38def70e81d58712f80dbe613483` with tree
`0480170128bb0c88a57eb91ff752a0ad954c6e08`. The facts below come from the
operator-supplied read-only terminal observation of the separately authorized
v2 run. This closeout package did not read, reuse, modify, move, or delete either
external v1 or v2 evidence root.

This package changes no runtime code, test, blueprint, module contract, policy,
or workflow. It performs no real Codex, API, provider, downstream, production,
cleanup, or rollback operation. Repository publication of this four-path
closeout is a separate action-scoped GitHub lifecycle and is not a v2 runtime
remote-publication result.

## Frozen identity and isolation evidence

- The frozen manifest and change plan passed their recorded SHA-256 checks.
- The tool-system checkout was clean at canonical
  `027dbb3fb83c38def70e81d58712f80dbe613483`, tree
  `0480170128bb0c88a57eb91ff752a0ad954c6e08`.
- The synthetic fixture was clean at
  `3912cee5591f9808715bcf2d4665642306aaad02`, tree
  `ab9f7cd41810e5e4e899767db7107ff08012ad51`, with zero remotes.
- The isolated workspace was detached at the same fixture commit and tree, had
  zero remotes, and contained zero delta commits. No branch or local commit was
  created.
- The terminal observation found no remaining acceptance process. SQLite
  integrity and foreign-key checks were clean, with zero outbox and side-effect
  rows.

These observations establish no drift in the frozen inputs, canonical base,
synthetic fixture, remote-free workspace, or read-only terminal inspection.

## Durable dispatch and terminal result

Before the real Codex process started, durable state contained ordinal worker
call 1 in `STARTED` state. The pre-dispatch receipt reported that its evidence
was fsynced before process start and that approximately 1979.97 seconds remained
on the 1980-second task lease.

The durable worker call began at epoch `1786462915.7681437` and completed at
`1786463515.8701015`, an elapsed duration of approximately 600.10 seconds. It
ended `BLOCKED` with the stable safe terminal code
`SUBSCRIPTION_WORKER_TIMEOUT`. The public execution result also ended `BLOCK`
with `worker_invocations: 1`, `durable_lease_seconds: 1980.0`, and the same
terminal code. The call count and terminal code were therefore preserved and
were not replaced by `DURABLE_STATE_CONFLICT` or reset to zero.

The driver exited with `DRIVER_RC=1`, as expected for the blocked result. v2 is
not a passing acceptance.

## Work not completed

The worker did not produce a usable candidate. No validation command was
actually executed, no branch was created, no local commit was made, and no
completed-receipt replay was attempted. No acceptance summary or replay result
was produced. The workspace remained at the unchanged fixture tree.

For the v2 run, provider invocations, real downstream repository access and
mutation, runtime remote publication, production operations, cleanup, and
rollback were all zero.

## Residual gaps

Two observed defects remain uncorrected:

1. The public result reports `validation_command_invocations: 1` although no
   validation command actually ran.
2. The terminal task is `FAILED`, but its durable run remains `ACTIVE`.

The available evidence does not establish why the worker timed out. This
closeout makes no network, proxy, model, structured-output, or other causal
inference.

## Closeout decision and stop boundary

The v2 result is `BLOCK`. P14G successful real Subscription Worker acceptance
remains incomplete. Correcting either residual gap or conducting a v3 real
isolated acceptance requires separate explicit authorization. After this
descriptive closeout is merged, work stops immediately.
