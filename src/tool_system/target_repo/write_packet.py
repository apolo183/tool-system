from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.p4d_precheck import build_p4d_precheck


def _preview_payload(precheck: dict[str, object]) -> dict[str, object]:
    pr_preview = dict(precheck.get("pr_preview") or {})
    action_plan = dict(precheck.get("action_plan") or {})
    return {
        "branch_name": pr_preview.get("branch_name"),
        "title": pr_preview.get("title"),
        "body_summary": pr_preview.get("body_summary"),
        "changed_files": list(pr_preview.get("changed_files") or []),
        "verification_commands": list(pr_preview.get("verification_commands") or []),
        "rollback": dict(pr_preview.get("rollback") or {}),
        "action_steps": list(action_plan.get("steps") or []),
    }


def build_write_packet(
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
    reasons = list(precheck.get("reasons") or [])
    status = "PASS" if precheck.get("status") == "PASS" else "BLOCK"
    return {
        "status": status,
        "mode": "target_repo_write_packet",
        "target_repo": precheck.get("target_repo"),
        "target_branch": precheck.get("target_branch"),
        "task_id": precheck.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "ready_for_execution": status == "PASS",
        "execution_requires": [
            "separate target repository execution approval",
            "fresh target repository state collection",
            "target repository branch write through approved connector or local git workflow",
        ],
        "required_gates": precheck.get("required_gates", {}),
        "approvals": precheck.get("approvals", {}),
        "write_packet": _preview_payload(precheck) if status == "PASS" else {},
        "reasons": reasons,
    }


def run_write_packet(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    packet = build_write_packet(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, packet)
    return {**packet, "audit_path": str(artifact_path)}
