from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from tool_system.agent_worker.interface import WorkerRequest

AdapterStatus = Literal["PASS", "BLOCK"]


@dataclass(frozen=True)
class AdapterRequest:
    adapter_id: str
    role: str
    action: str
    task_id: object | None = None
    input_refs: list[object] = field(default_factory=list)
    context: dict[str, object] = field(default_factory=dict)
    execute: bool = False
    calls_external_worker: bool = False
    writes_target_repo: bool = False
    executes_target_repo_mutation: bool = False
    production_deployment: bool = False


@dataclass(frozen=True)
class AdapterResult:
    adapter_id: str
    role: str
    action: str
    status: AdapterStatus
    adapter_kind: str
    execute: bool
    calls_external_worker: bool
    writes_target_repo: bool
    executes_target_repo_mutation: bool
    production_deployment: bool
    evidence: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    output: dict[str, object] = field(default_factory=dict)

    def to_record(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "role": self.role,
            "action": self.action,
            "status": self.status,
            "adapter_kind": self.adapter_kind,
            "execute": self.execute,
            "calls_external_worker": self.calls_external_worker,
            "writes_target_repo": self.writes_target_repo,
            "executes_target_repo_mutation": self.executes_target_repo_mutation,
            "production_deployment": self.production_deployment,
            "evidence": list(self.evidence),
            "reasons": list(self.reasons),
            "output": dict(self.output),
        }


class WorkerAdapter(Protocol):
    adapter_kind: str

    def run(self, request: AdapterRequest) -> AdapterResult:
        ...


class DryRunWorkerAdapter:
    adapter_kind = "dry_run_worker_adapter"

    def run(self, request: AdapterRequest) -> AdapterResult:
        reasons = _adapter_request_violations(request)
        status: AdapterStatus = "BLOCK" if reasons else "PASS"
        return AdapterResult(
            adapter_id=request.adapter_id,
            role=request.role,
            action=request.action,
            status=status,
            adapter_kind=self.adapter_kind,
            execute=False,
            calls_external_worker=False,
            writes_target_repo=False,
            executes_target_repo_mutation=False,
            production_deployment=False,
            evidence=[
                "worker_adapter_contract.no_mutation_dry_run",
                f"role={request.role}",
                f"action={request.action}",
            ],
            reasons=reasons,
            output={
                "mode": "dry_run_record_only",
                "requested_execute": request.execute,
                "requested_calls_external_worker": request.calls_external_worker,
                "requested_writes_target_repo": request.writes_target_repo,
                "requested_executes_target_repo_mutation": request.executes_target_repo_mutation,
                "requested_production_deployment": request.production_deployment,
            },
        )


def _adapter_request_violations(request: AdapterRequest) -> list[str]:
    reasons: list[str] = []
    if request.execute:
        reasons.append("request.execute must be false")
    if request.calls_external_worker:
        reasons.append("request.calls_external_worker must be false")
    if request.writes_target_repo:
        reasons.append("request.writes_target_repo must be false")
    if request.executes_target_repo_mutation:
        reasons.append("request.executes_target_repo_mutation must be false")
    if request.production_deployment:
        reasons.append("request.production_deployment must be false")
    return reasons


def _true_only(value: object) -> bool:
    return value is True


def build_adapter_request_from_worker_request(
    request: WorkerRequest,
    adapter_id: str | None = None,
) -> AdapterRequest:
    return AdapterRequest(
        adapter_id=adapter_id or f"adapter-{request.step_id}",
        role=request.role,
        action=request.action,
        task_id=request.task_id,
        input_refs=[request.task_manifest, request.change_plan],
        context={"source": "worker_request", **dict(request.context)},
        execute=_true_only(request.execute),
        calls_external_worker=False,
        writes_target_repo=_true_only(request.writes_target_repo),
        executes_target_repo_mutation=_true_only(request.executes_target_repo_mutation),
        production_deployment=False,
    )


def run_adapter_requests(
    requests: list[AdapterRequest],
    adapter: WorkerAdapter | None = None,
) -> list[dict[str, object]]:
    active_adapter = adapter or DryRunWorkerAdapter()
    return [active_adapter.run(request).to_record() for request in requests]
