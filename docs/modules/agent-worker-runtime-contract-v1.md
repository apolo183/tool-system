# Agent Worker Runtime Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`agent_worker_runtime` module. Its process boundary remains fixture-only and
does not authorize provider or target-repository execution.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/agent-worker-runtime-contract-v1.md
  identity:
    canonical_module_id: agent-worker-runtime
    current_module_id: agent_worker_runtime
    module_version: 1.0.0
    aggregate_interface:
      interface_id: agent-worker-runtime-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:agent_worker_runtime@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.agent_worker
  role:
    summary: execute bounded fixture-only process workers behind the worker request interface
    responsibility_boundary: Validate and run one approved Python fixture in an isolated ephemeral workspace with bounded resources and fail-closed guards.
  natural_owner_evidence_paths:
    - src/tool_system/agent_worker/__init__.py
    - src/tool_system/agent_worker/interface.py
    - src/tool_system/agent_worker/process_runtime.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids:
      - role_runtime
      - worker_adapter
  input_contract:
    registered_inputs:
      - WorkerRequest_v1
    boundary: Accept no-mutation role requests or fixture-only process requests with explicit fixture, workspace, forbidden-root, interpreter, and resource limits.
  output_contract:
    registered_outputs:
      - WorkerResult_v1
    boundary: Return bounded status, redacted reasons, captured output, resource evidence, and workspace cleanup evidence.
  error_contract:
    registered_error_semantics:
      - bounded_worker_error_codes
    boundary: Invalid paths, symlinks, hard links, network, mutation flags, guard denials, timeouts, cancellation, resource limits, or cleanup failure block.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - data_write
      - generated_artifact_write
      - database_write
    direct_effects:
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/agent_worker/process_runtime.py
        boundary: Create guard and worker files only inside the creator-owned temporary workspace and remove that workspace before returning.
    delegated_effects:
      - capability_id: fixture-sqlite-inside-ephemeral-workspace
        capability_state: conditional-delegated-maximum
        effect_classes:
          - data_write
          - database_write
        evidence_paths:
          - src/tool_system/agent_worker/process_runtime.py
        activation_condition: An approved fixture explicitly opens a SQLite database inside its isolated ephemeral workspace while the audit guard is active.
        boundary: The fixture may persist SQLite data only inside the temporary workspace; database_write is also data_write, and the workspace is removed before return.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve request and result fields, guard behavior, resource limits, output caps, path isolation, and cleanup evidence.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of role-runtime and worker-adapter consumers.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:agent_worker_runtime@1.0.0
    method: Revert through a separately audited pull request and rerun fixture, adversarial, resource, timeout, cancellation, and cleanup tests.
  replacement_contract:
    activation_rule: Replace only after the fixture process boundary, preflight, guard, resource limits, result contract, and direct consumers pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: forbidden-write-root
      contract: The tool-system repository and every supplied forbidden root remain outside the workspace write boundary.
    data:
      mode: scrubbed-fixture-input
      contract: Fixture source is content-checked; environment secrets and host data outside approved readable library roots do not cross the guard.
    artifact:
      mode: ephemeral-workspace
      contract: Guard, worker copy, bounded stdout, bounded stderr, and result evidence are creator-owned and workspace files are deleted.
    database:
      mode: denied-outside-workspace
      contract: Database access outside the ephemeral workspace is denied by path and audit-event controls.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: fixture-and-ephemeral-workspace-roots
        access: read-write
        evidence_paths:
          - src/tool_system/agent_worker/process_runtime.py
        evidence_symbols:
          - ProcessWorkerRequest
          - preflight_process_worker
          - run_process_worker
        boundary_parameters:
          - entrypoint
          - allowed_fixture_root
          - workspace_root
          - forbidden_roots
        constraint: Read one approved non-symlink fixture and write only inside a disjoint temporary workspace outside every forbidden root.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-python-subprocess
        mode: isolated fixture execution
        evidence_paths:
          - src/tool_system/agent_worker/process_runtime.py
        boundary: Use the approved interpreter with isolated flags, scrubbed environment, disabled network, audit guard, process-group termination, and bounded resources.
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
