from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.p5h_record import build_p5h_record


def _file_count(final_plan: dict[str, object]) -> int:
    states = final_plan.get("expected_file_states")
    return len(states) if isinstance(states, dict) else 0


def build_p5i_bundle(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    final_record = build_p5h_record(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        observed_state=observed_state,
        change_plan=change_plan,
    )
    reasons = list(final_record.get("reasons") or [])
    if final_record.get("status") != "PASS" or not final_record.get("ready_for_explicit_execution_request"):
        reasons.append("passing final plan record is required")
    status = "PASS" if not reasons else "BLOCK"
    final_plan = dict(final_record.get("final_plan") or {})
    bundle = {
        "dry_run": True,
        "execute": False,
        "target_repo": final_record.get("target_repo"),
        "target_branch": final_record.get("target_branch"),
        "task_id": final_record.get("task_id"),
        "base_commit_sha": final_plan.get("base_commit_sha"),
        "planned_file_count": _file_count(final_plan),
        "restore_steps": [
            {"step": "close_future_pr_if_open", "execute": False},
            {"step": "remove_future_branch_if_created", "execute": False},
            {"step": "revert_future_merge_if_merged", "execute": False},
        ],
        "evidence_refs": {
            "final_plan_id": final_plan.get("plan_id"),
            "default_branch_head_sha": final_plan.get("default_branch_head_sha"),
        },
    }
    return {
        "status": status,
        "mode": "target_repo_p5i_audit_bundle",
        "target_repo": final_record.get("target_repo"),
        "target_branch": final_record.get("target_branch"),
        "task_id": final_record.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_milestone_review": status == "PASS",
        "final_record": final_record,
        "audit_bundle": bundle if status == "PASS" else {},
        "reasons": reasons,
    }


def run_p5i_bundle(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    observed_state: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    record = build_p5i_bundle(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        observed_state=observed_state,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
