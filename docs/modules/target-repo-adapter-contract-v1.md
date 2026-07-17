# Target Repository Adapter Module Compound Contract v1

This file materializes the S3 contract evidence owned by the current
`target_repo_adapter` module. Current target-repository outputs are dry-run,
precheck, state, intent, packet, and audit records; they do not execute target
mutation.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/target-repo-adapter-contract-v1.md
  identity:
    canonical_module_id: target-repo-adapter
    current_module_id: target_repo_adapter
    module_version: 1.0.0
    aggregate_interface:
      interface_id: target-repo-adapter-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_adoption_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:target_repo_adapter@1.0.0
    python_import_identities:
      - kind: prefix
        name: tool_system.target_repo
  role:
    summary: construct target-repository dry-run, precheck, snapshot, intent, and separately gated mutation packets
    responsibility_boundary: Validate target evidence and approvals, normalize caller-supplied target state, and construct no-execution previews, intent, command, final-plan, audit, and rollback records.
  natural_owner_evidence_paths:
    - src/tool_system/target_repo/__init__.py
    - src/tool_system/target_repo/dry_run_adapter.py
    - src/tool_system/target_repo/execution_approval.py
    - src/tool_system/target_repo/execution_state_snapshot.py
    - src/tool_system/target_repo/mutation_command_packet.py
    - src/tool_system/target_repo/p4c_preview_module.py
    - src/tool_system/target_repo/p4d_precheck.py
    - src/tool_system/target_repo/p5h_record.py
    - src/tool_system/target_repo/p5i_bundle.py
    - src/tool_system/target_repo/pr_plan_preview.py
    - src/tool_system/target_repo/state_collector.py
    - src/tool_system/target_repo/write_intent_record.py
    - src/tool_system/target_repo/write_packet.py
  dependency_contract:
    basis: s0-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - manifest_validation
      - repository_controller
    direct_consumer_module_ids:
      - cli_frontend
  input_contract:
    registered_inputs:
      - target_state_manifest_change_plan_and_action_authority
    boundary: Accept target manifest, policy, optional change plan, named approval mappings, and caller-supplied observed state without contacting or mutating the target.
  output_contract:
    registered_outputs:
      - dry_run_precheck_snapshot_intent_and_mutation_packet_records
    boundary: Return dry-run plans, PR previews, prechecks, write intent, gated packets, state snapshots, final plans, audit bundles, and structured reasons with execute false.
  error_contract:
    registered_error_semantics:
      - missing_authority_or_stale_target_state_blocks
    boundary: Missing target evidence, policy mismatch, forbidden path, absent approval, existing branch or PR, incomplete file state, stale SHA, or missing observation blocks.
  side_effect_contract:
    taxonomy_source: finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:config/module_registry_schema_v1.json
    effect_classes:
      - repository_write
      - data_write
      - generated_artifact_write
    direct_effects:
      - effect_class: repository_write
        evidence_paths:
          - src/tool_system/target_repo/dry_run_adapter.py
          - src/tool_system/target_repo/execution_approval.py
          - src/tool_system/target_repo/execution_state_snapshot.py
          - src/tool_system/target_repo/mutation_command_packet.py
          - src/tool_system/target_repo/p4c_preview_module.py
          - src/tool_system/target_repo/p4d_precheck.py
          - src/tool_system/target_repo/p5h_record.py
          - src/tool_system/target_repo/p5i_bundle.py
          - src/tool_system/target_repo/pr_plan_preview.py
          - src/tool_system/target_repo/state_collector.py
          - src/tool_system/target_repo/write_intent_record.py
          - src/tool_system/target_repo/write_packet.py
        boundary: If the selected audit path is inside an authorized repository, the append-only evidence write is also a repository write.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/target_repo/dry_run_adapter.py
          - src/tool_system/target_repo/execution_approval.py
          - src/tool_system/target_repo/execution_state_snapshot.py
          - src/tool_system/target_repo/mutation_command_packet.py
          - src/tool_system/target_repo/p4c_preview_module.py
          - src/tool_system/target_repo/p4d_precheck.py
          - src/tool_system/target_repo/p5h_record.py
          - src/tool_system/target_repo/p5i_bundle.py
          - src/tool_system/target_repo/pr_plan_preview.py
          - src/tool_system/target_repo/state_collector.py
          - src/tool_system/target_repo/write_intent_record.py
          - src/tool_system/target_repo/write_packet.py
        boundary: Persist one no-execution target plan, gate, state, intent, packet, final, or audit record as append-only JSONL data at the caller-selected path.
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/target_repo/dry_run_adapter.py
          - src/tool_system/target_repo/execution_approval.py
          - src/tool_system/target_repo/execution_state_snapshot.py
          - src/tool_system/target_repo/mutation_command_packet.py
          - src/tool_system/target_repo/p4c_preview_module.py
          - src/tool_system/target_repo/p4d_precheck.py
          - src/tool_system/target_repo/p5h_record.py
          - src/tool_system/target_repo/p5i_bundle.py
          - src/tool_system/target_repo/pr_plan_preview.py
          - src/tool_system/target_repo/state_collector.py
          - src/tool_system/target_repo/write_intent_record.py
          - src/tool_system/target_repo/write_packet.py
        boundary: Append one no-execution target plan, gate, state, intent, packet, final, or audit record to the caller-selected JSONL path.
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve target evidence checks, approval separation, no-execution flags, state normalization, SHA preconditions, packet shapes, final records, audit bundles, and CLI result fields.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of repository-controller, manifest-validation, and CLI boundaries.
  rollback_contract:
    rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:target_repo_adapter@1.0.0
    method: Revert through a separately audited pull request while retaining target evidence and performing no target cleanup or mutation.
  replacement_contract:
    activation_rule: Replace only after dry-run, preview, approval, state, intent, packet, final-plan, audit, no-mutation, and CLI tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: evidence-write-only
      contract: The module does not modify the target repository; only a caller-selected local JSONL evidence path may be written.
    data:
      mode: target-state-packet-and-jsonl-records
      contract: Target manifests, policies, approvals, observations, file states, PR states, SHAs, plans, and packets are structured evidence that may persist as append-only JSONL at the selected audit path.
    artifact:
      mode: append-only-jsonl
      contract: Target dry-run, preview, precheck, state, intent, packet, final, and audit records are creator-owned local artifacts.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-target-evidence-audit-root
        access: write-only
        evidence_paths:
          - src/tool_system/target_repo/dry_run_adapter.py
        evidence_symbols:
          - run_target_repo_dry_run
        boundary_parameters:
          - task_manifest
          - repo_policy
          - change_plan
          - audit_path
        constraint: Build the record from caller-supplied evidence and append only to the selected local audit path.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: target-repository-evidence-domain
        mode: caller-supplied state and action preview only
        evidence_paths:
          - src/tool_system/target_repo/mutation_command_packet.py
          - src/tool_system/target_repo/state_collector.py
        boundary: Model target branch, file, PR, SHA, and future action data without connector calls, Git writes, network writes, or target mutation.
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
