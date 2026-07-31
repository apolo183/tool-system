# P14C Bounded Real Model Provider Execution — Source and Correction Evidence

Status: `CORRECTED_SOURCE_MERGED_LIVE_EXECUTION_NOT_RUN_NOT_ACCEPTED`

This retained report records the narrow source implementation authorized by
`P14C-IMPL-v2` and the authorization-boundary correction authorized by
`P14C-CORR-v1`, plus the correction's separately authorized PR lifecycle
outcome. It is evidence, not execution authority or stage acceptance.

## Authority and preconditions

- correction parent: `b04fb05da9fd4cf4a291fc7dbc11a47b832a19e0`
- packet tool-system base: `637fe60782ed9e15d58795a0113b84965d6664d2`
- central governance consumption: canonical `finance-governance` remote,
  current `main`, and its two fixed formal paths; no central commit pin
- correction branch: `agent/p14c-corr-v1`
- correction commit: `e8fc1611c770cf4f3f8d6b8746a81c1df13503db`
- correction PR: `#143`
- squash-merge commit: `352b2638bb9a1cf7504a224c0571062072b32db1`
- implementation packet: `P14C-IMPL-v2`
- correction packet: `P14C-CORR-v1`
- Ready packet: `P14C-CORR-READY-v1`
- merge packet: `P14C-CORR-MERGE-v1`
- state-sync packet: `P14C-STATE-SYNC-v1`
- state-sync base: `352b2638bb9a1cf7504a224c0571062072b32db1`
- state-sync branch: `agent/p14c-state-sync-v1`
- static packet SHA-256:
  `3883ccb31ef59ff19c45b2818ac8cc3606b63d1f2b9575bc2a9ea18edb5db9b5`
- permitted repository: `apolo183/tool-system` only
- original permitted publication: one correction branch, one commit, and one
  Draft PR after all local gates passed and both current main identities were
  revalidated

`P14C-IMPL-v2` and `P14C-CORR-v1` permitted source, contract, test, evidence,
local Git, feature-branch, and Draft-PR work. They did not permit a Ready
transition or main merge. `P14C-CORR-READY-v1` later authorized only the PR #143
Ready transition, and `P14C-CORR-MERGE-v1` separately authorized only the PR
body synchronization and squash merge while base, head, CI, and the exact
seven-file scope remained unchanged. Those lifecycle actions completed, with
the successful correction tree retained at the squash-merge commit above.

None of those approvals, and no state recorded here, permits a credential-value
read, real provider call, P14C acceptance, P14D, downstream repository read or
write, cleanup, branch deletion, rollback execution, or production deployment.
The correction branch is retained; its deletion remains separately gated.

Subsequent repository lifecycle authorization and exact required-check
provenance hardening merged through PRs `#145` and `#146` at
`main@3256e17c416394ac7d209f9cafc529a3fb72504d`. That
`repository-controller@1.2.0` control-plane evidence has no live
mutation-capability issuer and does not change this report's status: no
credential value was read, no real provider call occurred, and P14C remains
unaccepted.

## Parent and global alignment

The direct parent is
`P14MR_MILESTONE_MODULE_INVARIANT`, whose accepted durable-module rule requires
this change to remain inside the existing `ai_worker_runtime` natural owner.
The global owner is
`blueprint/tool_system_v0.yaml:product_objective`, which requires a bounded real
AI-worker path while preserving action-scoped authority, auditability, hard
limits, redaction, and no silent scope expansion.

This change is an interface-compatible `ai_worker_runtime` implementation
revision from module `1.0.0` to `1.1.0`. The aggregate
`ai-worker-runtime-api@1.0.0` request, result, error, replay, and default fixture
behavior remain stable. No consumer module or downstream repository changes.

## Exact source envelope

| Control | Locked value |
| --- | --- |
| Provider | `openai` |
| Model | `gpt-5.6-luna` |
| Route | `POST https://api.openai.com/v1/responses` |
| Credential reference | `env:OPENAI_API_KEY` |
| Fixture | public synthetic `P14C-001` only |
| Reasoning effort | `none` |
| Output | strict JSON schema; `summary` and `control_status` only |
| Storage and tools | `store=false`; no tools field |
| Per-attempt tokens | input `4096`, output `512`, total `4608` |
| Attempts | maximum `2`; cumulative token ceiling `9216` |
| Time | request timeout `20s`; total wall clock `45s` |
| Cost | cumulative maximum `20,000` microUSD |
| Price seal | input `1` and output `6` microUSD per token |
| Retry | only `408`, `429`, `500`, `502`, `503`, `504`, connection, timeout |
| Backoff | default `250ms`; `Retry-After` capped at `2s` |
| Network | TLS verification required; exact host/path; no redirect, proxy environment, or fallback |

