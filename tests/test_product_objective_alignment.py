from __future__ import annotations

import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
BLUEPRINT_SCHEMA = (
    ROOT / "blueprint" / "schema" / "tool_system_blueprint.schema.json"
)
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
P14R_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14r_blueprint_product_objective_roadmap_reconciliation.yaml"
)


def test_product_objective_controls_the_end_to_end_flow() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    objective = blueprint["product_objective"]
    contract = blueprint["product_contract"]
    alignment = blueprint["global_alignment"]

    assert blueprint["schema_version"] == 0.6
    assert "compatibility_identifier_semantics" not in blueprint
    assert objective["id"] == "blueprint_driven_autonomous_software_development"
    assert set(objective["required_end_to_end_flow"]) == {
        "ingest_approved_blueprint",
        "inspect_repository_state",
        "build_repository_context",
        "decompose_milestones",
        "assemble_durable_module_dag_and_milestone_change_bindings",
        "validate_module_interfaces_and_dependencies",
        "generate_task_dag",
        "generate_phase_documents",
        "generate_task_manifests",
        "generate_change_plans",
        "identify_natural_owners",
        "freeze_bounded_closure_contract",
        "profile_task_complexity_risk_and_critical_path",
        "resolve_authorized_provider_model_portfolio",
        "select_route_by_expected_total_economic_cost",
        "invoke_bounded_real_ai_worker",
        "execute_bounded_provider_availability_failover",
        "execute_bounded_model_quality_escalation",
        "implement_code_changes",
        "validate_file_scope",
        "run_tests",
        "diagnose_failures",
        "repair_with_bounded_retry",
        "persist_cycle_state_and_detect_no_progress",
        "review_parent_alignment",
        "review_global_product_objective_alignment",
        "isolate_and_replace_failed_or_drifted_modules",
        "revalidate_affected_module_dependents",
        "create_local_git_commits",
        "produce_draft_pull_request_plan",
        "prepare_separately_authorized_repository_publish_action",
        "record_provider_model_outcomes_and_economics",
        "produce_acceptance_evidence",
        "seal_terminal_candidate_and_restrict_evidence_reopening",
        "close_completed_milestones",
    }
    assert "approved_project_blueprint" in contract["inputs"]
    assert "authorization_envelope" in contract["inputs"]
    assert "authorized_provider_model_portfolio_snapshot" in contract["inputs"]
    assert "private_project_economics_references" in contract["inputs"]
    assert "durable_module_contract_and_milestone_change_binding" in (
        contract["inputs"]
    )
    assert "milestone_module_invariant_and_project_adoption_record" not in (
        contract["inputs"]
    )
    assert "bounded_code_patches" in contract["outputs"]
    assert "durable_module_dag_and_milestone_change_bindings" in contract["outputs"]
    assert "module_interface_and_dependency_contracts" in contract["outputs"]
    assert "module_isolation_replacement_and_revalidation_evidence" in (
        contract["outputs"]
    )
    assert "separately_authorized_draft_pull_request" in contract["outputs"]
    assert "acceptance_and_closure_record" in contract["outputs"]
    assert "task_complexity_and_risk_profile" in contract["outputs"]
    assert "provider_model_routing_failover_and_escalation_plan" in (
        contract["outputs"]
    )
    assert "provider_model_outcome_and_economic_evidence" in contract["outputs"]
    assert alignment == {
        "required_for_every_milestone": True,
        "required_for_every_task_manifest": True,
        "required_for_every_change_plan": True,
        "required_for_every_acceptance_record": True,
        "require_direct_parent_alignment": True,
        "require_global_product_objective_alignment": True,
        "product_objective_ref": "product_objective",
        "fail_closed_on_missing_alignment": True,
    }


def test_blueprint_is_target_state_only_and_schema_rejects_progress_keys() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    schema = json.loads(BLUEPRINT_SCHEMA.read_text(encoding="utf-8"))
    project_state = load_yaml_file(PROJECT_STATE)
    process_keys = {
        "phase",
        "status",
        "acceptance",
        "successor_authorization",
        "active_phase_execution",
        "p14c_source_implementation",
    }

    assert set(blueprint) == set(schema["required"])
    assert set(schema["properties"]) == set(schema["required"])
    assert process_keys.isdisjoint(blueprint)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == 0.6
    assert project_state["role"] == "descriptive_project_progress_only"
    assert project_state["authority_effect"] == "none"
    assert project_state["blueprint"]["process_state_allowed_in_blueprint"] is False
    assert project_state["evidence_rule"]["blueprint_is_not_a_progress_ledger"] is True
    blueprint_text = BLUEPRINT.read_text(encoding="utf-8")
    for process_marker in (
        "_implemented:",
        "current_task_caller_audit_complete:",
        "accepted_at:",
        "authorized_at:",
        "pull_request_ci_run_id:",
        "main_ci_run_id:",
        "branch_retained:",
    ):
        assert process_marker not in blueprint_text


