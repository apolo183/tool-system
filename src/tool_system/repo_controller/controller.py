from __future__ import annotations

from typing import Any

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


def evaluate_repo_write(
    pull_request: dict[str, Any],
    gate_decision: dict[str, Any],
    repo_policy: dict[str, Any],
    status_checks: list[dict[str, Any]],
    merge_method: str = "squash",
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
    if merge_policy.get("system_merge_allowed_after_gates_pass") is not True:
        reasons.append("system merge is not allowed by policy")
    if merge_policy.get("human_review_required_before_regular_merge") is True:
        reasons.append("policy requires human review before regular merge")
    if not _is_allowed_merge_method(repo_policy, merge_method):
        reasons.append(f"merge method must be {merge_policy.get('default_method', 'squash')}")

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "merge_method": merge_method,
        "reasons": reasons,
    }
