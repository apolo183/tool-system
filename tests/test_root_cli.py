from __future__ import annotations

from pathlib import Path

from tool_system.cli.main import main
from tool_system.cli.validate_change_plan import validate as validate_change_plan


ROOT = Path(__file__).resolve().parents[1]
TASK_MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_audit_bundle.yaml"
CHANGE_PLAN = ROOT / "examples" / "change_plans" / "tool_system_audit_bundle.yaml"
BATCH = ROOT / "examples" / "batches" / "tool_system_batch_runner.yaml"
ROOT_CLI_PLAN = ROOT / "examples" / "change_plans" / "tool_system_root_cli.yaml"


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


def test_root_cli_change_plan_validates() -> None:
    result = validate_change_plan(ROOT_CLI_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_root_cli_develop_preflight_is_nonexecuting_and_redacted(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.chdir(ROOT)
    exit_code = main([
        "develop",
        "examples/task_manifests/tool_system_audit_bundle.yaml",
        "--change-plan",
        "examples/change_plans/tool_system_audit_bundle.yaml",
        "--repository-root",
        str(ROOT),
        "--expected-head",
        "b" * 40,
        "--milestone",
        "P16",
        "--acceptance",
        "subscription-core-remains-bounded",
        "--governance-path",
        "AGENTS.md",
        "--query-term",
        "task-runner",
        "--seed-path",
        "src/tool_system/runner/task_runner.py",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"mode": "subscription_worker_public_entry_authority_preflight"' in output
    assert '"worker_execution_authorized": false' in output
    assert '"repository_root_identity_sha256"' in output
    assert str(ROOT) not in output
    assert not (tmp_path / "unexpected").exists()
