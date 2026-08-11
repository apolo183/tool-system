from __future__ import annotations

import re
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
P14C_ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "p14c_bounded_real_provider_acceptance.md"
)
P14D_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p14d_repository_context_natural_owner_acceptance.md"
)
P14E_ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "p14e_blueprint_compiler_acceptance.md"
)
P14F_ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "p14f_development_loop_acceptance.md"
)
P14F_CANCELLATION_REPORT = (
    ROOT / "docs" / "reports" / "p14f_cancellation_correction_acceptance.md"
)
P14G_TOPOLOGY_REPORT = (
    ROOT / "docs" / "reports" / "p14g_file_topology_correction_acceptance.md"
)
P14H_ACCEPTANCE_REPORT = (
    ROOT / "docs" / "reports" / "p14h_multi_stack_fixture_acceptance.md"
)
P14I_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p14i_blueprint_to_code_acceptance_closure.md"
)
P14I_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14i_acceptance_closure_v1.yaml"
)
P14I_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14i_acceptance_closure_v1.yaml"
)
P14I_FILES = {
    "docs/reports/p14i_blueprint_to_code_acceptance_closure.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p14i_acceptance_closure_v1.yaml",
    "examples/task_manifests/tool_system_p14i_acceptance_closure_v1.yaml",
    "tests/test_p14_phase_entry_contract.py",
    "tests/test_phase_alignment.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_repository_context_builder.py",
}
P15A_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p15a_provider_portfolio_qualification_specification.md"
)
P15A_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15a_phase_entry_qualification_spec_v1.yaml"
)
P15A_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15a_phase_entry_qualification_spec_v1.yaml"
)
P15A_FILES = {
    "docs/reports/p15a_provider_portfolio_qualification_specification.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15a_phase_entry_qualification_spec_v1.yaml",
    "examples/task_manifests/tool_system_p15a_phase_entry_qualification_spec_v1.yaml",
    "tests/test_p14_phase_entry_contract.py",
    "tests/test_phase_alignment.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_repository_context_builder.py",
}
P15B_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p15b_adapter_router_profiler_fixture_acceptance.md"
)
P15B_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15b_adapter_router_profiler_fixtures_v1.yaml"
)
P15B_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15b_adapter_router_profiler_fixtures_v1.yaml"
)
P15B_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/p15b_adapter_router_profiler_fixture_acceptance.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15b_adapter_router_profiler_fixtures_v1.yaml",
    "examples/task_manifests/tool_system_p15b_adapter_router_profiler_fixtures_v1.yaml",
    "src/tool_system/provider_portfolio/__init__.py",
    "src/tool_system/provider_portfolio/fixtures.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_module_contracts.py",
    "tests/test_module_registry.py",
    "tests/test_p14_phase_entry_contract.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_phase_alignment.py",
    "tests/test_provider_portfolio_fixtures.py",
    "tests/test_repo_manifest.py",
    "tests/test_repository_context_builder.py",
}
P16I_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p16i_production_operations_acceptance_decision.md"
)
P16_FINAL_ACCEPTANCE_MAPPING = (
    ROOT / "docs" / "reports" / "p16_final_acceptance_mapping_v1.yaml"
)
P16I_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p16i_production_operations_acceptance_decision_v1.yaml"
)
P16I_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p16i_production_operations_acceptance_decision_v1.yaml"
)
P16I_FILES = {
    "docs/reports/p16_final_acceptance_mapping_v1.yaml",
    "docs/reports/p16i_production_operations_acceptance_decision.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p16i_production_operations_acceptance_decision_v1.yaml",
    "examples/task_manifests/tool_system_p16i_production_operations_acceptance_decision_v1.yaml",
    "tests/test_phase_alignment.py",
}
SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "subscription_worker_public_entry_acceptance_v1.md"
)
SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_MAPPING = (
    ROOT
    / "docs"
    / "reports"
    / "subscription_worker_public_entry_acceptance_mapping_v1.yaml"
)
SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_subscription_worker_public_entry_acceptance_v1.yaml"
)
SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_subscription_worker_public_entry_acceptance_v1.yaml"
)
SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES = {
    "docs/reports/subscription_worker_public_entry_acceptance_mapping_v1.yaml",
    "docs/reports/subscription_worker_public_entry_acceptance_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_subscription_worker_public_entry_acceptance_v1.yaml",
    "examples/task_manifests/tool_system_subscription_worker_public_entry_acceptance_v1.yaml",
    "tests/test_phase_alignment.py",
}
SUBSCRIPTION_DURABLE_CORRECTION_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "subscription_worker_durable_call_lease_correction_v1.md"
)
SUBSCRIPTION_DURABLE_CORRECTION_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_subscription_worker_durable_call_lease_correction_v1.yaml"
)
SUBSCRIPTION_DURABLE_CORRECTION_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_subscription_worker_durable_call_lease_correction_v1.yaml"
)
SUBSCRIPTION_DURABLE_CORRECTION_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/development-loop-contract-v1.md",
    "docs/modules/durable-orchestrator-contract-v1.md",
    "docs/modules/local-git-contract-v1.md",
    "docs/modules/task-runner-contract-v1.md",
    "docs/modules/worker-adapter-contract-v1.md",
    "docs/reports/subscription_worker_durable_call_lease_correction_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_subscription_worker_durable_call_lease_correction_v1.yaml",
    "examples/task_manifests/tool_system_subscription_worker_durable_call_lease_correction_v1.yaml",
    "src/tool_system/development_loop/loop.py",
    "src/tool_system/local_git/orchestrator.py",
    "src/tool_system/orchestrator/durable.py",
    "src/tool_system/runner/task_runner.py",
    "src/tool_system/worker_adapter/contract.py",
    "src/tool_system/worker_adapter/orchestration.py",
    "tests/test_durable_orchestrator_side_effects.py",
    "tests/test_durable_orchestrator_recovery.py",
    "tests/test_durable_orchestrator_reliability.py",
    "tests/test_durable_orchestrator_state.py",
    "tests/test_module_registry.py",
    "tests/test_phase_alignment.py",
    "tests/test_task_runner.py",
    "tests/test_worker_adapter_contract.py",
    "tests/test_worker_adapter_orchestration.py",
}
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
REPO_WRITE_POLICY = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy" / "autonomy_policy.yaml"
CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14mr_milestone_module_invariant.yaml"
)
BOUNDED_CLOSURE_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_bounded_closure_no_progress_contract_v1.yaml"
)
BOUNDED_CLOSURE_CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_bounded_closure_no_progress_contract_v1.yaml"
)
BOUNDED_CLOSURE_FILES = {
    "docs/tool_system_global_development_principles_v1.md",
    "blueprint/tool_system_v0.yaml",
    "tests/test_phase_alignment.py",
    "tests/test_product_objective_alignment.py",
    "tests/test_repo_manifest.py",
    "examples/task_manifests/tool_system_bounded_closure_no_progress_contract_v1.yaml",
    "examples/change_plans/tool_system_bounded_closure_no_progress_contract_v1.yaml",
}
P14_PHASE = "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
P15_PHASE = "P15_MULTI_PROJECT_BENCHMARK"
EXPECTED_PHASE = "P16_PRODUCTION_OPERATIONS_ACCEPTANCE"
TRANSIENT_RULE_OWNER_PATTERNS = {
    "pull-request receipt": r"\bPR\s+#\d+\b",
    "main commit receipt": r"\bmain@[0-9a-f]{40}\b",
    "P14C authorization receipt": r"\bP14C-[A-Z0-9-]+-v\d+\b",
    "completed caller audit": r"\bcurrent-task caller audit is complete\b",
    "current P14 status": r"\bP14 remains active\b",
    "last accepted stage": r"\bP14MR remains the last accepted stage\b",
}


