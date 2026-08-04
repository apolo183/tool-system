# P15C DeepSeek Exact-Version Block

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION`

Task identity: `P15C-DEEPSEEK-EXACT-VERSION-BLOCK-v1`

Baseline: `tool-system@7e371b8e5f14c64cbe3ff06f6c3476fc166e01b1`
with tree `802e32725c371907ff367ff7fd31ddcd3d502887`.

## Evidence and decision

On 2026-08-05, the current official DeepSeek pricing catalog identified the
dated model version `DeepSeek-V4-Flash-0731`, while the current Chat
Completions request reference admitted only the moving request model IDs
`deepseek-v4-flash` and `deepseek-v4-pro`. The public request surface therefore
did not provide evidence that a request could bind `DeepSeek-V4-Flash-0731`.

The exact-version reproducibility invariant remains unchanged. The public
packet now records the dated catalog fact but marks the DeepSeek route
`BLOCKED_EXACT_VERSION_UNPINNABLE` with blocker
`EXACT_MODEL_VERSION_UNPINNABLE`. The stable runtime failure is
`PROVIDER_EXACT_VERSION_UNPINNABLE`.

This is not a provider rejection and does not change the provider portfolio,
economics, model ID, route, limits, target contract, or operator authorization.
It is a fail-closed correction at the existing `ai_worker_runtime` boundary.

Official evidence:

- Model/version and price: <https://api-docs.deepseek.com/quick_start/pricing/>
- Request model identifiers and surface: <https://api-docs.deepseek.com/api/create-chat-completion/>

## Boundary proof

`--packet-only` loads public packet metadata and returns the blocker with zero
private or live operations. `--preflight`, `--execute`, and direct executor
entry validate the canonical public packet disposition before settings,
credentials, target packet, target snapshot, usage ledger, request transport,
or provider response processing.

Synthetic lower-runtime tests remain possible only after creating a test-local
sealed packet copy whose DeepSeek disposition is explicitly eligible. The
tracked canonical packet is never made eligible by a private operator switch,
budget, credential, or transfer authorization.

## Zero-operation record

```yaml
credential_resolver_invocations: 0
credential_value_accesses: 0
private_target_packet_reads: 0
private_target_snapshot_reads: 0
provider_invocations: 0
network_operations: 0
benchmark_executions: 0
target_repository_accesses: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
blueprint_changes: 0
provider_portfolio_source_changes: 0
p15c_stage_accepted: false
p15d_authorized: false
```

## Future unblock condition

DeepSeek may become execution-eligible only through a separately audited
packet correction backed by current official evidence that the request API can
bind one exact model version (or returns a provider-verifiable immutable model
version before any private target is transmitted). That correction must rerun
the full packet, source-seal, fake-transport, redaction, budget, and Hosted CI
closure. This record grants no such correction or execution authority.
