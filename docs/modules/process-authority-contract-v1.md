# Process Authority Module Compound Contract v1

This file defines the module contract owned by the current
`process_authority` module. The explicit task pair remains current authority;
legacy inputs remain non-executing replay only. The P14C live-provider issuer
can authenticate one exact, short-lived GitHub owner comment, but this source
change creates no approval record and performs no provider call.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/process-authority-contract-v1.md
  identity:
    canonical_module_id: process-authority
    current_module_id: process_authority
    module_version: 2.1.0
    aggregate_interface:
      interface_id: process-authority-api
      interface_version: 2.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@b6ea3c62aa668031e87abb6341f82cb1bd32a3eb:process_authority@2.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.process_authority
      - kind: exact
        name: tool_system.runner.active_gate_resolver
      - kind: exact
        name: tool_system.cli.validate_active_gates
      - kind: exact
        name: tool_system.cli.validate_process_authority
  role:
    summary: require one explicit current task pair, validate non-authoritative replay, and authenticate one exact P14C GitHub owner approval record
    responsibility_boundary: Validate the current process-authority contract, one exact manifest/change-plan pair, the pinned non-executing legacy replay snapshot, and one unedited short-lived GitHub issue comment whose owner identity and complete P14C action binding match exactly.
  natural_owner_evidence_paths:
    - config/process_authority_schema_v1.json
    - config/process_authority_v1.yaml
    - config/replay_snapshot_v1.yaml
    - docs/process_authority_contract_v1.md
    - src/tool_system/cli/validate_active_gates.py
    - src/tool_system/cli/validate_process_authority.py
    - src/tool_system/process_authority/__init__.py
    - src/tool_system/process_authority/contract.py
    - src/tool_system/process_authority/live_provider_approval.py
    - src/tool_system/runner/active_gate_resolver.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
    direct_consumer_module_ids:
      - ai_worker_runtime
      - task_planner
      - task_runner
  input_contract:
    registered_inputs:
      - explicit_manifest_change_plan_pair
      - explicit_non_authoritative_legacy_replay_request
      - pinned_p14c_github_issue_comment_id_and_exact_action_binding
    boundary: Accept one explicit current pair, one explicit request to validate canonical content-addressed replay inputs, or one positive GitHub issue-comment ID plus the exact typed P14C action binding. The GitHub path is fixed internally and accepts no caller-provided reader, actor mapping, or affirmative flag.
  output_contract:
    registered_outputs:
      - validated_explicit_pair_or_content_addressed_replay_result
      - opaque_single_use_p14c_live_execution_grant
    boundary: Return exact binding mode, replay status, hashes, counts, no-mutation flags, structured fail-closed reasons, or one opaque in-memory grant bound to the authenticated P14C approval digest, issue, comment, packet, request, limits, and denied authorities.
  error_contract:
    registered_error_semantics:
      - missing_mismatched_implicit_or_drifted_input_blocks
      - unauthenticated_stale_edited_mismatched_or_replayed_p14c_approval_blocks
    boundary: Missing pair members, mismatched references, symlinks, escaped paths, duplicate pairs, changed hashes, implicit index use, replay execution requests, GitHub read failures, non-owner or edited comments, malformed or expired approval bodies, binding drift, or in-process replay block.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve explicit-pair default, exact binding, canonical replay hashes, replay-only non-authority, result fields, and caller defaults.
    interface_incompatible_change: Requires a new aggregate interface version and explicit migration of every current caller.
  rollback_contract:
    rollback_identity: tool-system@b6ea3c62aa668031e87abb6341f82cb1bd32a3eb:process_authority@2.0.0
    method: Revert through a separately audited pull request while retaining legacy inputs and replay evidence until separate cleanup authorization.
  replacement_contract:
    activation_rule: Replace only after schema, current-pair, replay snapshot, active-gate adapter, planner, runner, no-command-on-failure, GitHub approval authentication, exact binding, expiry, replay, and no-real-I/O tests pass.
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
      contract: Read process authority, explicit pair files, replay snapshot, legacy index, and hashed source files without modifying them.
    data:
      mode: content-addressed-input
      contract: Current pair identity and legacy replay hashes are validation inputs; replay data never becomes execution authority.
    artifact:
      mode: result-only
      contract: Validation returns structured in-memory results and does not create a process packet, projection, or cache.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-process-document-roots
        access: read-only
        evidence_paths:
          - src/tool_system/process_authority/contract.py
        evidence_symbols:
          - validate_explicit_task_pair
          - validate_process_authority
        boundary_parameters:
          - task_manifest_path
          - change_plan_path
          - authority_path
          - repo_root
        constraint: Resolve explicit inputs under their selected repository context, reject symlinks and escapes, and never use a repository index implicitly.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: github-public-issue-comment-api
        mode: optional-explicitly-invoked-read-only-approval-authentication
        evidence_paths:
          - src/tool_system/process_authority/live_provider_approval.py
        boundary: Perform one TLS-verified unauthenticated GET to api.github.com/repos/apolo183/tool-system/issues/comments/{comment_id}; require exact repository, owner login apolo183, OWNER association, an unedited comment, strict JSON, at most fifteen minutes of validity, complete P14C action binding, and fail closed on every read or validation error.
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
