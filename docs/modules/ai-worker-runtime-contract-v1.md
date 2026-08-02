# AI Worker Runtime Module Compound Contract v1

This file defines the module contract owned by the current
`ai_worker_runtime` module. The default implementation remains a deterministic
in-memory fixture. P14C adds a bounded live-provider adapter behind an exact
process-authority grant and single-use execution capability. The committed
operator entry prepares exact approval JSON separately from execution, is
included in the source seal, and emits only redacted receipts. This source does
not create a real approval comment or authorize a live provider call. Credential
whitespace is rejected before transport, and live HTTP 401 and 403 responses
produce distinct stable redacted failure classes.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/ai-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: ai-worker-runtime
    current_module_id: ai_worker_runtime
    module_version: 1.6.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@d9c211324487e3bfd31c1276763ed2ed781cc085:ai_worker_runtime@1.5.1
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide a provider-neutral structured AI worker contract, deterministic fixture, bounded live adapter, and committed source-sealed P14C operator entry
    responsibility_boundary: Validate content-addressed requests, default to deterministic in-memory fixtures, prepare exact source-bound approval JSON without external reads, reject credential whitespace before transport, keep HTTP 401 invalid-key and HTTP 403 forbidden-access outcomes distinctly redacted, and admit only the exact public P14C synthetic request through the frozen DeepSeek V4 Flash recovery adapter when a durably consumed process-authority grant has minted a capability bound to the same packet, request, exact live transport instance, clean execution commit/tree/critical-source manifest including the operator entry, host, and ledger identity.
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
      - explicit_P14C_repository_ledger_and_positive_owner_comment_id
    boundary: Accept finite canonical structured input, content hashes, fixture or live model identity, capability requirements, budgets, mandatory no-mutation flags, and—only through the committed operator entry—an exact repository root, hardened ledger path, positive owner-comment ID, and unexpired opaque capability derived from one authenticated durably consumed process-authority grant bound to the same transport object and current execution source seal.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
      - P14C_exact_approval_body_and_redacted_execution_receipt
    boundary: Return structured output, stable provider-neutral errors, bounded usage evidence, output hash, an exact public approval body during preparation, and redacted execution receipts without credential values or raw provider output.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Integrity, grant or capability binding, capability expiry, transport-instance identity, execution commit/tree/source/host/ledger drift, provider identity, credential whitespace, budget, cancellation, timeout, response, replay, and internal failures return stable sanitized errors; live HTTP 401 and 403 remain distinct as AUTH_INVALID_KEY and ACCESS_FORBIDDEN without exposing provider response details.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes:
      - network_write
      - external_system_write
    direct_effects:
      - effect_class: network_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: The committed execute entry can reach the optional transport, which may issue one exact TLS-verified POST to api.deepseek.com/chat/completions only after source, ledger, owner approval, packet, request, guard, cancellation, owner-only local credential-file reference, and budget preflight succeed.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: The execute entry can submit only public fixture P14C-001 to the exact DeepSeek V4 Flash Chat Completions endpoint with thinking disabled and no fallback; prepare, packet-only evidence, default runtime guards, and all tests perform no external provider call.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request validation, stable redacted error taxonomy including distinct invalid-key and forbidden-access classes, deterministic replay, default fixture-only execution, separate prepare and execute commands, process-authority durable grant, exact live-capability and operator-entry source-seal binding, immediate pre-credential revalidation, credential-whitespace rejection, redaction, budgets, provider metadata checks, and result fields.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized provider qualification or migration stage.
  rollback_contract:
    rollback_identity: tool-system@d9c211324487e3bfd31c1276763ed2ed781cc085:ai_worker_runtime@1.5.1
    method: Revert through a separately audited pull request and rerun contract, fixture-provider, operator-entry, live-adapter fake-transport, replay, budget, redaction, and packet-only no-I/O tests.
  replacement_contract:
    activation_rule: Replace only after provider-neutral contract, deterministic fixture, committed prepare/execute entry, process-authority durable grant, exact transport/operator-source-bound capability, fake GitHub and provider transports, source-drift-before-credential, replay, receipt redaction, budget, and isolation behavior pass with no real I/O.
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
      mode: stdout-only-redacted-json
      contract: The operator entry emits exact public approval JSON during preparation or a redacted execution receipt; it creates no receipt file, cache, projection, or other generated artifact.
    database:
      mode: delegated-single-host-ledger
      contract: The operator entry asks process-authority to open the caller-selected hardened ledger; durable-orchestrator owns initialization and burn-on-claim writes, while AI-worker owns no schema or migration.
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
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: deepseek-chat-completions-api
        mode: optional-explicitly-guarded-live-provider
        evidence_paths:
          - src/tool_system/ai_worker/live_provider.py
        boundary: Only the execute command may reach exact POST https://api.deepseek.com/chat/completions for exact model deepseek-v4-flash, public fixture P14C-001, JSON mode, thinking disabled, one 128-token output ceiling, one transport attempt, no tools, redirects, proxy environment, or fallback, and owner-only local credential reference file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key resolved only after all preflight checks; prepare performs no credential or provider access.
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
