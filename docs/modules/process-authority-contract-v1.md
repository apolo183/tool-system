# Process Authority Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`process_authority` module. The explicit task pair remains current authority;
legacy inputs remain non-executing replay only.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/process-authority-contract-v1.md
  identity:
    canonical_module_id: process-authority
    current_module_id: process_authority
    module_version: 2.0.0
    aggregate_interface:
      interface_id: process-authority-api
      interface_version: 2.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:process_authority@2.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.process_authority
      - kind: exact
        name: tool_system.runner.active_gate_resolver
      - kind: exact
        name: tool_system.cli.validate_active_gates
      - kind: exact
        name: tool_system.cli.validate_process_authority
  role:
    summary: require one explicit current task pair and validate non-authoritative content-addressed legacy replay
    responsibility_boundary: Validate the current process-authority contract, one exact manifest/change-plan pair, and the pinned non-executing legacy replay snapshot.
  natural_owner_evidence_paths:
    - config/process_authority_schema_v1.json
    - config/process_authority_v1.yaml
    - config/replay_snapshot_v1.yaml
    - docs/process_authority_contract_v1.md
    - src/tool_system/cli/validate_active_gates.py
    - src/tool_system/cli/validate_process_authority.py
    - src/tool_system/process_authority/__init__.py
    - src/tool_system/process_authority/contract.py
    - src/tool_system/runner/active_gate_resolver.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
    direct_consumer_module_ids:
      - task_planner
      - task_runner
  input_contract:
    registered_inputs:
      - explicit_manifest_change_plan_pair
      - explicit_non_authoritative_legacy_replay_request
    boundary: Accept one explicit current pair or one explicit request to validate the canonical content-addressed legacy replay inputs.
  output_contract:
    registered_outputs:
      - validated_explicit_pair_or_content_addressed_replay_result
    boundary: Return exact binding mode, replay status, hashes, counts, no-mutation flags, and structured fail-closed reasons.
  error_contract:
    registered_error_semantics:
      - missing_mismatched_implicit_or_drifted_input_blocks
    boundary: Missing pair members, mismatched references, symlinks, escaped paths, duplicate pairs, changed hashes, implicit index use, or replay execution requests block.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve explicit-pair default, exact binding, canonical replay hashes, replay-only non-authority, result fields, and caller defaults.
    interface_incompatible_change: Requires a new aggregate interface version and explicit migration of every current caller.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:process_authority@2.0.0
    method: Revert through a separately audited pull request while retaining legacy inputs and replay evidence until separate cleanup authorization.
  replacement_contract:
    activation_rule: Replace only after schema, current-pair, replay snapshot, active-gate adapter, planner, runner, and no-command-on-failure tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-only
      contract: Read process authority, explicit pair files, replay snapshot, legacy index, and hashed source files without modifying them.
    data:
      mode: content-addressed-input
      contract: Current pair identity and legacy replay hashes are validation inputs; replay data never becomes execution authority.
    artifact:
      mode: result-only
      contract: Validation returns structured in-memory results and does not create a process packet, projection, or cache.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-process-document-roots
        access: read-only
        evidence_paths:
          - src/tool_system/process_authority/contract.py
        evidence_symbols:
          - validate_explicit_task_pair
          - validate_process_authority
        boundary_parameters:
          - task_manifest_path
          - change_plan_path
          - authority_path
          - repo_root
        constraint: Resolve explicit inputs under their selected repository context, reject symlinks and escapes, and never use a repository index implicitly.
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
