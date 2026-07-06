from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.state_collector import build_state_collector_record


def _plan_id(task_id: object, target_repo: object, target_branch: object, base_sha: object) -> str:
    return "::".join(str(value or "unknown") for value in (task_id, target_repo, target_branch, base_sha))


def build_p5h_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    collector = build_state_collector_record(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        observed_state=observed_state,
        change_plan=change_plan,
    )
    reasons = list(collector.get("reasons") or [])
    if collector.get("status") != "PASS" or not collector.get("collector_ready"):
        reasons.append("passing target repo state collector is required")
    status = "PASS" if not reasons else "BLOCK"
    snapshot = dict(collector.get("state_snapshot") or {})
    commands = list((dict((collector.get("snapshot_gate") or {})).get("command_packet") or {}).get("commands") or [])
    final_plan = {
        "plan_id": _plan_id(
            collector.get("task_id"),
            collector.get("target_repo"),
            collector.get("target_branch"),
            snapshot.get("base_commit_sha"),
        ),
        "dry_run": True,
        "execute": False,
        "target_repo": collector.get("target_repo"),
        "target_branch": collector.get("target_branch"),
        "task_id": collector.get("task_id"),
        "base_commit_sha": snapshot.get("base_commit_sha"),
        "default_branch_head_sha": snapshot.get("default_branch_head_sha"),
        "expected_file_states": snapshot.get("file_states", {}),
        "commands": commands,
    }
    return {
        "status": status,
        "mode": "target_repo_p5h_final_plan_record",
        "target_repo": collector.get("target_repo"),
        "target_branch": collector.get("target_branch"),
        "task_id": collector.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_explicit_execution_request": status == "PASS",
        "collector": collector,
        "final_plan": final_plan if status == "PASS" else {},
        "next_step_contract": {
            "may_execute_target_repo_mutation": False,
            "requires_new_explicit_execution_request": True,
            "requires_state_sha_match_before_execution": True,
            "direct_main_branch_write_allowed": False,
        },
        "reasons": reasons,
    }


def run_p5h_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    record = build_p5h_record(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        observed_state=observed_state,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