def test_blueprint_and_descriptive_project_state_have_separate_roles() -> None:
    agents_text = AGENTS.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")
    principles_text = PRINCIPLES.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)

    assert project_state["current_phase"] == {
        "id": EXPECTED_PHASE,
        "status": "accepted",
        "entry_record": "docs/reports/default_subscription_mainline_optional_api_plugin_realignment.md",
        "entry_authorized": True,
        "last_accepted_stage": EXPECTED_PHASE,
        "last_accepted_stage_record": (
            "docs/reports/p16i_production_operations_acceptance_decision.md"
        ),
        "next_stage": None,
        "next_stage_authorized": False,
        "active_stage": None,
        "active_stage_status": (
            "accepted_subscription_primary_sustainable_operations_core"
        ),
        "next_phase": None,
        "next_phase_entry_authorized": False,
    }
    assert project_state["authority_effect"] == "none"
    assert EXPECTED_PHASE in blueprint["milestones"]
    assert {
        "phase",
        "status",
        "acceptance",
        "successor_authorization",
        "active_phase_execution",
        "p14c_source_implementation",
    }.isdisjoint(blueprint)
    assert project_state["prior_acceptance"]["phase"] == P14_PHASE
    assert project_state["prior_acceptance"]["record"] == (
        "docs/reports/p14i_blueprint_to_code_acceptance_closure.md"
    )
    assert project_state["prior_acceptance"]["accepted_scope"] == (
        "approved_bounded_blueprint_isolated_repository_fixture_auditable_"
        "resumable_fail_closed_local_git_workflow"
    )
    assert project_state["prior_acceptance"]["predecessor"]["phase"] == (
        "P13_SECURITY_RELIABILITY_HARDENING"
    )
    p14c = project_state["p14c"]
    assert p14c["implementation_authorization_packet"] == "P14C-IMPL-v2"
    assert p14c["source_status"] == "bounded_deepseek_live_provider_proof_accepted"
    assert p14c["acceptance_record"] == (
        "docs/reports/p14c_bounded_real_provider_acceptance.md"
    )
    assert p14c["acceptance_authorization_packet"] == (
        "P14C-DEEPSEEK-RESULT-ACCEPTANCE-v1"
    )
    assert p14c["acceptance_status"] == "accepted"
    assert (
        p14c["live_issuer_implementation_authorization_packet"]
        == "P14C-LIVE-ISSUER-IMPL-v1"
    )
    assert (
        p14c["live_issuer_lifecycle_authorization_packet"]
        == "P14C-LIVE-ISSUER-LIFECYCLE-v1"
    )
    assert p14c["live_issuer_source"]["pull_request"] == 148
    assert p14c["live_issuer_source"]["merge"] == (
        "20cbb13feb934ce95f2624dafc4510efcd04f1da"
    )
    assert p14c["live_issuer_source"]["publication_status"] == (
        "merged_hosted_ci_validated"
    )
    assert p14c["live_issuer_source"]["branch_retained"] is True
    assert p14c["source_hardening_authorization_packet"] == (
        "P14C-SOURCE-SEAL-REPLAY-LIFECYCLE-v1"
    )
    assert p14c["execution_source_seal_required"] is True
    assert p14c["durable_replay_boundary"] == (
        "single_host_sqlite_burn_on_claim_at_most_once"
    )
    assert p14c["multi_host_exactly_once_claimed"] is False
    assert p14c["real_live_approval_record_created"] is True
    assert p14c["live_capability_issued"] is True
    assert p14c["first_live_attempt"]["approval_durably_consumed"] is True
    assert p14c["first_live_attempt"]["redacted_error_code"] == (
        "PROVIDER_FAILURE"
    )
    assert p14c["prior_recovery_implementation_packet"] == (
        "P14C-QWEN-RECOVERY-v1"
    )
    prior_recovery = p14c["prior_recovery_attempt"]
    assert prior_recovery["live_execution_attempted"] is True
    assert prior_recovery["live_execution_succeeded"] is False
    assert prior_recovery["approval_comment_id"] == 5_156_628_612
    assert prior_recovery["approval_durably_consumed"] is True
    assert prior_recovery["provider_invocation_count"] == 1
    assert prior_recovery["redacted_failure_class"] == "AUTH_FAILED"
    assert prior_recovery["failure_detail"] == (
        "ambiguous_http_401_or_403_under_legacy_classifier"
    )
    assert prior_recovery["credential_value_recorded"] is False
    assert prior_recovery["acceptance_effect"] == "none"
    assert p14c["recovery_implementation_packet"] == (
        "P14C-DEEPSEEK-RECOVERY-v1"
    )
    recovery = p14c["recovery_route"]
    assert recovery["provider_id"] == "deepseek"
    assert recovery["model_id"] == "deepseek-v4-flash"
    assert recovery["live_execution_attempted"] is True
    assert recovery["live_execution_succeeded"] is True
    assert recovery["approval_comment_id"] == 5_158_008_082
    assert recovery["approval_durably_consumed"] is True
    assert recovery["credential_resolution_attempt_count"] == 1
    assert recovery["provider_invocation_count"] == 1
    assert recovery["transport_attempt_ceiling"] == 1
    assert recovery["usage"]["total_tokens"] == 145
    assert recovery["usage"]["cost_microunits"] == 184
    assert recovery["usage"]["duration_ms"] == 1770
    assert recovery["source_seal"]["execution_commit_sha"] == (
        "55ed92e336d2aa110e50e197c5eefb8fa80896a8"
    )
    assert recovery["source_seal"]["execution_tree_sha"] == (
        "2e6ce267738a396f52a5847052f91edafea74af9"
    )
    assert recovery["credential_value_recorded"] is False
    assert recovery["raw_provider_output_recorded"] is False
    assert recovery["acceptance_effect"] == (
        "p14c_bounded_real_model_provider_execution_accepted"
    )
    assert p14c["stage_accepted"] is True
    p14d = project_state["p14d"]
    assert p14d["implementation_authorization_packet"] == (
        "P14D-REPOSITORY-CONTEXT-LIFECYCLE-v1"
    )
    assert p14d["module_id"] == "repository-context"
    assert p14d["module_version"] == "1.0.0"
    assert p14d["public_interface_id"] == "repository-context-api"
    assert p14d["acceptance_record"] == (
        "docs/reports/p14d_repository_context_natural_owner_acceptance.md"
    )
    assert p14d["acceptance_status"] == "accepted"
    assert p14d["evidence_boundary"] == (
        "isolated_local_git_fixture_repositories_only"
    )
    assert p14d["natural_owner_proposal_grants_authority"] is False
    assert p14d["real_downstream_repository_accessed"] is False
    assert p14d["stage_accepted"] is True
    p14e = project_state["p14e"]
    assert p14e["implementation_authorization_packet"] == (
        "P14E-BLUEPRINT-COMPILER-LIFECYCLE-v1"
    )
    assert p14e["module_id"] == "blueprint-compiler"
    assert p14e["module_version"] == "1.0.0"
    assert p14e["public_interface_id"] == "blueprint-compiler-api"
    assert p14e["acceptance_status"] == "accepted"
    assert p14e["compilation_contract"]["authority_effect"] == "none"
    assert p14e["generated_documents_grant_authority"] is False
    assert p14e["real_downstream_repository_accessed"] is False
    assert p14e["stage_accepted"] is True
    p14f = project_state["p14f"]
    assert p14f["module_version"] == "1.1.0"
    assert p14f["public_interface_version"] == "1.1.0"
    assert p14f["accepted_fixture_evidence"][
        "caller_cancellation_before_worker_dispatch"
    ] is True
    assert p14f["accepted_fixture_evidence"][
        "caller_cancellation_before_patch_application"
    ] is True
    assert p14f["accepted_fixture_evidence"][
        "cancelled_worker_patch_discarded"
    ] is True
    assert p14f["cancellation_correction"]["authority_effect"] == "none"
    p14g = project_state["p14g"]
    assert p14g["module_version"] == "1.1.0"
    assert p14g["public_interface_version"] == "1.1.0"
    assert p14g["accepted_fixture_evidence"][
        "exact_baseline_presence_and_content_topology"
    ] is True
    assert p14g["accepted_fixture_evidence"][
        "add_modify_delete_delta_in_one_commit"
    ] is True
    assert p14g["accepted_fixture_evidence"][
        "staged_paths_equal_actual_changed_subset"
    ] is True
    assert p14g["file_topology_correction"]["authority_effect"] == "none"
    p14h = project_state["p14h"]
    assert p14h["implementation_authorization_packet"] == (
        "P14H-MULTI-STACK-FIXTURE-LIFECYCLE-v1"
    )
    assert p14h["acceptance_status"] == "accepted"
    assert p14h["evidence_boundary"] == (
        "isolated_python_and_typescript_fixture_repositories_only"
    )
    assert all(
        p14h["accepted_fixture_evidence"][key] is True
        for key in (
            "greenfield_python_cli",
            "existing_python_library_natural_owner_change",
            "typescript_package_language_neutral_flow",
            "bounded_failing_test_repair",
            "ambiguous_blueprint_pre_mutation_block",
            "out_of_scope_patch_block_and_rollback",
            "timeout_cancellation_cleanup_and_resume",
            "completed_side_effect_crash_without_duplicate_replay",
            "local_git_conflict_policy",
            "deterministic_content_addressed_replay",
            "system_does_not_invent_milestones",
        )
    )
    assert p14h["stage_accepted"] is True
    p14i = project_state["p14i"]
    assert p14i["authorization_packet"] == (
        "P14I-ACCEPTANCE-CLOSURE-LIFECYCLE-v1"
    )
    assert p14i["acceptance_status"] == "accepted_and_closed"
    assert p14i["baseline_commit"] == (
        "cf1b8344695ab6e325cdb6c3cdd6b69037b2d657"
    )
    assert len(p14i["evidence_chain_read_only_revalidated"]) == 9
    assert p14i["product_wide_completion_claimed"] is False
    assert p14i["p15_entry_authorized"] is False
    assert all(
        p14i[key] == 0
        for key in (
            "runtime_source_changes",
            "blueprint_changes",
            "provider_invocations",
            "credential_value_accesses",
            "downstream_repository_accesses",
            "remote_fixture_operations",
            "production_operations",
            "cleanup_operations",
            "rollback_operations",
        )
    )
    assert p14i["stage_accepted"] is True
    p15a = project_state["p15a"]
    assert p15a["authorization_packet"] == (
        "P15A-PHASE-ENTRY-AND-QUALIFICATION-SPECIFICATION-LIFECYCLE-v1"
    )
    assert p15a["baseline_commit"] == (
        "e3b02654edbe69850d0f801adb77a083c444b2d3"
    )
    assert p15a["baseline_tree"] == (
        "ef8de13cce5ce55b713ba8a083196142f6504ccd"
    )
    assert p15a["specification_status"] == "accepted_governance_only"
    assert p15a["provider_neutral_interface_lock"] == {
        "protocol_path": "src/tool_system/ai_worker/contract.py",
        "protocol_symbol": "AIWorkerProvider",
        "aggregate_interface_id": "ai-worker-runtime-api",
        "aggregate_interface_version": "1.0.0",
        "selection_contract_path": (
            "docs/model_provider_portfolio_and_economics_contract_v1.md"
        ),
        "selection_module_id": "adaptive_model_portfolio_and_economics",
        "selection_public_interface_version": 1,
    }
    assert set(p15a["task_profile_required_fields"]) == {
        "task_class_language_repository_context_and_dependency_breadth",
        "reasoning_and_implementation_complexity",
        "independent_security_data_repository_mutation_and_operational_risk",
        "required_capabilities_and_minimum_quality_confidence_floor",
        "verification_and_repair_burden",
        "critical_path_slack_and_delay_sensitivity",
        "evidence_confidence_and_uncertainty_reasons",
    }
    assert set(p15a["hard_floor_categories"]) == {
        "authorization_and_execution_surface",
        "data_policy_residency_retention_and_sensitivity",
        "exact_model_capability_context_and_output_limits",
        "independent_security_quality_and_risk",
        "time_token_cost_retry_cancellation_and_no_progress_limits",
        "current_catalog_policy_benchmark_health_and_precondition_evidence",
        "repository_access_and_mutation_authority",
    }
    assert p15a["economics_objective"] == (
        "expected_total_economic_cost_per_accepted_module"
    )
    assert p15a["private_economic_values_publicly_recorded"] is False
    assert p15a["qualification_states"] == [
        "DISCOVERED",
        "QUARANTINED",
        "BENCHMARKING",
        "SHADOW",
        "CANARY",
        "ELIGIBLE",
        "PRIMARY",
        "DEGRADED",
        "RETIRED",
    ]
    assert p15a["benchmark_corpus_seed_boundary"] == (
        "accepted_p14_isolated_python_and_typescript_fixtures_as_"
        "specification_inputs_only"
    )
    assert p15a["benchmark_results_created"] == 0
    assert p15a["provider_candidates_enabled"] == 0
    assert p15a["provider_adapters_added_or_modified"] == 0
    assert p15a["credential_reference_metadata_inspected"] is True
    assert all(
        p15a[key] == 0
        for key in (
            "credential_resolver_invocations",
            "credential_value_accesses",
            "provider_invocations",
            "network_operations",
            "real_downstream_repository_accesses",
            "target_mutations",
            "production_operations",
            "cleanup_operations",
            "rollback_operations",
            "blueprint_changes",
            "runtime_source_changes",
        )
    )
    assert p15a["p15b_authorized"] is False
    assert p15a["stage_accepted"] is True
    p15b = project_state["p15b"]
    assert p15b["authorization_packet"] == (
        "P15B-ADAPTER-ROUTER-AND-PROFILER-FIXTURES-LIFECYCLE-v1"
    )
    assert p15b["baseline_commit"] == (
        "f912add44845be9d60021333c6792e4ecf6a142b"
    )
    assert p15b["baseline_tree"] == (
        "493c5563cf4d95b1cc3e236e1453c8c9db5e3423"
    )
    assert p15b["implementation_status"] == (
        "accepted_isolated_fixture_no_live_provider"
    )
    assert p15b["module"] == {
        "current_module_id": "adaptive_model_portfolio_and_economics",
        "canonical_module_id": "adaptive-model-portfolio-and-economics",
        "module_version": "1.0.0",
        "aggregate_interface_id": "adaptive-model-portfolio-and-economics-api",
        "aggregate_interface_version": "1.0.0",
        "upstream_interface_id": "ai-worker-runtime-api",
        "upstream_interface_version": "1.0.0",
        "natural_owner_paths": [
            "src/tool_system/provider_portfolio/__init__.py",
            "src/tool_system/provider_portfolio/fixtures.py",
        ],
    }
    assert p15b["task_profile_builder"] == "build_task_profile_fixture"
    assert p15b["routing_policy_version"] == "p15b-fixture-routing-policy-v1"
    assert p15b["catalog_fixture_version"] == "p15b-fixture-catalog-v1"
    assert p15b["hard_floors_evaluated_before_economics"] is True
    assert p15b["economics_arithmetic"] == (
        "non_negative_integer_microunits_without_float_scoring"
    )
    assert p15b["selectable_qualification_states"] == ["ELIGIBLE", "PRIMARY"]
    assert p15b["failure_dispositions"] == [
        "AVAILABILITY_FAILOVER",
        "SAME_ROUTE_REPAIR_THEN_ESCALATE",
        "BLOCK_NO_PROVIDER_BYPASS",
        "STOP",
    ]
    assert p15b["fixture_adapter"] == {
        "protocol_path": "src/tool_system/ai_worker/contract.py",
        "protocol_symbol": "AIWorkerProvider",
        "provider_kind": "deterministic_fixture",
        "execution_mode": "fixture",
        "structural_compatibility_tested": True,
        "calls_external_provider": False,
        "uses_credentials": False,
        "network_access": False,
    }
    assert p15b["module_source_files_added"] == 2
    assert p15b["existing_ai_worker_source_changes"] == 0
    assert p15b["p15c_authorized"] is False
    assert p15b["stage_accepted"] is True
    assert all(
        p15b[key] == 0
        for key in (
            "live_provider_adapters_added_or_modified",
            "provider_candidates_enabled_for_live_execution",
            "benchmark_results_created",
            "benchmark_executions",
            "provider_invocations",
            "provider_network_operations",
            "credential_resolver_invocations",
            "credential_value_accesses",
            "real_downstream_repository_accesses",
            "remote_fixture_operations",
            "target_mutations",
            "production_operations",
            "cleanup_operations",
            "rollback_operations",
            "blueprint_changes",
        )
    )
    boundaries = project_state["authorization_boundaries"]
    assert boundaries["state_file_grants_authority"] is False
    assert boundaries["live_model_provider_execution_authorized"] is True
    assert boundaries["credential_value_access_authorized"] is True
    assert boundaries["downstream_repository_access_authorized"] is True
    assert boundaries["remote_target_mutation_authorized"] is False
    assert boundaries["production_deployment_authorized"] is False
    assert boundaries["cleanup_execution_authorized"] is False
    assert boundaries["rollback_execution_authorized"] is False
    assert "P14C_ACCEPTED_BOUNDED_DEEPSEEK_PROOF" in (
        P14C_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    )
    assert "P14D_ACCEPTED_ISOLATED_FIXTURE_ONLY" in (
        P14D_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    )
    assert "P14E_ACCEPTED_ISOLATED_FIXTURE_ONLY" in (
        P14E_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    )
    assert "P14F_ACCEPTED_ISOLATED_FIXTURE_ONLY" in (
        P14F_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    )
    assert "P14F_CANCELLATION_CORRECTION_ACCEPTED_FIXTURE_ONLY" in (
        P14F_CANCELLATION_REPORT.read_text(encoding="utf-8")
    )
    assert "P14G_FILE_TOPOLOGY_CORRECTION_ACCEPTED_FIXTURE_ONLY" in (
        P14G_TOPOLOGY_REPORT.read_text(encoding="utf-8")
    )
    assert "P14H_ACCEPTED_ISOLATED_MULTI_STACK_FIXTURES_ONLY" in (
        P14H_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    )
    p14i_report = P14I_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    normalized_p14i_report = " ".join(p14i_report.split())
    assert "P14_ACCEPTED_AND_CLOSED_BOUNDED_ISOLATED_FIXTURE_SCOPE" in p14i_report
    assert "P15_entry_authorized: false" in p14i_report
    assert "product-wide P15 or P16 conditions" in normalized_p14i_report
    p15a_report = P15A_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    normalized_p15a_report = " ".join(p15a_report.split())
    assert "P15A_ACCEPTED_GOVERNANCE_ONLY_QUALIFICATION_SPECIFICATION" in (
        p15a_report
    )
    assert "Locked provider/model qualification record" in p15a_report
    assert "expected_total_economic_cost_per_accepted_module" in p15a_report
    assert "P15B remains separately unauthorized" in normalized_p15a_report
    p15b_report = P15B_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    assert "P15B_ACCEPTED_ISOLATED_FIXTURE_NO_LIVE_PROVIDER" in p15b_report
    assert "hard-floor order" in p15b_report
    assert "P15C_authorized: false" in p15b_report
    for public_contract in (agents_text, readme_text, principles_text):
        assert "docs/tool_system_project_state_v1.yaml" in public_contract
        assert "authority" in public_contract


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_p14i_manifest_and_change_plan_freeze_exact_governance_scope() -> None:
    manifest_result = validate_task_manifest(
        P14I_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P14I_CHANGE_PLAN)
    manifest = load_yaml_file(P14I_MANIFEST)
    plan = load_yaml_file(P14I_CHANGE_PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P14I_FILES
    assert set(plan["changed_files"]) == P14I_FILES
    assert manifest["bounded_closure"]["frozen_before_execution"][
        "baseline_commit"
    ] == "cf1b8344695ab6e325cdb6c3cdd6b69037b2d657"
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False
    assert all(not path.startswith("src/") for path in P14I_FILES)
    assert "blueprint/tool_system_v0.yaml" not in P14I_FILES


def test_p14i_closes_only_bounded_p14_and_stops_before_p15() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)
    report = P14I_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    p14 = blueprint["milestones"][P14_PHASE]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert stages["P14I_ACCEPTANCE_CLOSURE"]["execution_boundary"] == (
        "governance_only"
    )
    assert "isolated repository fixture" in p14["accepted_claim"]
    assert "local Git software change" in p14["accepted_claim"]
    assert project_state["prior_acceptance"]["phase"] == P14_PHASE
    assert project_state["p14i"]["p15_entry_authorized"] is False
    assert project_state["current_phase"]["id"] == EXPECTED_PHASE
    for marker in (
        "P14 output acceptance matrix",
        "Required P14 fixture matrix",
        "Global product-objective disposition",
        "provider_invocations: 0",
        "runtime_source_changes: 0",
        "P15_entry_authorized: false",
    ):
        assert marker in report


