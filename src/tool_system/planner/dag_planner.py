from __future__ import annotations

from typing import Any


REQUIRED_NODES = {
    "blueprint_intake",
    "task_decomposition",
    "change_plan",
    "verification",
    "audit",
}


def compile_blueprint_dag(blueprint: dict[str, Any], milestone: str) -> dict[str, object]:
    milestones = blueprint.get("milestones", {})
    if milestone not in milestones:
        return {
            "status": "BLOCK",
            "reasons": [f"unknown milestone: {milestone}"],
            "nodes": [],
            "edges": [],
        }

    outputs = milestones[milestone].get("outputs", [])
    nodes = [
        {"id": "blueprint_intake", "role": "blueprint_architect"},
        {"id": "task_decomposition", "role": "task_decomposer"},
        {"id": "change_plan", "role": "change_planner"},
        {"id": "verification", "role": "test_engineer"},
        {"id": "audit", "role": "audit_recorder"},
    ]
    edges = [
        ["blueprint_intake", "task_decomposition"],
        ["task_decomposition", "change_plan"],
        ["change_plan", "verification"],
        ["verification", "audit"],
    ]
    return {
        "status": "PASS",
        "milestone": milestone,
        "outputs": outputs,
        "nodes": nodes,
        "edges": edges,
        "reasons": [],
    }


def validate_dag(dag: dict[str, object]) -> dict[str, object]:
    nodes = dag.get("nodes") or []
    node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
    reasons: list[str] = []

    missing = sorted(REQUIRED_NODES - node_ids)
    if missing:
        reasons.append("missing required DAG nodes: " + ", ".join(missing))

    if dag.get("status") != "PASS":
        reasons.extend(str(reason) for reason in dag.get("reasons", []))

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "reasons": reasons,
    }


def topological_order(dag: dict[str, object]) -> list[str]:
    nodes = {node["id"] for node in dag.get("nodes", []) if isinstance(node, dict)}
    edges = dag.get("edges", [])
    incoming = {node: 0 for node in nodes}
    graph = {node: [] for node in nodes}
    for edge in edges:
        if isinstance(edge, list) and len(edge) == 2:
            graph[edge[0]].append(edge[1])
            incoming[edge[1]] += 1

    queue = [node for node, count in incoming.items() if count == 0]
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in graph[node]:
            incoming[child] -= 1
            if incoming[child] == 0:
                queue.append(child)
    return order
