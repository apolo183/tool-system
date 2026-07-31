# Repository Controller Module Compound Contract v1

This file defines the module contract owned by the current
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
    module_version: 1.2.0
    aggregate_interface:
      interface_id: repository-controller-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@6cb43f8723619bddfdd4c5b52a7d68db1ea3f30f:repository_controller@1.1.0
    python_import_identities:
      - kind: prefix
        name: tool_system.repo_controller
  role:
    summary: evaluate and execute explicitly authorized repository control actions with audit records
    responsibility_boundary: Evaluate current PR, policy-declared exact check name and source application, check-run head SHA, manifest, plan, separately supplied lifecycle approval, and current PR head evidence; derive an approval digest; and require one exact single-use mutation capability before an optional action-scoped GitHub merge and append-only audit record.
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
    basis: tool-system-static-python-import-dag
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
    boundary: Accept one named repository and PR, current GitHub state, a non-empty policy-declared set of required check name and source-application bindings, complete check-run records bound to the current PR head, exact task scope, a lifecycle approval supplied separately from the task manifest and bound to repository, PR, action, base, head, identity, source, and reason, an exact mutation capability for non-dry-run execution, and a caller-selected audit path.
  output_contract:
    registered_outputs:
      - action_plan_decision_and_append_only_audit_record
    boundary: Return a deterministic repository decision carrying the canonical lifecycle-approval SHA-256, an action plan or action result carrying that same digest, and append-only JSONL audit evidence.
  error_contract:
    registered_error_semantics:
      - deny_or_block_on_missing_authority_and_stale_state
    boundary: Draft, closed, unmergeable, stale, mismatched, unconfigured, incomplete, duplicate, wrong-source, wrong-head, pending, failed-check, out-of-scope, task-manifest-only approval, missing or replayed capability, unauthorized runner, or audit validation failures block before mutation. GitHub-compatible success, neutral, and skipped conclusions are passing only after exact check provenance and completeness validation.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes:
      - repository_write
      - data_write
      - generated_artifact_write
      - git_write
      - network_write
      - external_system_write
    direct_effects:
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        boundary: If the caller selects an audit path inside an authorized repository, the append-only audit write is also a repository write.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        boundary: Persist one structured controller or observation record as append-only JSONL data at the caller-selected audit path.
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/repo_controller/artifact.py
        boundary: Append one structured controller or observation record to the caller-selected JSONL audit path.
      - effect_class: git_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
        boundary: The guarded GitHub pull-request merge changes Git history only after consuming one capability bound to the exact repository, PR, squash action, base, head SHA, approval-record digest, and runner kind.
      - effect_class: network_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
          - src/tool_system/repo_controller/live_github_collector.py
        boundary: GitHub PR and workflow reads use the network, and network mutation occurs only through the guarded gh pull-request merge command when dry-run is false and an exact single-use capability is consumed.
      - effect_class: external_system_write
        evidence_paths:
          - src/tool_system/repo_controller/actions.py
        boundary: Submit only the approved pull-request merge action to the named GitHub repository after all state, approval-digest, and capability guards pass; this classification and a PASS decision do not issue the capability or authorize merge.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve decision and result shapes, GitHub-compatible passing conclusions, fail-closed guards, separate lifecycle-approval input, approval digest, dry-run behavior, exact action binding, single-use capability consumption, action command shape, audit fields, and injected runner boundaries; require exact policy-declared check provenance for a PASS decision.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of every direct consumer plus repository lifecycle controls.
  rollback_contract:
    rollback_identity: tool-system@6cb43f8723619bddfdd4c5b52a7d68db1ea3f30f:repository_controller@1.1.0
    method: Revert code through a separately audited pull request; any prior repository merge requires its own audited revert workflow.
  replacement_contract:
    activation_rule: Replace only after exact required-check policy, check-run provenance normalization, completeness and head binding, dry-run, injected action, live collector, audit, and all direct-consumer tests pass.
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
      contract: Repository mutation requires a separately supplied exact named-action record, its canonical digest, current state, a complete non-duplicate set containing every policy-declared check name and source application at the current PR head, allowed passing conclusions, an allowed merge method, a non-draft mergeable PR, and one matching single-use capability. An unconfigured repository fails closed. The current source provides no live capability issuer.
    data:
      mode: state-policy-and-append-only-audit
      contract: Pull-request, check-run, workflow-observation, manifest, plan, policy, rollback, and separately supplied lifecycle-approval mappings are caller-supplied evidence; the approval digest and controller records may persist as append-only JSONL data at the selected audit path.
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
        boundary: Read PR state, provenance-bearing GitHub check runs, and post-merge workflow observations, or execute the one guarded merge command after exact capability consumption; current production entrypoints have no capability issuer, and no branch creation, file update, label, Ready transition, deployment, or unrelated action is implicit.
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
