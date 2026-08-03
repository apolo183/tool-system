# AI Worker Runtime Module Compound Contract v1

This file defines the module contract owned by the current
`ai_worker_runtime` module. The default implementation remains a deterministic
in-memory fixture. P14C adds a bounded live-provider adapter behind an exact
process-authority grant and single-use execution capability. P15C adds a
separate, generic, source-sealed read-only benchmark control plane for exact
operator-private policy, credential-reference, target-packet, snapshot, and
usage-ledger inputs. It fixes the only live routes to OpenAI Responses and
DeepSeek Chat Completions, keeps Qwen disabled, and never serializes credential
values, private target identity or paths, target bytes, or raw provider output
into public evidence. The contract describes these capabilities but grants no
execution authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/ai-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: ai-worker-runtime
    current_module_id: ai_worker_runtime
    module_version: 1.7.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@1019b719547fe0b38341821e968dcae57a1f3697:ai_worker_runtime@1.6.0
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide a provider-neutral structured AI worker contract, deterministic fixture, bounded P14C adapter, and generic source-sealed P15C read-only benchmark control plane
    responsibility_boundary: Preserve the P14C exact public synthetic proof while validating owner-only P15C policy, opaque credential references, caller-supplied content-addressed target packets and snapshots, a clean canonical execution tree, an atomic cumulative cost ledger, the exact two-provider by two-case matrix, fixed direct-TLS routes, structured JSON responses, cancellation, conservative cost settlement, and public evidence redaction. The P15C path performs no repository mutation, tools, provider web search, retry, fallback, proxy, response storage, production, cleanup, or rollback.
  natural_owner_evidence_paths:
    - src/tool_system/ai_worker/__init__.py
    - src/tool_system/ai_worker/contract.py
    - src/tool_system/ai_worker/fixture_provider.py
    - src/tool_system/ai_worker/live_evidence.py
    - src/tool_system/ai_worker/live_provider.py
    - src/tool_system/ai_worker/p15c_benchmark.py
    - src/tool_system/ai_worker/p15c_controls.py
    - src/tool_system/ai_worker/p15c_entry.py
    - src/tool_system/ai_worker/runtime.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - process_authority
    direct_consumer_module_ids:
      - adaptive_model_portfolio_and_economics
  input_contract:
    registered_inputs:
      - AIWorkerRequest_v1
      - opaque_single_use_P14CLiveExecutionCapability
      - explicit_P14C_repository_ledger_and_positive_owner_comment_id
      - owner_only_P15C_execution_policy_and_credential_references
      - caller_supplied_content_addressed_P15C_target_packet_and_snapshot
      - owner_only_P15C_atomic_usage_ledger
    boundary: Accept finite canonical structured input, content hashes, fixture or live model identity, capability requirements, budgets, and mandatory no-mutation flags. P14C additionally accepts its exact hardened approval inputs. P15C accepts only an owner-only, expiring policy at or below the public 20 USD ceiling; exact opaque OpenAI and DeepSeek credential references; a caller-supplied exact commit and sorted content-addressed UTF-8 allowlist; an owner-only snapshot root; and an owner-only SQLite ledger. Qwen, mutation, retries, tools, provider web search, fallback, proxies, and response storage remain disabled.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
      - P14C_exact_approval_body_and_redacted_execution_receipt
      - P15C_public_preflight_and_aggregate_benchmark_receipts
    boundary: Return structured output, stable errors, bounded usage and cost evidence, output hashes, exact public P14C approval material, and redacted P14C or P15C receipts. P15C public records contain no credential value, private repository identity, private commit, private path, target content, or raw provider response.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Integrity, authority, policy expiry, capability or transport binding, execution commit/tree/source/host/ledger drift, provider identity, credential reference or value shape, private target safety, budget, cancellation, timeout, response, replay, and internal failures return stable sanitized codes. HTTP 401 and 403 remain AUTH_INVALID_KEY and ACCESS_FORBIDDEN without provider response details; an uncertain post-transport outcome conservatively consumes the full reserved attempt cap and is never retried.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes:
      - network_write
      - external_system_write
      - data_write
      - database_write
    direct_effects:
      - effect_class: network_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: P14C retains its one guarded DeepSeek request. A separately authorized P15C execute entry may issue only the exact two-provider by two-case matrix through verified direct TLS to api.deepseek.com/chat/completions and api.openai.com/v1/responses after repeated source, policy, target-transfer, credential-reference, cancellation, request, and atomic budget checks. Packet-only, preflight, and all tests issue no provider request.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: P15C submits supplied snapshot bytes only when both the public lifecycle and exact private policy and per-provider transfer switches authorize it. Requests use the frozen model and surface, structured JSON, no tools, no provider web search, no retry or fallback, and no raw-response persistence.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: P15C writes only reservation, settlement, release, or conservative uncertain-cost state to the caller-selected owner-only usage ledger; it never writes the credential store, policy, target packet, snapshot, target repository, or tool-system source.
      - effect_class: database_write
        evidence_paths:
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: P15C initializes and transactionally updates one owner-only single-host SQLite usage ledger with exact schema and atomic BEGIN IMMEDIATE budget checks. Existing schema drift blocks; the ledger is not a multi-host coordination claim.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request validation, stable redacted errors, deterministic fixture defaults, all P14C authority and replay bindings, and every P15C source seal, owner-only input, opaque reference, target safety, private transfer, exact route/model/matrix, Qwen-disablement, cancellation, budget reservation, conservative failure charging, no-retry, no-tool, no-proxy, no-storage, and public-redaction invariant.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized provider qualification or migration stage.
  rollback_contract:
    rollback_identity: tool-system@1019b719547fe0b38341821e968dcae57a1f3697:ai_worker_runtime@1.6.0
    method: Revert through a separately audited pull request and rerun contract, fixture-provider, P14C operator-entry and adapter, P15C private-control, fake-transport, cancellation, ledger, source-seal, budget, redaction, and packet-only no-I/O tests. This contract grants no rollback authority.
  replacement_contract:
    activation_rule: Replace only after provider-neutral and deterministic behavior, the complete P14C contract, and the complete P15C source seal, owner-only controls, exact matrix, injected fake transport, cancellation, replay block, atomic ledger, conservative budget, structured response, and redaction suites pass with no real I/O.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: delegated-read-only-source-seal
      contract: Live capability construction and invocation revalidate the caller-selected canonical tool-system checkout through process-authority; no repository bytes are written.
    data:
      mode: in-memory-plus-owner-only-p15c-ledger
      contract: Requests, fixture scenarios, packets, target bytes, source seals, capabilities, results, credentials, and raw responses remain process memory only. Durable P14C replay remains owned by durable-orchestrator; P15C writes only sanitized aggregate usage and cost state to its caller-selected owner-only SQLite ledger.
    artifact:
      mode: stdout-only-redacted-json
      contract: Operator entries emit exact public approval JSON or redacted receipts to stdout. P15C emits hashes and aggregate metrics only and creates no receipt file, cache, target projection, raw response artifact, or private-target serialization.
    database:
      mode: delegated-p14c-ledger-plus-direct-owner-only-p15c-usage-ledger
      contract: P14C retains its process-authority ledger boundary. P15C owns one versioned single-host SQLite usage schema solely for atomic attempt reservation and settlement; exact shape drift blocks and no multi-host exactly-once guarantee is claimed.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: p14c-execution-source-root
        access: read-only
        evidence_paths:
          - src/tool_system/ai_worker/live_evidence.py
          - src/tool_system/ai_worker/live_provider.py
        evidence_symbols:
          - build_prepare_approval_evidence
          - execute_p14c_live_entry
          - issue_p14c_live_network_capability
          - DeepSeekChatCompletionsProvider
        boundary_parameters:
          - repository_root
        constraint: Load the canonical committed operator module and use only the exact clean source seal returned and revalidated by process-authority; missing entry source or any drift blocks before approval read or credential access.
      - root_id: p15c-execution-source-root
        access: read-only
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
          - src/tool_system/ai_worker/p15c_controls.py
          - src/tool_system/ai_worker/p15c_entry.py
        evidence_symbols:
          - build_execution_source_seal
          - P15CBenchmarkExecutor
        boundary_parameters:
          - repository_root
        constraint: Require canonical tool-system origin, an exact canonical tree, clean worktree, and content hashes for the frozen packet config and all P15C execution modules before credential resolution and again immediately before every transport attempt.
      - root_id: p15c-operator-private-input-root
        access: read-write
        evidence_paths:
          - src/tool_system/ai_worker/p15c_controls.py
        evidence_symbols:
          - load_execution_policy
          - OwnerOnlyCredentialResolver
          - load_target_packet
          - load_target_snapshot
          - P15CUsageLedger
        boundary_parameters:
          - path
          - snapshot_root
        constraint: Each caller-supplied private path must resolve to an owner-only, non-symlink boundary. Credential values are read only through exact opaque references and never written or serialized; target files are exact content-addressed UTF-8 regular files; only the separate usage ledger is writable.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: deepseek-chat-completions-api
        mode: optional-explicitly-guarded-live-provider
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: P14C retains its exact public fixture path. P15C may use exact model deepseek-v4-flash at POST https://api.deepseek.com/chat/completions with JSON object mode, thinking disabled, 2048 requested output tokens, a 25000 microUSD hard cap, one attempt, and no tools, redirects, proxy environment, retry, storage, or fallback. Only the exact private-control credential reference may resolve after all checks.
      - system_id: openai-responses-api
        mode: optional-explicitly-guarded-p15c-read-only-provider
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: P15C may use exact model gpt-5.6-luna at POST https://api.openai.com/v1/responses with strict JSON schema output, store false, 2048 requested output tokens, a 25000 microUSD hard cap, one attempt, and no tools, redirects, proxy environment, retry, storage, or fallback. Only the exact private-control credential reference may resolve after all checks.
  non_claims:
    provider_execution_authorized: false
    target_repo_mutation_authorized: false
    cleanup_execution_authorized: false
    production_operation_authorized: false
  authority_boundary:
    execution_authority: false
    downstream_authority: false
    evidence_role: tool-system-module-contract
    change_boundary: separately-audited-module-change
~~~
<!-- MODULE-COMPOUND-CONTRACT:END -->
