from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.write_packet import build_write_packet


def _execution_approval_ok(approvals: dict[str, Any] | None) -> bool:
    return bool((approvals or {}).get("target_repo_execution_approved"))


def build_execution_approval_gate(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    packet = build_write_packet(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    reasons = list(packet.get("reasons") or [])
    if packet.get("status") != "PASS" or not packet.get("ready_for_execution"):
        reasons.append("approved write packet is required")
    if not _execution_approval_ok(approvals):
        reasons.append("separate target repository execution approval is required")

    status = "PASS" if not reasons else "BLOCK"
    return {
        "status": status,
        "mode": "target_repo_execution_approval_gate",
        "target_repo": packet.get("target_repo"),
        "target_branch": packet.get("target_branch"),
        "task_id": packet.get("task_id"),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "execution_approved": _execution_approval_ok(approvals),
        "approved_for_next_step": status == "PASS",
        "required_gates": packet.get("required_gates", {}),
        "approvals": approvals or {},
        "write_packet": packet.get("write_packet", {}),
        "next_step_contract": {
            "may_request_target_repo_mutation": status == "PASS",
            "mutation_must_be_separate_step": True,
            "direct_main_branch_write_allowed": False,
        },
        "reasons": reasons,
    }


def run_execution_approval_gate(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    gate = build_execution_approval_gate(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, gate)
    return {**gate, "audit_path": str(artifact_path)}
