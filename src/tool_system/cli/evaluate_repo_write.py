from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.audit_log import build_audit_record
from tool_system.repo_controller.controller import evaluate_repo_write


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate whether a PR can be merged by tool-system.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--task-manifest", type=Path, required=True)
    parser.add_argument("--change-plan", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    args = parser.parse_args()

    value = load_yaml_file(args.input)
    policy = load_yaml_file(args.policy)
    task_manifest = load_yaml_file(args.task_manifest)
    change_plan = load_yaml_file(args.change_plan)
    decision = evaluate_repo_write(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        status_checks=value["status_checks"],
        merge_method=value.get("merge_method", "squash"),
        task_manifest=task_manifest,
        change_plan=change_plan,
    )
    audit_record = build_audit_record(
        pull_request=value["pull_request"],
        decision=decision,
        rollback=value.get("rollback", {}),
    )
    output = {"decision": decision, "audit_record": audit_record}
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
