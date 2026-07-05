from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

REQUIRED_PLAN_KEYS = {
    "plan_id",
    "target_repo",
    "task_manifest",
    "changed_files",
    "verification",
    "rollback",
}


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def validate_change_plan_structure(plan: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_PLAN_KEYS - set(plan))
    if missing:
        reasons.append("missing change plan keys: " + ", ".join(missing))
    if not isinstance(plan.get("changed_files"), list) or not plan.get("changed_files"):
        reasons.append("changed_files must be a non-empty list")
    if not isinstance(plan.get("verification"), dict):
        reasons.append("verification must be a mapping")
    if not isinstance(plan.get("rollback"), dict):
        reasons.append("rollback must be a mapping")
    return not reasons, reasons


def validate_change_plan_against_manifest(
    plan: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if plan.get("target_repo") != manifest.get("target_repo"):
        reasons.append("target_repo must match task manifest")

    allowed_files = manifest.get("allowed_files") or []
    blocked_files = manifest.get("forbidden_files") or []
    changed_files = plan.get("changed_files") or []

    for path in changed_files:
        if not isinstance(path, str):
            reasons.append("changed_files entries must be strings")
            continue
        if _matches_any(path, blocked_files):
            reasons.append(f"blocked changed file: {path}")
        if allowed_files and not _matches_any(path, allowed_files):
            reasons.append(f"changed file outside manifest allowlist: {path}")

    manifest_commands = set((manifest.get("verification") or {}).get("commands") or [])
    plan_commands = set((plan.get("verification") or {}).get("commands") or [])
    if manifest_commands and not plan_commands.issubset(manifest_commands):
        reasons.append("change plan verification commands must be declared by task manifest")

    return not reasons, reasons
