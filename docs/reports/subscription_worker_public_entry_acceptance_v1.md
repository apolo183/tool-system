# Subscription Worker Public-Entry Acceptance v1

Decision on guarded merge: `accepted_subscription_worker_public_entry_core`.

## Accepted boundary

This package implements package 4 of
`docs/reports/subscription_worker_public_entry_closure_specification_v1.md` as
a read-only closure decision. It accepts the existing root-CLI
`develop-execute` composition at the evidence boundary proven by injected fake
Codex process I/O, isolated Python and TypeScript repositories, temporary
durable state, bounded validation and review, and exactly one remote-free local
Git commit.

The acceptance does not claim that this package invoked a real Codex process or
operated on a real downstream repository. It establishes that the canonical
public entry composes the accepted blueprint compiler, repository context,
bounded task and development loop, subscription worker adapter, isolated
workspace, validation, review, durable state, and local-Git owners behind exact
manifest/change-plan and snapshot bindings.

## Canonical evidence closure

The closure specification was squash-merged by PR #206 as
`ab40eb743cadb88111a7e7fd9c6dd96adfeb5cf4`. The adapter, structured-result,
development-loop bridge, task-runner pipeline, public preflight,
context/compiler, snapshot-binding, sandbox correction, and public execution
integration packages were then squash-merged in order through PR #215.

Draft PR #216 is not accepted evidence. It remained unmerged after exposing an
unsealed runtime change and receipt-replay ordering failure. PR #217 corrected
that defect in the local-Git natural owner and squash-merged as
`983e225377fdef23a18368c9e662f8231d6aaec8` after Hosted CI runs 1298 and 1299.
PR #218 then validated the corrected route across Python and TypeScript,
passed Hosted CI runs 1301 and 1302, and squash-merged as
`8be8950937407bbca0c562b77348c67aba6b5685` with the feature branch retained.

The exact canonical chain and per-requirement disposition are frozen in
`docs/reports/subscription_worker_public_entry_acceptance_mapping_v1.yaml`.

## Acceptance decision

The canonical evidence satisfies every requirement in the parent specification:

- default invocation performs no external worker call and no mutation;
- fake-process tests prove exact shell-free invocation, minimal environment,
  bounded output, structured final output, timeout, and cancellation;
- the public CLI reaches the injected subscription adapter only after current
  process authority, exact pair, repository snapshot, and execution-binding
  gates pass;
- scope escapes, symlink escapes, stale or dirty repositories, no-progress
  states, and unsealed candidates fail closed before a local commit;
- isolated Python and TypeScript successes create exactly one remote-free local
  commit, while completed replay creates no second worker call or commit;
- Hosted CI uses fake process I/O and temporary local repositories only; and
- API mode remains disabled with zero provider invocations.

## Non-claims and stop boundary

This decision grants no real Codex execution, ChatGPT Web automation, API or
provider execution, credential access, real downstream access or mutation,
remote push or pull-request publication by the runtime path, production or
deployment operation, cleanup, or rollback authority. No such operation occurs
in this package.

Successful publication closes the subscription-worker public-entry milestone
and stops before real downstream execution, any real subscription-worker run,
remote publication, production, cleanup, or rollback.
Each remains a separately authorized future lifecycle.
