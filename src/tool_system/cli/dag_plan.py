from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.dag_planner import compile_blueprint_dag, validate_dag


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a blueprint milestone into a deterministic DAG.")
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("milestone")
    args = parser.parse_args()

    dag = compile_blueprint_dag(load_yaml_file(args.blueprint), args.milestone)
    result = validate_dag(dag)
    output = {**dag, "validation": result}
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
