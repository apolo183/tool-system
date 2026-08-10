# Subscription Worker Public-Entry Execution Integration v1

## Objective

Compose the accepted subscription-primary modules behind one existing root-CLI route. The route must bind the exact task pair and repository snapshot, expose only a bounded context to the guarded Codex CLI adapter, validate the current candidate in an isolated clone, seal it through two review boundaries, and create at most one remote-free local branch and commit.

## Frozen boundary

- canonical base: `9c596282dbc784d8a5afdc1f4d283f4828adbf6b`
- exact scope: 21 paths in the paired task manifest and change plan
- APIs and provider credentials: absent and disabled
- real Codex, downstream repositories, remotes, production, cleanup, and rollback: zero operations
- Hosted CI: injected fake Codex process and temporary local Git repositories only
- remote publication: a non-executing draft-PR plan only

## Implementation decision

The read-only `develop` command remains unchanged. A separate `develop-execute` subcommand inside the same root CLI requires explicit repository-read, subscription-worker, validation, data-transfer, and local-Git flags, but those flags grant nothing unless an exact manifest execution binding matches every path identity, source commit/tree, scope, command, budget, worker configuration digest, branch, and commit message.

The task-runner composes existing module APIs. The local-Git owner creates or resumes one remote-free isolated workspace from a local exact snapshot; the development loop supplies the current candidate files on each worker cycle; validation commands are extracted only from captured validated change-plan bytes; the terminal result contains no prompt, file content, private path, raw worker output, or credential value.

## Current status

Implementation is in progress. This report is evidence only and grants no runtime or publication authority.
