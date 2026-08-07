# tool-system Module Registry Contract v1

## Local ownership

- repo_rel_path: docs/tool_system_module_registry_contract_v1.md
- role: tool-system module identity, import ownership, and static DAG contract
- owner: architecture_registry module
- registry_path: config/module_registry_v1.yaml
- implementation_path: src/tool_system/architecture/module_registry.py
- global_anchor: blueprint/tool_system_v0.yaml:product_objective

This is a tool-system-owned implementation and validation contract. It grants
no execution, downstream-repository, cleanup, provider, or production
authority, and it records no external policy state.

## Twenty-two-row identity and aggregate-interface mapping

The canonical registry IDs use hyphens while Python package and import names
remain unchanged. The mapping below is the local identity owner used by the
registry validator and module-contract tests.

<!-- MODULE-IDENTITY-MAPPING:BEGIN -->
~~~yaml
mapping_contract:
  mapping_version: tool-system-module-identity-mapping-v1
  module_count: 22
  identity_mapping_owner: src/tool_system/architecture/module_registry.py
  mappings:
    - current_module_id: architecture_registry
      canonical_module_id: architecture-registry
      current_module_version: 2.0.0
      aggregate_interface_id: architecture-registry-api
      aggregate_interface_version: 2.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: exact, name: tool_system}
        - {kind: prefix, name: tool_system.architecture}
        - {kind: exact, name: tool_system.cli.validate_module_registry}
        - {kind: exact, name: tool_system.cli.validate_repo_manifest}
      direct_consumer_module_ids: []
      change_risk: "high: self-hosting registry and manifest validation boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:architecture_registry@1.1.0
    - current_module_id: manifest_validation
      canonical_module_id: manifest-validation
      current_module_version: 1.0.0
      aggregate_interface_id: manifest-validation-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.manifest}
        - {kind: exact, name: tool_system.gate}
        - {kind: exact, name: tool_system.gate.alignment_gate}
        - {kind: exact, name: tool_system.gate.change_plan}
        - {kind: prefix, name: tool_system.policy}
        - {kind: exact, name: tool_system.cli.validate_task_manifest}
        - {kind: exact, name: tool_system.cli.validate_change_plan}
        - {kind: exact, name: tool_system.cli.validate_alignment_gate}
      direct_consumer_module_ids:
        - architecture_registry
        - cleanup_planner
        - cli_frontend
        - process_authority
        - repository_controller
        - role_runtime
        - target_repo_adapter
        - task_planner
        - task_runner
      change_risk: "critical: shared validation foundation with nine direct consumers"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:manifest_validation@1.0.0
    - current_module_id: agent_worker_runtime
      canonical_module_id: agent-worker-runtime
      current_module_version: 1.0.0
      aggregate_interface_id: agent-worker-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.agent_worker}
      direct_consumer_module_ids:
        - role_runtime
        - worker_adapter
      change_risk: "high: fixture process and workspace safety boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:agent_worker_runtime@1.0.0
    - current_module_id: ai_worker_runtime
      canonical_module_id: ai-worker-runtime
      current_module_version: 2.0.0
      aggregate_interface_id: ai-worker-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.ai_worker}
      direct_consumer_module_ids:
        - adaptive_model_portfolio_and_economics
      change_risk: "critical: the default remains fixture-only, the generic worker adds a default-disabled exact externally selected route guard, P14C is unchanged, and schema 3 adds a source-sealed single-success API backup chain with public-fixture-only input, bounded availability failover, and all-provider fake-I/O; no live authority is added"
      rollback_identity: tool-system@149296ff5e87e6b18a4982a9046012fd3edeb1b0:ai_worker_runtime@1.9.1
    - current_module_id: adaptive_model_portfolio_and_economics
      canonical_module_id: adaptive-model-portfolio-and-economics
      current_module_version: 2.0.0
      aggregate_interface_id: adaptive-model-portfolio-and-economics-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.provider_portfolio}
      direct_consumer_module_ids: []
      change_risk: "high: the active pure in-memory portfolio path now consumes repository-external provider order and requested models, keeps every API default-disabled, skips only unavailable routes, blocks hard-control bypass, requires fake-I/O evidence, selects at most one route, and retains exact-matrix behavior only as compatibility; it adds no execution authority and does not accept P15 or enter P16"
      rollback_identity: tool-system@529001694c6d41ee819736293418cebfe455c392:adaptive_model_portfolio_and_economics@1.3.0
    - current_module_id: durable_orchestrator
      canonical_module_id: durable-orchestrator
      current_module_version: 1.2.0
      aggregate_interface_id: durable-orchestrator-api
      aggregate_interface_version: 1.1.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.orchestrator}
      direct_consumer_module_ids:
        - process_authority
        - local_git
      change_risk: "high: persistent SQLite state, race-safe optional-sidecar validation, recovery, and burn-on-claim authorization boundary"
      rollback_identity: tool-system@783a1bf16c48e717da281d9fefc134e68bf879c4:durable_orchestrator@1.1.0
    - current_module_id: repository_controller
      canonical_module_id: repository-controller
      current_module_version: 1.2.0
      aggregate_interface_id: repository-controller-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.repo_controller}
      direct_consumer_module_ids:
        - cleanup_planner
        - cli_frontend
        - role_runtime
        - target_repo_adapter
        - task_runner
        - worker_adapter
      change_risk: "critical: action-scoped Git and GitHub mutation boundary"
      rollback_identity: tool-system@6cb43f8723619bddfdd4c5b52a7d68db1ea3f30f:repository_controller@1.1.0
    - current_module_id: process_authority
      canonical_module_id: process-authority
      current_module_version: 2.3.0
      aggregate_interface_id: process-authority-api
      aggregate_interface_version: 2.1.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.process_authority}
        - {kind: exact, name: tool_system.runner.active_gate_resolver}
        - {kind: exact, name: tool_system.cli.validate_active_gates}
        - {kind: exact, name: tool_system.cli.validate_process_authority}
      direct_consumer_module_ids:
        - ai_worker_runtime
        - task_planner
        - task_runner
      change_risk: "critical: current task-pair authority, operator-entry source binding, and durable single-host GitHub-owner approval consumption"
      rollback_identity: tool-system@999cb60d20a15730dbf0096ad20a598f3bf0fa5c:process_authority@2.2.0
    - current_module_id: task_planner
      canonical_module_id: task-planner
      current_module_version: 1.1.0
      aggregate_interface_id: task-planner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.planner}
      direct_consumer_module_ids:
        - cli_frontend
        - role_runtime
        - task_runner
      change_risk: "high: task DAG and process-authority binding boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_planner@1.1.0
    - current_module_id: task_runner
      canonical_module_id: task-runner
      current_module_version: 1.1.0
      aggregate_interface_id: task-runner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: exact, name: tool_system.gate.command_runner}
        - {kind: exact, name: tool_system.gate.test_gate}
        - {kind: exact, name: tool_system.runner.stage_runner}
        - {kind: exact, name: tool_system.runner.task_graph_runner}
        - {kind: exact, name: tool_system.runner.task_runner}
      direct_consumer_module_ids:
        - cli_frontend
      change_risk: "critical: configured command execution and audit boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:task_runner@1.1.0
    - current_module_id: role_runtime
      canonical_module_id: role-runtime
      current_module_version: 1.1.0
      aggregate_interface_id: role-runtime-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.runtime}
      direct_consumer_module_ids:
        - cli_frontend
      change_risk: "high: multi-role plan and audit bundle boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:role_runtime@1.1.0
    - current_module_id: worker_adapter
      canonical_module_id: worker-adapter
      current_module_version: 1.0.0
      aggregate_interface_id: worker-adapter-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.worker_adapter}
      direct_consumer_module_ids: []
      change_risk: "medium: no-mutation orchestration adapter boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:worker_adapter@1.0.0
    - current_module_id: target_repo_adapter
      canonical_module_id: target-repo-adapter
      current_module_version: 1.0.0
      aggregate_interface_id: target-repo-adapter-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.target_repo}
      direct_consumer_module_ids:
        - cli_frontend
      change_risk: "critical: separately authorized downstream mutation packet boundary"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:target_repo_adapter@1.0.0
    - current_module_id: cleanup_planner
      canonical_module_id: cleanup-planner
      current_module_version: 1.0.0
      aggregate_interface_id: cleanup-planner-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.cleanup}
      direct_consumer_module_ids:
        - cli_frontend
      change_risk: "high: must preserve plan-only and separate cleanup authorization"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cleanup_planner@1.0.0
    - current_module_id: cli_frontend
      canonical_module_id: cli-frontend
      current_module_version: 1.1.0
      aggregate_interface_id: cli-frontend-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
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
      direct_consumer_module_ids: []
      change_risk: "high: public entrypoint delegation surface"
      rollback_identity: tool-system@2b86079dbb82d0426240fd6b5836868e5b9c9697:cli_frontend@1.1.0
    - current_module_id: repository_context
      canonical_module_id: repository-context
      current_module_version: 1.0.0
      aggregate_interface_id: repository-context-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.repository_context}
      direct_consumer_module_ids: []
      change_risk: "medium: bounded read-only local Git context and non-authorizing natural-owner evidence boundary"
      rollback_identity: tool-system@7e3a114a25d70c3ebecc952f13ce68b1adbbbc80:repository_context@absent
    - current_module_id: blueprint_compiler
      canonical_module_id: blueprint-compiler
      current_module_version: 1.0.0
      aggregate_interface_id: blueprint-compiler-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.blueprint_compiler}
      direct_consumer_module_ids: []
      change_risk: "medium: deterministic non-authorizing blueprint compilation and task-graph compatibility boundary"
      rollback_identity: tool-system@00793ad07bba2e3fe3bd29882e83788d32697da6:blueprint_compiler@absent
    - current_module_id: development_loop
      canonical_module_id: development-loop
      current_module_version: 1.1.0
      aggregate_interface_id: development-loop-api
      aggregate_interface_version: 1.1.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.development_loop}
      direct_consumer_module_ids:
        - local_git
      change_risk: "medium: bounded in-memory fixture patch, validation, repair, review, and no-progress termination boundary"
      rollback_identity: tool-system@0b5110a2eea79ebde650e1088b787c781ddab171:development_loop@absent
    - current_module_id: local_git
      canonical_module_id: local-git
      current_module_version: 1.1.0
      aggregate_interface_id: local-git-api
      aggregate_interface_version: 1.1.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.local_git}
      direct_consumer_module_ids: []
      change_risk: "high: remote-free add/modify/delete local Git writes coordinated with durable receipts and crash resume"
      rollback_identity: tool-system@22dedb0f2a2c0b38a0bd4c67f36c1c2454ca19d5:local_git@absent
    - current_module_id: release_governance
      canonical_module_id: release-governance
      current_module_version: 1.0.0
      aggregate_interface_id: release-governance-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.release_governance}
      direct_consumer_module_ids:
        - state_migration
      change_risk: "medium: deterministic non-authorizing release compatibility and deprecation boundary"
      rollback_identity: tool-system@c35be57de6ff1f7e31446469281fa369f529d937:release_governance@absent
    - current_module_id: state_migration
      canonical_module_id: state-migration
      current_module_version: 1.0.0
      aggregate_interface_id: state-migration-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.state_migration}
      direct_consumer_module_ids:
        - recovery_planning
      change_risk: "medium: deterministic product-wide migration compatibility and dry-run planning boundary"
      rollback_identity: tool-system@315f4bb08aacf038e0391a0a55553fe1bed67a26:state_migration@absent
    - current_module_id: recovery_planning
      canonical_module_id: recovery-planning
      current_module_version: 1.0.0
      aggregate_interface_id: recovery-planning-api
      aggregate_interface_version: 1.0.0
      runtime_id_preserved: true
      python_import_identities:
        - {kind: prefix, name: tool_system.recovery_planning}
      direct_consumer_module_ids: []
      change_risk: "medium: deterministic non-live backup verification, restore planning, and disaster-recovery evaluation boundary"
      rollback_identity: tool-system@a4042551e5c2b77e07db30ecdbdb5ae28f618ec7:recovery_planning@absent
