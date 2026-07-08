from __future__ import annotations

from pathlib import Path

from tool_system.cli.run_stage import main as run_stage_main
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.runner.stage_runner import run_stage_pipeline


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "examples" / "requirements" / "tool_system_p7d.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_stage.yaml"


def test_stage_runner_executes_compiled_batch_without_commands(tmp_path: Path) -> None:
    result = run_stage_pipeline(
        input_path=INPUT_PATH,
        blueprint_path=BLUEPRINT_PATH,
        audit_path=tmp_path / "stage_runner.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_stage_runner"
    assert result["graph_result"]["status"] == "PASS"
    assert result["compiled_batch"]["status"] == "PASS"
    assert result["batch_result"]["status"] == "PASS"
    assert result["batch_result"]["completed_task_count"] == 4
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert Path(result["audit_path"]).exists()


def test_stage_runner_cli(tmp_path: Path, capsys) -> None:
    exit_code = run_stage_main([
        str(INPUT_PATH),
        "--blueprint",
        str(BLUEPRINT_PATH),
        "--audit-path",
        str(tmp_path / "cli.jsonl"),
        "--skip-commands",
    ])

    assert exit_code == 0
    assert '"mode": "tool_system_stage_runner"' in capsys.readouterr().out


def test_stage_runner_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
