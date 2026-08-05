# Adaptive Model Portfolio and Economics Module Compound Contract v1

This file defines the repository-external provider-mode selector, retained
isolated exact-catalog compatibility fixtures, non-authorizing P15D prerequisite
corpus, and pure in-memory failure-control implementation owned by the
`adaptive_model_portfolio_and_economics` module. The active selector preserves
operator provider order and requested model identifiers, returns `API_DISABLED`
unless API mode is explicit, skips unavailable routes, blocks non-bypassable
authorization, transfer, budget, precondition, cancellation, or fake-I/O
contract failures, and selects at most one route without resolving a credential
or performing I/O. It cannot execute a live route, enter P15D, or grant provider,
credential, repository, mutation, rollback, or production authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md
  identity:
    canonical_module_id: adaptive-model-portfolio-and-economics
    current_module_id: adaptive_model_portfolio_and_economics
    module_version: 2.0.0
    aggregate_interface:
      interface_id: adaptive-model-portfolio-and-economics-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@529001694c6d41ee819736293418cebfe455c392:adaptive_model_portfolio_and_economics@1.3.0
    python_import_identities:
      - kind: prefix
        name: tool_system.provider_portfolio
  role:
    summary: select one repository-external explicitly enabled provider and requested model from a bounded operator-priority snapshot after every hard control passes, retain exact-catalog fixtures only for compatibility, and return pure in-memory non-executing failure-control isolation and integer economics decisions
    responsibility_boundary: Validate immutable provider-mode snapshots, route availability, fake-I/O contract evidence, provider transfer permission, authorization state, policy and source preconditions, bounded attempts, integer reservations and budgets, plus retained task-profile, exact-catalog, P15D prerequisite, failure, rollback, isolation, and synthetic total-economic-cost fixtures; never inspect a key, require simultaneous provider availability, require funding for a named provider, require an exact version behind a moving alias, dispatch a route, apply a candidate, execute rollback, enter P15D, or read external state.
  natural_owner_evidence_paths:
    - src/tool_system/provider_portfolio/__init__.py
    - src/tool_system/provider_portfolio/failure_control.py
    - src/tool_system/provider_portfolio/fixtures.py
    - src/tool_system/provider_portfolio/provider_mode.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - ai_worker_runtime
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - repository_external_provider_mode_snapshot_v1
      - operator_ordered_provider_requested_model_route_v1
      - advisory_task_profile_fixture_v1
      - exact_provider_model_catalog_snapshot_v1
      - exact_non_executing_provider_case_matrix_v1
      - p15d_non_authorizing_failure_economics_prerequisite_corpus_v1
      - isolated_fixture_authorization_envelope_v1
      - provider_neutral_adapter_scenarios_v1
      - failure_control_request_v1
      - bounded_cycle_observation_v1
      - module_isolation_request_v1
      - total_economic_cost_fixture_v1
    boundary: Accept finite immutable caller-owned provider-mode values containing only non-secret provider identifiers, externally requested model identifiers, enablement, availability classification, fake-I/O evidence, transfer permission, authorization state, bounded attempts, integer reservations and budgets, plus retained public fixture catalog and P15D prerequisite metadata. Key values, key-presence authority, private economic values, repository-owned live provider/model selection, live surfaces, real repositories, and authority-bearing inputs are rejected.
  output_contract:
    registered_outputs:
      - default_disabled_provider_mode_decision_v1
      - ordered_single_route_selection_or_skip_decision_v1
      - deterministic_fixture_route_decision_v1
      - bounded_failure_disposition_v1
      - structural_AIWorkerProvider_fixture_response_v1
      - frozen_non_executing_provider_case_matrix_record_v1
      - frozen_p15d_non_authorizing_prerequisite_corpus_record_v1
      - non_executing_failure_control_decision_v1
      - finite_no_progress_decision_v1
      - non_executing_module_isolation_plan_v1
      - hard_floor_gated_total_economic_cost_decision_v1
    boundary: Return `API_DISABLED`, `SELECTED`, `NO_AVAILABLE_PROVIDER`, or `BLOCKED` with the externally ordered eligible, skipped, bounded failover, and quality-escalation route identifiers; preserve requested moving aliases without inventing resolved versions; or return one retained content-addressed fixture, failure-control, no-progress, isolation, rollback-plan, P15D prerequisite-corpus, or integer total-economic-cost decision. Every output denies dispatch, application, rollback, cleanup, key access, provider invocation, and network authority.
  error_contract:
    registered_error_semantics:
      - stable_fail_closed_fixture_validation_and_hard_floor_reasons
    boundary: Malformed, negative, floating, duplicate-provider, or inconsistent inputs raise a stable local validation error. API disabled returns before route activation. Disabled, unconfigured, unfunded, missing-key, invalid-key, expired-key, quota, rate-limit, or unavailable states yield deterministic skips; inactive or expired authorization, stale policy or source preconditions, cancellation, missing fake-I/O proof, provider transfer denial, and hard-budget failure yield deterministic non-bypassable blocks. An exhausted eligible set returns `NO_AVAILABLE_PROVIDER` without treating a named provider or model as a completion requirement.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve the aggregate interface while adding the active repository-external provider-mode decision. Preserve all-API-default-disabled behavior, operator order and requested model identity, key non-authority, availability-only skips, hard-control non-bypass, fake-I/O evidence, one-route selection, integer budget floors, bounded failover and retry planning, deterministic evidence hashes, retained exact-catalog fixture compatibility, P15D corpus identity, cancellation, no-progress, isolation, non-executing rollback plans, structural AIWorkerProvider fixture compatibility, fail-closed runtime consumption, stage-entry gates, and zero external effects.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of the ai-worker-runtime provider boundary plus every future portfolio consumer before activation.
  rollback_contract:
    rollback_identity: tool-system@529001694c6d41ee819736293418cebfe455c392:adaptive_model_portfolio_and_economics@1.3.0
    method: Revert through a separately audited pull request and rerun portfolio route, failure-control, no-progress, isolation, economics, module registry, module contract, import graph, repository manifest, phase-state, and full tests without executing rollback here.
  replacement_contract:
    activation_rule: Replace only after default-disabled, repository-external order and requested-model, availability skip, `NO_AVAILABLE_PROVIDER`, hard-control non-bypass, fake-I/O proof, moving-alias, integer budget, bounded failure-control compatibility, retained exact-catalog and P15D-corpus compatibility, cancellation, no-progress, isolation, non-executing rollback-plan, zero-side-effect, module-boundary, and full tests pass without credential access, provider execution, P15 acceptance, P16 entry, or final live smoke.
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
      contract: Repository shape, size, risk, and mutation intent arrive only as bounded task-profile scalars; this module performs no filesystem, Git, or repository operation.
    data:
      mode: repository-config-and-in-memory-only
      contract: The public P15D prerequisite corpus and retained exact packet are non-authorizing repository compatibility configurations. Active provider/model order, enablement, availability and budgets arrive only as caller-owned in-memory values derived from repository-external local configuration. No key value, private economic value, live evidence, or execution authority is accepted or stored.
    artifact:
      mode: result-only
      contract: Evidence hashes and records are returned to the caller and are not written, cached, published, or treated as execution receipts.
    database:
      mode: none
      contract: This module owns no database connection, schema, migration, ledger, credential store, billing store, or benchmark store.
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
