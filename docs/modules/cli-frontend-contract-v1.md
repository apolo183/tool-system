# CLI Frontend Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`cli_frontend` module. CLI selection and argument parsing do not expand the
authority of any delegated module.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/cli-frontend-contract-v1.md
  identity:
    canonical_module_id: cli-frontend
    current_module_id: cli_frontend
    module_version: 1.1.0
    aggregate_interface:
      interface_id: cli-frontend-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cli_frontend@1.1.0
    python_import_identities:
      - kind: exact
        name: tool_system.cli
      - kind: exact
        name: tool_system.cli.cleanup_plan
      - kind: exact
        name: tool_system.cli.controller_run
      - kind: exact
        name: tool_system.cli.controller_self_check
      - kind: exact
        name: tool_system.cli.evaluate_github_state
      - kind: exact
        name: tool_system.cli.evaluate_repo_write
      - kind: exact
        name: tool_system.cli.execute_change_plan
      - kind: exact
        name: tool_system.cli.main
      - kind: exact
        name: tool_system.cli.observe_main_ci
      - kind: exact
        name: tool_system.cli.plan_requirement
      - kind: exact
        name: tool_system.cli.plan_task_graph
      - kind: exact
        name: tool_system.cli.run_batch
      - kind: exact
        name: tool_system.cli.run_role_graph
      - kind: exact
        name: tool_system.cli.run_stage
      - kind: exact
        name: tool_system.cli.run_task
      - kind: exact
        name: tool_system.cli.run_task_graph
      - kind: exact
        name: tool_system.cli.target_repo_dry_run
      - kind: exact
        name: tool_system.cli.target_repo_pr_plan_preview
  role:
    summary: expose stable command-line entry points that delegate to registered public module interfaces
    responsibility_boundary: Parse command-line arguments, select one current public module entry point, render its result, and derive a process exit code without changing delegated authority.
  natural_owner_evidence_paths:
    - src/tool_system/cli/__init__.py
    - src/tool_system/cli/cleanup_plan.py
    - src/tool_system/cli/controller_run.py
    - src/tool_system/cli/controller_self_check.py
    - src/tool_system/cli/evaluate_github_state.py
    - src/tool_system/cli/evaluate_repo_write.py
    - src/tool_system/cli/execute_change_plan.py
    - src/tool_system/cli/main.py
    - src/tool_system/cli/observe_main_ci.py
    - src/tool_system/cli/plan_requirement.py
    - src/tool_system/cli/plan_task_graph.py
    - src/tool_system/cli/run_batch.py
    - src/tool_system/cli/run_role_graph.py
    - src/tool_system/cli/run_stage.py
    - src/tool_system/cli/run_task.py
    - src/tool_system/cli/run_task_graph.py
    - src/tool_system/cli/target_repo_dry_run.py
    - src/tool_system/cli/target_repo_pr_plan_preview.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - cleanup_planner
      - manifest_validation
      - repository_controller
      - role_runtime
      - target_repo_adapter
      - task_planner
      - task_runner
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - command_line_arguments_and_versioned_module_inputs
    boundary: Accept command-line arguments for one selected current entry point, including explicit paths, repository identifiers, PR numbers, flags, and module inputs.
  output_contract:
    registered_outputs:
      - exit_code_and_structured_or_human_readable_result
    boundary: Print the delegated structured result and return zero only for the selected entry point's accepted success status.
  error_contract:
    registered_error_semantics:
      - nonzero_exit_on_block_or_failure
    boundary: Argument errors, delegated BLOCK or failure status, or delegated exceptions do not become success and cannot be hidden by CLI routing.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - repository_write
      - data_write
      - generated_artifact_write
      - git_write
      - database_write
      - network_write
      - external_system_write
      - production_operation
    direct_effects: []
    delegated_effects:
      - capability_id: selected-module-interface
        capability_state: conditional-delegated-maximum
        effect_classes:
          - repository_write
          - data_write
          - generated_artifact_write
          - git_write
          - database_write
          - network_write
          - external_system_write
          - production_operation
        evidence_paths:
          - src/tool_system/cli/controller_run.py
          - src/tool_system/cli/execute_change_plan.py
          - src/tool_system/cli/main.py
          - src/tool_system/cli/plan_requirement.py
          - src/tool_system/cli/plan_task_graph.py
          - src/tool_system/cli/target_repo_dry_run.py
        activation_condition: A caller selects one concrete CLI entry point and that delegated interface independently satisfies its plan, policy, state, and authorization gates.
        boundary: This is the conservative maximum classification of callable interfaces, not a claim that argument parsing directly performs every effect or that the CLI currently performs a production operation.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve command names, required and optional argument semantics, module delegation, structured output, and exit-code behavior.
    interface_incompatible_change: Requires a new aggregate interface version, entry-point migration, packaging review, and all delegated CLI tests.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cli_frontend@1.1.0
    method: Revert through a separately audited pull request and restore the prior entry-point delegation and argument contract.
  replacement_contract:
    activation_rule: Replace only after root and dedicated CLI tests, packaging entry-point checks, delegated-module tests, output rendering, and exit-code tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: delegated
      contract: CLI path arguments are passed to the selected module; the CLI creates no independent repository authority or write boundary.
    data:
      mode: arguments-and-results
      contract: Parsed arguments and delegated result mappings are transient CLI data.
    artifact:
      mode: delegated
      contract: Stdout and stderr are direct process streams; persistent artifacts remain owned by the selected module and caller path.
    database:
      mode: delegated
      contract: The CLI owns no database connection or schema; any database boundary remains with the selected module.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-selected-cli-paths
        access: read-write
        evidence_paths:
          - src/tool_system/cli/main.py
        evidence_symbols:
          - build_parser
          - main
        boundary_parameters:
          - task_manifest
          - change_plan
          - cwd
          - audit_path
        constraint: Parse explicit path arguments and delegate them unchanged to the selected module; do not infer broader roots or permissions.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: delegated-module-entrypoints
        mode: one selected module call
        evidence_paths:
          - src/tool_system/cli/main.py
        boundary: Select one current module interface and preserve its authorization, side-effect, error, and stop boundaries.
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
