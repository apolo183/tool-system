from __future__ import annotations

import ast
import copy
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Iterator

import pytest
import yaml

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "docs" / "modules"
S0_CONTRACT = ROOT / "docs" / "tool_system_module_registry_adoption_contract_v1.md"
REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
SOURCE_ROOT = ROOT / "src"

BLOCK_NAME = "MODULE-COMPOUND-CONTRACT"
FORMAT_IDENTITY = "tool-system-module-compound-contract-v1"
SCHEMA_IDENTITY = "tool-system-module-compound-contract-schema-v1"
EFFECT_TAXONOMY_SOURCE = (
    "finance-governance@04ca9d558f59dae17603d7976727aa29782253aa:"
    "config/module_registry_schema_v1.json"
)
CENTRAL_EFFECT_CLASSES = {
    "repository_write",
    "data_write",
    "generated_artifact_write",
    "git_write",
    "database_write",
    "network_write",
    "external_system_write",
    "production_operation",
}
EFFECT_SOURCE_SIGNALS = {
    "repository_write": (
        "write_jsonl_record",
        "write_text",
        "write_bytes",
        ".open(",
    ),
    "data_write": ("sqlite3", "INSERT INTO", "UPDATE "),
    "generated_artifact_write": (
        "write_jsonl_record",
        "write_text",
        "write_bytes",
        ".open(",
    ),
    "git_write": ("\"pr\"", "\"merge\"", "execute_action_plan"),
    "database_write": ("sqlite3",),
    "network_write": ("run_gh", "subprocess.run"),
    "external_system_write": ("run_gh", "execute_action_plan"),
    "production_operation": ("production",),
}
TOKEN_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
PLACEHOLDERS = {"UNKNOWN", "TBD", "TODO"}
NON_CLAIM_KEYS = {
    "registry_membership",
    "central_registry_adopted",
    "central_schema_compliance_claimed",
    "central_gate_pass_claimed",
    "governance_activated",
    "provider_execution_authorized",
    "target_repo_mutation_authorized",
    "cleanup_execution_authorized",
    "production_operation_authorized",
    "governance_cutover_completed",
}
REVALIDATION_KEYS = {
    "module_implementation",
    "public_provider_boundaries",
    "public_consumer_boundaries",
    "affected_downstream_dependency_closure",
    "unrelated_modules_reimplementation_required",
}
REQUIRED_CONTRACT_KEYS = {
    "format_identity",
    "schema_identity",
    "contract_path",
    "identity",
    "role",
    "natural_owner_evidence_paths",
    "dependency_contract",
    "input_contract",
    "output_contract",
    "error_contract",
    "side_effect_contract",
    "compatibility_policy",
    "rollback_contract",
    "replacement_contract",
    "replacement_revalidation_boundary",
    "local_boundaries",
    "external_root_contracts",
    "external_system_contracts",
    "non_claims",
    "authority_boundary",
}


class ModuleContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ModuleContractError(message)


def _yaml_block(path: Path, name: str = BLOCK_NAME) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = f"<!-- {name}:BEGIN -->\n~~~yaml\n"
    end = f"\n~~~\n<!-- {name}:END -->"
    _require(text.count(start) == 1, f"{path}: one {name} start marker required")
    _require(text.count(end) == 1, f"{path}: one {name} end marker required")
    body = text.split(start, 1)[1].split(end, 1)[0]
    try:
        loaded = yaml.safe_load(body)
    except yaml.YAMLError as exc:
        raise ModuleContractError(f"{path}: invalid YAML: {exc}") from exc
    _require(
        isinstance(loaded, dict) and set(loaded) == {"module_compound_contract"},
        f"{path}: exact module_compound_contract wrapper required",
    )
    contract = loaded["module_compound_contract"]
    _require(isinstance(contract, dict), f"{path}: contract must be a mapping")
    return contract


def _s0_block(name: str) -> dict[str, Any]:
    text = S0_CONTRACT.read_text(encoding="utf-8")
    start = f"<!-- {name}:BEGIN -->\n~~~yaml\n"
    end = f"\n~~~\n<!-- {name}:END -->"
    _require(text.count(start) == 1, f"{name}: one start marker required")
    _require(text.count(end) == 1, f"{name}: one end marker required")
    loaded = yaml.safe_load(text.split(start, 1)[1].split(end, 1)[0])
    _require(isinstance(loaded, dict), f"{name}: mapping required")
    return loaded


