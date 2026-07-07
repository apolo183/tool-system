from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN = ROOT / "examples" / "change_plans" / "tool_system_phase_alignment.yaml"
EXPECTED_PHASE = "P7_BLUEPRINT_TO_TASK_GRAPH"


def test_public_contracts_have_same_current_phase() -> None:
    agents_text = AGENTS.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")
    blueprint = load_yaml_file(BLUEPRINT)

    assert f"Current phase: {EXPECTED_PHASE}" in agents_text
    assert f"Current phase: `{EXPECTED_PHASE}`" in readme_text
    assert blueprint["phase"] == EXPECTED_PHASE
    assert "P7_BLUEPRINT_TO_TASK_GRAPH" in blueprint["milestones"]


def test_phase_alignment_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
