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
EXPECTED_PHASE = "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
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

    assert project_state["current_phase"]["id"] == EXPECTED_PHASE
    assert project_state["current_phase"]["status"] == "accepted_and_closed"
    assert project_state["authority_effect"] == "none"
    assert project_state["current_phase"]["last_accepted_stage"] == (
        "P14H_MULTI_STACK_END_TO_END_FIXTURE_ACCEPTANCE"
    )
    assert project_state["current_phase"]["last_accepted_stage_record"] == (
        "docs/reports/p14h_multi_stack_fixture_acceptance.md"
    )
    assert project_state["current_phase"]["closure_stage"] == (
        "P14I_ACCEPTANCE_CLOSURE"
    )
    assert project_state["current_phase"]["closure_stage_record"] == (
        "docs/reports/p14i_blueprint_to_code_acceptance_closure.md"
    )
    assert project_state["current_phase"]["acceptance_record"] == (
        "docs/reports/p14i_blueprint_to_code_acceptance_closure.md"
    )
    assert project_state["current_phase"]["next_stage"] is None
    assert project_state["current_phase"]["next_stage_authorized"] is False
    assert project_state["current_phase"]["next_phase"] == (
        "P15_MULTI_PROJECT_BENCHMARK"
    )
    assert project_state["current_phase"]["next_phase_entry_authorized"] is False
    assert EXPECTED_PHASE in blueprint["milestones"]
    assert {
        "phase",
        "status",
        "acceptance",
        "successor_authorization",
        "active_phase_execution",
        "p14c_source_implementation",
    }.isdisjoint(blueprint)
    assert project_state["prior_acceptance"]["record"] == (
        "docs/reports/p13e_security_reliability_acceptance_closure.md"
    )
    assert project_state["prior_acceptance"]["accepted_scope"] == (
        "application_guarded_local_fixture_worker_and_single_host_sqlite_hardening"
    )
    assert project_state["prior_acceptance"]["predecessor"]["phase"] == (
        "P12_DURABLE_ORCHESTRATOR"
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
    boundaries = project_state["authorization_boundaries"]
    assert boundaries["state_file_grants_authority"] is False
    assert boundaries["live_model_provider_execution_authorized"] is False
    assert boundaries["credential_value_access_authorized"] is False
    assert boundaries["downstream_repository_access_authorized"] is False
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
    p14 = blueprint["milestones"][EXPECTED_PHASE]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert stages["P14I_ACCEPTANCE_CLOSURE"]["execution_boundary"] == (
        "governance_only"
    )
    assert "isolated repository fixture" in p14["accepted_claim"]
    assert "local Git software change" in p14["accepted_claim"]
    assert project_state["current_phase"]["next_phase"] == (
        "P15_MULTI_PROJECT_BENCHMARK"
    )
    assert project_state["current_phase"]["next_phase_entry_authorized"] is False
    for marker in (
        "P14 output acceptance matrix",
        "Required P14 fixture matrix",
        "Global product-objective disposition",
        "provider_invocations: 0",
        "runtime_source_changes: 0",
        "P15_entry_authorized: false",
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
