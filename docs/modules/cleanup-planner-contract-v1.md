# Cleanup Planner Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`cleanup_planner` module. It inventories residue and emits plans; it never
executes cleanup.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/cleanup-planner-contract-v1.md
  identity:
    canonical_module_id: cleanup-planner
    current_module_id: cleanup_planner
    module_version: 1.0.0
    aggregate_interface:
      interface_id: cleanup-planner-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cleanup_planner@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.cleanup
  role:
    summary: inventory residue and emit non-executing cleanup plans
    responsibility_boundary: Classify temporary branch, closed-PR branch, and temporary artifact candidates from caller-supplied state and emit actions with execute false.
  natural_owner_evidence_paths:
    - src/tool_system/cleanup/__init__.py
    - src/tool_system/cleanup/residue_plan.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
      - repository_controller
    direct_consumer_module_ids:
      - cli_frontend
  input_contract:
    registered_inputs:
      - residue_inventory_and_cleanup_authority
    boundary: Accept a caller-supplied residue inventory; the current implementation treats it only as planning input and receives no cleanup authority.
  output_contract:
    registered_outputs:
      - cleanup_plan_without_execution
    boundary: Return deterministic candidate actions, reasons, counts, and false execution and target-mutation flags, optionally with a local audit path.
  error_contract:
    registered_error_semantics:
      - invalid_inventory_or_missing_authority_blocks
    boundary: Malformed branch or pull-request inventory entries block; protected branches and non-temporary artifacts are excluded from candidate actions.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - generated_artifact_write
      - repository_write
    direct_effects:
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/cleanup/residue_plan.py
        boundary: Append the non-executing cleanup plan to the caller-selected JSONL audit path.
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/cleanup/residue_plan.py
        boundary: If the selected audit path is inside an authorized repository, the append-only cleanup-plan evidence is also a repository write.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve protected-branch exclusions, candidate classification, execute false, no-target-mutation flags, result fields, and optional audit writing.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of repository-controller, manifest-validation, and CLI boundaries.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cleanup_planner@1.0.0
    method: Revert through a separately audited pull request; do not execute inverse cleanup or delete retained evidence.
  replacement_contract:
    activation_rule: Replace only after classification, protected-branch, malformed-input, no-execution, audit-write, and CLI tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-and-plan-only
      contract: Repository state is caller-supplied; no branch, pull request, artifact, file, or cache is removed.
    data:
      mode: residue-inventory
      contract: Branch, pull-request, artifact, action, and reason mappings remain non-executing planning data.
    artifact:
      mode: optional-jsonl-plan
      contract: The cleanup plan is a creator-owned local evidence artifact and not a cleanup authorization.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-residue-inventory-and-audit-roots
        access: read-write
        evidence_paths:
          - src/tool_system/cleanup/residue_plan.py
        evidence_symbols:
          - build_cleanup_plan_file
        boundary_parameters:
          - state_path
          - audit_path
        constraint: Read one selected state file and append only the non-executing plan to the selected audit path.
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
