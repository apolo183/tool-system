# P15C DeepSeek Packet Evidence Correction

Status: `ACCEPTED_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION`

## Decision

`P15C-DEEPSEEK-PACKET-EVIDENCE-CORRECTION-v1` corrects two unsupported
DeepSeek claims in the frozen, non-executing P15C packet. The official current
model catalog identifies model version `DeepSeek-V4-Flash` and the official API
reference exposes the OpenAI-compatible `POST /chat/completions` surface. The
prior packet incorrectly recorded `DeepSeek-V4-Flash-0731` and
`responses.create` after confusing the catalog's `Json Output` feature with an
OpenAI Responses API surface.

The corrected packet therefore binds:

- provider ID: `deepseek`;
- model ID: `deepseek-v4-flash`;
- model version: `DeepSeek-V4-Flash`;
- execution surface: `deepseek-openai-compatible-chat`;
- operation: `chat.completions.create`;
- endpoint: `POST https://api.deepseek.com/chat/completions`.

Official evidence:

- model version, context, output, Json Output, price, and concurrency:
  <https://api-docs.deepseek.com/quick_start/pricing/>;
- exact Chat Completions request and response surface:
  <https://api-docs.deepseek.com/api/create-chat-completion>.

## Frozen baseline and scope

- canonical repository: `apolo183/tool-system`;
- canonical base: `f30f43512acfa497afd9f27dcce7cf4a0ebeb101`;
- canonical base tree: `1c6b29bdcb9b823e7e063d5050587df45cd2f126`;
- branch: `agent/p15c-deepseek-packet-evidence-correction-v1`;
- natural owner: `adaptive-model-portfolio-and-economics` packet catalog;
- exact scope: seven paths named by the bound task manifest and change plan.
- corrected packet semantics SHA-256 after removing only
  `tool_system_baseline`:
  `27dc75dc1644518aee2717a1a0150a86c55be38d09a2d8c753c0a8bdf1bfc483`.

The correction changes no blueprint, runtime source, provider ID, model ID,
price, budget, token or time limit, retry rule, deterministic corpus, private
credential/policy/target/ledger separation, OpenAI packet, Qwen disposition,
target repository, or execution authority.

## Acceptance predicate

The correction is accepted only when its exact task pair validates, focused and
full tests pass, the packet and descriptive state agree, no secret or target
identity is serialized, Hosted CI succeeds, canonical main remains unchanged,
and the exact candidate is moved from Draft to Ready and squash-merged while the
feature branch is retained.

```text
official_provider_document_reads: 2
credential_value_accesses: 0
provider_invocations: 0
target_repository_accesses: 0
benchmark_executions: 0
target_mutations: 0
production_operations: 0
cleanup_operations: 0
rollback_operations: 0
P15C_execution_authority_added: false
P15C_accepted: false
```

This record is evidence, not execution authority. The separately authorized
P15C runtime implementation and benchmark execution must start from the later
canonical main and revalidate the corrected packet before any credential
resolution or provider call.