def _mapping_contract() -> dict[str, Any]:
    value = _s0_block("S0-IDENTITY-MAPPING").get("mapping_contract")
    _require(isinstance(value, dict), "S0 mapping_contract is required")
    return value


def _mappings_by_current_id() -> dict[str, dict[str, Any]]:
    rows = _mapping_contract().get("mappings")
    _require(isinstance(rows, list), "S0 mappings must be a list")
    _require(len(rows) == 14, "S0 mappings must contain fourteen rows")
    result = {
        str(row["current_module_id"]): row
        for row in rows
        if isinstance(row, dict)
    }
    _require(len(result) == 14, "S0 current module IDs must be unique")
    return result


def _s0_consumers() -> dict[str, list[str]]:
    value = _s0_block("S0-STATIC-DAG").get("static_import_dag")
    _require(isinstance(value, dict), "S0 static_import_dag is required")
    providers = value.get("providers")
    _require(isinstance(providers, dict), "S0 providers must be a mapping")
    return {
        str(module_id): list(consumers)
        for module_id, consumers in providers.items()
    }


def _direct_providers(consumers: dict[str, list[str]]) -> dict[str, list[str]]:
    providers = {module_id: [] for module_id in consumers}
    for provider, direct_consumers in consumers.items():
        for consumer in direct_consumers:
            _require(consumer in providers, f"S0 DAG has unknown consumer: {consumer}")
            providers[consumer].append(provider)
    return {
        module_id: sorted(module_providers)
        for module_id, module_providers in providers.items()
    }


def _registry_by_id() -> dict[str, dict[str, Any]]:
    modules = load_yaml_file(REGISTRY)["modules"]
    return {module["module_id"]: module for module in modules}


def _tracked_paths() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return {
        path
        for path in result.stdout.decode("utf-8").split("\0")
        if path
    }


def _expanded_owner_paths(
    registry: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    tracked = _tracked_paths()
    owners: dict[str, str] = {}
    expanded: dict[str, list[str]] = {}
    for module_id, module in registry.items():
        paths: set[str] = set()
        for pattern in module["natural_owner_paths"]:
            paths.update(
                path.relative_to(ROOT).as_posix()
                for path in ROOT.glob(pattern)
                if path.is_file()
            )
        _require(paths, f"{module_id}: natural owners must resolve")
        for path in paths:
            _require(path in tracked, f"{module_id}: owner path must be tracked: {path}")
            _require(path not in owners, f"duplicate natural owner: {path}")
            owners[path] = module_id
        expanded[module_id] = sorted(paths)
    return expanded


def _iter_values(value: object) -> Iterator[object]:
    yield value
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _iter_values(key)
            yield from _iter_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_values(nested)


def _require_non_placeholder_values(contract: dict[str, Any], module_id: str) -> None:
    for value in _iter_values(contract):
        if isinstance(value, str):
            _require(bool(value.strip()), f"{module_id}: empty string is forbidden")
            _require(
                value.strip().upper() not in PLACEHOLDERS,
                f"{module_id}: placeholder value is forbidden",
            )


def _source_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _validate_external_roots(
    contract: dict[str, Any],
    module_id: str,
    owner_paths: set[str],
) -> None:
    value = contract["external_root_contracts"]
    _require(
        isinstance(value, dict) and set(value) == {"declaration", "roots"},
        f"{module_id}: external_root_contracts shape drifted",
    )
    declaration = value["declaration"]
    roots = value["roots"]
    _require(
        declaration in {"declared", "explicit-none"},
        f"{module_id}: invalid external-root declaration",
    )
    _require(isinstance(roots, list), f"{module_id}: roots must be a list")
    if declaration == "explicit-none":
        _require(roots == [], f"{module_id}: explicit-none roots must be empty")
        python_text = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in owner_paths
            if path.endswith(".py")
        )
        path_signals = (
            "from pathlib import",
            "import pathlib",
            "sqlite3",
            "tempfile",
            "audit_path",
            "output_path",
            "workspace_root",
            "repo_root",
            "state_path",
        )
        _require(
            not any(signal in python_text for signal in path_signals),
            f"{module_id}: explicit-none conflicts with source path evidence",
        )
        return

    _require(bool(roots), f"{module_id}: declared external roots cannot be empty")
    for root in roots:
        _require(
            isinstance(root, dict)
            and set(root)
            == {
                "root_id",
                "access",
                "evidence_paths",
                "evidence_symbols",
                "boundary_parameters",
                "constraint",
            },
            f"{module_id}: external root shape drifted",
        )
        _require(
            root["access"] in {"read-only", "write-only", "read-write"},
            f"{module_id}: external root access is invalid",
        )
        evidence_paths = root["evidence_paths"]
        _require(
            isinstance(evidence_paths, list) and bool(evidence_paths),
            f"{module_id}: external root evidence paths are required",
        )
        _require(
            set(evidence_paths) <= owner_paths,
            f"{module_id}: external root evidence must be module-owned",
        )
        symbols = root["evidence_symbols"]
        _require(
            isinstance(symbols, list) and bool(symbols),
            f"{module_id}: external root evidence symbols are required",
        )
        available_symbols: set[str] = set()
        source_text = ""
        for relative in evidence_paths:
            path = ROOT / relative
            _require(path.suffix == ".py", f"{module_id}: root evidence must be Python")
            available_symbols.update(_source_symbols(path))
            source_text += path.read_text(encoding="utf-8")
        _require(
            set(symbols) <= available_symbols,
            f"{module_id}: external root evidence symbol is absent",
        )
        parameters = root["boundary_parameters"]
        _require(
            isinstance(parameters, list) and bool(parameters),
            f"{module_id}: external root boundary parameters are required",
        )
        _require(
            all(str(parameter) in source_text for parameter in parameters),
            f"{module_id}: external root parameter lacks source evidence",
        )


