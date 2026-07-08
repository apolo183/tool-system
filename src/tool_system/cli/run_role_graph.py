from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.runtime.role_runtime import build_role_runtime_plan_file


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a no-mutation role runtime plan from a task graph.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    parser.add_argument("--active-gates", type=Path, default=Path("examples/active_gates.yaml"))
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/role_runtime_audit.jsonl"))
    args = parser.parse_args(argv)

    output = build_role_runtime_plan_file(
        graph_path=args.graph,
        blueprint_path=args.blueprint,
        active_gates_path=args.active_gates,
        audit_path=args.audit_path,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
