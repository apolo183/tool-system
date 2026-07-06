from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file


def _validate_paths(value: Any, key: str) -> tuple[list[Path], list[str]]:
    reasons: list[str] = []
    raw_paths = value.get(key) if isinstance(value, dict) else None
    if not isinstance(raw_paths, list) or not raw_paths:
        return [], [f"{key} must be a non-empty list"]
    paths: list[Path] = []
    for raw_path in raw_paths:
        if not isinstance(raw_path, str):
            reasons.append(f"{key} entries must be strings")
            continue
        paths.append(Path(raw_path))
    return paths, reasons


def validate(index_path: Path) -> dict[str, object]:
    index = load_yaml_file(index_path)
    manifest_paths, manifest_reasons = _validate_paths(index, "task_manifests")
    change_plan_paths, plan_reasons = _validate_paths(index, "change_plans")

    results: list[dict[str, object]] = []
    reasons = manifest_reasons + plan_reasons

    for manifest_path in manifest_paths:
        result = validate_task_manifest(manifest_path, Path("policy/repo_write_policy.yaml"), Path("policy/autonomy_policy.yaml"))
        results.append({"kind": "task_manifest", **result})
        reasons.extend(str(reason) for reason in result.get("reasons", []))

    for change_plan_path in change_plan_paths:
        result = validate_change_plan(change_plan_path)
        results.append({"kind": "change_plan", **result})
        reasons.extend(str(reason) for reason in result.get("reasons", []))

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "index_path": str(index_path),
        "results": results,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate active tool-system manifests and change plans.")
    parser.add_argument("index", type=Path, default=Path("examples/active_gates.yaml"), nargs="?")
    args = parser.parse_args()

    result = validate(args.index)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