def _validate_contract(
    contract: dict[str, Any],
    path: Path,
    mapping: dict[str, Any],
    registry_module: dict[str, Any],
    direct_consumers: list[str],
    direct_providers: list[str],
    owner_paths: list[str],
) -> None:
    module_id = str(mapping["current_module_id"])
    canonical_id = str(mapping["canonical_module_id"])
    expected_path = f"docs/modules/{canonical_id}-contract-v1.md"

    _require(set(contract) == REQUIRED_CONTRACT_KEYS, f"{module_id}: contract keys drifted")
    _require(contract["format_identity"] == FORMAT_IDENTITY, f"{module_id}: format drifted")
    _require(contract["schema_identity"] == SCHEMA_IDENTITY, f"{module_id}: schema drifted")
    _require(
        TOKEN_RE.fullmatch(str(contract["format_identity"])) is not None,
        f"{module_id}: invalid format identity",
    )
    _require(
        TOKEN_RE.fullmatch(str(contract["schema_identity"])) is not None,
        f"{module_id}: invalid schema identity",
    )
    _require(contract["contract_path"] == expected_path, f"{module_id}: path drifted")
    _require(path == ROOT / expected_path, f"{module_id}: file path drifted")

    identity = contract["identity"]
    _require(
        isinstance(identity, dict)
        and set(identity)
        == {
            "canonical_module_id",
            "current_module_id",
            "module_version",
            "aggregate_interface",
            "mapping_owner",
            "rollback_identity",
            "python_import_identities",
        },
        f"{module_id}: identity shape drifted",
    )
    _require(identity["canonical_module_id"] == canonical_id, f"{module_id}: canonical ID drifted")
    _require(identity["current_module_id"] == module_id, f"{module_id}: current ID drifted")
    _require(
        identity["module_version"] == mapping["current_module_version"],
        f"{module_id}: module version drifted",
    )
    _require(TOKEN_RE.fullmatch(canonical_id) is not None, f"{module_id}: invalid canonical ID")
    _require(
        SEMVER_RE.fullmatch(str(identity["module_version"])) is not None,
        f"{module_id}: invalid module version",
    )
    aggregate = identity["aggregate_interface"]
    _require(
        aggregate
        == {
            "interface_id": mapping["aggregate_interface_id"],
            "interface_version": mapping["aggregate_interface_version"],
        },
        f"{module_id}: aggregate interface drifted",
    )
    _require(
        TOKEN_RE.fullmatch(str(aggregate["interface_id"])) is not None,
        f"{module_id}: invalid interface ID",
    )
    _require(
        SEMVER_RE.fullmatch(str(aggregate["interface_version"])) is not None,
        f"{module_id}: invalid interface version",
    )
    mapping_owner = identity["mapping_owner"]
    _require(
        mapping_owner
        == {
            "contract_path": S0_CONTRACT.relative_to(ROOT).as_posix(),
            "implementation_path": _mapping_contract()["identity_mapping_owner"],
        },
        f"{module_id}: S0 mapping owner drifted",
    )
    _require(
        identity["rollback_identity"] == mapping["rollback_identity"],
        f"{module_id}: rollback identity drifted",
    )
    _require(
        identity["python_import_identities"] == mapping["python_import_identities"],
        f"{module_id}: Python ownership evidence drifted",
    )

    role = contract["role"]
    _require(
        isinstance(role, dict) and set(role) == {"summary", "responsibility_boundary"},
        f"{module_id}: role shape drifted",
    )
    _require(
        role["summary"] == registry_module["single_responsibility"],
        f"{module_id}: registered responsibility drifted",
    )
    _require(
        contract["natural_owner_evidence_paths"] == owner_paths,
        f"{module_id}: natural-owner evidence drifted",
    )

    dependencies = contract["dependency_contract"]
    _require(
        dependencies
        == {
            "basis": "s0-static-python-import-dag",
            "direction": "provider-to-direct-consumer",
            "direct_provider_module_ids": direct_providers,
            "direct_consumer_module_ids": direct_consumers,
        },
        f"{module_id}: dependency DAG drifted",
    )

    for section, registry_key, value_key in (
        ("input_contract", "input_contract", "registered_inputs"),
        ("output_contract", "output_contract", "registered_outputs"),
        ("error_contract", "error_semantics", "registered_error_semantics"),
    ):
        value = contract[section]
        _require(
            isinstance(value, dict) and set(value) == {value_key, "boundary"},
            f"{module_id}: {section} shape drifted",
        )
        _require(
            value[value_key] == registry_module[registry_key],
            f"{module_id}: {section} drifted from current registry",
        )
        _require(
            isinstance(value["boundary"], str) and bool(value["boundary"].strip()),
            f"{module_id}: {section} boundary is required",
        )

    effects = contract["side_effect_contract"]
    _require(
        isinstance(effects, dict)
        and set(effects)
        == {
            "taxonomy_source",
            "effect_classes",
            "direct_effects",
            "delegated_effects",
            "classification_grants_authority",
        },
        f"{module_id}: side-effect shape drifted",
    )
    _require(effects["taxonomy_source"] == EFFECT_TAXONOMY_SOURCE, f"{module_id}: taxonomy drifted")
    effect_classes = effects["effect_classes"]
    _require(isinstance(effect_classes, list), f"{module_id}: effect classes must be a list")
    _require(len(effect_classes) == len(set(effect_classes)), f"{module_id}: duplicate effect class")
    _require(
        set(effect_classes) <= CENTRAL_EFFECT_CLASSES,
        f"{module_id}: non-central effect class",
    )
    direct_effects = effects["direct_effects"]
    _require(isinstance(direct_effects, list), f"{module_id}: direct effects must be a list")
    observed_effects: set[str] = set()
    for effect in direct_effects:
        _require(
            isinstance(effect, dict)
            and set(effect) == {"effect_class", "evidence_paths", "boundary"},
            f"{module_id}: direct effect shape drifted",
        )
        observed_effects.add(effect["effect_class"])
        _require(
            isinstance(effect["evidence_paths"], list)
            and bool(effect["evidence_paths"])
            and set(effect["evidence_paths"]) <= set(owner_paths),
            f"{module_id}: effect evidence must be module-owned",
        )
        source_text = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in effect["evidence_paths"]
        )
        _require(
            any(
                signal in source_text
                for signal in EFFECT_SOURCE_SIGNALS[effect["effect_class"]]
            ),
            f"{module_id}: effect class lacks source evidence",
        )
    _require(observed_effects == set(effect_classes), f"{module_id}: effect evidence incomplete")
    _require(
        isinstance(effects["delegated_effects"], list),
        f"{module_id}: delegated effects must be a list",
    )
    _require(
        effects["classification_grants_authority"] is False,
        f"{module_id}: effect classification cannot grant authority",
    )

    compatibility = contract["compatibility_policy"]
    _require(
        isinstance(compatibility, dict)
        and set(compatibility)
        == {"interface_compatible_replacement", "interface_incompatible_change"},
        f"{module_id}: compatibility policy shape drifted",
    )
    rollback = contract["rollback_contract"]
    _require(
        isinstance(rollback, dict)
        and set(rollback) == {"rollback_identity", "method"}
        and rollback["rollback_identity"] == mapping["rollback_identity"],
        f"{module_id}: rollback contract drifted",
    )
    replacement = contract["replacement_contract"]
    _require(
        isinstance(replacement, dict)
        and set(replacement) == {"activation_rule", "parallel_active_mainlines_allowed"}
        and replacement["parallel_active_mainlines_allowed"] is False,
        f"{module_id}: parallel active mainlines are forbidden",
    )
    revalidation = contract["replacement_revalidation_boundary"]
    _require(set(revalidation) == REVALIDATION_KEYS, f"{module_id}: revalidation shape drifted")
    _require(
        all(revalidation[key] is True for key in REVALIDATION_KEYS - {"unrelated_modules_reimplementation_required"}),
        f"{module_id}: required revalidation boundary is missing",
    )
    _require(
        revalidation["unrelated_modules_reimplementation_required"] is False,
        f"{module_id}: unrelated modules cannot require reimplementation",
    )

    boundaries = contract["local_boundaries"]
    _require(
        isinstance(boundaries, dict)
        and set(boundaries) == {"repository", "data", "artifact", "database"},
        f"{module_id}: local boundary shape drifted",
    )
    for boundary in boundaries.values():
        _require(
            isinstance(boundary, dict) and set(boundary) == {"mode", "contract"},
            f"{module_id}: local boundary must declare mode and contract",
        )

    _validate_external_roots(contract, module_id, set(owner_paths))
    systems = contract["external_system_contracts"]
    _require(
        isinstance(systems, dict) and set(systems) == {"declaration", "systems"},
        f"{module_id}: external-system shape drifted",
    )
    _require(
        systems["declaration"] in {"declared", "explicit-none"},
        f"{module_id}: invalid external-system declaration",
    )
    _require(isinstance(systems["systems"], list), f"{module_id}: systems must be a list")
    _require(
        (systems["declaration"] == "declared") == bool(systems["systems"]),
        f"{module_id}: external-system declaration mismatch",
    )
    for system in systems["systems"]:
        _require(
            isinstance(system, dict)
            and set(system) == {"system_id", "mode", "evidence_paths", "boundary"},
            f"{module_id}: external-system contract shape drifted",
        )
        _require(
            set(system["evidence_paths"]) <= set(owner_paths),
            f"{module_id}: external-system evidence must be module-owned",
        )

    non_claims = contract["non_claims"]
    _require(set(non_claims) == NON_CLAIM_KEYS, f"{module_id}: non-claims shape drifted")
    _require(all(value is False for value in non_claims.values()), f"{module_id}: positive claim")
    authority = contract["authority_boundary"]
    _require(
        authority
        == {
            "execution_authority": False,
            "governance_authority": False,
            "evidence_role": "s3-contract-reference-input",
            "next_stage": "separately-authorized-s4",
        },
        f"{module_id}: authority boundary drifted",
    )
    _require_non_placeholder_values(contract, module_id)
    forbidden_self_hash_keys = {"git_blob_sha", "file_sha256", "self_sha256"}
    _require(
        not forbidden_self_hash_keys.intersection(
            value for value in _iter_values(contract) if isinstance(value, str)
        ),
        f"{module_id}: self-referential hash field is forbidden",
    )


