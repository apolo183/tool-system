from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.repo_controller.actions import build_action_plan, execute_action_plan


ROOT = Path(__file__).resolve().parents[1]
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3d_controller_actions.yaml"


def test_action_plan_blocks_failed_decision() -> None:
    plan = build_action_plan(
        decision={"status": "BLOCK", "reasons": ["ci failed"]},
        pull_request={"number": 8, "head_sha": "abc123"},
    )

    assert plan == {"status": "BLOCK", "actions": [], "reasons": ["ci failed"]}


def test_action_plan_adds_ready_for_draft_pr() -> None:
    plan = build_action_plan(
        decision={"status": "PASS", "merge_method": "squash", "reasons": []},
        pull_request={"number": 8, "head_sha": "abc123", "draft": True},
    )

    assert plan["status"] == "PASS"
    assert plan["actions"] == [
        {"action": "pr_ready", "pr_number": 8},
        {
            "action": "pr_squash",
            "pr_number": 8,
            "expected_head_sha": "abc123",
            "merge_method": "squash",
        },
    ]


def test_execute_action_plan_dry_run_returns_commands() -> None:
    plan = build_action_plan(
        decision={"status": "PASS", "merge_method": "squash", "reasons": []},
        pull_request={"number": 8, "head_sha": "abc123", "draft": False},
    )

    result = execute_action_plan("apolo183/tool-system", plan, dry_run=True)

    assert result["status"] == "PASS"
    assert result["results"][0]["dry_run"] is True
    assert result["results"][0]["command"] == [
        "pr",
        "merge",
        "8",
        "--repo",
        "apolo183/tool-system",
        "--squash",
        "--match-head-commit",
        "abc123",
    ]


def test_execute_action_plan_runs_with_injected_runner() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str]) -> dict[str, Any]:
        calls.append(args)
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}

    plan = build_action_plan(
        decision={"status": "PASS", "merge_method": "squash", "reasons": []},
        pull_request={"number": 8, "head_sha": "abc123", "draft": False},
    )
    result = execute_action_plan("apolo183/tool-system", plan, runner=runner, dry_run=False)

    assert result["status"] == "PASS"
    assert calls == [[
        "pr",
        "merge",
        "8",
        "--repo",
        "apolo183/tool-system",
        "--squash",
        "--match-head-commit",
        "abc123",
    ]]


def test_execute_action_plan_blocks_failed_runner_result() -> None:
    def runner(args: list[str]) -> dict[str, Any]:
        return {"exit_code": 7, "stdout": "", "stderr": "failed"}

    plan = build_action_plan(
        decision={"status": "PASS", "merge_method": "squash", "reasons": []},
        pull_request={"number": 8, "head_sha": "abc123", "draft": False},
    )
    result = execute_action_plan("apolo183/tool-system", plan, runner=runner, dry_run=False)

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["failed"]


def test_p3d_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
