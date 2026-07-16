# Manifest Validation Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`manifest_validation` module. It does not authorize any command described by
an input change plan.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/manifest-validation-contract-v1.md
  identity:
    canonical_module_id: manifest-validation
    current_module_id: manifest_validation
    module_version: 1.0.0
    aggregate_interface:
      interface_id: manifest-validation-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:manifest_validation@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.manifest
      - kind: prefix
        name: tool_system.gate
      - kind: prefix
        name: tool_system.policy
      - kind: exact
        name: tool_system.cli.validate_task_manifest
      - kind: exact
        name: tool_system.cli.validate_change_plan
      - kind: exact
        name: tool_system.cli.validate_alignment_gate
  role:
    summary: load and validate task manifests, change plans, alignment gates, and repository write policy
    responsibility_boundary: Validate document structure, alignment, scope, policy, and explicit command results without manufacturing authority.
  natural_owner_evidence_paths:
    - src/tool_system/cli/validate_alignment_gate.py
    - src/tool_system/cli/validate_change_plan.py
    - src/tool_system/cli/validate_task_manifest.py
    - src/tool_system/gate/README.md
    - src/tool_system/gate/__init__.py
    - src/tool_system/gate/alignment_gate.py
    - src/tool_system/gate/change_plan.py
    - src/tool_system/gate/command_runner.py
    - src/tool_system/gate/test_gate.py
    - src/tool_system/manifest/__init__.py
    - src/tool_system/manifest/task_manifest.py
    - src/tool_system/policy/__init__.py
    - src/tool_system/policy/autonomy_policy.py
    - src/tool_system/policy/repo_write_policy.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids:
      - architecture_registry
      - cleanup_planner
      - cli_frontend
      - process_authority
      - repository_controller
      - role_runtime
      - target_repo_adapter
      - task_planner
      - task_runner
  input_contract:
    registered_inputs:
      - task_manifest_and_change_plan_yaml
    boundary: Accept caller-supplied YAML, policy mappings, alignment references, and explicitly selected local commands.
  output_contract:
    registered_outputs:
      - validation_decision_and_reasons
    boundary: Return deterministic PASS or BLOCK decisions, structured reasons, and bounded command result records.
  error_contract:
    registered_error_semantics:
      - invalid_or_missing_input_blocks
    boundary: Missing fields, mismatched scope, invalid policy, failed alignment, or nonzero command results fail closed.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes: []
    direct_effects: []
    delegated_effects:
      - Local subprocess effects belong to the caller-authorized command and do not acquire authority from validation or execution routing.
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve required fields, fail-closed policy, result shapes, and explicit caller control over command invocation.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of all direct consumers.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:manifest_validation@1.0.0
    method: Revert through a separately audited pull request and rerun manifest, policy, gate, and dependent-module tests.
  replacement_contract:
    activation_rule: Replace only after manifest, change-plan, alignment, policy, command-result, and direct-consumer compatibility pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-only-by-default
      contract: Validation reads repository-local policy and documents; selected commands remain separately bounded caller actions.
    data:
      mode: caller-owned-input
      contract: YAML mappings, policy mappings, and command results are not persisted by the validation interfaces.
    artifact:
      mode: in-memory-result
      contract: The module returns validation and command result records but does not independently select an artifact path.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-input-and-command-working-roots
        access: read-write
        evidence_paths:
          - src/tool_system/gate/command_runner.py
          - src/tool_system/manifest/task_manifest.py
        evidence_symbols:
          - load_yaml_file
          - run_commands
        boundary_parameters:
          - path
          - cwd
        constraint: YAML paths are read inputs; the command working directory is caller-selected and cannot broaden the supplied authorization envelope.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-command-subprocess
        mode: explicitly invoked caller command
        evidence_paths:
          - src/tool_system/gate/command_runner.py
        boundary: Start only commands explicitly passed to run_commands and report their exit code and output without treating execution as new authority.
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
