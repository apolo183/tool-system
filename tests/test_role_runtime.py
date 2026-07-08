from __future__ import annotations

from pathlib import Path

from tool_system.cli.run_role_graph import main as run_role_graph_main
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.runtime.role_runtime import build_role_runtime_plan_file


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_role_runtime.yaml"


def test_role_runtime_builds_no_mutation_steps(tmp_path: Path) -> None:
    result = build_role_runtime_plan_file(
        graph_path=GRAPH_PATH,
        blueprint_path=BLUEPRINT_PATH,
        audit_path=tmp_path / "role_runtime.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_role_runtime_plan"
    assert result["role_step_count"] == 4
    assert result["execute"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert all(step["execute"] is False for step in result["role_steps"])
    assert [step["role"] for step in result["role_steps"]] == [
        "evidence_collector",
        "policy_guard",
        "test_engineer",
        "audit_recorder",
    ]
    assert Path(result["audit_path"]).exists()


def test_role_runtime_cli(tmp_path: Path, capsys) -> None:
    exit_code = run_role_graph_main([
        str(GRAPH_PATH),
        "--blueprint",
        str(BLUEPRINT_PATH),
        "--audit-path",
        str(tmp_path / "cli.jsonl"),
    ])

    assert exit_code == 0
    assert '"mode": "tool_system_role_runtime_plan"' in capsys.readouterr().out


def test_role_runtime_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