The price seal matches the official model page's published USD 1.00 input and
USD 6.00 output price per one million tokens:
<https://developers.openai.com/api/docs/models/gpt-5.6-luna>. The Responses
structured-output envelope uses `text.format` with `type=json_schema` and
`strict=true`, matching the official Structured Outputs guide:
<https://developers.openai.com/api/docs/guides/structured-outputs>.

## Implementation boundary

`src/tool_system/ai_worker/live_provider.py` owns:

- the immutable P14C packet and public synthetic request;
- an opaque, single-use execution capability bound to the exact packet,
  request, and transport kind;
- an explicit `P14CLiveExecutionGuard` that verifies the provider holds that
  same capability;
- the OpenAI Responses request encoder and strict response parser;
- provider-entrypoint capability consumption before request-body construction,
  credential resolution, or transport;
- an injected transport contract used by every test;
- an optional standard-library TLS transport that ignores proxy environment and
  does not follow redirects;
- retry, timeout, token, cost, response-size, model, refusal, incomplete-output,
  structured-output, and redaction controls.

`AIWorkerRuntime` defaults to `FixtureOnlyExecutionGuard`. In addition,
`OpenAIResponsesProvider.invoke()` independently requires and consumes the exact
capability, so bypassing the runtime cannot bypass authorization. The only
issuer in this source is private and test-only: it creates capabilities bound to
`injected_fake`. No issuer can authorize the `live_network` transport. A future
live proof therefore requires a separately authorized process-authority issuer;
no constructible affirmative boolean remains. This is a fail-closed supported
entrypoint boundary, not a claim that Python can sandbox hostile code already
executing inside the provider module's process.

`src/tool_system/ai_worker/live_evidence.py --validate-packet-only` validates
the packet and public fixture without constructing a provider, resolving a
credential, or sending transport. Its source evidence is:

```text
status=PASS
credential_value_access_count=0
provider_call_count=0
transport_call_count=0
live_provider_execution_authorized=false
```

All successful provider-path tests inject fake credential resolvers, fake
transports, and fake clocks. The live-network transport mismatch test replaces
its `send` method with a forbidden-call sentinel and proves zero calls. No test
reads a real credential or transmits network traffic.

## Claims and non-claims

This evidence supports only these claims:

- the bounded adapter source exists inside the registered AI-worker module;
- the default runtime blocks live providers before credential or transport;
- direct provider invocation without a capability performs zero credential and
  transport access;
- a fake capability cannot authorize the live-network transport and cannot be
  consumed twice;
- an explicitly guarded fake-transport path exercises request, retry, response,
  budget, cancellation, and audit behavior;
- packet-only validation performs zero provider, transport, and credential-value
  access.

It does not claim or authorize:

- a real provider request occurred or succeeded;
- the credential reference is populated;
- model quality, availability, latency, or billing was observed;
- P14C is accepted or closed;
- any downstream repository was inspected or modified;
- any future PR ready or merge action, cleanup, branch deletion, rollback, or
  production authority.

## Verification and stop condition

Before publication, the implementation must pass focused AI-worker tests, the
full repository suite, module-registry validation, repository-manifest
validation, source compilation, `git diff --check`, and packet-only evidence.

Local verification recorded on 2026-07-30:

- task manifest and change plan: `PASS`;
- focused P14C and affected-contract suite: `62 passed`;
- full repository suite: `503 passed`;
- active-gate validator: `PASS`;
- process-authority validator: `PASS`;
- current module-registry authority validator: `PASS`, with `100` owned paths
  and `152` ContractReferences;
- repository-manifest validator: `PASS`, with `204` formal files, `292`
  retained non-authority paths, and zero unclassified paths;
- packet-only evidence: `PASS`, with zero credential-value, provider, and
  transport calls;
- source compilation and `git diff --check`: `PASS`.

Any baseline drift, unapproved file, real network attempt, credential-value
access, test failure, registry/manifest mismatch, or scope expansion blocks
publication. The correction rollback reference is
`tool-system@b04fb05da9fd4cf4a291fc7dbc11a47b832a19e0`; the underlying P14C
module rollback boundary remains
`tool-system@637fe60782ed9e15d58795a0113b84965d6664d2:ai_worker_runtime@1.0.0`.
Rollback execution itself remains separately gated.
