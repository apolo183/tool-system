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
    / "tool_system_p13e_security_reliability_acceptance_closure.yaml"
)
EXPECTED_PHASE = "P13_SECURITY_RELIABILITY_HARDENING"


def test_public_contracts_have_same_current_phase() -> None:
    agents_text = AGENTS.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)

    assert f"Current phase: {EXPECTED_PHASE}" in agents_text
    assert f"Current phase: `{EXPECTED_PHASE}`" in readme_text
    assert "Status: `accepted_and_closed`." in agents_text
    assert "Status: `accepted_and_closed`." in readme_text
    assert blueprint["phase"] == EXPECTED_PHASE
    assert EXPECTED_PHASE in blueprint["milestones"]
    assert blueprint["acceptance"]["successor_phase_authorized"] is False
    assert blueprint["status"] == "accepted_and_closed"
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
    assert blueprint["successor_authorization"]["active_phase"] is None
    assert blueprint["successor_authorization"]["record"] == (
        "docs/reports/p13e_security_reliability_acceptance_closure.md"
    )
    assert blueprint["successor_authorization"]["next_phase"] == (
        "P14_MULTI_REPO_BENCHMARK"
    )
    assert blueprint["successor_authorization"]["next_phase_entry_authorized"] is False
    assert set(blueprint["successor_authorization"]["authorized_roadmap"]) == {
        "P11_REAL_WORKER_RUNTIME",
        "P12_DURABLE_ORCHESTRATOR",
        "P13_SECURITY_RELIABILITY_HARDENING",
        "P14_MULTI_REPO_BENCHMARK",
        "P15_PRODUCTION_OPERATIONS_ACCEPTANCE",
    }


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