def test_completion_and_non_goals_prevent_false_product_claims() -> None:
    objective = load_yaml_file(BLUEPRINT)["product_objective"]

    assert set(objective["completion_definition"]) >= {
        "approved_blueprint_converts_to_executable_task_graph",
        "bounded_projects_complete_end_to_end_in_isolated_repositories",
        "real_ai_worker_performs_controlled_implementation_and_repair",
        "every_milestone_proves_parent_and_global_objective_alignment",
        "every_milestone_identifies_one_durable_module_or_versioned_interface_change",
        "interface_compatible_replacement_preserves_unaffected_modules",
        "failed_or_drifted_modules_pause_dependents_until_revalidation",
        "hidden_cross_module_dependencies_are_rejected",
        "failed_runs_stop_or_rollback_without_silent_scope_expansion",
        "closure_contract_is_frozen_before_execution_while_candidate_tree_remains_per_cycle_state",
        "repeated_or_non_progress_cycles_stop_within_finite_budgets",
        "recurrence_fingerprint_excludes_attempt_and_bookkeeping_metadata",
        "evidence_and_pr_metadata_cannot_create_new_acceptance_obligations",
        "sealed_candidate_reopens_only_by_user_authorization_or_original_acceptance_violation",
        "crash_recovery_does_not_duplicate_task_branch_commit_or_pull_request",
        "system_never_invents_milestones_acceptance_conditions_authority_or_endpoints",
        "task_profile_and_routing_decisions_are_auditable_and_reproducible",
        "provider_unavailability_and_quality_failure_have_distinct_bounded_controls",
        "model_selection_uses_task_class_evidence_and_expected_total_economic_cost",
        "safety_quality_data_and_authorization_floors_override_economics",
        "credentials_and_private_economic_values_remain_outside_public_repository",
        "chatgpt_codex_subscription_is_the_daily_development_route",
        "every_large_model_api_is_disabled_by_default",
        "api_key_presence_never_grants_call_authority",
        "live_provider_and_model_selection_is_repository_external",
        "unavailable_or_unfunded_api_providers_may_be_skipped",
        "every_provider_specific_adapter_passes_fake_io_contract_tests",
        "one_enabled_usable_api_key_smoke_proves_the_backup_path",
        "simultaneous_multi_provider_availability_is_not_a_completion_gate",
        "named_provider_funding_is_not_a_completion_gate",
        "moving_model_alias_exact_version_is_not_a_completion_gate",
    }
    assert set(objective["non_goals"]) >= {
        "unrestricted_remote_repository_mutation",
        "autonomous_production_deployment",
        "bypassing_human_authorization_boundaries",
        "claiming_codex_replacement_without_independent_evidence",
    }


