from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

VALID_MODES = {"read_only", "patch_only", "pull_request", "direct_bootstrap"}
ACTIVE_POLICY_STATUS = "active"


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _collect_allowed_paths(repo_rules: dict[str, Any]) -> list[str]:
    allowlist: list[str] = []
    for key, value in repo_rules.items():
        if key.endswith("_allowed_paths") or key == "allowed_bootstrap_paths":
            if isinstance(value, list):
                allowlist.extend(value)
    return allowlist


def _requires_per_pr_human_review(policy: dict[str, Any]) -> bool:
    legacy = policy.get("approval") or {}
    if legacy.get("explicit_user_approval_required") is True:
        return True
    model = policy.get("approval_model") or {}
    return model.get("per_pr_human_review_required") is True


def validate_repo_write_policy(manifest: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if policy.get("status") != ACTIVE_POLICY_STATUS:
        reasons.append("repo_write_policy.status must be active")

    target_repo = manifest.get("target_repo")
    repos = policy.get("allowed_target_repos") or {}
    repo_rules = repos.get(target_repo)
    if not isinstance(repo_rules, dict):
        return False, [*reasons, f"target repo not allowed: {target_repo}"]

    mode = manifest.get("write_mode")
    if mode not in VALID_MODES:
        reasons.append(f"unsupported mode: {mode}")

    paths = manifest.get("allowed_files") or []
    if not paths:
        reasons.append("allowed_files must be non-empty")
        return False, reasons

    allowlist = _collect_allowed_paths(repo_rules)
    blocklist = repo_rules.get("forbidden_paths") or []

    for path in paths:
        if _match(path, blocklist):
            reasons.append(f"blocked path: {path}")
        if allowlist and not _match(path, allowlist):
            reasons.append(f"path outside allowlist: {path}")

    if _requires_per_pr_human_review(policy):
        approval = manifest.get("approval") or {}
        if approval.get("required") is not True:
            reasons.append("approval.required must be true")
        if not approval.get("approved_by"):
            reasons.append("approval.approved_by is required")

    return not reasons, reasons
