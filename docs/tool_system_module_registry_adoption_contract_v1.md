# tool-system Module Registry Adoption Contract v1

## Metadata and status

- repo_rel_path: docs/tool_system_module_registry_adoption_contract_v1.md
- role: S0 identity/interface mapping authority
- purpose: freeze evidence-backed identity, aggregate-interface, Python-import, static-DAG, compatibility-adapter, and missing-ContractReference facts for separately authorized later adoption stages
- status: S0_IDENTITY_INTERFACE_MAPPING_AUTHORITY
- adoption_state: CANDIDATE_ADOPTION_INPUT
- current_registry_adoption: false
- runtime_activation: false
- central_cutover: false
- immediate_parent: accepted TOOL_SYSTEM_MODULE_REGISTRY_ADOPTION_DESIGN_V1
- global_anchor: blueprint/tool_system_v0.yaml:product_objective
- stop_condition: stop after S0; every S1-S11 stage requires separate authorization

This contract is the formal S0 mapping owner only. It is not the current module
registry, a registry adoption, a runtime activation, or a central-governance
cutover. It creates no second module authority.

## Fixed sources

<!-- S0-SOURCES:BEGIN -->
~~~yaml
source_contract:
  tool_system_repository_commit: 2b86079dbb82d0426240fd6b5836868e5b9c9697
  tool_system_registry_path: config/module_registry_v1.yaml
  tool_system_registry_sha256: c0de8e77e36d8e90f3306ab5becd471a4426e4cef69a9e918cea6520722ecc87
  tool_system_local_schema_path: config/module_registry_schema_v1.json
  tool_system_local_schema_sha256: 14c2083d0ceb640ef6873149d5d05ed63788f42a63b9de44e5fe36a7cbe097b0
  finance_governance_repository_commit: 04ca9d558f59dae17603d7976727aa29782253aa
  finance_governance_schema_path: config/module_registry_schema_v1.json
  finance_governance_schema_sha256: fba270a7ddf8b38dda7cb21263cee8cd96c5b549f0d0b5d364395964b7ecaf67
  blueprint_path: blueprint/tool_system_v0.yaml
  blueprint_sha256: fd5770de23dffd81591c2f268eeafc40100e5541666fa801c1f4a4f977b1628a
  blueprint_section: product_objective
  blueprint_product_objective_id: blueprint_driven_autonomous_software_development
~~~
<!-- S0-SOURCES:END -->

The tool-system commit fixes the observed registry, source tree, tests, and
blueprint. The finance-governance commit fixes the candidate central schema.
The central contract remains candidate pending cutover; these references do not
activate it.

## Fourteen-row identity and aggregate-interface mapping

The current underscore IDs remain rollback and pre-adoption runtime identities
only. The final formal IDs are the corresponding canonical hyphen IDs.
Python package and import names remain unchanged. In particular, no Python
underscore package is renamed to satisfy the formal-ID grammar, and an
underscore string must not remain the final formal module ID.

