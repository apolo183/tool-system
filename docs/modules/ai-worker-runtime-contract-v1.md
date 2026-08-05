# AI Worker Runtime Module Compound Contract v1

This file defines the module contract owned by the current
`ai_worker_runtime` module. The default implementation remains a deterministic
in-memory fixture. P14C adds a bounded live-provider adapter behind an exact
process-authority grant and single-use execution capability. P15C adds a
separate, generic, source-sealed read-only benchmark control plane for exact
repository-external operator settings, credential-reference, target-packet,
snapshot, and usage-ledger inputs. The settings and credentials are separate
owner-only files under each installation's local configuration root; the
public repository contains disabled examples only. It fixes the only live
routes to OpenAI Responses, DeepSeek Chat Completions, and the exact
Qwen3.7 Plus snapshot through Alibaba Model Studio Chat Completions. The
current canonical P15C matrix is still fail-closed because
the DeepSeek request API exposes only a moving model alias and cannot bind the
dated catalog version. Packet-only metadata remains public; every private or
live P15C entry blocks before private input. Qwen support is a dormant adapter;
the unchanged canonical packet keeps Qwen outside the execution matrix and
blocked as not funded. The module never serializes credential
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
    module_version: 1.9.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@c4f7527a8a9f859c1f3ed64bfcc93393331dfc14:ai_worker_runtime@1.8.1
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide a provider-neutral structured AI worker contract, deterministic fixture, bounded P14C adapter, and generic source-sealed P15C read-only benchmark control plane with a dormant exact Qwen snapshot adapter and fail-closed native-currency accounting
    responsibility_boundary: Preserve the P14C exact public synthetic proof and every P15C source-seal, private-input, exact-version, budget, transfer, cancellation, redaction, and no-retry invariant while adding an exact qwen3.7-plus-2026-05-26 Chat Completions adapter. The runtime accepts only the legacy DeepSeek/OpenAI matrix or an explicit OpenAI/Qwen matrix, uses fixed direct-TLS routes, and converts Qwen native CNY cost into the shared microUSD ledger with an owner-only conservative accounting ceiling. The unchanged canonical catalog has no explicit matrix, keeps Qwen BLOCKED_NOT_FUNDED, and keeps DeepSeek BLOCKED_EXACT_VERSION_UNPINNABLE, so preflight and execute still block before settings, credentials, target packet, snapshot, ledger, or transport. Hosted CI uses test-local eligible packet copies and fake I/O only. The P15C path performs no repository mutation, tools, provider web search, retry, fallback, proxy, response storage, production, cleanup, or rollback.
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
      - owner_only_repository_external_P15C_settings
      - separately_stored_owner_only_P15C_credential_references
      - caller_supplied_content_addressed_P15C_target_packet_and_snapshot
      - owner_only_P15C_atomic_usage_ledger
    boundary: Accept finite canonical structured input, content hashes, fixture or live model identity, capability requirements, budgets, and mandatory no-mutation flags. P14C additionally accepts its exact hardened approval inputs. P15C first accepts only public packet metadata and requires every configured provider route to be exact-version pinnable. Policy schema 1 remains compatible only with Qwen disabled; schema 2 may explicitly name Qwen switches, transfer, sub-budget, and a conservative CNY-to-microUSD ceiling that is at least 1000000 and never obtained from the network. Total private budget may not exceed 20000000 microUSD. The current canonical DeepSeek disposition blocks before the runtime may accept or read an owner-only settings file, separate credential file, caller-supplied target packet or snapshot, or owner-only SQLite ledger. Private controls cannot bypass a public packet blocker. The public example is disabled, and mutation, retries, tools, provider web search, fallback, proxies, and response storage remain disabled.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
      - P14C_exact_approval_body_and_redacted_execution_receipt
      - P15C_public_preflight_and_aggregate_benchmark_receipts
    boundary: Return structured output, stable errors, bounded usage and cost evidence, output hashes, exact public P14C approval material, and redacted P14C or P15C receipts. P15C packet-only output includes public packet status and execution blocker; blocked private entries return PROVIDER_EXACT_VERSION_UNPINNABLE with zero private-input and live-operation counters. P15C public records contain no credential value, private repository identity, private commit, private path, target content, or raw provider response.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Integrity, authority, exact-version request binding, policy schema, public budget ceiling, native-currency conversion, policy drift after reservation, capability or transport binding, execution commit/tree/source/host/ledger drift, provider identity, credential reference or value shape, private target safety, cancellation, timeout, response, replay, and internal failures return stable sanitized codes. An exact catalog version that cannot be bound by the provider request API returns PROVIDER_EXACT_VERSION_UNPINNABLE before private input. HTTP 401 and 403 remain AUTH_INVALID_KEY and ACCESS_FORBIDDEN without provider response details; an uncertain post-transport outcome conservatively consumes the full converted reservation and is never retried.
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
        boundary: P14C retains its one guarded DeepSeek request. The current canonical P15C packet set issues no request because its DeepSeek route cannot bind the dated catalog version, so preflight, execute, and direct executor entry fail before private controls or transport. The lower verified direct-TLS implementation is bounded to api.deepseek.com/chat/completions, api.openai.com/v1/responses, and dashscope.aliyuncs.com/compatible-mode/v1/chat/completions. The Qwen route is exercised only through injected fake I/O with an explicit test-local OpenAI/Qwen matrix and eligible packet copy. Packet-only and all tests issue no provider request.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: The current canonical P15C packet set submits no snapshot bytes because its exact-version eligibility check blocks before target input. A future separately audited exact-version-pinnable matrix would still require public packet eligibility, exact private policy, target-packet authority, and per-provider transfer switches. Qwen requests additionally bind the exact dated model, disable thinking, and retain JSON output, no tools, no provider web search, no retry or fallback, and no raw-response persistence.
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
    interface_compatible_replacement: Preserve request validation, stable redacted errors, deterministic fixture defaults, all P14C authority and replay bindings, and every P15C exact-version eligibility guard, source seal, owner-only input, opaque reference, target safety, provider-specific private transfer, exact route/model/matrix, legacy-policy Qwen disablement, schema-2 currency ceiling, public total budget ceiling, cancellation, conservative reservation and failure charging, no-retry, no-tool, no-proxy, no-storage, and public-redaction invariant.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized provider qualification or migration stage.
  rollback_contract:
    rollback_identity: tool-system@c4f7527a8a9f859c1f3ed64bfcc93393331dfc14:ai_worker_runtime@1.8.1
    method: Revert through a separately audited pull request and rerun contract, fixture-provider, P14C operator-entry and adapter, P15C repository-external settings and credentials, private-control, Hosted fake-I/O, cancellation, ledger, source-seal, budget, redaction, and packet-only no-I/O tests. This contract grants no rollback authority.
  replacement_contract:
    activation_rule: Replace only after provider-neutral and deterministic behavior, the complete P14C contract, and the complete P15C exact-version blocker, source seal, owner-only controls, schema compatibility, fixed Qwen route, native-currency accounting, injected OpenAI/Qwen fake matrix, cancellation, replay block, atomic ledger, conservative budget, structured response, and redaction suites pass with no real I/O. Changing the current canonical matrix or Qwen funding disposition requires a separate adaptive-portfolio packet correction.
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
        constraint: Parse only the legacy DeepSeek/OpenAI matrix or an explicit OpenAI/Qwen matrix, require every selected public provider packet to be exact-version execution-eligible before any private input, then require canonical tool-system origin, an exact canonical tree, clean worktree, and content hashes for the frozen packet config and all P15C execution modules before credential resolution and again immediately before every transport attempt. The current unchanged DeepSeek disposition blocks at the first eligibility requirement.
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
        constraint: Default settings, credentials, and target-packet paths resolve under ~/.config/tool-system while the default usage ledger resolves under ~/.local/state/tool-system; callers may select other repository-external paths. Each private path must resolve to an owner-only, non-symlink boundary. Settings and credentials remain separate files, credential values are read only through exact opaque references and never written or serialized, target files are exact content-addressed UTF-8 regular files, and only the separate usage ledger is writable. Policy schema 2 stores the adjustable non-secret CNY accounting ceiling and provider budgets; schema 1 may not enable Qwen. Public examples are disabled and contain no credential values; Hosted CI may exercise only synthetic or injected fake I/O.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: deepseek-chat-completions-api
        mode: p14c-optional-live-plus-p15c-blocked-exact-version-unpinnable
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: P14C retains its exact public fixture path. For P15C, the official catalog version is DeepSeek-V4-Flash-0731 but POST https://api.deepseek.com/chat/completions accepts only the moving request model ID deepseek-v4-flash; the canonical P15C route therefore returns PROVIDER_EXACT_VERSION_UNPINNABLE before any private-control credential reference, target input, ledger, or transport access.
      - system_id: openai-responses-api
        mode: optional-explicitly-guarded-p15c-read-only-provider
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: The OpenAI packet remains individually configured for exact model gpt-5.6-luna at POST https://api.openai.com/v1/responses with strict JSON schema output, store false, 2048 requested output tokens, a 25000 microUSD hard cap, one attempt, and no tools, redirects, proxy environment, retry, storage, or fallback. The canonical two-provider P15C matrix is nevertheless blocked before private input by the DeepSeek exact-version disposition, so no OpenAI P15C call is currently eligible.
      - system_id: qwen-chat-completions-api
        mode: dormant-exact-snapshot-adapter-fake-io-only
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: The dormant adapter binds qwen3.7-plus-2026-05-26 at POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions with JSON-object output, enable_thinking false, 2048 requested output tokens, a 250000 microCNY native hard cap converted upward through the owner-only accounting ceiling, one attempt, and no tools, redirects, proxy environment, retry, storage, or fallback. The unchanged canonical catalog excludes Qwen from the matrix and marks it BLOCKED_NOT_FUNDED, so this adapter has no live authority.
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
