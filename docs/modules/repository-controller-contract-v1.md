# Repository Controller Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`repository_controller` module. It records the module's guarded GitHub action
surface but grants no repository action by itself.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/repository-controller-contract-v1.md
  identity:
    canonical_module_id: repository-controller
    current_module_id: repository_controller
    module_version: 1.0.0
    aggregate_interface:
      interface_id: repository-controller-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:repository_controller@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.repo_controller
  role:
    summary: evaluate and execute explicitly authorized repository control actions with audit records
    responsibility_boundary: Evaluate current PR, policy, check, manifest, plan, approval, and head-SHA evidence before an optional action-scoped GitHub merge and append-only audit record.
  natural_owner_evidence_paths:
    - src/tool_system/repo_controller/__init__.py
    - src/tool_system/repo_controller/actions.py
    - src/tool_system/repo_controller/artifact.py
    - src/tool_system/repo_controller/audit_log.py
    - src/tool_system/repo_controller/controller.py
    - src/tool_system/repo_controller/controller_run.py
    - src/tool_system/repo_controller/github_state.py
    - src/tool_system/repo_controller/live_github_collector.py
    - src/tool_system/repo_controller/main_ci.py
    - src/tool_system/repo_controller/self_check.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
    direct_consumer_module_ids:
      - cleanup_planner
      - cli_frontend
      - role_runtime
      - target_repo_adapter
      - task_runner
      - worker_adapter
  input_contract:
    registered_inputs:
      - repository_state_policy_and_action_intent
    boundary: Accept one named repository and PR, current GitHub state, passing checks, exact task scope, action approval, expected head SHA, and caller-selected audit path.
  output_contract:
    registered_outputs:
      - action_plan_decision_and_append_only_audit_record
    boundary: Return a deterministic repository decision, action plan or action result, and append-only JSONL audit evidence.
  error_contract:
    registered_error_semantics:
      - deny_or_block_on_missing_authority_and_stale_state
    boundary: Draft, closed, unmergeable, stale, mismatched, failed-check, out-of-scope, unauthorized, runner, or audit validation failures block.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - external_system_write
      - generated_artifact_write
      - git_write
      - network_write
      - repository_write
    direct_effects:
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
        boundary: Submit only the approved pull-request merge action to the named GitHub repository after all guards pass.
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        boundary: Append one structured controller or observation record to the caller-selected JSONL audit path.
      - effect_class: git_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
        boundary: The guarded GitHub pull-request merge changes Git history only for the exact approved repository, PR, merge method, and head SHA.
      - effect_class: network_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
        boundary: Network mutation occurs only through the guarded gh pull-request merge command when dry-run is false.
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        boundary: If the caller selects an audit path inside an authorized repository, the append-only audit write is also a repository write.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve decision fields, fail-closed guards, dry-run behavior, exact head matching, action command shape, audit fields, and injected runner boundaries.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of every direct consumer plus repository lifecycle controls.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:repository_controller@1.0.0
    method: Revert code through a separately audited pull request; any prior repository merge requires its own audited revert workflow.
  replacement_contract:
    activation_rule: Replace only after policy, state normalization, check evaluation, dry-run, injected action, live collector, audit, and all direct-consumer tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: action-scoped
      contract: Repository mutation requires exact named action authorization, current state, expected head SHA, allowed merge method, and non-draft mergeable PR.
    data:
      mode: state-and-policy-input
      contract: Pull-request, workflow, manifest, plan, policy, rollback, and approval mappings remain caller-supplied evidence.
    artifact:
      mode: append-only-jsonl
      contract: Controller, self-check, and main-CI records append to a caller-selected path and retain structured reasons.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-audit-artifact-root
        access: read-write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        evidence_symbols:
          - write_jsonl_record
        boundary_parameters:
          - path
          - record
        constraint: Append only the supplied structured record to the caller-selected path; do not infer repository or cleanup authority from that location.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: github-through-gh-subprocess
        mode: read state or action-scoped pull-request merge
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
          - src/tool_system/repo_controller/live_github_collector.py
        boundary: Read PR and workflow state or execute the one guarded merge command; no branch creation, file update, label, deployment, or unrelated action is implicit.
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
