from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.development_loop import FrozenDevelopmentContract
import tool_system.gate.command_runner as command_runner
from tool_system.runner.task_runner import (
    run_subscription_development_pipeline,
    run_task_pipeline,
)
from tool_system.worker_adapter.contract import (
    AdapterRequest,
    CodexCLIAdapterConfig,
    CodexCLISubscriptionWorkerAdapter,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "examples" / "task_manifests" / "tool_system_audit_bundle.yaml"
PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_audit_bundle.yaml"
P6_PLAN_PATH = ROOT / "examples" / "change_plans" / "tool_system_run_entry.yaml"


def test_task_runner_validates_manifest_and_plan_without_commands(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        audit_path=tmp_path / "task_runner.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "PASS"
    assert result["manifest_result"]["status"] == "PASS"
    assert result["change_plan_result"]["status"] == "PASS"
    assert result["gate_decision"]["status"] == "PASS"
    assert result["command_results"] == []
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False
    assert Path(result["audit_path"]).exists()


def test_task_runner_blocks_without_change_plan_when_index_is_off(tmp_path: Path) -> None:
    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        active_gates_path=None,
        audit_path=tmp_path / "blocked.jsonl",
        execute_commands=False,
    )

    assert result["status"] == "BLOCK"
    assert "change plan is required" in result["reasons"]
    assert result["writes_target_repo"] is False
    assert result["executes_target_repo_mutation"] is False


def test_task_runner_change_plan_validates() -> None:
    result = validate_change_plan(P6_PLAN_PATH)

    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_task_runner_delegates_execution_to_protected_revalidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="fixture-pass\n", stderr="")

    monkeypatch.setattr(command_runner.subprocess, "run", fake_run)

    result = run_task_pipeline(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        execute_commands=True,
    )

    protected = result["protected_execution_result"]
    assert result["status"] == "PASS"
    assert protected["status"] == "PASS"
    assert protected["preflight"]["validation_to_dispatch_inputs_equal"] is True
    assert protected["input_sha256_before"] == protected["input_sha256_after"]
    assert protected["subprocess_call_count"] == len(calls)



def test_subscription_pipeline_composes_adapter_and_development_loop() -> None:
    calls: list[list[str]] = []

    def fake_run(
        argv: list[str], **_: Any
    ) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        prompt = json.loads(argv[-1])
        assert prompt["attempt_number"] == 1
        structured = {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/app.py",
                    "expected_sha256": hashlib.sha256(
                        b"return 1\n"
                    ).hexdigest(),
                    "content": "return 2\n",
                }
            ],
            "usage": {"duration_ms": 1, "cost_microunits": 0},
        }
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(structured, sort_keys=True) + "\n",
            stderr="",
        )

    adapter = CodexCLISubscriptionWorkerAdapter(
        CodexCLIAdapterConfig(executable="codex", enabled=True),
        process_runner=fake_run,
        source_environment={"PATH": "/usr/bin", "HOME": "/isolated/home"},
    )
    contract = FrozenDevelopmentContract(
        task_digest="a" * 64,
        baseline_tree="b" * 40,
        allowed_scope=("src/app.py",),
        acceptance_set=("implementation-correct",),
        validation_set=("pytest",),
    )

    result = run_subscription_development_pipeline(
        contract=contract,
        baseline_files={"src/app.py": "return 1\n"},
        adapter=adapter,
        adapter_request=AdapterRequest(
            adapter_id="pipeline-adapter",
            role="patch_author",
            action="implement",
            context={
                "workspace": "/isolated/workspace",
                "subscription_worker_authorized": True,
            },
        ),
        validator=lambda files: {
            "validation_results": {
                "pytest": {
                    "status": (
                        "PASS"
                        if files.get("src/app.py") == "return 2\n"
                        else "BLOCK"
                    )
                }
            },
            "satisfied_acceptance_items": ["implementation-correct"],
        },
        code_reviewer=lambda _: {"violated_acceptance_items": []},
        contract_reviewer=lambda _: {"violated_acceptance_items": []},
    )

    assert result["status"] == "PASS"
    assert result["terminal_candidate_sealed"] is True
    assert result["candidate_files"] == {"src/app.py": "return 2\n"}
    assert result["adapter_kind"] == "codex_cli_subscription_worker_adapter"
    assert len(calls) == 1
    assert result["api_mode_enabled"] is False
    assert result["provider_invocations"] == 0
    assert result["provider_credential_value_accesses"] == 0
    assert result["target_repo_mutations"] == 0
    assert result["remote_repository_operations"] == 0
    assert result["local_git_operations"] == 0
    assert result["subscription_worker_invocations"] == 1


def test_subscription_pipeline_rejects_unknown_adapter_before_invocation() -> None:
    class UnknownAdapter:
        adapter_kind = "optional_api_provider_adapter"

        def run(self, _: AdapterRequest) -> object:
            raise AssertionError("unknown adapter must not be invoked")

    result = run_subscription_development_pipeline(
        contract=FrozenDevelopmentContract(
            task_digest="a" * 64,
            baseline_tree="b" * 40,
            allowed_scope=("src/app.py",),
            acceptance_set=("implementation-correct",),
            validation_set=("pytest",),
        ),
        baseline_files={"src/app.py": "return 1\n"},
        adapter=UnknownAdapter(),  # type: ignore[arg-type]
        adapter_request=AdapterRequest(
            adapter_id="unknown",
            role="patch_author",
            action="implement",
        ),
        validator=lambda _: {},
        code_reviewer=lambda _: {},
        contract_reviewer=lambda _: {},
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "UNSUPPORTED_SUBSCRIPTION_WORKER_ADAPTER"
    assert result["provider_invocations"] == 0
    assert result["remote_repository_operations"] == 0
    assert result["local_git_operations"] == 0
