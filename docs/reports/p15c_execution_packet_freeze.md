# P15C Pre-Entry Execution Packet Freeze

Status: `P15C_PACKET_FREEZE_ACCEPTED_PRE_ENTRY_NO_EXECUTION`

## Decision

This record freezes a machine-readable, non-executing P15C packet set for
DeepSeek, OpenAI, and Qwen, one immutable P14H seed corpus, and one exact
private downstream target snapshot held outside this public repository. The
tracked packet serializes only a generic target-packet contract and no
downstream project identity, commit, path, or content-derived digest. It does not enter
`P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK`, activate a provider, resolve a
credential, transfer private repository content, or execute a benchmark.

DeepSeek and OpenAI are frozen as `QUARANTINED` candidates pending a separately
authorized P15C live lifecycle and every activation preflight. Qwen is retained
as a named `QUARANTINED` candidate but is `BLOCKED_NOT_FUNDED`; it receives zero
USD budget and cannot be selected by availability failover.

## Parent, baseline, and authority

- Direct accepted parent:
  `docs/reports/p15b_adapter_router_profiler_fixture_acceptance.md`.
- Current compatible canonical tool-system baseline:
  `1ede788b8b1c36bcc224cde15a5f6462c9b51938`.
- Current compatible canonical baseline tree:
  `7abd3b555d5c05f8bdf719c18619459ae9e06645`.
- Original packet-freeze baseline:
  `81be20f8cdf2d588993347fa11ca090dc9f17135` / tree
  `23addb451399ae89cc99e2c740115596f5e763c0`.
- Stage owner:
  `blueprint/tool_system_v0.yaml:milestones.P15_MULTI_PROJECT_BENCHMARK.stage_plan.P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK`.
- Authorization packet: `P15C-EXECUTION-PACKET-FREEZE-v1` plus the
  2026-08-03 owner-supplied provider, private-target, budget, and official-doc
  read-only evidence scope.

Canonical main compared identical to the original frozen baseline before the
original branch was created. It later advanced only through the accepted
target-identity decoupling governance correction. The
`P15C-PACKET-CANONICAL-REFREEZE-v1` task verified current canonical main at the
compatible commit above and re-anchored only `tool_system_baseline`. The stable
blueprint, runtime source,
provider packets, credential boundary, target packet, economics, limits, and
fixture corpus remain unchanged, and P15C remains unauthorized.

## Secret, policy, and usage-state separation

The operator's proposed design is accepted with one security correction:
budget and manual switches belong together, but they do not belong in the
credential file.

```text
private-control:credentials
    secret values only; runtime read-only; never tracked

private-control:p15c-execution-policy
    human-adjustable master switch, provider switches, private-target transfer
    switch, expiry, and budget; never tracked; contains no secret values

private-control:p15c-target-packet
    exact downstream identity, commit, allowlist, digests, and target authority;
    never tracked and never serialized into the public tool repository

private-state:p15c-usage-ledger
    durable cumulative attempt/token/cost accounting; never tracked; not a
    human policy input
```

This separation prevents a policy editor or future control UI from needing
write access to API keys, permits key rotation without changing authority, and
permits the operator to reduce the budget or stop execution without changing
code. The public packet authorizes at most 20 USD across all providers. A local
policy may lower that ceiling or disable any provider; it cannot raise authority
above 20 USD.

The repository contains only opaque reference IDs and the required non-secret
contract shapes. Exact private-target evidence is prepared out of band and its
contents are neither copied nor fingerprinted into this repository.

## Exact provider packets

The packet catalog is
`config/p15c_execution_packet_freeze_v1.yaml`.

