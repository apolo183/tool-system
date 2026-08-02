from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runtime.agent_scheduler import build_agent_execution_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a role-assigned agent execution plan from a task graph.")
    parser.add_argument("task_graph", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    args = parser.parse_args()

    output = build_agent_execution_plan(
        load_yaml_file(args.task_graph),
        load_yaml_file(args.blueprint),
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
