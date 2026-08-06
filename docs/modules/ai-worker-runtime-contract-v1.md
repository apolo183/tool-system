# AI Worker Runtime Module Compound Contract v1

This file defines the contract owned by `ai_worker_runtime`. The default worker
remains deterministic and provider-neutral. The accepted P14C bounded proof is
unchanged. For P15, policy schema 4 exposes an optional API-backup path whose
provider priority and requested models come only from owner-only,
repository-external settings. API mode and every provider are disabled by
default; a credential's presence grants no authority. The generic worker also
has a default-disabled pre-invocation guard for the exact externally selected
provider/model pair. The active backup path uses only the deterministic public fixture and stops after one successful provider. Schema 4 keeps direct verified TLS as the default and permits only an explicitly configured owner-only loopback HTTP CONNECT endpoint for the same verified HTTPS target routes; proxy environment variables and proxy credentials are unsupported and private proxy endpoints never appear in public evidence. Schema 3 remains readable as direct-TLS single-provider compatibility. Schema 1 and schema 2 exact-matrix inputs remain readable as legacy compatibility and do not define the completion route.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/ai-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: ai-worker-runtime
    current_module_id: ai_worker_runtime
    module_version: 2.0.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@efd4d4c306a77fd97b835651e3d5c36796a9778d:ai_worker_runtime@2.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide the provider-neutral worker, deterministic fixtures, generic default-disabled exact-route execution guard, bounded P14C adapter, and source-sealed default-off P15 API-backup runtime
    responsibility_boundary: Preserve the accepted P14C proof and all source-seal, owner-only input, budget, expiry, authorization, transfer, retry, cancellation, reservation, audit, and redaction controls. The generic worker route selector has no credential or transport input, returns API_DISABLED without explicit API mode, chooses at most one externally named enabled and declared-available provider/model, and feeds a guard that rejects request or runtime route drift before invocation. Policy schema 4 reads provider priority and requested model identifiers only from repository-external settings, rejects disabled API mode before credential resolution, permits only the public deterministic fixture, never loads a private target, and stops after one successful route. Disabled, unconfigured, zero-budget, missing-credential, invalid-key, unfunded, moving-alias, or availability-failed providers do not make another enabled eligible route fail. Local policy, data-transfer, hard-budget, cancellation, source-integrity, and response-integrity failures remain non-bypassable. Legacy schemas 1 and 2 preserve their exact two-case matrix behavior; schema 3 preserves the direct-TLS single-provider path. Schema 4 keeps direct verified TLS as default and adds only explicit owner-only loopback CONNECT with no proxy credentials, environment activation, redirect support, or endpoint disclosure. All three adapters retain fixed verified TLS surfaces and injected fake-I/O coverage. No provider execution, stage acceptance, target access, production, cleanup, or rollback occurs in this contract package.
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
      - repository_external_ProviderRouteConfig_v1
      - opaque_single_use_P14CLiveExecutionCapability
      - explicit_P14C_repository_ledger_and_positive_owner_comment_id
      - owner_only_repository_external_P15C_settings_schema_1_2_3_or_4
      - separately_stored_owner_only_P15C_credential_references
      - optional_legacy_content_addressed_P15C_target_packet_and_snapshot
      - owner_only_P15C_atomic_usage_ledger
    boundary: The generic route record contains only provider ID, model ID, explicit enablement, and caller-supplied declared availability; it contains no key, credential value, transport, or implicit authorization. Schema 4 accepts an explicit API-mode switch, positive total budget, expiry, exact source commit and tree, ordered supported-provider subset, provider-specific requested models, provider switches, budgets, transfer switches, and a direct_tls or http_connect transport choice. Direct TLS requires empty proxy fields. HTTP CONNECT requires an owner-only loopback host and bounded port, carries verified TLS only to the existing fixed provider route, ignores environment proxy variables, accepts no proxy credential, and redacts the endpoint from the public policy digest. The disabled public template has API mode false, no priority, empty models, zero total and provider budgets, and every provider and transfer switch false. Enabled prioritized providers require a requested model, but credential presence is never inspected until API mode, route, budget, and transfer policy pass. Schema 4 authorizes only deterministic-corpus and no private target. Static catalog funding or exact-version labels are descriptive adapter evidence, not completion authority; the external policy selects the requested model. Schema 3 remains direct-TLS single-provider compatibility. Schemas 1 and 2 remain legacy exact-matrix inputs, including their target-packet binding and conservative CNY conversion rules. Total configured budget never exceeds 20000000 microUSD.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
      - ProviderRouteSelection_v1
      - P14C_exact_approval_body_and_redacted_execution_receipt
      - P15C_public_catalog_preflight_skip_attempt_and_single_success_receipts
    boundary: The generic selector returns API_DISABLED, INVALID_EXTERNAL_CONFIGURATION, NO_AVAILABLE_PROVIDER, or one ROUTE_SELECTED provider/model with zero credential, provider, and network counters. Runtime execution still requires the exact selected route guard. The P15 path returns structured output, stable sanitized codes, request and output hashes, bounded usage and cost, ordered skip evidence, requested and provider-resolved model identifiers, and a single winning provider when one succeeds. Packet-only output is public and grants no execution authority. Receipts never contain credential values, raw provider output, private repository identity, private commit, private paths, or target bytes.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Disabled or expired policy, malformed external selection, transfer denial, budget exhaustion, source or policy drift, cancellation, replay, request or response integrity failure, and unsafe private-control boundaries return stable sanitized codes and stop. An empty eligible or credential-ready set and an exhausted availability-only chain return NO_AVAILABLE_PROVIDER. Missing or invalid credentials, HTTP authentication or access failure, no funding, unavailable model, rate limit, provider outage, and transport timeout or connection failure are availability-class evidence and may advance only to another already enabled eligible route. There is no same-route retry. Moving aliases may resolve to a different provider-returned model identifier; both requested and resolved identifiers are recorded without inventing an exact version.
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
        boundary: P14C retains its separately guarded historical path. P15 network transport exists only behind explicit execute mode plus active schema-4 policy, an enabled prioritized provider, configured requested model, positive conservative budgets, transfer permission, exact source seal, credential reference, and unused ledger. Routes are fixed to api.deepseek.com/chat/completions, api.openai.com/v1/responses, and dashscope.aliyuncs.com/compatible-mode/v1/chat/completions. The direct path remains default. An explicit schema-4 http_connect selection tunnels only one of those verified HTTPS routes through an owner-only loopback endpoint, never follows redirects, never uses proxy credentials or environment variables, and never emits the endpoint. Hosted CI and this package use injected fake I/O only.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: A future separately authorized schema-4 smoke may submit only the deterministic public fixture, with tools, provider search, streaming, storage, implicit proxy use, proxy credentials, redirects, and same-route retry disabled. Explicit schema-4 loopback CONNECT is transport only and grants no provider authority. It stops after one success and never accesses or mutates a downstream repository.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: P15 writes only reservation, settlement, release, or conservative uncertain-cost state to the caller-selected owner-only usage ledger; it never writes settings, credentials, provider catalog, target packet, snapshot, repository, or source.
      - effect_class: database_write
        evidence_paths:
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: The owner-only single-host SQLite ledger uses exact schema and atomic BEGIN IMMEDIATE budget checks. Existing schema drift blocks, and no multi-host claim is made.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request validation, deterministic defaults, stable errors, the generic default-disabled exact-route guard, P14C authority and replay bindings, schema-1/2 legacy matrix behavior, schema-3 direct single-provider compatibility, schema-4 default-off and external-selection semantics, source sealing, owner-only paths, explicit transfer, total and provider budgets, expiry, zero retry, cancellation, conservative charging, requested/resolved model audit, fixed adapter routes, direct-default verified TLS, explicit owner-only loopback CONNECT without proxy credentials or endpoint disclosure, public-fixture-only smoke, single-success stop, NO_AVAILABLE_PROVIDER, and redaction.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized migration stage.
  rollback_contract:
    rollback_identity: tool-system@efd4d4c306a77fd97b835651e3d5c36796a9778d:ai_worker_runtime@2.0.0
    method: Revert through a separately audited pull request and rerun worker, P14C, schema-1/2/3 compatibility, schema-4 external selection, all-provider fake-I/O, budget, transfer, source-seal, cancellation, ledger, redaction, packet-only, registry, and repository-manifest tests. This contract grants no rollback authority.
  replacement_contract:
    activation_rule: Replace only after provider-neutral worker behavior, generic API-disabled and exact-route-guard tests, the complete P14C suite, legacy matrix compatibility, schema-4 disabled-default, direct-default and explicit CONNECT fake-I/O, external priority and model selection, skip classification, hard-failure non-bypass, all-provider fake-I/O, single-success stop, source seal, owner-only controls, budgets, cancellation, replay, atomic ledger, structured response, requested/resolved model evidence, and redaction pass without real I/O. Adaptive catalog and economics correction remains a dependent independent package.
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
      contract: Execution revalidates canonical origin, expected tree, clean worktree, and critical-source hashes; no repository byte is written.
    data:
      mode: in-memory-plus-owner-only-p15c-ledger
      contract: Requests, fixture bytes, packets, capabilities, credentials, and raw responses remain in process memory. P15 writes only sanitized usage, cost, requested-model, and resolved-model evidence to its ledger.
    artifact:
      mode: stdout-only-redacted-json
      contract: Entries emit only public metadata or redacted receipts and create no receipt file, cache, target projection, raw response artifact, or private-target serialization.
    database:
      mode: delegated-p14c-ledger-plus-direct-owner-only-p15c-usage-ledger
      contract: P14C retains its process-authority ledger boundary. P15 owns one exact single-host usage schema for atomic attempt reservation and settlement.
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
        constraint: Load and revalidate only the exact canonical committed P14C source accepted by process-authority; drift blocks before credential access.
      - root_id: p15c-execution-source-root
        access: read-only
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
          - src/tool_system/ai_worker/p15c_controls.py
          - src/tool_system/ai_worker/p15c_entry.py
        evidence_symbols:
          - build_execution_source_seal
          - P15CBenchmarkExecutor
          - select_p15c_backup_candidates
        boundary_parameters:
          - repository_root
        constraint: Require canonical tool-system origin, expected tree, clean worktree, and hashes for the adapter catalog and execution modules before credential resolution and immediately before transport. Schema 4 obtains provider order and requested models only from owner settings, reads only the public deterministic fixture, and stops after one success. Legacy schema 1, 2, and 3 retain exact-matrix validation.
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
        constraint: Settings and credentials are separate repository-external owner-only files; credential lookup is lazy and occurs only after active route policy passes. Missing credential references become sanitized unavailable evidence, while unsafe file permissions remain hard failures. Target packet and snapshot inputs are legacy-only for schema 1 and 2. Only the usage ledger is writable. Public examples are disabled with zero budgets; Hosted CI uses fake I/O only.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: deepseek-chat-completions-api
        mode: optional-default-disabled-fixed-surface-adapter
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: The P15 adapter uses POST https://api.deepseek.com/chat/completions. A repository-external requested moving alias is permitted and its provider-resolved identifier is recorded; lack of a date-pinned identifier is not a completion blocker. The adapter has fake-I/O evidence and no authority in this package.
      - system_id: openai-responses-api
        mode: optional-default-disabled-fixed-surface-adapter
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
        boundary: The adapter uses POST https://api.openai.com/v1/responses with strict JSON schema, store false, bounded tokens and cost, one attempt, and no tools, redirects, implicit proxy activation, proxy credentials, retry, or fallback authority outside the bounded enabled chain. It has fake-I/O evidence and no authority in this package.
      - system_id: qwen-chat-completions-api
        mode: optional-default-disabled-fixed-surface-adapter
        evidence_paths:
          - src/tool_system/ai_worker/p15c_benchmark.py
          - src/tool_system/ai_worker/p15c_controls.py
        boundary: The adapter uses POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions with JSON-object output, thinking false, bounded tokens, conservative CNY-to-microUSD accounting, one attempt, and no tools, redirects, implicit proxy activation, proxy credentials, retry, or storage. Funding comes from external positive budget configuration; the old catalog funding label is not call authority or a project gate. It has fake-I/O evidence and no authority in this package.
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
