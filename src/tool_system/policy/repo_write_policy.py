from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

VALID_MODES = {"read_only", "patch_only", "pull_request", "direct_bootstrap"}
ACTIVE_POLICY_STATUS = "active"
VALID_LIFECYCLE_APPROVAL_MODES = {"manifest", "named_action"}


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _allowed_paths_for_mode(repo_rules: dict[str, Any], mode: object) -> list[str] | None:
    by_mode = repo_rules.get("allowed_paths_by_mode")
    if not isinstance(by_mode, dict) or not isinstance(mode, str):
        return None
    value = by_mode.get(mode)
    if not isinstance(value, list) or not all(isinstance(path, str) for path in value):
        return None
    return list(value)


def _requires_per_pr_human_review(policy: dict[str, Any]) -> bool:
    legacy = policy.get("approval") or {}
    if legacy.get("explicit_user_approval_required") is True:
        return True
    model = policy.get("approval_model") or {}
    return model.get("per_pr_human_review_required") is True


def _validate_retired_fixture(
    manifest: dict[str, Any], repo_rules: dict[str, Any]
) -> list[str]:
    if repo_rules.get("status") != "retired":
        return []
    fixture = manifest.get("historical_fixture")
    fixture_rules = repo_rules.get("historical_fixture")
    if not isinstance(fixture, dict) or not isinstance(fixture_rules, dict):
        return ["retired target repo is not allowed for new work"]
    if fixture.get("closed") is not True or fixture.get("new_work_authorized") is not False:
        return ["retired target repo is not allowed for new work"]
    allowed_task_ids = fixture_rules.get("allowed_task_ids") or []
    allowed_modes = fixture_rules.get("allowed_modes") or []
    if manifest.get("task_id") not in allowed_task_ids:
        return ["retired target repo is not allowed for new work"]
    if manifest.get("write_mode") not in allowed_modes:
        return ["retired target repo is not allowed for new work"]
    return []


def validate_repo_write_policy(manifest: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if policy.get("status") != ACTIVE_POLICY_STATUS:
        reasons.append("repo_write_policy.status must be active")

    target_repo = manifest.get("target_repo")
    repos = policy.get("allowed_target_repos") or {}
    repo_rules = repos.get(target_repo)
    if not isinstance(repo_rules, dict):
        return False, [*reasons, f"target repo not allowed: {target_repo}"]
    reasons.extend(_validate_retired_fixture(manifest, repo_rules))

    mode = manifest.get("write_mode")
    if mode not in VALID_MODES:
        reasons.append(f"unsupported mode: {mode}")

    if mode == "direct_bootstrap" and repo_rules.get("bootstrap_direct_main_allowed") is not True:
        reasons.append(f"direct bootstrap is disabled for target repo: {target_repo}")

    paths = manifest.get("allowed_files") or []
    if not paths:
        reasons.append("allowed_files must be non-empty")
        return False, reasons

    allowlist = _allowed_paths_for_mode(repo_rules, mode)
    blocklist = repo_rules.get("forbidden_paths") or []

    if allowlist is None:
        reasons.append(f"allowed paths are not configured for mode: {mode}")
        allowlist = []

    for path in paths:
        if _match(path, blocklist):
            reasons.append(f"blocked path: {path}")
        if not _match(path, allowlist):
            reasons.append(f"path outside allowlist: {path}")

    if _requires_per_pr_human_review(policy):
        approval = manifest.get("approval") or {}
        if approval.get("required") is not True:
            reasons.append("approval.required must be true")
        if not approval.get("approved_by"):
            reasons.append("approval.approved_by is required")

    return not reasons, reasons


def validate_lifecycle_approval(
    manifest: dict[str, Any],
    policy: dict[str, Any],
    *,
    action: str,
    repository_full_name: object,
    base_branch: object,
    expected_head_sha: object,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    target_repo = manifest.get("target_repo")
    if repository_full_name != target_repo:
        reasons.append(
            f"pull request repository must match task manifest target_repo: {target_repo}"
        )

    repos = policy.get("allowed_target_repos") or {}
    repo_rules = repos.get(target_repo)
    if not isinstance(repo_rules, dict):
        return False, [*reasons, f"target repo not allowed: {target_repo}"]

    lifecycle = repo_rules.get("lifecycle_approval")
    if not isinstance(lifecycle, dict):
        return False, [*reasons, "lifecycle approval policy is required"]
    approval_mode = lifecycle.get(action)
    if approval_mode not in VALID_LIFECYCLE_APPROVAL_MODES:
        return False, [*reasons, f"lifecycle action is not allowed by policy: {action}"]

    approval = manifest.get("approval")
    if not isinstance(approval, dict) or approval.get("required") is not True:
        return False, [*reasons, "approval.required must be true"]
    if not approval.get("approved_by"):
        reasons.append("approval.approved_by is required for lifecycle action")

    if approval_mode == "named_action":
        expected = {
            "repository_full_name": repository_full_name,
            "action": action,
            "base_branch": base_branch,
            "expected_head_sha": expected_head_sha,
        }
        for key, value in expected.items():
            if not isinstance(value, str) or not value:
                reasons.append(f"current lifecycle context requires {key}")
            elif approval.get(key) != value:
                reasons.append(f"approval.{key} must match current lifecycle context")
        if not approval.get("approval_record_or_reason"):
            reasons.append("approval.approval_record_or_reason is required")

    return not reasons, reasons
