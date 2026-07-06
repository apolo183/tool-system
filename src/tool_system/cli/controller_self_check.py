from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.self_check import run_self_check


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a dry-run controller self-check for a pull request.")
    parser.add_argument("--repo", dest="repository_full_name")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--github-event-path", type=Path)
    parser.add_argument("--gate-decision", type=Path, default=Path("examples/gate_decisions/pass.yaml"))
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    parser.add_argument("--audit-path", type=Path, default=Path("artifacts/controller_self_check.jsonl"))
    args = parser.parse_args()

    gate_decision = load_yaml_file(args.gate_decision)
    policy = load_yaml_file(args.policy)
    output = run_self_check(
        repository_full_name=args.repository_full_name,
        pr_number=args.pr_number,
        event_path=args.github_event_path,
        gate_decision=gate_decision,
        repo_policy=policy,
        audit_path=args.audit_path,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
