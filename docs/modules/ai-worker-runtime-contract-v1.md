# AI Worker Runtime Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`ai_worker_runtime` module. The current implementation remains a deterministic
in-memory fixture and does not authorize a live provider.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/ai-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: ai-worker-runtime
    current_module_id: ai_worker_runtime
    module_version: 1.0.0
    aggregate_interface:
      interface_id: ai-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:ai_worker_runtime@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.ai_worker
  role:
    summary: provide a provider-neutral structured AI worker contract and deterministic fixture implementation
    responsibility_boundary: Validate content-addressed requests and execute only deterministic in-memory fixture scenarios with redacted audit records.
  natural_owner_evidence_paths:
    - src/tool_system/ai_worker/__init__.py
    - src/tool_system/ai_worker/contract.py
    - src/tool_system/ai_worker/fixture_provider.py
    - src/tool_system/ai_worker/runtime.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - AIWorkerRequest_v1
    boundary: Accept finite canonical structured input, content hashes, fixture model identity, capability requirements, budgets, and no-mutation flags.
  output_contract:
    registered_outputs:
      - AIWorkerResult_v1
    boundary: Return deterministic structured output, stable provider-neutral errors, usage evidence, output hash, and redacted audit records.
  error_contract:
    registered_error_semantics:
      - stable_redacted_provider_neutral_errors
    boundary: Integrity, capability, provider identity, budget, cancellation, timeout, response, replay, and internal failures return stable sanitized errors.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request validation, error taxonomy, deterministic replay, redaction, budgets, provider metadata checks, and result fields.
    interface_incompatible_change: Requires a new aggregate interface version and a separately authorized provider qualification or migration stage.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:ai_worker_runtime@1.0.0
    method: Revert through a separately audited pull request and rerun contract, fixture-provider, replay, budget, redaction, and no-I/O tests.
  replacement_contract:
    activation_rule: Replace only after provider-neutral contract, deterministic fixture, replay, budget, redaction, and isolation behavior pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: none
      contract: The current AI worker implementation does not read or write a repository.
    data:
      mode: in-memory
      contract: Requests, replay records, fixture scenarios, results, and redacted audit data remain process memory only.
    artifact:
      mode: none
      contract: The current implementation creates no persistent file, cache, projection, or generated artifact.
    database:
      mode: none
      contract: The current implementation owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: explicit-none
    roots: []
  external_system_contracts:
    declaration: explicit-none
    systems: []
  non_claims:
    registry_membership: false
    central_registry_adopted: false
    central_schema_compliance_claimed: false
    central_gate_pass_claimed: false
    governance_activated: false
    provider_execution_authorized: false
    target_repo_mutation_authorized: false
    cleanup_execution_authorized: false
    production_operation_authorized: false
    governance_cutover_completed: false
  authority_boundary:
    execution_authority: false
    governance_authority: false
    evidence_role: s3-contract-reference-input
    next_stage: separately-authorized-s4
~~~
<!-- MODULE-COMPOUND-CONTRACT:END -->
