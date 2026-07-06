from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.runner.task_runner import run_task_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tool-system task manifest and optional change plan through one local gate pipeline.")
    parser.add_argument("task_manifest", type=Path)
    parser.add_argument("--change-plan", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--autonomy-policy", type=Path, default=Path("policy/autonomy_policy.yaml"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_runner_audit.jsonl"))
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args()

    output = run_task_pipeline(
        task_manifest_path=args.task_manifest,
        change_plan_path=args.change_plan,
        policy_path=args.policy,
        autonomy_policy_path=args.autonomy_policy,
        cwd=args.cwd,
        audit_path=args.audit_path,
        execute_commands=not args.skip_commands,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
