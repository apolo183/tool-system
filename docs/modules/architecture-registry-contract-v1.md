# Architecture Registry Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`architecture_registry` module. It is not registry membership or execution
authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/architecture-registry-contract-v1.md
  identity:
    canonical_module_id: architecture-registry
    current_module_id: architecture_registry
    module_version: 1.1.0
    aggregate_interface:
      interface_id: architecture-registry-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:architecture_registry@1.1.0
    python_import_identities:
      - kind: exact
        name: tool_system
      - kind: prefix
        name: tool_system.architecture
      - kind: exact
        name: tool_system.cli.validate_module_registry
      - kind: exact
        name: tool_system.cli.validate_repo_manifest
  role:
    summary: validate the durable module inventory, natural owners, versions, and declared dependency DAG
    responsibility_boundary: Parse and validate the one current module registry and repository manifest without changing either authority source.
  natural_owner_evidence_paths:
    - REPO_MANIFEST.md
    - config/module_registry_schema_v1.json
    - config/module_registry_v1.yaml
    - src/tool_system/__init__.py
    - src/tool_system/architecture/__init__.py
    - src/tool_system/architecture/module_registry.py
    - src/tool_system/architecture/repo_manifest.py
    - src/tool_system/cli/validate_module_registry.py
    - src/tool_system/cli/validate_repo_manifest.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - module_registry_v1
      - repository_formal_file_set_manifest_v1
    boundary: Accept one caller-selected current registry or manifest path and a read-only repository root.
  output_contract:
    registered_outputs:
      - module_registry_validation_result_v1
      - repository_manifest_validation_result_v1
    boundary: Return deterministic structured status, mode, counts, compatibility metadata, and fail-closed reasons.
  error_contract:
    registered_error_semantics:
      - fail_closed_with_structured_reasons
    boundary: Missing, mixed, malformed, ambiguous, overlapping, unowned, or graph-inconsistent input returns BLOCK or a bounded validation error.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve result fields, parser modes, current authority paths, natural-owner coverage, and declared DAG semantics.
    interface_incompatible_change: Requires a new aggregate interface version and an explicitly reviewed migration.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:architecture_registry@1.1.0
    method: Revert through a separately audited pull request while preserving registry, manifest, Git, and audit history.
  replacement_contract:
    activation_rule: A replacement becomes current only after interface, owner coverage, dependency graph, manifest coverage, and affected consumers pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: read-only
      contract: Inspect current tracked paths and authority documents without staging, writing, converting, or caching them.
    data:
      mode: read-only
      contract: Registry, schema, S0 mapping, source ownership, and manifest table data remain caller-owned inputs.
    artifact:
      mode: result-only
      contract: Validation results exist in memory or stdout only unless an external caller separately persists them.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-repository-root
        access: read-only
        evidence_paths:
          - src/tool_system/architecture/module_registry.py
          - src/tool_system/architecture/repo_manifest.py
        evidence_symbols:
          - validate_module_registry
          - validate_repo_manifest
        boundary_parameters:
          - registry_path
          - manifest_path
          - repo_root
        constraint: Resolve and inspect only the caller-selected repository root; never create a projection, registry, manifest, cache, or Git write.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-git-index
        mode: read-only tracked-path enumeration
        evidence_paths:
          - src/tool_system/architecture/repo_manifest.py
        boundary: Invoke local Git only to enumerate tracked paths with a minimal deterministic environment and no index mutation.
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
