from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Mapping
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



@dataclass(frozen=True)
class CodexCLIAdapterConfig:
    executable: str
    enabled: bool = False
    timeout_seconds: int = 120
    max_output_bytes: int = 1_048_576
    inherited_environment_names: tuple[str, ...] = ("PATH", "HOME", "LANG", "LC_ALL")

    def violations(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.executable or "/" in self.executable or "\\" in self.executable:
            reasons.append("Codex executable must be one owner-configured command name")
        if self.timeout_seconds < 1 or self.timeout_seconds > 3600:
            reasons.append("Codex timeout must be between 1 and 3600 seconds")
        if self.max_output_bytes < 1 or self.max_output_bytes > 16_777_216:
            reasons.append("Codex output limit must be between 1 and 16777216 bytes")
        forbidden = {"OPENAI_API_KEY", "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "ZHIPUAI_API_KEY"}
        if forbidden.intersection(self.inherited_environment_names):
            reasons.append("provider credential environment names are forbidden")
        return tuple(reasons)


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


class CodexCLISubscriptionWorkerAdapter:
    adapter_kind = "codex_cli_subscription_worker_adapter"

    def __init__(
        self,
        config: CodexCLIAdapterConfig,
        *,
        process_runner: ProcessRunner = subprocess.run,
        source_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.config = config
        self._process_runner = process_runner
        self._source_environment = source_environment if source_environment is not None else os.environ

    def run(self, request: AdapterRequest) -> AdapterResult:
        reasons = list(self.config.violations())
        prompt = request.context.get("prompt")
        workspace = request.context.get("workspace")
        authorization = request.context.get("subscription_worker_authorized")
        if not self.config.enabled:
            reasons.append("subscription worker adapter is disabled")
        if authorization is not True:
            reasons.append("subscription worker execution is not explicitly authorized")
        if request.execute is not True or request.calls_external_worker is not True:
            reasons.append("subscription worker request must explicitly authorize execution and external worker")
        if request.writes_target_repo or request.executes_target_repo_mutation or request.production_deployment:
            reasons.append("subscription worker cannot receive target mutation or production authority")
        if not isinstance(prompt, str) or not prompt.strip():
            reasons.append("structured subscription worker prompt is required")
        if not isinstance(workspace, str) or not workspace:
            reasons.append("isolated workspace identity is required")
        if reasons:
            return AdapterResult(
                adapter_id=request.adapter_id,
                role=request.role,
                action=request.action,
                status="BLOCK",
                adapter_kind=self.adapter_kind,
                execute=False,
                calls_external_worker=False,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
                evidence=["worker_adapter.subscription.preflight.block"],
                reasons=reasons,
                output={},
            )

        argv = [self.config.executable, "exec", "--json", "--skip-git-repo-check", str(prompt)]
        env = {
            name: self._source_environment[name]
            for name in self.config.inherited_environment_names
            if name in self._source_environment
        }
        try:
            completed = self._process_runner(
                argv,
                cwd=str(workspace),
                env=env,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return AdapterResult(
                adapter_id=request.adapter_id,
                role=request.role,
                action=request.action,
                status="BLOCK",
                adapter_kind=self.adapter_kind,
                execute=True,
                calls_external_worker=True,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
                evidence=["worker_adapter.subscription.process.block"],
                reasons=[f"subscription worker process failed closed: {type(exc).__name__}"],
                output={"raw_output_recorded": False},
            )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if len(stdout.encode()) + len(stderr.encode()) > self.config.max_output_bytes:
            return AdapterResult(
                adapter_id=request.adapter_id,
                role=request.role,
                action=request.action,
                status="BLOCK",
                adapter_kind=self.adapter_kind,
                execute=True,
                calls_external_worker=True,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
                evidence=["worker_adapter.subscription.output_limit.block"],
                reasons=["subscription worker output exceeded the configured byte limit"],
                output={"raw_output_recorded": False, "returncode": completed.returncode},
            )
        if completed.returncode != 0:
            return AdapterResult(
                adapter_id=request.adapter_id,
                role=request.role,
                action=request.action,
                status="BLOCK",
                adapter_kind=self.adapter_kind,
                execute=True,
                calls_external_worker=True,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
                evidence=["worker_adapter.subscription.process.block"],
                reasons=["subscription worker returned a nonzero status"],
                output={"returncode": completed.returncode, "raw_output_recorded": False},
            )
        try:
            records = [json.loads(line) for line in stdout.splitlines() if line.strip()]
            structured_result = records[-1]
            if not isinstance(structured_result, dict):
                raise ValueError("terminal record must be an object")
        except (json.JSONDecodeError, ValueError):
            return AdapterResult(
                adapter_id=request.adapter_id,
                role=request.role,
                action=request.action,
                status="BLOCK",
                adapter_kind=self.adapter_kind,
                execute=True,
                calls_external_worker=True,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
                evidence=["worker_adapter.subscription.structured_output.block"],
                reasons=["subscription worker did not return valid JSON object records"],
                output={"returncode": completed.returncode, "raw_output_recorded": False},
            )
        return AdapterResult(
            adapter_id=request.adapter_id,
            role=request.role,
            action=request.action,
            status="PASS",
            adapter_kind=self.adapter_kind,
            execute=True,
            calls_external_worker=True,
            writes_target_repo=False,
            executes_target_repo_mutation=False,
            production_deployment=False,
            evidence=["worker_adapter.subscription.structured_output.complete"],
            reasons=[],
            output={
                "returncode": completed.returncode,
                "structured_result": structured_result,
                "raw_output_recorded": False,
                "argv_shape": ["<configured-codex>", "exec", "--json", "--skip-git-repo-check", "<structured-prompt>"],
                "environment_names": sorted(env),
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