| Packet | Exact model and surface | Frozen disposition | Per-attempt envelope |
| --- | --- | --- | --- |
| `P15C-DEEPSEEK-V4-FLASH-READONLY-v1` | `deepseek-v4-flash` / `DeepSeek-V4-Flash-0731`, Responses API at `https://api.deepseek.com` | `QUARANTINED`, not activated; private-repository transfer and retention review block | 65,536 input, 8,192 output, one attempt, no retry, 90-second request, 120-second wall clock, 25,000 microUSD |
| `P15C-OPENAI-GPT-5.6-LUNA-READONLY-v1` | `gpt-5.6-luna`, Responses API at `https://api.openai.com/v1` | `QUARANTINED`, not activated; private-repository transfer block | 65,536 input, 8,192 output, one attempt, no retry, 90-second request, 120-second wall clock, 25,000 microUSD |
| `P15C-QWEN-3.7-PLUS-READONLY-v1` | `qwen3.7-plus-2026-05-26`, OpenAI-compatible Chat surface at the Beijing DashScope endpoint | `QUARANTINED`, `BLOCKED_NOT_FUNDED`, zero USD allocation | same token/time/attempt envelope; 250,000 microCNY request cap remains inert while blocked |

The operational token limits are deliberately below every selected model's
official context and output maximum. At the frozen price snapshots, the
DeepSeek ceiling assumes the announced 2x peak multiplier and the OpenAI ceiling
uses uncached input; each calculates to at most 22,400 microUSD before applying
the 25,000-microUSD hard cap. These are request ceilings, not permission to
spend. The shared private ledger and 20-USD authorization ceiling remain
independent hard stops.

Provider tools, provider-side web search, response storage, streaming, retries,
and target mutation are disabled. Cancellation and no-progress stops are
mandatory future activation gates.

## Official evidence snapshot

All provider metadata was read from official public sources on 2026-08-03; no
provider endpoint was called.

### DeepSeek

- The official API catalog identifies `deepseek-v4-flash`, exact version
  `DeepSeek-V4-Flash-0731`, a 1M context, a 384K output maximum, Responses API
  support, and the current price schedule:
  <https://api-docs.deepseek.com/quick_start/pricing/>.
- The official Responses guide fixes the base URL and records `store: false`:
  <https://api-docs.deepseek.com/guides/responses_api/>.
- The official status page reported all systems operating on the retrieval date:
  <https://status.deepseek.com/>.
- The applicable privacy policy permits service-improvement processing and
  identifies storage in the People's Republic of China, so private repository
  transfer remains blocked pending explicit owner review:
  <https://cdn.deepseek.com/policies/zh-CN/deepseek-privacy-policy.html>.

### OpenAI

- The official model page identifies `gpt-5.6-luna`, Responses API support, a
  1.05M context, 128K maximum output, and the frozen price snapshot:
  <https://developers.openai.com/api/docs/models/gpt-5.6-luna>.
- The official status page reported no known system issues on the retrieval
  date: <https://status.openai.com/>.
- The official API data-control record states that API data is not used for
  training by default and that default abuse-monitoring logs may be retained up
  to 30 days:
  <https://platform.openai.com/docs/models/default-usage-policies-by-endpoint>.

### Qwen

- The official model record identifies the immutable
  `qwen3.7-plus-2026-05-26` snapshot, 1M context, 65,536 maximum output, pricing,
  and limits: <https://help.aliyun.com/zh/model-studio/qwen3-7-plus>.
- The official OpenAI-compatible API record fixes the Beijing Chat surface:
  <https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions>.
- Alibaba recommends environment variables or a secret system instead of
  hard-coding API keys:
  <https://help.aliyun.com/zh/model-studio/get-api-key/>.
- Alibaba documents that a per-key monthly or daily hard auto-stop is not
  available, so provider billing alerts cannot replace the local policy and
  usage-ledger hard gates:
  <https://help.aliyun.com/zh/model-studio/model-telemetry/>.

## Deterministic corpus snapshot

The exact twelve tracked files under `tests/fixtures/p14h/**` are frozen as
immutable specification inputs with aggregate SHA-256
`8b527c193fee4970516a5d7794c13db0a3b6b25770ef3d85c6b4d5ccc4234953`.
They remain seed specifications, not P15 benchmark results. No fixture is
modified and no benchmark is executed.

