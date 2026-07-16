# Durable Orchestrator Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`durable_orchestrator` module. Its persistent boundary is a caller-selected
single-host SQLite database outside protected roots.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/durable-orchestrator-contract-v1.md
  identity:
    canonical_module_id: durable-orchestrator
    current_module_id: durable_orchestrator
    module_version: 1.0.0
    aggregate_interface:
      interface_id: durable-orchestrator-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:durable_orchestrator@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.orchestrator
  role:
    summary: persist and reconcile single-host task state, leases, attempts, and side-effect evidence
    responsibility_boundary: Own one hardened local SQLite state store for task, lease, checkpoint, side-effect, outbox, recovery, and integrity records.
  natural_owner_evidence_paths:
    - src/tool_system/orchestrator/__init__.py
    - src/tool_system/orchestrator/durable.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - durable_task_and_side_effect_intent_v1
    boundary: Accept bounded identifiers, content hashes, checkpoints, lease requests, local-fixture side-effect intent, and idempotent outbox callbacks.
  output_contract:
    registered_outputs:
      - durable_task_state_and_reconciliation_result_v1
    boundary: Return durable run, task, effect, outbox, recovery, integrity, and reconciliation records from the current SQLite state.
  error_contract:
    registered_error_semantics:
      - lease_retry_recovery_and_terminal_error_states
    boundary: Invalid paths, unsafe permissions, identity substitution, stale lease, precondition drift, retry exhaustion, ambiguous replay, corruption, or integrity failure blocks.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - data_write
      - database_write
    direct_effects:
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Persist bounded task, lease, checkpoint, side-effect, outbox, reconciliation, and receipt state in the selected local database.
      - effect_class: database_write
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Create, migrate, transact, checkpoint, and integrity-check one local SQLite database and its SQLite sidecars.
    delegated_effects:
      - Outbox callbacks remain caller-supplied idempotent sinks and receive no external-write authority from the store.
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve schema migration, state machine, leases, attempts, idempotency, preconditions, transactions, outbox, recovery, integrity, and record shapes.
    interface_incompatible_change: Requires a new aggregate interface version, explicit database migration contract, and recovery evidence.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:durable_orchestrator@1.0.0
    method: Revert through a separately audited pull request while retaining the prior database and applying no destructive data rollback without separate authorization.
  replacement_contract:
    activation_rule: Replace only after schema, migration, concurrency, lease, side-effect, outbox, recovery, corruption, and integrity tests pass against a copied fixture store.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: forbidden-root
      contract: The database path must remain outside the tool-system repository and every caller-supplied forbidden root.
    data:
      mode: persistent-single-host
      contract: Durable orchestration records are bounded canonical JSON and text stored under the versioned local schema.
    artifact:
      mode: none
      contract: The module owns durable database state, not a separate report, projection, cache, or authority artifact.
    database:
      mode: sqlite-read-write
      contract: One regular non-symlink SQLite file with controlled parent permissions, identity checks, WAL, foreign keys, synchronous writes, and transactions.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: secure-database-parent-root
        access: read-write
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        evidence_symbols:
          - DurableOrchestratorStore
        boundary_parameters:
          - database_path
          - forbidden_roots
        constraint: Use a secure existing parent outside forbidden roots; reject symlinks, hard links, substitutions, unsafe permissions, and unsupported suffixes.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-sqlite-engine
        mode: single-host transactional persistence
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Use the Python SQLite driver only for the selected local database; no remote database or network sink is owned.
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
