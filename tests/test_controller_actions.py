from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.repo_controller.actions import (
    _issue_test_repository_action_capability,
    build_action_plan,
    execute_action_plan,
)

ROOT = Path(__file__).resolve().parents[1]
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3d_controller_actions.yaml"
APPROVAL_SHA256 = "a" * 64


def _passing_decision() -> dict[str, object]:
    return {
        "status": "PASS",
        "merge_method": "squash",
        "approval_record_sha256": APPROVAL_SHA256,
        "reasons": [],
    }


def _pull_request() -> dict[str, object]:
    return {
        "repository": "apolo183/tool-system",
        "number": 8,
        "base": "main",
        "head_sha": "abc123",
        "draft": False,
    }


def _capability(runner):
    return _issue_test_repository_action_capability(
        repository_full_name="apolo183/tool-system",
        pr_number=8,
        action="pr_squash",
        base_branch="main",
        expected_head_sha="abc123",
        approval_record_sha256=APPROVAL_SHA256,
        runner=runner,
    )


def test_action_plan_blocks_failed_decision() -> None:
    plan = build_action_plan(
        decision={"status": "BLOCK", "reasons": ["ci failed"]},
        pull_request={"number": 8, "head_sha": "abc123"},
    )

    assert plan == {"status": "BLOCK", "actions": [], "reasons": ["ci failed"]}


def test_action_plan_blocks_draft_pr() -> None:
    plan = build_action_plan(
        decision=_passing_decision(),
        pull_request={"number": 8, "head_sha": "abc123", "draft": True},
    )

    assert plan == {
        "status": "BLOCK",
        "actions": [],
        "reasons": ["pull request must not be draft before action planning"],
    }


def test_execute_action_plan_dry_run_returns_commands() -> None:
    plan = build_action_plan(
        decision=_passing_decision(),
        pull_request=_pull_request(),
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
        decision=_passing_decision(),
        pull_request=_pull_request(),
    )
    result = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        capability=_capability(runner),
        runner_kind="injected_fake",
    )

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
        decision=_passing_decision(),
        pull_request=_pull_request(),
    )
    result = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        capability=_capability(runner),
        runner_kind="injected_fake",
    )

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["failed"]


def test_execute_action_plan_requires_capability_before_runner() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str]) -> dict[str, Any]:
        calls.append(args)
        return {"exit_code": 0, "stdout": "unexpected", "stderr": ""}

    plan = build_action_plan(
        decision=_passing_decision(),
        pull_request=_pull_request(),
    )
    result = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        runner_kind="injected_fake",
    )

    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "repository action capability is required before mutation"
    ]
    assert calls == []


def test_repository_action_capability_is_context_bound_and_single_use() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str]) -> dict[str, Any]:
        calls.append(args)
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}

    plan = build_action_plan(
        decision=_passing_decision(),
        pull_request=_pull_request(),
    )
    capability = _capability(runner)
    mismatch = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        capability=capability,
        runner_kind="live_gh",
    )
    first = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        capability=capability,
        runner_kind="injected_fake",
    )
    replay = execute_action_plan(
        "apolo183/tool-system",
        plan,
        runner=runner,
        dry_run=False,
        capability=capability,
        runner_kind="injected_fake",
    )

    assert mismatch["status"] == "BLOCK"
    assert mismatch["reasons"] == [
        "repository action capability does not match current action context"
    ]
    assert first["status"] == "PASS"
    assert replay["status"] == "BLOCK"
    assert replay["reasons"] == [
        "repository action capability has already been consumed"
    ]
    assert len(calls) == 1


def test_p3d_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
