from __future__ import annotations

from pathlib import Path

import yaml

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import (
    compile_task_graph_file_to_batch,
    validate_task_graph,
    validate_task_graph_active_gates,
    validate_task_graph_active_gates_file,
    validate_task_graph_file,
    write_task_graph_batch_file,
)
from tool_system.runner.task_runner import run_batch_file


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"
ACTIVE_GATES_PATH = ROOT / "examples" / "active_gates.yaml"
P7A_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_task_graph_planner.yaml"
P7B_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_graph_batch.yaml"
P7C_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_task_graph_active_gate.yaml"
STRICT_MANIFEST_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_task_manifest_v1.yaml"
STRICT_PLAN_PATH = ROOT / "tests" / "fixtures" / "manifest_validation" / "forward_valid_change_plan_v1.yaml"


def _strict_graph(tmp_path: Path) -> Path:
    graph = load_yaml_file(GRAPH_PATH)
    for task in graph["tasks"]:
        task["task_manifest"] = STRICT_MANIFEST_PATH.as_posix()
        task["change_plan"] = STRICT_PLAN_PATH.as_posix()
    path = tmp_path / "strict_graph.yaml"
    path.write_text(yaml.safe_dump(graph, sort_keys=False), encoding="utf-8")
    return path


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


def test_task_graph_validates_active_gates() -> None:
    result = validate_task_graph_active_gates_file(GRAPH_PATH, BLUEPRINT_PATH, ACTIVE_GATES_PATH)

    assert result["status"] == "PASS"
    assert len(result["active_gate_checks"]) == 4
    assert all(check["resolved_change_plan"] for check in result["active_gate_checks"])


def test_task_graph_blocks_inactive_manifest() -> None:
    graph = load_yaml_file(GRAPH_PATH)
    graph["tasks"][0]["task_manifest"] = "examples/task_manifests/not_active.yaml"
    blueprint = load_yaml_file(BLUEPRINT_PATH)

    result = validate_task_graph_active_gates(graph, blueprint, ACTIVE_GATES_PATH)

    assert result["status"] == "BLOCK"
    assert "task manifest is not active: examples/task_manifests/not_active.yaml" in result["reasons"]


def test_task_graph_compiles_to_batch_in_order() -> None:
    result = compile_task_graph_file_to_batch(GRAPH_PATH, BLUEPRINT_PATH)

    assert result["status"] == "PASS"
    assert result["batch"]["batch_id"] == "tool-system-p7a-task-graph-compiled-batch"
    assert [task["task_manifest"] for task in result["batch"]["tasks"]] == [
        "examples/task_manifests/tool_system_phase_alignment.yaml",
        "examples/task_manifests/tool_system_root_cli.yaml",
        "examples/task_manifests/tool_system_active_gate_resolver.yaml",
        "examples/task_manifests/tool_system_audit_bundle.yaml",
    ]


def test_task_graph_writes_runnable_batch(tmp_path: Path) -> None:
    batch_path = tmp_path / "compiled_batch.yaml"
    compile_result = write_task_graph_batch_file(
        _strict_graph(tmp_path), batch_path, BLUEPRINT_PATH
    )

    assert compile_result["status"] == "PASS"
    assert batch_path.exists()

    run_result = run_batch_file(batch_path=batch_path, execute_commands=False)
    assert run_result["status"] == "PASS"
    assert run_result["completed_task_count"] == 4


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


def test_task_graph_change_plans_validate() -> None:
    p7a_result = validate_change_plan(P7A_PLAN_PATH)
    p7b_result = validate_change_plan(P7B_PLAN_PATH)
    p7c_result = validate_change_plan(P7C_PLAN_PATH)

    for result in (p7a_result, p7b_result, p7c_result):
        assert result["status"] == "BLOCK"
        assert any(
            "TASK_MANIFEST_SCHEMA_VIOLATION" in reason
            for reason in result["reasons"]
        )
