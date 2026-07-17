# Role Runtime Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`role_runtime` module. Current role steps, worker results, transition decisions,
and rollback steps remain no-mutation records.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/role-runtime-contract-v1.md
  identity:
    canonical_module_id: role-runtime
    current_module_id: role_runtime
    module_version: 1.1.0
    aggregate_interface:
      interface_id: role-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:role_runtime@1.1.0
    python_import_identities:
      - kind: prefix
        name: tool_system.runtime
  role:
    summary: build bounded multi-role runtime plans and audit bundles
    responsibility_boundary: Validate an explicitly bound task graph, build deterministic no-mutation role steps and worker records, assemble audit and rollback bundles, and gate the next review transition.
  natural_owner_evidence_paths:
    - src/tool_system/runtime/__init__.py
    - src/tool_system/runtime/audit_bundle.py
    - src/tool_system/runtime/role_runtime.py
    - src/tool_system/runtime/transition_gate.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - agent_worker_runtime
      - manifest_validation
      - repository_controller
      - task_planner
    direct_consumer_module_ids:
      - cli_frontend
  input_contract:
    registered_inputs:
      - role_graph_worker_and_transition_inputs
    boundary: Accept a validated task graph, blueprint, process-authority path, no-mutation worker results, source references, rollback reference, and transition name.
  output_contract:
    registered_outputs:
      - role_runtime_plan_transition_decision_and_audit_bundle
    boundary: Return role steps, worker results, runtime plan, audit bundle, rollback bundle, transition decision, and structured reasons with mutation flags false.
  error_contract:
    registered_error_semantics:
      - invalid_role_graph_or_transition_blocks
    boundary: Invalid authority binding, graph, worker parity, worker result, mutation flag, audit bundle, rollback bundle, or transition input blocks.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - repository_write
      - data_write
      - generated_artifact_write
    direct_effects: []
    delegated_effects:
      - capability_id: repository-controller-jsonl-persistence
        capability_state: conditional-delegated-maximum
        effect_classes:
          - repository_write
          - data_write
          - generated_artifact_write
        evidence_paths:
          - src/tool_system/runtime/audit_bundle.py
          - src/tool_system/runtime/role_runtime.py
          - src/tool_system/runtime/transition_gate.py
        activation_condition: A caller invokes a role-runtime file API with an audit_path after the corresponding record passes validation.
        boundary: The file APIs delegate append-only JSONL persistence to repository-controller; data_write and generated_artifact_write apply, while repository_write applies only when the selected path is inside an authorized repository. The delegation grants no target mutation or execution authority.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve role taxonomy mapping, step ordering, no-mutation flags, worker parity, audit and rollback bundle fields, and transition gate behavior.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of all provider boundaries and the CLI consumer.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:role_runtime@1.1.0
    method: Revert through a separately audited pull request and retain runtime plans, audit bundles, rollback bundles, and transition evidence.
  replacement_contract:
    activation_rule: Replace only after graph binding, role-step, worker-result, audit, rollback, transition, no-mutation, and CLI tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-and-conditional-audit-write
      contract: Read graph, blueprint, process authority, and source references; write only the caller-selected local audit record.
    data:
      mode: runtime-records-and-optional-jsonl
      contract: Role steps, worker results, audit bundles, rollback bundles, and transition decisions are structured records that may persist as append-only JSONL through repository-controller when an audit path is supplied.
    artifact:
      mode: optional-jsonl
      contract: Role plan, audit bundle, and transition artifacts are creator-owned local evidence with no target mutation.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-graph-blueprint-authority-and-audit-roots
        access: read-write
        evidence_paths:
          - src/tool_system/runtime/audit_bundle.py
          - src/tool_system/runtime/role_runtime.py
          - src/tool_system/runtime/transition_gate.py
        evidence_symbols:
          - build_role_runtime_plan_file
          - build_runtime_audit_bundle_file
          - build_role_transition_gate_file
        boundary_parameters:
          - graph_path
          - blueprint_path
          - process_authority_path
          - audit_path
        constraint: Read the explicit graph and authority inputs and append only to the selected audit path after a passing record is built.
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
