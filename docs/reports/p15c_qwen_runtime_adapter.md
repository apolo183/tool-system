# P15C Qwen runtime adapter record

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION`

This record closes `P15C-QWEN-RUNTIME-ADAPTER-v1`. It adds a reusable exact
Qwen adapter to `ai_worker_runtime`; it does not change the canonical P15C
provider packet catalog or make the current DeepSeek/OpenAI matrix eligible.

## Frozen baseline and scope

- Repository: `apolo183/tool-system`
- Canonical baseline: `c4f7527a8a9f859c1f3ed64bfcc93393331dfc14`
- Canonical tree: `6104fa710311cda019741d3c0d103a30af51fb9e`
- Durable module: `ai_worker_runtime` `1.8.1` to `1.9.0`
- Aggregate interface: `ai-worker-runtime-api` `1.0.0` unchanged
- Exact scope: the fifteen paths in the retained task manifest and change plan

The canonical `config/p15c_execution_packet_freeze_v1.yaml` is forbidden from
this scope and remains byte-for-byte unchanged. Consequently its absent
`execution_matrix` record continues to select the legacy exact provider pair
`deepseek`, `openai`; the dated DeepSeek catalog version remains unpinnable and
blocks every private entry before settings, credentials, target input, ledger,
or transport access.

## Exact Qwen adapter

- Provider: Alibaba Cloud Model Studio
- Exact model: `qwen3.7-plus-2026-05-26`
- Fixed base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Fixed direct-TLS operation: `POST /compatible-mode/v1/chat/completions`
- Credential reference: `private-control:credentials#providers.qwen.api_key`
- Requested output ceiling: 2,048 tokens
- Request controls: `enable_thinking=false`, `stream=false`, empty tools, JSON
  object response, one attempt, zero retries, no provider web search, no proxy,
  no fallback, no redirect, and no response storage
- Response controls: exact model echo, one stopped choice, bounded usage, strict
  existing review-output schema, and no raw response serialization

Official evidence consumed read-only:

- Exact snapshot, context, price, and regional limits:
  `https://help.aliyun.com/zh/model-studio/qwen3-7-plus`
- OpenAI-compatible request, response, `response_format`, `enable_thinking`,
  and endpoint contract:
  `https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions`

The runtime accepts only the existing legacy matrix or an explicit
`openai`, `qwen` matrix. Tests create the latter only in a temporary sealed
repository and inject fake transport; no Hosted or local source-validation path
can reach a provider.

## Currency and budget boundary

Policy schema 2 adds `cny_to_micro_usd_ceiling` to the owner-only,
repository-external settings file. It is an accounting ceiling, not a claimed
market exchange rate. The runtime rejects values below 1,000,000 microUSD per
CNY and above 20,000,000, performs integer ceiling arithmetic, and makes no FX
network lookup. At the minimum, the frozen 250,000 microCNY Qwen attempt cap
reserves 250,000 microUSD. The private provider sub-budget and the shared
microUSD ledger must cover two such reservations before a two-case matrix can
start.

Schema 1 remains readable for existing installations only while Qwen stays
disabled with zero Qwen budget and transfer. The public schema-2 example is
disabled, expires in 1970, binds zero hashes, gives every provider zero budget,
and denies every transfer. Runtime policy loading now also rejects any total
budget above the public 20,000,000 microUSD authorization ceiling.

## Synthetic evidence and stop boundary

The focused suite covers the exact Qwen request and response, the fixed route,
native CNY calculation, integer microUSD conversion, conservative reservation,
schema-1 compatibility, schema-2 Qwen controls, provider-specific target
transfer, replay, cancellation, redaction, and one fake OpenAI/Qwen four-call
matrix. Hosted CI remains source-only and fake-I/O.

Local candidate validation completed with 162 focused tests and 685 full-suite
tests passing. Python compilation, Ruff 0.16.0 lint and format checks, the task
manifest, change plan, active-gates, process-authority, module-registry, and
repository-manifest validators all passed. The exact fifteen-path comparison,
secret-pattern scan, target-identity-neutrality scan, and unchanged canonical
packet digest also passed. Packet-only inspection returned `PASS`; default
preflight returned `PROVIDER_EXACT_VERSION_UNPINNABLE` with zero credential,
private-target, provider, or network operations, as required. Hosted CI success
and unchanged-base verification remain publication-time merge gates.

- credential_resolver_invocations: 0
- credential_value_accesses: 0
- private_target_packet_reads: 0
- private_target_snapshot_reads: 0
- provider_invocations: 0
- network_operations: 0
- benchmark_executions: 0
- private_repository_provider_transfers: 0
- target_repository_accesses: 0
- target_mutations: 0
- production_operations: 0
- cleanup_operations: 0
- rollback_operations: 0
- p15c_stage_accepted: false
- p15d_authorized: false

Changing the canonical matrix, changing Qwen funding status, reading any
credential value, reading the operator-private target, or executing the
benchmark remains outside this record.
