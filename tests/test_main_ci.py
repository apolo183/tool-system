from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.repo_controller.main_ci import evaluate_commit_runs, observe_main_ci


ROOT = Path(__file__).resolve().parents[1]
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p3i_observability.yaml"


def test_evaluate_commit_runs_passes_completed_success() -> None:
    result = evaluate_commit_runs([
        {
            "id": 1001,
            "name": "tool-system-ci",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc123",
        }
    ])

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_evaluate_commit_runs_marks_unavailable_when_no_runs() -> None:
    result = evaluate_commit_runs([])

    assert result["status"] == "UNAVAILABLE"
    assert result["reasons"] == ["workflow runs unavailable for commit"]


def test_evaluate_commit_runs_blocks_failed_run() -> None:
    result = evaluate_commit_runs([
        {
            "id": 1001,
            "name": "tool-system-ci",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "abc123",
        }
    ])

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["tool-system-ci conclusion is failure"]


def test_observe_main_ci_writes_jsonl_record(tmp_path: Path) -> None:
    def runner(args: list[str]) -> Any:
        assert args[:2] == ["run", "list"]
        return [
            {
                "databaseId": 1001,
                "name": "tool-system-ci",
                "status": "completed",
                "conclusion": "success",
                "headSha": "abc123",
            }
        ]

    audit_path = tmp_path / "main_ci.jsonl"
    result = observe_main_ci(
        repository_full_name="apolo183/tool-system",
        commit_sha="abc123",
        audit_path=audit_path,
        runner=runner,
    )

    assert result["status"] == "PASS"
    assert result["audit_path"] == str(audit_path)
    record = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert record["repository_full_name"] == "apolo183/tool-system"
    assert record["commit_sha"] == "abc123"
    assert record["status"] == "PASS"


def test_p3i_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
