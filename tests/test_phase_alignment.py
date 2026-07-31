from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14mr_milestone_module_invariant.yaml"
)
EXPECTED_PHASE = "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"


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
        "P14MR_MILESTONE_MODULE_INVARIANT"
    )
    assert project_state["current_phase"]["next_stage"] == (
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
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
    assert p14c["source_status"] == (
        "corrected_source_and_live_issuer_merged_no_execution_not_accepted"
    )
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
    assert p14c["real_live_approval_record_created"] is False
    assert p14c["live_capability_issued"] is False
    assert p14c["stage_accepted"] is False
    boundaries = project_state["authorization_boundaries"]
    assert boundaries["state_file_grants_authority"] is False
    assert boundaries["live_model_provider_execution_authorized"] is False
    for public_contract in (agents_text, readme_text, principles_text):
        assert "docs/tool_system_project_state_v1.yaml" in public_contract
        assert "authority" in public_contract


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
