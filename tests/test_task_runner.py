from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool_system.cli.validate_change_plan import validate as validate_change_plan
import tool_system.gate.command_runner as command_runner
from tool_system.runner.task_runner import run_task_pipeline


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_audit_bundle.yaml"
PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_audit_bundle.yaml"
P6_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_run_entry.yaml"


def test_task_runner_validates_manifest_and_plan_without_commands(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        audit_path=tmp_path / "task_runner.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["manifest_result"]["status"] == "PASS"
    assert result["change_plan_result"]["status"] == "PASS"
    assert result["gate_decision"]["status"] == "PASS"
    assert result["command_results"] == []
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert Path(result["audit_path"]).exists()


def test_task_runner_blocks_without_change_plan_when_index_is_off(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        active_gates_path=None,
        audit_path=tmp_path / "blocked.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert "change plan is required" in result["reasons"]
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_task_runner_change_plan_validates() -> None:
    result = validate_change_plan(P6_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_task_runner_delegates_execution_to_protected_revalidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="fixture-pass\n", stderr="")

    monkeypatch.setattr(command_runner.subprocess, "run", fake_run)

    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        execute_commands=True,
    )

    protected = result["protected_execution_result"]
    assert result["status"] == "PASS"
    assert protected["status"] == "PASS"
    assert protected["preflight"]["validation_to_dispatch_inputs_equal"] is True
    assert protected["input_sha256_before"] == protected["input_sha256_after"]
    assert protected["subprocess_call_count"] == len(calls)
