# P14G File Topology Correction Acceptance

`P14G_FILE_TOPOLOGY_CORRECTION_ACCEPTED_FIXTURE_ONLY`

## Accepted correction

`local-git@1.1.0` binds the supplied baseline mapping to the exact paths and
blob contents present at the frozen base commit. Allowed paths absent at base
may be added; present paths may be modified or deleted. The sealed candidate
may contain any subset of allowed scope, while the staged Git path set must
equal the actual add/modify/delete delta rather than every allowed path.

## Evidence boundary

Tests use pytest temporary remote-free Git repositories and caller-selected
temporary SQLite stores. They prove a mixed add/modify/delete commit, baseline
presence and content mismatch blocking before durable writes, exact changed-path
staging, and unchanged crash-resume behavior. Remote Git, GitHub, provider,
credential, downstream, production, cleanup, and rollback operations are zero.

## Non-claims

This correction does not accept P14H, authorize P14I, or alter the stable
blueprint. It does not execute a downstream workflow or publish a remote PR.
