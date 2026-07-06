from __future__ import annotations

from typing import Any

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "policy",
    "status",
    "authorization_model",
    "human_review_required_for",
    "system_handled_when_manifest_allows",
    "gates_before_system_merge",
}

REQUIRED_HUMAN_REVIEW_ITEMS = {
    "blueprint_change",
    "objective_change",
    "milestone_acceptance",
    "policy_boundary_change",
}

REQUIRED_SYSTEM_ITEMS = {
    "code_add",
    "code_modify",
    "file_cleanup",
    "file_swap",
    "test_add",
    "test_modify",
    "docs_update",
    "local_verification",
    "pr_create",
    "pr_ready",
    "pr_merge",
}

REQUIRED_GATES = {
    "task_manifest_valid",
    "repo_write_policy_pass",
    "allowed_files_respected",
    "verification_commands_pass",
    "rollback_plan_present",
}


def _missing_items(value: Any, required_items: set[str]) -> list[str]:
    if not isinstance(value, list):
        return sorted(required_items)
    return sorted(required_items - set(value))


def validate_autonomy_policy(policy: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - set(policy))
    if missing_keys:
        reasons.append("missing autonomy policy keys: " + ", ".join(missing_keys))

    if policy.get("policy") != "autonomy_policy":
        reasons.append("policy must be autonomy_policy")
    if policy.get("status") != "active":
        reasons.append("autonomy_policy.status must be active")

    authorization = policy.get("authorization_model")
    if not isinstance(authorization, dict):
        reasons.append("authorization_model must be a mapping")
    else:
        if authorization.get("level") != "milestone_authorization":
            reasons.append("authorization_model.level must be milestone_authorization")
        if authorization.get("per_task_human_review_required") is not False:
            reasons.append("per_task_human_review_required must be false")
        if authorization.get("per_pr_human_review_required") is not False:
            reasons.append("per_pr_human_review_required must be false")
        if authorization.get("milestone_result_human_review_required") is not True:
            reasons.append("milestone_result_human_review_required must be true")

    missing_human_items = _missing_items(policy.get("human_review_required_for"), REQUIRED_HUMAN_REVIEW_ITEMS)
    if missing_human_items:
        reasons.append("missing human review items: " + ", ".join(missing_human_items))

    missing_system_items = _missing_items(policy.get("system_handled_when_manifest_allows"), REQUIRED_SYSTEM_ITEMS)
    if missing_system_items:
        reasons.append("missing system handled items: " + ", ".join(missing_system_items))

    missing_gates = _missing_items(policy.get("gates_before_system_merge"), REQUIRED_GATES)
    if missing_gates:
        reasons.append("missing merge gates: " + ", ".join(missing_gates))

    return not reasons, reasons
