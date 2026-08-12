# Task Runner Module Compound Contract v1

This file defines the module contract owned by the current
`task_runner` module. Configured commands and audit paths remain bounded by the
explicit current task pair and caller authorization. The public-entry context
stage accepts only an exact manifest-bound repository read and delegates hardened
read-only snapshot inspection plus pure compilation. The subscription-development path accepts only the guarded Codex CLI subscription
adapter kind. A separately exact-bound public execution route composes isolated
candidate validation and remote-free local Git, while API, source/target mutation,
remote publication, production, cleanup, and rollback remain unauthorized.
That execution route also requires one canonical machine-verifiable evidence
obligation per frozen acceptance item and seals no candidate until independent
code and contract review revalidate the runner-issued receipts against the
actual diff, candidate tree, and frozen contract.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/task-runner-contract-v1.md
  identity:
    canonical_module_id: task-runner
    current_module_id: task_runner
    module_version: 2.0.0
    aggregate_interface:
      interface_id: task-runner-api
      interface_version: 2.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@f9dd68909ed0ffba9dc1a40197482d908c9cc2db:task_runner@1.2.0
    python_import_identities:
      - kind: exact
        name: tool_system.gate.command_runner
      - kind: exact
        name: tool_system.gate.test_gate
      - kind: exact
        name: tool_system.runner.stage_runner
      - kind: exact
        name: tool_system.runner.task_graph_runner
      - kind: exact
        name: tool_system.runner.task_runner
  role:
    summary: execute validated task plans and compose guarded subscription development with exact per-acceptance machine-verifiable evidence, a frozen-budget-derived durable lease, retry-wide call accounting, isolated validation, and one remote-free local Git commit
    responsibility_boundary: Resolve one explicit current task pair, run validation and policy gates, optionally execute exact configured commands, byte-seal one manifest-bound repository read, and on the separately exact execution-binding-v2 require one content-addressed behavior or contract evidence obligation per acceptance item before deriving a renewable durable stage lease from worker timeout, both termination waits, validation and local-Git subprocess envelopes; then compose the guarded worker, current-candidate loop, protected validation, independent actual-diff and contract receipt reviews, durable retry-wide call accounting, and one remote-free local commit while returning redacted terminal/count/lease evidence and non-executing disposition plans.
  natural_owner_evidence_paths:
    - src/tool_system/gate/command_runner.py
    - src/tool_system/gate/test_gate.py
    - src/tool_system/runner/stage_runner.py
    - src/tool_system/runner/task_graph_runner.py
    - src/tool_system/runner/task_runner.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - blueprint_compiler
      - development_loop
      - local_git
      - manifest_validation
      - process_authority
      - repository_context
      - repository_controller
      - task_planner
      - worker_adapter
    direct_consumer_module_ids:
      - cli_frontend
  input_contract:
    registered_inputs:
      - validated_task_manifest_change_plan_and_task_graph
      - frozen_development_contract_baseline_and_explicit_subscription_worker_adapter
      - explicit_subscription_public_entry_authority_and_bounded_selection
      - exact_manifest_bound_repository_context_and_compiler_limits
      - exact_subscription_execution_binding_worker_configuration_workspace_state_validation_and_local_git_identity
      - exact_per_acceptance_machine_verifiable_evidence_obligations
    boundary: Accept one explicit validated manifest/change-plan pair or a validated batch, graph, or requirement route with caller-selected policies, working directory, and audit path; for subscription context, require the manifest to bind the hashed repository identity, expected commit, blueprint, module registry, milestone, acceptance, governance, query, seed, repository-read authority, and false worker/local-Git write authority exactly to the requested finite selections; or accept a frozen development contract, in-memory baseline, guarded subscription-worker adapter request, validators, reviewers, finite limits, resume state, and cancellation callback. The public execution route additionally requires a second exact v2 manifest mapping that binds path identities, source commit/tree, existing/addable topology, current acceptance and captured plan commands, worker configuration including timeout and termination grace, total call budgets, validation limits, data transfer, isolated workspace, durable state, branch, commit message, one-commit ceiling, and hard-false API, credential, remote, target, production, cleanup, and rollback fields. Every acceptance item must have exactly one ordered obligation with its canonical item digest, supported behavior or contract evidence type, the validation command at the same frozen position and its digest, expected stdout and stderr digests, the complete expected baseline-to-candidate diff, and one present-content or absent-state assertion for every changed path. Missing, duplicate, swapped, extra, unsupported, self-inconsistent, or unmachine-verifiable evidence fails closed. The lease is a deterministic non-authorizing derivation from the other frozen values.
  output_contract:
    registered_outputs:
      - pipeline_result_gate_decision_and_audit_record
      - sealed_subscription_worker_candidate_and_effect_boundary_record
      - nonexecuting_subscription_public_entry_authority_packet
      - redacted_manifest_bound_context_and_blueprint_compilation_packet
      - redacted_subscription_local_commit_and_nonexecuting_draft_pr_plan
      - internal_content_addressed_acceptance_evidence_receipts
    boundary: Return pair resolution, validation, gate, command, batch, graph, stage, status, reason, and optional audit-path evidence; a passing public-entry preflight returns a canonical packet with hashed repository-root, task-pair input, and exact authority-binding evidence; the manifest-bound context stage returns redacted exact-snapshot evidence, deterministic compiled task DAG and hashes without repository-root or selected-content disclosure; the subscription development path returns the bounded in-memory result. For every satisfied acceptance item the public execution validator creates one canonical receipt binding the obligation digest, evidence type, frozen contract digest, actual candidate tree, complete actual diff, validation-command digest, exit code, captured output digests, and candidate-assertion digest. The code reviewer independently recomputes the actual diff, candidate tree, assertions, and receipt; the contract reviewer independently checks exact acceptance coverage, obligation identity, validation receipt, candidate tree, contract digest, and receipt digest. Only then may the route return its existing redacted hashes, retry-wide durable worker count, exact safe terminal status, derived lease seconds, finite worker usage, local branch/commit/tree identity, and non-executing disposition plans, with zero API, provider, credential, source/target mutation, remote-repository, production, cleanup, and rollback operations.
  error_contract:
    registered_error_semantics:
      - first_failed_gate_or_command_stops_pipeline
      - unsupported_adapter_or_blocked_development_loop_stops_before_downstream_effects
      - invalid_public_entry_input_or_failed_authority_blocks_packet_creation
      - missing_mismatched_ambiguous_or_drifting_snapshot_authority_binding_blocks_before_context
      - unclassified_stale_dirty_unsafe_malformed_or_rejected_context_blocks_compilation
      - missing_mismatched_or_drifting_execution_binding_workspace_state_scope_validation_or_git_identity_blocks_before_unreceipted_commit
      - missing_duplicate_extra_unsupported_stale_or_tampered_acceptance_evidence_blocks_before_local_commit
    boundary: Missing current pair, invalid replay request, invalid repository identity or bounded public-entry selection, absent, duplicate, mismatched, authority-bearing, or byte-drifting manifest binding, failed authority, stale or dirty snapshot, unsafe or missing evidence, invalid committed YAML mappings, rejected compilation, manifest, plan, policy, gate, command, graph, batch, unsupported subscription adapter, invalid structured worker result, exhausted durable total call budget, candidate validation command failure, empty or mismatched candidate diff, mismatched candidate assertion, wrong command output, wrong acceptance digest, stale candidate tree, wrong contract digest, tampered receipt, unsafe workspace or state path, lease/receipt ambiguity, or blocked development-loop input stops before any unreceipted commit or downstream execution. A command exit status alone never satisfies an acceptance item. Natural-language acceptance without a complete supported machine-verifiable obligation fails closed. A worker timeout remains SUBSCRIPTION_WORKER_TIMEOUT with its durable nonzero call count and cannot be collapsed to a generic state conflict.
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
        evidence_paths:
          - src/tool_system/runner/stage_runner.py
          - src/tool_system/runner/task_graph_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: If the selected audit path is inside an authorized repository, the append-only audit write is also a repository write.
      - effect_class: data_write
        evidence_paths:
          - src/tool_system/runner/stage_runner.py
          - src/tool_system/runner/task_graph_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: Persist structured task, batch, graph, or stage results as append-only JSONL data at the caller-selected local audit path.
      - effect_class: generated_artifact_write
        evidence_paths:
          - src/tool_system/runner/stage_runner.py
          - src/tool_system/runner/task_graph_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: Append structured task, batch, graph, or stage results to the caller-selected local JSONL audit path.
    delegated_effects:
      - capability_id: configured-command-execution
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
          - src/tool_system/gate/command_runner.py
          - src/tool_system/runner/task_runner.py
        activation_condition: An exact configured command is selected from the explicit current change plan and every process-authority, manifest, policy, gate, and caller authorization precondition passes.
        boundary: This is the conservative maximum classification of the exact configured command. It is not a claim that the runner directly performs a production operation and does not grant command execution or any listed effect authority.
        classification_grants_authority: false
      - capability_id: guarded-subscription-worker-development-pipeline
        capability_state: conditional-delegated-maximum
        effect_classes:
          - network_write
          - external_system_write
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        activation_condition: A caller explicitly injects the guarded Codex CLI subscription adapter with its own enabled configuration, subscription-worker authorization, isolated workspace, finite limits, and cancellation boundary.
        boundary: The task runner rejects every other adapter kind before invocation. This conservative classification grants no API, provider, provider-credential, target-repository, local-Git, remote-repository, production, cleanup, or rollback authority.
        classification_grants_authority: false
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve explicit-pair resolution, execution-binding-v2 exact per-item obligation closure, runner-issued receipt fields and digests, independent code and contract review, deterministic lease derivation from already frozen fields, retry-wide worker count and safe terminal preservation, input byte sealing, exact manifest-bound repository-read authorization, gate order, stop behavior, command-result fields, batch and graph aggregation, non-executing public-entry packet fields and digests, exact-snapshot context and freshness checks, deterministic compiler output, redaction, guarded subscription-adapter selection, structured in-memory candidate results, hard-zero downstream write and external effect fields, no-target flags, and audit result shapes.
    interface_incompatible_change: Accepting execution-binding v1, weakening per-item machine evidence or exact receipt review, adding source/remote/production effects, or changing the public result shape requires a new aggregate interface version and revalidation of the CLI plus every upstream validation and planning boundary.
  rollback_contract:
    rollback_identity: tool-system@f9dd68909ed0ffba9dc1a40197482d908c9cc2db:task_runner@1.2.0
    method: Revert through a separately audited pull request and preserve prior task, batch, graph, stage, command, and audit evidence.
  replacement_contract:
    activation_rule: Replace only after explicit-pair, replay-block, policy, command, batch, graph, stage, audit, public-entry input denial, execution-binding-v2 pass and v1 denial, missing/duplicate/extra obligation denial, wrong-code plus unrelated-PASS denial, swapped passing acceptance-command denial, wrong acceptance receipt, stale tree, empty diff and tampered receipt denial, correct remote-free Python and TypeScript fake-I/O success, byte-drift, stale-snapshot, context/compiler composition, redaction, derived-lease bounds, pre-process durable-call observation, fake timeout terminal/count preservation, retry-wide budget, guarded subscription-adapter, unsupported-adapter denial, no-target-mutation, and CLI tests pass.
    parallel_active_mainlines_allowed: false
  replacement_revalidation_boundary:
    module_implementation: true
    public_provider_boundaries: true
    public_consumer_boundaries: true
    affected_downstream_dependency_closure: true
    unrelated_modules_reimplementation_required: false
  local_boundaries:
    repository:
      mode: validated-local-execution
      contract: Read current task inputs and policies; command and audit writes remain limited to the explicit authorization and selected local paths.
    data:
      mode: pipeline-records-and-optional-jsonl
      contract: Manifest, plan, policy, graph, batch, command, and result mappings are bounded pipeline data; optional audit records persist as append-only JSONL at the selected path.
    artifact:
      mode: append-only-jsonl
      contract: Optional task, batch, graph, and stage audit records append to a caller-selected creator-owned path.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, or database write.
  external_root_contracts:
    declaration: declared
    roots:
      - root_id: caller-task-working-and-audit-roots
        access: read-write
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        evidence_symbols:
          - run_task_pipeline
        boundary_parameters:
          - task_manifest_path
          - change_plan_path
          - cwd
          - audit_path
        constraint: Resolve the exact current pair, use only the selected working directory, and append only to the selected audit path.
      - root_id: manifest-bound-caller-selected-repository
        access: read-only
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        evidence_symbols:
          - run_subscription_public_entry_context_compilation
          - run_subscription_public_entry_execution
        boundary_parameters:
          - repository_root
          - expected_head
          - blueprint_path
          - module_registry_path
        constraint: Both public routes inspect one exact clean committed source snapshot without changing it; all source identity and selected-content evidence is redacted.
      - root_id: manifest-bound-subscription-execution-workspace-and-state
        access: read-write
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        evidence_symbols:
          - run_subscription_public_entry_execution
        boundary_parameters:
          - workspace_root
          - durable_state_path
        constraint: Only the separately exact-bound execution route may create or resume the creator-owned remote-free workspace and hardened durable state outside the source; candidate validation uses private ephemeral clones and all private roots and contents remain redacted.
  external_system_contracts:
    declaration: declared
    systems:
      - system_id: local-command-subprocess
        mode: exact configured command after passing gates
        evidence_paths:
          - src/tool_system/gate/command_runner.py
          - src/tool_system/runner/task_runner.py
        boundary: Invoke the exact configured command only after explicit-pair, process-authority, manifest, plan, policy, gate, and caller authorization preconditions pass; classification itself grants no execution authority.
      - system_id: manifest-bound-local-git-object-database
        mode: delegated hardened read-only snapshot inspection
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        boundary: Delegate only to repository-context after the current exact task-pair passes, captured manifest and plan bytes remain unchanged, every bounded selection matches the manifest, and repository read is explicitly authorized; preserve fixed expected HEAD, clean-worktree, no-remote, no-hook, no-lock, no-write, freshness, and finite-limit boundaries.
      - system_id: local-git-and-durable-subscription-workflow
        mode: separately exact-bound isolated local execution
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        boundary: Compose local-git-api and durable-orchestrator-api only after the current task pair and execution-binding-v2 obligations match; derive and pass one renewable stage-covering lease from the frozen worker, validation, and local-Git limits, consume every worker call durably before process start, require all per-item candidate-bound receipts and both independent reviews before sealing, create at most one remote-free local commit, and return only non-executing remote, cleanup, and rollback plans.
      - system_id: codex-cli-subscription-worker
        mode: explicitly injected guarded adapter only
        evidence_paths:
          - src/tool_system/runner/task_runner.py
        boundary: Compose the in-memory development loop with only the guarded Codex CLI subscription adapter kind after adapter-owned enablement and authorization checks; its injected process starts only after P14G commits the call consumption, and timeout or other safe terminal evidence is retained with the durable count. Reject unknown or optional-API adapters before invocation and grant no downstream effect authority.
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
