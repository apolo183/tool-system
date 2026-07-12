from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.runner.task_graph_runner import run_task_graph_pipeline


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a validated task graph through the compiled batch runner.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--autonomy-policy", type=Path, default=Path("policy/autonomy_policy.yaml"))
    parser.add_argument(
        "--process-authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
    )
    parser.add_argument(
        "--active-gates",
        type=Path,
        help="Legacy replay-only pair index; never authorizes command execution.",
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_graph_runner_audit.jsonl"))
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args(argv)

    output = run_task_graph_pipeline(
        graph_path=args.graph,
        blueprint_path=args.blueprint,
        policy_path=args.policy,
        autonomy_policy_path=args.autonomy_policy,
        process_authority_path=args.process_authority,
        active_gates_path=args.active_gates,
        cwd=args.cwd,
        audit_path=args.audit_path,
        execute_commands=not args.skip_commands,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
