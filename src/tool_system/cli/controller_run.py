from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.controller_run import run_controller


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the tool-system PR controller.")
    parser.add_argument("repository_full_name")
    parser.add_argument("pr_number", type=int)
    parser.add_argument("--gate-decision", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/controller_audit.jsonl"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--merge-method", default="squash")
    args = parser.parse_args()

    gate_decision = load_yaml_file(args.gate_decision)
    policy = load_yaml_file(args.policy)
    output = run_controller(
        repository_full_name=args.repository_full_name,
        pr_number=args.pr_number,
        gate_decision=gate_decision,
        repo_policy=policy,
        audit_path=args.audit_path,
        dry_run=not args.apply,
        merge_method=args.merge_method,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