## Private target-packet boundary

The exact downstream repository identity, visibility, branch, commit, file
allowlist, blob inventory, aggregate digest, durable-module contract, and
target-specific authority are held in an operator-private, untracked target
packet. This public repository records only the required private packet shape,
an out-of-band preparation attestation, and fail-closed defaults.

The prepared target packet grants inventory reads only. Benchmark reads,
provider transfer, mutation, production, cleanup, and rollback remain false. A
later P15C execution lifecycle must resolve and validate the exact private packet
without logging it, and must explicitly authorize sending its allowlisted
content to each selected provider. Provider switching cannot bypass that data
boundary. Public tests use only synthetic project-neutral inputs.

## Exact eight-path change

```text
REPO_MANIFEST.md
config/p15c_execution_packet_freeze_v1.yaml
docs/reports/p15c_execution_packet_freeze.md
docs/tool_system_project_state_v1.yaml
examples/change_plans/tool_system_p15c_execution_packet_freeze_v1.yaml
examples/task_manifests/tool_system_p15c_execution_packet_freeze_v1.yaml
tests/test_p15c_execution_packet_freeze.py
tests/test_repo_manifest.py
```

No blueprint, runtime source, provider adapter, credential file, P14H fixture,
or downstream repository path is in scope.

## Canonical re-freeze addendum

The intervening canonical change was PR #171, which removed active downstream
project identity coupling from the reusable public core. Its final candidate
head was `2dbd0c6735b4a0f081d1a064458750d73d870cfe`, its final candidate tree was
`7abd3b555d5c05f8bdf719c18619459ae9e06645`, Hosted CI run `30811800450`
(`#1067`) passed, and the exact tree was squash-merged as
`1ede788b8b1c36bcc224cde15a5f6462c9b51938`. The feature branch remains
retained. These facts establish a governance-only compatibility transition;
they do not qualify a provider or authorize P15C.

The re-freeze is bounded to these nine paths:

```text
config/p15c_execution_packet_freeze_v1.yaml
docs/reports/p15c_execution_packet_freeze.md
docs/reports/p15c_packet_canonical_refreeze_acceptance.md
docs/reports/target_identity_decoupling_acceptance.md
docs/tool_system_project_state_v1.yaml
examples/change_plans/tool_system_p15c_packet_canonical_refreeze_v1.yaml
examples/task_manifests/tool_system_p15c_packet_canonical_refreeze_v1.yaml
tests/test_p15c_execution_packet_freeze.py
tests/test_target_identity_decoupling.py
```

The normalized SHA-256 of the entire packet after removing only the
`tool_system_baseline` mapping remains
`03f99a7e43ce7f3a381d59231c8a9d31ec1a9324922639126fa2268ff6d42626`.
That lock proves the provider/model choices, official evidence snapshot,
economics, corpus, private-control separation, target-packet contract, limits,
activation gates, and zero-authority boundary are semantically preserved.

## Acceptance and stop condition

The freeze is accepted only when the exact provider packet, corpus, generic
private-target contract, provider facts, private-control separation, task pair, state, repository
manifest, and focused consistency test pass locally and in Hosted CI, canonical
main remains unchanged through Ready, and the exact branch is squash-merged and
retained.

After merge, descriptive state continues to show P15B as the last accepted
stage and P15C as the next unauthorized stage. This record grants no execution
authority. Activation stops unless every packet gate passes, including a fresh
credential-reference availability check without disclosure, current health and
funding evidence, an enabled unexpired private policy, sufficient shared budget,
and explicit private-repository provider-transfer authorization.

```text
blueprint_changes: 0
runtime_source_changes: 0
provider_adapter_changes: 0
credential_value_accesses: 0
provider_invocations: 0
benchmark_executions: 0
private_target_inventory: completed out of band and not serialized
private_repository_provider_transfers: 0
private_repository_mutations: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
P15C_authorized: false
```
