# Provider mode AI worker runtime realignment

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXTERNAL_EXECUTION`

This package implements the second dependency of
`PROVIDER-MODE-AND-ACCEPTANCE-REALIGNMENT-LIFECYCLE-v1`.

The ai-worker runtime now exposes a repository-external route record and a
default-disabled API execution guard. API mode disabled returns `API_DISABLED`.
When API mode is explicitly enabled, disabled or unavailable providers are
skipped without credential resolution, provider invocation, network access, or
benchmark execution. One enabled usable route is sufficient. If none remains,
the stable result is `NO_AVAILABLE_PROVIDER`.

A credential or key is deliberately absent from the route-decision input, so
key presence cannot grant activation or call authority. The execution guard
binds the exact externally selected provider and model before invocation.

This package does not change the adaptive provider portfolio, frozen historical
provider packets, operator credential files, CI policy, process authority,
blueprint, or production controls. It invokes no provider, reads no credential
value, accesses no downstream repository, performs no benchmark, accepts no P15
stage, enters no P16 stage, and executes no smoke test.

Acceptance additionally requires Hosted CI success, unchanged base and scope,
no new review or conversation blocker, guarded Ready, squash merge, and retained
feature branch.
