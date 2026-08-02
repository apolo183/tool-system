from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runtime.agent_scheduler import build_agent_execution_plan


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_scheduler_assigns_roles_from_task_graph() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    graph = {
        "tasks": [
            {"task_id": "a", "role": "evidence_collector"},
            {"task_id": "b", "role": "test_engineer"},
            {"task_id": "c", "role": "audit_recorder"},
        ]
    }

    result = build_agent_execution_plan(graph, blueprint)

    assert result["status"] == "PASS"
    assert result["task_count"] == 3
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_scheduler_blocks_unknown_roles() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    result = build_agent_execution_plan({"tasks": [{"task_id": "x", "role": "unknown"}]}, blueprint)

    assert result["status"] == "BLOCK"