~~~
<!-- MODULE-IDENTITY-MAPPING:END -->

The aggregate interface is the local identity assigned to each module's one
currently registered public-interface version. This mapping alone does not
claim behavioral compatibility.

## Current static Python import DAG

The edge direction below is provider to direct consumer. The graph is derived
from AST import nodes in the Python files under the current registry ownership
boundary.

<!-- MODULE-STATIC-DAG:BEGIN -->
~~~yaml
static_import_dag:
  basis: python_ast_import_nodes_in_current_owned_source
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
    ai_worker_runtime:
      - adaptive_model_portfolio_and_economics
    adaptive_model_portfolio_and_economics: []
    durable_orchestrator:
      - process_authority
      - local_git
    repository_controller:
      - cleanup_planner
      - cli_frontend
      - role_runtime
      - target_repo_adapter
      - task_runner
      - worker_adapter
    process_authority:
      - ai_worker_runtime
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
    repository_context: []
    blueprint_compiler: []
    development_loop:
      - local_git
    local_git: []
    release_governance:
      - state_migration
    state_migration:
      - recovery_planning
    recovery_planning: []
  zero_consumer_modules:
    - architecture_registry
    - adaptive_model_portfolio_and_economics
    - durable_orchestrator
    - worker_adapter
    - cli_frontend
    - repository_context
    - blueprint_compiler
    - development_loop
    - local_git
    - recovery_planning
  non_claim: >-
    Static AST import equality does not prove absence of dynamic imports, CLI
    invocation dependencies, data dependencies, configuration dependencies,
    network dependencies, or hidden dependencies.
~~~
<!-- MODULE-STATIC-DAG:END -->

Zero-consumer modules remain registered as observed; the validator does not
invent edges to make the graph look connected.

## Side-effect taxonomy

The tool-system-owned module effect classes are:

- `repository_write`
- `data_write`
- `generated_artifact_write`
- `git_write`
- `database_write`
- `network_write`
- `external_system_write`
- `production_operation`

Classification documents possible effects but grants no execution authority.
Each module contract must bind every declared effect to module-owned evidence
and the current registry must bind every permitted effect to a registered local
boundary.

## Change and rollback boundary

Changes to identities, import ownership, dependency edges, interfaces, effect
classes, or ContractReference hashes require a separately audited tool-system
change with affected module and downstream-closure validation. Rollback uses
the repository history and the per-module rollback identities recorded in this
contract. This contract cannot authorize target mutation, provider execution,
cleanup execution, or production operation.
