from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.development_loop import FrozenDevelopmentContract
import tool_system.gate.command_runner as command_runner
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runner.task_runner import (
    run_subscription_development_pipeline,
    run_subscription_public_entry_context_compilation,
    run_subscription_public_entry_preflight,
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
CONTEXT_COMPILER_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_subscription_worker_public_entry_context_compiler_v1.yaml"
)
CONTEXT_COMPILER_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_subscription_worker_public_entry_context_compiler_v1.yaml"
)
CONTEXT_COMPILER_FILES = {
    "config/module_registry_v1.yaml",
    "docs/modules/blueprint-compiler-contract-v1.md",
    "docs/modules/cli-frontend-contract-v1.md",
    "docs/modules/repository-context-contract-v1.md",
    "docs/modules/task-runner-contract-v1.md",
    "docs/reports/subscription_worker_public_entry_context_compiler_v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "examples/change_plans/tool_system_subscription_worker_public_entry_context_compiler_v1.yaml",
    "examples/task_manifests/tool_system_subscription_worker_public_entry_context_compiler_v1.yaml",
    "src/tool_system/cli/main.py",
    "src/tool_system/runner/task_runner.py",
    "tests/test_module_registry.py",
    "tests/test_root_cli.py",
    "tests/test_task_runner.py",
}


