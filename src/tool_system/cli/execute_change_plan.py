from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.gate.command_runner import run_commands


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Execute commands only from an explicit manifest/change-plan pair "
            "after protected process-authority and policy preflight."
        )
    )
    parser.add_argument("task_manifest", type=Path)
    parser.add_argument("change_plan", type=Path)
    parser.add_argument("--process-authority", type=Path, required=True)
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("policy/repo_write_policy.yaml"),
    )
    parser.add_argument(
        "--autonomy-policy",
        type=Path,
        default=Path("policy/autonomy_policy.yaml"),
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args(argv)

    result = run_commands(
        task_manifest_path=args.task_manifest,
        change_plan_path=args.change_plan,
        process_authority_path=args.process_authority,
        policy_path=args.policy,
        autonomy_policy_path=args.autonomy_policy,
        cwd=args.cwd,
        timeout_seconds=args.timeout_seconds,
    )
    output = {
        **result,
        "task_manifest_path": str(args.task_manifest),
        "change_plan_path": str(args.change_plan),
        "process_authority_path": str(args.process_authority),
        "policy_path": str(args.policy),
        "autonomy_policy_path": str(args.autonomy_policy),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