def _validate_contract_set(
    contracts: list[dict[str, Any]],
    digests: list[str],
) -> None:
    _require(len(contracts) == 14, "exactly fourteen module contracts are required")
    for key_path in (
        ("contract_path",),
        ("identity", "current_module_id"),
        ("identity", "canonical_module_id"),
        ("identity", "aggregate_interface", "interface_id"),
    ):
        values: list[object] = []
        for contract in contracts:
            value: object = contract
            for key in key_path:
                _require(isinstance(value, dict), "contract identity shape is invalid")
                value = value[key]
            values.append(value)
        _require(len(values) == len(set(values)), f"duplicate contract owner: {key_path}")
    _require(len(digests) == len(set(digests)), "shared cross-module contract hash")


def _validated_contracts() -> tuple[list[dict[str, Any]], list[str]]:
    mappings = _mappings_by_current_id()
    registry = _registry_by_id()
    consumers = _s0_consumers()
    providers = _direct_providers(consumers)
    owner_paths = _expanded_owner_paths(registry)
    expected_paths = {
        ROOT / "docs" / "modules" / f"{mapping['canonical_module_id']}-contract-v1.md"
        for mapping in mappings.values()
    }
    actual_paths = set(CONTRACT_DIR.glob("*.md"))
    _require(actual_paths == expected_paths, "contract directory must contain exactly fourteen owners")

    contracts: list[dict[str, Any]] = []
    digests: list[str] = []
    for module_id, mapping in mappings.items():
        path = ROOT / "docs" / "modules" / f"{mapping['canonical_module_id']}-contract-v1.md"
        contract = _yaml_block(path)
        _validate_contract(
            contract,
            path,
            mapping,
            registry[module_id],
            consumers[module_id],
            providers[module_id],
            owner_paths[module_id],
        )
        contracts.append(contract)
        digests.append(hashlib.sha256(path.read_bytes()).hexdigest())
    _validate_contract_set(contracts, digests)
    return contracts, digests


