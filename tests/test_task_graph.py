from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import validate_task_graph, validate_task_graph_file


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"
P7A_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_task_graph_planner.yaml"


def test_task_graph_planner_orders_tasks() -> None:
    result = validate_task_graph_file(GRAPH_PATH, BLUEPRINT_PATH)

    assert result["status"] == "PASS"
    assert result["execution_order"] == [
        "collect-evidence",
        "enforce-policy",
        "verify-runner",
        "record-audit",
    ]
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_task_graph_planner_blocks_cycles() -> None:
    graph = load_yaml_file(GRAPH_PATH)
    graph["tasks"][0]["depends_on"] = ["record-audit"]
    blueprint = load_yaml_file(BLUEPRINT_PATH)

    result = validate_task_graph(graph, blueprint)

    assert result["status"] == "BLOCK"
    assert any("cycle" in reason for reason in result["reasons"])


def test_task_graph_planner_requires_control_roles() -> None:
    graph = load_yaml_file(GRAPH_PATH)
    graph["tasks"] = [task for task in graph["tasks"] if task["role"] != "audit_recorder"]
    blueprint = load_yaml_file(BLUEPRINT_PATH)

    result = validate_task_graph(graph, blueprint)

    assert result["status"] == "BLOCK"
    assert "task graph missing control roles: audit_recorder" in result["reasons"]


def test_task_graph_change_plan_validates() -> None:
    result = validate_change_plan(P7A_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
