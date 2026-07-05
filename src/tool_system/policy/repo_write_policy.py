from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

VALID_MODES = {"read_only", "patch_only", "pull_request", "direct_bootstrap"}


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def validate_repo_write_policy(manifest: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    target_repo = manifest.get("target_repo")
    repos = policy.get("allowed_target_repos") or {}
    repo_rules = repos.get(target_repo)
    if not isinstance(repo_rules, dict):
        return False, [f"target repo not allowed: {target_repo}"]

    mode = manifest.get("write_mode")
    if mode not in VALID_MODES:
        reasons.append(f"unsupported mode: {mode}")

    paths = manifest.get("allowed_files") or []
    if not paths:
        reasons.append("allowed_files must be non-empty")
        return False, reasons

    allowlist = []
    allowlist.extend(repo_rules.get("allowed_bootstrap_paths") or [])
    allowlist.extend(repo_rules.get("phase_1_allowed_paths") or [])
    blocklist = repo_rules.get("forbidden_paths") or []

    for path in paths:
        if _match(path, blocklist):
            reasons.append(f"blocked path: {path}")
        if allowlist and not _match(path, allowlist):
            reasons.append(f"path outside allowlist: {path}")

    approval = manifest.get("approval") or {}
    if approval.get("required") is not True:
        reasons.append("approval.required must be true")
    if not approval.get("approved_by"):
        reasons.append("approval.approved_by is required")

    return not reasons, reasons
