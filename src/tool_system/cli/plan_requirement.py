from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.planner.requirement_graph import compile_requirement_file_to_task_graph, write_requirement_task_graph_file
from tool_system.repo_controller.artifact import write_jsonl_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a structured requirement into a task graph.")
    parser.add_argument("requirement", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    parser.add_argument("--graph-output", type=Path)
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/requirement_graph_audit.jsonl"))
    args = parser.parse_args()

    if args.graph_output is not None:
        output = write_requirement_task_graph_file(args.requirement, args.graph_output, args.blueprint)
    else:
        output = compile_requirement_file_to_task_graph(args.requirement, args.blueprint)
    artifact_path = write_jsonl_record(args.audit_path, output)
    output = {**output, "audit_path": str(artifact_path)}
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
