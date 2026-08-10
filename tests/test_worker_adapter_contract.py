from __future__ import annotations

import json
import signal
import subprocess
from pathlib import Path

import pytest

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.worker_adapter.contract import (
    AdapterRequest,
    CodexCLIAdapterConfig,
    CodexCLISubscriptionWorkerAdapter,
    DryRunWorkerAdapter,
    _run_codex_process,
    build_adapter_request_from_worker_request,
    run_adapter_requests,
)


def test_dry_run_worker_adapter_records_pass_without_execution() -> None:
    request = AdapterRequest(
        adapter_id="adapter-role-step-001",
        role="evidence_collector",
        action="collect_evidence",
    )

    result = DryRunWorkerAdapter().run(request)

    assert result.status == "PASS"
    assert result.adapter_kind == "dry_run_worker_adapter"
    assert result.execute is False
    assert result.calls_external_worker is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production_deployment is False
    assert result.reasons == []
    assert result.output["mode"] == "dry_run_record_only"


def test_dry_run_worker_adapter_blocks_external_and_mutating_requests() -> None:
    request = AdapterRequest(
        adapter_id="adapter-role-step-002",
        role="patch_author",
        action="prepare_patch_preview",
        execute=True,
        calls_external_worker=True,
        writes_target_repo=True,
        executes_target_repo_mutation=True,
        production_deployment=True,
    )

    result = DryRunWorkerAdapter().run(request)

    assert result.status == "BLOCK"
    assert result.execute is False
    assert result.calls_external_worker is False
    assert result.writes_target_repo is False
    assert result.executes_target_repo_mutation is False
    assert result.production_deployment is False
    assert result.reasons == [
        "request.execute must be false",
        "request.calls_external_worker must be false",
        "request.writes_target_repo must be false",
        "request.executes_target_repo_mutation must be false",
        "request.production_deployment must be false",
    ]


def test_adapter_request_from_worker_request_preserves_no_mutation_boundary() -> None:
    worker_request = WorkerRequest(
        step_id="role-step-003",
        task_id="verify",
        role="test_engineer",
        action="prepare_verification",
        task_manifest="examples/task_manifests/tool_system_role_runtime.yaml",
        change_plan="examples/change_plans/tool_system_role_runtime.yaml",
    )

    adapter_request = build_adapter_request_from_worker_request(worker_request)

    assert adapter_request.adapter_id == "adapter-role-step-003"
    assert adapter_request.role == "test_engineer"
    assert adapter_request.action == "prepare_verification"
    assert adapter_request.input_refs == [
        "examples/task_manifests/tool_system_role_runtime.yaml",
        "examples/change_plans/tool_system_role_runtime.yaml",
    ]
    assert adapter_request.execute is False
    assert adapter_request.calls_external_worker is False
    assert adapter_request.writes_target_repo is False
    assert adapter_request.executes_target_repo_mutation is False
    assert adapter_request.production_deployment is False


def test_run_adapter_requests_uses_dry_run_adapter_by_default() -> None:
    records = run_adapter_requests([
        AdapterRequest(
            adapter_id="adapter-role-step-004",
            role="audit_recorder",
            action="record_audit",
        )
    ])

    assert records == [
        {
            "adapter_id": "adapter-role-step-004",
            "role": "audit_recorder",
            "action": "record_audit",
            "status": "PASS",
            "adapter_kind": "dry_run_worker_adapter",
            "execute": False,
            "calls_external_worker": False,
            "writes_target_repo": False,
            "executes_target_repo_mutation": False,
            "production_deployment": False,
            "evidence": [
                "worker_adapter_contract.no_mutation_dry_run",
                "role=audit_recorder",
                "action=record_audit",
            ],
            "reasons": [],
            "output": {
                "mode": "dry_run_record_only",
                "requested_execute": False,
                "requested_calls_external_worker": False,
                "requested_writes_target_repo": False,
                "requested_executes_target_repo_mutation": False,
                "requested_production_deployment": False,
            },
        }
    ]


def _subscription_request(**overrides: object) -> AdapterRequest:
    values: dict[str, object] = {
        "adapter_id": "subscription-001",
        "role": "patch_author",
        "action": "prepare_patch",
        "context": {
            "prompt": '{"task_id":"fixture-task"}',
            "workspace": "/isolated/workspace",
            "subscription_worker_authorized": True,
        },
        "execute": True,
        "calls_external_worker": True,
    }
    values.update(overrides)
    return AdapterRequest(**values)


