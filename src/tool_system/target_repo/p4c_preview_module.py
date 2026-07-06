from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.target_repo.pr_plan_preview import build_target_repo_pr_plan_preview


def _file_steps(target_repo: object, planned_files: list[str]) -> list[dict[str, object]]:
    return [
        {
            "step": "file_change_preview",
            "repository_full_name": target_repo,
            "path": path,
            "operation": "create_or_update",
            "dry_run": True,
        }
        for path in planned_files
    ]


def build_p4c_preview(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    preview = build_target_repo_pr_plan_preview(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    pr_preview = dict(preview.get("pr_preview") or {})
    target_repo = preview.get("target_repo")
    branch_name = pr_preview.get("branch_name")
    changed_files = [str(path) for path in pr_preview.get("changed_files") or []]
    steps: list[dict[str, object]] = []
    if preview.get("status") == "PASS":
        steps.append(
            {
                "step": "branch_preview",
                "repository_full_name": target_repo,
                "branch_name": branch_name,
                "base_ref": "main",
                "dry_run": True,
            }
        )
        steps.extend(_file_steps(target_repo, changed_files))
        steps.append(
            {
                "step": "pull_request_preview",
                "repository_full_name": target_repo,
                "head": branch_name,
                "base": "main",
                "title": pr_preview.get("title"),
                "body_summary": pr_preview.get("body_summary"),
                "dry_run": True,
            }
        )

    action_plan = {
        "status": preview.get("status"),
        "dry_run": True,
        "steps": steps,
    }
    return {
        "status": preview.get("status"),
        "mode": "target_repo_branch_pr_preview",
        "target_repo": preview.get("target_repo"),
        "target_branch": preview.get("target_branch"),
        "task_id": preview.get("task_id"),
        "writes_target_repo": False,
        "pr_preview": pr_preview,
        "action_plan": action_plan,
        "reasons": list(preview.get("reasons") or []),
    }


def build_p4c_record(plan: dict[str, object]) -> dict[str, object]:
    return {
        "status": plan.get("status"),
        "mode": plan.get("mode"),
        "target_repo": plan.get("target_repo"),
        "target_branch": plan.get("target_branch"),
        "task_id": plan.get("task_id"),
        "writes_target_repo": False,
        "pr_preview": plan.get("pr_preview", {}),
        "action_plan": plan.get("action_plan", {}),
        "reasons": plan.get("reasons", []),
    }


def run_p4c_preview(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    plan = build_p4c_preview(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    record = build_p4c_record(plan)
    artifact_path = write_jsonl_record(audit_path, record)
    return {**plan, "audit_path": str(artifact_path)}
