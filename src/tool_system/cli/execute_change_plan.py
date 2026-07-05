from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.gate.command_runner import commands_from_change_plan, run_commands
from tool_system.gate.test_gate import build_gate_decision
from tool_system.manifest.task_manifest import load_yaml_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate commands from a tool-system change plan.")
    parser.add_argument("change_plan", type=Path)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()

    plan = load_yaml_file(args.change_plan)
    results = run_commands(commands_from_change_plan(plan), cwd=args.cwd)
    decision = build_gate_decision(plan_ok=True, plan_reasons=[], command_results=results)
    output = {
        "status": decision["status"],
        "change_plan_path": str(args.change_plan),
        "results": results,
        "reasons": decision["reasons"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
