from __future__ import annotations

import hashlib
import json
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
REQUIRED_STATUS_CHECK_FIELDS = frozenset({"name", "source_app"})
LIFECYCLE_APPROVAL_FIELDS = frozenset({
    "required",
    "approved_by",
    "approval_source",
    "approved_at",
    "approval_record_id",
    "repository_full_name",
    "pull_request_number",
    "action",
    "base_branch",
    "expected_head_sha",
    "approval_record_or_reason",
})


def _required_status_check_bindings(
    repo_policy: dict[str, Any],
    repository_full_name: object,
) -> tuple[list[tuple[str, str]], list[str]]:
    if not isinstance(repository_full_name, str) or not repository_full_name:
        return [], ["pull request repository is required for status check policy"]

    repositories = repo_policy.get("allowed_target_repos")
    repository_rules = (
        repositories.get(repository_full_name)
        if isinstance(repositories, dict)
        else None
    )
    if not isinstance(repository_rules, dict):
        return [], [
            f"status check policy repository is not configured: {repository_full_name}"
        ]

    configured_checks = repository_rules.get("required_status_checks")
    if not isinstance(configured_checks, list) or not configured_checks:
        return [], [
            (
                "required status checks are not configured for repository: "
                f"{repository_full_name}"
            )
        ]

    bindings: list[tuple[str, str]] = []
    reasons: list[str] = []
    for index, configured_check in enumerate(configured_checks):
        if not isinstance(configured_check, dict):
            reasons.append(f"required status check {index} must be a mapping")
            continue
        non_string_fields = sorted(
            repr(field)
            for field in configured_check
            if not isinstance(field, str)
        )
        if non_string_fields:
            reasons.append(
                f"required status check {index} field names must be strings: "
                + ", ".join(non_string_fields)
            )
        fields = {
            field for field in configured_check if isinstance(field, str)
        }
        missing = sorted(REQUIRED_STATUS_CHECK_FIELDS - fields)
        unexpected = sorted(fields - REQUIRED_STATUS_CHECK_FIELDS)
        if missing:
            reasons.append(
                f"required status check {index} missing fields: "
                + ", ".join(missing)
            )
        if unexpected:
            reasons.append(
                f"required status check {index} has unexpected fields: "
                + ", ".join(unexpected)
            )

        name = configured_check.get("name")
        source_app = configured_check.get("source_app")
        if not isinstance(name, str) or not name:
            reasons.append(f"required status check {index} name is required")
        if not isinstance(source_app, str) or not source_app:
            reasons.append(
                f"required status check {index} source_app is required"
            )
        if (
            isinstance(name, str)
            and name
            and isinstance(source_app, str)
            and source_app
        ):
            binding = (name, source_app)
            if binding in bindings:
                reasons.append(
                    "required status check policy has duplicate binding: "
                    f"{name} from {source_app}"
                )
            else:
                bindings.append(binding)
    return bindings, reasons


