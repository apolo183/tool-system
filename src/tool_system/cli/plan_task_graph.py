from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.planner.task_graph import (
    validate_task_graph_active_gates_file,
    validate_task_graph_file,
    validate_task_graph_process_authority_file,
    write_task_graph_batch_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and order a tool-system task graph.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    parser.add_argument("--active-gates", type=Path, default=Path("examples/active_gates.yaml"))
    parser.add_argument(
        "--process-authority",
        type=Path,
        default=Path("config/process_authority_v1.yaml"),
    )
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/task_graph_audit.jsonl"))
    parser.add_argument("--batch-output", type=Path)
    parser.add_argument("--require-active-gates", action="store_true")
    parser.add_argument("--require-process-authority", action="store_true")
    args = parser.parse_args()

    if args.batch_output is not None:
        output = write_task_graph_batch_file(args.graph, args.batch_output, args.blueprint)
    elif args.require_active_gates:
        output = validate_task_graph_active_gates_file(args.graph, args.blueprint, args.active_gates)
    elif args.require_process_authority:
        output = validate_task_graph_process_authority_file(
            args.graph,
            args.blueprint,
            args.process_authority,
        )
    else:
        output = validate_task_graph_file(args.graph, args.blueprint)
    artifact_path = write_jsonl_record(args.audit_path, output)
    output = {**output, "audit_path": str(artifact_path)}
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
