from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.dag_planner import compile_blueprint_dag, topological_order, validate_dag


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_compile_p6_dag() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    dag = compile_blueprint_dag(blueprint, "P6_RUNNER_PRODUCTIZATION")

    assert dag["status"] == "PASS"
    assert validate_dag(dag)["status"] == "PASS"
    assert topological_order(dag)[0] == "blueprint_intake"


def test_unknown_milestone_blocks() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    dag = compile_blueprint_dag(blueprint, "UNKNOWN")

    assert dag["status"] == "BLOCK"
