# Task Planner Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`task_planner` module. Generated plans remain local artifacts and do not grant
execution authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/task-planner-contract-v1.md
  identity:
    canonical_module_id: task-planner
    current_module_id: task_planner
    module_version: 1.1.0
    aggregate_interface:
      interface_id: task-planner-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_planner@1.1.0
    python_import_identities:
      - kind: prefix
        name: tool_system.planner
  role:
    summary: compile requirements and task graphs into validated execution plans
    responsibility_boundary: Normalize structured requirements, validate task DAGs and process bindings, topologically order work, and optionally write local graph or batch plans.
  natural_owner_evidence_paths:
    - src/tool_system/planner/__init__.py
    - src/tool_system/planner/requirement_graph.py
    - src/tool_system/planner/task_graph.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
      - process_authority
    direct_consumer_module_ids:
      - cli_frontend
      - role_runtime
      - task_runner
  input_contract:
    registered_inputs:
      - requirement_and_task_graph_v1
    boundary: Accept structured requirement or task-graph mappings, the active blueprint, and explicit process-authority bindings.
  output_contract:
    registered_outputs:
      - validated_task_graph_and_batch_plan_v1
    boundary: Return deterministic validation, execution order, graph, or batch plan records and optionally write the selected local YAML plan.
  error_contract:
    registered_error_semantics:
      - invalid_dependency_or_authority_binding_blocks
    boundary: Missing work, invalid roles, unknown dependencies, cycles, absent control roles, blueprint drift, inactive pairs, or process-binding failures block.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - generated_artifact_write
      - repository_write
    direct_effects:
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/planner/requirement_graph.py
          - src/tool_system/planner/task_graph.py
        boundary: Write one caller-selected YAML task graph or batch plan only when the explicit write helper is invoked.
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/planner/requirement_graph.py
          - src/tool_system/planner/task_graph.py
        boundary: If the selected output is inside an authorized repository, the generated plan write is also a repository write.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve requirement normalization, graph validation, topological order, control roles, process binding, result shapes, and optional write semantics.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of runner, role-runtime, and CLI consumers.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_planner@1.1.0
    method: Revert through a separately audited pull request; creator-owned generated plans may be removed only under their applicable cleanup authorization.
  replacement_contract:
    activation_rule: Replace only after requirement, DAG, cycle, control-role, process-authority, output ordering, optional-write, and direct-consumer tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-and-conditional-write
      contract: Read blueprint and process inputs; write only the caller-selected generated plan path when the explicit helper is invoked.
    data:
      mode: structured-planning-input
      contract: Requirement, task, dependency, role, and process-binding mappings remain caller-owned planning data.
    artifact:
      mode: optional-yaml-plan
      contract: Generated graph and batch YAML files are local creator-owned artifacts, not process or governance authority by existence.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-input-and-generated-plan-roots
        access: read-write
        evidence_paths:
          - src/tool_system/planner/requirement_graph.py
          - src/tool_system/planner/task_graph.py
        evidence_symbols:
          - write_requirement_task_graph_file
          - write_task_graph_batch_file
        boundary_parameters:
          - requirement_path
          - graph_path
          - blueprint_path
          - output_path
        constraint: Read the selected planning inputs and write only the explicit output path after successful validation.
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
