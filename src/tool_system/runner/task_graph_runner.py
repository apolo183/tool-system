from __future__ import annotations

from pathlib import Path
from typing import Any

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import compile_task_graph_to_batch
from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.runner.task_runner import run_batch_pipeline


def run_task_graph_pipeline(
    graph_path: str | Path,
    blueprint_path: str | Path = "blueprint/tool_system_v0.yaml",
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    active_gates_path: str | Path | None = "examples/active_gates.yaml",
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    graph = load_yaml_file(graph_path)
    blueprint = load_yaml_file(blueprint_path)
    compiled = compile_task_graph_to_batch(graph, blueprint)

    batch_result: dict[str, object] | None = None
    reasons = list(compiled.get("reasons") or [])
    if compiled["status"] == "PASS" and compiled.get("batch") is not None:
        batch_result = run_batch_pipeline(
            batch=compiled["batch"],
            policy_path=policy_path,
            autonomy_policy_path=autonomy_policy_path,
            active_gates_path=active_gates_path,
            cwd=cwd,
            execute_commands=execute_commands,
        )
        if batch_result["status"] != "PASS":
            reasons.append("compiled batch execution failed")
            reasons.extend(str(reason) for reason in batch_result.get("reasons", []))

    output = {
        "status": "PASS" if not reasons else "BLOCK",
        "mode": "tool_system_task_graph_runner",
        "graph_path": str(graph_path),
        "blueprint_path": str(blueprint_path),
        "policy_path": str(policy_path),
        "autonomy_policy_path": str(autonomy_policy_path),
        "active_gates_path": str(active_gates_path) if active_gates_path is not None else None,
        "compiled_graph": compiled,
        "batch_result": batch_result,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output