def _structured_patch() -> dict[str, object]:
    return {
        "operations": [
            {
                "op": "add",
                "path": "src/app.py",
                "content": "return 1\n",
            }
        ],
        "usage": {"duration_ms": 3, "cost_microunits": 0},
        "material_evidence": "fake-process fixture",
    }


def _write_final_result(argv: list[str], value: object) -> None:
    output_path = Path(argv[argv.index("--output-last-message") + 1])
    output_path.write_text(json.dumps(value), encoding="utf-8")


def test_codex_subscription_adapter_is_disabled_by_default() -> None:
    calls: list[object] = []
    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex"),
        process_runner=lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = adapter.run(_subscription_request())

    assert result.status == "BLOCK"
    assert result.execute is False
    assert result.calls_external_worker is False
    assert result.reasons == ["subscription worker adapter is disabled"]
    assert calls == []


def test_codex_subscription_adapter_uses_schema_final_message_stdin_and_minimal_environment() -> None:
    observed: dict[str, object] = {}

    def fake_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        schema_path = Path(argv[argv.index("--output-schema") + 1])
        output_path = Path(argv[argv.index("--output-last-message") + 1])
        observed["argv"] = argv
        observed["schema"] = json.loads(schema_path.read_text(encoding="utf-8"))
        observed["schema_mode"] = schema_path.stat().st_mode & 0o777
        observed["result_mode"] = output_path.stat().st_mode & 0o777
        observed["temporary_parent_shared"] = schema_path.parent == output_path.parent
        observed.update(kwargs)
        _write_final_result(argv, _structured_patch())
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout='{"type":"thread.started"}\n{"type":"turn.completed"}\n',
            stderr="",
        )

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(
            executable="codex",
            enabled=True,
            timeout_seconds=17,
            termination_grace_seconds=3,
            inherited_environment_names=("PATH", "LANG"),
        ),
        process_runner=fake_runner,
        source_environment={
            "PATH": "/bin",
            "LANG": "C",
            "OPENAI_API_KEY": "not-forwarded",
        },
    )

    result = adapter.run(_subscription_request())

    assert result.status == "PASS"
    argv = observed["argv"]
    assert isinstance(argv, list)
    assert argv[:7] == [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--output-schema",
    ]
    assert argv[8] == "--output-last-message"
    assert argv[10:] == ["--skip-git-repo-check", "-"]
    assert '{"task_id":"fixture-task"}' not in argv
    assert observed["input"] == '{"task_id":"fixture-task"}'
    assert observed["cwd"] == "/isolated/workspace"
    assert observed["env"] == {"PATH": "/bin", "LANG": "C"}
    assert observed["shell"] is False
    assert observed["timeout"] == 17
    assert observed["termination_grace_seconds"] == 3
    assert observed["schema"]["additionalProperties"] is False
    assert observed["schema"]["required"] == ["operations"]
    assert observed["schema_mode"] == 0o600
    assert observed["result_mode"] == 0o600
    assert observed["temporary_parent_shared"] is True
    assert result.output["raw_output_recorded"] is False
    assert result.output["structured_result"] == _structured_patch()
    assert result.output["environment_names"] == ["LANG", "PATH"]
    assert result.output["prompt_on_stdin"] is True
    assert result.output["sandbox_mode"] == "read-only"
    assert result.output["session_persistence"] == "ephemeral"
    assert "<creator-owned-schema>" in result.output["argv_shape"]
    assert "<creator-owned-result>" in result.output["argv_shape"]


def test_codex_subscription_adapter_blocks_credentials_mutation_and_missing_authority() -> None:
    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(
            executable="codex",
            enabled=True,
            inherited_environment_names=("PATH", "OPENAI_API_KEY"),
        )
    )
    request = _subscription_request(
        context={"prompt": "fixture", "workspace": "/tmp/work"},
        writes_target_repo=True,
    )

    result = adapter.run(request)

    assert result.status == "BLOCK"
    assert "provider credential environment names are forbidden" in result.reasons
    assert "subscription worker execution is not explicitly authorized" in result.reasons
    assert "subscription worker cannot receive target mutation or production authority" in result.reasons


def test_codex_subscription_adapter_fails_closed_on_timeout_and_event_output_limit() -> None:
    def timeout_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="codex", timeout=1)

    timeout_adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True),
        process_runner=timeout_runner,
    )
    timeout = timeout_adapter.run(_subscription_request())
    assert timeout.status == "BLOCK"
    assert timeout.reasons == ["subscription worker process failed closed: TimeoutExpired"]

    output_adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True, max_output_bytes=4),
        process_runner=lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout="12345", stderr=""
        ),
    )
    output = output_adapter.run(_subscription_request())
    assert output.status == "BLOCK"
    assert output.reasons == ["subscription worker output exceeded the configured byte limit"]


