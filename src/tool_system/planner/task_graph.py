from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runner.active_gate_resolver import resolve_change_plan_from_active_gates

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


def _same_path(left: str | Path | None, right: str | Path | None) -> bool:
    if left is None or right is None:
        return False
    return Path(str(left)).as_posix() == Path(str(right)).as_posix()


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


def validate_task_graph_active_gates(
    graph: dict[str, Any],
    blueprint: dict[str, Any],
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> dict[str, object]:
    graph_result = validate_task_graph(graph, blueprint)
    reasons = list(graph_result.get("reasons") or [])
    active_gate_checks: list[dict[str, object]] = []

    if graph_result["status"] == "PASS":
        for task in graph_result["execution_plan"]:
            task_manifest = task.get("task_manifest")
            declared_change_plan = task.get("change_plan")
            resolved_change_plan = resolve_change_plan_from_active_gates(str(task_manifest), active_gates_path)
            check = {
                "task_id": task.get("task_id"),
                "task_manifest": task_manifest,
                "declared_change_plan": declared_change_plan,
                "resolved_change_plan": str(resolved_change_plan) if resolved_change_plan is not None else None,
            }
            if resolved_change_plan is None:
                reasons.append(f"task manifest is not active: {task_manifest}")
            elif declared_change_plan and not _same_path(declared_change_plan, resolved_change_plan):
                reasons.append(f"declared change plan does not match active gate for {task.get('task_id')}")
            active_gate_checks.append(check)

    return {
        **graph_result,
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_task_graph_active_gate_validation",
        "active_gates_path": str(active_gates_path),
        "active_gate_checks": active_gate_checks,
        "reasons": reasons,
    }


def validate_task_graph_active_gates_file(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
    active_gates_path: str | Path = "examples/active_gates.yaml",
) -> dict[str, object]:
    graph = load_yaml_file(graph_path)
    blueprint = load_yaml_file(blueprint_path)
    result = validate_task_graph_active_gates(graph, blueprint, active_gates_path)
    return {
        **result,
        "graph_path": str(graph_path),
        "blueprint_path": str(blueprint_path),
    }


def _batch_tasks_from_plan(execution_plan: list[dict[str, Any]]) -> list[dict[str, str]]:
    batch_tasks: list[dict[str, str]] = []
    for task in execution_plan:
        batch_task = {"task_manifest": str(task.get("task_manifest"))}
        if task.get("change_plan"):
            batch_task["change_plan"] = str(task.get("change_plan"))
        batch_tasks.append(batch_task)
    return batch_tasks


def compile_task_graph_to_batch(graph: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, object]:
    graph_result = validate_task_graph(graph, blueprint)
    if graph_result["status"] != "PASS":
        return {
            **graph_result,
            "mode": "tool_system_task_graph_batch_compile",
            "batch": None,
        }

    batch = {
        "batch_id": f"{graph_result['graph_id']}-compiled-batch",
        "halt_on_failure": True,
        "tasks": _batch_tasks_from_plan(graph_result["execution_plan"]),
    }
    return {
        **graph_result,
        "mode": "tool_system_task_graph_batch_compile",
        "batch": batch,
    }


def compile_task_graph_file_to_batch(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
) -> dict[str, object]:
    graph = load_yaml_file(graph_path)
    blueprint = load_yaml_file(blueprint_path)
    result = compile_task_graph_to_batch(graph, blueprint)
    return {**result, "graph_path": str(graph_path), "blueprint_path": str(blueprint_path)}


def write_task_graph_batch_file(
    graph_path: str | Path,
    output_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
) -> dict[str, object]:
    result = compile_task_graph_file_to_batch(graph_path, blueprint_path)
    if result["status"] != "PASS" or result.get("batch") is None:
        return result
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(result["batch"], sort_keys=False), encoding="utf-8")
    return {**result, "batch_output_path": str(destination)}
