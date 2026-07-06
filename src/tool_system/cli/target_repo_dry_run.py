from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.target_repo.dry_run_adapter import run_target_repo_dry_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run target repository dry-run validation without writing the target repo.")
    parser.add_argument("task_manifest", type=Path)
    parser.add_argument("--change-plan", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/target_repo_dry_run.jsonl"))
    args = parser.parse_args()

    task_manifest = load_yaml_file(args.task_manifest)
    repo_policy = load_yaml_file(args.policy)
    change_plan = load_yaml_file(args.change_plan) if args.change_plan else None
    output = run_target_repo_dry_run(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
        audit_path=args.audit_path,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
