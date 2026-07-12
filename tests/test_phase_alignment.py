from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14mr_milestone_module_invariant.yaml"
)
EXPECTED_PHASE = "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"


def test_public_contracts_have_same_current_phase() -> None:
    agents_text = AGENTS.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)

    assert f"Current phase: {EXPECTED_PHASE}" in agents_text
    assert f"Current phase: `{EXPECTED_PHASE}`" in readme_text
    assert "Status: `active`." in agents_text
    assert "Status: `active`." in readme_text
    assert blueprint["phase"] == EXPECTED_PHASE
    assert EXPECTED_PHASE in blueprint["milestones"]
    assert blueprint["acceptance"]["successor_phase_authorized"] is True
    assert blueprint["status"] == "active"
    assert blueprint["acceptance"]["record"] == (
        "docs/reports/p13e_security_reliability_acceptance_closure.md"
    )
    assert blueprint["acceptance"]["accepted_scope"] == (
        "application_guarded_local_fixture_worker_and_single_host_sqlite_hardening"
    )
    assert blueprint["acceptance"]["prior_acceptance"]["phase"] == (
        "P12_DURABLE_ORCHESTRATOR"
    )
    assert blueprint["successor_authorization"]["later_phase_entry_authorized"] is False
    assert blueprint["successor_authorization"]["active_phase"] == EXPECTED_PHASE
    assert blueprint["successor_authorization"]["record"] == (
        "docs/reports/p14a_blueprint_to_code_phase_entry_and_contract.md"
    )
    assert blueprint["successor_authorization"]["next_phase"] == (
        "P15_MULTI_PROJECT_BENCHMARK"
    )
    assert blueprint["successor_authorization"]["next_phase_entry_authorized"] is False
    assert set(blueprint["successor_authorization"]["defined_roadmap"]) == {
        "P11_REAL_WORKER_RUNTIME",
        "P12_DURABLE_ORCHESTRATOR",
        "P13_SECURITY_RELIABILITY_HARDENING",
        "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT",
        "P15_MULTI_PROJECT_BENCHMARK",
        "P16_PRODUCTION_OPERATIONS_ACCEPTANCE",
    }
    execution = blueprint["active_phase_execution"]
    assert execution["current_stage"] == (
        "P14MR_MILESTONE_MODULE_INVARIANT"
    )
    assert execution["phase_entry_authorized"] is True
    assert execution["authority_effect"] == "tool_system_local_only"
    assert "authorized_scope" not in execution
    assert "authorized_scope_role" not in execution
    assert "global_milestone_module_governance_only" not in execution.values()
    assert execution["record_role"] == "existing_acceptance_evidence_only"
    assert execution["durable_rule_owners"] == [
        "blueprint/tool_system_v0.yaml:milestone_module_invariant",
        (
            "docs/tool_system_global_development_principles_v1.md:"
            "durable_module_and_milestone_discipline"
        ),
    ]
    assert execution["phase_source_implementation_authorized"] is False
    assert execution["next_stage"] == "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    assert execution["next_stage_authorized"] is False
    assert execution["live_model_provider_execution_authorized"] is False
    assert execution["remote_target_mutation_authorized"] is False
    assert execution["production_deployment_authorized"] is False


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
