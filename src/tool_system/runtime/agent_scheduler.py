from __future__ import annotations

from typing import Any


PROTECTED_ROLE_PAIRS = {
    ("policy_guard", "target_repo_executor"),
    ("code_reviewer", "patch_author"),
}


def build_agent_execution_plan(task_graph: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, object]:
    agents = blueprint.get("agents", {})
    reasons: list[str] = []
    assignments: list[dict[str, object]] = []

    for task in task_graph.get("tasks", []):
        if not isinstance(task, dict):
            reasons.append("task entries must be mappings")
            continue
        role = task.get("role")
        task_id = task.get("task_id")
        if role not in agents:
            reasons.append(f"unknown agent role: {role}")
            continue
        assignments.append({
            "task_id": task_id,
            "role": role,
            "permissions": agents[role].get("permissions", []),
        })

    roles = {str(item["role"]) for item in assignments}
    for left, right in PROTECTED_ROLE_PAIRS:
        if left in roles and right in roles:
            reasons.append(f"protected role pair requires separation: {left}/{right}")

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_agent_execution_plan",
        "assignments": assignments,
        "task_count": len(assignments),
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
