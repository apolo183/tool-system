from __future__ import annotations

import subprocess

from tool_system.agent_worker.interface import WorkerRequest
from tool_system.worker_adapter.contract import (
    AdapterRequest,
    CodexCLIAdapterConfig,
    CodexCLISubscriptionWorkerAdapter,
    DryRunWorkerAdapter,
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


def test_codex_subscription_adapter_uses_exact_argv_and_minimal_environment() -> None:
    observed: dict[str, object] = {}

    def fake_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["argv"] = argv
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout='{"type":"result"}\n', stderr="")

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(
            executable="codex",
            enabled=True,
            timeout_seconds=17,
            inherited_environment_names=("PATH", "LANG"),
        ),
        process_runner=fake_runner,
        source_environment={"PATH": "/bin", "LANG": "C", "OPENAI_API_KEY": "not-forwarded"},
    )

    result = adapter.run(_subscription_request())

    assert result.status == "PASS"
    assert observed["argv"] == [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        '{"task_id":"fixture-task"}',
    ]
    assert observed["cwd"] == "/isolated/workspace"
    assert observed["env"] == {"PATH": "/bin", "LANG": "C"}
    assert observed["shell"] is False
    assert observed["timeout"] == 17
    assert result.output["raw_output_recorded"] is False
    assert result.output["structured_result"] == {"type": "result"}
    assert result.output["environment_names"] == ["LANG", "PATH"]


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


def test_codex_subscription_adapter_fails_closed_on_timeout_and_output_limit() -> None:
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


def test_codex_subscription_adapter_rejects_non_json_success_output() -> None:
    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True),
        process_runner=lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout="not-json\n", stderr=""
        ),
    )

    result = adapter.run(_subscription_request())

    assert result.status == "BLOCK"
    assert result.reasons == [
        "subscription worker did not return valid JSON object records"
    ]
    assert result.output == {"returncode": 0, "raw_output_recorded": False}
