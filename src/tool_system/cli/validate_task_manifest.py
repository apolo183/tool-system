from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file, validate_manifest_structure
from tool_system.policy import repo_write_policy as policy_module


def validate(manifest_path: Path, policy_path: Path) -> dict[str, object]:
    manifest = load_yaml_file(manifest_path)
    policy = load_yaml_file(policy_path)
    structure_ok, structure_reasons = validate_manifest_structure(manifest)
    policy_ok, policy_reasons = policy_module.validate_repo_write_policy(manifest, policy)
    reasons = structure_reasons + policy_reasons
    return {
        "status": "PASS" if structure_ok and policy_ok else "BLOCK",
        "manifest_path": str(manifest_path),
        "policy_path": str(policy_path),
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a tool-system task manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    args = parser.parse_args()
    result = validate(args.manifest, args.policy)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
