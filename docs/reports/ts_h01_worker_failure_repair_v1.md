# TS-H01 worker failure accounting and terminal repair

Task: `TS-H01-worker-failure-accounting-and-terminal-repair-v1`

Reasoning: Extra high

Base: `e664a2c5fbaee5aac48d848e645b47cd917974db`

Base tree: `50cd400daba4e63e1b8bb56f1764c85b572ee3ca`

This local source correction records actual validation dispatch attempts and
persists an exhausted run's failure. Publication and runtime reacceptance remain
pending. The historical timeout cause is still unknown.

## Alignment and authority

The direct finding is TS-H01 in
`docs/reports/independent_audit_acceptance_reopen_v1.md`. The observed v2 failure
recorded zero validation commands but reported one, while the task was FAILED
and the parent run remained ACTIVE. The global parent is
`blueprint/tool_system_v0.yaml:product_objective`: bounded autonomous development
needs truthful validation, durable failure state, and repeat-safe evidence.

The active task manifest and change plan are
`docs/reports/ts_h01_worker_failure_repair_v1_task.yaml` and
`docs/reports/ts_h01_worker_failure_repair_v1_plan.yaml`. They freeze ten files,
a two-hour ceiling, three repair cycles, two complete regressions, and local
patch-only delivery. Current central main governance and local governance were
read before implementation. Existing Draft PR #235 retains the broader delivery
plan and was not modified. No new delivery plan or old backend task was opened.

## Changes and resulting behavior

| Natural owner | Correction | Observable result |
| --- | --- | --- |
| `runner/task_runner.py` | Accumulate the protected dispatcher's actual counts for this public call, including a later runtime exception. | Worker timeout, pre-dispatch rejection, cancellation before validation, and completed replay contribute zero; completed and partial validation attempts retain their counts. |
| `gate/command_runner.py` | Parse before counting; return a blocked result with the count retained after expected spawn, decoding, or timeout failures. | An invalid or empty argv has no dispatch; each attempted `subprocess.run` counts once even if process creation fails. Raw spawn error details are not returned. |
| `orchestrator/durable.py` | Project the registered task set into the existing FAILED run status in the task-transition transaction. Commit an exhausted claim before raising `RetryExhausted`. | A run fails when every registered task is terminal and at least one failed. Retryable or unfinished peer tasks keep the run ACTIVE. Failure survives reopening the database. |

The dispatcher count measures attempts at its subprocess boundary, not proof
that the OS created a child process. It is scoped to the current public call;
the separately reported durable worker count still spans that task's history.
Successful all-task completion continues to use the existing explicit
`complete_run` path. No public signature, lifecycle enum, schema, registry,
contract, or local-Git implementation changed.

The source fix does not migrate historical databases or rewrite previous
receipts. It does not establish the cause of the historical Worker timeout.

## Verification

Baseline reproduction on the unchanged production source, with new regression
assertions, produced **9 failures and 1 pass in 4.42 seconds**. It independently
exposed the overcount, the FAILED/ACTIVE mismatch, the rollback of exhausted
claims, and lost dispatch counts after expected command errors.

After the first source repair, the frozen focused set passed:
**135 passed in 29.71 seconds**. Its fixtures exercise the public entry, protected
dispatcher, durable state/recovery/side effects/reliability, and the local-Git
consumer. Fake Worker processes and temporary local repositories are test
fixtures; they are not real Codex or backend acceptance.

The full local regression passed **1095 tests in 133.39 seconds**, including
the installed-distribution check. It includes the focused tests above; their
counts must not be added together. All four required governance validators
returned PASS: strict active gates, current process authority, current module
registry, and repository manifest. The latter observed 850 tracked paths and
zero unclassified paths. This is local candidate verification, not main CI.

One source repair cycle and one complete regression were used. The final
documentation update records these results and removes three Markdown trailing
spaces found by the initial whitespace check; production source and test bytes
are unchanged from the passing runs. Final patch-scope, signature, and whitespace
results are bound in the external receipt.

The existing test interpreter was reused without installing dependencies. The
first task-pair check with the default interpreter reported a missing schema
dependency; it did not authorize execution. The same unchanged task pair passed
with the existing test interpreter before source edits.

## Remaining delivery boundary

This patch addresses the two TS-H01 source defects. TS-B02 still blocks real
execution: the actual isolation, lifecycle enforcement, hard deadline and full
cleanup require their separately authorized implementation and runtime evidence.
The existing delivery plan then needs a real Worker minimum task with actual
code changes, test/review evidence, and termination/cleanup evidence. H02/H03,
the output-memory bound, remaining CI hardening, and affected P16 acceptance
remain separate obligations; this patch closes none of them.

`real_repository_execution_blocked=true`. Real Worker/provider invocations,
DGX/backend effects, remote GitHub writes, PR creation/Ready/merge actions,
independent review agents, and deployment are all zero in this task.

## Review and rollback

The local patch contains only the frozen files. The original base is retained;
reversal can remove the patch or revert a future authorized commit. No rollback,
historical cleanup, or automatic publication was performed. The sealed external
task receipt binds the patch, changed-file bytes, command logs, elapsed time,
and actual operation counts without a circular self-hash.
