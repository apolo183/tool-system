# Record Retention Module Compound Contract v1

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/record-retention-contract-v1.md
  identity:
    canonical_module_id: record-retention
    current_module_id: record_retention
    module_version: 1.0.0
    aggregate_interface: {interface_id: record-retention-api, interface_version: 1.0.0}
    mapping_owner: {contract_path: docs/tool_system_module_registry_contract_v1.md, implementation_path: src/tool_system/architecture/module_registry.py}
    rollback_identity: tool-system@c1e0e700831ed6ef19056f123722260774a79f2f:record_retention@absent
    python_import_identities:
      - {kind: prefix, name: tool_system.record_retention}
  role:
    summary: evaluate immutable audit run and incident record metadata against retention legal-hold archival and deletion policies
    responsibility_boundary: Produce in-memory index and readiness decisions only; never read records, archive, delete, mutate stores, release holds, or grant execution authority.
  natural_owner_evidence_paths:
    - src/tool_system/record_retention/__init__.py
    - src/tool_system/record_retention/policy.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: [operational_observability]
    direct_consumer_module_ids:
      - production_readiness
  input_contract:
    registered_inputs: [record_metadata_v1, retention_policy_v1, caller_observed_utc_v1]
    boundary: Accept immutable record identity class timestamp hash hold archive and incident-state values.
  output_contract:
    registered_outputs: [retention_index_entry_v1, archive_decision_v1, deletion_decision_v1]
    boundary: Return expiry index and stable readiness reasons with execution authority false.
  error_contract:
    registered_error_semantics: [invalid_metadata_raises_value_error, legal_hold_blocks_deletion, unexpired_or_unarchived_record_blocks_deletion, open_incident_blocks_deletion]
    boundary: Invalid identity hash chronology class policy hold archive or incident closure evidence fails closed.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve deterministic expiry exact hashes legal-hold priority ordered reasons incident closure and non-execution.
    interface_incompatible_change: Requires a new aggregate interface version and affected-consumer evidence.
  rollback_contract:
    rollback_identity: tool-system@c1e0e700831ed6ef19056f123722260774a79f2f:record_retention@absent
    method: Revert through a separately audited pull request without deleting records or evidence.
  replacement_contract:
    activation_rule: Manifest registry index hold archive deletion incident negative-case import-graph focused and full tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository: {mode: none, contract: The module does not discover read or mutate repository state.}
    data: {mode: input-only, contract: Record metadata policy and observation values remain caller-owned and immutable.}
    artifact: {mode: result-only, contract: Index and decisions remain in memory unless separately persisted or executed.}
    database: {mode: none, contract: The module opens no database and performs no archival or deletion.}
  external_root_contracts: {declaration: explicit-none, roots: []}
  external_system_contracts: {declaration: explicit-none, systems: []}
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
