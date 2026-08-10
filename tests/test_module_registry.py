from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml

from tool_system.architecture import module_registry
from tool_system.architecture.module_registry import (
    CURRENT_REGISTRY_INPUT_MODE,
    LEGACY_REGISTRY_INPUT_MODE,
    load_module_identity_mapping,
    validate_module_registry,
)
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/module_registry_v1.yaml"
LOCAL_SCHEMA = ROOT / "config/module_registry_schema_v1.json"
MODULE_CONTRACT = ROOT / "docs/tool_system_module_registry_contract_v1.md"
CONTRACT_DIR = ROOT / "docs/modules"
BLUEPRINT = ROOT / "blueprint/tool_system_v0.yaml"
QWEN_ADAPTER_REPORT = ROOT / "docs/reports/p15c_qwen_runtime_adapter.md"
QWEN_ADAPTER_MANIFEST = (
    ROOT / "examples/task_manifests/tool_system_p15c_qwen_runtime_adapter_v1.yaml"
)
QWEN_ADAPTER_PLAN = (
    ROOT / "examples/change_plans/tool_system_p15c_qwen_runtime_adapter_v1.yaml"
)
QWEN_ECONOMICS_REPORT = (
    ROOT / "docs/reports/p15c_qwen_economics_consistency_correction.md"
)
QWEN_ECONOMICS_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_p15c_qwen_economics_consistency_correction_v1.yaml"
)
QWEN_ECONOMICS_PLAN = (
    ROOT
    / "examples/change_plans/tool_system_p15c_qwen_economics_consistency_correction_v1.yaml"
)
OPENAI_QWEN_MATRIX_REPORT = ROOT / "docs/reports/p15c_openai_qwen_matrix_refreeze.md"
OPENAI_QWEN_MATRIX_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml"
)
OPENAI_QWEN_MATRIX_PLAN = (
    ROOT / "examples/change_plans/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml"
)
P15D_PREREQUISITE_REPORT = (
    ROOT / "docs/reports/p15d_failure_economics_corpus_prerequisite_freeze.md"
)
P15D_PREREQUISITE_MANIFEST = (
    ROOT / "examples/task_manifests/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml"
)
P15D_PREREQUISITE_PLAN = (
    ROOT / "examples/change_plans/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml"
)
P15D_PREREQUISITE_CONFIG = (
    ROOT / "config/p15d_failure_economics_corpus_prerequisite_v1.yaml"
)
P15D_FAILURE_CONTROL_REPORT = (
    ROOT / "docs/reports/p15d_prerequisite_failure_control_fixture_implementation.md"
)
P15D_FAILURE_CONTROL_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml"
)
P15D_FAILURE_CONTROL_PLAN = (
    ROOT
    / "examples/change_plans/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml"
)
DURABLE_SIDECAR_RACE_REPORT = (
    ROOT / "docs/reports/durable_orchestrator_sqlite_sidecar_race_correction.md"
)
DURABLE_SIDECAR_RACE_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_durable_orchestrator_sqlite_sidecar_race_correction_v1.yaml"
)
DURABLE_SIDECAR_RACE_PLAN = (
    ROOT
    / "examples/change_plans/tool_system_durable_orchestrator_sqlite_sidecar_race_correction_v1.yaml"
)
AI_WORKER_REALIGNMENT_REPORT = (
    ROOT / "docs/reports/provider_mode_ai_worker_runtime_realignment.md"
)
AI_WORKER_REALIGNMENT_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_provider_mode_ai_worker_runtime_realignment_v1.yaml"
)
AI_WORKER_REALIGNMENT_PLAN = (
    ROOT
    / "examples/change_plans/tool_system_provider_mode_ai_worker_runtime_realignment_v1.yaml"
)
PROVIDER_PORTFOLIO_REALIGNMENT_REPORT = (
    ROOT / "docs/reports/provider_mode_adaptive_provider_portfolio_realignment.md"
)
PROVIDER_PORTFOLIO_REALIGNMENT_MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_provider_mode_adaptive_provider_portfolio_realignment_v1.yaml"
)
PROVIDER_PORTFOLIO_REALIGNMENT_PLAN = (
    ROOT
    / "examples/change_plans/tool_system_provider_mode_adaptive_provider_portfolio_realignment_v1.yaml"
)
PROJECT_STATE = ROOT / "docs/tool_system_project_state_v1.yaml"
REPO_WRITE_POLICY = ROOT / "policy/repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy/autonomy_policy.yaml"
PACKET_CONFIG = ROOT / "config/p15c_execution_packet_freeze_v1.yaml"
QWEN_ADAPTER_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/p15c_qwen_runtime_adapter.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_qwen_runtime_adapter_v1.yaml",
    "examples/operator_config/tool_system_settings.example.toml",
    "examples/task_manifests/tool_system_p15c_qwen_runtime_adapter_v1.yaml",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "src/tool_system/ai_worker/p15c_controls.py",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_controls.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_local_operator_config.py",
}
QWEN_ECONOMICS_FILES = {
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/p15c_qwen_economics_consistency_correction.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_qwen_economics_consistency_correction_v1.yaml",
    "examples/task_manifests/tool_system_p15c_qwen_economics_consistency_correction_v1.yaml",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_module_registry.py",
}
OPENAI_QWEN_MATRIX_FILES = {
    "config/module_registry_v1.yaml",
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15c_openai_qwen_matrix_refreeze.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml",
    "examples/task_manifests/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_entry.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_execution_packet_freeze.py",
}
P15D_PREREQUISITE_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "config/p15d_failure_economics_corpus_prerequisite_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15d_failure_economics_corpus_prerequisite_freeze.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml",
    "examples/task_manifests/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml",
    "tests/test_module_registry.py",
    "tests/test_p15d_failure_economics_corpus_prerequisite.py",
    "tests/test_repo_manifest.py",
}
P15D_FAILURE_CONTROL_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15d_prerequisite_failure_control_fixture_implementation.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml",
    "examples/task_manifests/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml",
    "src/tool_system/provider_portfolio/__init__.py",
    "src/tool_system/provider_portfolio/failure_control.py",
    "tests/test_module_registry.py",
    "tests/test_provider_portfolio_failure_control.py",
    "tests/test_repo_manifest.py",
}
DURABLE_SIDECAR_RACE_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/durable-orchestrator-contract-v1.md",
    "docs/reports/durable_orchestrator_sqlite_sidecar_race_correction.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_durable_orchestrator_sqlite_sidecar_race_correction_v1.yaml",
    "examples/task_manifests/tool_system_durable_orchestrator_sqlite_sidecar_race_correction_v1.yaml",
    "src/tool_system/orchestrator/durable.py",
    "tests/test_durable_orchestrator_reliability.py",
    "tests/test_module_registry.py",
    "tests/test_repo_manifest.py",
}
AI_WORKER_REALIGNMENT_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/provider_mode_ai_worker_runtime_realignment.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_provider_mode_ai_worker_runtime_realignment_v1.yaml",
    "examples/operator_config/tool_system_settings.example.toml",
    "examples/task_manifests/tool_system_provider_mode_ai_worker_runtime_realignment_v1.yaml",
    "src/tool_system/ai_worker/__init__.py",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "src/tool_system/ai_worker/p15c_controls.py",
    "src/tool_system/ai_worker/p15c_entry.py",
    "src/tool_system/ai_worker/runtime.py",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_controls.py",
    "tests/test_ai_worker_p15c_entry.py",
    "tests/test_ai_worker_provider_mode.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_local_operator_config.py",
    "tests/test_repo_manifest.py",
}
PROVIDER_PORTFOLIO_REALIGNMENT_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/provider_mode_adaptive_provider_portfolio_realignment.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_provider_mode_adaptive_provider_portfolio_realignment_v1.yaml",
    "examples/task_manifests/tool_system_provider_mode_adaptive_provider_portfolio_realignment_v1.yaml",
    "src/tool_system/provider_portfolio/__init__.py",
    "src/tool_system/provider_portfolio/failure_control.py",
    "src/tool_system/provider_portfolio/provider_mode.py",
    "tests/test_module_registry.py",
    "tests/test_provider_portfolio_failure_control.py",
    "tests/test_provider_portfolio_provider_mode.py",
    "tests/test_repo_manifest.py",
}
PRE_MATRIX_CANONICAL_PACKET_SHA256 = (
    "509270b737aab11776397a5d5db9c0a6f8a89165a07f37002a669cb2cbf3a962"
)
OPENAI_QWEN_MATRIX_PACKET_SHA256 = (
    "cc8a924d73106d6f373e7cf2ddab11170be8b8409dcaed040aef5cf8cba5b34a"
)

