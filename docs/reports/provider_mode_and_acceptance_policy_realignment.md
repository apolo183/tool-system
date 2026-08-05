# Provider mode and acceptance policy realignment

Status: `ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_POLICY_REALIGNMENT_NO_EXECUTION`

This record closes the target/policy package of
`PROVIDER-MODE-AND-ACCEPTANCE-REALIGNMENT-LIFECYCLE-v1` only after guarded
squash merge. It corrects the stable product target before either affected
runtime module changes and grants no provider, credential, private-target,
benchmark, downstream, P15 acceptance, P16 entry, production, cleanup, or
rollback authority.

## Baseline and exact scope

- repository: `apolo183/tool-system`
- canonical baseline: `c4120a8275f6eb8bc8aaa660282b8875b013f1f6`
- canonical tree: `b6268cb92b54d46d5166466a87bf6def01fb2c62`
- task: `PROVIDER-MODE-AND-ACCEPTANCE-POLICY-REALIGNMENT-v1`
- exact scope: 13 paths in the task manifest and change plan
- runtime source changes: 0
- module contract or registry changes: 0
- provider packet or operator configuration changes: 0

## Corrected stable rules

1. Supported ChatGPT/Codex subscription mode is the ordinary daily development
   route and is not API credit.
2. Every large-model API is a dormant backup and disabled by default, including
   OpenAI, DeepSeek, Qwen, and future providers.
3. Key presence does not enable an API or authorize a call. Provider/model choice
   is repository-external operator configuration.
4. Unconfigured, unfunded, invalid, expired, or unavailable providers may be
   skipped. Hard policy, data, budget, authorization, and precondition failures
   remain non-bypassable.
5. Every provider-specific adapter must pass injected fake-I/O contract tests.
6. The overall backup path requires one explicitly enabled usable key to complete
   one controlled smoke test on the then-canonical main.
7. Simultaneous multi-provider availability, Qwen funding, and date-pinned
   versions for moving aliases are not project-completion gates.

The stable `P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK` identifier remains for
compatibility in this policy package, but its target-state objective no longer
requires multiple live providers or a real downstream repository transfer. P15D
still depends on P15C acceptance, P15F still closes P15, and P16 entry still
depends on accepted P15. This package neither accepts P15 nor enters P16.

## Preserved safety boundary

The existing disabled operator template, external credentials, budgets, expiry,
authorization, data-transfer, retry, cancellation, redacted audit, source seal,
and Hosted CI fake-I/O controls remain unchanged. No historical evidence is
rewritten; old OpenAI-Qwen matrix records remain retained non-authority evidence.

## Validation and zero-operation evidence

The frozen candidate passed 72 focused tests and 704 full-suite tests. Python
compilation, Ruff 0.16, task-manifest, change-plan, active-gate,
process-authority, current module-registry, repository-manifest, diff, exact
scope, forbidden-path, secret, and project-identity checks also passed. The
publication gate additionally requires Hosted CI success and unchanged canonical
base, head, scope, comments, and review state before Ready and squash merge.

- credential_resolver_invocations: 0
- credential_value_accesses: 0
- provider_invocations: 0
- network_operations: 0
- benchmark_executions: 0
- private_target_reads: 0
- target_repository_accesses: 0
- target_mutations: 0
- production_operations: 0
- cleanup_operations: 0
- rollback_operations: 0
- p15_stage_accepted: false
- p16_stage_entered: false
- final_live_smoke_executed: false
