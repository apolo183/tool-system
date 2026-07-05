from __future__ import annotations

from pathlib import Path

from tool_system.gate.change_plan import validate_change_plan_against_manifest
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_p2_gate_foundation.yaml"
PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_p2_gate_foundation.yaml"


def test_gate_readme_is_allowed_by_manifest_wildcard() -> None:
    plan = load_yaml_file(PLAN_PATH)
    manifest = load_yaml_file(MANIFEST_PATH)
    assert "src/tool_system/gate/README.md" in plan["changed_files"]

    ok, reasons = validate_change_plan_against_manifest(plan, manifest)

    assert ok, reasons
