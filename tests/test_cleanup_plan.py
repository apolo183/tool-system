from __future__ import annotations

from pathlib import Path

from tool_system.cleanup.residue_plan import build_cleanup_plan, build_cleanup_plan_file
from tool_system.cli.validate_change_plan import validate as validate_change_plan


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "examples" / "cleanup" / "tool_system_residue_state.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_residue_review.yaml"


def test_cleanup_plan_marks_probe_residue_without_execution() -> None:
    result = build_cleanup_plan_file(STATE_PATH)

    assert result["status"] == "PASS"
    assert result["action_count"] >= 3
    assert result["execute"] is False
    assert all(action["execute"] is False for action in result["actions"])
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_cleanup_plan_blocks_malformed_state() -> None:
    result = build_cleanup_plan({"branches": [123]})

    assert result["status"] == "BLOCK"
    assert "branch entries must be strings or mappings with name" in result["reasons"]


def test_cleanup_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
