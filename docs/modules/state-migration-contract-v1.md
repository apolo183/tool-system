# State Migration Module Compound Contract v1

This file defines the non-executing product-wide state migration and compatibility planning contract owned by the current `state_migration` module.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/state-migration-contract-v1.md
  identity:
    canonical_module_id: state-migration
    current_module_id: state_migration
    module_version: 1.0.0
    aggregate_interface:
      interface_id: state-migration-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@315f4bb08aacf038e0391a0a55553fe1bed67a26:state_migration@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.state_migration
  role:
    summary: validate product-wide migration registries and compatibility matrices and produce deterministic dry-run upgrade or downgrade plans
    responsibility_boundary: Plan only from caller-supplied immutable values; never open state stores, execute migration steps, mutate artifacts, inspect deployments, or grant release authority.
  natural_owner_evidence_paths:
    - src/tool_system/state_migration/__init__.py
    - src/tool_system/state_migration/planner.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - release_governance
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - migration_registry_v1
      - compatibility_matrix_v1
      - migration_plan_request_v1
    boundary: Accept canonical semantic versions, uniquely identified adjacent migration steps, explicit reversibility, product compatibility ranges, and an explicit downgrade flag.
  output_contract:
    registered_outputs:
      - migration_registry_validation_v1
      - state_compatibility_decision_v1
      - migration_dry_run_plan_v1
    boundary: Return immutable direction, ordered step identifiers, status, and stable reason codes; a ready plan remains non-executing.
  error_contract:
    registered_error_semantics:
      - malformed_registry_raises_value_error
      - incompatible_or_unsafe_path_returns_block
    boundary: Duplicate edges, branches, cycles, gaps, unsupported state, implicit downgrade, or irreversible downgrade fail closed without side effects.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve canonical versions, unique linear paths, inclusive compatibility ranges, explicit downgrade opt-in, all-step reversibility, ordered reasons, and non-executing plans.
    interface_incompatible_change: Requires a new aggregate interface version, explicit registry migration, and affected-consumer evidence.
  rollback_contract:
    rollback_identity: tool-system@315f4bb08aacf038e0391a0a55553fe1bed67a26:state_migration@absent
    method: Revert through a separately audited pull request while preserving migration evidence and repository history.
  replacement_contract:
    activation_rule: A replacement becomes current only after registry, compatibility, upgrade, downgrade, gap, cycle, negative-case, module-registry, and import-graph tests pass.
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
      contract: Migration steps, compatibility ranges, and requested versions remain caller-owned immutable values.
    artifact:
      mode: result-only
      contract: Plans exist in memory only unless a separately authorized caller persists or executes them.
    database:
      mode: none
      contract: The module opens no database and performs no schema or state migration.
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
