# Repository Context Module Compound Contract v1

This file defines the module contract owned by the current
`repository_context` module. A natural-owner result is an evidence-backed
proposal only; it does not assign authority or authorize repository mutation.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/repository-context-contract-v1.md
  identity:
    canonical_module_id: repository-context
    current_module_id: repository_context
    module_version: 1.0.0
    aggregate_interface:
      interface_id: repository-context-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@7e3a114a25d70c3ebecc952f13ce68b1adbbbc80:repository_context@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.repository_context
  role:
    summary: build deterministic bounded repository context and natural-owner evidence from one clean committed local Git snapshot
    responsibility_boundary: Index tracked blobs, map static dependencies and tests, select relevant context, and propose a natural owner without writing the repository, contacting a remote, or granting authority.
  natural_owner_evidence_paths:
    - src/tool_system/repository_context/__init__.py
    - src/tool_system/repository_context/builder.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids: []
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - clean_committed_repository_snapshot_blueprint_governance_query_seeds_and_finite_limits
    boundary: Accept one caller-selected exact local Git repository root, expected HEAD, tracked blueprint and governance paths, query terms, optional seed paths, and finite context ceilings.
  output_contract:
    registered_outputs:
      - content_addressed_repository_index_dependency_test_map_selected_context_owner_proposal_and_freshness_evidence
    boundary: Return deterministic JSON-compatible evidence with bounded selected UTF-8 content, source and test relationships, a non-authorizing natural-owner proposal, and zero-operation counters.
  error_contract:
    registered_error_semantics:
      - stale_dirty_ambiguous_unsafe_unreadable_unbounded_or_insufficient_evidence_blocks
    boundary: Invalid roots or paths, head drift, dirty state, unsupported entries, symlinks, binary or non-UTF-8 required inputs, exceeded limits, parse failure, or missing owner evidence fails closed before a result is returned.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve exact-snapshot validation, deterministic content hashes, finite limits, tracked-blob reads, dependency and test maps, evidence sufficiency, freshness checks, non-authorizing owner proposals, and zero write, network, provider, and credential effects.
    interface_incompatible_change: Requires a new aggregate interface version and explicit revalidation of every registered consumer and isolated fixture.
  rollback_contract:
    rollback_identity: tool-system@7e3a114a25d70c3ebecc952f13ce68b1adbbbc80:repository_context@absent
    method: Revert through a separately audited pull request while preserving repository history and P14D acceptance evidence.
  replacement_contract:
    activation_rule: Replace only after deterministic Python and TypeScript fixture selection, owner evidence, stale-snapshot, path-safety, size, and no-side-effect tests pass.
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
      contract: Read committed tracked blobs and Git snapshot metadata only; reject a dirty worktree and perform no checkout, index refresh, cache, branch, commit, or remote operation.
    data:
      mode: in-memory-only
      contract: Repository index, selected context, relationship maps, owner proposal, and freshness evidence remain caller-owned in-memory values.
    artifact:
      mode: result-only
      contract: The module returns a structured value and never selects or writes a report, cache, receipt, database, or context file.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, replay ledger, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-selected-isolated-git-repository
        access: read-only
        evidence_paths:
          - src/tool_system/repository_context/builder.py
        evidence_symbols:
          - build_repository_context
          - validate_repository_context_freshness
        boundary_parameters:
          - repository_root
          - expected_head
        constraint: Resolve exactly one caller-selected repository top level and read only tracked blobs from the expected clean commit under finite file and byte ceilings.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-git-object-database
        mode: hardened read-only snapshot and blob inspection
        evidence_paths:
          - src/tool_system/repository_context/builder.py
        boundary: Invoke local Git with optional locks, lazy fetch, replacement objects, prompts, hooks, and global or system configuration disabled; never invoke a remote or a mutating Git verb.
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
