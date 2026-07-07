from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file


def _normalize_path(path: str | Path) -> str:
    return Path(path).as_posix()


def _active_gate_entries(active_gates: dict[str, Any], key: str) -> list[str]:
    entries = active_gates.get(key) or []
    if not isinstance(entries, list):
        return []
    return [str(entry) for entry in entries if isinstance(entry, str)]


def resolve_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path | None:
    manifest_key = _normalize_path(task_manifest_path)
    active_gates_file = Path(active_gates_path)
    active_gates = load_yaml_file(active_gates_file)
    task_manifests = _active_gate_entries(active_gates, "task_manifests")
    if manifest_key not in {_normalize_path(entry) for entry in task_manifests}:
        return None

    for change_plan_entry in _active_gate_entries(active_gates, "change_plans"):
        change_plan_path = Path(change_plan_entry)
        change_plan = load_yaml_file(change_plan_path)
        if _normalize_path(str(change_plan.get("task_manifest") or "")) == manifest_key:
            return change_plan_path
    return None


def resolve_required_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path:
    resolved = resolve_change_plan_from_active_gates(task_manifest_path, active_gates_path)
    if resolved is None:
        raise ValueError(f"no active change plan found for task manifest: {_normalize_path(task_manifest_path)}")
    return resolved
