# P14C Bounded Real Model Provider Execution — Source Implementation Evidence

Status: `SOURCE_IMPLEMENTED_LIVE_EXECUTION_NOT_RUN_NOT_ACCEPTED`

This retained report records the narrow source implementation authorized by
`P14C-IMPL-v2`. It is evidence, not execution authority or stage acceptance.

## Authority and preconditions

- tool-system base: `637fe60782ed9e15d58795a0113b84965d6664d2`
- central finance-governance base:
  `71c89101d3e5f90adfb469f7effef8fe39ddf394`
- implementation branch: `agent/p14c-openai-luna-v2`
- implementation packet: `P14C-IMPL-v2`
- static packet SHA-256:
  `1c5423ae2aac7af64902638e300ba375748db1d1ece0ee306108cf336df3b4c2`
- permitted repository: `apolo183/tool-system` only
- permitted publication: one feature branch, one commit series, and one Draft
  PR after all local gates pass and both main baselines are revalidated

The implementation packet permits source, contract, test, evidence, local Git,
feature-branch, and Draft-PR work. It does not permit a credential-value read,
real provider call, downstream repository read or write, PR ready transition,
main merge, cleanup, branch deletion, rollback execution, or production
deployment.

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
- an explicit `P14CLiveExecutionGuard` bound to the exact packet and request;
- the OpenAI Responses request encoder and strict response parser;
- credential-reference resolution after packet, request, guard, cancellation,
  and budget preflight;
- an injected transport contract used by every test;
- an optional standard-library TLS transport that ignores proxy environment and
  does not follow redirects;
- retry, timeout, token, cost, response-size, model, refusal, incomplete-output,
  structured-output, and redaction controls.

`AIWorkerRuntime` defaults to `FixtureOnlyExecutionGuard`. A live request is
therefore blocked before credential resolution or transport unless a caller
separately supplies an affirmative, exact-packet P14C guard. The source
implementation does not itself create that affirmative runtime authorization.

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

All provider-path tests inject fake credential resolvers, fake transports, and
fake clocks. No test uses the standard network transport or reads a real
credential.

## Claims and non-claims

This evidence supports only these claims:

- the bounded adapter source exists inside the registered AI-worker module;
- the default runtime blocks live providers before credential or transport;
- an explicitly guarded fake-transport path exercises request, retry, response,
  budget, cancellation, and audit behavior;
- packet-only validation performs zero provider, transport, and credential-value
  access.

It does not claim:

- a real provider request occurred or succeeded;
- the credential reference is populated;
- model quality, availability, latency, or billing was observed;
- P14C is accepted or closed;
- any downstream repository was inspected or modified;
- PR ready, merge, cleanup, rollback, or production authority.

## Verification and stop condition

Before publication, the implementation must pass focused AI-worker tests, the
full repository suite, module-registry validation, repository-manifest
validation, source compilation, `git diff --check`, and packet-only evidence.

Local verification recorded on 2026-07-30:

- focused P14C and affected-contract suite: `141 passed`;
- full repository suite: `498 passed`;
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
publication. Rollback identity is
`tool-system@637fe60782ed9e15d58795a0113b84965d6664d2:ai_worker_runtime@1.0.0`;
rollback execution itself remains separately gated.