def test_codex_subscription_adapter_fails_closed_on_terminal_result_limit() -> None:
    def oversized_result(
        argv: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        output_path = Path(argv[argv.index("--output-last-message") + 1])
        output_path.write_text("x" * 65, encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(
            executable="codex",
            enabled=True,
            max_output_bytes=64,
        ),
        process_runner=oversized_result,
    )

    result = adapter.run(_subscription_request())

    assert result.status == "BLOCK"
    assert result.reasons == [
        "subscription worker output exceeded the configured byte limit"
    ]


@pytest.mark.parametrize(
    "terminal_value",
    [
        "not-an-object",
        {"operations": []},
        {
            "operations": [
                {
                    "op": "add",
                    "path": "src/app.py",
                    "content": "x",
                }
            ],
            "acceptance_set": ["invented-authority"],
        },
        {
            "operations": [
                {
                    "op": "delete",
                    "path": "src/app.py",
                    "expected_sha256": "bad",
                }
            ]
        },
    ],
)
def test_codex_subscription_adapter_rejects_invalid_schema_bound_patch(
    terminal_value: object,
) -> None:
    def invalid_result(
        argv: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        _write_final_result(argv, terminal_value)
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout='{"type":"turn.completed"}\n',
            stderr="",
        )

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True),
        process_runner=invalid_result,
    )

    result = adapter.run(_subscription_request())

    assert result.status == "BLOCK"
    assert result.reasons == [
        "subscription worker did not return a valid schema-bound structured patch"
    ]
    assert result.output == {"returncode": 0, "raw_output_recorded": False}


def test_codex_subscription_adapter_rejects_invalid_jsonl_event_stream() -> None:
    def invalid_events(
        argv: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        _write_final_result(argv, _structured_patch())
        return subprocess.CompletedProcess(argv, 0, stdout="not-json\n", stderr="")

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True),
        process_runner=invalid_events,
    )

    result = adapter.run(_subscription_request())

    assert result.status == "BLOCK"
    assert result.reasons == [
        "subscription worker event stream was not valid JSONL objects"
    ]


class _TimeoutProcess:
    pid = 4242
    returncode = -1

    def __init__(self, wait_outcomes: list[str]) -> None:
        self.wait_outcomes = wait_outcomes
        self.popen_options: dict[str, object] = {}
        self.communicate_input: str | None = None
        self.communicate_timeout: int | None = None

    def communicate(
        self,
        *,
        input: str,
        timeout: int,
    ) -> tuple[str, str]:
        self.communicate_input = input
        self.communicate_timeout = timeout
        raise subprocess.TimeoutExpired(cmd="codex", timeout=timeout)

    def wait(self, *, timeout: int) -> int:
        outcome = self.wait_outcomes.pop(0)
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(cmd="codex", timeout=timeout)
        return 0

    def terminate(self) -> None:
        raise AssertionError("POSIX cancellation must address the process group")

    def kill(self) -> None:
        raise AssertionError("POSIX cancellation must address the process group")


@pytest.mark.parametrize(
    "wait_outcomes,expected_signals",
    [
        (["complete"], [signal.SIGTERM]),
        (["timeout", "complete"], [signal.SIGTERM, signal.SIGKILL]),
    ],
)
def test_codex_process_timeout_cancels_posix_process_group(
    wait_outcomes: list[str],
    expected_signals: list[int],
) -> None:
    process = _TimeoutProcess(list(wait_outcomes))
    group_signals: list[tuple[int, int]] = []

    def fake_popen(argv: list[str], **kwargs: object) -> _TimeoutProcess:
        process.popen_options = kwargs
        return process

    with pytest.raises(subprocess.TimeoutExpired):
        _run_codex_process(
            ["codex", "exec", "-"],
            cwd="/isolated/workspace",
            env={"PATH": "/bin"},
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=17,
            input="structured prompt",
            termination_grace_seconds=3,
            popen_factory=fake_popen,
            platform_name="posix",
            group_killer=lambda group, sig: group_signals.append((group, sig)),
        )

    assert process.popen_options["start_new_session"] is True
    assert process.popen_options["shell"] is False
    assert process.communicate_input == "structured prompt"
    assert process.communicate_timeout == 17
    assert group_signals == [(process.pid, item) for item in expected_signals]
