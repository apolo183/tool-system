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
    entries = active_gates.get(key)
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{key} must be a non-empty list")
    if not all(isinstance(entry, str) and entry.strip() for entry in entries):
        raise ValueError(f"{key} entries must be non-empty strings")
    return [str(entry) for entry in entries]


def _matches_path(left: str | Path, right: str | Path) -> bool:
    return bool(_path_keys(left) & _path_keys(right))


def _reject_duplicate_paths(entries: list[str], label: str) -> None:
    for index, entry in enumerate(entries):
        if any(_matches_path(entry, previous) for previous in entries[:index]):
            raise ValueError(f"duplicate {label} path: {entry}")


def build_active_gate_pairings(
    active_gates: dict[str, Any],
) -> list[tuple[str, Path]]:
    task_manifests = _active_gate_entries(active_gates, "task_manifests")
    change_plans = _active_gate_entries(active_gates, "change_plans")
    _reject_duplicate_paths(task_manifests, "task manifest")
    _reject_duplicate_paths(change_plans, "change plan")

    plans_by_manifest: dict[str, list[Path]] = {
        manifest: [] for manifest in task_manifests
    }
    for change_plan_entry in change_plans:
        change_plan_path = Path(change_plan_entry)
        try:
            change_plan = load_yaml_file(change_plan_path)
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"unable to read active change plan: {change_plan_entry}"
            ) from exc
        manifest_ref = change_plan.get("task_manifest")
        if not isinstance(manifest_ref, str) or not manifest_ref.strip():
            raise ValueError(
                "active change plan task_manifest must be a non-empty string: "
                f"{change_plan_entry}"
            )
        matching_manifests = [
            manifest
            for manifest in task_manifests
            if _matches_path(manifest_ref, manifest)
        ]
        if not matching_manifests:
            raise ValueError(
                "change plan references unregistered task manifest: "
                f"{change_plan_entry} -> {manifest_ref}"
            )
        plans_by_manifest[matching_manifests[0]].append(change_plan_path)

    for manifest in sorted(task_manifests):
        matching_plans = plans_by_manifest[manifest]
        if not matching_plans:
            raise ValueError(
                f"registered task manifest has no change plan: {manifest}"
            )
        if len(matching_plans) > 1:
            raise ValueError(
                f"registered task manifest has multiple change plans: {manifest}"
            )

    return [
        (manifest, plans_by_manifest[manifest][0]) for manifest in task_manifests
    ]


def resolve_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path | None:
    active_gates_file = Path(active_gates_path)
    active_gates = load_yaml_file(active_gates_file)
    pairings = build_active_gate_pairings(active_gates)
    matching_pairings = [
        pairing
        for pairing in pairings
        if _matches_path(task_manifest_path, pairing[0])
    ]
    if not matching_pairings:
        return None
    if len(matching_pairings) > 1:
        requested = sorted(_path_keys(task_manifest_path))[0]
        raise ValueError(f"multiple active task manifests match request: {requested}")
    return matching_pairings[0][1]


def resolve_required_change_plan_from_active_gates(
    task_manifest_path: str | Path,
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> Path:
    resolved = resolve_change_plan_from_active_gates(task_manifest_path, active_gates_path)
    if resolved is None:
        requested = sorted(_path_keys(task_manifest_path))[0]
        raise ValueError(f"no active change plan found for task manifest: {requested}")
    return resolved
