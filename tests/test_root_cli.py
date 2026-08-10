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


def test_root_cli_develop_routes_isolated_context_compilation(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    private_repository_root = tmp_path / "target-fixture"
    captured: dict[str, object] = {}

    def fake_context_compilation(**arguments: object) -> dict[str, object]:
        captured.update(arguments)
        return {
            "status": "PASS",
            "mode": "subscription_worker_public_entry_context_compile",
            "repository_root_identity_sha256": "a" * 64,
            "repository_context_built": True,
            "blueprint_compiled": True,
            "worker_execution_authorized": False,
            "provider_invocations": 0,
            "local_git_write_operations": 0,
        }

    monkeypatch.setattr(
        "tool_system.cli.main.run_subscription_public_entry_context_compilation",
        fake_context_compilation,
    )
    exit_code = main([
        "develop",
        "examples/task_manifests/tool_system_audit_bundle.yaml",
        "--change-plan",
        "examples/change_plans/tool_system_audit_bundle.yaml",
        "--repository-root",
        str(private_repository_root),
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
        "--isolated-fixture-repository",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert captured["repository_root"] == private_repository_root
    assert captured["isolated_fixture_repository"] is True
    assert '"mode": "subscription_worker_public_entry_context_compile"' in output
    assert '"worker_execution_authorized": false' in output
    assert '"repository_root_identity_sha256"' in output
    assert str(private_repository_root) not in output
