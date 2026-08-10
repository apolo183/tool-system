# Blueprint Compiler Module Compound Contract v1

This file defines the module contract owned by the current
`blueprint_compiler` module. Compiled documents and plans have
`authority_effect: none`; they do not authorize execution or repository writes.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/blueprint-compiler-contract-v1.md
  identity:
    canonical_module_id: blueprint-compiler
    current_module_id: blueprint_compiler
    module_version: 1.0.0
    aggregate_interface:
      interface_id: blueprint-compiler-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@00793ad07bba2e3fe3bd29882e83788d32697da6:blueprint_compiler@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.blueprint_compiler
  role:
    summary: compile approved blueprint milestones and accepted repository evidence into deterministic bounded development plans
    responsibility_boundary: Validate explicit module-change bindings and derive module and task DAGs, documents, manifests, plans, gates, tests, isolation, replacement, and rollback nodes without persisting or executing them.
  natural_owner_evidence_paths:
    - src/tool_system/blueprint_compiler/__init__.py
    - src/tool_system/blueprint_compiler/compiler.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids:
      - task_runner
  input_contract:
    registered_inputs:
      - approved_blueprint_repository_context_module_registry_authorization_and_acceptance_v1
    boundary: Accept caller-owned mappings for one approved product objective, selected milestones with exact module-change bindings, accepted repository context, current module inventory, an isolated-fixture authorization envelope, finite limits, and acceptance requirements.
  output_contract:
    registered_outputs:
      - bounded_blueprint_development_compilation_v1
    boundary: Return deterministic milestone-module bindings, module and executable task DAGs, non-authorizing document descriptors, isolation paths, replacement and rollback nodes, compatibility validation, hashes, and zero-operation counters.
  error_contract:
    registered_error_semantics:
      - ambiguous_stale_unauthorized_unbounded_overlapping_or_cyclic_input_blocks
    boundary: Missing approval, rejected context, authority-bearing owner proposals, malformed identifiers or paths, invalid module preconditions, unknown dependencies, overlap, cycles, invalid task graphs, and exceeded finite limits fail closed.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve exact module-change binding, finite limits, deterministic ordering and hashes, task-planner graph and task-runner consumer compatibility, non-authorizing outputs, fail-closed errors, and zero side effects.
    interface_incompatible_change: Requires a new aggregate interface version and explicit revalidation of repository-context and future development-loop consumers.
  rollback_contract:
    rollback_identity: tool-system@00793ad07bba2e3fe3bd29882e83788d32697da6:blueprint_compiler@absent
    method: Revert through a separately audited pull request while preserving P14D, repository history, and P14E acceptance evidence.
  replacement_contract:
    activation_rule: Replace only after deterministic compilation, module binding, graph compatibility, limit, authorization, overlap, cycle, path, and no-side-effect tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: none
      contract: Repository bytes are supplied as accepted structured context; this module performs no Git or filesystem operation.
    data:
      mode: in-memory-only
      contract: Blueprint, registry, authorization, context, and compilation results remain caller-owned in-memory values.
    artifact:
      mode: result-only
      contract: Generated document and plan descriptors are returned only and never persisted by this module.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, ledger, or write.
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
