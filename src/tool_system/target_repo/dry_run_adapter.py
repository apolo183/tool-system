from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.gate.change_plan import validate_change_plan_against_manifest, validate_change_plan_structure
from tool_system.manifest.task_manifest import validate_manifest_structure
from tool_system.policy.repo_write_policy import validate_repo_write_policy
from tool_system.repo_controller.artifact import write_jsonl_record


def _refs_for_repo(items: list[dict[str, Any]], target_repo: str) -> list[dict[str, Any]]:
    return [item for item in items if item.get("repo") == target_repo]


def _paths(items: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("path")) for item in items if item.get("path")}


def validate_target_contract_references(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    target_repo = str(manifest.get("target_repo") or "")
    blueprint_refs = _refs_for_repo(manifest.get("approved_blueprint_refs") or [], target_repo)
    evidence_refs = _refs_for_repo(manifest.get("evidence") or [], target_repo)
    evidence_paths = _paths(evidence_refs)
    blueprint_paths = _paths(blueprint_refs)

    if not blueprint_refs:
        reasons.append("target repo blueprint reference is required")
    if "AGENTS.md" not in evidence_paths:
        reasons.append("target repo AGENTS.md evidence is required")
    if not any(path.startswith("blueprint/") for path in blueprint_paths | evidence_paths):
        reasons.append("target repo blueprint evidence is required")
    return not reasons, reasons


def build_target_repo_dry_run_plan(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    reasons: list[str] = []

    manifest_ok, manifest_reasons = validate_manifest_structure(task_manifest)
    policy_ok, policy_reasons = validate_repo_write_policy(task_manifest, repo_policy)
    refs_ok, refs_reasons = validate_target_contract_references(task_manifest)
    if not manifest_ok:
        reasons.extend(manifest_reasons)
    if not policy_ok:
        reasons.extend(policy_reasons)
    if not refs_ok:
        reasons.extend(refs_reasons)

    if change_plan is not None:
        plan_ok, plan_reasons = validate_change_plan_structure(change_plan)
        scope_ok, scope_reasons = validate_change_plan_against_manifest(change_plan, task_manifest)
        if not plan_ok:
            reasons.extend(plan_reasons)
        if not scope_ok:
            reasons.extend(scope_reasons)
        planned_files = list(change_plan.get("changed_files") or [])
    else:
        planned_files = list(task_manifest.get("allowed_files") or [])

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "target_repo_dry_run",
        "target_repo": task_manifest.get("target_repo"),
        "target_branch": task_manifest.get("target_branch"),
        "task_id": task_manifest.get("task_id"),
        "writes_target_repo": False,
        "planned_files": planned_files,
        "proposed_actions": [
            "read_target_contract_refs",
            "validate_target_repo_boundary",
            "prepare_no_write_plan",
            "write_tool_system_audit_artifact",
        ],
        "reasons": reasons,
    }


def build_target_repo_dry_run_record(plan: dict[str, object]) -> dict[str, object]:
    return {
        "status": plan.get("status"),
        "mode": plan.get("mode"),
        "target_repo": plan.get("target_repo"),
        "target_branch": plan.get("target_branch"),
        "task_id": plan.get("task_id"),
        "writes_target_repo": False,
        "planned_files": plan.get("planned_files", []),
        "proposed_actions": plan.get("proposed_actions", []),
        "reasons": plan.get("reasons", []),
    }


def run_target_repo_dry_run(
    task_manifest: dict[str, Any],
    repo_policy: dict[str, Any],
    audit_path: str | Path,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    plan = build_target_repo_dry_run_plan(
        task_manifest=task_manifest,
        repo_policy=repo_policy,
        change_plan=change_plan,
    )
    record = build_target_repo_dry_run_record(plan)
    artifact_path = write_jsonl_record(audit_path, record)
    return {**plan, "audit_path": str(artifact_path)}
