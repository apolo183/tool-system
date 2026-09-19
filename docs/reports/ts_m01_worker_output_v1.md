# TS-M01 worker output capture repair

## Scope and alignment

This completes the source correction of the two whole-output buffering paths
identified by TS-M01 in independent_audit_acceptance_reopen_v1.md. The parent
command-runner correction is already in base 99b579e214de9cb57478539d6bf3d7dce151c1cc
(PR #239). Global alignment is blueprint/tool_system_v0.yaml:product_objective:
bounded authorized worker invocation with unchanged module and authority boundaries.

Only the worker-adapter implementation, its existing test owner, descriptive
project state and this task/report/plan are changed. Module contract, registry,
provider boundaries and command-runner source remain KEEP. No formal acceptance,
real worker execution, downstream mutation or TS-B02 closure is claimed.

## Implementation and compatibility

The default process runner now uses binary, unbuffered nonblocking pipes and one
selector for stdin, stdout and stderr. Input is written in at most 4096-byte
pieces while both output pipes are drained. Retained raw output is capped at the
configured combined stdout-plus-stderr max_output_bytes. Each read requests at
most 64 KiB and at most remaining capacity plus one detection byte. Overflow is
raised before appending that byte; no communicate or background reader/writer is
used. Memory remains O(configured limits), not a kernel-enforced RSS cap.

One monotonic deadline covers prompt transfer, output EOF and child exit. Any
exchange failure invokes the existing bounded process-group TERM/KILL cleanup,
and all three owned pipes close in finally. The existing wait envelope is at
most two termination-grace waits, already reflected by the task-runner lease.
This retains existing process-group cleanup limitations; it is not proof of
complete descendants/reap/namespace/reference/helper/core cleanup. Popen creation
and OS scheduling are not separately enforced hard deadlines.

Successful output is decoded with the prior locale-oriented text convention and
universal newlines. Its UTF-8 combined length is also checked, preserving the
existing postdecode check for injected process runners. The new raw-byte cap can
reject newline-heavy or non-UTF-8 output before the former text-only limit.
Invalid text fails closed. The terminal final-message file remains separately
bounded by the existing no-follow read and schema validation.

The adapter's public request, configuration and result types are unchanged.
The injected internal ProcessRunner receives max_output_bytes as a keyword;
in-repository injected runners accept keyword arguments and are revalidated.
Custom injected runners must accept and enforce that limit; their own I/O cannot
be bounded by a receipt from this adapter. An early OverflowError maps to the
existing SUBSCRIPTION_WORKER_OUTPUT_LIMIT without raw output, prompt or paths.
The early-overflow output omits returncode because completion is not guaranteed.
Default-disabled operation, preflight, argv, minimal environment, private schema,
structured final result and false mutation/production flags are retained.

Linux/POSIX selector pipes are validated. Windows pipe-selector support is not
claimed; unsupported hosts fail closed. No real Codex/provider, credentials,
DGX backend or target repository was invoked by this task.

## Validation

The first baseline fixture attempt omitted required executable configuration and
failed before dispatch; it is not defect evidence. After fixing that fixture,
two regressions against unchanged production code returned TIMEOUT instead of
OUTPUT_LIMIT. Both failed as expected. With the fix, all 24 worker tests passed.

New tests exercise both overflow streams through the adapter, combined-limit
accounting and read size, exact-boundary dual-pipe output before large stdin
consumption, blocked stdin, closed-output sleeping child, early stdin close,
newline conversion, nonzero exit, reaped direct child and closed owned pipes.
Existing fake cancellation tests still verify TERM and TERM-to-KILL dispatch;
their timeout injection moved from communicate to the new stream exchange.

Focused affected-closure suite: 82 passed in 28.39 seconds. Full regression:
1127 passed in 139.65 seconds. Four current-source governance validators, the
explicit manifest/plan pair, and git diff --check passed. Hosted PR CI remains
to be observed after publication.

## Disposition

The two historical full-buffering source defects are corrected when this source
and its regression gates pass. That is not independent acceptance of TS-M01 or
proof of actual resource isolation; historical findings remain immutable.
Author review is not independent review. PR CI and manual merge remain required;
no auto-merge. real_repository_execution_blocked=true remains in force.
Rollback is a separately reviewed Git revert to the recorded base; no branch,
artifact or historical evidence deletion is authorized or performed.
