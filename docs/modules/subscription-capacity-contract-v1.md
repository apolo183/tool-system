# Subscription Capacity Module Compound Contract v1

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/subscription-capacity-contract-v1.md
  identity:
    canonical_module_id: subscription-capacity
    current_module_id: subscription_capacity
    module_version: 1.0.0
    aggregate_interface: {interface_id: subscription-capacity-api, interface_version: 1.0.0}
    mapping_owner: {contract_path: docs/tool_system_module_registry_contract_v1.md, implementation_path: src/tool_system/architecture/module_registry.py}
    rollback_identity: tool-system@e6aaa4b0af3b16d48dd5e151b8374810bc29d5fa:subscription_capacity@absent
    python_import_identities:
      - {kind: prefix, name: tool_system.subscription_capacity}
  role:
    summary: evaluate caller-supplied subscription capacity windows and renewal dates and choose a deterministic owner-gated channel recommendation
    responsibility_boundary: Produce in-memory decisions only; never inspect accounts, call providers, purchase, renew, switch channels, or grant external authority.
  natural_owner_evidence_paths:
    - src/tool_system/subscription_capacity/__init__.py
    - src/tool_system/subscription_capacity/policy.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: [release_governance]
    direct_consumer_module_ids:
      - production_readiness
  input_contract:
    registered_inputs: [capacity_snapshot_v1, capacity_policy_v1, subscription_decision_set_v1]
    boundary: Accept immutable channel version capacity usage observation reset renewal enablement and threshold values.
  output_contract:
    registered_outputs: [subscription_decision_v1, portfolio_decision_v1]
    boundary: Return integer PPM status stable reasons and optional preferred channel with all external authority false.
  error_contract:
    registered_error_semantics: [invalid_snapshot_raises_value_error, invalid_thresholds_raise_value_error, duplicate_channels_raise_value_error, no_eligible_channel_returns_none]
    boundary: Invalid capacity chronology thresholds duplication disablement exhaustion or absence fails closed.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve integer PPM threshold ordering explicit enablement deterministic channel ordering owner review and non-execution.
    interface_incompatible_change: Requires a new aggregate interface version and affected-consumer evidence.
  rollback_contract:
    rollback_identity: tool-system@e6aaa4b0af3b16d48dd5e151b8374810bc29d5fa:subscription_capacity@absent
    method: Revert through a separately audited pull request without modifying subscriptions.
  replacement_contract:
    activation_rule: Manifest registry capacity threshold renewal disablement portfolio negative-case import-graph focused and full tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository: {mode: none, contract: The module does not discover read or mutate repository state.}
    data: {mode: input-only, contract: Subscription snapshots and policies remain caller-owned immutable values.}
    artifact: {mode: result-only, contract: Decisions remain in memory unless separately persisted or acted upon.}
    database: {mode: none, contract: The module opens no database and performs no subscription action.}
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
