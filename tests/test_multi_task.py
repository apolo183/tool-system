from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.runner.task_runner import run_batch_file, run_batch_pipeline


ROOT = Path(__file__).resolve().parents[1]
GROUP_PATH = ROOT / "examples" / "batches" / "tool_system_batch_runner.yaml"
PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_batch_runner.yaml"


def test_multi_task_pipeline_runs_without_commands(tmp_path: Path) -> None:
    result = run_batch_file(
        batch_path=GROUP_PATH,
        audit_path=tmp_path / "group.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["task_count"] == 2
    assert result["completed_task_count"] == 2
    assert all(task["status"] == "PASS" for task in result["task_results"])
    assert Path(result["audit_path"]).exists()


def test_multi_task_pipeline_blocks_empty_input(tmp_path: Path) -> None:
    result = run_batch_pipeline(
        batch={"tasks": []},
        audit_path=tmp_path / "blocked.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert "batch.tasks must be a non-empty list" in result["reasons"]


def test_multi_task_pipeline_change_plan_validates() -> None:
    result = validate_change_plan(PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
