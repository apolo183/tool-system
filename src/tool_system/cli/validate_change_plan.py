from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.gate.change_plan import (
    validate_change_plan_against_manifest,
    validate_change_plan_structure,
)
from tool_system.manifest.task_manifest import load_yaml_file, validate_manifest_structure


def validate(change_plan_path: Path) -> dict[str, object]:
    plan = load_yaml_file(change_plan_path)
    manifest_path = Path(str(plan.get("task_manifest", "")))
    manifest = load_yaml_file(manifest_path)

    plan_structure_ok, plan_structure_reasons = validate_change_plan_structure(plan)
    manifest_ok, manifest_reasons = validate_manifest_structure(manifest)
    plan_scope_ok, plan_scope_reasons = validate_change_plan_against_manifest(plan, manifest)

    reasons = plan_structure_reasons + manifest_reasons + plan_scope_reasons
    return {
        "status": "PASS" if plan_structure_ok and manifest_ok and plan_scope_ok else "BLOCK",
        "change_plan_path": str(change_plan_path),
        "task_manifest_path": str(manifest_path),
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a tool-system change plan.")
    parser.add_argument("change_plan", type=Path)
    args = parser.parse_args()
    result = validate(args.change_plan)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
