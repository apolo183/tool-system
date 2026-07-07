from __future__ import annotations

from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.dag_planner import compile_blueprint_dag, topological_order, validate_dag


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
CHANGE_PLAN = ROOT / "examples" / "change_plans" / "tool_system_p7a_dag_planner.yaml"


def test_compile_p7_dag() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    dag = compile_blueprint_dag(blueprint, "P7_BLUEPRINT_TO_DAG_PLANNER")

    assert dag["status"] == "PASS"
    assert validate_dag(dag)["status"] == "PASS"
    assert topological_order(dag) == [
        "blueprint_intake",
        "task_decomposition",
        "change_plan",
        "verification",
        "audit",
    ]


def test_unknown_milestone_blocks() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    dag = compile_blueprint_dag(blueprint, "UNKNOWN")

    assert dag["status"] == "BLOCK"


def test_p7a_change_plan_validates() -> None:
    result = validate_change_plan(CHANGE_PLAN)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