def test_p15a_manifest_and_change_plan_freeze_exact_governance_scope() -> None:
    manifest_result = validate_task_manifest(
        P15A_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P15A_CHANGE_PLAN)
    manifest = load_yaml_file(P15A_MANIFEST)
    plan = load_yaml_file(P15A_CHANGE_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P15A_FILES
    assert set(manifest["scope"]["in_scope"]) == P15A_FILES
    assert set(plan["changed_files"]) == P15A_FILES
    assert closure["baseline_commit"] == (
        "e3b02654edbe69850d0f801adb77a083c444b2d3"
    )
    assert closure["baseline_tree"] == (
        "ef8de13cce5ce55b713ba8a083196142f6504ccd"
    )
    assert closure["allowed_scope"] == "exact_10_paths_listed_below"
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["benchmark_executions"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["real_downstream_repository_accesses"] == 0
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False
    assert all(not path.startswith("src/") for path in P15A_FILES)
    assert "blueprint/tool_system_v0.yaml" not in P15A_FILES
    assert "docs/model_provider_portfolio_and_economics_contract_v1.md" not in (
        P15A_FILES
    )


def test_p15a_specification_remains_the_direct_parent_of_p15b() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)
    report = P15A_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    p15 = blueprint["milestones"][P15_PHASE]
    stages = {stage["stage"]: stage for stage in p15["stage_plan"]}

    assert "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT accepted" in (
        p15["entry_requires"]
    )
    assert "explicit P15 phase-entry authorization" in p15["entry_requires"]
    assert stages["P15A_PROVIDER_PORTFOLIO_QUALIFICATION_SPECIFICATION"][
        "execution_boundary"
    ] == "governance_only"
    assert project_state["current_phase"]["id"] == EXPECTED_PHASE
    assert project_state["p15a"]["p15b_authorized"] is False
    for marker in (
        "Read-only existing-surface inventory",
        "Locked task profile",
        "Locked hard floors and decision order",
        "Locked economics contract",
        "Locked benchmark corpus and metrics",
        "Credential-reference and evidence boundary",
        "provider_invocations: 0",
        "benchmark_executions: 0",
        "P15B_authorized: false",
    ):
        assert marker in report


def test_p15b_manifest_and_change_plan_freeze_exact_one_module_scope() -> None:
    manifest_result = validate_task_manifest(
        P15B_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P15B_CHANGE_PLAN)
    manifest = load_yaml_file(P15B_MANIFEST)
    plan = load_yaml_file(P15B_CHANGE_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P15B_FILES
    assert set(manifest["scope"]["in_scope"]) == P15B_FILES
    assert set(plan["changed_files"]) == P15B_FILES
    assert len(P15B_FILES) == 21
    assert closure["task_identity"] == (
        "P15B-ADAPTER-ROUTER-AND-PROFILER-FIXTURES-LIFECYCLE-v1"
    )
    assert closure["baseline_commit"] == (
        "f912add44845be9d60021333c6792e4ecf6a142b"
    )
    assert closure["baseline_tree"] == (
        "493c5563cf4d95b1cc3e236e1453c8c9db5e3423"
    )
    assert closure["allowed_scope"] == "exact_21_paths_listed_below"
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["benchmark_executions"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["real_downstream_repository_accesses"] == 0
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False
    assert "blueprint/tool_system_v0.yaml" not in P15B_FILES
    assert "docs/model_provider_portfolio_and_economics_contract_v1.md" not in (
        P15B_FILES
    )
    assert {
        "src/tool_system/provider_portfolio/__init__.py",
        "src/tool_system/provider_portfolio/fixtures.py",
    } <= P15B_FILES
    assert all(
        not path.startswith("src/tool_system/ai_worker/") for path in P15B_FILES
    )


def test_p15b_accepts_only_isolated_fixtures_and_stops_before_p15c() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    project_state = load_yaml_file(PROJECT_STATE)
    report = P15B_ACCEPTANCE_REPORT.read_text(encoding="utf-8")
    p15 = blueprint["milestones"][P15_PHASE]
    stages = {stage["stage"]: stage for stage in p15["stage_plan"]}

    assert stages["P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES"][
        "entry_requires"
    ] == ["P15A_PROVIDER_PORTFOLIO_QUALIFICATION_SPECIFICATION accepted"]
    assert stages["P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES"][
        "execution_boundary"
    ] == "isolated_fixture_no_live_provider"
    assert stages["P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK"][
        "execution_boundary"
    ] == (
        "fake_io_all_adapters_no_live_provider_no_target_access"
    )
    assert project_state["p15b"]["p15c_authorized"] is False
    for marker in (
        "Advisory task-profile fixture",
        "Catalog, hard floors, and deterministic routing",
        "Provider-neutral fixture adapter",
        "Failure-classification fixture",
        "provider_invocations: 0",
        "credential_value_accesses: 0",
        "P15C_authorized: false",
    ):
        assert marker in report


def test_bounded_closure_manifest_and_change_plan_validate_exact_scope() -> None:
    manifest_result = validate_task_manifest(
        BOUNDED_CLOSURE_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(BOUNDED_CLOSURE_CHANGE_PLAN)
    manifest = load_yaml_file(BOUNDED_CLOSURE_MANIFEST)
    plan = load_yaml_file(BOUNDED_CLOSURE_CHANGE_PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == BOUNDED_CLOSURE_FILES
    assert set(plan["changed_files"]) == BOUNDED_CLOSURE_FILES
    assert all(not path.startswith("src/") for path in plan["changed_files"])
    assert "docs/tool_system_project_state_v1.yaml" not in plan["changed_files"]


def test_stable_principles_define_finite_non_reopening_closure() -> None:
    text = " ".join(PRINCIPLES.read_text(encoding="utf-8").split())

    assert "baseline tree" in text
    assert "candidate tree is deliberately not" in text
    assert "finite repair, review, time, and cost budgets" in text
    assert "satisfied acceptance items" in text
    assert "recurrence fingerprint uses only the task digest" in text
    assert "excludes the attempt number" in text
    assert "two consecutive completed cycles make no progress" in text
    assert "cannot reopen a successfully sealed candidate" in text
    assert "Reopening requires explicit user authorization" in text
    assert "may not invent a new milestone" in text


def test_stable_rule_owners_delegate_transient_progress_to_project_state() -> None:
    for owner in (AGENTS, PRINCIPLES):
        text = owner.read_text(encoding="utf-8")

        assert "docs/tool_system_project_state_v1.yaml" in text
        for label, pattern in TRANSIENT_RULE_OWNER_PATTERNS.items():
            assert re.search(pattern, text, flags=re.IGNORECASE) is None, (
                f"{owner.relative_to(ROOT)} contains {label}"
            )


def test_p15_non_live_multi_project_matrix_is_isolated_and_zero_external() -> None:
    matrix = load_yaml_file(
        ROOT / "docs" / "reports" / "p15_non_live_multi_project_matrix_v1.yaml"
    )
    p14h_source = (
        ROOT / "tests" / "test_p14h_multi_stack_e2e.py"
    ).read_text(encoding="utf-8")

    assert matrix["schema_version"] == 1
    assert matrix["authority_effect"] == "none"
    assert matrix["execution_boundary"] == "isolated_committed_fixtures_only"

    projects = matrix["projects"]
    assert len(projects) == 2
    assert {project["language_stack"] for project in projects} == {
        "python",
        "typescript",
    }
    assert len({project["project_id"] for project in projects}) == len(projects)
    assert len({project["fixture_root"] for project in projects}) == len(projects)
    assert all(project["isolated_repository"] is True for project in projects)
    assert all((ROOT / project["fixture_root"]).is_dir() for project in projects)
    assert all(
        f'def {project["acceptance_test"]}(' in p14h_source
        for project in projects
    )

    assert matrix["cross_project_controls"] == {
        "unique_repository_roots_required": True,
        "unique_orchestrator_state_required": True,
        "caller_supplied_project_identity_required": True,
        "shared_candidate_tree_forbidden": True,
        "shared_branch_identity_forbidden": True,
        "downstream_repository_access_allowed": False,
    }

    cases = matrix["generalization_cases"]
    assert len(cases) == 3
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert all(
        f'def {case["acceptance_test"]}(' in p14h_source for case in cases
    )

    metrics = matrix["metrics"]
    assert metrics["quality"]["accepted_project_count"] == 2
    assert metrics["quality"]["rejected_out_of_scope_case_count"] == 1
    assert metrics["time"]["critical_path_measure"] == (
        "logical_development_cycles"
    )
    assert metrics["economics"]["unit"] == "integer_microunits"
    assert metrics["economics"]["private_value_required"] is False
    assert metrics["economics"]["double_counting_allowed"] is False
    assert set(metrics["recovery"].values()) == {1}
    assert set(metrics["policy"].values()) == {0}

    provider = matrix["provider_boundary"]
    assert provider["daily_route"] == "chatgpt_codex_subscription"
    assert provider["all_large_model_apis_default_disabled"] is True
    assert provider["provider_model_selection_source"] == (
        "repository_external_operator_configuration"
    )
    assert provider["adapter_fake_io_evidence_required"] is True
    assert provider["live_smoke_executed"] is False
    assert set(matrix["acceptance_boundary"].values()) == {False}


def test_p15_consolidated_non_live_evidence_stops_before_final_smoke() -> None:
    evidence = load_yaml_file(
        ROOT / "docs" / "reports" / "p15_non_live_consolidated_evidence_v1.yaml"
    )
    smoke = load_yaml_file(
        ROOT / "docs" / "reports" / "p15_final_smoke_control_packet_schema_v1.yaml"
    )

    assert evidence["schema_version"] == 1
    assert evidence["authority_effect"] == "none"
    assert all(
        (ROOT / source["path"]).is_file()
        and source["commit"] == "32ad304576d5e38405313fbddc0c519dd9bc8b1a"
        for source in evidence["source_snapshots"]
    )

    representative = evidence["representative_coverage"]
    assert representative["isolated_project_count"] == 2
    assert set(representative["language_stacks"]) == {"python", "typescript"}
    assert representative["cross_project_isolation_proven"] is True
    assert (
        representative["generalization_proven_within_committed_fixture_boundary"]
        is True
    )

    provider = evidence["provider_coverage"]
    assert provider["daily_route"] == "chatgpt_codex_subscription"
    assert provider["all_large_model_apis_default_disabled"] is True
    assert provider["key_presence_grants_call_authority"] is False
    assert provider["provider_model_selection_source"] == (
        "repository_external_operator_configuration"
    )
    assert set(provider["fake_io_adapter_contracts"]) == {
        "openai",
        "deepseek",
        "qwen",
    }
    assert set(provider["fake_io_adapter_contracts"].values()) == {
        "passed_in_hosted_ci"
    }
    assert provider["no_available_provider_code"] == "NO_AVAILABLE_PROVIDER"
    assert provider["single_success_stop"] is True
    assert provider["simultaneous_multi_provider_availability_required"] is False
    assert provider["named_provider_funding_required"] is False
    assert provider["moving_alias_exact_version_required"] is False

    assert set(evidence["hard_gates"].values()) == {False}
    failure = evidence["failure_and_recovery"]
    assert failure["frozen_case_count"] == 8
    assert failure["rollback_is_plan_only"] is True
    assert all(value is True for key, value in failure.items() if key != "frozen_case_count")

    metrics = evidence["metrics"]
    assert metrics["quality"] == {
        "accepted_isolated_project_count": 2,
        "rejected_out_of_scope_case_count": 1,
        "provider_fake_io_adapter_count": 3,
    }
    assert metrics["time"]["measure"] == "logical_development_and_attempt_cycles"
    assert metrics["economics"]["unit"] == "integer_microunits"
    assert metrics["economics"]["private_inputs_committed"] is False
    assert metrics["economics"]["hard_floors_precede_economics"] is True
    assert metrics["economics"]["double_counting_allowed"] is False
    assert set(metrics["policy"].values()) == {0}

    assert evidence["remaining_items"] == [
        "separately_authorized_single_provider_live_smoke_on_then_canonical_main",
        "explicit_p15_acceptance_decision_after_smoke",
    ]
    assert evidence["acceptance_boundary"] == {
        "all_non_live_p15_evidence_complete_on_guarded_merge": True,
        "p15_stage_accepted": False,
        "p16_stage_entered": False,
        "final_live_smoke_executed": False,
    }

    assert smoke["role"] == "non_authorizing_repository_template_only"
    assert smoke["authority_effect"] == "none"
    assert smoke["api_mode_enabled"] is False
    assert smoke["provider"]["enabled"] is False
    assert smoke["credential"]["value_present_in_packet"] is False
    assert smoke["credential"]["key_presence_grants_call_authority"] is False
    assert smoke["network"]["authorized"] is False
    assert smoke["budget"]["authorized"] is False
    assert smoke["budget"]["hard_ceiling_microunits"] == 0
    assert smoke["authorization"]["final_smoke_authorized"] is False
    assert (
        smoke["authorization"]["separate_current_user_authorization_required"]
        is True
    )
    assert smoke["data_transfer"]["authorized"] is False
    assert smoke["retry_and_cancellation"] == {
        "max_attempts": 1,
        "max_retries": 0,
        "cancellation_token_required": True,
    }
    assert smoke["current_state"] == {
        "executable": False,
        "live_smoke_executed": False,
        "p15_accepted": False,
        "p16_entered": False,
    }


def test_subscription_primary_core_acceptance_enters_p16_without_api_smoke() -> None:
    state = load_yaml_file(PROJECT_STATE)
    lifecycle = state["default_subscription_mainline_optional_api_plugin_realignment"]
    assert lifecycle["evidence_source"]["non_live_evidence_complete"] is True
    assert lifecycle["p15_core_acceptance"]["status"] == "accepted_subscription_primary_core"
    assert lifecycle["p15_core_acceptance"]["live_api_smoke_required"] is False
    plugin = lifecycle["optional_api_provider_plugin_v2"]
    assert plugin["status"] == "default_disabled_deferred_independent_module_backlog"
    assert plugin["project_completion_gate"] is False
    assert plugin["p16_entry_gate"] is False
    assert plugin["release_requires_one_separately_authorized_single_provider_smoke"] is True
    assert lifecycle["p16_entry"] == {
        "phase": "P16_PRODUCTION_OPERATIONS_ACCEPTANCE",
        "authorized": True,
        "entered": True,
        "production_deployment_authorized": False,
        "api_mode_required": False,
    }
    assert set(lifecycle["zero_operation_boundary"].values()) == {0}

def test_p16i_manifest_and_change_plan_freeze_exact_acceptance_scope() -> None:
    manifest_result = validate_task_manifest(
        P16I_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P16I_CHANGE_PLAN)
    manifest = load_yaml_file(P16I_MANIFEST)
    plan = load_yaml_file(P16I_CHANGE_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P16I_FILES
    assert set(manifest["scope"]["in_scope"]) == P16I_FILES
    assert set(plan["changed_files"]) == P16I_FILES
    assert len(P16I_FILES) == 6
    assert closure["baseline_commit"] == (
        "02699469bf96024bb481980712d47494a4ef08ff"
    )
    assert closure["allowed_scope"] == "exact_6_paths_listed_below"
    assert set(closure["finite_budgets"].values()) <= {0, 1, 3}
    assert closure["finite_budgets"]["provider_invocations"] == 0
    assert closure["finite_budgets"]["credential_value_accesses"] == 0
    assert closure["finite_budgets"]["deployment_operations"] == 0
    assert closure["finite_budgets"]["production_operations"] == 0
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False
    assert all(not path.startswith("src/") for path in P16I_FILES)
    assert "blueprint/tool_system_v0.yaml" not in P16I_FILES
    assert "REPO_MANIFEST.md" not in P16I_FILES


def test_p16i_maps_all_blueprint_outputs_without_api_gating() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    mapping = load_yaml_file(P16_FINAL_ACCEPTANCE_MAPPING)
    outputs = blueprint["milestones"][EXPECTED_PHASE]["outputs"]
    rows = {row["output"]: row for row in mapping["outputs"]}

    assert set(rows) == set(outputs)
    assert len(rows) == 16
    dispositions = [row["disposition"] for row in mapping["outputs"]]
    assert dispositions.count("accepted_core") == 9
    assert dispositions.count("optional_api_plugin_conditional_deferred") == 6
    assert dispositions.count("p16_acceptance_decision_record") == 1
    assert mapping["decision"] == (
        "accepted_subscription_primary_sustainable_operations_core"
    )
    assert mapping["core_route"] == {
        "daily_mainline": ["chatgpt_web", "codex_cli"],
        "large_model_apis_default_enabled": False,
        "api_activation_required_for_core_acceptance": False,
    }
    plugin = mapping["optional_api_provider_plugin_v2"]
    assert plugin == {
        "status": "default_disabled_independent_deferred",
        "p16_core_hard_gate": False,
        "implementation_authorized": False,
        "release_authorized": False,
    }
    assert set(mapping["zero_operation_boundary"].values()) == {0}


def test_p16i_accepts_only_core_and_preserves_every_external_stop() -> None:
    state = load_yaml_file(PROJECT_STATE)
    p16h = state["p16h_operator_runbook_and_production_readiness"]
    p16i = state["p16i_production_operations_acceptance_decision"]
    report = P16I_ACCEPTANCE_REPORT.read_text(encoding="utf-8")

    assert p16h["status"] == (
        "merged_hosted_ci_passed_ready_for_p16_acceptance_review"
    )
    assert p16h["publication_receipt"] == {
        "pull_request": 203,
        "final_pr_head": "e48d7c2cda714c5fe578333eb5110b5c084f8c8c",
        "canonical_squash_commit": (
            "02699469bf96024bb481980712d47494a4ef08ff"
        ),
        "hosted_ci_run": 1199,
        "hosted_ci_conclusion": "success",
        "exact_changed_path_count": 19,
        "feature_branch": (
            "agent/p16h-operator-runbook-production-readiness-v1"
        ),
        "feature_branch_retained": True,
    }
    assert p16i["status"] == (
        "accepted_subscription_primary_sustainable_operations_core"
    )
    assert p16i["p16_core"] == {
        "accepted": True,
        "route": "subscription_primary",
        "daily_mainline": ["chatgpt_web", "codex_cli"],
        "acceptance_scope": "sustainable_operations_non_live_core",
    }
    assert set(p16i["remaining_authority"].values()) == {False}
    assert set(p16i["zero_operation_boundary"].values()) == {0}
    assert p16i["optional_api_provider_plugin_v2"][
        "p16_core_hard_gate"
    ] is False
    for marker in (
        "accepted_subscription_primary_sustainable_operations_core",
        "P16B through P16H",
        "nine Core outputs",
        "six API-mode-only outputs",
        "OPTIONAL-API-PROVIDER-PLUGIN-v2",
        "grants no production deployment",
        "No such operation occurred",
    ):
        assert marker in report


def test_subscription_public_entry_acceptance_freezes_exact_scope() -> None:
    manifest_result = validate_task_manifest(
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_CHANGE_PLAN
    )
    manifest = load_yaml_file(SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_MANIFEST)
    plan = load_yaml_file(SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_CHANGE_PLAN)
    closure = manifest["bounded_closure"]["frozen_before_execution"]

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == (
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES
    )
    assert set(manifest["scope"]["in_scope"]) == (
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES
    )
    assert set(plan["changed_files"]) == (
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES
    )
    assert len(SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES) == 6
    assert closure["task_identity"] == (
        "SUBSCRIPTION-WORKER-PUBLIC-ENTRY-ACCEPTANCE-v1"
    )
    assert closure["baseline_commit"] == (
        "8be8950937407bbca0c562b77348c67aba6b5685"
    )
    assert closure["baseline_tree"] == (
        "331d5496ea2aee610c17bd522850b959015ecb9f"
    )
    assert closure["allowed_scope"] == "exact_6_paths_listed_below"
    assert set(closure["finite_budgets"].values()) <= {0, 1, 3, 4}
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False
    assert all(
        not path.startswith("src/")
        for path in SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES
    )
    assert "blueprint/tool_system_v0.yaml" not in (
        SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES
    )
    assert "REPO_MANIFEST.md" not in SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_FILES


def test_subscription_public_entry_acceptance_maps_parent_matrix() -> None:
    mapping = load_yaml_file(SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_MAPPING)
    rows = {row["requirement"]: row for row in mapping["acceptance_matrix"]}
    expected_requirements = {
        "default_invocation_has_no_external_worker_call_or_mutation",
        "fake_codex_process_proves_argv_environment_output_timeout_and_cancellation",
        "public_cli_reaches_adapter_only_after_current_authority_and_snapshot_gates",
        "invalid_scope_snapshot_progress_or_candidate_fails_before_local_commit",
        "isolated_success_creates_exactly_one_local_commit_and_no_remote_effect",
        "hosted_ci_uses_fake_process_and_fake_repositories_only",
        "api_mode_remains_disabled_and_provider_invocations_remain_zero",
    }

    assert mapping["decision"] == (
        "accepted_subscription_worker_public_entry_core"
    )
    assert mapping["baseline_commit"] == (
        "8be8950937407bbca0c562b77348c67aba6b5685"
    )
    assert mapping["baseline_tree"] == (
        "331d5496ea2aee610c17bd522850b959015ecb9f"
    )
    assert set(rows) == expected_requirements
    assert {row["disposition"] for row in rows.values()} == {"accepted"}
    assert len(mapping["canonical_evidence_chain"]) == 12
    assert mapping["canonical_evidence_chain"][-1] == {
        "pull_request": 218,
        "role": "corrected_multi_stack_acceptance",
        "merge_commit": "8be8950937407bbca0c562b77348c67aba6b5685",
    }
    assert mapping["discarded_attempt"] == {
        "pull_request": 216,
        "merged": False,
        "accepted_evidence": False,
        "reason": (
            "unsealed_runtime_change_and_completed_receipt_replay_ordering_failure"
        ),
    }
    assert set(mapping["remaining_authority"].values()) == {False}
    assert set(mapping["zero_operation_boundary"].values()) == {0}


def test_subscription_public_entry_acceptance_preserves_external_stops() -> None:
    state = load_yaml_file(PROJECT_STATE)
    acceptance = state["subscription_worker_public_entry_acceptance"]
    report = SUBSCRIPTION_PUBLIC_ENTRY_ACCEPTANCE_REPORT.read_text(
        encoding="utf-8"
    )

    assert state["current_phase"]["status"] == "accepted"
    assert state["current_phase"]["id"] == EXPECTED_PHASE
    assert acceptance["status"] == (
        "accepted_subscription_worker_public_entry_core"
    )
    assert acceptance["authority_effect"] == "none"
    assert acceptance["accepted_public_entry"]["root_cli_subcommand"] == (
        "develop-execute"
    )
    assert acceptance["accepted_public_entry"][
        "real_codex_execution_observed_in_this_acceptance"
    ] is False
    assert acceptance["evidence_closure"][
        "stopped_unmerged_attempt_pull_request"
    ] == 216
    assert acceptance["evidence_closure"][
        "corrected_multi_stack_hosted_ci_runs"
    ] == [1301, 1302]
    assert set(acceptance["remaining_authority"].values()) == {False}
    assert set(acceptance["zero_operation_boundary"].values()) == {0}
    for marker in (
        "accepted_subscription_worker_public_entry_core",
        "develop-execute",
        "Draft PR #216 is not accepted evidence",
        "Hosted CI runs 1301 and 1302",
        "grants no real Codex execution",
        "No such operation occurs",
        "separately authorized future lifecycle",
    ):
        assert marker in report


def test_subscription_durable_call_lease_correction_is_exact_and_non_authorizing() -> None:
    manifest_result = validate_task_manifest(
        SUBSCRIPTION_DURABLE_CORRECTION_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(
        SUBSCRIPTION_DURABLE_CORRECTION_CHANGE_PLAN
    )
    manifest = load_yaml_file(SUBSCRIPTION_DURABLE_CORRECTION_MANIFEST)
    plan = load_yaml_file(SUBSCRIPTION_DURABLE_CORRECTION_CHANGE_PLAN)
    state = load_yaml_file(PROJECT_STATE)
    correction = state["subscription_worker_durable_call_lease_correction"]
    report = SUBSCRIPTION_DURABLE_CORRECTION_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert plan_result["status"] == "PASS"
    assert set(manifest["allowed_files"]) == SUBSCRIPTION_DURABLE_CORRECTION_FILES
    assert set(manifest["scope"]["in_scope"]) == SUBSCRIPTION_DURABLE_CORRECTION_FILES
    assert set(plan["changed_files"]) == SUBSCRIPTION_DURABLE_CORRECTION_FILES
    assert len(SUBSCRIPTION_DURABLE_CORRECTION_FILES) == 26
    closure = manifest["bounded_closure"]["frozen_before_execution"]
    assert closure["task_identity"] == (
        "P14G-SUBSCRIPTION-WORKER-DURABLE-CALL-LEASE-CORRECTION-v1"
    )
    assert closure["baseline_commit"] == (
        "0c710929e292b340538845a5e9e87c03c36f5794"
    )
    assert closure["baseline_tree"] == (
        "77232d4cc53217726c651572c4b8d277aa05ee28"
    )
    assert closure["allowed_scope"] == "exact_26_paths_listed_below"
    assert closure["finite_budgets"]["real_codex_invocations"] == 0
    assert closure["finite_budgets"]["api_provider_invocations"] == 0
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["branch_deletion_authorized"] is False

    assert state["current_phase"]["status"] == "accepted"
    assert state["current_phase"]["id"] == EXPECTED_PHASE
    assert correction["authority_effect"] == "none"
    assert correction["corrected_boundary"]["sqlite_schema_version"] == 4
    assert correction["corrected_boundary"]["timeout_terminal_code"] == (
        "SUBSCRIPTION_WORKER_TIMEOUT"
    )
    assert correction["deterministic_evidence"]["fake_process_only"] is True
    assert correction["deterministic_evidence"]["real_codex_invocations"] == 0
    assert set(correction["remaining_authority"].values()) == {False}
    assert set(correction["zero_operation_boundary"].values()) == {0}
    retained = correction["retained_failure_evidence"]
    assert retained["path"] == "/tmp/tool-system-real-subscription-acceptance-v1"
    assert retained["repository_managed"] is False
    assert set(retained) - {"path", "repository_managed"}
    assert all(
        retained[key] == 0
        for key in set(retained) - {"path", "repository_managed"}
    )
    for marker in (
        "schema v4",
        "SUBSCRIPTION_WORKER_TIMEOUT",
        "before process start",
        "/tmp/tool-system-real-subscription-acceptance-v1",
        "No actual Codex",
        "stops before any new real isolated acceptance",
    ):
        assert marker in report



def test_readme_matches_accepted_core_and_current_registry_inventory() -> None:
    readme_text = README.read_text(encoding="utf-8")
    assert "It registers 26 current tool-system modules" in readme_text
    assert "It registers 14 current tool-system modules" not in readme_text
    assert "P15 Core is accepted" in readme_text
    assert "P16 Core is accepted for subscription-primary sustainable operations" in readme_text
    assert "Build the missing blueprint-to-code autonomous implementation" not in readme_text
    assert "Production deployment and real-environment validation remain separately authorized" in readme_text
