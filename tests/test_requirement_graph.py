from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.requirement_graph import compile_requirement_file_to_task_graph, write_requirement_task_graph_file
from tool_system.planner.task_graph import validate_task_graph_file


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT_PATH = ROOT / "examples" / "requirements" / "tool_system_p7d.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_requirement_graph.yaml"


def test_requirement_compiles_to_valid_task_graph() -> None:
    result = compile_requirement_file_to_task_graph(REQUIREMENT_PATH, BLUEPRINT_PATH)

    assert result["status"] == "PASS"
    assert result["graph"]["graph_id"] == "tool-system-p7d-compiled-graph"
    assert result["graph_validation"]["status"] == "PASS"
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_requirement_graph_file_can_be_written_and_validated(tmp_path: Path) -> None:
    graph_path = tmp_path / "compiled_graph.yaml"
    result = write_requirement_task_graph_file(REQUIREMENT_PATH, graph_path, BLUEPRINT_PATH)

    assert result["status"] == "PASS"
    assert graph_path.exists()
    graph_result = validate_task_graph_file(graph_path, BLUEPRINT_PATH)
    assert graph_result["status"] == "PASS"


def test_requirement_blocks_missing_work_items() -> None:
    requirement = load_yaml_file(REQUIREMENT_PATH)
    requirement["work_items"] = []
    from tool_system.planner.requirement_graph import compile_requirement_to_task_graph
    blueprint = load_yaml_file(BLUEPRINT_PATH)

    result = compile_requirement_to_task_graph(requirement, blueprint)

    assert result["status"] == "BLOCK"
    assert "work_items must be a non-empty list" in result["reasons"]


def test_requirement_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
