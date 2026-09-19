# TS-M01 bounded command-output repair

## Scope and alignment

Parent: `independent_audit_acceptance_reopen_v1.md`, TS-M01. Product alignment:
`blueprint/tool_system_v0.yaml:product_objective` requires bounded validation and
controlled repair. This batch repairs command capture in the existing task-runner
module. It does not close the separate worker-adapter output issue or TS-B02.
Base: `827821191e58ccb644750fdfcd9c62b8418707f0`.

## Implementation

`run_commands` previously collected all stdout/stderr before checking output size.
It now uses a private Popen/selector helper with nonblocking binary pipes. Both
streams are drained concurrently. Each stream retains at most max_output_bytes;
each read is at most 64 KiB and at most remaining capacity plus one overflow byte.
The extra byte causes BLOCK and is not appended. Raw capture is capped before
text decoding; successful decoded UTF-8 result length is also checked. This means
newline-heavy or non-UTF-8 output may be rejected at its raw limit before the old
post-decoding limit. Per-stream limits remain separate, not one combined budget.
Memory is O(limit) per stream, not an OS RSS cap or an aggregate all-command cap.

One monotonic deadline covers pipe reading, EOF and direct-child completion.
On failure our pipe handles are closed; the directly spawned child, if running,
is killed and waited for at most one second. Failure to reap within that wait
returns an explicit cleanup-timeout BLOCK. This is a bounded attempt, not proof
of descendant, namespace, helper or reference cleanup. Inherited pipe write ends
cannot force an unbounded read/EOF wait. No process-group or by-name kill occurs.
Popen creation/OS scheduling itself is not a separately enforced hard deadline.
Cancellation retains its existing pre-command check.

Success preserves command-result fields, text newline translation and exit code;
the caller's existing gate still interprets nonzero exit. Launch attempts,
including failed launches and timeouts, retain TS-H01 counts. Public signatures,
authority validation and existing module contract/registry bytes are unchanged.
Tests that injected subprocess.run now inject the private capture helper, while
new public-entry tests exercise real inert local Python fixture children.

Host validation is Linux/POSIX. Selector support for pipes is required; unsupported
hosts fail closed through the existing dispatch-error boundary. No Windows host
execution compatibility or portability acceptance is claimed by this batch.

## Verification

Baseline: two new stdout/stderr overflow regressions failed against unchanged
production code, returning timeout instead of overflow. After repair the focused
command/task/durable/process-authority suite passed 123 tests in 39.06 seconds.
First full regression: 1119 passed, one stale subprocess.run module-boundary
assertion failed. After the recorded direct-test correction, the second and final
full regression passed: 1120 tests in 142.64 seconds. Four current-source governance
validators and the explicit task/plan pair passed. A manifest-only unknown metadata
key was rejected and moved into the allowed scope summary; no schema was changed.
Remote PR CI remains to be observed after publication.

Coverage includes sustained output, simultaneous large stdout/stderr, exact
limits, closed-pipe sleeping child, quiet timeout, direct-child reap/closed handles,
failed launch counts, decoded text and nonzero exit semantics. Fixtures are local
and inert; no actual Codex, provider, target repository or DGX process is invoked.

## Disposition and limits

Eight paths after explicit direct-test scope correction: command runner, three existing test owners, project state, this
report, task manifest and plan. No new module, formal interface identity, policy,
blueprint or acceptance milestone. Worker-adapter buffering, TS-B02 isolation,
TS-H03 broad acceptance and TS-M02 CI/supply-chain work remain separate.

Author review is not independent review. Publication and passing CI do not grant
runtime authority. User manually merges; automatic merge is forbidden.
`real_repository_execution_blocked=true` remains. Rollback requires separate
review of a revert to the recorded base; no deletion or rollback is performed.

The initial seven-path enumeration omitted tests/test_module_contracts.py. Full
regression exposed its fixed subprocess.run AST assertion. Under the user's
approved implementation/regression scope and delegated routine process decisions,
the exact direct-test correction is recorded in the manifest and plan before
editing it. The original freeze record is retained. No acceptance obligation,
budget, source-module boundary or runtime permission is changed. The test now
requires Popen and rejects subprocess.run; other effect checks stay intact.
