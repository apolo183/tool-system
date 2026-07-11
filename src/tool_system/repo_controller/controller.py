from __future__ import annotations

from typing import Any

from tool_system.gate.change_plan import (
    validate_change_plan_against_manifest,
    validate_change_plan_structure,
)
from tool_system.manifest.task_manifest import validate_manifest_structure
from tool_system.policy.repo_write_policy import (
    validate_lifecycle_approval,
    validate_repo_write_policy,
)

PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}


def _all_checks_pass(status_checks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not status_checks:
        return False, ["status checks must be non-empty"]

    for check in status_checks:
        name = str(check.get("name") or check.get("context") or "unnamed-check")
        status = check.get("status")
        conclusion = check.get("conclusion")
        if status != "completed":
            reasons.append(f"{name} status is {status}")
            continue
        if conclusion not in PASSING_CONCLUSIONS:
            reasons.append(f"{name} conclusion is {conclusion}")
    return not reasons, reasons


def _is_allowed_merge_method(policy: dict[str, Any], merge_method: str) -> bool:
    merge_policy = policy.get("merge_policy") or {}
    default_method = merge_policy.get("default_method", "squash")
    return merge_method == default_method


def _validate_controller_context(
    task_manifest: dict[str, Any] | None,
    change_plan: dict[str, Any] | None,
    repo_policy: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if task_manifest is None:
        reasons.append("task manifest is required for repo write decision")
    if change_plan is None:
        reasons.append("change plan is required for repo write decision")
    if task_manifest is None or change_plan is None:
        return reasons

    manifest_ok, manifest_reasons = validate_manifest_structure(task_manifest)
    policy_ok, policy_reasons = validate_repo_write_policy(task_manifest, repo_policy)
    plan_structure_ok, plan_structure_reasons = validate_change_plan_structure(change_plan)
    plan_scope_ok, plan_scope_reasons = validate_change_plan_against_manifest(change_plan, task_manifest)

    if not manifest_ok:
        reasons.extend(manifest_reasons)
    if not policy_ok:
        reasons.extend(policy_reasons)
    if not plan_structure_ok:
        reasons.extend(plan_structure_reasons)
    if not plan_scope_ok:
        reasons.extend(plan_scope_reasons)
    if not task_manifest.get("rollback"):
        reasons.append("task manifest rollback is required")
    if not change_plan.get("rollback"):
        reasons.append("change plan rollback is required")
    return reasons


def evaluate_repo_write(
    pull_request: dict[str, Any],
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    status_checks: list[dict[str, Any]],
    merge_method: str = "squash",
    task_manifest: dict[str, Any] | None = None,
    change_plan: dict[str, Any] | None = None,
) -> dict[str, object]:
    reasons: list[str] = []

    if pull_request.get("state") != "open":
        reasons.append("pull request must be open")
    if pull_request.get("draft") is True:
        reasons.append("pull request must not be draft")
    if pull_request.get("mergeable") is not True:
        reasons.append("pull request must be mergeable")
    if gate_decision.get("status") != "PASS":
        reasons.append("gate decision must be PASS")
        reasons.extend(str(reason) for reason in gate_decision.get("reasons", []))

    checks_ok, check_reasons = _all_checks_pass(status_checks)
    if not checks_ok:
        reasons.extend(check_reasons)

    merge_policy = repo_policy.get("merge_policy") or {}
    if repo_policy.get("status") != "active":
        reasons.append("repo_write_policy.status must be active")
    if merge_policy.get("system_merge_allowed_after_gates_pass") is not True:
        reasons.append("system merge is not allowed by policy")
    if merge_policy.get("human_review_required_before_regular_merge") is True:
        reasons.append("policy requires human review before regular merge")
    if not _is_allowed_merge_method(repo_policy, merge_method):
        reasons.append(f"merge method must be {merge_policy.get('default_method', 'squash')}")

    reasons.extend(_validate_controller_context(task_manifest, change_plan, repo_policy))
    if task_manifest is not None:
        _, lifecycle_reasons = validate_lifecycle_approval(
            task_manifest,
            repo_policy,
            action="pr_merge",
            repository_full_name=pull_request.get("repository"),
            base_branch=pull_request.get("base"),
            expected_head_sha=pull_request.get("head_sha"),
        )
        reasons.extend(lifecycle_reasons)

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "merge_method": merge_method,
        "reasons": reasons,
    }
