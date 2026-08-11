# Subscription Worker Public-Entry Replay Correction v1

## Objective

Restore receipt-gated replay for the accepted subscription-primary public entry without broadening local-Git, remote, API, credential, production, cleanup, or rollback authority.

## Observed gap

At canonical main `dcf01353a4b86f7f472649a2b2c352d44393f748`, a successful public-entry run leaves one clean remote-free local commit in its isolated workspace and records the completed effect in the durable local-Git store. A repeated exact request is blocked by `create_isolated_local_workspace` because its pre-reconciliation check accepts only the original base HEAD/tree. The request therefore cannot reach the existing completed-commit receipt path in `run_durable_local_git`.

## Correction design

An existing workspace may pass the preliminary workspace gate in exactly two non-authorizing states:

- exact clean base HEAD/tree; or
- one clean remote-free first-parent commit directly above the exact base, marked as pending durable receipt reconciliation.

The preliminary result never declares the candidate authoritative. `run_durable_local_git` remains the sole owner of branch and commit receipt reconciliation. A candidate commit with no exact completed receipt, a different parent, more than one commit, a dirty tree, a remote, or any identity drift fails closed before another worker call or Git effect.

## Frozen boundary

- exact base: `dcf01353a4b86f7f472649a2b2c352d44393f748`
- exact scope: 8 paths in the paired task manifest and change plan
- runtime owner: `src/tool_system/local_git/orchestrator.py`
- direct public-entry regression: `tests/test_task_runner.py`
- API/provider/credential/downstream/remote/production/cleanup/rollback operations: zero
- validation: fake Codex process, temporary remote-free Git repositories, temporary SQLite only

## Current status

The correction is proposed and non-authorizing pending exact implementation, Hosted CI, and no-drift publication.
