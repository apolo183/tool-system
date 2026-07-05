from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_KEYS = {
    "task_id",
    "task_type",
    "target_repo",
    "target_branch",
    "phase",
    "approved_blueprint_refs",
    "scope",
    "evidence",
    "allowed_files",
    "forbidden_files",
    "write_mode",
    "verification",
    "rollback",
    "approval",
}


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("YAML root must be a mapping")
    return value


def validate_manifest_structure(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_KEYS - set(manifest))
    if missing:
        reasons.append("missing required keys: " + ", ".join(missing))
    if not manifest.get("allowed_files"):
        reasons.append("allowed_files must be non-empty")
    if not manifest.get("approved_blueprint_refs"):
        reasons.append("approved_blueprint_refs must be non-empty")
    if not manifest.get("evidence"):
        reasons.append("evidence must be non-empty")
    if not isinstance(manifest.get("verification"), dict):
        reasons.append("verification must be a mapping")
    if not isinstance(manifest.get("rollback"), dict):
        reasons.append("rollback must be a mapping")
    approval = manifest.get("approval")
    if not isinstance(approval, dict) or approval.get("required") is not True:
        reasons.append("approval.required must be true")
    return not reasons, reasons
