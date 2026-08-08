# Operational Observability Module Compound Contract v1

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/operational-observability-contract-v1.md
  identity:
    canonical_module_id: operational-observability
    current_module_id: operational_observability
    module_version: 1.0.0
    aggregate_interface: {interface_id: operational-observability-api, interface_version: 1.0.0}
    mapping_owner: {contract_path: docs/tool_system_module_registry_contract_v1.md, implementation_path: src/tool_system/architecture/module_registry.py}
    rollback_identity: tool-system@01fffab69a0db3e7110cd6edc7db6f188feb48ab:operational_observability@absent
    python_import_identities:
      - {kind: prefix, name: tool_system.operational_observability}
  role:
    summary: evaluate caller-supplied telemetry against deterministic SLO alert and incident-response policies
    responsibility_boundary: Produce in-memory decisions only; never collect telemetry, deliver alerts, page operators, mutate incidents, deploy systems, or grant production authority.
  natural_owner_evidence_paths:
    - src/tool_system/operational_observability/__init__.py
    - src/tool_system/operational_observability/policy.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: [release_governance]
    direct_consumer_module_ids:
      - record_retention
  input_contract:
    registered_inputs: [telemetry_sample_v1, slo_policy_v1, alert_policy_v1, incident_observation_v1]
    boundary: Accept immutable service release window count threshold and evidence values.
  output_contract:
    registered_outputs: [slo_decision_v1, alert_decision_v1, incident_decision_v1]
    boundary: Return integer PPM metrics stable reasons severity and next state with all external authority false.
  error_contract:
    registered_error_semantics: [invalid_telemetry_raises_value_error, invalid_policy_raises_value_error, missing_evidence_holds_state]
    boundary: Invalid windows counts thresholds transitions or missing evidence fail closed without side effects.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve integer PPM arithmetic ordered reasons monotonic evidence-gated transitions and non-execution.
    interface_incompatible_change: Requires a new aggregate interface version and affected-consumer evidence.
  rollback_contract:
    rollback_identity: tool-system@01fffab69a0db3e7110cd6edc7db6f188feb48ab:operational_observability@absent
    method: Revert through a separately audited pull request.
  replacement_contract:
    activation_rule: Manifest registry SLO alert incident negative-case import-graph focused and full tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository: {mode: none, contract: The module does not discover read or mutate repository state.}
    data: {mode: input-only, contract: Telemetry policies and evidence remain caller-owned immutable values.}
    artifact: {mode: result-only, contract: Decisions remain in memory unless a separately authorized caller persists them.}
    database: {mode: none, contract: The module opens no database and performs no incident operation.}
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
