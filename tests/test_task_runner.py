from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.development_loop import FrozenDevelopmentContract
import tool_system.gate.command_runner as command_runner
import tool_system.runner.task_runner as task_runner_module
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runner.task_runner import (
    run_subscription_development_pipeline,
    run_subscription_public_entry_context_compilation,
    run_subscription_public_entry_execution,
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
SNAPSHOT_BINDING_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_subscription_worker_snapshot_authority_binding_v1.yaml"
)
SNAPSHOT_BINDING_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_subscription_worker_snapshot_authority_binding_v1.yaml"
)
SNAPSHOT_BINDING_FILES = {
    "config/module_registry_v1.yaml",
    "docs/modules/blueprint-compiler-contract-v1.md",
    "docs/modules/cli-frontend-contract-v1.md",
    "docs/modules/task-runner-contract-v1.md",
    "docs/reports/subscription_worker_snapshot_authority_binding_v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "examples/change_plans/tool_system_subscription_worker_snapshot_authority_binding_v1.yaml",
    "examples/task_manifests/tool_system_subscription_worker_snapshot_authority_binding_v1.yaml",
    "src/tool_system/blueprint_compiler/compiler.py",
    "src/tool_system/cli/main.py",
    "src/tool_system/runner/task_runner.py",
    "tests/test_blueprint_compiler.py",
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


def _bound_subscription_task_pair(
    tmp_path: Path,
    *,
    repository_root: Path,
    expected_head: str,
    blueprint_path: str,
    module_registry_path: str,
    milestone_ids: list[str],
    acceptance_requirements: list[str],
    governance_paths: list[str],
    query_terms: list[str],
    seed_paths: list[str],
) -> tuple[Path, Path]:
    manifest = load_yaml_file(MANIFEST_PATH)
    manifest["subscription_public_entry"] = {
        "binding_version": "subscription_public_entry_authority_binding_v1",
        "enabled": True,
        "repository_root_identity_sha256": hashlib.sha256(
            str(repository_root).encode("utf-8")
        ).hexdigest(),
        "expected_head": expected_head,
        "blueprint_path": blueprint_path,
        "module_registry_path": module_registry_path,
        "milestone_ids": milestone_ids,
        "acceptance_requirements": acceptance_requirements,
        "governance_paths": governance_paths,
        "query_terms": query_terms,
        "seed_paths": seed_paths,
        "repository_read_authorized": True,
        "worker_execution_authorized": False,
        "local_git_write_authorized": False,
    }
    manifest_path = tmp_path / "bound-task-manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    plan = load_yaml_file(PLAN_PATH)
    plan["task_manifest"] = manifest_path.as_posix()
    plan_path = tmp_path / "bound-change-plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest_path, plan_path


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
    calls: list[dict[str, object]] = []

    def fake_run(
        argv: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        prompt = json.loads(str(kwargs["input"]))
        calls.append(prompt)
        attempt = len(calls)
        expected_content = "return 1\n" if attempt == 1 else "return 0\n"
        replacement_content = "return 0\n" if attempt == 1 else "return 2\n"
        assert prompt["attempt_number"] == attempt
        assert prompt["candidate_files"] == {
            "src/app.py": expected_content
        }
        assert argv[-1] == "-"
        assert "--ignore-user-config" in argv
        assert argv[argv.index("--sandbox") + 1] == "read-only"
        structured = {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/app.py",
                    "expected_sha256": hashlib.sha256(
                        expected_content.encode("utf-8")
                    ).hexdigest(),
                    "content": replacement_content,
                }
            ],
            "usage": {"duration_ms": 1, "cost_microunits": 0},
        }
        final_message = Path(
            argv[argv.index("--output-last-message") + 1]
        )
        final_message.write_text(
            json.dumps(structured, sort_keys=True),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout='{"type":"turn.completed"}\n',
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

    def validator(files: dict[str, str]) -> dict[str, object]:
        passed = files.get("src/app.py") == "return 2\n"
        return {
            "validation_results": {
                "pytest": {
                    "status": "PASS" if passed else "BLOCK",
                }
            },
            "satisfied_acceptance_items": (
                ["implementation-correct"] if passed else []
            ),
        }

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
        validator=validator,
        code_reviewer=lambda _: {"violated_acceptance_items": []},
        contract_reviewer=lambda _: {"violated_acceptance_items": []},
    )

    assert result["status"] == "PASS"
    assert result["terminal_candidate_sealed"] is True
    assert result["candidate_files"] == {"src/app.py": "return 2\n"}
    assert result["adapter_kind"] == "codex_cli_subscription_worker_adapter"
    assert len(calls) == 2
    assert result["api_mode_enabled"] is False
    assert result["provider_invocations"] == 0
    assert result["provider_credential_value_accesses"] == 0
    assert result["target_repo_mutations"] == 0
    assert result["remote_repository_operations"] == 0
    assert result["local_git_operations"] == 0
    assert result["subscription_worker_invocations"] == 2


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