EXPECTED_RAW_SHA256 = "e75115bb40c3577ab9e758ddd58d48eecab16e5d5c85b3eaf09f5eb95a1235e3"
EXPECTED_BYTE_LENGTH = 124_859
EXPECTED_SEMANTIC_SHA256 = (
    "860f48c2013c44303506624d9015bfa7dd2e67ce89474fb752dd1957240d49ae"
)
EXPECTED_MANAGED_PYTHON_FILE_COUNT = 122
EXPECTED_MODULE_IDS = {
    "architecture_registry",
    "manifest_validation",
    "agent_worker_runtime",
    "ai_worker_runtime",
    "adaptive_model_portfolio_and_economics",
    "durable_orchestrator",
    "repository_controller",
    "process_authority",
    "task_planner",
    "task_runner",
    "role_runtime",
    "worker_adapter",
    "target_repo_adapter",
    "cleanup_planner",
    "cli_frontend",
    "repository_context",
    "blueprint_compiler",
    "development_loop",
    "local_git",
    "release_governance",
    "state_migration",
    "recovery_planning",
    "operational_observability",
    "record_retention",
    "subscription_capacity",
    "production_readiness",
}
TARGET_OWNER_DELTAS = {
    "src/tool_system/gate/command_runner.py": (
        "manifest_validation",
        "task_runner",
    ),
    "src/tool_system/gate/test_gate.py": (
        "manifest_validation",
        "task_runner",
    ),
}
TEST_SELECTORS = {
    "architecture_registry": "tests/test_module_registry.py",
    "manifest_validation": "tests/test_task_manifest_policy.py",
    "agent_worker_runtime": "tests/test_agent_worker_interface.py",
    "ai_worker_runtime": "tests/test_ai_worker_contract.py",
    "adaptive_model_portfolio_and_economics": "tests/test_provider_portfolio_fixtures.py",
    "durable_orchestrator": "tests/test_durable_orchestrator_state.py",
    "repository_controller": "tests/test_repo_controller.py",
    "process_authority": "tests/test_process_authority.py",
    "task_planner": "tests/test_task_graph.py",
    "task_runner": "tests/test_task_runner.py",
    "role_runtime": "tests/test_role_runtime.py",
    "worker_adapter": "tests/test_worker_adapter_contract.py",
    "target_repo_adapter": "tests/test_target_repo_dry_run.py",
    "cleanup_planner": "tests/test_cleanup_plan.py",
    "cli_frontend": "tests/test_root_cli.py",
    "repository_context": "tests/test_repository_context_builder.py",
    "blueprint_compiler": "tests/test_blueprint_compiler.py",
    "development_loop": "tests/test_development_loop.py",
    "local_git": "tests/test_local_git_orchestrator.py",
    "release_governance": "tests/test_release_governance.py",
    "state_migration": "tests/test_state_migration.py",
    "recovery_planning": "tests/test_recovery_planning.py",
    "operational_observability": "tests/test_operational_observability.py",
    "record_retention": "tests/test_record_retention.py",
    "subscription_capacity": "tests/test_subscription_capacity.py",
    "production_readiness": "tests/test_production_readiness.py",
}
ADDITIONAL_TEST_SELECTORS = {
    "adaptive_model_portfolio_and_economics": (
        "tests/test_p15d_failure_economics_corpus_prerequisite.py",
        "tests/test_provider_portfolio_failure_control.py",
        "tests/test_provider_portfolio_provider_mode.py",
    ),
    "ai_worker_runtime": (
        "tests/test_ai_worker_live_provider.py",
        "tests/test_ai_worker_p15c_benchmark.py",
        "tests/test_ai_worker_p15c_controls.py",
        "tests/test_ai_worker_p15c_entry.py",
        "tests/test_p15c_local_operator_config.py",
        "tests/test_ai_worker_provider_mode.py",
    ),
    "durable_orchestrator": ("tests/test_durable_orchestrator_reliability.py",),
    "process_authority": ("tests/test_p14c_live_issuer.py",),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_path(name: str) -> Path:
    value = subprocess.run(
        ["git", "rev-parse", "--git-path", name],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _yaml_block(path: Path, name: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = f"<!-- {name}:BEGIN -->\n~~~yaml\n"
    end = f"\n~~~\n<!-- {name}:END -->"
    assert text.count(start) == text.count(end) == 1
    value = yaml.safe_load(text.split(start, 1)[1].split(end, 1)[0])
    assert isinstance(value, dict)
    return value


def authority_contracts() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for mapping in load_module_identity_mapping(ROOT):
        path = CONTRACT_DIR / f"{mapping['canonical_module_id']}-contract-v1.md"
        contract = _yaml_block(path, "MODULE-COMPOUND-CONTRACT")[
            "module_compound_contract"
        ]
        assert contract["identity"]["current_module_id"] == mapping["current_module_id"]
        result[str(mapping["current_module_id"])] = contract
    assert set(result) == EXPECTED_MODULE_IDS
    return result


def _python_import_identity(path: Path) -> str:
    parts = list(path.relative_to(ROOT / "src").with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _selector_matches(selector: dict[str, str], import_name: str) -> bool:
    name = selector["name"]
    if selector["kind"] == "exact":
        return import_name == name
    return import_name == name or import_name.startswith(f"{name}.")


def target_python_owner_by_path() -> dict[str, str]:
    mappings = load_module_identity_mapping(ROOT)
    result: dict[str, str] = {}
    for path in sorted((ROOT / "src/tool_system").rglob("*.py")):
        import_name = _python_import_identity(path)
        matches = [
            str(mapping["current_module_id"])
            for mapping in mappings
            for selector in mapping["python_import_identities"]
            if _selector_matches(selector, import_name)
        ]
        assert len(matches) == 1
        result[path.relative_to(ROOT).as_posix()] = matches[0]
    assert len(result) == EXPECTED_MANAGED_PYTHON_FILE_COUNT
    return result


def authority_code_paths() -> dict[str, list[str]]:
    contracts = authority_contracts()
    result = {
        current_id: list(contract["natural_owner_evidence_paths"])
        for current_id, contract in contracts.items()
    }
    flattened = [path for paths in result.values() for path in paths]
    assert len(flattened) == len(set(flattened)) == 130
    python_owners = target_python_owner_by_path()
    assert {
        path: current_id
        for current_id, paths in result.items()
        for path in paths
        if path.startswith("src/tool_system/") and path.endswith(".py")
    } == python_owners
    return result


def current_registry_fixture() -> dict[str, Any]:
    return copy.deepcopy(load_yaml_file(REGISTRY))


def _write_registry(tmp_path: Path, registry: dict[str, Any]) -> Path:
    path = tmp_path / "module_registry_v1.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def _modules_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(module["module_id"]): module for module in registry["modules"]}


def _iter_contract_references(
    registry: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    for module in registry["modules"]:
        yield module["rollback_boundary"]
        yield module["replacement_boundary"]
        for category in ("code", "data", "tests", "runtime_artifacts", "cleanup"):
            for boundary in module["boundaries"][category]:
                if "root_contract" in boundary:
                    yield boundary["root_contract"]
        for effect in module["permitted_side_effects"]:
            yield effect["effect_contract"]
    for interface in registry["interfaces"]:
        for field in (
            "input_contract",
            "output_contract",
            "error_contract",
            "side_effect_contract",
            "compatibility_policy",
            "replacement_revalidation_boundary",
        ):
            yield interface[field]


def authority_effect_matrices() -> tuple[
    list[tuple[str, str, str, tuple[str, ...], str]],
    dict[tuple[str, str, str, str], tuple[str, ...]],
]:
    mappings = {
        str(row["current_module_id"]): row for row in load_module_identity_mapping(ROOT)
    }
    expanded: list[tuple[str, str, str, tuple[str, ...], str]] = []
    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    for current_id, contract in authority_contracts().items():
        canonical = str(mappings[current_id]["canonical_module_id"])
        path = ROOT / str(contract["contract_path"])
        digest = _sha256(path)
        effects = contract["side_effect_contract"]
        assert effects["classification_grants_authority"] is False
        for effect in effects["direct_effects"]:
            for target in effect["evidence_paths"]:
                row = (
                    canonical,
                    "direct",
                    target,
                    (str(effect["effect_class"]),),
                    digest,
                )
                expanded.append(row)
                key = (canonical, "direct", target, digest)
                grouped.setdefault(key, [])
                if effect["effect_class"] not in grouped[key]:
                    grouped[key].append(str(effect["effect_class"]))
        for capability in effects["delegated_effects"]:
            assert capability["capability_state"] == ("conditional-delegated-maximum")
            assert capability["classification_grants_authority"] is False
            for target in capability["evidence_paths"]:
                row = (
                    canonical,
                    "conditional-delegated",
                    target,
                    tuple(capability["effect_classes"]),
                    digest,
                )
                expanded.append(row)
                key = (canonical, "conditional-delegated", target, digest)
                grouped.setdefault(key, [])
                for effect_class in capability["effect_classes"]:
                    if effect_class not in grouped[key]:
                        grouped[key].append(str(effect_class))
    return expanded, {key: tuple(value) for key, value in grouped.items()}


def _registry_effect_matrix(
    registry: dict[str, Any],
) -> dict[tuple[str, str, str, str], tuple[str, ...]]:
    result: dict[tuple[str, str, str, str], tuple[str, ...]] = {}
    for module in registry["modules"]:
        path_by_boundary = {
            boundary["boundary_id"]: boundary["path"]
            for category in ("code", "data", "tests", "runtime_artifacts", "cleanup")
            for boundary in module["boundaries"][category]
        }
        for effect in module["permitted_side_effects"]:
            effect_id = str(effect["effect_id"])
            identity = (
                "conditional-delegated"
                if effect_id.startswith("conditional-delegated-effects-")
                else "direct"
            )
            reference = effect["effect_contract"]
            key = (
                str(module["module_id"]),
                identity,
                str(path_by_boundary[effect["target_boundary_id"]]),
                str(reference["sha256"]),
            )
            assert key not in result
            result[key] = tuple(effect["effect_classes"])
    return result


def assert_effect_oracle(registry: dict[str, Any]) -> None:
    expanded, grouped = authority_effect_matrices()
    assert len(expanded) == 97
    assert len(grouped) == 45
    assert _registry_effect_matrix(registry) == grouped


def legacy_registry_fixture() -> dict[str, Any]:
    mappings = load_module_identity_mapping(ROOT)
    contracts = authority_contracts()
    by_current = {str(row["current_module_id"]): row for row in mappings}
    downstream = {
        current_id: list(contract["dependency_contract"]["direct_consumer_module_ids"])
        for current_id, contract in contracts.items()
    }
    modules = []
    for row in mappings:
        current_id = str(row["current_module_id"])
        contract = contracts[current_id]
        interface_major = str(row["aggregate_interface_version"]).split(".")[0]

        def dependency(target: str) -> dict[str, str]:
            return {
                "module_id": target,
                "module_version": str(by_current[target]["current_module_version"]),
                "public_interface_version": str(
                    by_current[target]["aggregate_interface_version"]
                ).split(".")[0],
            }

        modules.append(
            {
                "module_id": current_id,
                "module_version": row["current_module_version"],
                "owner": row["canonical_module_id"],
                "lifecycle": "ACTIVE",
                "status": "REGISTERED",
                "single_responsibility": contract["role"]["summary"],
                "blueprint_objective_ref": "product_objective",
                "natural_owner_paths": contract["natural_owner_evidence_paths"],
                "public_interface_version": interface_major,
                "input_contract": ["legacy-compatibility-fixture"],
                "output_contract": ["legacy-compatibility-fixture"],
                "error_semantics": ["legacy-compatibility-fixture"],
                "externally_visible_side_effects": ["legacy-compatibility-fixture"],
                "code_boundary": ["legacy-compatibility-fixture"],
                "data_boundary": ["legacy-compatibility-fixture"],
                "test_boundary": ["legacy-compatibility-fixture"],
                "runtime_artifact_boundary": ["legacy-compatibility-fixture"],
                "cleanup_boundary": ["legacy-compatibility-fixture"],
                "upstream_dependency_module_ids_and_versions": [
                    dependency(target)
                    for target in contract["dependency_contract"][
                        "direct_provider_module_ids"
                    ]
                ],
                "downstream_dependency_module_ids_and_versions": [
                    dependency(target) for target in downstream[current_id]
                ],
                "content_hashes_and_expected_preconditions": [
                    "legacy-compatibility-fixture"
                ],
                "authorization_envelope": ["no-authority"],
                "acceptance_evidence": ["legacy-compatibility-fixture"],
                "rollback_evidence": ["legacy-compatibility-fixture"],
                "replacement_evidence": ["legacy-compatibility-fixture"],
            }
        )
    return {
        "registry_version": "module_registry_v1",
        "blueprint_objective_ref": "product_objective",
        "modules": modules,
    }


def test_qwen_runtime_adapter_pair_scope_and_zero_io_state_validate() -> None:
    manifest_result = validate_task_manifest(
        QWEN_ADAPTER_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(QWEN_ADAPTER_PLAN)
    manifest = load_yaml_file(QWEN_ADAPTER_MANIFEST)
    plan = load_yaml_file(QWEN_ADAPTER_PLAN)
    state = load_yaml_file(PROJECT_STATE)["p15c_qwen_runtime_adapter"]
    report = QWEN_ADAPTER_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == QWEN_ADAPTER_FILES
    assert set(manifest["scope"]["in_scope"]) == QWEN_ADAPTER_FILES
    assert set(plan["changed_files"]) == QWEN_ADAPTER_FILES
    assert len(QWEN_ADAPTER_FILES) == 15
    assert state["canonical_packet_catalog_sha256"] == (
        PRE_MATRIX_CANONICAL_PACKET_SHA256
    )
    assert state["module"]["module_version"] == "1.9.0"
    assert state["exact_qwen_adapter"]["exact_model_version"] == (
        "qwen3.7-plus-2026-05-26"
    )
    assert state["currency_accounting"]["minimum_micro_usd_per_cny"] == (1_000_000)
    assert state["canonical_packet_catalog_changed"] is False
    assert state["synthetic_matrix_only"] is True
    assert state["qwen_funding_attested"] is False
    assert state["source_stage_evidence"]["credential_value_accesses"] == 0
    assert state["source_stage_evidence"]["provider_invocations"] == 0
    assert state["source_stage_evidence"]["benchmark_executions"] == 0
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_authorized"] is False
    assert "ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION" in report
    assert "qwen3.7-plus-2026-05-26" in report
    assert "provider_invocations: 0" in report


def test_qwen_economics_correction_pair_scope_and_zero_io_state_validate() -> None:
    manifest_result = validate_task_manifest(
        QWEN_ECONOMICS_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(QWEN_ECONOMICS_PLAN)
    manifest = load_yaml_file(QWEN_ECONOMICS_MANIFEST)
    plan = load_yaml_file(QWEN_ECONOMICS_PLAN)
    state = load_yaml_file(PROJECT_STATE)["p15c_qwen_economics_consistency_correction"]
    report = QWEN_ECONOMICS_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == QWEN_ECONOMICS_FILES
    assert set(manifest["scope"]["in_scope"]) == QWEN_ECONOMICS_FILES
    assert set(plan["changed_files"]) == QWEN_ECONOMICS_FILES
    assert len(QWEN_ECONOMICS_FILES) == 10
    assert state["canonical_packet_catalog_sha256"] == (
        PRE_MATRIX_CANONICAL_PACKET_SHA256
    )
    assert state["module"]["previous_module_version"] == "1.9.0"
    assert state["module"]["module_version"] == "1.9.1"
    assert (
        state["corrected_invariant"]["current_calculated_worst_case_micro_cny"]
        == 196_608
    )
    assert state["corrected_invariant"]["per_attempt_hard_cap_micro_cny"] == (250_000)
    assert state["canonical_packet_catalog_changed"] is False
    assert state["qwen_selected_in_canonical_matrix"] is False
    assert state["qwen_funding_attested"] is False
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_authorized"] is False
    assert "ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION" in report
    assert "196608 microCNY" in report
    assert "provider_invocations: 0" in report


def test_openai_qwen_matrix_pair_scope_module_and_zero_io_state_validate() -> None:
    manifest_result = validate_task_manifest(
        OPENAI_QWEN_MATRIX_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(OPENAI_QWEN_MATRIX_PLAN)
    manifest = load_yaml_file(OPENAI_QWEN_MATRIX_MANIFEST)
    plan = load_yaml_file(OPENAI_QWEN_MATRIX_PLAN)
    state = load_yaml_file(PROJECT_STATE)["p15c_openai_qwen_matrix_refreeze"]
    packet = load_yaml_file(PACKET_CONFIG)
    report = OPENAI_QWEN_MATRIX_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == OPENAI_QWEN_MATRIX_FILES
    assert set(manifest["scope"]["in_scope"]) == OPENAI_QWEN_MATRIX_FILES
    assert set(plan["changed_files"]) == OPENAI_QWEN_MATRIX_FILES
    assert len(OPENAI_QWEN_MATRIX_FILES) == 12
    assert hashlib.sha256(PACKET_CONFIG.read_bytes()).hexdigest() == (
        OPENAI_QWEN_MATRIX_PACKET_SHA256
    )
    assert state["module"]["previous_module_version"] == "1.0.0"
    assert state["module"]["module_version"] == "1.1.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert state["execution_matrix"]["provider_ids"] == ["openai", "qwen"]
    assert packet["execution_matrix"]["provider_ids"] == ["openai", "qwen"]
    assert state["provider_dispositions"]["deepseek"]["selected"] is False
    assert state["provider_dispositions"]["qwen"]["funding_attested"] is False
    assert state["provider_transfer_authorization_record"] == {
        "deepseek": False,
        "openai": True,
        "qwen": True,
        "grants_runtime_transfer": False,
        "private_policy_and_target_packet_match_required": True,
    }
    assert state["local_validation"]["packet_only_zero_io"] == "passed"
    assert state["local_validation"]["default_preflight_before_private_input"] == (
        "PROVIDER_PACKET_BLOCKED"
    )
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["qwen_funding_attested"] is False
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_authorized"] is False
    assert (
        "ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_BLOCKED_NOT_FUNDED_NO_EXECUTION"
        in report
    )
    assert "provider_invocations: 0" in report


def test_p15d_prerequisite_scope_module_and_stage_stop_validate() -> None:
    manifest_result = validate_task_manifest(
        P15D_PREREQUISITE_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P15D_PREREQUISITE_PLAN)
    manifest = load_yaml_file(P15D_PREREQUISITE_MANIFEST)
    plan = load_yaml_file(P15D_PREREQUISITE_PLAN)
    state = load_yaml_file(PROJECT_STATE)["p15d_prerequisite_corpus_freeze"]
    corpus = load_yaml_file(P15D_PREREQUISITE_CONFIG)
    report = P15D_PREREQUISITE_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P15D_PREREQUISITE_FILES
    assert set(manifest["scope"]["in_scope"]) == P15D_PREREQUISITE_FILES
    assert set(plan["changed_files"]) == P15D_PREREQUISITE_FILES
    assert len(P15D_PREREQUISITE_FILES) == 12
    assert state["module"]["previous_module_version"] == "1.1.0"
    assert state["module"]["module_version"] == "1.2.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert state["frozen_case_ids"] == [
        case["case_id"] for case in corpus["case_catalog"]
    ]
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["funding_or_live_execution_required_for_this_freeze"] is False
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_stage_entered"] is False
    assert state["p15d_stage_accepted"] is False
    assert state["p15e_authorized"] is False
    assert "NON_EXECUTING_PREENTRY_FREEZE" in report
    assert "provider_invocations: 0" in report


def test_p15d_failure_control_scope_module_and_stage_stop_validate() -> None:
    manifest_result = validate_task_manifest(
        P15D_FAILURE_CONTROL_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P15D_FAILURE_CONTROL_PLAN)
    manifest = load_yaml_file(P15D_FAILURE_CONTROL_MANIFEST)
    plan = load_yaml_file(P15D_FAILURE_CONTROL_PLAN)
    state = load_yaml_file(PROJECT_STATE)["p15d_prerequisite_failure_control_fixture"]
    report = P15D_FAILURE_CONTROL_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P15D_FAILURE_CONTROL_FILES
    assert set(manifest["scope"]["in_scope"]) == P15D_FAILURE_CONTROL_FILES
    assert set(plan["changed_files"]) == P15D_FAILURE_CONTROL_FILES
    assert len(P15D_FAILURE_CONTROL_FILES) == 13
    assert state["module"]["previous_module_version"] == "1.2.0"
    assert state["module"]["module_version"] == "1.3.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert state["implementation"]["frozen_prerequisite_packet_modified"] is False
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["funding_or_live_execution_required_for_this_fixture"] is False
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_stage_entered"] is False
    assert state["p15d_stage_accepted"] is False
    assert state["p15e_authorized"] is False
    assert "NON_EXECUTING_PREREQUISITE_FIXTURE" in report
    assert "dispatch_authorized" in report
    assert "provider_invocations: 0" in report


def test_durable_sidecar_race_correction_scope_and_boundary_validate() -> None:
    manifest_result = validate_task_manifest(
        DURABLE_SIDECAR_RACE_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(DURABLE_SIDECAR_RACE_PLAN)
    manifest = load_yaml_file(DURABLE_SIDECAR_RACE_MANIFEST)
    plan = load_yaml_file(DURABLE_SIDECAR_RACE_PLAN)
    state = load_yaml_file(PROJECT_STATE)[
        "durable_orchestrator_sqlite_sidecar_race_correction"
    ]
    report = DURABLE_SIDECAR_RACE_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == DURABLE_SIDECAR_RACE_FILES
    assert set(manifest["scope"]["in_scope"]) == DURABLE_SIDECAR_RACE_FILES
    assert set(plan["changed_files"]) == DURABLE_SIDECAR_RACE_FILES
    assert len(DURABLE_SIDECAR_RACE_FILES) == 12
    assert state["module"]["previous_module_version"] == "1.1.0"
    assert state["module"]["module_version"] == "1.2.0"
    assert state["module"]["aggregate_interface_version"] == "1.1.0"
    assert state["module"]["sqlite_schema_version"] == 3
    assert state["correction"]["missing_before_atomic_lstat_is_valid_absence"]
    assert state["correction"]["observed_regular_zero_link_metadata_is_valid_absence"]
    assert state["correction"]["observed_multilink_blocked"]
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["funding_or_live_execution_required_for_this_correction"] is False
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_stage_entered"] is False
    assert state["p15d_stage_accepted"] is False
    assert state["p15e_authorized"] is False
    assert "RELIABILITY_CORRECTION" in report
    assert "st_nlink == 0" in report
    assert "provider_invocations: 0" in report


def test_ai_worker_runtime_realignment_scope_module_and_stage_stop_validate() -> None:
    manifest_result = validate_task_manifest(
        AI_WORKER_REALIGNMENT_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(AI_WORKER_REALIGNMENT_PLAN)
    manifest = load_yaml_file(AI_WORKER_REALIGNMENT_MANIFEST)
    plan = load_yaml_file(AI_WORKER_REALIGNMENT_PLAN)
    project = load_yaml_file(PROJECT_STATE)
    state = project["provider_mode_and_acceptance_realignment_lifecycle"][
        "ai_worker_runtime_package"
    ]
    registry = load_yaml_file(REGISTRY)
    module = next(
        item for item in registry["modules"] if item["module_id"] == "ai-worker-runtime"
    )
    report = AI_WORKER_REALIGNMENT_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == AI_WORKER_REALIGNMENT_FILES
    assert set(manifest["scope"]["in_scope"]) == AI_WORKER_REALIGNMENT_FILES
    assert set(plan["changed_files"]) == AI_WORKER_REALIGNMENT_FILES
    assert len(AI_WORKER_REALIGNMENT_FILES) == 21
    assert state["module"]["previous_module_version"] == "1.9.1"
    assert state["module"]["module_version"] == module["module_version"] == "2.0.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert state["active_policy_schema"] == 3
    assert state["active_case_ids"] == ["deterministic-corpus"]
    assert state["private_target_loaded_by_active_route"] is False
    assert state["all_provider_adapters_fake_io_covered"] is True
    assert state["static_funding_or_exact_version_label_is_completion_gate"] is False
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["p15_stage_accepted"] is False
    assert state["p16_stage_entered"] is False
    assert state["final_live_smoke_executed"] is False
    assert state["publication_continuity"]["draft_pr"] == 185
    assert state["publication_continuity"]["force_update_used"] is False
    assert project["provider_mode_and_acceptance_realignment_lifecycle"][
        "adaptive_provider_portfolio_package"
    ]["status"] == (
        "accepted_only_on_guarded_squash_merge_portfolio_realignment_no_execution"
    )
    assert "schema-3" in report
    assert "NO_AVAILABLE_PROVIDER" in report
    assert "provider_invocations: 0" in report


def test_provider_portfolio_realignment_scope_module_and_stage_stop_validate() -> None:
    manifest_result = validate_task_manifest(
        PROVIDER_PORTFOLIO_REALIGNMENT_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(PROVIDER_PORTFOLIO_REALIGNMENT_PLAN)
    manifest = load_yaml_file(PROVIDER_PORTFOLIO_REALIGNMENT_MANIFEST)
    plan = load_yaml_file(PROVIDER_PORTFOLIO_REALIGNMENT_PLAN)
    project = load_yaml_file(PROJECT_STATE)
    state = project["provider_mode_and_acceptance_realignment_lifecycle"][
        "adaptive_provider_portfolio_package"
    ]
    registry = load_yaml_file(REGISTRY)
    module = next(
        item
        for item in registry["modules"]
        if item["module_id"] == "adaptive-model-portfolio-and-economics"
    )
    report = PROVIDER_PORTFOLIO_REALIGNMENT_REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == PROVIDER_PORTFOLIO_REALIGNMENT_FILES
    assert set(manifest["scope"]["in_scope"]) == (
        PROVIDER_PORTFOLIO_REALIGNMENT_FILES
    )
    assert set(plan["changed_files"]) == PROVIDER_PORTFOLIO_REALIGNMENT_FILES
    assert len(PROVIDER_PORTFOLIO_REALIGNMENT_FILES) == 15
    assert state["baseline_commit"] == (
        "529001694c6d41ee819736293418cebfe455c392"
    )
    assert state["module"]["previous_module_version"] == "1.3.0"
    assert state["module"]["module_version"] == module["module_version"] == "2.0.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert state["active_route_mode"] == (
        "repository_external_priority_requested_model_single_route"
    )
    assert state["all_large_model_apis_default_disabled"] is True
    assert state["key_presence_grants_call_authority"] is False
    assert state["availability_only_provider_skips"] is True
    assert state["hard_control_provider_bypass_allowed"] is False
    assert state["exact_matrix_is_compatibility_only"] is True
    assert state["simultaneous_multi_provider_availability_required"] is False
    assert state["named_provider_funding_required"] is False
    assert state["moving_alias_exact_version_required"] is False
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["p15_stage_accepted"] is False
    assert state["p16_stage_entered"] is False
    assert state["final_live_smoke_executed"] is False
    assert "API_DISABLED" in report
    assert "NO_AVAILABLE_PROVIDER" in report
    assert "provider_invocations: 0" in report


def test_authoritative_registry_exact_seals_schema_and_counts() -> None:
    raw = REGISTRY.read_bytes()
    registry = load_yaml_file(REGISTRY)
    normalized = json.dumps(
        registry,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    assert set(registry) == {
        "registry_contract_version",
        "canonical_repo_id",
        "modules",
        "interfaces",
    }
    assert len(raw) == EXPECTED_BYTE_LENGTH
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_RAW_SHA256
    assert hashlib.sha256(normalized).hexdigest() == EXPECTED_SEMANTIC_SHA256
    assert len(registry["modules"]) == len(registry["interfaces"]) == 26
    assert (
        sum(len(module["boundaries"]["code"]) for module in registry["modules"]) == 130
    )
    assert (
        sum(len(module["boundaries"]["tests"]) for module in registry["modules"]) == 37
    )
    assert (
        sum(len(module["permitted_side_effects"]) for module in registry["modules"])
        == 45
    )
    assert len(list(_iter_contract_references(registry))) == 253
    assert (
        sum(len(module["external_dependencies"]) for module in registry["modules"]) == 0
    )
    assert len(target_python_owner_by_path()) == 122
    assert_effect_oracle(registry)


def test_current_current_registry_is_authority_and_tmp_copy_is_not(
    tmp_path: Path,
) -> None:
    current = validate_module_registry(
        REGISTRY,
        ROOT,
        require_current_authority=True,
    )
    fixture = _write_registry(tmp_path, current_registry_fixture())
    compatibility = validate_module_registry(fixture, ROOT)

    assert current["status"] == "PASS", current["reasons"]
    assert current["registry_input_mode"] == CURRENT_REGISTRY_INPUT_MODE
    assert current["current_registry_authority"] is True
    assert current["validation_scope"] == "tool_system_current_module_registry"
    assert current["compatibility_adapter"]["applied"] is False
    assert current["contract_reference_count"] == 253
    assert current["external_provider_count"] == 0
    assert compatibility["status"] == "PASS"
    assert compatibility["current_registry_authority"] is False
    assert compatibility["validation_scope"] == "tool_system_local_compatibility_only"
    assert compatibility["compatibility_adapter"]["applied"] is False


def test_legacy_registry_remains_memory_only_compatibility(
    tmp_path: Path,
) -> None:
    fixture = _write_registry(tmp_path, legacy_registry_fixture())
    result = validate_module_registry(fixture, ROOT)
    authority = validate_module_registry(
        fixture,
        ROOT,
        require_current_authority=True,
    )

    assert result["status"] == "PASS"
    assert result["registry_input_mode"] == LEGACY_REGISTRY_INPUT_MODE
    assert result["current_registry_authority"] is False
    assert result["compatibility_adapter"]["applied"] is True
    assert result["compatibility_adapter"]["translation_boundary"] == "memory_only"
    assert authority["status"] == "BLOCK"


def test_module_contracts_close_identity_boundaries_dag_and_effects() -> None:
    registry = load_yaml_file(REGISTRY)
    mappings = load_module_identity_mapping(ROOT)
    contracts = authority_contracts()
    modules = _modules_by_id(registry)
    interfaces = {
        (interface["interface_id"], interface["interface_version"]): interface
        for interface in registry["interfaces"]
    }
    code_paths = authority_code_paths()
    edge_count = 0

    for row in mappings:
        current = str(row["current_module_id"])
        canonical = str(row["canonical_module_id"])
        contract = contracts[current]
        module = modules[canonical]
        assert module["module_version"] == row["current_module_version"]
        assert module["owner"] == canonical
        assert [
            boundary["path"] for boundary in module["boundaries"]["code"]
        ] == code_paths[current]
        assert [boundary["path"] for boundary in module["boundaries"]["tests"]] == [
            TEST_SELECTORS[current],
            *ADDITIONAL_TEST_SELECTORS.get(current, ()),
        ]
        expected_dependencies = {
            (
                next(
                    mapping["aggregate_interface_id"]
                    for mapping in mappings
                    if mapping["current_module_id"] == provider
                ),
                next(
                    mapping["aggregate_interface_version"]
                    for mapping in mappings
                    if mapping["current_module_id"] == provider
                ),
            )
            for provider in contract["dependency_contract"][
                "direct_provider_module_ids"
            ]
        }
        assert {
            (dependency["interface_id"], dependency["interface_version"])
            for dependency in module["internal_dependencies"]
        } == expected_dependencies
        edge_count += len(expected_dependencies)
        key = (row["aggregate_interface_id"], row["aggregate_interface_version"])
        assert interfaces[key]["provider_module_id"] == canonical
    assert edge_count == 44
    assert_effect_oracle(registry)


def test_manifest_selector_and_unique_registry_authority_path() -> None:
    registry = load_yaml_file(REGISTRY)
    modules = _modules_by_id(registry)
    assert [
        boundary["path"]
        for boundary in modules["manifest-validation"]["boundaries"]["tests"]
    ] == ["tests/test_task_manifest_policy.py"]
    assert [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*module_registry*.y*ml")
        if ".git" not in path.relative_to(ROOT).parts
    ] == ["config/module_registry_v1.yaml"]
    forbidden_names = ("projection", "cache", "generated_registry")
    assert not [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and "module_registry" in path.name
        and any(name in path.name for name in forbidden_names)
    ]


def test_mixed_legacy_current_shape_and_legacy_current_claim_block(
    tmp_path: Path,
) -> None:
    mixed = current_registry_fixture()
    mixed["registry_version"] = "module_registry_v1"
    result = validate_module_registry(_write_registry(tmp_path, mixed), ROOT)
    assert result["status"] == "BLOCK"
    assert result["reasons"] == [
        "mixed legacy/current top-level shape is not permitted"
    ]
    legacy = legacy_registry_fixture()
    result = validate_module_registry(_write_registry(tmp_path, legacy), ROOT)
    assert result["current_registry_authority"] is False


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("duplicate-module", "duplicate canonical module ID"),
        ("duplicate-interface", "duplicate current interface identity"),
        ("duplicate-owner", "duplicate current module owner"),
        ("duplicate-dependency", "internal_dependencies repeats"),
        ("duplicate-effect", "repeats effect ID"),
        ("nonreciprocal", "provider/consumer declarations do not close"),
        ("cycle", "module dependency graph must be acyclic"),
        ("overlap", "duplicate path owner"),
        ("prefix-overlap", "duplicate path owner"),
        ("stale-reference", "contract reference SHA256 mismatch"),
        ("missing-reference", "contract reference path is missing"),
        ("inconsistent-reference", "contract reference identity conflicts"),
        ("unknown-effect-target", "unknown target boundary"),
        ("external-provider", "external_dependencies are outside"),
    ],
)
def test_current_dynamic_negative_cases(
    tmp_path: Path,
    mutation: str,
    reason: str,
) -> None:
    registry = current_registry_fixture()
    modules = registry["modules"]
    if mutation == "duplicate-module":
        modules.append(copy.deepcopy(modules[0]))
    elif mutation == "duplicate-interface":
        registry["interfaces"].append(copy.deepcopy(registry["interfaces"][0]))
    elif mutation == "duplicate-owner":
        modules[1]["owner"] = modules[0]["owner"]
    elif mutation == "duplicate-dependency":
        module = next(m for m in modules if m["internal_dependencies"])
        module["internal_dependencies"].append(
            copy.deepcopy(module["internal_dependencies"][0])
        )
    elif mutation == "duplicate-effect":
        module = next(m for m in modules if m["permitted_side_effects"])
        module["permitted_side_effects"].append(
            copy.deepcopy(module["permitted_side_effects"][0])
        )
    elif mutation == "nonreciprocal":
        interface = next(item for item in registry["interfaces"] if item["consumers"])
        interface["consumers"] = []
    elif mutation == "cycle":
        manifest = next(m for m in modules if m["module_id"] == "manifest-validation")
        manifest["internal_dependencies"].append(
            {
                "interface_id": "architecture-registry-api",
                "interface_version": "2.0.0",
            }
        )
        interface = next(
            i
            for i in registry["interfaces"]
            if i["interface_id"] == "architecture-registry-api"
        )
        interface["consumers"].append({"consumer_module_id": "manifest-validation"})
    elif mutation == "overlap":
        modules[1]["boundaries"]["code"].append(
            copy.deepcopy(modules[0]["boundaries"]["code"][0])
        )
    elif mutation == "prefix-overlap":
        modules[0]["boundaries"]["code"].append(
            {
                "boundary_id": "broad-gate-overlap",
                "location_kind": "repository_local",
                "path_kind": "directory_prefix",
                "path": "src/tool_system/gate",
            }
        )
    elif mutation == "stale-reference":
        modules[0]["rollback_boundary"]["sha256"] = "0" * 64
    elif mutation == "missing-reference":
        modules[0]["rollback_boundary"]["repo_relative_path"] = (
            "docs/missing-contract.md"
        )
    elif mutation == "inconsistent-reference":
        modules[0]["rollback_boundary"]["format_identity"] = "different-format-v1"
    elif mutation == "unknown-effect-target":
        effect_module = next(m for m in modules if m["permitted_side_effects"])
        effect_module["permitted_side_effects"][0]["target_boundary_id"] = (
            "missing-boundary"
        )
    else:
        modules[0]["external_dependencies"] = [
            {
                "provider_canonical_repo_id": "invented-provider",
                "provider_repository_commit_sha": "0" * 40,
                "provider_registry_sha256": "0" * 64,
                "interface_id": "invented-api",
                "interface_version": "1.0.0",
            }
        ]
    result = validate_module_registry(_write_registry(tmp_path, registry), ROOT)
    assert result["status"] == "BLOCK"
    assert any(reason in value for value in result["reasons"])


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-existing-target",
        "missing-target-record",
        "weakened-union",
        "identity-collapse",
    ],
)
def test_effect_oracle_rejects_target_and_identity_drift(mutation: str) -> None:
    registry = current_registry_fixture()
    module = next(m for m in registry["modules"] if m["permitted_side_effects"])
    effect = module["permitted_side_effects"][0]
    if mutation == "wrong-existing-target":
        effect["target_boundary_id"] = next(
            boundary["boundary_id"]
            for boundary in module["boundaries"]["code"]
            if boundary["boundary_id"] != effect["target_boundary_id"]
        )
    elif mutation == "missing-target-record":
        module["permitted_side_effects"].pop(0)
    elif mutation == "weakened-union":
        effect["effect_classes"].pop()
    else:
        module = next(
            m
            for m in registry["modules"]
            if any(
                str(item["effect_id"]).startswith("conditional-delegated")
                for item in m["permitted_side_effects"]
            )
        )
        effect = next(
            item
            for item in module["permitted_side_effects"]
            if str(item["effect_id"]).startswith("conditional-delegated")
        )
        effect["effect_id"] = effect["effect_id"].replace(
            "conditional-delegated", "direct"
        )
    with pytest.raises(AssertionError):
        assert_effect_oracle(registry)


def test_registry_validator_has_no_persistence_calls() -> None:
    source = ROOT / "src/tool_system/architecture/module_registry.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    forbidden = {
        "dump",
        "dumps",
        "mkdir",
        "open",
        "safe_dump",
        "touch",
        "write",
        "write_bytes",
        "write_text",
    }
    observed = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert observed.isdisjoint(forbidden)


def test_adapter_reads_one_registry_and_does_not_mutate_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _write_registry(tmp_path, current_registry_fixture())
    calls: list[Path] = []
    real_loader = module_registry.load_yaml_file
    index_path = _git_path("index")
    index_sha = _sha256(index_path)

    def tracked_loader(path: str | Path) -> dict[str, Any]:
        calls.append(Path(path).resolve())
        return real_loader(path)

    monkeypatch.setattr(module_registry, "load_yaml_file", tracked_loader)
    result = validate_module_registry(fixture, ROOT)
    assert result["status"] == "PASS"
    assert calls == [fixture.resolve()]
    assert _sha256(index_path) == index_sha


def test_blueprint_and_ci_keep_local_registry_authority() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    enforcement = blueprint["milestone_module_invariant"]["enforcement"]
    workflow = (ROOT / ".github/workflows/tool-system-ci.yml").read_text(
        encoding="utf-8"
    )
    workflow_lines = {line.strip() for line in workflow.splitlines()}
    guarded_command = (
        "python -m tool_system.cli.validate_module_registry "
        "config/module_registry_v1.yaml --require-current-authority"
    )
    unguarded_command = (
        "python -m tool_system.cli.validate_module_registry "
        "config/module_registry_v1.yaml"
    )

    assert enforcement["module_registry_path"] == "config/module_registry_v1.yaml"
    assert set(enforcement["required_validations"]) >= {
        "module_registry_structure",
        "source_import_edges",
        "contract_reference_hashes",
        "side_effect_target_bindings",
    }
    assert enforcement["runtime_module_enforcement_required"] is True
    assert not any(key.endswith("_implemented") for key in enforcement)
    assert not any("central" in key or ("cut" + "over") in key for key in enforcement)
    assert f"run: {guarded_command}" in workflow_lines
    assert f"run: {unguarded_command}" not in workflow_lines
    assert json.loads(LOCAL_SCHEMA.read_text(encoding="utf-8"))["title"] == (
        "tool-system Durable Module Registry Schema v1"
    )


def test_cli_help_describes_single_local_authority() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tool_system.cli.validate_module_registry",
            "--help",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    help_text = " ".join(result.stdout.split())
    assert "current local registry authority" in help_text
    assert "no projection or second authority" in help_text


def test_cli_require_current_authority_accepts_fixed_registry() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tool_system.cli.validate_module_registry",
            "config/module_registry_v1.yaml",
            "--require-current-authority",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)

    assert output["status"] == "PASS"
    assert output["current_registry_authority"] is True
    assert output["validation_scope"] == "tool_system_current_module_registry"
    assert output["compatibility_adapter"]["applied"] is False
