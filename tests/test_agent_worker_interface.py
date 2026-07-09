from __future__ import annotations

from pathlib import Path

from tool_system.agent_worker.interface import (
    NoMutationAgentWorker,
    WorkerRequest,
    build_worker_request_from_role_step,
)
from tool_system.runtime.role_runtime import build_role_runtime_plan_file


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "examples" / "task_graphs" / "tool_system_p7a_task_graph.yaml"
BLUEPRINT_PATH = ROOT / "blueprint" / "tool_system_v0.yaml"


def test_no_mutation_worker_records_pass_without_execution() -> None:
    request = WorkerRequest(
        step_id="role-step-001",
        task_id="collect-evidence",
        role="evidence_collector",
        action="collect_evidence",
    )

    result = NoMutationAgentWorker().run(request)

    assert result.status == "PASS"
    assert result.worker_kind == "no_mutation_agent_worker"
    assert result.execute is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.reasons == []
    assert result.output["mode"] == "record_only"


def test_no_mutation_worker_blocks_requested_execution() -> None:
    request = WorkerRequest(
        step_id="role-step-002",
        task_id="prepare-patch",
        role="patch_author",
        action="prepare_patch_preview",
        execute=True,
        writes_target_repo=True,
        executes_target_repo_mutation=True,
    )

    result = NoMutationAgentWorker().run(request)

    assert result.status == "BLOCK"
    assert result.execute is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.reasons == [
        "request.execute must be false",
        "request.writes_target_repo must be false",
        "request.executes_target_repo_mutation must be false",
    ]


def test_worker_request_from_role_step_preserves_no_mutation_flags() -> None:
    request = build_worker_request_from_role_step({
        "step_id": "role-step-003",
        "task_id": "verify",
        "role": "test_engineer",
        "action": "prepare_verification",
        "depends_on": ["role-step-001"],
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
    })

    assert request.step_id == "role-step-003"
    assert request.role == "test_engineer"
    assert request.action == "prepare_verification"
    assert request.depends_on == ["role-step-001"]
    assert request.execute is False
    assert request.writes_target_repo is False
    assert request.executes_target_repo_mutation is False


def test_role_runtime_includes_no_mutation_worker_results(tmp_path: Path) -> None:
    result = build_role_runtime_plan_file(
        graph_path=GRAPH_PATH,
        blueprint_path=BLUEPRINT_PATH,
        audit_path=tmp_path / "role_runtime.jsonl",
    )

    assert result["status"] == "PASS"
    assert result["worker_result_count"] == result["role_step_count"]
    assert all(record["status"] == "PASS" for record in result["worker_results"])
    assert all(record["worker_kind"] == "no_mutation_agent_worker" for record in result["worker_results"])
    assert all(record["execute"] is False for record in result["worker_results"])
    assert all(record["writes_target_repo"] is False for record in result["worker_results"])
    assert all(record["executes_target_repo_mutation"] is False for record in result["worker_results"])
