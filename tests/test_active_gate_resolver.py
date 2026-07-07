from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.runner.active_gate_resolver import resolve_change_plan_from_active_gates
from tool_system.runner.task_runner import run_batch_file, run_task_pipeline


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_GATES = ROOT / "examples" / "active_gates.yaml"
MANIFEST = ROOT / "examples" / "task_manifests" / "tool_system_run_entry.yaml"
RESOLVED_PLAN = ROOT / "examples" / "change_plans" / "tool_system_run_entry.yaml"
BATCH = ROOT / "examples" / "batches" / "tool_system_resolved_batch.yaml"
P6E_PLAN = ROOT / "examples" / "change_plans" / "tool_system_active_gate_resolver.yaml"


def test_resolves_change_plan_from_active_gates() -> None:
    resolved = resolve_change_plan_from_active_gates(MANIFEST, ACTIVE_GATES)

    assert resolved == RESOLVED_PLAN


def test_task_runner_resolves_change_plan_when_omitted(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST,
        active_gates_path=ACTIVE_GATES,
        audit_path=tmp_path / "resolved.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["change_plan_path"] == str(RESOLVED_PLAN)
    assert result["change_plan_resolution_source"] == "active_gates"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_batch_runner_resolves_omitted_change_plans(tmp_path: Path) -> None:
    result = run_batch_file(
        batch_path=BATCH,
        active_gates_path=ACTIVE_GATES,
        audit_path=tmp_path / "resolved_batch.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["completed_task_count"] == 2
    assert all(task["change_plan_resolution_source"] == "active_gates" for task in result["task_results"])


def test_active_gate_resolver_change_plan_validates() -> None:
    result = validate_change_plan(P6E_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
