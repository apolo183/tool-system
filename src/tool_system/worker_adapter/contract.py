from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
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
    termination_grace_seconds: int = 2
    max_prompt_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    inherited_environment_names: tuple[str, ...] = ("PATH", "HOME", "LANG", "LC_ALL")

    def violations(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.executable or "/" in self.executable or "\\" in self.executable:
            reasons.append("Codex executable must be one owner-configured command name")
        if self.timeout_seconds < 1 or self.timeout_seconds > 3600:
            reasons.append("Codex timeout must be between 1 and 3600 seconds")
        if self.termination_grace_seconds < 1 or self.termination_grace_seconds > 30:
            reasons.append("Codex termination grace must be between 1 and 30 seconds")
        if self.max_prompt_bytes < 1 or self.max_prompt_bytes > 16_777_216:
            reasons.append("Codex prompt limit must be between 1 and 16777216 bytes")
        if self.max_output_bytes < 1 or self.max_output_bytes > 16_777_216:
            reasons.append("Codex output limit must be between 1 and 16777216 bytes")
        forbidden = {"OPENAI_API_KEY", "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "ZHIPUAI_API_KEY"}
        if forbidden.intersection(self.inherited_environment_names):
            reasons.append("provider credential environment names are forbidden")
        return tuple(reasons)


_PATCH_RESULT_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["operations"],
    "properties": {
        "operations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["op", "path", "content"],
                        "properties": {
                            "op": {"const": "add"},
                            "path": {"type": "string", "minLength": 1},
                            "content": {"type": "string"},
                            "expected_sha256": {"type": ["string", "null"]},
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["op", "path", "expected_sha256", "content"],
                        "properties": {
                            "op": {"const": "replace"},
                            "path": {"type": "string", "minLength": 1},
                            "expected_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                            "content": {"type": "string"},
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["op", "path", "expected_sha256"],
                        "properties": {
                            "op": {"const": "delete"},
                            "path": {"type": "string", "minLength": 1},
                            "expected_sha256": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{64}$",
                            },
                        },
                    },
                ]
            },
        },
        "usage": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "duration_ms": {"type": "integer", "minimum": 0},
                "cost_microunits": {"type": "integer", "minimum": 0},
            },
        },
        "material_evidence": {
            "type": ["string", "array", "object", "null"],
        },
    },
}


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
PopenFactory = Callable[..., subprocess.Popen[str]]
GroupKiller = Callable[[int, int], None]


def _kill_process_group(group_id: int, sig: int) -> None:
    os.killpg(group_id, sig)


def _wait_for_process(process: subprocess.Popen[str], timeout: int) -> bool:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return True


