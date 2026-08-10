# Subscription Worker Snapshot Authority Binding v1

## Objective

This package closes the authority gap between the existing `tool-system develop` selection and the read-only repository-context stage. A passing general task pair is no longer sufficient. The exact task manifest must contain one `subscription_public_entry` binding whose redacted repository-root SHA256, expected HEAD, blueprint, module registry, milestone, acceptance, governance, query, and seed selections exactly equal the requested public entry.

## Binding and byte seal

The binding also requires `repository_read_authorized: true`, while worker execution and local-Git writes remain false. A CLI flag acknowledges the requested read but grants no authority by itself. The task runner captures manifest and change-plan bytes, runs the existing process-authority, policy, manifest, plan, and exact-pair gates with command execution disabled, then requires both byte sequences to remain identical before it accepts the binding. The authority packet records only hashes and bounded repo-relative selections.

## Compiler compatibility

The blueprint compiler accepts either its retained `isolated_fixture_repositories_only: true` envelope or the new `repository_context_read_authorized: true` envelope. Both routes still require blueprint approval plus false target mutation, provider execution, credential access, production, and cleanup authority. This is an interface-compatible extension; existing fixture callers remain valid.

## Public and validation boundary

The public CLI uses `--repository-read-authorized` as the primary spelling and retains the prior fixture flag only as a compatibility alias. Repository context remains fixed-HEAD, clean-worktree, tracked-blob, read-only, no-remote, finite, and freshness checked. Public output remains root- and content-redacted.

Hosted CI exercises only creator-owned isolated Git fixtures. This package performs no real downstream access, worker/Codex invocation, repository or local-Git write, API/provider call, credential-value access, remote operation, production, cleanup, or rollback. Worker dispatch remains the next independent package.
