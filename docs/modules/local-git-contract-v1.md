# Local Git Orchestrator Module Compound Contract v1

This contract owns P14G durable orchestration of one isolated, remote-free local
Git fixture. It consumes the accepted development loop and durable SQLite store;
it does not publish a branch, open a pull request, or mutate a downstream repo.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/local-git-contract-v1.md
  identity:
    canonical_module_id: local-git
    current_module_id: local_git
    module_version: 1.1.0
    aggregate_interface:
      interface_id: local-git-api
      interface_version: 1.1.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@22dedb0f2a2c0b38a0bd4c67f36c1c2454ca19d5:local_git@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.local_git
  role:
    summary: durably record one bounded change in an isolated local Git fixture
    responsibility_boundary: Freeze Git identity, scope, and exact baseline presence/content topology, consume a sealed development-loop result containing a subset of the allowed scope, bind it to durable leases/checkpoints/side-effect receipts, stage the exact add/modify/delete delta, create one local branch and commit, resume completed effects without duplication, and return non-executing rollback, cleanup, and draft-PR plans.
  natural_owner_evidence_paths:
    - src/tool_system/local_git/__init__.py
    - src/tool_system/local_git/orchestrator.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - development_loop
      - durable_orchestrator
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - frozen_development_contract_and_callbacks_v1
      - isolated_local_git_identity_v1
      - durable_orchestrator_store_v1
    boundary: Accept an absolute remote-free clean fixture root, exact base commit/tree, one agent branch, an allowed scope whose baseline mapping exactly represents the paths present at base, frozen P14F callbacks and budgets, and one caller-selected hardened durable store. Allowed paths absent from the baseline may be added; present paths may be modified or deleted.
  output_contract:
    registered_outputs:
      - durable_local_git_change_receipt_v1
      - unauthorized_local_disposition_plans_v1
    boundary: Return the sealed candidate identity, one local branch/commit/tree, durable completion, zero remote/provider/credential counts, and rollback, creator-cleanup, and draft-PR plans whose execution remains false.
  error_contract:
    registered_error_semantics:
      - precondition_scope_lease_and_receipt_conflicts_fail_closed
      - ambiguous_side_effect_never_replays
    boundary: Remote configuration, dirty state, symlink or root drift, head/tree mismatch, baseline presence/content mismatch, unreceipted branch, ambiguous in-progress effect, lease conflict, candidate scope expansion, empty candidate delta, staged-delta mismatch, or Git failure blocks without remote fallback.
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
      - effect_class: repository_write
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        boundary: Add, modify, or delete only the exact changed subset of frozen paths inside the caller-owned isolated local fixture.
      - effect_class: data_write
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        boundary: Persist task checkpoints and side-effect receipts through durable-orchestrator-api and write exact fixture content.
      - effect_class: git_write
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        boundary: Create one local agent branch and one commit in a repository with no configured remotes.
    delegated_effects:
      - capability_id: durable-orchestrator-store
        capability_state: conditional-delegated-maximum
        effect_classes: [database_write]
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        activation_condition: A caller supplies a DurableOrchestratorStore and invokes the local workflow.
        boundary: The provider module owns the SQLite write; this consumer supplies bounded lease, checkpoint, and receipt records only.
        classification_grants_authority: false
      - capability_id: injected-development-loop-callbacks
        capability_state: conditional-delegated-maximum
        effect_classes: [repository_write, data_write, generated_artifact_write, git_write, database_write, network_write, external_system_write, production_operation]
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        activation_condition: A caller supplies worker, validator, or reviewer callbacks to development-loop-api.
        boundary: Callback effects and authority remain caller-owned; P14G acceptance uses deterministic in-process fixture callbacks only.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve remote-free preflight, exact base/scope and baseline-topology binding, exact add/modify/delete staging, durable effect ordering, no-duplicate completed-effect resume, and non-executing disposition plans.
    interface_incompatible_change: Remote support, automatic rollback/cleanup, a new persistence schema, or weaker receipt reconciliation requires a new interface version and separate authorization.
  rollback_contract:
    rollback_identity: tool-system@22dedb0f2a2c0b38a0bd4c67f36c1c2454ca19d5:local_git@absent
    method: Revert the module through a separately audited pull request; runtime rollback plans remain non-executing.
  replacement_contract:
    activation_rule: Replace only after isolated add/modify/delete branch/commit, baseline presence/content drift, scope, durable receipts, crash-after-completion resume, conflict, and zero-remote tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: isolated-local-git-read-write
      contract: The root is absolute, clean, non-symlink, has no configured remote, and matches exact base commit/tree before the first effect.
    data:
      mode: durable-single-host
      contract: State is recorded through the hardened caller-selected SQLite store outside the fixture root.
    artifact:
      mode: local-git-commit
      contract: One local branch and commit are the only executable artifacts; remote, rollback, cleanup, and draft-PR outputs are plans only.
    database:
      mode: delegated-durable-orchestrator
      contract: This module owns no schema and accesses SQLite only through durable-orchestrator-api.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: isolated-local-git-fixture
        access: read-write
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        evidence_symbols: [run_durable_local_git]
        boundary_parameters: [repository_root]
        constraint: Exact absolute remote-free fixture root; no target or tool-system repository is authorized.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-git-process
        mode: isolated-local-only
        evidence_paths: [src/tool_system/local_git/orchestrator.py]
        boundary: Invoke local git only after remote-free and identity preflight; network and GitHub operations are absent.
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
