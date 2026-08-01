# AI Worker Runtime Module Compound Contract v1

This file defines the module contract owned by the current
`ai_worker_runtime` module. The default implementation remains a deterministic
in-memory fixture. P14C adds a bounded live-provider adapter behind an exact
process-authority grant and single-use execution capability; this contract
revalidates the exact source seal immediately before each credential access,
but does not create a real approval record or authorize a live provider call.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/ai-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: ai-worker-runtime
    current_module_id: ai_worker_runtime
    module_version: 1.3.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2c325f20f4c7a2b531725463b98572dee5f70967:ai_worker_runtime@1.2.0
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide a provider-neutral structured AI worker contract, deterministic fixture, and bounded live-adapter implementation
    responsibility_boundary: Validate content-addressed requests, default to deterministic in-memory fixtures, and admit only the exact public P14C synthetic request when a durably consumed process-authority grant has minted a capability bound to the same packet, request, exact live transport instance, clean execution commit/tree/critical-source manifest, host, and ledger identity.
  natural_owner_evidence_paths:
    - src/tool_system/ai_worker/__init__.py
    - src/tool_system/ai_worker/contract.py
    - src/tool_system/ai_worker/fixture_provider.py
    - src/tool_system/ai_worker/live_evidence.py
    - src/tool_system/ai_worker/live_provider.py
    - src/tool_system/ai_worker/runtime.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - process_authority
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - AIWorkerRequest_v1
      - opaque_single_use_P14CLiveExecutionCapability
    boundary: Accept finite canonical structured input, content hashes, fixture or live model identity, capability requirements, budgets, mandatory no-mutation flags, and—only for live execution—an unexpired opaque capability derived from one authenticated durably consumed process-authority grant and bound to the same transport object and current execution source seal.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
    boundary: Return structured output, stable provider-neutral errors, bounded usage evidence, output hash, and redacted audit records without prompt, response, or credential values.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Integrity, grant or capability binding, capability expiry, transport-instance identity, execution commit/tree/source/host/ledger drift, provider identity, budget, cancellation, timeout, response, replay, and internal failures return stable sanitized errors before credential or provider access whenever preflight fails.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes:
      - network_write
      - external_system_write
    direct_effects:
      - effect_class: network_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: The optional transport can issue one exact TLS-verified POST to api.openai.com/v1/responses per bounded attempt only after packet, request, guard, cancellation, credential-reference, and budget preflight succeed.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: The optional adapter can submit only public fixture P14C-001 to the exact OpenAI Responses endpoint through an injected transport; default runtime guards, packet-only evidence, and all tests perform no external call.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request validation, error taxonomy, deterministic replay, default fixture-only execution, process-authority durable grant, exact live-capability and source-seal binding, immediate pre-credential revalidation, redaction, budgets, provider metadata checks, and result fields.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized provider qualification or migration stage.
  rollback_contract:
    rollback_identity: tool-system@2c325f20f4c7a2b531725463b98572dee5f70967:ai_worker_runtime@1.2.0
    method: Revert through a separately audited pull request and rerun contract, fixture-provider, live-adapter fake-transport, replay, budget, redaction, and packet-only no-I/O tests.
  replacement_contract:
    activation_rule: Replace only after provider-neutral contract, deterministic fixture, process-authority durable grant, exact transport/source-bound capability, fake GitHub and provider transports, source-drift-before-credential, replay, budget, redaction, and isolation behavior pass with no real I/O.
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
      mode: in-memory
      contract: Requests, fixture scenarios, execution packets, source seals, capabilities, results, and redacted audit data remain process memory only; durable replay records remain owned by durable-orchestrator.
    artifact:
      mode: none
      contract: The current implementation creates no persistent file, cache, projection, or generated artifact.
    database:
      mode: delegated-read-only-ledger-identity
      contract: The current implementation owns no database connection, schema, migration, or write; source revalidation reads the immutable ledger identity through process-authority and durable-orchestrator.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: p14c-execution-source-root
        access: read-only
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        evidence_symbols:
          - issue_p14c_live_network_capability
          - OpenAIResponsesProvider
        boundary_parameters:
          - repository_root
        constraint: Use only the exact clean source seal returned and revalidated by process-authority; drift blocks before credential access.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: openai-responses-api
        mode: optional-explicitly-guarded-live-provider
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: Exact POST https://api.openai.com/v1/responses for model gpt-5.6-luna, public fixture P14C-001, strict structured output, fixed budgets, no tools, no redirects, no proxy environment, no fallback, and credential reference env:OPENAI_API_KEY resolved only after all preflight checks.
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
