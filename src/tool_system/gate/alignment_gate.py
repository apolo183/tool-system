from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file

ALIGNMENT_KEYS = ("parent", "global")
ALIGNMENT_FIELD_KEYS = ("document", "section_or_key", "scope")


def _as_list(value: Any, key: str) -> list[str]:
    raw = value.get(key) if isinstance(value, dict) else None
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if isinstance(item, str)]


def _validate_alignment_block(value: dict[str, Any], path: Path, kind: str) -> list[str]:
    reasons: list[str] = []
    alignment = value.get("alignment")
    if not isinstance(alignment, dict):
        return [f"{kind} {path} must define alignment"]

    for section in ALIGNMENT_KEYS:
        block = alignment.get(section)
        if not isinstance(block, dict):
            reasons.append(f"{kind} {path} alignment.{section} must be a mapping")
            continue
        for field in ALIGNMENT_FIELD_KEYS:
            raw_value = block.get(field)
            if not isinstance(raw_value, str) or not raw_value.strip():
                reasons.append(f"{kind} {path} alignment.{section}.{field} must be a non-empty string")

    return reasons


def _manifest_global_ref_matches(manifest: dict[str, Any]) -> bool:
    alignment = manifest.get("alignment") if isinstance(manifest, dict) else None
    global_block = alignment.get("global") if isinstance(alignment, dict) else None
    if not isinstance(global_block, dict):
        return False
    document = global_block.get("document")
    section = global_block.get("section_or_key")
    if not isinstance(document, str) or not isinstance(section, str):
        return False

    refs = manifest.get("approved_blueprint_refs")
    if not isinstance(refs, list):
        return False
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        if ref.get("path") == document and ref.get("section_or_key") == section:
            return True
    return False


def _validate_task_manifest_alignment(path: Path) -> list[str]:
    manifest = load_yaml_file(path)
    reasons = _validate_alignment_block(manifest, path, "task_manifest")
    if not reasons and not _manifest_global_ref_matches(manifest):
        reasons.append(
            f"task_manifest {path} alignment.global must match an approved_blueprint_refs entry"
        )
    return reasons


def _validate_change_plan_alignment(path: Path) -> list[str]:
    plan = load_yaml_file(path)
    reasons = _validate_alignment_block(plan, path, "change_plan")
    task_manifest_raw = plan.get("task_manifest")
    if not isinstance(task_manifest_raw, str) or not task_manifest_raw.strip():
        reasons.append(f"change_plan {path} task_manifest must be a non-empty string")
        return reasons

    alignment = plan.get("alignment") if isinstance(plan, dict) else None
    parent = alignment.get("parent") if isinstance(alignment, dict) else None
    if isinstance(parent, dict) and parent.get("document") != task_manifest_raw:
        reasons.append(
            f"change_plan {path} alignment.parent.document must match task_manifest"
        )

    try:
        manifest = load_yaml_file(Path(task_manifest_raw))
    except FileNotFoundError:
        reasons.append(f"change_plan {path} task_manifest does not exist: {task_manifest_raw}")
        return reasons

    manifest_alignment = manifest.get("alignment") if isinstance(manifest, dict) else None
    manifest_global = manifest_alignment.get("global") if isinstance(manifest_alignment, dict) else None
    plan_global = alignment.get("global") if isinstance(alignment, dict) else None
    if isinstance(manifest_global, dict) and isinstance(plan_global, dict):
        for field in ("document", "section_or_key"):
            if plan_global.get(field) != manifest_global.get(field):
                reasons.append(
                    f"change_plan {path} alignment.global.{field} must match task_manifest alignment.global.{field}"
                )

    return reasons


def _paths_from_marker(index: dict[str, Any], key: str, marker_key: str) -> tuple[list[Path], list[str]]:
    reasons: list[str] = []
    gate = index.get("alignment_gate")
    if not isinstance(gate, dict):
        return [], ["alignment_gate must be configured"]
    marker = gate.get(marker_key)
    if not isinstance(marker, str) or not marker.strip():
        return [], [f"alignment_gate.{marker_key} must be a non-empty string"]

    raw_paths = _as_list(index, key)
    if marker not in raw_paths:
        return [], [f"alignment gate marker not found in {key}: {marker}"]
    marker_index = raw_paths.index(marker)
    return [Path(path) for path in raw_paths[marker_index:]], reasons


def validate(index_path: Path) -> dict[str, object]:
    index = load_yaml_file(index_path)
    gate = index.get("alignment_gate")
    if not isinstance(gate, dict) or gate.get("enabled") is not True:
        return {
            "status": "PASS",
            "index_path": str(index_path),
            "checked": [],
            "reasons": [],
            "alignment_gate_enabled": False,
        }

    manifest_paths, manifest_marker_reasons = _paths_from_marker(
        index, "task_manifests", "task_manifest_marker"
    )
    change_plan_paths, plan_marker_reasons = _paths_from_marker(
        index, "change_plans", "change_plan_marker"
    )

    reasons = manifest_marker_reasons + plan_marker_reasons
    checked: list[dict[str, str]] = []

    for manifest_path in manifest_paths:
        checked.append({"kind": "task_manifest", "path": str(manifest_path)})
        reasons.extend(_validate_task_manifest_alignment(manifest_path))

    for change_plan_path in change_plan_paths:
        checked.append({"kind": "change_plan", "path": str(change_plan_path)})
        reasons.extend(_validate_change_plan_alignment(change_plan_path))

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "index_path": str(index_path),
        "checked": checked,
        "reasons": reasons,
        "alignment_gate_enabled": True,
    }
