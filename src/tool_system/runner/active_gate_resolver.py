from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file


_REPO_PATH_MARKERS = (
    "examples/",
    "src/",
    "tests/",
    "policy/",
    "blueprint/",
    "docs/",
    ".github/",
)


def _path_keys(path: str | Path) -> set[str]:
    raw = Path(path).as_posix()
    keys = {raw}
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            keys.add(candidate.relative_to(Path.cwd()).as_posix())
        except ValueError:
            pass
    for marker in _REPO_PATH_MARKERS:
        if marker in raw:
            keys.add(raw[raw.index(marker) :])
    for filename in ("README.md", "AGENTS.md", "pyproject.toml"):
        if raw.endswith(filename):
            keys.add(filename)
    return keys


def _active_gate_entries(active_gates: dict[str, Any], key: str) -> list[str]:
    entries = active_gates.get(key) or []
    if not isinstance(entries, list):
        return []
    return [str(entry) for entry in entries if isinstance(entry, str)]


def _matches_path(left: str | Path, right: str | Path) -> bool:
    return bool(_path_keys(left) & _path_keys(right))


def resolve_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path | None:
    active_gates_file = Path(active_gates_path)
    active_gates = load_yaml_file(active_gates_file)
    task_manifests = _active_gate_entries(active_gates, "task_manifests")
    if not any(_matches_path(task_manifest_path, entry) for entry in task_manifests):
        return None

    for change_plan_entry in _active_gate_entries(active_gates, "change_plans"):
        change_plan_path = Path(change_plan_entry)
        change_plan = load_yaml_file(change_plan_path)
        if _matches_path(str(change_plan.get("task_manifest") or ""), task_manifest_path):
            return change_plan_path
    return None


def resolve_required_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path:
    resolved = resolve_change_plan_from_active_gates(task_manifest_path, active_gates_path)
    if resolved is None:
        requested = sorted(_path_keys(task_manifest_path))[0]
        raise ValueError(f"no active change plan found for task manifest: {requested}")
    return resolved
