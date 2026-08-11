# Development Loop Module Compound Contract v1

This file defines the module contract owned by the current `development_loop`
module. The module executes only against caller-owned bounded in-memory files
and injected callbacks. Returned cycle state is persistable evidence,
not execution authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/development-loop-contract-v1.md
  identity:
    canonical_module_id: development-loop
    current_module_id: development_loop
    module_version: 1.1.0
    aggregate_interface:
      interface_id: development-loop-api
      interface_version: 1.1.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@0b5110a2eea79ebde650e1088b787c781ddab171:development_loop@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.development_loop
  role:
    summary: execute bounded structured patch, validation, diagnosis, repair, and independent review cycles against isolated in-memory repositories while reconciling a caller-supplied durable worker-call floor and preserving terminal, cancellation, no-progress, and zero-external-effect semantics
    responsibility_boundary: Freeze acceptance and finite budgets, reconcile the caller's durable total worker-call floor, count a dispatch before invoking its callback, expose the current authorized candidate-file mapping to each worker cycle, preserve a trusted bridge terminal envelope, enforce atomic exact-scope patch preconditions, honor caller cancellation before dispatch and patch application, terminate repeated or non-progressing cycles, seal successful candidates, and apply evidence non-reopening semantics without performing external operations.
  natural_owner_evidence_paths:
    - src/tool_system/development_loop/__init__.py
    - src/tool_system/development_loop/loop.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids:
      - local_git
      - task_runner
  input_contract:
    registered_inputs:
      - frozen_development_contract_virtual_repository_and_fixture_callbacks_v1
    boundary: Accept a frozen task digest, baseline tree, exact scope, acceptance and validation sets, fixed terminal predicate, finite budgets, caller-owned in-memory files, injected worker, validator and two independent reviewer callbacks, optional caller-persisted resume state, a non-negative durable initial worker-call count, and an optional caller-owned boolean cancellation callback; every worker request includes a fresh copy of the current candidate files plus its candidate-tree digest.
  output_contract:
    registered_outputs:
      - bounded_development_cycle_state_v1
    boundary: Return canonical candidate files and tree digest after every worker has received the matching current candidate mapping, the maximum of resumed and durable call counts, per-cycle fingerprints, blockers, satisfied acceptance, validation and review evidence, finite usage, the exact safe bridge terminal or other stop classification, sealed-candidate status, and zero-operation counters. A dispatched callback is counted before invocation; cancellation before dispatch performs no call and cancellation after return discards that unapplied patch.
  error_contract:
    registered_error_semantics:
      - invalid_drifted_out_of_scope_stale_unbounded_repeated_or_non_progressing_input_blocks
    boundary: Invalid frozen identity, path, scope, patch, content precondition, bridge terminal shape, callback output including a raising or non-boolean cancellation signal, validation set, acceptance set, review obligation, durable call floor, resume identity, finite or exhausted worker-call budget, repeated fingerprint, or two-cycle no-progress state fails closed without reducing the consumed call count.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve exact frozen-contract semantics, durable worker-call floor reconciliation, pre-callback call counting, safe terminal-envelope propagation, current-candidate worker request context, atomic patch preconditions, caller cancellation checkpoints, validation and review set closure, recurrence fingerprint fields and exclusions, finite budgets, evidence non-reopening, canonical output, and zero external side effects.
    interface_incompatible_change: Requires a new aggregate interface version and explicit revalidation of local-Git, task-runner, blueprint-compiler, and future durable-orchestrator consumers.
  rollback_contract:
    rollback_identity: tool-system@0b5110a2eea79ebde650e1088b787c781ddab171:development_loop@absent
    method: Revert through a separately audited pull request while preserving P14E, repository history, and P14F acceptance evidence.
  replacement_contract:
    activation_rule: Replace only after structured patch, exact-scope, precondition, durable call-floor exhaustion, safe terminal propagation with nonzero count, validation, diagnosis, bounded repair, independent review, cancellation before dispatch and before patch application, invalid cancellation, recurrence, finite-budget, resume, evidence non-reopening, and no-side-effect tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: caller-owned-in-memory-fixture-only
      contract: Repository paths and UTF-8 text are mappings copied into each worker request; this module performs no filesystem or Git operation.
    data:
      mode: in-memory-and-caller-persistable-state
      contract: Cycle state is canonical JSON-compatible data; durable storage and leases belong to P14G.
    artifact:
      mode: result-only
      contract: Evidence is returned to the caller and never persisted by this module.
    database:
      mode: none
      contract: This module owns no database, ledger, schema, migration, or write.
  external_root_contracts:
    declaration: explicit-none
    roots: []
  external_system_contracts:
    declaration: explicit-none
    systems: []
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
