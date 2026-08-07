# Release Governance Module Compound Contract v1

This file defines the non-authorizing release, version, compatibility, and deprecation contract owned by the current `release_governance` module.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/release-governance-contract-v1.md
  identity:
    canonical_module_id: release-governance
    current_module_id: release_governance
    module_version: 1.0.0
    aggregate_interface:
      interface_id: release-governance-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@c35be57de6ff1f7e31446469281fa369f529d937:release_governance@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.release_governance
  role:
    summary: evaluate semantic versions, compatibility windows, deprecation clocks, and release-candidate evidence
    responsibility_boundary: Return deterministic non-authorizing decisions from caller-supplied values without reading clocks, repositories, credentials, networks, or deployment state.
  natural_owner_evidence_paths:
    - src/tool_system/release_governance/__init__.py
    - src/tool_system/release_governance/policy.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - semantic_version_v1
      - compatibility_window_v1
      - deprecation_record_v1
      - release_candidate_evidence_v1
    boundary: Accept immutable caller-supplied versions, integer UTC epoch seconds, release channel, compatibility checks, and sealed-evidence flags.
  output_contract:
    registered_outputs:
      - compatibility_decision_v1
      - deprecation_decision_v1
      - release_candidate_decision_v1
    boundary: Return immutable status and ordered reason codes; eligibility means only eligible for a separate release authorization.
  error_contract:
    registered_error_semantics:
      - invalid_input_raises_value_error
      - incompatible_or_incomplete_returns_block
    boundary: Malformed versions, invalid windows, non-monotonic timestamps, or incomplete evidence fail closed without side effects.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve semantic-version ordering, inclusive support windows, monotonic deprecation transitions, ordered reason codes, and the non-authorizing eligibility boundary.
    interface_incompatible_change: Requires a new aggregate interface version and explicit downstream migration evidence.
  rollback_contract:
    rollback_identity: tool-system@c35be57de6ff1f7e31446469281fa369f529d937:release_governance@absent
    method: Revert through a separately audited pull request while preserving release evidence and repository history.
  replacement_contract:
    activation_rule: A replacement becomes current only after interface, ordering, window, deprecation, negative-case, registry, and import-graph tests pass.
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
      contract: The module does not discover, read, or mutate repository state.
    data:
      mode: input-only
      contract: Versions, timestamps, checks, and evidence flags remain caller-owned immutable values.
    artifact:
      mode: result-only
      contract: Decisions exist in memory only unless a separately authorized caller persists them.
    database:
      mode: none
      contract: The module owns no database connection, schema, migration, or write.
  external_root_contracts:
    declaration: explicit-none
    roots: []
  external_system_contracts:
    declaration: explicit-none
    systems: []
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