<!-- S0-IDENTITY-MAPPING:BEGIN -->
~~~yaml
mapping_contract:
  mapping_version: s0-identity-interface-mapping-v1
  module_count: 14
  identity_mapping_owner: src/tool_system/architecture/module_registry.py
  mappings:
    - current_module_id: architecture_registry
      canonical_module_id: architecture-registry
      current_module_version: 1.1.0
      aggregate_interface_id: architecture-registry-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: exact, name: tool_system}
        - {kind: prefix, name: tool_system.architecture}
        - {kind: exact, name: tool_system.cli.validate_module_registry}
        - {kind: exact, name: tool_system.cli.validate_repo_manifest}
      current_observed_consumers: []
      migration_risk: "high: self-hosting registry and manifest validation boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:architecture_registry@1.1.0
    - current_module_id: manifest_validation
      canonical_module_id: manifest-validation
      current_module_version: 1.0.0
      aggregate_interface_id: manifest-validation-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.manifest}
        - {kind: exact, name: tool_system.gate}
        - {kind: exact, name: tool_system.gate.alignment_gate}
        - {kind: exact, name: tool_system.gate.change_plan}
        - {kind: prefix, name: tool_system.policy}
        - {kind: exact, name: tool_system.cli.validate_task_manifest}
        - {kind: exact, name: tool_system.cli.validate_change_plan}
        - {kind: exact, name: tool_system.cli.validate_alignment_gate}
      current_observed_consumers:
        - architecture_registry
        - cleanup_planner
        - cli_frontend
        - process_authority
        - repository_controller
        - role_runtime
        - target_repo_adapter
        - task_planner
        - task_runner
      migration_risk: "critical: shared validation foundation with nine direct consumers"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:manifest_validation@1.0.0
    - current_module_id: agent_worker_runtime
      canonical_module_id: agent-worker-runtime
      current_module_version: 1.0.0
      aggregate_interface_id: agent-worker-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.agent_worker}
      current_observed_consumers:
        - role_runtime
        - worker_adapter
      migration_risk: "high: fixture process and workspace safety boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:agent_worker_runtime@1.0.0
    - current_module_id: ai_worker_runtime
      canonical_module_id: ai-worker-runtime
      current_module_version: 1.0.0
      aggregate_interface_id: ai-worker-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.ai_worker}
      current_observed_consumers: []
      migration_risk: "medium: currently isolated provider-neutral fixture boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:ai_worker_runtime@1.0.0
    - current_module_id: durable_orchestrator
      canonical_module_id: durable-orchestrator
      current_module_version: 1.0.0
      aggregate_interface_id: durable-orchestrator-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.orchestrator}
      current_observed_consumers: []
      migration_risk: "high: persistent SQLite state and recovery boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:durable_orchestrator@1.0.0
    - current_module_id: repository_controller
      canonical_module_id: repository-controller
      current_module_version: 1.0.0
      aggregate_interface_id: repository-controller-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.repo_controller}
      current_observed_consumers:
        - cleanup_planner
        - cli_frontend
        - role_runtime
        - target_repo_adapter
        - task_runner
        - worker_adapter
      migration_risk: "critical: action-scoped Git and GitHub mutation boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:repository_controller@1.0.0
    - current_module_id: process_authority
      canonical_module_id: process-authority
      current_module_version: 2.0.0
      aggregate_interface_id: process-authority-api
      aggregate_interface_version: 2.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.process_authority}
        - {kind: exact, name: tool_system.runner.active_gate_resolver}
        - {kind: exact, name: tool_system.cli.validate_active_gates}
        - {kind: exact, name: tool_system.cli.validate_process_authority}
      current_observed_consumers:
        - task_planner
        - task_runner
      migration_risk: "critical: current task-pair authority and replay boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:process_authority@2.0.0
    - current_module_id: task_planner
      canonical_module_id: task-planner
      current_module_version: 1.1.0
      aggregate_interface_id: task-planner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.planner}
      current_observed_consumers:
        - cli_frontend
        - role_runtime
        - task_runner
      migration_risk: "high: task DAG and process-authority binding boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_planner@1.1.0
    - current_module_id: task_runner
      canonical_module_id: task-runner
      current_module_version: 1.1.0
      aggregate_interface_id: task-runner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: exact, name: tool_system.gate.command_runner}
        - {kind: exact, name: tool_system.gate.test_gate}
        - {kind: exact, name: tool_system.runner.stage_runner}
        - {kind: exact, name: tool_system.runner.task_graph_runner}
        - {kind: exact, name: tool_system.runner.task_runner}
      current_observed_consumers:
        - cli_frontend
      migration_risk: "critical: configured command execution and audit boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_runner@1.1.0
    - current_module_id: role_runtime
      canonical_module_id: role-runtime
      current_module_version: 1.1.0
      aggregate_interface_id: role-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.runtime}
      current_observed_consumers:
        - cli_frontend
      migration_risk: "high: multi-role plan and audit bundle boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:role_runtime@1.1.0
    - current_module_id: worker_adapter
      canonical_module_id: worker-adapter
      current_module_version: 1.0.0
      aggregate_interface_id: worker-adapter-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.worker_adapter}
      current_observed_consumers: []
      migration_risk: "medium: no-mutation orchestration adapter boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:worker_adapter@1.0.0
    - current_module_id: target_repo_adapter
      canonical_module_id: target-repo-adapter
      current_module_version: 1.0.0
      aggregate_interface_id: target-repo-adapter-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.target_repo}
      current_observed_consumers:
        - cli_frontend
      migration_risk: "critical: separately authorized downstream mutation packet boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:target_repo_adapter@1.0.0
    - current_module_id: cleanup_planner
      canonical_module_id: cleanup-planner
      current_module_version: 1.0.0
      aggregate_interface_id: cleanup-planner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: prefix, name: tool_system.cleanup}
      current_observed_consumers:
        - cli_frontend
      migration_risk: "high: must preserve plan-only and separate cleanup authorization"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cleanup_planner@1.0.0
    - current_module_id: cli_frontend
      canonical_module_id: cli-frontend
      current_module_version: 1.1.0
      aggregate_interface_id: cli-frontend-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved_during_s0: true
      python_import_identities:
        - {kind: exact, name: tool_system.cli}
        - {kind: exact, name: tool_system.cli.cleanup_plan}
        - {kind: exact, name: tool_system.cli.controller_run}
        - {kind: exact, name: tool_system.cli.controller_self_check}
        - {kind: exact, name: tool_system.cli.evaluate_github_state}
        - {kind: exact, name: tool_system.cli.evaluate_repo_write}
        - {kind: exact, name: tool_system.cli.execute_change_plan}
        - {kind: exact, name: tool_system.cli.main}
        - {kind: exact, name: tool_system.cli.observe_main_ci}
        - {kind: exact, name: tool_system.cli.plan_requirement}
        - {kind: exact, name: tool_system.cli.plan_task_graph}
        - {kind: exact, name: tool_system.cli.run_batch}
        - {kind: exact, name: tool_system.cli.run_role_graph}
        - {kind: exact, name: tool_system.cli.run_stage}
        - {kind: exact, name: tool_system.cli.run_task}
        - {kind: exact, name: tool_system.cli.run_task_graph}
        - {kind: exact, name: tool_system.cli.target_repo_dry_run}
        - {kind: exact, name: tool_system.cli.target_repo_pr_plan_preview}
      current_observed_consumers: []
      migration_risk: "high: public entrypoint delegation surface"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cli_frontend@1.1.0