def test_all_module_contracts_match_s0_registry_and_real_owner_evidence() -> None:
    contracts, digests = _validated_contracts()

    assert len(contracts) == 14
    assert len(digests) == len(set(digests)) == 14
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing-field", "contract keys drifted"),
        ("wrong-identity", "canonical ID drifted"),
        ("wrong-owner", "natural-owner evidence drifted"),
        ("wrong-dag", "dependency DAG drifted"),
        ("illegal-effect", "non-central effect class"),
        ("placeholder", "placeholder value is forbidden"),
    ],
)
def test_invalid_compound_contracts_fail_closed(
    mutation: str,
    message: str,
) -> None:
    mappings = _mappings_by_current_id()
    registry = _registry_by_id()
    consumers = _s0_consumers()
    providers = _direct_providers(consumers)
    owner_paths = _expanded_owner_paths(registry)
    module_id = "architecture_registry"
    mapping = mappings[module_id]
    path = CONTRACT_DIR / f"{mapping['canonical_module_id']}-contract-v1.md"
    contract = copy.deepcopy(_yaml_block(path))

    if mutation == "missing-field":
        contract.pop("error_contract")
    elif mutation == "wrong-identity":
        contract["identity"]["canonical_module_id"] = "wrong-module"
    elif mutation == "wrong-owner":
        contract["natural_owner_evidence_paths"] = owner_paths["manifest_validation"]
    elif mutation == "wrong-dag":
        contract["dependency_contract"]["direct_consumer_module_ids"] = ["cli_frontend"]
    elif mutation == "illegal-effect":
        contract["side_effect_contract"]["effect_classes"] = ["local_process"]
    else:
        contract["input_contract"]["boundary"] = "TBD"

    with pytest.raises(ModuleContractError, match=message):
        _validate_contract(
            contract,
            path,
            mapping,
            registry[module_id],
            consumers[module_id],
            providers[module_id],
            owner_paths[module_id],
        )


def test_shared_contract_owner_or_hash_fails_closed() -> None:
    contracts, digests = _validated_contracts()

    duplicate_owner = copy.deepcopy(contracts)
    duplicate_owner[1]["contract_path"] = duplicate_owner[0]["contract_path"]
    with pytest.raises(ModuleContractError, match="duplicate contract owner"):
        _validate_contract_set(duplicate_owner, digests)

    duplicate_hashes = list(digests)
    duplicate_hashes[1] = duplicate_hashes[0]
    with pytest.raises(ModuleContractError, match="shared cross-module contract hash"):
        _validate_contract_set(contracts, duplicate_hashes)
