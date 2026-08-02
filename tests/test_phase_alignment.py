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
    assert project_state["current_phase"]["status"] == "active"
    assert project_state["authority_effect"] == "none"
    assert project_state["current_phase"]["last_accepted_stage"] == (
        "P14D_REPOSITORY_CONTEXT_NATURAL_OWNER"
    )
    assert project_state["current_phase"]["last_accepted_stage_record"] == (
        "docs/reports/p14d_repository_context_natural_owner_acceptance.md"
    )
    assert project_state["current_phase"]["next_stage"] == (
        "P14E_BLUEPRINT_COMPILER"
    )
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
    for public_contract in (agents_text, readme_text, principles_text):
        assert "docs/tool_system_project_state_v1.yaml" in public_contract
        assert "authority" in public_contract


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


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