~~~
<!-- S0-IDENTITY-MAPPING:END -->

The aggregate interface is the S0 identity assigned to each module's one
currently registered public-interface version. It does not materialize any
central Interface object or claim behavioral compatibility.

## Current static Python import DAG

The edge direction below is provider to direct consumer. The graph is derived
from AST import nodes in the Python files under the fixed S4 target ownership
boundary: the current registry ownership baseline plus only the accepted
`command_runner.py` and `test_gate.py` transfer from manifest-validation to
task-runner. Physical paths and the accepted module DAG remain unchanged.

<!-- S0-STATIC-DAG:BEGIN -->
~~~yaml
static_import_dag:
  basis: python_ast_import_nodes_in_s4_target_owned_source
  direction: provider_to_direct_consumer
  providers:
    architecture_registry: []
    manifest_validation:
      - architecture_registry
      - cleanup_planner
      - cli_frontend
      - process_authority
      - repository_controller
      - role_runtime
      - target_repo_adapter
      - task_planner
      - task_runner
    agent_worker_runtime:
      - role_runtime
      - worker_adapter
    ai_worker_runtime: []
    durable_orchestrator: []
    repository_controller:
      - cleanup_planner
      - cli_frontend
      - role_runtime
      - target_repo_adapter
      - task_runner
      - worker_adapter
    process_authority:
      - task_planner
      - task_runner
    task_planner:
      - cli_frontend
      - role_runtime
      - task_runner
    task_runner:
      - cli_frontend
    role_runtime:
      - cli_frontend
    worker_adapter: []
    target_repo_adapter:
      - cli_frontend
    cleanup_planner:
      - cli_frontend
    cli_frontend: []
  zero_consumer_modules:
    - architecture_registry
    - ai_worker_runtime
    - durable_orchestrator
    - worker_adapter
    - cli_frontend
  non_claim: >-
    Static AST import equality does not prove absence of dynamic imports, CLI
    invocation dependencies, data dependencies, configuration dependencies,
    network dependencies, or hidden dependencies.
~~~
<!-- S0-STATIC-DAG:END -->

Zero-consumer modules remain registered as observed; S0 does not invent an edge
to make the graph look connected.

## Temporary compatibility adapter

The only permitted mapping layer is a future temporary adapter at the existing
natural owner below. It translates identity values in memory at the registry
loader/validator call boundary. It is not authoritative and cannot persist,
publish, cache, or generate another registry.

