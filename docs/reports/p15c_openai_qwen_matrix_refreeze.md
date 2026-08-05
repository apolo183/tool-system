# P15C OpenAI and Qwen matrix re-freeze

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_BLOCKED_NOT_FUNDED_NO_EXECUTION`

This record closes `P15C-OPENAI-QWEN-MATRIX-REFREEZE-v1` as a non-executing
catalog update. It makes the canonical selected matrix exactly OpenAI and Qwen,
retains DeepSeek as a quarantined blocked catalog record, and leaves Qwen
blocked until operator funding evidence exists. It grants no provider,
credential, private-target, network, benchmark, mutation, P15D, production,
cleanup, or rollback authority.

## Frozen baseline and module boundary

- repository: `apolo183/tool-system`
- canonical baseline: `0908a1d2ed8e88554fa4bd1e73bb7c4c4a88807b`
- canonical tree: `c053dd93999c5ef2f9112a7638b5fd2c00acb676`
- durable module: `adaptive_model_portfolio_and_economics` `1.0.0` to `1.1.0`
- aggregate interface: `adaptive-model-portfolio-and-economics-api` `1.0.0`
  unchanged
- exact scope: the twelve paths retained in the task manifest and change plan
- runtime source changes: 0

The module now owns the public, exact, non-authorizing provider catalog and
provider/case matrix record in addition to its isolated fixture portfolio. The
accepted `ai_worker_runtime` `1.9.1` consumes that record fail-closed; this
change does not alter its implementation or interface.

## Exact matrix and stop state

The selected matrix is:

| Provider | Exact model | Packet state | Cases |
| --- | --- | --- | --- |
| OpenAI | `gpt-5.6-luna` | `FROZEN_NOT_ACTIVATED` | deterministic corpus, private target |
| Qwen | `qwen3.7-plus-2026-05-26` | `BLOCKED_NOT_FUNDED` | deterministic corpus, private target |

The invocation ceiling is four: two selected providers by two cases with one
attempt and zero retries. DeepSeek remains in the catalog as
`BLOCKED_EXACT_VERSION_UNPINNABLE` and is excluded from the selected matrix; it
is neither enabled nor used as a bypass.

The frozen Qwen public evidence records a 1,000,000-token context, 131,072-token
official maximum output, the Beijing <=256k-input tier of 2 CNY per million
input tokens and 8 CNY per million output tokens, and the accepted attempt
envelope of 65,536 input plus 8,192 output tokens. Its exact calculated ceiling
is therefore 196,608 microCNY, below the 250,000 microCNY hard cap. Its shared
USD budget allocation remains 0 and no funding is attested.

## Transfer record is not execution authority

The user authorization record permits the exact private allowlist to be sent to
OpenAI and Qwen in a later, separately enabled execution. This public catalog
records that provider-specific decision but deliberately keeps the aggregate
runtime-transfer flag false. A future run still requires the matching
owner-private policy and target packet, exact source seal, clean canonical
worktree, unexpired switch, credential reference, funded selected providers,
provider sub-budgets, shared ledger capacity, and every existing token, time,
cost, cancellation, redaction, retry, and no-progress gate.

The public record contains no credential value, private target identity, commit,
path allowlist, content digest, or raw provider output. Packet-only inspection
returns the two selected public packets with zero private or live operations.
Default preflight stops on `PROVIDER_PACKET_BLOCKED` before reading settings,
credentials, target input, ledger, or transport because Qwen is unfunded.

## Validation and terminal boundary

Acceptance requires task-pair validation, exact packet and matrix assertions,
historical-evidence isolation, downstream packet-only and fail-closed runtime
revalidation, module-contract and registry validation, focused and full pytest,
Python compilation, Ruff, exact twelve-path and forbidden-diff checks, secret
and project-neutrality scans, Hosted CI success, and an unchanged canonical
base before Ready and squash merge.

Local candidate validation completed with 152 focused tests and 689 full-suite
tests passing. Task-manifest, change-plan, active-gates, process-authority,
module-registry, and repository-manifest validators passed. Python compilation,
Ruff 0.16.0, exact-scope, forbidden-diff, secret-pattern, project-neutrality,
packet-only zero-I/O, and default-preflight stop checks passed. Hosted CI and
the unchanged-base guard remain publication-time requirements.

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

After guarded merge, the only next action inside P15C is to wait for explicit
operator funding evidence and then revalidate the private controls against the
new canonical commit. No benchmark may execute under this re-freeze record.
