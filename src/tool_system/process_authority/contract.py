from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.runner.active_gate_resolver import paths_match


FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

AUTHORITY_FIELDS = {
    "contract_version",
    "authority_id",
    "blueprint_objective_ref",
    "module",
    "current_task_input",
    "legacy_compatibility",
    "canonical_replay",
    "authorization_boundary",
}
MODULE_FIELDS = {
    "module_id",
    "module_version",
    "public_interface_id",
    "public_interface_version",
}
CURRENT_INPUT_FIELDS = {
    "mode",
    "task_manifest_required",
    "change_plan_required",
    "pair_binding_required",
    "implicit_repository_index_allowed",
}
LEGACY_FIELDS = {
    "index_path",
    "authority",
    "explicit_opt_in_only",
    "replay_only",
    "execution_allowed",
    "cleanup_authorized",
}
CANONICAL_REPLAY_FIELDS = {
    "snapshot_path",
    "authority",
    "required_for_legacy_replay",
}
AUTHORIZATION_FIELDS = {
    "repository",
    "target_repo_mutation",
    "production_deployment",
    "live_provider_execution",
    "cleanup_execution",
}
REPLAY_FIELDS = {
    "snapshot_contract_version",
    "snapshot_id",
    "blueprint_objective_ref",
    "source_repository",
    "source_head_sha",
    "source_tree_sha",
    "source_index_path",
    "source_index_sha256",
    "pair_count",
    "pair_set_sha256",
    "capture_algorithm",
    "authority",
    "replay_only",
    "execute",
    "writes_target_repo",
    "executes_target_repo_mutation",
    "production_deployment",
    "cleanup_execution",
}


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("process authority mapping keys must be strings")
        if key in mapping:
            raise ValueError(f"duplicate process authority key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_process_authority(path: Path) -> dict[str, Any]:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(value, dict):
        raise ValueError("process authority top level must be a mapping")
    return value


def _exact_mapping(
    value: object,
    fields: set[str],
    label: str,
    reasons: list[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        reasons.append(f"{label} must be a mapping")
        return {}
    if set(value) != fields:
        reasons.append(f"{label} must contain exactly {sorted(fields)}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_entries(index: dict[str, Any], field: str) -> list[str]:
    value = index.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    if not all(isinstance(entry, str) and entry.strip() for entry in value):
        raise ValueError(f"{field} entries must be non-empty strings")
    entries = [str(entry) for entry in value]
    for position, entry in enumerate(entries):
        if any(paths_match(entry, previous) for previous in entries[:position]):
            raise ValueError(f"duplicate {field} path: {entry}")
    return entries


def _safe_source_path(root: Path, raw_path: str, label: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes replay source root: {raw_path}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} must not use a symlink: {raw_path}")
    if candidate.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"{label} must be a YAML file: {raw_path}")
    if not candidate.is_file():
        raise ValueError(f"{label} is missing or not a regular file: {raw_path}")
    return candidate


def _snapshot_pairings(
    index_path: Path,
    root: Path,
) -> list[tuple[str, Path, str, Path]]:
    index = load_yaml_file(index_path)
    manifest_entries = _source_entries(index, "task_manifests")
    plan_entries = _source_entries(index, "change_plans")
    manifests = {
        entry: _safe_source_path(root, entry, "task manifest")
        for entry in manifest_entries
    }
    plans_by_manifest: dict[str, list[tuple[str, Path]]] = {
        entry: [] for entry in manifest_entries
    }
    for plan_entry in plan_entries:
        plan_path = _safe_source_path(root, plan_entry, "change plan")
        plan = load_yaml_file(plan_path)
        manifest_ref = plan.get("task_manifest")
        if not isinstance(manifest_ref, str) or not manifest_ref.strip():
            raise ValueError(
                f"change plan task_manifest must be a non-empty string: {plan_entry}"
            )
        matching = [
            entry
            for entry in manifest_entries
            if paths_match(manifest_ref, entry)
        ]
        if len(matching) != 1:
            raise ValueError(
                "change plan must reference exactly one registered task manifest: "
                f"{plan_entry} -> {manifest_ref}"
            )
        plans_by_manifest[matching[0]].append((plan_entry, plan_path))
    pairings: list[tuple[str, Path, str, Path]] = []
    for manifest_entry in manifest_entries:
        plans = plans_by_manifest[manifest_entry]
        if len(plans) != 1:
            raise ValueError(
                "registered task manifest must have exactly one change plan: "
                f"{manifest_entry}"
            )
        plan_entry, plan_path = plans[0]
        pairings.append(
            (manifest_entry, manifests[manifest_entry], plan_entry, plan_path)
        )
    return pairings


def build_replay_snapshot(
    index_path: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    index = Path(index_path)
    root = Path(repo_root).resolve() if repo_root is not None else index.resolve().parents[1]
    index = _safe_source_path(root, str(index), "replay source index")
    pairings = _snapshot_pairings(index, root)
    digest = hashlib.sha256()
    for manifest_entry, manifest_path, plan_entry, plan_path in sorted(
        pairings,
        key=lambda pair: Path(pair[0]).as_posix(),
    ):
        values = (
            Path(manifest_entry).as_posix(),
            _sha256(manifest_path),
            Path(plan_entry).as_posix(),
            _sha256(plan_path),
        )
        for value in values:
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
    return {
        "source_index_sha256": _sha256(index),
        "pair_count": len(pairings),
        "pair_set_sha256": digest.hexdigest(),
    }


def validate_replay_snapshot(
    snapshot_path: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    path = Path(snapshot_path)
    root = Path(repo_root).resolve() if repo_root is not None else path.resolve().parents[1]
    if path.is_symlink():
        return {
            "status": "BLOCK",
            "snapshot_path": str(path),
            "reasons": ["replay snapshot must not be a symlink"],
        }
    try:
        snapshot = load_yaml_file(path)
    except (OSError, ValueError) as exc:
        return {
            "status": "BLOCK",
            "snapshot_path": str(path),
            "reasons": [f"unable to read replay snapshot: {exc}"],
        }

    reasons: list[str] = []
    if set(snapshot) != REPLAY_FIELDS:
        reasons.append("replay snapshot must contain exactly the registered fields")
    expected_values = {
        "snapshot_contract_version": "replay_snapshot_v1",
        "snapshot_id": "tool_system_legacy_pair_replay",
        "blueprint_objective_ref": "product_objective",
        "source_repository": "apolo183/tool-system",
        "capture_algorithm": "sha256_sorted_manifest_hash_plan_hash_v1",
        "authority": False,
        "replay_only": True,
        "execute": False,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "cleanup_execution": False,
    }
    for field, expected in expected_values.items():
        if snapshot.get(field) != expected:
            reasons.append(f"{field} must be {expected!r}")
    for field in ("source_head_sha", "source_tree_sha"):
        value = snapshot.get(field)
        if not isinstance(value, str) or FULL_SHA_RE.fullmatch(value) is None:
            reasons.append(f"{field} must be a full lowercase SHA")
    for field in ("source_index_sha256", "pair_set_sha256"):
        value = snapshot.get(field)
        if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
            reasons.append(f"{field} must be a lowercase SHA256")
    source_index = snapshot.get("source_index_path")
    if source_index != "examples/active_gates.yaml":
        reasons.append("source_index_path must be examples/active_gates.yaml")
    else:
        try:
            current = build_replay_snapshot(root / source_index, root)
        except (OSError, ValueError) as exc:
            reasons.append(f"unable to reconstruct replay snapshot: {exc}")
        else:
            for field, value in current.items():
                if snapshot.get(field) != value:
                    reasons.append(f"replay snapshot {field} does not match source inputs")

    return {
        "status": "PASS" if not reasons else "BLOCK",
        "snapshot_path": str(path),
        "pair_count": snapshot.get("pair_count"),
        "authority": False,
        "replay_only": True,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }


def validate_process_authority(
    authority_path: str | Path = "config/process_authority_v1.yaml",
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    path = Path(authority_path)
    root = Path(repo_root).resolve() if repo_root is not None else path.resolve().parents[1]
    if path.is_symlink():
        return {
            "status": "BLOCK",
            "authority_path": str(path),
            "reasons": ["process authority must not be a symlink"],
        }
    try:
        authority = _load_process_authority(path)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        return {
            "status": "BLOCK",
            "authority_path": str(path),
            "reasons": [f"unable to read process authority: {exc}"],
        }

    reasons: list[str] = []
    if set(authority) != AUTHORITY_FIELDS:
        reasons.append("process authority must contain exactly the registered fields")
    if authority.get("contract_version") != "process_authority_v1":
        reasons.append("contract_version must be process_authority_v1")
    if authority.get("authority_id") != "tool_system_explicit_task_pair_authority":
        reasons.append("authority_id must identify explicit task-pair authority")
    if authority.get("blueprint_objective_ref") != "product_objective":
        reasons.append("blueprint_objective_ref must be product_objective")

    module = _exact_mapping(authority.get("module"), MODULE_FIELDS, "module", reasons)
    if module != {
        "module_id": "process-authority",
        "module_version": "2.0.0",
        "public_interface_id": "process-authority-api",
        "public_interface_version": "2.0.0",
    }:
        reasons.append(
            "module must identify process-authority 2.0.0 interface "
            "process-authority-api 2.0.0"
        )

    current = _exact_mapping(
        authority.get("current_task_input"),
        CURRENT_INPUT_FIELDS,
        "current_task_input",
        reasons,
    )
    expected_current = {
        "mode": "explicit_manifest_change_plan_pair",
        "task_manifest_required": True,
        "change_plan_required": True,
        "pair_binding_required": True,
        "implicit_repository_index_allowed": False,
    }
    if current != expected_current:
        reasons.append("current_task_input must require one explicit bound pair")

    legacy = _exact_mapping(
        authority.get("legacy_compatibility"),
        LEGACY_FIELDS,
        "legacy_compatibility",
        reasons,
    )
    expected_legacy = {
        "index_path": "examples/active_gates.yaml",
        "authority": False,
        "explicit_opt_in_only": True,
        "replay_only": True,
        "execution_allowed": False,
        "cleanup_authorized": False,
    }
    if legacy != expected_legacy:
        reasons.append("legacy_compatibility must remain replay-only and non-authoritative")

    replay = _exact_mapping(
        authority.get("canonical_replay"),
        CANONICAL_REPLAY_FIELDS,
        "canonical_replay",
        reasons,
    )
    expected_replay = {
        "snapshot_path": "config/replay_snapshot_v1.yaml",
        "authority": False,
        "required_for_legacy_replay": True,
    }
    if replay != expected_replay:
        reasons.append("canonical_replay must require the non-authoritative v1 snapshot")

    boundary = _exact_mapping(
        authority.get("authorization_boundary"),
        AUTHORIZATION_FIELDS,
        "authorization_boundary",
        reasons,
    )
    expected_boundary = {
        "repository": "tool-system",
        "target_repo_mutation": False,
        "production_deployment": False,
        "live_provider_execution": False,
        "cleanup_execution": False,
    }
    if boundary != expected_boundary:
        reasons.append("authorization_boundary must preserve all registered denials")

    replay_result = validate_replay_snapshot(
        root / "config" / "replay_snapshot_v1.yaml",
        root,
    )
    reasons.extend(str(reason) for reason in replay_result.get("reasons", []))
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "authority_path": str(path),
        "module_id": module.get("module_id"),
        "module_version": module.get("module_version"),
        "public_interface_id": module.get("public_interface_id"),
        "public_interface_version": module.get("public_interface_version"),
        "current_task_input_mode": current.get("mode"),
        "implicit_repository_index_allowed": False,
        "legacy_authority": False,
        "replay_result": replay_result,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "production_deployment": False,
        "cleanup_execution": False,
        "reasons": reasons,
    }


def validate_explicit_task_pair(
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
) -> dict[str, object]:
    manifest_path = Path(task_manifest_path)
    plan_path = Path(change_plan_path)
    reasons: list[str] = []
    if manifest_path.is_symlink():
        reasons.append(f"task manifest must not be a symlink: {manifest_path}")
    elif not manifest_path.is_file():
        reasons.append(f"task manifest is missing: {manifest_path}")
    if plan_path.is_symlink():
        reasons.append(f"change plan must not be a symlink: {plan_path}")
        change_plan = {}
    else:
        try:
            change_plan = load_yaml_file(plan_path)
        except (OSError, ValueError) as exc:
            reasons.append(f"unable to read change plan: {exc}")
            change_plan = {}
    manifest_ref = change_plan.get("task_manifest")
    if not isinstance(manifest_ref, str) or not manifest_ref.strip():
        reasons.append("change plan task_manifest must be a non-empty string")
    elif not paths_match(manifest_path, manifest_ref):
        reasons.append(
            "explicit change plan is bound to a different task manifest: "
            f"{plan_path} -> {manifest_ref}"
        )
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "task_manifest_path": str(manifest_path),
        "change_plan_path": str(plan_path),
        "binding_mode": "explicit_manifest_change_plan_pair",
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
