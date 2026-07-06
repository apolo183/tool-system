from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.dry_run_adapter import build_target_repo_dry_run_plan
from tool_system.target_repo.p4c_preview_module import build_p4c_preview
from tool_system.target_repo.pr_plan_preview import build_target_repo_pr_plan_preview


def _approval_ok(target_repo: object, approvals: dict[str, Any] | None) -> bool:
    if target_repo != "apolo183/finance-os":
        return True
    if not approvals:
        return False
    return bool(approvals.get("target_repo_approved"))


def _nested_writes_target_repo(*items: dict[str, object]) -> bool:
    return any(bool(item.get("writes_target_repo")) for item in items)


def build_p4d_precheck(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    dry_run = build_target_repo_dry_run_plan(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    pr_preview = build_target_repo_pr_plan_preview(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    action_preview = build_p4c_preview(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )

    target_repo = task_manifest.get("target_repo")
    reasons: list[str] = []
    if dry_run.get("status") != "PASS":
        reasons.append("passing dry-run is required")
    if pr_preview.get("status") != "PASS":
        reasons.append("passing PR preview is required")
    if action_preview.get("status") != "PASS":
        reasons.append("passing action-plan preview is required")
    if _nested_writes_target_repo(dry_run, pr_preview, action_preview):
        reasons.append("precheck inputs must not write target repo")
    if not _approval_ok(target_repo, approvals):
        reasons.append(f"explicit target repo approval is required for {target_repo}")

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "target_repo_precheck",
        "target_repo": target_repo,
        "target_branch": task_manifest.get("target_branch"),
        "task_id": task_manifest.get("task_id"),
        "writes_target_repo": False,
        "approvals": approvals or {},
        "required_gates": {
            "dry_run_status": dry_run.get("status"),
            "pr_preview_status": pr_preview.get("status"),
            "action_preview_status": action_preview.get("status"),
            "target_repo_approval": _approval_ok(target_repo, approvals),
        },
        "dry_run_plan": dry_run,
        "pr_preview": pr_preview.get("pr_preview", {}),
        "action_plan": action_preview.get("action_plan", {}),
        "reasons": reasons,
    }


def build_p4d_record(precheck: dict[str, object]) -> dict[str, object]:
    return {
        "status": precheck.get("status"),
        "mode": precheck.get("mode"),
        "target_repo": precheck.get("target_repo"),
        "target_branch": precheck.get("target_branch"),
        "task_id": precheck.get("task_id"),
        "writes_target_repo": False,
        "approvals": precheck.get("approvals", {}),
        "required_gates": precheck.get("required_gates", {}),
        "reasons": precheck.get("reasons", []),
    }


def run_p4d_precheck(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    approvals: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    precheck = build_p4d_precheck(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        approvals=approvals,
        change_plan=change_plan,
    )
    artifact_path = write_jsonl_record(audit_path, build_p4d_record(precheck))
    return {**precheck, "audit_path": str(artifact_path)}
