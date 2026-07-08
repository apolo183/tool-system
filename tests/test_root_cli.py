from __future__ import annotations

from pathlib import Path

from tool_system.cli.main import main
from tool_system.cli.validate_change_plan import validate as validate_change_plan


ROOT = Path(__file__).resolve().parents[1]
TASK_MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_audit_bundle.yaml"
CHANGE_PLAN = ROOT / "examples" / "change_plans" / "tool_system_audit_bundle.yaml"
BATCH = ROOT / "examples" / "batches" / "tool_system_batch_runner.yaml"
GRAPH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
ROOT_CLI_PLAN = ROOT / "examples" / "change_plans" / "tool_system_root_cli.yaml"
ROOT_ROLES_PLAN = ROOT / "examples" / "change_plans" / "tool_system_root_roles.yaml"


def test_root_cli_run_subcommand(tmp_path: Path, capsys) -> None:
    exit_code = main([
        "run",
        str(TASK_MANIFEST),
        "--change-plan",
        str(CHANGE_PLAN),
        "--audit-path",
        str(tmp_path / "run.jsonl"),
        "--skip-commands",
    ])

    assert exit_code == 0
    assert (tmp_path / "run.jsonl").exists()
    assert '"mode": "tool_system_task_runner"' in capsys.readouterr().out


def test_root_cli_batch_subcommand(tmp_path: Path, capsys) -> None:
    exit_code = main([
        "batch",
        str(BATCH),
        "--audit-path",
        str(tmp_path / "batch.jsonl"),
        "--skip-commands",
    ])

    assert exit_code == 0
    assert (tmp_path / "batch.jsonl").exists()
    assert '"mode": "tool_system_batch_runner"' in capsys.readouterr().out


def test_root_cli_roles_subcommand(tmp_path: Path, capsys) -> None:
    exit_code = main([
        "roles",
        str(GRAPH),
        "--audit-path",
        str(tmp_path / "roles.jsonl"),
    ])

    assert exit_code == 0
    assert (tmp_path / "roles.jsonl").exists()
    assert '"mode": "tool_system_role_runtime_plan"' in capsys.readouterr().out


def test_root_cli_change_plans_validate() -> None:
    root_result = validate_change_plan(ROOT_CLI_PLAN)
    roles_result = validate_change_plan(ROOT_ROLES_PLAN)

    assert root_result["status"] == "PASS"
    assert root_result["reasons"] == []
    assert roles_result["status"] == "PASS"
    assert roles_result["reasons"] == []