<!-- S0-ADAPTER:BEGIN -->
~~~yaml
compatibility_adapter:
  natural_owner: src/tool_system/architecture/module_registry.py
  implementation_status: NOT_IMPLEMENTED_IN_S0
  authority: false
  persistence: none
  translation_boundary: memory_only
  caller_boundary: registry_loader_and_validator_entrypoints_only
  registry_paths_read:
    - config/module_registry_v1.yaml
  generated_projection: false
  persistent_projection: false
  cache_registry: false
  legacy_registry: false
  second_registry_authority: false
  second_schema_authority: false
  current_formal_registry_owner: config/module_registry_v1.yaml
  removal_stage: S11
  exit_conditions:
    - S3_module_owned_contract_references_materialized_and_verified
    - S4_single_formal_registry_constructed
    - S7_all_local_consumers_tests_and_CI_use_canonical_identity_contract
    - S9_real_module_registry_check_accepted
    - S10_explicit_cutover_accepted
    - no_remaining_underscore_formal_ID_callers
    - S11_adapter_removal_validation_passes
~~~
<!-- S0-ADAPTER:END -->

The adapter preserves Python imports and transitional caller inputs without
creating hidden dual identity: every translated pair is fixed in the fourteen
mapping rows, the adapter reads exactly one registry path, and only
config/module_registry_v1.yaml may become the current formal registry owner.

## Module-owned ContractReference evidence

No module-owned central ContractReference contract exists at the fixed
tool-system source commit. Shared repository-wide contracts are not substitutes.
S0 therefore leaves path, blob, digest, format, and schema identities unknown.
Only separately authorized S3 may materialize them.

<!-- S0-CONTRACT-REFERENCES:BEGIN -->
~~~yaml
module_owned_contract_references:
  materialization_stage: S3
  records:
    - {module_id: architecture_registry, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: manifest_validation, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: agent_worker_runtime, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: ai_worker_runtime, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: durable_orchestrator, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: repository_controller, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: process_authority, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: task_planner, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: task_runner, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: role_runtime, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: worker_adapter, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: target_repo_adapter, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: cleanup_planner, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
    - {module_id: cli_frontend, repo_relative_path: UNKNOWN, git_blob_sha: UNKNOWN, sha256: UNKNOWN, format_identity: UNKNOWN, schema_identity: UNKNOWN, ready: false}
~~~
<!-- S0-CONTRACT-REFERENCES:END -->

## Stage boundary and stop

The adoption order is fixed, but only S0 is authorized by this contract:

1. S0 — freeze identity, aggregate-interface, import, DAG, adapter, and unknown-reference facts.
2. S1 — reconcile manifest parser and format.
3. S2 — implement bounded consumer/validator compatibility.
4. S3 — materialize module-owned contracts and real ContractReferences.
5. S4 — construct the single formal registry.
6. S5 — align process authority and identity callers.
7. S6 — align blueprint and durable local rule text.
8. S7 — align local tests and CI.
9. S8 — update the immutable governance reference.
10. S9 — run the real central module-registry check.
11. S10 — perform an explicitly authorized cutover.
12. S11 — remove legacy compatibility and prove one remaining route.

S0 completion is a mandatory stop. Each later stage needs its own authorization,
write set, tests, rollback point, completion evidence, non-claims, and
immediate-parent plus product-objective alignment check.

## Dual-anchor alignment

Immediate-parent alignment: this contract implements only the identity/interface
freeze selected by the accepted TOOL_SYSTEM_MODULE_REGISTRY_ADOPTION_DESIGN_V1.
It does not implement that design's later migration stages.

Global alignment: the stable module and aggregate-interface identities support
blueprint/tool_system_v0.yaml:product_objective by preserving durable,
replaceable module boundaries and bounded downstream revalidation without
changing the active runtime or authorization envelope.

## Non-claims

<!-- S0-NON-CLAIMS:BEGIN -->
~~~yaml
non_claims:
  current_registry_changed: false
  local_schema_changed: false
  manifest_parser_changed: false
  runtime_changed: false
  validator_changed: false
  CI_changed: false
  blueprint_changed: false
  process_authority_changed: false
  governance_reference_changed: false
  module_registry_check_executed: false
  module_registry_check_pass_claimed: false
  governance_activated: false
  central_cutover_completed: false
  provider_execution_authorized: false
  target_mutation_authorized: false
  cleanup_authorized: false
  production_authorized: false
  S1_through_S11_started: false
~~~
<!-- S0-NON-CLAIMS:END -->

S0 changes only this mapping contract, its manifest registration, and validation
evidence. It grants no provider, target, cleanup, production, governance
activation, central gate, cutover, or later-stage authority.
