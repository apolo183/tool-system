from __future__ import annotations

import argparse
import json
from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repo_controller.github_state import evaluate_github_state


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate repo write readiness from GitHub state snapshots.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--task-manifest", type=Path, required=True)
    parser.add_argument("--change-plan", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policy/repo_write_policy.yaml"))
    args = parser.parse_args()

    value = load_yaml_file(args.input)
    policy = load_yaml_file(args.policy)
    task_manifest = load_yaml_file(args.task_manifest)
    change_plan = load_yaml_file(args.change_plan)
    output = evaluate_github_state(
        pull_request=value["pull_request"],
        gate_decision=value["gate_decision"],
        repo_policy=policy,
        workflow_runs=value.get("workflow_runs"),
        workflow_jobs=value.get("workflow_jobs"),
        rollback=value.get("rollback", {}),
        merge_method=value.get("merge_method", "squash"),
        repository_full_name=value.get("repository_full_name"),
        task_manifest=task_manifest,
        change_plan=change_plan,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["decision"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
