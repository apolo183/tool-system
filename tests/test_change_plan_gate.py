from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate
from tool_system.gate.change_plan import (
    validate_change_plan_against_manifest,
    validate_change_plan_structure,
)
from tool_system.gate.test_gate import build_gate_decision, evaluate_command_results
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p2_gate_foundation.yaml"
PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p2_gate_foundation.yaml"


def test_change_plan_passes_structure_and_manifest_scope() -> None:
    plan = load_yaml_file(PLAN_PATH)
    manifest = load_yaml_file(MANIFEST_PATH)

    structure_ok, structure_reasons = validate_change_plan_structure(plan)
    scope_ok, scope_reasons = validate_change_plan_against_manifest(plan, manifest)

    assert structure_ok, structure_reasons
    assert scope_ok, scope_reasons


def test_cli_validate_change_plan_returns_pass() -> None:
    result = validate(PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_change_plan_blocks_path_outside_manifest_allowlist() -> None:
    plan = load_yaml_file(PLAN_PATH)
    manifest = load_yaml_file(MANIFEST_PATH)
    plan["changed_files"] = ["unknown/file.py"]

    scope_ok, reasons = validate_change_plan_against_manifest(plan, manifest)

    assert not scope_ok
    assert any("outside manifest allowlist" in reason for reason in reasons)


def test_command_results_pass_when_exit_codes_are_zero() -> None:
    ok, reasons = evaluate_command_results([
        {"name": "unit", "exit_code": 0},
        {"name": "plan", "exit_code": 0},
    ])

    assert ok
    assert reasons == []


def test_gate_blocks_nonzero_command_result() -> None:
    result = build_gate_decision(
        plan_ok=True,
        plan_reasons=[],
        command_results=[{"name": "unit", "exit_code": 1}],
    )

    assert result["status"] == "BLOCK"
    assert result["reasons"] == ["unit exited with 1"]