def test_successor_chain_builds_product_before_benchmark_and_operations() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    milestones = blueprint["milestones"]
    p14 = milestones["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    p15 = milestones["P15_MULTI_PROJECT_BENCHMARK"]
    p16 = milestones["P16_PRODUCTION_OPERATIONS_ACCEPTANCE"]

    assert "P14_MULTI_REPO_BENCHMARK" not in milestones
    assert "P15_PRODUCTION_OPERATIONS_ACCEPTANCE" not in milestones
    assert "P13_SECURITY_RELIABILITY_HARDENING accepted" in p14["entry_requires"]
    assert "explicit P14 phase-entry authorization" in p14["entry_requires"]
    assert "implementation begins in isolated local fixture repositories only" in (
        p14["entry_requires"]
    )
    assert "autonomous patch-test-diagnose-repair-review loop" in p14["outputs"]
    assert "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT accepted" in (
        p15["entry_requires"]
    )
    assert (
        "each benchmark project supplies its own explicitly authorized "
        "durable-module contract"
    ) in (
        p15["entry_requires"]
    )
    assert "every benchmark project passes the milestone-module adoption gate" not in (
        p15["entry_requires"]
    )
    assert "each real repository mutation separately authorized" in (
        p15["entry_requires"]
    )
    assert not any("final live API backup smoke" in item for item in p15["entry_requires"])
    assert "deterministic policy-owned routing decisions and hard capability floors" in (
        p15["outputs"]
    )
    assert (
        "quality, time-to-acceptance, expected total economic cost, recovery, "
        "and policy metrics"
    ) in p15["outputs"]
    assert (
        "independent optional API plugin release criteria requiring one controlled "
        "smoke through any single explicitly enabled usable key only when that "
        "plugin is separately released"
    ) in p15["outputs"]
    assert (
        "explicit proof that simultaneous multi-provider availability Qwen "
        "funding and moving-alias exact versions are not completion gates"
    ) in p15["outputs"]
    assert [stage["stage"] for stage in p15["stage_plan"]] == [
        "P15A_PROVIDER_PORTFOLIO_QUALIFICATION_SPECIFICATION",
        "P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES",
        "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK",
        "P15D_FAILURE_ROLLBACK_ISOLATION_AND_ECONOMICS_CORPUS",
        "P15E_OPTIONAL_CONTROLLED_TARGET_MUTATION_PILOT",
        "P15F_BENCHMARK_ACCEPTANCE_CLOSURE",
    ]
    assert "P15_MULTI_PROJECT_BENCHMARK accepted" in p16["entry_requires"]
    assert "production deployment remains separately approved only" in (
        p16["entry_requires"]
    )
    assert (
        "operator-configured availability critical-path and economic "
        "recomputation when API mode is enabled"
    ) in p16["outputs"]
    assert (
        "operator-configured changed-route incremental benchmarks when API mode is enabled"
        in p16["outputs"]
    )
    rules = blueprint["role_control_rules"]
    assert rules["chatgpt_codex_subscription_is_daily_default_route"] is True
    assert rules["every_large_model_api_is_default_disabled"] is True
    assert rules["api_key_presence_grants_call_authority"] is False
    assert rules["one_enabled_usable_api_smoke_satisfies_backup_path_proof"] is True
    assert rules["api_backup_live_smoke_is_independent_of_p15_and_p16_core_acceptance"] is True
    assert rules["optional_api_plugin_may_be_completed_after_core_product"] is True
    assert rules["simultaneous_multi_provider_availability_required_for_completion"] is False


def test_p14f_and_p14h_freeze_bounded_terminal_semantics_without_new_stage() -> None:
    p14 = load_yaml_file(BLUEPRINT)["milestones"][
        "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
    ]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert list(stages) == [
        "P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION",
        "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT",
        "P14MR_MILESTONE_MODULE_INVARIANT",
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION",
        "P14D_REPOSITORY_CONTEXT_NATURAL_OWNER",
        "P14E_BLUEPRINT_COMPILER",
        "P14F_AUTONOMOUS_PATCH_TEST_REPAIR_REVIEW",
        "P14G_DURABLE_LOCAL_GIT_ORCHESTRATION",
        "P14H_MULTI_STACK_END_TO_END_FIXTURE_ACCEPTANCE",
        "P14I_ACCEPTANCE_CLOSURE",
    ]
    closure = stages["P14F_AUTONOMOUS_PATCH_TEST_REPAIR_REVIEW"][
        "closure_contract"
    ]
    assert set(closure["frozen_before_execution"]) == {
        "task_digest",
        "baseline_tree",
        "allowed_scope",
        "acceptance_set",
        "validation_set",
        "terminal_predicate",
        "finite_repair_review_time_and_cost_budgets",
    }
    assert closure["excluded_from_frozen_contract"] == ["candidate_tree"]
    assert "candidate_tree" in closure["per_cycle_state"]
    assert "satisfied_acceptance_items" in closure["per_cycle_state"]
    assert "attempt_number" in closure["per_cycle_state"]
    assert "attempt_number" not in closure["recurrence_fingerprint"]
    assert "attempt_number" in closure["recurrence_fingerprint_excludes"]
    assert closure["no_progress_window_completed_cycles"] == 2
    assert closure["terminal_candidate_sealed_only_after_predicate"] is True
    assert closure["explicit_user_authorization_may_reopen_sealed_candidate"] is True
    assert closure["evidence_may_reopen_only_on_original_acceptance_violation"] is True
    assert closure["system_may_invent_milestones_acceptance_authority_or_endpoints"] is False
    assert set(
        stages["P14H_MULTI_STACK_END_TO_END_FIXTURE_ACCEPTANCE"][
            "required_acceptance_scenarios"
        ]
    ) >= {
        "stale_status_text_converges_within_finite_cycles_after_source_passes",
        "stale_pull_request_metadata_does_not_reopen_accepted_source",
        "repeated_recurrence_fingerprint_stops_automatically",
        "suggestion_outside_frozen_acceptance_is_non_blocking",
        "receipt_cannot_generate_a_new_acceptance_obligation",
        "crash_recovery_does_not_duplicate_task_branch_commit_or_pull_request",
        "system_does_not_invent_a_milestone",
    }


def test_public_contracts_and_p14r_manifest_reference_global_objective() -> None:
    readme = README.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    manifest = load_yaml_file(P14R_MANIFEST)

    assert "permanent product objective" in readme
    assert "machine-readable target-state blueprint" in readme
    assert "docs/tool_system_project_state_v1.yaml" in readme
    assert "permanent product objective" in agents
    assert "product_objective" in agents
    assert manifest["alignment"]["global"] == {
        "document": "blueprint/tool_system_v0.yaml",
        "section_or_key": "product_objective",
        "scope": (
            "Make bounded blueprint-to-code autonomous development the permanent "
            "global objective controlling P14-P16."
        ),
    }
    assert set(manifest["scope"]["out_of_scope"]) >= {
        "policy or runtime source changes",
        "P14 phase entry or implementation",
    }