def _terminate_process_group(
    process: subprocess.Popen[str],
    *,
    grace_seconds: int,
    platform_name: str,
    group_killer: GroupKiller,
) -> None:
    if platform_name == "posix":
        try:
            group_killer(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        if _wait_for_process(process, grace_seconds):
            return
        try:
            group_killer(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        _wait_for_process(process, grace_seconds)
        return
    try:
        process.terminate()
    except OSError:
        return
    if _wait_for_process(process, grace_seconds):
        return
    try:
        process.kill()
    except OSError:
        return
    _wait_for_process(process, grace_seconds)


def _run_codex_process(
    argv: list[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    shell: bool,
    check: bool,
    capture_output: bool,
    text: bool,
    timeout: int,
    input: str,
    termination_grace_seconds: int,
    popen_factory: PopenFactory = subprocess.Popen,
    platform_name: str = os.name,
    group_killer: GroupKiller = _kill_process_group,
) -> subprocess.CompletedProcess[str]:
    if shell or check or not capture_output or not text:
        raise ValueError("unsupported Codex process boundary")
    popen_options: dict[str, object] = {
        "cwd": cwd,
        "env": dict(env),
        "shell": False,
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    if platform_name == "posix":
        popen_options["start_new_session"] = True
    process = popen_factory(argv, **popen_options)
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate_process_group(
            process,
            grace_seconds=termination_grace_seconds,
            platform_name=platform_name,
            group_killer=group_killer,
        )
        raise
    return subprocess.CompletedProcess(
        argv,
        process.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _write_private_file(path: Path, content: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)


def _read_private_result(path: Path, max_bytes: int) -> object:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    with os.fdopen(descriptor, "rb") as handle:
        file_stat = os.fstat(handle.fileno())
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("terminal result must be a regular file")
        if file_stat.st_size > max_bytes:
            raise OverflowError("terminal result exceeded the configured byte limit")
        payload = handle.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise OverflowError("terminal result exceeded the configured byte limit")
    return json.loads(payload.decode("utf-8"))


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value) <= set("0123456789abcdef")
    )


def _validate_structured_patch(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("structured patch must be an object")
    if set(value) - {"operations", "usage", "material_evidence"}:
        raise ValueError("structured patch contains authority expansion")
    operations = value.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("structured patch operations are required")
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError("patch operation must be an object")
        op = operation.get("op")
        path = operation.get("path")
        if not isinstance(path, str) or not path:
            raise ValueError("patch path is required")
        if op == "add":
            if (
                set(operation) - {"op", "path", "content", "expected_sha256"}
                or not isinstance(operation.get("content"), str)
                or operation.get("expected_sha256") is not None
            ):
                raise ValueError("invalid add operation")
        elif op == "replace":
            if (
                set(operation) != {"op", "path", "content", "expected_sha256"}
                or not isinstance(operation.get("content"), str)
                or not _valid_sha256(operation.get("expected_sha256"))
            ):
                raise ValueError("invalid replace operation")
        elif op == "delete":
            if (
                set(operation) != {"op", "path", "expected_sha256"}
                or not _valid_sha256(operation.get("expected_sha256"))
            ):
                raise ValueError("invalid delete operation")
        else:
            raise ValueError("unsupported patch operation")
    usage = value.get("usage", {})
    if not isinstance(usage, dict) or set(usage) - {"duration_ms", "cost_microunits"}:
        raise ValueError("invalid structured patch usage")
    for name in ("duration_ms", "cost_microunits"):
        item = usage.get(name, 0)
        if type(item) is not int or item < 0:
            raise ValueError("invalid structured patch usage")
    return value


def _valid_jsonl_events(stdout: str) -> bool:
    try:
        return all(
            isinstance(json.loads(line), dict)
            for line in stdout.splitlines()
            if line.strip()
        )
    except json.JSONDecodeError:
        return False


class CodexCLISubscriptionWorkerAdapter:
    adapter_kind = "codex_cli_subscription_worker_adapter"

    def __init__(
        self,
        config: CodexCLIAdapterConfig,
        *,
        process_runner: ProcessRunner = _run_codex_process,
        source_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.config = config
        self._process_runner = process_runner
        self._source_environment = source_environment if source_environment is not None else os.environ

    def _result(
        self,
        request: AdapterRequest,
        *,
        status: AdapterStatus,
        execute: bool,
        evidence: list[str],
        reasons: list[str],
        output: dict[str, object],
    ) -> AdapterResult:
        return AdapterResult(
            adapter_id=request.adapter_id,
            role=request.role,
            action=request.action,
            status=status,
            adapter_kind=self.adapter_kind,
            execute=execute,
            calls_external_worker=execute,
            writes_target_repo=False,
            executes_target_repo_mutation=False,
            production_deployment=False,
            evidence=evidence,
            reasons=reasons,
            output=output,
        )

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
        elif len(prompt.encode("utf-8")) > self.config.max_prompt_bytes:
            reasons.append("subscription worker prompt exceeded the configured byte limit")
        if not isinstance(workspace, str) or not workspace:
            reasons.append("isolated workspace identity is required")
        if reasons:
            return self._result(
                request,
                status="BLOCK",
                execute=False,
                evidence=["worker_adapter.subscription.preflight.block"],
                reasons=reasons,
                output={},
            )

        env = {
            name: self._source_environment[name]
            for name in self.config.inherited_environment_names
            if name in self._source_environment
        }
        schema_payload = json.dumps(
            _PATCH_RESULT_SCHEMA,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="tool-system-codex-worker-"
        ) as temporary_directory:
            temporary_root = Path(temporary_directory)
            os.chmod(temporary_root, 0o700)
            schema_path = temporary_root / "structured-patch.schema.json"
            result_path = temporary_root / "structured-patch.result.json"
            _write_private_file(schema_path, schema_payload)
            _write_private_file(result_path, b"")
            argv = [
                self.config.executable,
                "--ask-for-approval",
                "never",
                "exec",
                "--json",
                "--ephemeral",
                "--ignore-user-config",
                "--sandbox",
                "read-only",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(result_path),
                "--skip-git-repo-check",
                "-",
            ]
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
                    input=prompt,
                    termination_grace_seconds=self.config.termination_grace_seconds,
                )
            except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.process.block"],
                    reasons=[f"subscription worker process failed closed: {type(exc).__name__}"],
                    output={"raw_output_recorded": False},
                )

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            if (
                len(stdout.encode("utf-8")) + len(stderr.encode("utf-8"))
                > self.config.max_output_bytes
            ):
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.output_limit.block"],
                    reasons=["subscription worker output exceeded the configured byte limit"],
                    output={
                        "raw_output_recorded": False,
                        "returncode": completed.returncode,
                    },
                )
            if completed.returncode != 0:
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.process.block"],
                    reasons=["subscription worker returned a nonzero status"],
                    output={
                        "returncode": completed.returncode,
                        "raw_output_recorded": False,
                    },
                )
            if not _valid_jsonl_events(stdout):
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.event_stream.block"],
                    reasons=["subscription worker event stream was not valid JSONL objects"],
                    output={
                        "returncode": completed.returncode,
                        "raw_output_recorded": False,
                    },
                )
            try:
                structured_result = _validate_structured_patch(
                    _read_private_result(result_path, self.config.max_output_bytes)
                )
            except OverflowError:
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.output_limit.block"],
                    reasons=["subscription worker output exceeded the configured byte limit"],
                    output={
                        "raw_output_recorded": False,
                        "returncode": completed.returncode,
                    },
                )
            except (json.JSONDecodeError, OSError, UnicodeDecodeError, ValueError):
                return self._result(
                    request,
                    status="BLOCK",
                    execute=True,
                    evidence=["worker_adapter.subscription.structured_output.block"],
                    reasons=["subscription worker did not return a valid schema-bound structured patch"],
                    output={
                        "returncode": completed.returncode,
                        "raw_output_recorded": False,
                    },
                )

        return self._result(
            request,
            status="PASS",
            execute=True,
            evidence=["worker_adapter.subscription.structured_output.complete"],
            reasons=[],
            output={
                "returncode": completed.returncode,
                "structured_result": structured_result,
                "raw_output_recorded": False,
                "prompt_on_stdin": True,
                "sandbox_mode": "read-only",
                "session_persistence": "ephemeral",
                "argv_shape": [
                    "<configured-codex>",
                    "--ask-for-approval",
                    "never",
                    "exec",
                    "--json",
                    "--ephemeral",
                    "--ignore-user-config",
                    "--sandbox",
                    "read-only",
                    "--output-schema",
                    "<creator-owned-schema>",
                    "--output-last-message",
                    "<creator-owned-result>",
                    "--skip-git-repo-check",
                    "-",
                ],
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