def _all_checks_pass(
    status_checks: list[dict[str, Any]],
    *,
    required_bindings: list[tuple[str, str]],
    expected_head_sha: object,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not status_checks:
        return False, ["status checks must be non-empty"]

    observed_bindings: set[tuple[str, str]] = set()
    for index, check in enumerate(status_checks):
        if not isinstance(check, dict):
            reasons.append(f"status check {index} must be a mapping")
            continue
        raw_name = check.get("name") or check.get("context")
        name = raw_name if isinstance(raw_name, str) and raw_name else "unnamed-check"
        source_app = check.get("source_app")
        head_sha = check.get("head_sha")
        status = check.get("status")
        conclusion = check.get("conclusion")

        if name == "unnamed-check":
            reasons.append("status check name is required")
        if not isinstance(source_app, str) or not source_app:
            reasons.append(f"{name} source_app is required")
        if not isinstance(expected_head_sha, str) or not expected_head_sha:
            reasons.append("pull request head_sha is required for status checks")
        elif head_sha != expected_head_sha:
            reasons.append(f"{name} head_sha must match current pull request head")

        if name != "unnamed-check" and isinstance(source_app, str) and source_app:
            binding = (name, source_app)
            if binding in observed_bindings:
                reasons.append(
                    f"status check has duplicate binding: {name} from {source_app}"
                )
            observed_bindings.add(binding)

        if status != "completed":
            reasons.append(f"{name} status is {status}")
            continue
        if conclusion not in PASSING_CONCLUSIONS:
            reasons.append(f"{name} conclusion is {conclusion}")

    for name, source_app in required_bindings:
        if (name, source_app) in observed_bindings:
            continue
        observed_sources = sorted(
            observed_source
            for observed_name, observed_source in observed_bindings
            if observed_name == name
        )
        if observed_sources:
            reasons.append(
                f"required status check {name} must come from {source_app}"
            )
        else:
            reasons.append(
                f"required status check missing: {name} from {source_app}"
            )
    return not reasons, reasons


def _is_allowed_merge_method(policy: dict[str, Any], merge_method: str) -> bool:
    merge_policy = policy.get("merge_policy") or {}
    default_method = merge_policy.get("default_method", "squash")
    return merge_method == default_method


def _validate_controller_lifecycle_approval(
    lifecycle_approval: dict[str, Any] | None,
    pull_request: dict[str, Any],
) -> tuple[str | None, list[str]]:
    if not isinstance(lifecycle_approval, dict):
        return None, [
            (
                "separate lifecycle approval is required; task manifest approval "
                "does not authorize repository mutation"
            )
        ]

    reasons: list[str] = []
    non_string_fields = sorted(
        repr(field) for field in lifecycle_approval if not isinstance(field, str)
    )
    if non_string_fields:
        reasons.append(
            "lifecycle approval field names must be strings: "
            + ", ".join(non_string_fields)
        )
    fields = {field for field in lifecycle_approval if isinstance(field, str)}
    missing = sorted(LIFECYCLE_APPROVAL_FIELDS - fields)
    unexpected = sorted(fields - LIFECYCLE_APPROVAL_FIELDS)
    if missing:
        reasons.append("lifecycle approval missing fields: " + ", ".join(missing))
    if unexpected:
        reasons.append("lifecycle approval has unexpected fields: " + ", ".join(unexpected))

    if lifecycle_approval.get("required") is not True:
        reasons.append("lifecycle approval required must be true")

    for field in (
        "approved_by",
        "approval_source",
        "approved_at",
        "approval_record_id",
        "approval_record_or_reason",
    ):
        if not isinstance(lifecycle_approval.get(field), str) or not lifecycle_approval.get(field):
            reasons.append(f"lifecycle approval {field} is required")

    approval_source = lifecycle_approval.get("approval_source")
    if isinstance(approval_source, str) and not approval_source.startswith(
        "external_authority:"
    ):
        reasons.append(
            "lifecycle approval approval_source must identify an external authority"
        )

    expected = {
        "repository_full_name": pull_request.get("repository"),
        "pull_request_number": pull_request.get("number"),
        "action": "pr_merge",
        "base_branch": pull_request.get("base"),
        "expected_head_sha": pull_request.get("head_sha"),
    }
    for field, value in expected.items():
        if field == "pull_request_number":
            context_value_valid = (
                isinstance(value, int) and not isinstance(value, bool) and value > 0
            )
        else:
            context_value_valid = isinstance(value, str) and bool(value)
        if not context_value_valid:
            reasons.append(f"current lifecycle context requires {field}")
        elif lifecycle_approval.get(field) != value:
            reasons.append(
                f"lifecycle approval {field} must match current lifecycle context"
            )

    if reasons:
        return None, reasons
    canonical = json.dumps(
        lifecycle_approval,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest(), []


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
    lifecycle_approval: dict[str, Any] | None = None,
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

    required_bindings, check_policy_reasons = _required_status_check_bindings(
        repo_policy,
        pull_request.get("repository"),
    )
    reasons.extend(check_policy_reasons)
    checks_ok, check_reasons = _all_checks_pass(
        status_checks,
        required_bindings=required_bindings,
        expected_head_sha=pull_request.get("head_sha"),
    )
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
        approval_manifest = dict(task_manifest)
        approval_manifest["approval"] = lifecycle_approval
        _, lifecycle_reasons = validate_lifecycle_approval(
            approval_manifest,
            repo_policy,
            action="pr_merge",
            repository_full_name=pull_request.get("repository"),
            base_branch=pull_request.get("base"),
            expected_head_sha=pull_request.get("head_sha"),
        )
        reasons.extend(lifecycle_reasons)
    approval_record_sha256, controller_approval_reasons = (
        _validate_controller_lifecycle_approval(lifecycle_approval, pull_request)
    )
    reasons.extend(controller_approval_reasons)

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "merge_method": merge_method,
        "approval_action": "pr_merge",
        "approval_record_sha256": approval_record_sha256,
        "reasons": reasons,
    }
