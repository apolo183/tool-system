# Default subscription mainline and optional API plugin realignment

## Decision

ChatGPT subscription web use and Codex CLI are the ordinary development mainline.
Every metered large-model API is a default-disabled, independently replaceable,
optional backup plugin. API activation, provider funding, key availability, and a
live provider smoke are not completion gates for the subscription-primary core,
P15 core acceptance, or P16 entry.

## Read-only P15 evidence finding

The accepted evidence consolidated by PR #189 and published on canonical commit
`579dde4718fb80ae0dc9c16d796e825c62aba189`, then descriptively closed on
`71bc347942e921675cea340ff06f6c3476fc166e01b1`, proves all non-live P15
requirements:

- two isolated representative projects across Python and TypeScript;
- cross-project isolation and bounded generalization;
- OpenAI, DeepSeek, and Qwen adapter fake-I/O contracts;
- deterministic default-off routing and hard policy gates;
- failure, repair, escalation, cancellation, no-progress, recovery, isolation,
  rollback planning, and integer synthetic economics;
- zero credential values, live provider calls, real downstream access,
  production, cleanup, and rollback operations for the non-live acceptance.

Those facts are inherited without rerunning a benchmark or reinterpreting a failed
live attempt as success.

## Acceptance and phase transition

P15 is accepted for the subscription-primary core scope. P16 production-operations
acceptance is entered under the current user authorization, without granting
production deployment or target mutation authority.

The old P15C live runtime remains default-disabled and is moved to
`OPTIONAL-API-PROVIDER-PLUGIN-v2` backlog. Its historical authorization,
legacy-catalog, and transport findings must be addressed only if that independent
plugin is later developed. The plugin remains subject to fake-I/O adapter
contracts and one separately authorized successful single-provider smoke before
its own release.

## Safety and zero-operation boundary

This realignment reads no credential value or private proxy address, invokes no
provider, performs no live smoke or benchmark, accesses no real downstream,
executes no production, cleanup, or rollback operation, and changes no runtime
source or provider adapter.
