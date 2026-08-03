# Adaptive Model Portfolio and Economics Module Compound Contract v1

This file defines the isolated-fixture implementation owned by the
`adaptive_model_portfolio_and_economics` module. It profiles finite caller-owned
fixture inputs, evaluates hard floors before economics, selects one deterministic
eligible route, and classifies bounded failure dispositions. It cannot execute a
live route or grant provider, credential, repository, mutation, or production
authority.

<!-- MODULE-COMPOUND-CONTRACT:BEGIN -->
~~~yaml
module_compound_contract:
  format_identity: tool-system-module-compound-contract-v1
  schema_identity: tool-system-module-compound-contract-schema-v1
  contract_path: docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md
  identity:
    canonical_module_id: adaptive-model-portfolio-and-economics
    current_module_id: adaptive_model_portfolio_and_economics
    module_version: 1.0.0
    aggregate_interface:
      interface_id: adaptive-model-portfolio-and-economics-api
      interface_version: 1.0.0
    mapping_owner:
      contract_path: docs/tool_system_module_registry_contract_v1.md
      implementation_path: src/tool_system/architecture/module_registry.py
    rollback_identity: tool-system@f912add44845be9d60021333c6792e4ecf6a142b:adaptive_model_portfolio_and_economics@absent
    python_import_identities:
      - kind: prefix
        name: tool_system.provider_portfolio
  role:
    summary: profile isolated fixture tasks and select one deterministic authorized fixture provider-model route after every hard floor passes
    responsibility_boundary: Validate immutable task profiles, exact catalog and authorization snapshots, fixture-only structural AIWorkerProvider adapters, integer expected-total-economic-cost components, and distinct availability, quality, policy-block, and stop failures without executing a live route or reading external state.
  natural_owner_evidence_paths:
    - src/tool_system/provider_portfolio/__init__.py
    - src/tool_system/provider_portfolio/fixtures.py
  dependency_contract:
    basis: tool-system-static-python-import-dag
    direction: provider-to-direct-consumer
    direct_provider_module_ids:
      - ai_worker_runtime
    direct_consumer_module_ids: []
  input_contract:
    registered_inputs:
      - advisory_task_profile_fixture_v1
      - exact_provider_model_catalog_snapshot_v1
      - isolated_fixture_authorization_envelope_v1
      - provider_neutral_adapter_scenarios_v1
    boundary: Accept finite immutable fixture values with exact task, capability, risk, evidence, catalog, policy, authorization, token, time, attempt, and integer economic-cost fields; secret values, live surfaces, real repositories, and authority-bearing inputs are rejected.
  output_contract:
    registered_outputs:
      - deterministic_fixture_route_decision_v1
      - bounded_failure_disposition_v1
      - structural_AIWorkerProvider_fixture_response_v1
    boundary: Return one content-addressed non-authorizing route decision with every candidate evaluation, ordered eligible and bounded fallback or escalation route IDs, stable stop reason, zero-operation counters, or one in-memory provider-neutral fixture response.
  error_contract:
    registered_error_semantics:
      - stable_fail_closed_fixture_validation_and_hard_floor_reasons
    boundary: Malformed or non-canonical inputs raise a stable local validation error; version, evidence, authorization, capability, risk, data, context, output, time, cost, credential, network, or live-surface mismatch yields deterministic ineligible or blocked evidence without provider bypass.
  side_effect_contract:
    taxonomy_source: docs/tool_system_module_registry_contract_v1.md#side-effect-taxonomy
    effect_classes: []
    direct_effects: []
    delegated_effects: []
    classification_grants_authority: false
  compatibility_policy:
    interface_compatible_replacement: Preserve immutable canonical inputs, exact qualification states, independent complexity and risk fields, hard-floors-before-economics ordering, integer cost totals, deterministic evidence hashes, bounded failure semantics, structural AIWorkerProvider fixture compatibility, and zero external effects.
    interface_incompatible_change: Requires a new aggregate interface version and revalidation of the ai-worker-runtime provider boundary plus every future portfolio consumer before activation.
  rollback_contract:
    rollback_identity: tool-system@f912add44845be9d60021333c6792e4ecf6a142b:adaptive_model_portfolio_and_economics@absent
    method: Revert through a separately audited pull request and rerun portfolio fixture, module registry, module contract, import graph, repository manifest, phase-state, and full tests without executing rollback here.
  replacement_contract:
    activation_rule: Replace only after deterministic profiling, hard-floor ordering, integer economics, catalog and policy drift, failure classification, structural adapter, zero-side-effect, module-boundary, and full tests pass in isolated fixtures.
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
      mode: in-memory-only
      contract: Profiles, catalogs, authorization envelopes, scenario maps, evaluations, decisions, and failure policies remain caller-owned in-memory values.
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
