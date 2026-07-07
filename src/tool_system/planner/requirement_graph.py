from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import validate_task_graph


REQUIRED_REQUIREMENT_KEYS = {"requirement_id", "phase", "objective", "work_items"}
REQUIRED_WORK_ITEM_KEYS = {"item_id", "role", "task_manifest"}


def _normalize_work_items(work_items: object) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(work_items, list) or not work_items:
        return [], ["work_items must be a non-empty list"]

    normalized: list[dict[str, Any]] = []
    reasons: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(work_items):
        if not isinstance(item, dict):
            reasons.append(f"work item {index} must be a mapping")
            continue
        missing = sorted(REQUIRED_WORK_ITEM_KEYS - set(item))
        if missing:
            reasons.append(f"work item {index} missing keys: " + ", ".join(missing))
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            reasons.append(f"work item {index} item_id must be a non-empty string")
        elif item_id in seen:
            reasons.append(f"duplicate work item: {item_id}")
        else:
            seen.add(item_id)
        depends_on = item.get("depends_on", [])
        if depends_on is None:
            depends_on = []
        if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
            reasons.append(f"work item {item_id or index} depends_on must be a list of strings")
        normalized.append({**item, "depends_on": depends_on})
    return normalized, reasons


def compile_requirement_to_task_graph(requirement: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, object]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_REQUIREMENT_KEYS - set(requirement))
    if missing:
        reasons.append("missing requirement keys: " + ", ".join(missing))

    work_items, work_item_reasons = _normalize_work_items(requirement.get("work_items"))
    reasons.extend(work_item_reasons)

    graph = {
        "graph_id": requirement.get("target_graph_id") or f"{requirement.get('requirement_id')}-task-graph",
        "phase": requirement.get("phase"),
        "source_requirement": {
            "requirement_id": requirement.get("requirement_id"),
            "objective": requirement.get("objective"),
        },
        "source_blueprint": requirement.get("source_blueprint"),
        "tasks": [
            {
                "task_id": item.get("item_id"),
                "role": item.get("role"),
                "task_manifest": item.get("task_manifest"),
                "change_plan": item.get("change_plan"),
                "depends_on": item.get("depends_on") or [],
            }
            for item in work_items
        ],
    }

    graph_validation = validate_task_graph(graph, blueprint) if not reasons else {"status": "BLOCK", "reasons": []}
    reasons.extend(str(reason) for reason in graph_validation.get("reasons", []))

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_requirement_graph_compile",
        "requirement_id": requirement.get("requirement_id"),
        "graph": graph,
        "graph_validation": graph_validation,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }


def compile_requirement_file_to_task_graph(
    requirement_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
) -> dict[str, object]:
    requirement = load_yaml_file(requirement_path)
    blueprint = load_yaml_file(blueprint_path)
    result = compile_requirement_to_task_graph(requirement, blueprint)
    return {**result, "requirement_path": str(requirement_path), "blueprint_path": str(blueprint_path)}


def write_requirement_task_graph_file(
    requirement_path: str | Path,
    output_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
) -> dict[str, object]:
    result = compile_requirement_file_to_task_graph(requirement_path, blueprint_path)
    if result["status"] != "PASS":
        return result
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(result["graph"], sort_keys=False), encoding="utf-8")
    return {**result, "graph_output_path": str(destination)}
