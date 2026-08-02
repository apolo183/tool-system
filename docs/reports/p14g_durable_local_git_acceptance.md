# P14G Durable Local Git Orchestration Acceptance

## Decision

Status: `P14G_ACCEPTED_ISOLATED_LOCAL_GIT_ONLY`.

P14G accepts one remote-free local fixture workflow: a frozen P14F candidate is
bound to a durable lease, checkpoint, attempt, branch receipt, and commit
receipt, then recorded as one local branch and commit. No remote repository is
configured or contacted.

## Accepted capability

- Fail closed before durable or Git writes on root, remote, dirty-worktree,
  branch, base commit, base tree, or exact-scope drift.
- Persist the frozen contract identity and loop result in the existing hardened
  SQLite store; record branch and commit as ordered idempotent side effects.
- Resume after a crash following a completed durable commit receipt without
  creating a second commit. An ambiguous in-progress effect blocks.
- Apply only the sealed candidate's exact paths, verify the staged path set,
  and create one deterministic-identity local commit.
- Emit rollback, creator-cleanup, and future draft-PR plans with execution
  explicitly unauthorized.

## Evidence boundary

Focused tests use only pytest temporary directories, temporary SQLite, local Git,
and injected deterministic P14F callbacks. They cover success, remote blocking,
head/tree drift, failed validation before Git mutation, and crash resume without
duplicate commit. Full validation and hosted CI confirm the registered module
and dependency graph. Provider calls, credential reads, GitHub calls, remote Git
operations, downstream mutations, production, rollback, and cleanup are zero.

## Rollback point and non-claims

The rollback identity is
`tool-system@22dedb0f2a2c0b38a0bd4c67f36c1c2454ca19d5:local_git@absent`.
Rollback execution is not authorized. P14H remains the next stage and is not
implemented or accepted here.