def _fixture_git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _subscription_context_fixture(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "subscription-context-fixture"
    repository.mkdir()
    _fixture_git(repository, "init", "-q", "-b", "main")
    _fixture_git(repository, "config", "user.email", "fixture@example.invalid")
    _fixture_git(repository, "config", "user.name", "Fixture")
    files = {
        "blueprint.yaml": """product_objective:
  id: bounded-fixture
  statement: build a bounded fixture
agents:
  evidence_collector: {role: evidence_collector}
  policy_guard: {role: policy_guard}
  blueprint_architect: {role: blueprint_architect}
  change_planner: {role: change_planner}
  patch_author: {role: patch_author}
  test_engineer: {role: test_engineer}
  code_reviewer: {role: code_reviewer}
  contract_reviewer: {role: contract_reviewer}
  audit_recorder: {role: audit_recorder}
milestones:
  M1_BILLING:
    objective: add bounded billing
    module_change:
      module_id: billing
      module_version: 1.0.0
      interface_id: billing-api
      interface_version: 1.0.0
      change_kind: add
      natural_owner_paths: [src/billing]
      allowed_files: [src/billing/service.py, tests/test_billing.py]
      test_paths: [tests/test_billing.py]
      depends_on_module_ids: []
      acceptance: [billing behavior passes]
      validations: [pytest tests/test_billing.py]
""",
        "module-registry.yaml": """modules:
  - module_id: existing
    module_version: 1.0.0
""",
        "GOVERNANCE.md": "Owner evidence remains non-authorizing.\n",
        "src/billing/service.py": "def total(value: int) -> int:\n    return value * 100\n",
        "tests/test_billing.py": "from src.billing.service import total\n",
    }
    for relative, value in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    _fixture_git(repository, "add", "--all")
    _fixture_git(repository, "commit", "-q", "-m", "fixture")
    return repository, _fixture_git(repository, "rev-parse", "HEAD")


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


def test_subscription_public_entry_preflight_freezes_nonexecuting_packet() -> None:
    result = run_subscription_public_entry_preflight(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        repository_root=ROOT,
        expected_head="a" * 40,
        blueprint_path="blueprint/tool_system_v0.yaml",
        module_registry_path="config/module_registry_v1.yaml",
        milestone_ids=["P16"],
        acceptance_requirements=["subscription-core-remains-bounded"],
        governance_paths=["AGENTS.md"],
        query_terms=["task-runner"],
        seed_paths=["src/tool_system/runner/task_runner.py"],
        process_authority_path=ROOT / "config/process_authority_v1.yaml",
        policy_path=ROOT / "policy/repo_write_policy.yaml",
        autonomy_policy_path=ROOT / "policy/autonomy_policy.yaml",
    )

    assert result["status"] == "PASS"
    assert result["worker_execution_authorized"] is False
    assert result["repository_context_built"] is False
    assert result["blueprint_compiled"] is False
    assert result["provider_invocations"] == 0
    packet = result["dispatch_packet"]
    assert packet["packet_version"] == (
        "subscription_development_authority_packet_v1"
    )
    assert packet["expected_head"] == "a" * 40
    assert len(packet["repository_root_identity_sha256"]) == 64
    assert "repository_root" not in packet
    assert len(packet["packet_sha256"]) == 64


def test_subscription_public_entry_preflight_rejects_input_before_file_reads() -> None:
    result = run_subscription_public_entry_preflight(
        task_manifest_path="not-read.yaml",
        change_plan_path="not-read-plan.yaml",
        repository_root="relative/path",
        expected_head="not-a-commit",
        blueprint_path="../blueprint.yaml",
        module_registry_path="config/module_registry_v1.yaml",
        milestone_ids=[],
        acceptance_requirements=[],
        governance_paths=[],
        query_terms=[],
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "INVALID_SUBSCRIPTION_PREFLIGHT_INPUT"
    assert result["worker_execution_authorized"] is False
    assert result["provider_invocations"] == 0



def test_subscription_public_entry_context_compiles_isolated_fixture(
    tmp_path: Path,
) -> None:
    repository, head = _subscription_context_fixture(tmp_path)

    result = run_subscription_public_entry_context_compilation(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        repository_root=repository,
        expected_head=head,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_BILLING"],
        acceptance_requirements=["all milestone acceptance passes"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing"],
        seed_paths=["src/billing/service.py"],
        isolated_fixture_repository=True,
        process_authority_path=ROOT / "config/process_authority_v1.yaml",
        policy_path=ROOT / "policy/repo_write_policy.yaml",
        autonomy_policy_path=ROOT / "policy/autonomy_policy.yaml",
    )

    assert result["status"] == "PASS"
    assert result["terminal_code"] == "SUBSCRIPTION_CONTEXT_COMPILATION_PASS"
    assert result["repository_context_built"] is True
    assert result["blueprint_compiled"] is True
    assert result["repository_read_mode"] == "isolated_fixture_only"
    assert result["local_git_read_only_context_authorized"] is True
    assert result["worker_execution_authorized"] is False
    assert result["worker_invocations"] == 0
    assert result["provider_invocations"] == 0
    assert result["provider_credential_value_accesses"] == 0
    assert result["repository_writes"] == 0
    assert result["local_git_write_operations"] == 0
    assert result["remote_repository_operations"] == 0
    compilation = result["blueprint_compilation"]
    assert compilation["status"] == "PASS"
    assert compilation["task_graph_validation"]["task_count"] == 10
    packet = result["compilation_packet"]
    assert packet["isolated_fixture_repository"] is True
    assert packet["worker_execution_authorized"] is False
    assert len(packet["packet_sha256"]) == 64
    rendered = json.dumps(result, sort_keys=True)
    assert str(repository) not in rendered
    assert "def total(value: int)" not in rendered
    assert _fixture_git(
        repository,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ) == ""


def test_subscription_public_entry_context_requires_explicit_fixture_before_reads(
    tmp_path: Path,
) -> None:
    result = run_subscription_public_entry_context_compilation(
        task_manifest_path="not-read.yaml",
        change_plan_path="not-read-plan.yaml",
        repository_root=tmp_path / "not-read",
        expected_head="a" * 40,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1"],
        acceptance_requirements=["bounded"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing"],
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == (
        "SUBSCRIPTION_CONTEXT_REPOSITORY_CLASS_NOT_AUTHORIZED"
    )
    assert result["local_git_read_only_context_authorized"] is False
    assert result["worker_invocations"] == 0
    assert not (tmp_path / "not-read").exists()


def test_subscription_public_entry_context_blocks_stale_fixture(
    tmp_path: Path,
) -> None:
    repository, _ = _subscription_context_fixture(tmp_path)

    result = run_subscription_public_entry_context_compilation(
        task_manifest_path=MANIFEST_PATH,
        change_plan_path=PLAN_PATH,
        repository_root=repository,
        expected_head="0" * 40,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_BILLING"],
        acceptance_requirements=["all milestone acceptance passes"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing"],
        seed_paths=["src/billing/service.py"],
        isolated_fixture_repository=True,
        process_authority_path=ROOT / "config/process_authority_v1.yaml",
        policy_path=ROOT / "policy/repo_write_policy.yaml",
        autonomy_policy_path=ROOT / "policy/autonomy_policy.yaml",
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "SUBSCRIPTION_CONTEXT_COMPILATION_BLOCKED"
    assert result["reasons"] == ["STALE_EXPECTED_HEAD"]
    assert result["blueprint_compiled"] is False
    assert result["worker_invocations"] == 0
    assert result["local_git_write_operations"] == 0



def test_subscription_context_compiler_package_freezes_exact_scope() -> None:
    manifest_result = validate_task_manifest(
        CONTEXT_COMPILER_MANIFEST,
        ROOT / "policy/repo_write_policy.yaml",
        ROOT / "policy/autonomy_policy.yaml",
    )
    plan_result = validate_change_plan(CONTEXT_COMPILER_PLAN)
    manifest = load_yaml_file(CONTEXT_COMPILER_MANIFEST)
    plan = load_yaml_file(CONTEXT_COMPILER_PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == CONTEXT_COMPILER_FILES
    assert set(manifest["scope"]["in_scope"]) == CONTEXT_COMPILER_FILES
    assert set(plan["changed_files"]) == CONTEXT_COMPILER_FILES
    assert len(CONTEXT_COMPILER_FILES) == 14
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["bounded_closure"]["frozen_before_execution"][
        "real_downstream_accesses"
    ] == 0
