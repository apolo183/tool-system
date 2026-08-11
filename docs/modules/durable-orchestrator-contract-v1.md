# Durable Orchestrator Module Compound Contract v1

This file defines the module contract owned by the current
`durable_orchestrator` module. Its persistent boundary is a caller-selected
single-host SQLite database outside protected roots.
Version 1.1 also owns a generic burn-on-claim authorization-consumption ledger;
version 1.2 treats only SQLite-owned optional sidecars that disappear during
validation as absent; version 1.3 adds retry-wide pre-dispatch worker-call
consumption and controlled active-lease renewal.
It does not claim multi-host global exactly-once delivery.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/durable-orchestrator-contract-v1.md
  identity:
    canonical_module_id: durable-orchestrator
    current_module_id: durable_orchestrator
    module_version: 1.2.0
    aggregate_interface:
      interface_id: durable-orchestrator-api
      interface_version: 1.1.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@783a1bf16c48e717da281d9fefc134e68bf879c4:durable_orchestrator@1.1.0
    python_import_identities:
      - kind: prefix
        name: tool_system.orchestrator
  role:
    summary: persist and reconcile single-host task state, retry-wide worker-call consumption, side-effect evidence, and one-time authorization consumption
    responsibility_boundary: Own one hardened local SQLite state store for task, renewable lease, checkpoint, pre-dispatch worker-call consumption, side-effect, outbox, recovery, integrity, immutable ledger identity, burn-on-claim authorization records, and race-safe validation of SQLite-owned optional sidecars.
  natural_owner_evidence_paths:
    - src/tool_system/orchestrator/__init__.py
    - src/tool_system/orchestrator/durable.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids:
      - process_authority
      - local_git
  input_contract:
    registered_inputs:
      - durable_task_and_side_effect_intent_v1
      - durable_authorization_consumption_v1
      - durable_retry_wide_worker_call_consumption_v1
    boundary: Accept bounded identifiers, content hashes, checkpoints, active-lease claim or renewal requests, a frozen total worker-call budget and request digest, local-fixture side-effect intent, idempotent outbox callbacks, or one exact external authorization identity, digest, binding, host, ledger identity, and expiry.
  output_contract:
    registered_outputs:
      - durable_task_state_and_reconciliation_result_v1
      - durable_authorization_consumption_result_v1
      - durable_worker_call_consumption_result_v1
    boundary: Return durable run, task, renewable lease, ordinal worker-call, effect, outbox, recovery, integrity, reconciliation, immutable ledger-identity, and authorization-consumption records from the current SQLite state.
  error_contract:
    registered_error_semantics:
      - lease_retry_recovery_and_terminal_error_states
      - authorization_replay_is_terminal
      - worker_call_budget_exhaustion_is_terminal
    boundary: Invalid paths, unsafe permissions, identity substitution, observed sidecar symlinks, nonregular or multi-link sidecars, stale lease, precondition drift, retry exhaustion, exhausted worker-call budget, changed completed-call metadata, ambiguous replay, duplicate authorization consumption, wrong ledger identity, expiry, corruption, or integrity failure blocks. A committed STARTED worker call remains consumed after crash or task retry. An optional SQLite sidecar that disappears during validation is valid absence rather than a state conflict.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
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
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Persist bounded task, renewable lease, checkpoint, ordinal pre-dispatch worker-call consumption, side-effect, outbox, reconciliation, receipt, ledger identity, and authorization-consumption state in the selected local database.
      - effect_class: database_write
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Create, migrate schema v1 through v3 non-destructively to schema v4, transact with BEGIN IMMEDIATE, checkpoint, and integrity-check one local SQLite database and its SQLite sidecars while tolerating only a sidecar that atomically disappears during observation.
    delegated_effects:
      - capability_id: caller-supplied-outbox-delivery-sink
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
          - src/tool_system/orchestrator/durable.py
        activation_condition: A caller explicitly supplies an idempotent deliver callback and invokes outbox reconciliation for a claimed event.
        boundary: The callback owns its provider-specific effects and authorization; this conservative maximum classification does not grant the sink any write or production authority.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve schema migration, state machine, controlled lease renewal, attempts, retry-wide ordinal worker-call consumption before dispatch, total call budget, immutable completed-call metadata, idempotency, preconditions, transactions, outbox, recovery, integrity, immutable ledger identity, burn-on-claim uniqueness, record shapes, database-file single-link identity, and fail-closed validation of every observed unsafe sidecar.
    interface_incompatible_change: Requires a new aggregate interface version, explicit database migration contract, and recovery evidence.
  rollback_contract:
    rollback_identity: tool-system@783a1bf16c48e717da281d9fefc134e68bf879c4:durable_orchestrator@1.1.0
    method: Revert through a separately audited pull request while retaining the prior database and applying no destructive data rollback without separate authorization.
  replacement_contract:
    activation_rule: Replace only after schema v1/v2/v3-to-v4 migration, fake-clock renewal and expiry, pre-dispatch worker-call consumption, crash/reopen retry-wide budget, deterministic optional-sidecar disappearance, repeated cross-process authorization races, unsafe sidecar, crash-burn replay, side-effect, outbox, recovery, corruption, and integrity tests pass against temporary fixture stores.
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
      contract: Durable orchestration, worker-call consumption, and authorization-consumption records are bounded canonical JSON and text stored under the versioned local schema; a committed worker-call STARTED record or authorization claim is never erased after caller failure.
    artifact:
      mode: none
      contract: The module owns durable database state, not a separate report, projection, cache, or authority artifact.
    database:
      mode: sqlite-read-write
      contract: One regular non-symlink SQLite file with controlled parent permissions, identity checks, WAL, foreign keys, synchronous writes, BEGIN IMMEDIATE transactions, schema v4 with non-destructive prior-version migration, and an immutable random ledger instance identity. Optional WAL, SHM, and journal files may disappear during validation; every sidecar that remains observed must be regular, non-symlink, and single-link.
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
        constraint: Use a secure existing parent outside forbidden roots; reject symlinks, hard links, substitutions, unsafe permissions, and unsupported suffixes. Treat only FileNotFoundError or regular zero-link metadata observed for an optional SQLite sidecar as concurrent disappearance.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-sqlite-engine
        mode: single-host transactional persistence
        evidence_paths:
          - src/tool_system/orchestrator/durable.py
        boundary: Use the Python SQLite driver only for the selected local database; no remote database or network sink is owned.
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
