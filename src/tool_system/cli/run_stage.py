from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tool_system.runner.stage_runner import run_stage_pipeline


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a structured input through graph compilation and batch execution.")
    parser.add_argument("input_spec", type=Path)
    parser.add_argument("--blueprint", type=Path, default=Path("blueprint/tool_system_v0.yaml"))
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--autonomy-policy", type=Path, default=Path("policy/autonomy_policy.yaml"))
    parser.add_argument("--active-gates", type=Path, default=Path("examples/active_gates.yaml"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/stage_runner_audit.jsonl"))
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args(argv)

    output = run_stage_pipeline(
        input_path=args.input_spec,
        blueprint_path=args.blueprint,
        policy_path=args.policy,
        autonomy_policy_path=args.autonomy_policy,
        active_gates_path=args.active_gates,
        cwd=args.cwd,
        audit_path=args.audit_path,
        execute_commands=not args.skip_commands,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
