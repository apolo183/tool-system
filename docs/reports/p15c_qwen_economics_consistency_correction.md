# P15C Qwen economics consistency correction

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION`

This record closes `P15C-QWEN-ECONOMICS-CONSISTENCY-CORRECTION-v1` as a
prerequisite to the separately frozen OpenAI/Qwen canonical matrix. It changes
one `ai_worker_runtime` consistency invariant; it does not change the canonical
packet catalog, select Qwen, attest funding, or execute P15C.

## Defect and exact correction

The accepted dormant Qwen adapter expected
`calculated_worst_case_micro_cny: 192000`. The frozen request envelope and
official Qwen price tier instead produce:

```text
65536 input tokens * 2 microCNY/token = 131072 microCNY
 8192 output tokens * 8 microCNY/token =  65536 microCNY
                                          ------
                                          196608 microCNY
```

The runtime now requires `196608` for a selected Qwen execution packet and
continues to require the unchanged `250000 microCNY` per-attempt hard cap. A
stale selected packet fails with `PACKET_PRICE_DRIFT`. Exact executable
economics are evaluated for selected routes; an unselected blocked catalog
entry cannot prevent public inspection of the legacy selected pair.

## Frozen boundary

- canonical baseline: `20686afbef73d5985f4aac0d542eabe7f3fdadff`
- canonical tree: `0eca08ed3e32850d93b39dfdb151ca86962e59fa`
- durable module: `ai_worker_runtime` `1.9.0` to `1.9.1`
- aggregate interface: `ai-worker-runtime-api` `1.0.0` unchanged
- exact scope: ten paths in the retained task manifest and change plan
- canonical packet digest: unchanged from
  `509270b737aab11776397a5d5db9c0a6f8a89165a07f37002a669cb2cbf3a962`

The canonical catalog remains byte-for-byte unchanged: it has no explicit
matrix, Qwen remains `BLOCKED_NOT_FUNDED`, and the legacy DeepSeek/OpenAI pair
still blocks on `PROVIDER_EXACT_VERSION_UNPINNABLE` before every private
boundary. The OpenAI/Qwen test matrix is created only in a temporary sealed
repository, corrects the temporary Qwen ceiling, and uses injected fake I/O.

## Acceptance and stop evidence

Acceptance requires exact arithmetic and stale-packet negative tests, focused
and full pytest, Python compilation, Ruff, task-pair and governance validators,
an exact ten-path/forbidden-diff check, an unchanged packet digest, secret and
target-neutrality scans, Hosted CI success, and an unchanged canonical base
before Ready and squash merge. This report is evidence only and grants no
runtime authority.

Local candidate evidence completed with 122 focused tests and 687 full-suite
tests passing. Python compilation, Ruff 0.16.0 lint and format checks, the task
manifest, change plan, active-gates, process-authority, module-registry, and
repository-manifest validators passed. Packet-only returned the unchanged
DeepSeek/OpenAI public pair with zero I/O; default preflight returned
`PROVIDER_EXACT_VERSION_UNPINNABLE` before every private boundary. Hosted CI
and the unchanged-base guard remain publication-time requirements.

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
- canonical_packet_changes: 0
- p15c_stage_accepted: false
- p15d_authorized: false

The next matrix re-freeze must start from the later canonical main and still
leave Qwen blocked until operator funding evidence is supplied. No benchmark
may run under this correction.
