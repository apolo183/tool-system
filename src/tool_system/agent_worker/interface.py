from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

WorkerStatus = Literal["PASS", "BLOCK"]


@dataclass(frozen=True)
class WorkerRequest:
    step_id: str
    task_id: object | None
    role: str
    action: str
    task_manifest: object | None = None
    change_plan: object | None = None
    depends_on: list[object] = field(default_factory=list)
    context: dict[str, object] = field(default_factory=dict)
    execute: bool = False
    writes_target_repo: bool = False
    executes_target_repo_mutation: bool = False


@dataclass(frozen=True)
class WorkerResult:
    step_id: str
    task_id: object | None
    role: str
    action: str
    status: WorkerStatus
    worker_kind: str
    execute: bool
    writes_target_repo: bool
    executes_target_repo_mutation: bool
    evidence: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    output: dict[str, object] = field(default_factory=dict)

    def to_record(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "role": self.role,
            "action": self.action,
            "status": self.status,
            "worker_kind": self.worker_kind,
            "execute": self.execute,
            "writes_target_repo": self.writes_target_repo,
            "executes_target_repo_mutation": self.executes_target_repo_mutation,
            "evidence": list(self.evidence),
            "reasons": list(self.reasons),
            "output": dict(self.output),
        }


class AgentWorker(Protocol):
    worker_kind: str

    def run(self, request: WorkerRequest) -> WorkerResult:
        ...


class NoMutationAgentWorker:
    worker_kind = "no_mutation_agent_worker"

    def run(self, request: WorkerRequest) -> WorkerResult:
        reasons = _no_mutation_violations(request)
        status: WorkerStatus = "BLOCK" if reasons else "PASS"
        return WorkerResult(
            step_id=request.step_id,
            task_id=request.task_id,
            role=request.role,
            action=request.action,
            status=status,
            worker_kind=self.worker_kind,
            execute=False,
            writes_target_repo=False,
            executes_target_repo_mutation=False,
            evidence=[
                "agent_worker_interface.no_mutation_contract",
                f"role={request.role}",
                f"action={request.action}",
            ],
            reasons=reasons,
            output={
                "mode": "record_only",
                "requested_execute": request.execute,
                "requested_writes_target_repo": request.writes_target_repo,
                "requested_executes_target_repo_mutation": request.executes_target_repo_mutation,
            },
        )


def _no_mutation_violations(request: WorkerRequest) -> list[str]:
    reasons: list[str] = []
    if request.execute:
        reasons.append("request.execute must be false")
    if request.writes_target_repo:
        reasons.append("request.writes_target_repo must be false")
    if request.executes_target_repo_mutation:
        reasons.append("request.executes_target_repo_mutation must be false")
    return reasons


def _list_value(value: Any) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _true_only(value: Any) -> bool:
    return value is True


def build_worker_request_from_role_step(step: dict[str, Any]) -> WorkerRequest:
    return WorkerRequest(
        step_id=str(step.get("step_id") or ""),
        task_id=step.get("task_id"),
        role=str(step.get("role") or ""),
        action=str(step.get("action") or "record_role_step"),
        task_manifest=step.get("task_manifest"),
        change_plan=step.get("change_plan"),
        depends_on=_list_value(step.get("depends_on")),
        context={"source": "role_runtime_step"},
        execute=_true_only(step.get("execute")),
        writes_target_repo=_true_only(step.get("writes_target_repo")),
        executes_target_repo_mutation=_true_only(step.get("executes_target_repo_mutation")),
    )


def run_role_steps_with_worker(
    role_steps: list[dict[str, Any]],
    worker: AgentWorker | None = None,
) -> list[dict[str, object]]:
    active_worker = worker or NoMutationAgentWorker()
    return [
        active_worker.run(build_worker_request_from_role_step(step)).to_record()
        for step in role_steps
    ]
