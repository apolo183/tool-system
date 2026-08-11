from __future__ import annotations

from typing import Mapping

from pathlib import Path

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.worker_adapter.contract import AdapterRequest, AdapterResult
from tool_system.worker_adapter.orchestration import (
    build_adapter_orchestration_record,
    build_subscription_development_worker,
    build_adapter_orchestration_record_from_worker_requests,
    write_adapter_orchestration_record,
)


def test_adapter_orchestration_record_passes_for_dry_run_requests() -> None:
    result = build_adapter_orchestration_record([
        AdapterRequest(
            adapter_id="adapter-role-step-001",
            role="evidence_collector",
            action="collect_evidence",
        ),
        AdapterRequest(
            adapter_id="adapter-role-step-002",
            role="audit_recorder",
            action="record_audit",
        ),
    ])

    assert result["status"] == "PASS"
    assert result["mode"] == "tool_system_worker_adapter_orchestration"
    assert result["execute"] is False
    assert result["calls_external_worker"] is False
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert result["production_deployment"] is False
    assert result["audit_record"]["adapter_request_count"] == 2
    assert result["audit_record"]["adapter_result_count"] == 2
    assert result["rollback_bundle"]["execute"] is False
    assert result["reasons"] == []


def test_adapter_orchestration_blocks_mutating_or_external_request() -> None:
    result = build_adapter_orchestration_record([
        AdapterRequest(
            adapter_id="adapter-role-step-003",
            role="patch_author",
            action="prepare_patch_preview",
            execute=True,
            calls_external_worker=True,
            writes_target_repo=True,
            executes_target_repo_mutation=True,
            production_deployment=True,
        )
    ])

    assert result["status"] == "BLOCK"
    assert result["audit_record"] == {}
    assert result["rollback_bundle"] == {}
    assert "adapter_request adapter-role-step-003 execute must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 calls_external_worker must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 writes_target_repo must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 executes_target_repo_mutation must be false" in result["reasons"]
    assert "adapter_request adapter-role-step-003 production_deployment must be false" in result["reasons"]
    assert "adapter_result adapter-role-step-003: request.execute must be false" in result["reasons"]


def test_adapter_orchestration_from_worker_requests() -> None:
    result = build_adapter_orchestration_record_from_worker_requests([
        WorkerRequest(
            step_id="role-step-004",
            task_id="verify",
            role="test_engineer",
            action="prepare_verification",
        )
    ])

    assert result["status"] == "PASS"
    assert result["audit_record"]["adapter_requests"][0]["adapter_id"] == "adapter-role-step-004"
    assert result["audit_record"]["adapter_results"][0]["adapter_kind"] == "dry_run_worker_adapter"


def test_write_adapter_orchestration_record(tmp_path: Path) -> None:
    result = write_adapter_orchestration_record(
        adapter_requests=[
            AdapterRequest(
                adapter_id="adapter-role-step-005",
                role="audit_recorder",
                action="record_audit",
            )
        ],
        audit_path=tmp_path / "adapter_orchestration.jsonl",
    )

    assert result["status"] == "PASS"
    assert Path(result["audit_path"]).exists()


class _FixtureSubscriptionAdapter:
    adapter_kind = "fixture_subscription_adapter"

    def __init__(self, structured_result: Mapping[str, object] | None) -> None:
        self.structured_result = structured_result
        self.requests: list[AdapterRequest] = []

    def run(self, request: AdapterRequest) -> AdapterResult:
        self.requests.append(request)
        return AdapterResult(
            adapter_id=request.adapter_id,
            role=request.role,
            action=request.action,
            status="PASS" if self.structured_result is not None else "BLOCK",
            adapter_kind=self.adapter_kind,
            execute=request.execute,
            calls_external_worker=request.calls_external_worker,
            writes_target_repo=False,
            executes_target_repo_mutation=False,
            production_deployment=False,
            output=(
                {"structured_result": dict(self.structured_result)}
                if self.structured_result is not None
                else {}
            ),
        )


def test_subscription_development_worker_maps_canonical_loop_request() -> None:
    patch = {
        "operations": [{"op": "add", "path": "src/new.py", "content": "pass\n"}],
        "usage": {"duration_ms": 2, "cost_microunits": 0},
    }
    adapter = _FixtureSubscriptionAdapter(patch)
    worker = build_subscription_development_worker(
        adapter=adapter,
        request_template=AdapterRequest(
            adapter_id="subscription-loop",
            role="patch_author",
            action="implement",
            context={
                "workspace": "/isolated/workspace",
                "subscription_worker_authorized": True,
            },
        ),
    )

    result = worker({"task_digest": "a" * 64, "attempt_number": 1})

    assert result == patch
    assert len(adapter.requests) == 1
    request = adapter.requests[0]
    assert request.execute is True
    assert request.calls_external_worker is True
    assert request.writes_target_repo is False
    assert request.executes_target_repo_mutation is False
    assert request.production_deployment is False
    assert request.context["prompt"] == (
        '{"attempt_number":1,"task_digest":"'
        + "a" * 64
        + '"}'
    )


def test_subscription_development_worker_fails_closed_on_unusable_adapter_result() -> None:
    adapter = _FixtureSubscriptionAdapter(None)
    worker = build_subscription_development_worker(
        adapter=adapter,
        request_template=AdapterRequest(
            adapter_id="subscription-loop",
            role="patch_author",
            action="implement",
        ),
    )

    assert worker({"attempt_number": 1}) == {
        "subscription_worker_bridge_blocked": {
            "terminal_code": "SUBSCRIPTION_WORKER_RESULT_BLOCKED"
        }
    }