def test_subscription_public_entry_preflight_freezes_manifest_bound_packet(
    tmp_path: Path,
) -> None:
    expected_head = "a" * 40
    selections = {
        "blueprint_path": "blueprint/tool_system_v0.yaml",
        "module_registry_path": "config/module_registry_v1.yaml",
        "milestone_ids": ["P16"],
        "acceptance_requirements": ["subscription-core-remains-bounded"],
        "governance_paths": ["AGENTS.md"],
        "query_terms": ["task-runner"],
        "seed_paths": ["src/tool_system/runner/task_runner.py"],
    }
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=ROOT,
        expected_head=expected_head,
        **selections,
    )

    result = run_subscription_public_entry_preflight(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=ROOT,
        expected_head=expected_head,
        **selections,
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
    assert packet["expected_head"] == expected_head
    assert packet["repository_read_authorized"] is True
    assert len(packet["repository_read_binding_sha256"]) == 64
    assert len(packet["task_manifest_sha256"]) == 64
    assert len(packet["change_plan_sha256"]) == 64
    assert len(packet["repository_root_identity_sha256"]) == 64
    assert "repository_root" not in packet
    assert len(packet["packet_sha256"]) == 64


def test_subscription_public_entry_preflight_rejects_unbound_generic_pair() -> None:
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

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "SUBSCRIPTION_AUTHORITY_BINDING_BLOCKED"
    assert result["reasons"] == ["SUBSCRIPTION_AUTHORITY_BINDING_MISMATCH"]
    assert result["repository_context_built"] is False
    assert result["worker_execution_authorized"] is False


def test_subscription_public_entry_preflight_rejects_duplicate_binding(
    tmp_path: Path,
) -> None:
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=ROOT,
        expected_head="a" * 40,
        blueprint_path="blueprint/tool_system_v0.yaml",
        module_registry_path="config/module_registry_v1.yaml",
        milestone_ids=["P16"],
        acceptance_requirements=["subscription-core-remains-bounded"],
        governance_paths=["AGENTS.md"],
        query_terms=["task-runner"],
        seed_paths=["src/tool_system/runner/task_runner.py"],
    )
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8")
        + "\nsubscription_public_entry: {}\n",
        encoding="utf-8",
    )

    result = run_subscription_public_entry_preflight(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=ROOT,
        expected_head="a" * 40,
        blueprint_path="blueprint/tool_system_v0.yaml",
        module_registry_path="config/module_registry_v1.yaml",
        milestone_ids=["P16"],
        acceptance_requirements=["subscription-core-remains-bounded"],
        governance_paths=["AGENTS.md"],
        query_terms=["task-runner"],
        seed_paths=["src/tool_system/runner/task_runner.py"],
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "SUBSCRIPTION_AUTHORITY_INPUT_CAPTURE_BLOCKED"
    assert result["reasons"] == ["SUBSCRIPTION_AUTHORITY_MANIFEST_AMBIGUOUS"]
    assert result["repository_context_built"] is False


def test_subscription_public_entry_preflight_detects_pair_byte_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selections = {
        "blueprint_path": "blueprint/tool_system_v0.yaml",
        "module_registry_path": "config/module_registry_v1.yaml",
        "milestone_ids": ["P16"],
        "acceptance_requirements": ["subscription-core-remains-bounded"],
        "governance_paths": ["AGENTS.md"],
        "query_terms": ["task-runner"],
        "seed_paths": ["src/tool_system/runner/task_runner.py"],
    }
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=ROOT,
        expected_head="a" * 40,
        **selections,
    )
    real_pipeline = task_runner_module.run_task_pipeline

    def mutate_after_validation(**arguments: object) -> dict[str, object]:
        result = real_pipeline(**arguments)
        plan_path.write_text(
            plan_path.read_text(encoding="utf-8") + "\n# drift\n",
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(
        task_runner_module,
        "run_task_pipeline",
        mutate_after_validation,
    )
    result = run_subscription_public_entry_preflight(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=ROOT,
        expected_head="a" * 40,
        **selections,
        process_authority_path=ROOT / "config/process_authority_v1.yaml",
        policy_path=ROOT / "policy/repo_write_policy.yaml",
        autonomy_policy_path=ROOT / "policy/autonomy_policy.yaml",
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "SUBSCRIPTION_AUTHORITY_BINDING_BLOCKED"
    assert result["reasons"] == ["SUBSCRIPTION_AUTHORITY_INPUT_DRIFT"]
    assert result["repository_context_built"] is False


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



def test_subscription_public_entry_context_compiles_manifest_bound_snapshot(
    tmp_path: Path,
) -> None:
    repository, head = _subscription_context_fixture(tmp_path)
    selections = {
        "blueprint_path": "blueprint.yaml",
        "module_registry_path": "module-registry.yaml",
        "milestone_ids": ["M1_BILLING"],
        "acceptance_requirements": ["all milestone acceptance passes"],
        "governance_paths": ["GOVERNANCE.md"],
        "query_terms": ["billing"],
        "seed_paths": ["src/billing/service.py"],
    }
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=repository,
        expected_head=head,
        **selections,
    )

    result = run_subscription_public_entry_context_compilation(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=repository,
        expected_head=head,
        **selections,
        repository_read_authorized=True,
        process_authority_path=ROOT / "config/process_authority_v1.yaml",
        policy_path=ROOT / "policy/repo_write_policy.yaml",
        autonomy_policy_path=ROOT / "policy/autonomy_policy.yaml",
    )

    assert result["status"] == "PASS"
    assert result["terminal_code"] == "SUBSCRIPTION_CONTEXT_COMPILATION_PASS"
    assert result["repository_context_built"] is True
    assert result["repository_context_builds"] == 1
    assert result["blueprint_compiled"] is True
    assert result["repository_read_mode"] == "exact_manifest_bound_snapshot"
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
    assert compilation["repository_context_authorization_mode"] == (
        "manifest_bound_repository_context_read"
    )
    assert compilation["task_graph_validation"]["task_count"] == 10
    packet = result["compilation_packet"]
    assert packet["repository_read_authorized"] is True
    assert packet["legacy_isolated_fixture_alias_used"] is False
    assert packet["worker_execution_authorized"] is False
    assert len(packet["repository_read_binding_sha256"]) == 64
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


def test_subscription_public_entry_context_requires_read_request_before_files(
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
    assert result["terminal_code"] == "SUBSCRIPTION_CONTEXT_READ_NOT_REQUESTED"
    assert result["local_git_read_only_context_authorized"] is False
    assert result["worker_invocations"] == 0
    assert not (tmp_path / "not-read").exists()


def test_subscription_public_entry_context_blocks_stale_bound_snapshot(
    tmp_path: Path,
) -> None:
    repository, _ = _subscription_context_fixture(tmp_path)
    expected_head = "0" * 40
    selections = {
        "blueprint_path": "blueprint.yaml",
        "module_registry_path": "module-registry.yaml",
        "milestone_ids": ["M1_BILLING"],
        "acceptance_requirements": ["all milestone acceptance passes"],
        "governance_paths": ["GOVERNANCE.md"],
        "query_terms": ["billing"],
        "seed_paths": ["src/billing/service.py"],
    }
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=repository,
        expected_head=expected_head,
        **selections,
    )

    result = run_subscription_public_entry_context_compilation(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=repository,
        expected_head=expected_head,
        **selections,
        repository_read_authorized=True,
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
        "finite_budgets"
    ]["real_downstream_accesses"] == 0



def test_snapshot_authority_binding_package_freezes_exact_scope() -> None:
    manifest_result = validate_task_manifest(
        SNAPSHOT_BINDING_MANIFEST,
        ROOT / "policy/repo_write_policy.yaml",
        ROOT / "policy/autonomy_policy.yaml",
    )
    plan_result = validate_change_plan(SNAPSHOT_BINDING_PLAN)
    manifest = load_yaml_file(SNAPSHOT_BINDING_MANIFEST)
    plan = load_yaml_file(SNAPSHOT_BINDING_PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == SNAPSHOT_BINDING_FILES
    assert set(manifest["scope"]["in_scope"]) == SNAPSHOT_BINDING_FILES
    assert set(plan["changed_files"]) == SNAPSHOT_BINDING_FILES
    assert len(SNAPSHOT_BINDING_FILES) == 15
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["bounded_closure"]["frozen_before_execution"][
        "finite_budgets"
    ]["real_downstream_accesses"] == 0

def _bound_subscription_execution_pair(
    tmp_path: Path,
    *,
    repository_root: Path,
    workspace_root: Path,
    durable_state_path: Path,
    expected_head: str,
    expected_tree: str,
    config: CodexCLIAdapterConfig,
) -> tuple[Path, Path, str]:
    acceptance = ["billing behavior passes"]
    validation_command = (
        'python -c "from src.billing.service import total; '
        'assert total(2) == 2"'
    )
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=repository_root,
        expected_head=expected_head,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_BILLING"],
        acceptance_requirements=acceptance,
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing", "total"],
        seed_paths=[
            "src/billing/service.py",
            "tests/test_billing.py",
        ],
    )
    plan = load_yaml_file(plan_path)
    plan["verification"]["commands"] = [validation_command]
    plan_path.write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    manifest = load_yaml_file(manifest_path)
    manifest["verification"]["commands"] = [validation_command]
    manifest["subscription_public_entry_execution"] = {
        "binding_version": "subscription_public_entry_execution_binding_v1",
        "enabled": True,
        "repository_root_identity_sha256": hashlib.sha256(
            str(repository_root).encode("utf-8")
        ).hexdigest(),
        "workspace_root_identity_sha256": hashlib.sha256(
            str(workspace_root).encode("utf-8")
        ).hexdigest(),
        "durable_state_identity_sha256": hashlib.sha256(
            str(durable_state_path).encode("utf-8")
        ).hexdigest(),
        "expected_head": expected_head,
        "expected_tree": expected_tree,
        "existing_scope_paths": [
            "src/billing/service.py",
            "tests/test_billing.py",
        ],
        "addable_scope_paths": [],
        "allowed_scope": [
            "src/billing/service.py",
            "tests/test_billing.py",
        ],
        "acceptance_set": acceptance,
        "validation_set": [validation_command],
        "worker_configuration_sha256": (
            task_runner_module._worker_configuration_sha256(config)
        ),
        "branch_name": "agent/bounded-billing-v1",
        "commit_message": "Implement bounded billing",
        "finite_budgets": {
            "max_cycles": 2,
            "max_worker_calls": 2,
            "max_patch_operations_per_cycle": 8,
            "max_total_duration_ms": 30_000,
            "max_total_cost_microunits": 1,
        },
        "validation_timeout_seconds": 30,
        "max_validation_output_bytes": 65_536,
        "repository_read_authorized": True,
        "worker_execution_authorized": True,
        "validation_execution_authorized": True,
        "subscription_data_transfer_authorized": True,
        "local_git_write_authorized": True,
        "api_mode_enabled": False,
        "provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "remote_repository_operations_authorized": False,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "rollback_execution_authorized": False,
        "max_local_commits": 1,
    }
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest_path, plan_path, validation_command


def test_subscription_public_entry_executes_one_fake_worker_local_commit(
    tmp_path: Path,
) -> None:
    repository, expected_head = _subscription_context_fixture(tmp_path)
    expected_tree = _fixture_git(repository, "rev-parse", "HEAD^{tree}")
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir(mode=0o700)
    workspace = workspace_parent / "billing"
    state_parent = tmp_path / "state"
    state_parent.mkdir(mode=0o700)
    state = state_parent / "subscription.sqlite3"
    config = CodexCLIAdapterConfig(executable="codex", enabled=True)
    manifest_path, plan_path, validation_command = (
        _bound_subscription_execution_pair(
            tmp_path,
            repository_root=repository,
            workspace_root=workspace,
            durable_state_path=state,
            expected_head=expected_head,
            expected_tree=expected_tree,
            config=config,
        )
    )
    calls: list[dict[str, object]] = []

    def fake_run(
        argv: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        prompt = json.loads(str(kwargs["input"]))
        calls.append(prompt)
        expected_content = (
            "def total(value: int) -> int:\n"
            "    return value * 100\n"
        )
        replacement_content = (
            "def total(value: int) -> int:\n"
            "    return value\n"
        )
        assert prompt["candidate_files"]["src/billing/service.py"] == (
            expected_content
        )
        structured = {
            "operations": [
                {
                    "op": "replace",
                    "path": "src/billing/service.py",
                    "expected_sha256": hashlib.sha256(
                        expected_content.encode("utf-8")
                    ).hexdigest(),
                    "content": replacement_content,
                }
            ],
            "usage": {"duration_ms": 1, "cost_microunits": 0},
        }
        Path(
            argv[argv.index("--output-last-message") + 1]
        ).write_text(json.dumps(structured), encoding="utf-8")
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout='{"type":"turn.completed"}\n',
            stderr="",
        )

    adapter = CodexCLISubscriptionWorkerAdapter(
        config,
        process_runner=fake_run,
        source_environment={"PATH": "/usr/bin", "HOME": "/isolated/home"},
    )
    result = run_subscription_public_entry_execution(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=repository,
        workspace_root=workspace,
        durable_state_path=state,
        expected_head=expected_head,
        expected_tree=expected_tree,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_BILLING"],
        acceptance_requirements=["billing behavior passes"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing", "total"],
        seed_paths=[
            "src/billing/service.py",
            "tests/test_billing.py",
        ],
        codex_config=config,
        repository_read_authorized=True,
        worker_execution_authorized=True,
        validation_execution_authorized=True,
        subscription_data_transfer_authorized=True,
        local_git_write_authorized=True,
        adapter=adapter,
    )

    assert result["status"] == "PASS", result
    assert result["terminal_code"] == "LOCAL_COMMIT_RECORDED"
    assert result["worker_invocations"] == 1
    assert result["validation_command_invocations"] == 1
    assert result["provider_invocations"] == 0
    assert result["remote_repository_operations"] == 0
    assert result["target_repo_mutations"] == 0
    assert result["draft_pr_plan"]["authorized"] is False
    assert len(calls) == 1
    assert _fixture_git(workspace, "remote") == ""
    assert _fixture_git(
        workspace,
        "rev-list",
        "--count",
        f"{expected_head}..HEAD",
    ) == "1"
    assert (
        _fixture_git(workspace, "show", "HEAD:src/billing/service.py")
        == "def total(value: int) -> int:\n    return value"
    )
    assert validation_command not in json.dumps(result, sort_keys=True)


def test_subscription_public_entry_missing_flag_blocks_before_workspace(
    tmp_path: Path,
) -> None:
    repository, expected_head = _subscription_context_fixture(tmp_path)
    expected_tree = _fixture_git(repository, "rev-parse", "HEAD^{tree}")
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir(mode=0o700)
    workspace = workspace_parent / "blocked"
    state_parent = tmp_path / "state"
    state_parent.mkdir(mode=0o700)
    state = state_parent / "blocked.sqlite3"
    config = CodexCLIAdapterConfig(executable="codex", enabled=True)
    manifest_path, plan_path, _ = _bound_subscription_execution_pair(
        tmp_path,
        repository_root=repository,
        workspace_root=workspace,
        durable_state_path=state,
        expected_head=expected_head,
        expected_tree=expected_tree,
        config=config,
    )

    result = run_subscription_public_entry_execution(
        task_manifest_path=manifest_path,
        change_plan_path=plan_path,
        repository_root=repository,
        workspace_root=workspace,
        durable_state_path=state,
        expected_head=expected_head,
        expected_tree=expected_tree,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_BILLING"],
        acceptance_requirements=["billing behavior passes"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["billing", "total"],
        seed_paths=[
            "src/billing/service.py",
            "tests/test_billing.py",
        ],
        codex_config=config,
        repository_read_authorized=True,
        worker_execution_authorized=False,
        validation_execution_authorized=True,
        subscription_data_transfer_authorized=True,
        local_git_write_authorized=True,
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == (
        "SUBSCRIPTION_EXECUTION_NOT_EXPLICITLY_REQUESTED"
    )
    assert not workspace.exists()
    assert not state.exists()

def test_candidate_materialization_rejects_symlinked_parent(
    tmp_path: Path,
) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "src").symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        ValueError,
        match="SUBSCRIPTION_EXECUTION_CANDIDATE_PATH_UNSAFE",
    ):
        task_runner_module._materialize_candidate(
            root=root,
            baseline_files={},
            candidate_files={"src/service.py": "safe = True\n"},
            allowed_scope=("src/service.py",),
        )

    assert not (outside / "service.py").exists()

def test_public_execution_workspace_dependency_blocks_symlink_and_dirty_resume(
    tmp_path: Path,
) -> None:
    source, expected_head = _subscription_context_fixture(tmp_path)
    expected_tree = _fixture_git(source, "rev-parse", "HEAD^{tree}")
    workspace_parent = tmp_path / "workspace-guards"
    workspace_parent.mkdir(mode=0o700)
    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(source, target_is_directory=True)

    blocked_alias = task_runner_module.create_isolated_local_workspace(
        source_repository_root=source_alias,
        workspace_root=workspace_parent / "alias",
        expected_head_sha=expected_head,
        expected_tree_sha=expected_tree,
    )
    assert blocked_alias["status"] == "BLOCK"
    assert blocked_alias["terminal_code"] == "INVALID_SOURCE_REPOSITORY_ROOT"

    workspace = workspace_parent / "dirty"
    created = task_runner_module.create_isolated_local_workspace(
        source_repository_root=source,
        workspace_root=workspace,
        expected_head_sha=expected_head,
        expected_tree_sha=expected_tree,
    )
    assert created["status"] == "PASS"
    (workspace / "untracked.txt").write_text("drift\n", encoding="utf-8")
    blocked_resume = task_runner_module.create_isolated_local_workspace(
        source_repository_root=source,
        workspace_root=workspace,
        expected_head_sha=expected_head,
        expected_tree_sha=expected_tree,
    )
    assert blocked_resume["status"] == "BLOCK"
    assert blocked_resume["terminal_code"] == "DIRTY_EXISTING_WORKSPACE"

def _multi_stack_spec(stack: str) -> dict[str, str]:
    if stack == "python":
        return {
            "source": "src/calculator.py",
            "test": "tests/test_calculator.py",
            "baseline": "def total(value: int) -> int:\n    return value * 100\n",
            "intermediate": "def total(value: int) -> int:\n    return value * 2\n",
            "target": "def total(value: int) -> int:\n    return value\n",
            "test_content": (
                "from src.calculator import total\n\n"
                "def test_total() -> None:\n    assert total(2) == 2\n"
            ),
            "command": (
                'python -c "from src.calculator import total; '
                'assert total(2) == 2"'
            ),
        }
    return {
        "source": "src/calculator.ts",
        "test": "tests/calculator.test.ts",
        "baseline": (
            "export function total(value) {\n  return value * 100;\n}\n"
        ),
        "intermediate": (
            "export function total(value) {\n  return value * 2;\n}\n"
        ),
        "target": "export function total(value) {\n  return value;\n}\n",
        "test_content": (
            "import { total } from '../src/calculator.ts';\n"
            "if (total(2) !== 2) throw new Error('unexpected total');\n"
        ),
        "command": (
            'node -e "const fs=require(\'fs\');'
            "const s=fs.readFileSync('src/calculator.ts','utf8');"
            "if(!s.includes('return value;'))process.exit(1)"
            '"'
        ),
    }


def _multi_stack_context(tmp_path: Path, stack: str) -> dict[str, Any]:
    spec = _multi_stack_spec(stack)
    repository = tmp_path / f"{stack}-subscription-fixture"
    repository.mkdir()
    _fixture_git(repository, "init", "-q", "-b", "main")
    _fixture_git(repository, "config", "user.email", "fixture@example.invalid")
    _fixture_git(repository, "config", "user.name", "Fixture")
    files = {
        "blueprint.yaml": f"""product_objective:
  id: bounded-{stack}-fixture
  statement: build one bounded {stack} fixture
agents:
  evidence_collector: {{role: evidence_collector}}
  policy_guard: {{role: policy_guard}}
  blueprint_architect: {{role: blueprint_architect}}
  change_planner: {{role: change_planner}}
  patch_author: {{role: patch_author}}
  test_engineer: {{role: test_engineer}}
  code_reviewer: {{role: code_reviewer}}
  contract_reviewer: {{role: contract_reviewer}}
  audit_recorder: {{role: audit_recorder}}
milestones:
  M1_CALCULATOR:
    objective: repair bounded {stack} calculator
    module_change:
      module_id: calculator-{stack}
      module_version: 1.0.0
      interface_id: calculator-{stack}-api
      interface_version: 1.0.0
      change_kind: add
      natural_owner_paths: [src]
      allowed_files: [{spec["source"]}, {spec["test"]}]
      test_paths: [{spec["test"]}]
      depends_on_module_ids: []
      acceptance: [{stack} fixture passes]
      validations: [local isolated validation]
""",
        "module-registry.yaml": (
            "modules:\n  - module_id: existing\n    module_version: 1.0.0\n"
        ),
        "GOVERNANCE.md": "Owner evidence remains non-authorizing.\n",
        spec["source"]: spec["baseline"],
        spec["test"]: spec["test_content"],
    }
    for relative, content in files.items():
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _fixture_git(repository, "add", "--all")
    _fixture_git(repository, "commit", "-q", "-m", "fixture")
    head = _fixture_git(repository, "rev-parse", "HEAD")
    tree = _fixture_git(repository, "rev-parse", "HEAD^{tree}")
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir(mode=0o700)
    state_parent = tmp_path / "state"
    state_parent.mkdir(mode=0o700)
    workspace = workspace_parent / stack
    state = state_parent / f"{stack}.sqlite3"
    config = CodexCLIAdapterConfig(executable="codex", enabled=True)
    acceptance = [f"{stack} fixture passes"]
    scope = [spec["source"], spec["test"]]
    manifest_path, plan_path = _bound_subscription_task_pair(
        tmp_path,
        repository_root=repository,
        expected_head=head,
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_CALCULATOR"],
        acceptance_requirements=acceptance,
        governance_paths=["GOVERNANCE.md"],
        query_terms=["calculator", stack],
        seed_paths=scope,
    )
    plan = load_yaml_file(plan_path)
    plan["verification"]["commands"] = [spec["command"]]
    plan_path.write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    manifest = load_yaml_file(manifest_path)
    manifest["verification"]["commands"] = [spec["command"]]
    manifest["subscription_public_entry_execution"] = {
        "binding_version": "subscription_public_entry_execution_binding_v1",
        "enabled": True,
        "repository_root_identity_sha256": hashlib.sha256(
            str(repository).encode()
        ).hexdigest(),
        "workspace_root_identity_sha256": hashlib.sha256(
            str(workspace).encode()
        ).hexdigest(),
        "durable_state_identity_sha256": hashlib.sha256(
            str(state).encode()
        ).hexdigest(),
        "expected_head": head,
        "expected_tree": tree,
        "existing_scope_paths": scope,
        "addable_scope_paths": [],
        "allowed_scope": scope,
        "acceptance_set": acceptance,
        "validation_set": [spec["command"]],
        "worker_configuration_sha256": (
            task_runner_module._worker_configuration_sha256(config)
        ),
        "branch_name": f"agent/{stack}-fixture-v1",
        "commit_message": f"Repair bounded {stack} fixture",
        "finite_budgets": {
            "max_cycles": 2,
            "max_worker_calls": 2,
            "max_patch_operations_per_cycle": 8,
            "max_total_duration_ms": 30_000,
            "max_total_cost_microunits": 1,
        },
        "validation_timeout_seconds": 30,
        "max_validation_output_bytes": 65_536,
        "repository_read_authorized": True,
        "worker_execution_authorized": True,
        "validation_execution_authorized": True,
        "subscription_data_transfer_authorized": True,
        "local_git_write_authorized": True,
        "api_mode_enabled": False,
        "provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "remote_repository_operations_authorized": False,
        "target_repo_mutation_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
        "rollback_execution_authorized": False,
        "max_local_commits": 1,
    }
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {
        "stack": stack, "spec": spec, "repository": repository,
        "head": head, "tree": tree, "workspace": workspace, "state": state,
        "config": config, "manifest": manifest_path, "plan": plan_path,
    }


def _multi_stack_adapter(
    context: dict[str, Any], mode: str, calls: list[dict[str, object]]
) -> CodexCLISubscriptionWorkerAdapter:
    spec = context["spec"]

    def fake_run(
        argv: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        prompt = json.loads(str(kwargs["input"]))
        calls.append(prompt)
        if mode == "repair" and len(calls) == 1:
            before, after = spec["baseline"], spec["intermediate"]
        elif mode == "repair":
            before, after = spec["intermediate"], spec["target"]
        else:
            before, after = spec["baseline"], spec["target"]
        assert prompt["candidate_files"][spec["source"]] == before
        operations = (
            [{"op": "add", "path": "outside-scope.txt", "content": "x\n"}]
            if mode == "scope_denial"
            else [{
                "op": "replace",
                "path": spec["source"],
                "expected_sha256": hashlib.sha256(before.encode()).hexdigest(),
                "content": after,
            }]
        )
        output = {"operations": operations, "usage": {
            "duration_ms": 1, "cost_microunits": 0
        }}
        Path(argv[argv.index("--output-last-message") + 1]).write_text(
            json.dumps(output), encoding="utf-8"
        )
        return subprocess.CompletedProcess(
            argv, 0, stdout='{"type":"turn.completed"}\n', stderr=""
        )

    return CodexCLISubscriptionWorkerAdapter(
        context["config"],
        process_runner=fake_run,
        source_environment={"PATH": "/usr/bin", "HOME": "/isolated/home"},
    )


def _run_multi_stack(
    context: dict[str, Any],
    adapter: CodexCLISubscriptionWorkerAdapter,
    cancellation_requested: Any = None,
) -> dict[str, object]:
    spec = context["spec"]
    return run_subscription_public_entry_execution(
        task_manifest_path=context["manifest"],
        change_plan_path=context["plan"],
        repository_root=context["repository"],
        workspace_root=context["workspace"],
        durable_state_path=context["state"],
        expected_head=context["head"],
        expected_tree=context["tree"],
        blueprint_path="blueprint.yaml",
        module_registry_path="module-registry.yaml",
        milestone_ids=["M1_CALCULATOR"],
        acceptance_requirements=[f"{context['stack']} fixture passes"],
        governance_paths=["GOVERNANCE.md"],
        query_terms=["calculator", context["stack"]],
        seed_paths=[spec["source"], spec["test"]],
        codex_config=context["config"],
        repository_read_authorized=True,
        worker_execution_authorized=True,
        validation_execution_authorized=True,
        subscription_data_transfer_authorized=True,
        local_git_write_authorized=True,
        cancellation_requested=cancellation_requested,
        adapter=adapter,
    )


def _assert_zero_external_effects(result: dict[str, object]) -> None:
    for key in (
        "provider_invocations", "provider_credential_value_accesses",
        "target_repo_mutations", "remote_repository_operations",
        "production_operations", "cleanup_operations", "rollback_operations",
    ):
        assert result[key] == 0
    assert result["api_mode_enabled"] is False


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_implementation(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    calls: list[dict[str, object]] = []
    result = _run_multi_stack(
        context, _multi_stack_adapter(context, "implementation", calls)
    )
    assert result["status"] == "PASS", result
    assert result["terminal_code"] == "LOCAL_COMMIT_RECORDED"
    assert result["worker_invocations"] == 1
    assert len(calls) == 1
    assert _fixture_git(context["workspace"], "remote") == ""
    assert _fixture_git(
        context["workspace"], "rev-list", "--count",
        f"{context['head']}..HEAD"
    ) == "1"
    assert _fixture_git(
        context["workspace"], "show",
        f"HEAD:{context['spec']['source']}"
    ) == context["spec"]["target"].rstrip("\n")
    assert result["draft_pr_plan"]["authorized"] is False
    _assert_zero_external_effects(result)


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_repair(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    calls: list[dict[str, object]] = []
    result = _run_multi_stack(
        context, _multi_stack_adapter(context, "repair", calls)
    )
    assert result["status"] == "PASS", result
    assert result["worker_invocations"] == 2
    assert result["validation_command_invocations"] == 2
    assert calls[1]["candidate_files"][context["spec"]["source"]] == (
        context["spec"]["intermediate"]
    )
    assert _fixture_git(
        context["workspace"], "rev-list", "--count",
        f"{context['head']}..HEAD"
    ) == "1"
    _assert_zero_external_effects(result)


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_scope_denial(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    calls: list[dict[str, object]] = []
    result = _run_multi_stack(
        context, _multi_stack_adapter(context, "scope_denial", calls)
    )
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "PATCH_OUTSIDE_FROZEN_SCOPE"
    assert len(calls) == 1
    assert _fixture_git(
        context["workspace"], "rev-list", "--count",
        f"{context['head']}..HEAD"
    ) == "0"
    _assert_zero_external_effects(result)


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_cancellation(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    calls: list[dict[str, object]] = []
    checks = 0

    def cancelled() -> bool:
        nonlocal checks
        checks += 1
        return checks >= 2

    result = _run_multi_stack(
        context,
        _multi_stack_adapter(context, "implementation", calls),
        cancelled,
    )
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "CANCELLED_BY_CALLER"
    assert len(calls) == 1
    assert (context["workspace"] / context["spec"]["source"]).read_text(
        encoding="utf-8"
    ) == context["spec"]["baseline"]
    assert _fixture_git(
        context["workspace"], "rev-list", "--count",
        f"{context['head']}..HEAD"
    ) == "0"
    _assert_zero_external_effects(result)


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_completed_replay(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    calls: list[dict[str, object]] = []
    adapter = _multi_stack_adapter(context, "implementation", calls)
    first = _run_multi_stack(context, adapter)
    second = _run_multi_stack(context, adapter)
    assert first["status"] == "PASS", first
    assert second["status"] == "PASS", second
    assert second["terminal_code"] == "RESUMED_COMPLETED_LOCAL_COMMIT"
    assert second["commit"] == first["commit"]
    assert len(calls) == 1
    assert _fixture_git(
        context["workspace"], "rev-list", "--count",
        f"{context['head']}..HEAD"
    ) == "1"
    _assert_zero_external_effects(second)


@pytest.mark.parametrize("stack", ["python", "typescript"])
def test_subscription_public_entry_multi_stack_unreceipted_advance_blocks(
    tmp_path: Path, stack: str
) -> None:
    context = _multi_stack_context(tmp_path, stack)
    workspace = context["workspace"]
    created = task_runner_module.create_isolated_local_workspace(
        source_repository_root=context["repository"],
        workspace_root=workspace,
        expected_head_sha=context["head"],
        expected_tree_sha=context["tree"],
    )
    assert created["status"] == "PASS"
    (workspace / context["spec"]["source"]).write_text(
        context["spec"]["target"], encoding="utf-8"
    )
    _fixture_git(
        workspace, "switch", "-c", f"agent/unreceipted-{stack}-fixture-v1"
    )
    _fixture_git(workspace, "add", "--all")
    _fixture_git(
        workspace, "-c", "user.name=Fixture", "-c",
        "user.email=fixture@example.invalid", "commit", "-q", "-m",
        "unreceipted fixture advance"
    )
    calls: list[dict[str, object]] = []
    result = _run_multi_stack(
        context, _multi_stack_adapter(context, "implementation", calls)
    )
    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "HEAD_PRECONDITION_DRIFT"
    assert calls == []
    assert _fixture_git(
        workspace, "rev-list", "--count", f"{context['head']}..HEAD"
    ) == "1"
    _assert_zero_external_effects(result)

