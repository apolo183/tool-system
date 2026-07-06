from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.live_github_collector import (
    collect_github_state_snapshot,
    collect_pull_request_state,
    collect_workflow_runs_for_commit,
    evaluate_live_pull_request,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "repo_write_policy.yaml"
GATE_DECISION_PATH = ROOT / "examples" / "gate_decisions" / "pass.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3c_live_collector.yaml"
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p3c_live_collector.yaml"


def fake_runner(args: list[str]) -> Any:
    if args[:2] == ["pr", "view"]:
        return {
            "number": 7,
            "state": "OPEN",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "headRefOid": "abc123",
            "baseRefName": "main",
        }
    if args[:2] == ["run", "list"]:
        return [
            {
                "databaseId": 1001,
                "name": "tool-system-ci",
                "status": "completed",
                "conclusion": "success",
                "headSha": "abc123",
            }
        ]
    raise AssertionError(f"unexpected gh args: {args}")


def test_collect_pull_request_state_normalizes_gh_values() -> None:
    pull_request = collect_pull_request_state("apolo183/tool-system", 7, runner=fake_runner)

    assert pull_request == {
        "repository": "apolo183/tool-system",
        "number": 7,
        "state": "open",
        "draft": False,
        "mergeable": True,
        "head_sha": "abc123",
        "base": "main",
    }


def test_collect_workflow_runs_for_commit_normalizes_runs() -> None:
    runs = collect_workflow_runs_for_commit("apolo183/tool-system", "abc123", runner=fake_runner)

    assert runs == [
        {
            "id": 1001,
            "name": "tool-system-ci",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123",
        }
    ]


def test_collect_github_state_snapshot_builds_controller_input() -> None:
    gate_decision = load_yaml_file(GATE_DECISION_PATH)
    snapshot = collect_github_state_snapshot(
        "apolo183/tool-system",
        7,
        gate_decision=gate_decision,
        runner=fake_runner,
    )

    assert snapshot["repository_full_name"] == "apolo183/tool-system"
    assert snapshot["pull_request"]["head_sha"] == "abc123"
    assert snapshot["gate_decision"] == {"status": "PASS", "reasons": []}
    assert snapshot["workflow_runs"][0]["conclusion"] == "success"


def test_evaluate_live_pull_request_passes_successful_state() -> None:
    gate_decision = load_yaml_file(GATE_DECISION_PATH)
    policy = load_yaml_file(POLICY_PATH)

    output = evaluate_live_pull_request(
        "apolo183/tool-system",
        7,
        gate_decision=gate_decision,
        repo_policy=policy,
        runner=fake_runner,
        task_manifest=load_yaml_file(MANIFEST_PATH),
        change_plan=load_yaml_file(CHANGE_PLAN_PATH),
    )

    assert output["decision"]["status"] == "PASS"
    assert output["audit_record"]["head_sha"] == "abc123"


def test_p3c_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
