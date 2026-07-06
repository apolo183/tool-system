from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.dry_run_adapter import build_target_repo_dry_run_plan


def _verification_commands(task_manifest: dict[str, Any], change_plan: dict[str, Any] | None) -> list[str]:
    if change_plan is not None:
        commands = (change_plan.get("verification") or {}).get("commands") or []
        if commands:
            return [str(command) for command in commands]
    return [str(command) for command in (task_manifest.get("verification") or {}).get("commands") or []]


def _rollback(task_manifest: dict[str, Any], change_plan: dict[str, Any] | None) -> dict[str, Any]:
    if change_plan is not None and isinstance(change_plan.get("rollback"), dict):
        return dict(change_plan["rollback"])
    return dict(task_manifest.get("rollback") or {})


def _pr_title(task_manifest: dict[str, Any]) -> str:
    summary = ((task_manifest.get("scope") or {}).get("summary") or "").strip()
    task_id = str(task_manifest.get("task_id") or "target-repo-change")
    return summary or task_id.replace("-", " ").title()


def build_target_repo_pr_plan_preview(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    dry_run_plan = build_target_repo_dry_run_plan(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    planned_files = list(dry_run_plan.get("planned_files") or [])
    target_repo = task_manifest.get("target_repo")
    target_branch = task_manifest.get("target_branch")
    task_id = task_manifest.get("task_id")
    preview = {
        "branch_name": target_branch,
        "title": _pr_title(task_manifest),
        "body_summary": (task_manifest.get("scope") or {}).get("summary"),
        "changed_files": planned_files,
        "verification_commands": _verification_commands(task_manifest, change_plan),
        "rollback": _rollback(task_manifest, change_plan),
    }
    return {
        "status": dry_run_plan.get("status"),
        "mode": "target_repo_pr_plan_preview",
        "target_repo": target_repo,
        "target_branch": target_branch,
        "task_id": task_id,
        "writes_target_repo": False,
        "dry_run_plan": dry_run_plan,
        "pr_preview": preview,
        "reasons": list(dry_run_plan.get("reasons") or []),
    }


def build_target_repo_pr_preview_record(preview: dict[str, object]) -> dict[str, object]:
    return {
        "status": preview.get("status"),
        "mode": preview.get("mode"),
        "target_repo": preview.get("target_repo"),
        "target_branch": preview.get("target_branch"),
        "task_id": preview.get("task_id"),
        "writes_target_repo": False,
        "pr_preview": preview.get("pr_preview", {}),
        "reasons": preview.get("reasons", []),
    }


def run_target_repo_pr_plan_preview(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    preview = build_target_repo_pr_plan_preview(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    record = build_target_repo_pr_preview_record(preview)
    artifact_path = write_jsonl_record(audit_path, record)
    return {**preview, "audit_path": str(artifact_path)}
