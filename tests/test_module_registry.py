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
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/module_registry_v1.yaml"
LOCAL_SCHEMA = ROOT / "config/module_registry_schema_v1.json"
MODULE_CONTRACT = ROOT / "docs/tool_system_module_registry_contract_v1.md"
CONTRACT_DIR = ROOT / "docs/modules"
BLUEPRINT = ROOT / "blueprint/tool_system_v0.yaml"

EXPECTED_RAW_SHA256 = (
    "4f28a841ffb928f4a8f6405d4b4c2426bc439c1b0b39e635a8185cbbc2d7759a"
)
EXPECTED_BYTE_LENGTH = 104_561
EXPECTED_SEMANTIC_SHA256 = (
    "b951f8116afbe4ebd3e6116029f9ef215cc82bb5f1ecb0b3c9ec02cfaf265b9c"
)
EXPECTED_MANAGED_PYTHON_FILE_COUNT = 106
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
}
ADDITIONAL_TEST_SELECTORS = {
    "ai_worker_runtime": (
        "tests/test_ai_worker_live_provider.py",
        "tests/test_ai_worker_p15c_benchmark.py",
        "tests/test_ai_worker_p15c_controls.py",
        "tests/test_ai_worker_p15c_entry.py",
        "tests/test_p15c_local_operator_config.py",
    ),
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
        assert contract["identity"]["current_module_id"] == mapping[
            "current_module_id"
        ]
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
    assert len(flattened) == len(set(flattened)) == 114
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
        str(row["current_module_id"]): row
        for row in load_module_identity_mapping(ROOT)
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
            assert capability["capability_state"] == (
                "conditional-delegated-maximum"
            )
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
    assert len(expanded) == 96
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
                "module_version": str(
                    by_current[target]["current_module_version"]
                ),
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
    assert len(registry["modules"]) == len(registry["interfaces"]) == 19
    assert sum(len(module["boundaries"]["code"]) for module in registry["modules"]) == 114
    assert sum(len(module["boundaries"]["tests"]) for module in registry["modules"]) == 25
    assert sum(len(module["permitted_side_effects"]) for module in registry["modules"]) == 45
    assert len(list(_iter_contract_references(registry))) == 197
    assert sum(len(module["external_dependencies"]) for module in registry["modules"]) == 0
    assert len(target_python_owner_by_path()) == 106
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

    assert current["status"] == "PASS"
    assert current["registry_input_mode"] == CURRENT_REGISTRY_INPUT_MODE
    assert current["current_registry_authority"] is True
    assert current["validation_scope"] == "tool_system_current_module_registry"
    assert current["compatibility_adapter"]["applied"] is False
    assert current["contract_reference_count"] == 197
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
        assert [boundary["path"] for boundary in module["boundaries"]["code"]] == code_paths[current]
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
            for provider in contract["dependency_contract"]["direct_provider_module_ids"]
        }
        assert {
            (dependency["interface_id"], dependency["interface_version"])
            for dependency in module["internal_dependencies"]
        } == expected_dependencies
        edge_count += len(expected_dependencies)
        key = (row["aggregate_interface_id"], row["aggregate_interface_version"])
        assert interfaces[key]["provider_module_id"] == canonical
    assert edge_count == 31
    assert_effect_oracle(registry)


def test_manifest_selector_and_unique_registry_authority_path() -> None:
    registry = load_yaml_file(REGISTRY)
    modules = _modules_by_id(registry)
    assert [boundary["path"] for boundary in modules["manifest-validation"]["boundaries"]["tests"]] == [
        "tests/test_task_manifest_policy.py"
    ]
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
        interface = next(
            item for item in registry["interfaces"] if item["consumers"]
        )
        interface["consumers"] = []
    elif mutation == "cycle":
        manifest = next(
            m for m in modules if m["module_id"] == "manifest-validation"
        )
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
        interface["consumers"].append(
            {"consumer_module_id": "manifest-validation"}
        )
    elif mutation == "overlap":
        modules[1]["boundaries"]["code"].append(copy.deepcopy(modules[0]["boundaries"]["code"][0]))
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
        modules[0]["rollback_boundary"]["repo_relative_path"] = "docs/missing-contract.md"
    elif mutation == "inconsistent-reference":
        modules[0]["rollback_boundary"]["format_identity"] = "different-format-v1"
    elif mutation == "unknown-effect-target":
        effect_module = next(m for m in modules if m["permitted_side_effects"])
        effect_module["permitted_side_effects"][0]["target_boundary_id"] = "missing-boundary"
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
    workflow = (ROOT / ".github/workflows/tool-system-ci.yml").read_text(encoding="utf-8")
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
    assert not any(
        "central" in key or ("cut" + "over") in key for key in enforcement
    )
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
