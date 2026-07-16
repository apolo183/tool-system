# Task Runner Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`task_runner` module. Configured commands and audit paths remain bounded by the
explicit current task pair and caller authorization.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/task-runner-contract-v1.md
  identity:
    canonical_module_id: task-runner
    current_module_id: task_runner
    module_version: 1.1.0
    aggregate_interface:
      interface_id: task-runner-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_runner@1.1.0
    python_import_identities:
      - kind: exact
        name: tool_system.runner.stage_runner
      - kind: exact
        name: tool_system.runner.task_graph_runner
      - kind: exact
        name: tool_system.runner.task_runner
  role:
    summary: execute validated task, batch, graph, and stage plans through bounded gates
    responsibility_boundary: Resolve one explicit current task pair, run validation and policy gates, optionally execute its configured local commands, aggregate batches or graphs, and record local audit results.
  natural_owner_evidence_paths:
    - src/tool_system/runner/stage_runner.py
    - src/tool_system/runner/task_graph_runner.py
    - src/tool_system/runner/task_runner.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
      - process_authority
      - repository_controller
      - task_planner
    direct_consumer_module_ids:
      - cli_frontend
  input_contract:
    registered_inputs:
      - validated_task_manifest_change_plan_and_task_graph
    boundary: Accept one explicit validated manifest/change-plan pair or a validated batch, graph, or requirement route with caller-selected policies, working directory, and audit path.
  output_contract:
    registered_outputs:
      - pipeline_result_gate_decision_and_audit_record
    boundary: Return pair resolution, validation, gate, command, batch, graph, stage, status, reason, and optional audit-path evidence.
  error_contract:
    registered_error_semantics:
      - first_failed_gate_or_command_stops_pipeline
    boundary: Missing current pair, invalid replay request, failed authority, manifest, plan, policy, gate, command, graph, or batch input stops downstream execution.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - generated_artifact_write
      - repository_write
    direct_effects:
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/runner/stage_runner.py
          - src/tool_system/runner/task_graph_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: Append structured task, batch, graph, or stage results to the caller-selected local JSONL audit path.
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/runner/stage_runner.py
          - src/tool_system/runner/task_graph_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: If the selected audit path is inside an authorized repository, the append-only audit write is also a repository write.
    delegated_effects:
      - Effects of configured commands remain those of the exact authorized command and cannot be expanded by the runner, a batch, a graph, or a CLI.
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve explicit-pair resolution, gate order, stop behavior, command-result fields, batch and graph aggregation, no-target flags, and audit result shapes.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of the CLI plus every upstream validation and planning boundary.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_runner@1.1.0
    method: Revert through a separately audited pull request and preserve prior task, batch, graph, stage, command, and audit evidence.
  replacement_contract:
    activation_rule: Replace only after explicit-pair, replay-block, policy, command, batch, graph, stage, audit, no-target-mutation, and CLI tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: validated-local-execution
      contract: Read current task inputs and policies; command and audit writes remain limited to the explicit authorization and selected local paths.
    data:
      mode: pipeline-records
      contract: Manifest, plan, policy, graph, batch, command, and result mappings are bounded pipeline data.
    artifact:
      mode: append-only-jsonl
      contract: Optional task, batch, graph, and stage audit records append to a caller-selected creator-owned path.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-task-working-and-audit-roots
        access: read-write
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        evidence_symbols:
          - run_task_pipeline
        boundary_parameters:
          - task_manifest_path
          - change_plan_path
          - cwd
          - audit_path
        constraint: Resolve the exact current pair, use only the selected working directory, and append only to the selected audit path.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-command-subprocess
        mode: exact configured command after passing gates
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        boundary: Invoke command execution only after explicit-pair, process-authority, manifest, plan, policy, and gate preconditions pass.
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
