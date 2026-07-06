from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.p4d_precheck import build_p4d_precheck


def build_write_intent_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    precheck = build_p4d_precheck(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    intent_status = "APPROVED" if precheck.get("status") == "PASS" else "BLOCKED"
    return {
        "status": precheck.get("status"),
        "mode": "target_repo_write_intent",
        "intent_status": intent_status,
        "target_repo": precheck.get("target_repo"),
        "target_branch": precheck.get("target_branch"),
        "task_id": precheck.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "precheck_status": precheck.get("status"),
        "required_gates": precheck.get("required_gates", {}),
        "approvals": precheck.get("approvals", {}),
        "planned_intent": {
            "kind": "target_repo_pull_request_write",
            "execute": False,
            "requires_separate_execution_step": True,
        },
        "reasons": precheck.get("reasons", []),
    }


def run_write_intent_record(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    record = build_write_intent_record(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, record)
    return {**record, "audit_path": str(artifact_path)}
