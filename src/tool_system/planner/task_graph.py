from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file

REQUIRED_GRAPH_KEYS = {"graph_id", "phase", "tasks"}
REQUIRED_TASK_KEYS = {"task_id", "task_manifest", "role"}
REQUIRED_CONTROL_ROLES = {
    "evidence_collector",
    "policy_guard",
    "test_engineer",
    "audit_recorder",
}


def _task_ids(tasks: list[dict[str, Any]]) -> list[str]:
    return [str(task.get("task_id")) for task in tasks if isinstance(task.get("task_id"), str)]


def _allowed_roles(blueprint: dict[str, Any]) -> set[str]:
    agents = blueprint.get("agents") or {}
    if not isinstance(agents, dict):
        return set()
    return {str(role) for role in agents}


def _validate_task_shape(tasks: object, allowed_roles: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    reasons: list[str] = []
    if not isinstance(tasks, list) or not tasks:
        return [], ["tasks must be a non-empty list"]

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            reasons.append(f"task {index} must be a mapping")
            continue
        missing = sorted(REQUIRED_TASK_KEYS - set(task))
        if missing:
            reasons.append(f"task {index} missing keys: " + ", ".join(missing))
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            reasons.append(f"task {index} task_id must be a non-empty string")
        elif task_id in seen:
            reasons.append(f"duplicate task_id: {task_id}")
        else:
            seen.add(task_id)
        role = task.get("role")
        if not isinstance(role, str) or role not in allowed_roles:
            reasons.append(f"task {task_id or index} role is not allowed: {role}")
        depends_on = task.get("depends_on", [])
        if depends_on is None:
            depends_on = []
        if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
            reasons.append(f"task {task_id or index} depends_on must be a list of strings")
        normalized.append({**task, "depends_on": depends_on})
    return normalized, reasons


def _validate_dependencies(tasks: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    ids = set(_task_ids(tasks))
    for task in tasks:
        task_id = str(task.get("task_id"))
        for dependency in task.get("depends_on") or []:
            if dependency == task_id:
                reasons.append(f"task cannot depend on itself: {task_id}")
            if dependency not in ids:
                reasons.append(f"unknown dependency for {task_id}: {dependency}")
    return reasons


def _topological_order(tasks: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    ids = _task_ids(tasks)
    dependents: dict[str, list[str]] = defaultdict(list)
    indegree = {task_id: 0 for task_id in ids}
    for task in tasks:
        task_id = str(task["task_id"])
        for dependency in task.get("depends_on") or []:
            dependents[dependency].append(task_id)
            indegree[task_id] += 1

    queue = deque(task_id for task_id in ids if indegree[task_id] == 0)
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in dependents[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if len(order) != len(ids):
        cyclic = sorted(task_id for task_id, degree in indegree.items() if degree > 0)
        return order, ["task graph contains a cycle: " + ", ".join(cyclic)]
    return order, []


def validate_task_graph(graph: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, object]:
    reasons: list[str] = []
    missing = sorted(REQUIRED_GRAPH_KEYS - set(graph))
    if missing:
        reasons.append("missing graph keys: " + ", ".join(missing))

    allowed_roles = _allowed_roles(blueprint)
    tasks, task_reasons = _validate_task_shape(graph.get("tasks"), allowed_roles)
    reasons.extend(task_reasons)
    reasons.extend(_validate_dependencies(tasks))

    roles = {str(task.get("role")) for task in tasks if isinstance(task.get("role"), str)}
    missing_roles = sorted(REQUIRED_CONTROL_ROLES - roles)
    if missing_roles:
        reasons.append("task graph missing control roles: " + ", ".join(missing_roles))

    order, order_reasons = _topological_order(tasks) if not reasons else ([], [])
    reasons.extend(order_reasons)

    task_by_id = {str(task.get("task_id")): task for task in tasks if isinstance(task.get("task_id"), str)}
    execution_plan = [
        {
            "task_id": task_id,
            "role": task_by_id[task_id].get("role"),
            "task_manifest": task_by_id[task_id].get("task_manifest"),
            "change_plan": task_by_id[task_id].get("change_plan"),
            "depends_on": task_by_id[task_id].get("depends_on") or [],
        }
        for task_id in order
    ]

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_task_graph_plan",
        "graph_id": graph.get("graph_id"),
        "phase": graph.get("phase"),
        "task_count": len(tasks),
        "execution_order": order,
        "execution_plan": execution_plan,
        "role_assignments": {str(task.get("task_id")): task.get("role") for task in tasks if task.get("task_id")},
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }


def validate_task_graph_file(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
) -> dict[str, object]:
    graph = load_yaml_file(graph_path)
    blueprint = load_yaml_file(blueprint_path)
    result = validate_task_graph(graph, blueprint)
    return {**result, "graph_path": str(graph_path), "blueprint_path": str(blueprint_path)}
