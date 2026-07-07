from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.runner.task_graph_runner import run_task_graph_pipeline
from tool_system.runner.task_runner import run_batch_file, run_task_pipeline


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--active-gates", type=Path, default=Path("examples/active_gates.yaml"))
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--autonomy-policy", type=Path, default=Path("policy/autonomy_policy.yaml"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--skip-commands", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool-system", description="Run tool-system local automation gates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one task manifest and optional change plan.")
    run_parser.add_argument("task_manifest", type=Path)
    run_parser.add_argument("--change-plan", type=Path)
    run_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_runner_audit.jsonl"))
    _add_common_options(run_parser)

    batch_parser = subparsers.add_parser("batch", help="Run multiple task manifest and change-plan pairs.")
    batch_parser.add_argument("batch", type=Path)
    batch_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/batch_runner_audit.jsonl"))
    _add_common_options(batch_parser)

    graph_parser = subparsers.add_parser("graph", help="Run a task graph through the compiled batch runner.")
    graph_parser.add_argument("graph", type=Path)
    graph_parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    graph_parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_graph_runner_audit.jsonl"))
    _add_common_options(graph_parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        output = run_task_pipeline(
            task_manifest_path=args.task_manifest,
            change_plan_path=args.change_plan,
            active_gates_path=args.active_gates,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
            cwd=args.cwd,
            audit_path=args.audit_path,
            execute_commands=not args.skip_commands,
        )
    elif args.command == "batch":
        output = run_batch_file(
            batch_path=args.batch,
            active_gates_path=args.active_gates,
            policy_path=args.policy,
            autonomy_policy_path=args.autonomy_policy,
            cwd=args.cwd,
            audit_path=args.audit_path,
            execute_commands=not args.skip_commands,
        )
    else:
        output = run_task_graph_pipeline(
            graph_path=args.graph,
            blueprint_path=args.blueprint,
            active_gates_path=args.active_gates,
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
