# Recovery Planning Module Compound Contract v1

This file defines the non-live backup manifest, restore verification, and disaster-recovery planning contract owned by the current `recovery_planning` module.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/recovery-planning-contract-v1.md
  identity:
    canonical_module_id: recovery-planning
    current_module_id: recovery_planning
    module_version: 1.0.0
    aggregate_interface:
      interface_id: recovery-planning-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@a4042551e5c2b77e07db30ecdbdb5ae28f618ec7:recovery_planning@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.recovery_planning
  role:
    summary: validate content-addressed backup manifests and produce deterministic non-live restore and disaster-recovery decisions
    responsibility_boundary: Evaluate only caller-supplied metadata and observations; never read backup bytes, open stores, restore data, execute migrations, deploy systems, or grant production authority.
  natural_owner_evidence_paths:
    - src/tool_system/recovery_planning/__init__.py
    - src/tool_system/recovery_planning/planner.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - state_migration
    direct_consumer_module_ids:
      - production_readiness
  input_contract:
    registered_inputs:
      - backup_manifest_v1
      - observed_backup_inventory_v1
      - restore_plan_request_v1
      - non_live_drill_observation_v1
      - recovery_objectives_v1
    boundary: Accept immutable logical names, byte lengths, SHA256 digests, state versions, migration plans, integer UTC epoch seconds, and explicit RPO and RTO limits.
  output_contract:
    registered_outputs:
      - backup_verification_v1
      - restore_plan_v1
      - disaster_recovery_decision_v1
    boundary: Return immutable status, ordered restore entries, measured RPO and RTO, and stable reason codes; ready results remain non-executing.
  error_contract:
    registered_error_semantics:
      - malformed_manifest_raises_value_error
      - missing_extra_or_mismatched_entry_returns_block
      - blocked_migration_or_objective_breach_returns_block
    boundary: Ambiguous identities, invalid hashes, duplicate names, integrity mismatch, unsafe migration, invalid chronology, or RPO and RTO breach fail closed without side effects.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve exact-set content-addressed verification, deterministic restore order, migration-plan gating, integer RPO and RTO calculations, ordered reasons, and non-execution.
    interface_incompatible_change: Requires a new aggregate interface version, backup-format migration, and affected-consumer evidence.
  rollback_contract:
    rollback_identity: tool-system@a4042551e5c2b77e07db30ecdbdb5ae28f618ec7:recovery_planning@absent
    method: Revert through a separately audited pull request while preserving backup, restore, drill, and repository evidence.
  replacement_contract:
    activation_rule: A replacement becomes current only after manifest, exact-set integrity, migration gating, restore ordering, chronology, RPO, RTO, negative-case, registry, and import-graph tests pass.
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
      contract: Backup metadata, observed inventory, migration plans, objectives, and drill observations remain caller-owned immutable values.
    artifact:
      mode: result-only
      contract: Verification and plans exist in memory only unless a separately authorized caller persists or executes them.
    database:
      mode: none
      contract: The module opens no database and performs no backup, restore, migration, or recovery operation.
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
