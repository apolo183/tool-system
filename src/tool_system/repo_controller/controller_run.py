from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.actions import build_action_plan, execute_action_plan, run_gh
from tool_system.repo_controller.artifact import build_controller_record, write_jsonl_record
from tool_system.repo_controller.live_github_collector import evaluate_live_pull_request, run_gh_json


def run_controller(
    repository_full_name: str,
    pr_number: int,
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    dry_run: bool = True,
    merge_method: str = "squash",
    collector_runner=run_gh_json,
    action_runner=run_gh,
) -> dict[str, object]:
    evaluation = evaluate_live_pull_request(
        repository_full_name=repository_full_name,
        pr_number=pr_number,
        gate_decision=gate_decision,
        repo_policy=repo_policy,
        runner=collector_runner,
        merge_method=merge_method,
    )
    action_plan = build_action_plan(
        decision=evaluation["decision"],
        pull_request=evaluation["snapshot"]["pull_request"],
    )
    action_result = execute_action_plan(
        repository_full_name=repository_full_name,
        plan=action_plan,
        runner=action_runner,
        dry_run=dry_run,
    )
    record = build_controller_record(
        repository_full_name=repository_full_name,
        pr_number=pr_number,
        evaluation=evaluation,
        action_plan=action_plan,
        action_result=action_result,
        dry_run=dry_run,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    status = "PASS" if evaluation["decision"]["status"] == "PASS" and action_result["status"] == "PASS" else "BLOCK"
    reasons = []
    reasons.extend(evaluation["decision"].get("reasons", []))
    reasons.extend(action_result.get("reasons", []))
    return {
        "status": status,
        "decision": evaluation["decision"],
        "action_plan": action_plan,
        "action_result": action_result,
        "audit_path": str(artifact_path),
        "rollback": record.get("rollback", {}),
        "reasons": reasons,
    }
