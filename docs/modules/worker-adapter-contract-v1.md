# Worker Adapter Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`worker_adapter` module. The current adapter is a no-mutation dry-run adapter
and does not call an external worker.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/worker-adapter-contract-v1.md
  identity:
    canonical_module_id: worker-adapter
    current_module_id: worker_adapter
    module_version: 1.0.0
    aggregate_interface:
      interface_id: worker-adapter-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:worker_adapter@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.worker_adapter
  role:
    summary: adapt no-mutation worker requests into policy-gated orchestration records
    responsibility_boundary: Convert worker requests into adapter requests, run the deterministic no-mutation adapter, assemble orchestration and rollback records, and enforce all false mutation flags.
  natural_owner_evidence_paths:
    - src/tool_system/worker_adapter/__init__.py
    - src/tool_system/worker_adapter/contract.py
    - src/tool_system/worker_adapter/orchestration.py
    - src/tool_system/worker_adapter/policy_gate.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - agent_worker_runtime
      - repository_controller
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - AdapterRequest_v1_and_WorkerRequest_v1
    boundary: Accept worker or adapter requests whose execute, external-worker, target-write, target-mutation, and production flags are all false.
  output_contract:
    registered_outputs:
      - adapter_orchestration_and_policy_gate_record_v1
    boundary: Return deterministic adapter results, orchestration audit and rollback records, policy-gate decisions, and structured reasons with all mutation flags false.
  error_contract:
    registered_error_semantics:
      - policy_denial_or_worker_contract_error
    boundary: Any requested execution, external worker, target write, target mutation, production operation, missing record, parity failure, or nested true flag blocks.
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
    direct_effects:
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/worker_adapter/orchestration.py
          - src/tool_system/worker_adapter/policy_gate.py
        boundary: If the selected audit path is inside an authorized repository, the append-only adapter record is also a repository write.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/worker_adapter/orchestration.py
          - src/tool_system/worker_adapter/policy_gate.py
        boundary: Persist one adapter orchestration or policy-gate record as append-only JSONL data at the caller-selected audit path.
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/worker_adapter/orchestration.py
          - src/tool_system/worker_adapter/policy_gate.py
        boundary: Append one adapter orchestration or policy-gate record to the caller-selected JSONL audit path.
    delegated_effects:
      - capability_id: injected-worker-adapter
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
          - src/tool_system/worker_adapter/contract.py
        activation_condition: A caller explicitly injects a non-default WorkerAdapter into run_adapter_requests under its own provider-specific effect contract and applicable authorization.
        boundary: The default remains DryRunWorkerAdapter. The current runtime does not dynamically validate provider effect-contract completeness; this conservative maximum does not claim direct external, Git, database, network, or production effects and grants no authority.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request and result fields, default dry-run adapter, no-mutation flags, orchestration parity, rollback bundle, policy gate, and audit shapes.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of agent-worker and repository-controller provider boundaries.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:worker_adapter@1.0.0
    method: Revert through a separately audited pull request and retain adapter request, result, orchestration, policy, audit, and rollback evidence.
  replacement_contract:
    activation_rule: Replace only after adapter contract, worker conversion, no-mutation, orchestration, nested-policy, audit-write, and rollback tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: conditional-audit-write
      contract: No code or target mutation is performed; only the selected local audit path may receive an append-only record.
    data:
      mode: adapter-records-and-optional-jsonl
      contract: Worker requests, adapter requests, results, orchestration, rollback, and policy mappings are structured local records; optional audit records persist as append-only JSONL at the selected path.
    artifact:
      mode: optional-jsonl
      contract: Adapter orchestration and policy-gate audit records are creator-owned local evidence.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-adapter-audit-root
        access: write-only
        evidence_paths:
          - src/tool_system/worker_adapter/orchestration.py
          - src/tool_system/worker_adapter/policy_gate.py
        evidence_symbols:
          - write_adapter_orchestration_record
          - write_adapter_policy_gate_record
        boundary_parameters:
          - adapter_requests
          - audit_path
        constraint: Build a passing or blocked no-mutation record and append it only to the selected audit path.
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
