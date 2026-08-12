from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from tool_system.blueprint_compiler import (
    BlueprintCompilerError,
    BlueprintCompilerLimits,
    compile_blueprint,
)
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.development_loop import (
    DevelopmentLoopLimits,
    FrozenDevelopmentContract,
    run_development_loop,
)
from tool_system.gate.command_runner import commands_from_change_plan, run_commands
from tool_system.gate.test_gate import build_gate_decision
from tool_system.local_git import (
    LocalGitIdentity,
    create_durable_local_git_store,
    create_isolated_local_workspace,
    run_durable_local_git,
)
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.process_authority.contract import (
    validate_explicit_task_pair,
    validate_process_authority,
)
from tool_system.repo_controller.artifact import write_jsonl_record
from tool_system.repository_context import (
    RepositoryContextError,
    RepositoryContextLimits,
    build_repository_context,
    validate_repository_context_freshness,
)
from tool_system.runner.active_gate_resolver import (
    paths_match,
    resolve_change_plan_from_active_gates,
)
from tool_system.worker_adapter import (
    AdapterRequest,
    CodexCLIAdapterConfig,
    CodexCLISubscriptionWorkerAdapter,
    WorkerAdapter,
    build_subscription_development_worker,
)


_SUBSCRIPTION_WORKER_ADAPTER_KIND = "codex_cli_subscription_worker_adapter"
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUBSCRIPTION_PACKET_VERSION = "subscription_development_authority_packet_v1"
_SUBSCRIPTION_COMPILATION_PACKET_VERSION = (
    "subscription_development_context_compilation_packet_v1"
)
_SUBSCRIPTION_AUTHORITY_BINDING_VERSION = (
    "subscription_public_entry_authority_binding_v1"
)
_SUBSCRIPTION_AUTHORITY_INPUT_MAX_BYTES = 1_048_576
_SUBSCRIPTION_EXECUTION_BINDING_VERSION = (
    "subscription_public_entry_execution_binding_v2"
)
_SUBSCRIPTION_ACCEPTANCE_OBLIGATION_VERSION = (
    "subscription_acceptance_evidence_obligation_v1"
)
_SUBSCRIPTION_ACCEPTANCE_RECEIPT_VERSION = (
    "subscription_acceptance_evidence_receipt_v1"
)
_SUBSCRIPTION_ACCEPTANCE_EVIDENCE_TYPES = {"behavior", "contract"}
_SUBSCRIPTION_ACCEPTANCE_RECEIPT_KEYS = {
    "receipt_version",
    "acceptance_item_sha256",
    "evidence_obligation_sha256",
    "evidence_type",
    "contract_digest",
    "candidate_tree",
    "actual_diff_paths",
    "validation_command_sha256",
    "exit_code",
    "stdout_sha256",
    "stderr_sha256",
    "candidate_assertions_sha256",
    "status",
    "receipt_sha256",
}
_SUBSCRIPTION_GIT_COMMAND_TIMEOUT_SECONDS = 120
_SUBSCRIPTION_VALIDATION_GIT_COMMAND_LIMIT = 16
_SUBSCRIPTION_LOCAL_COMMIT_GIT_COMMAND_LIMIT = 8
_SUBSCRIPTION_LEASE_RENEWAL_MARGIN_SECONDS = 30


class _SubscriptionUniqueKeyLoader(yaml.SafeLoader):
    """Reject ambiguous mapping keys in public-entry authority manifests."""


def _construct_subscription_unique_mapping(
    loader: _SubscriptionUniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in mapping:
            raise ValueError("SUBSCRIPTION_AUTHORITY_MANIFEST_AMBIGUOUS")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_SubscriptionUniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_subscription_unique_mapping,
)


def _subscription_preflight_boundary(
    *,
    status: str,
    terminal_code: str,
    reasons: Sequence[str],
) -> dict[str, object]:
    return {
        "status": status,
        "mode": "subscription_worker_public_entry_authority_preflight",
        "terminal_code": terminal_code,
        "reasons": [str(reason) for reason in reasons],
        "repository_context_built": False,
        "blueprint_compiled": False,
        "worker_execution_authorized": False,
        "api_mode_enabled": False,
        "provider_invocations": 0,
        "provider_credential_value_accesses": 0,
        "target_repo_mutations": 0,
        "remote_repository_operations": 0,
        "local_git_operations": 0,
        "production_operations": 0,
        "cleanup_operations": 0,
        "rollback_operations": 0,
    }


def _bounded_subscription_values(
    values: Sequence[str],
    *,
    field: str,
    maximum: int,
    repository_paths: bool = False,
    required: bool = True,
) -> tuple[str, ...]:
    normalized = tuple(str(value) for value in values)
    if required and not normalized:
        raise ValueError(f"{field} is required")
    if len(normalized) > maximum or len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} exceeds its bound or contains duplicates")
    for value in normalized:
        if not value or len(value) > 256 or "\x00" in value:
            raise ValueError(f"{field} contains an invalid value")
        if repository_paths:
            path = PurePosixPath(value)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in value
                or value in {".", ""}
            ):
                raise ValueError(f"{field} must contain safe repo-relative paths")
    return normalized


def _capture_subscription_authority_inputs(
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
) -> tuple[bytes, bytes, Mapping[str, object]]:
    captured: list[bytes] = []
    for raw_path in (task_manifest_path, change_plan_path):
        path = Path(raw_path)
        if path.is_symlink() or not path.is_file():
            raise ValueError("SUBSCRIPTION_AUTHORITY_INPUT_UNAVAILABLE")
        data = path.read_bytes()
        if not data or len(data) > _SUBSCRIPTION_AUTHORITY_INPUT_MAX_BYTES:
            raise ValueError("SUBSCRIPTION_AUTHORITY_INPUT_LIMIT_EXCEEDED")
        captured.append(data)
    try:
        manifest = yaml.load(
            captured[0].decode("utf-8"),
            Loader=_SubscriptionUniqueKeyLoader,
        )
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ValueError("SUBSCRIPTION_AUTHORITY_MANIFEST_INVALID") from exc
    if not isinstance(manifest, Mapping):
        raise ValueError("SUBSCRIPTION_AUTHORITY_MANIFEST_INVALID")
    return captured[0], captured[1], manifest


def _subscription_authority_binding(
    manifest: Mapping[str, object],
    packet: Mapping[str, object],
) -> tuple[Mapping[str, object], str]:
    expected: dict[str, object] = {
        "binding_version": _SUBSCRIPTION_AUTHORITY_BINDING_VERSION,
        "enabled": True,
        "repository_root_identity_sha256": packet[
            "repository_root_identity_sha256"
        ],
        "expected_head": packet["expected_head"],
        "blueprint_path": packet["blueprint_path"],
        "module_registry_path": packet["module_registry_path"],
        "milestone_ids": list(packet["milestone_ids"]),
        "acceptance_requirements": list(packet["acceptance_requirements"]),
        "governance_paths": list(packet["governance_paths"]),
        "query_terms": list(packet["query_terms"]),
        "seed_paths": list(packet["seed_paths"]),
        "repository_read_authorized": True,
        "worker_execution_authorized": False,
        "local_git_write_authorized": False,
    }
    observed = manifest.get("subscription_public_entry")
    if not isinstance(observed, Mapping) or dict(observed) != expected:
        raise ValueError("SUBSCRIPTION_AUTHORITY_BINDING_MISMATCH")
    binding_sha256 = hashlib.sha256(
        json.dumps(
            expected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return expected, binding_sha256


def run_subscription_public_entry_preflight(
    *,
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
    repository_root: str | Path,
    expected_head: str,
    blueprint_path: str,
    module_registry_path: str,
    milestone_ids: Sequence[str],
    acceptance_requirements: Sequence[str],
    governance_paths: Sequence[str],
    query_terms: Sequence[str],
    seed_paths: Sequence[str] = (),
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
) -> dict[str, object]:
    """Validate authority and freeze a non-executing public-entry packet."""

    try:
        root = Path(repository_root)
        if not root.is_absolute() or "\x00" in str(root):
            raise ValueError("repository_root must be an absolute local path")
        head = str(expected_head)
        if _COMMIT_SHA.fullmatch(head) is None:
            raise ValueError("expected_head must be one lowercase 40-character SHA")
        blueprint = _bounded_subscription_values(
            [blueprint_path],
            field="blueprint_path",
            maximum=1,
            repository_paths=True,
        )[0]
        registry = _bounded_subscription_values(
            [module_registry_path],
            field="module_registry_path",
            maximum=1,
            repository_paths=True,
        )[0]
        milestones = _bounded_subscription_values(
            milestone_ids,
            field="milestone_ids",
            maximum=32,
        )
        acceptance = _bounded_subscription_values(
            acceptance_requirements,
            field="acceptance_requirements",
            maximum=64,
        )
        governance = _bounded_subscription_values(
            governance_paths,
            field="governance_paths",
            maximum=32,
            repository_paths=True,
        )
        terms = _bounded_subscription_values(
            query_terms,
            field="query_terms",
            maximum=32,
        )
        seeds = _bounded_subscription_values(
            seed_paths,
            field="seed_paths",
            maximum=64,
            repository_paths=True,
            required=False,
        )
    except (TypeError, ValueError) as exc:
        return _subscription_preflight_boundary(
            status="BLOCK",
            terminal_code="INVALID_SUBSCRIPTION_PREFLIGHT_INPUT",
            reasons=[str(exc)],
        )

    try:
        captured_manifest, captured_plan, authority_manifest = (
            _capture_subscription_authority_inputs(
                task_manifest_path,
                change_plan_path,
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        return _subscription_preflight_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_AUTHORITY_INPUT_CAPTURE_BLOCKED",
            reasons=[str(exc)],
        )

    authority = run_task_pipeline(
        task_manifest_path=task_manifest_path,
        change_plan_path=change_plan_path,
        policy_path=policy_path,
        autonomy_policy_path=autonomy_policy_path,
        process_authority_path=process_authority_path,
        execute_commands=False,
    )
    if authority["status"] != "PASS":
        blocked = _subscription_preflight_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_AUTHORITY_PREFLIGHT_BLOCKED",
            reasons=[str(reason) for reason in authority.get("reasons", [])],
        )
        return {**blocked, "authority_result": authority}

    packet: dict[str, object] = {
        "packet_version": _SUBSCRIPTION_PACKET_VERSION,
        "authority_status": "PASS",
        "repository_root_identity_sha256": hashlib.sha256(
            str(root).encode("utf-8")
        ).hexdigest(),
        "expected_head": head,
        "blueprint_path": blueprint,
        "module_registry_path": registry,
        "milestone_ids": list(milestones),
        "acceptance_requirements": list(acceptance),
        "governance_paths": list(governance),
        "query_terms": list(terms),
        "seed_paths": list(seeds),
        "repository_context_required": True,
        "blueprint_compilation_required": True,
        "worker_execution_authorized": False,
        "local_git_execution_authorized": False,
    }
    try:
        if (
            Path(task_manifest_path).read_bytes() != captured_manifest
            or Path(change_plan_path).read_bytes() != captured_plan
        ):
            raise ValueError("SUBSCRIPTION_AUTHORITY_INPUT_DRIFT")
        _, binding_sha256 = _subscription_authority_binding(
            authority_manifest,
            packet,
        )
    except (OSError, TypeError, ValueError) as exc:
        blocked = _subscription_preflight_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_AUTHORITY_BINDING_BLOCKED",
            reasons=[str(exc)],
        )
        return {**blocked, "authority_result": authority}
    packet.update(
        {
            "repository_read_authorized": True,
            "repository_read_binding_sha256": binding_sha256,
            "task_manifest_sha256": hashlib.sha256(
                captured_manifest
            ).hexdigest(),
            "change_plan_sha256": hashlib.sha256(captured_plan).hexdigest(),
        }
    )
    packet["packet_sha256"] = hashlib.sha256(
        json.dumps(
            packet,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    passed = _subscription_preflight_boundary(
        status="PASS",
        terminal_code="SUBSCRIPTION_AUTHORITY_PREFLIGHT_PASS",
        reasons=[],
    )
    return {
        **passed,
        "authority_result": authority,
        "dispatch_packet": packet,
    }


def _subscription_context_compilation_boundary(
    *,
    status: str,
    terminal_code: str,
    reasons: Sequence[str],
    repository_context_built: bool = False,
    blueprint_compiled: bool = False,
    local_git_read_only_context_authorized: bool = False,
) -> dict[str, object]:
    return {
        "status": status,
        "mode": "subscription_worker_public_entry_context_compile",
        "terminal_code": terminal_code,
        "reasons": [str(reason) for reason in reasons],
        "repository_context_built": repository_context_built,
        "blueprint_compiled": blueprint_compiled,
        "repository_read_mode": "exact_manifest_bound_snapshot",
        "local_git_read_only_context_authorized": (
            local_git_read_only_context_authorized
        ),
        "worker_execution_authorized": False,
        "worker_invocations": 0,
        "api_mode_enabled": False,
        "provider_invocations": 0,
        "provider_credential_value_accesses": 0,
        "repository_writes": 0,
        "target_repo_mutations": 0,
        "remote_repository_operations": 0,
        "local_git_write_operations": 0,
        "repository_context_builds": 1 if repository_context_built else 0,
        "production_operations": 0,
        "cleanup_operations": 0,
        "rollback_operations": 0,
    }


def _selected_context_mapping(
    repository_context: Mapping[str, object],
    path: str,
) -> Mapping[str, object]:
    selected = repository_context.get("selected_context")
    if not isinstance(selected, list):
        raise ValueError("SELECTED_CONTEXT_INVALID")
    matches = [
        record
        for record in selected
        if isinstance(record, Mapping) and record.get("path") == path
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("content"), str):
        raise ValueError("REQUIRED_COMMITTED_MAPPING_NOT_SELECTED")
    try:
        parsed = yaml.safe_load(str(matches[0]["content"]))
    except yaml.YAMLError as exc:
        raise ValueError("REQUIRED_COMMITTED_MAPPING_INVALID") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("REQUIRED_COMMITTED_MAPPING_INVALID")
    return parsed


def run_subscription_public_entry_context_compilation(
    *,
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
    repository_root: str | Path,
    expected_head: str,
    blueprint_path: str,
    module_registry_path: str,
    milestone_ids: Sequence[str],
    acceptance_requirements: Sequence[str],
    governance_paths: Sequence[str],
    query_terms: Sequence[str],
    seed_paths: Sequence[str] = (),
    repository_read_authorized: bool = False,
    isolated_fixture_repository: bool | None = None,
    repository_context_limits: RepositoryContextLimits | None = None,
    blueprint_compiler_limits: BlueprintCompilerLimits | None = None,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
) -> dict[str, object]:
    """Compose current authority, read-only context, and pure compilation."""

    read_requested = (
        repository_read_authorized is True
        or isolated_fixture_repository is True
    )
    if not read_requested:
        return {
            **_subscription_context_compilation_boundary(
                status="BLOCK",
                terminal_code="SUBSCRIPTION_CONTEXT_READ_NOT_REQUESTED",
                reasons=[
                    "repository read must be requested and exactly manifest-bound"
                ],
            ),
            "local_git_read_only_context_authorized": False,
        }

    preflight = run_subscription_public_entry_preflight(
        task_manifest_path=task_manifest_path,
        change_plan_path=change_plan_path,
        repository_root=repository_root,
        expected_head=expected_head,
        blueprint_path=blueprint_path,
        module_registry_path=module_registry_path,
        milestone_ids=milestone_ids,
        acceptance_requirements=acceptance_requirements,
        governance_paths=governance_paths,
        query_terms=query_terms,
        seed_paths=seed_paths,
        policy_path=policy_path,
        autonomy_policy_path=autonomy_policy_path,
        process_authority_path=process_authority_path,
    )
    if preflight["status"] != "PASS":
        return {
            **_subscription_context_compilation_boundary(
                status="BLOCK",
                terminal_code="SUBSCRIPTION_CONTEXT_AUTHORITY_BLOCKED",
                reasons=[str(reason) for reason in preflight.get("reasons", [])],
            ),
            "local_git_read_only_context_authorized": False,
            "preflight_result": preflight,
        }

    packet = preflight["dispatch_packet"]
    if not isinstance(packet, Mapping):
        return _subscription_context_compilation_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_AUTHORITY_PACKET_INVALID",
            reasons=["authority packet is missing"],
        )
    bounded_context = repository_context_limits or RepositoryContextLimits()
    context: Mapping[str, object] | None = None
    try:
        context_governance = tuple(
            dict.fromkeys(
                [
                    *[str(value) for value in packet["governance_paths"]],
                    str(packet["module_registry_path"]),
                ]
            )
        )
        context = build_repository_context(
            repository_root,
            expected_head=str(packet["expected_head"]),
            blueprint_path=str(packet["blueprint_path"]),
            governance_paths=context_governance,
            query_terms=[str(value) for value in packet["query_terms"]],
            seed_paths=[str(value) for value in packet["seed_paths"]],
            limits=bounded_context,
        )
        blueprint = _selected_context_mapping(
            context,
            str(packet["blueprint_path"]),
        )
        registry = _selected_context_mapping(
            context,
            str(packet["module_registry_path"]),
        )
        freshness = validate_repository_context_freshness(
            repository_root,
            context["snapshot"],
            max_tracked_files=bounded_context.max_tracked_files,
        )
        compilation = compile_blueprint(
            blueprint,
            context,
            registry,
            {
                "blueprint_approved": True,
                "repository_context_read_authorized": True,
                "target_repo_mutation_authorized": False,
                "provider_execution_authorized": False,
                "credential_value_access_authorized": False,
                "production_operation_authorized": False,
                "cleanup_execution_authorized": False,
            },
            milestone_ids=[str(value) for value in packet["milestone_ids"]],
            acceptance_requirements=[
                str(value) for value in packet["acceptance_requirements"]
            ],
            limits=blueprint_compiler_limits,
        )
    except (
        BlueprintCompilerError,
        RepositoryContextError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        reason = (
            exc.code
            if isinstance(exc, (BlueprintCompilerError, RepositoryContextError))
            else str(exc)
        )
        return _subscription_context_compilation_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_CONTEXT_COMPILATION_BLOCKED",
            reasons=[reason],
            repository_context_built=context is not None,
            local_git_read_only_context_authorized=True,
        )

    snapshot = context["snapshot"]
    selected = context["selected_context"]
    context_evidence = {
        "repository_root_identity_sha256": packet[
            "repository_root_identity_sha256"
        ],
        "snapshot": {
            key: snapshot[key]
            for key in (
                "head",
                "tree",
                "tracked_file_count",
                "tracked_set_sha256",
                "context_sha256",
                "clean_worktree",
            )
        },
        "freshness": freshness,
        "selected_paths": [
            str(record["path"])
            for record in selected
            if isinstance(record, Mapping)
        ],
        "selected_file_count": context["selected_file_count"],
        "selected_bytes": context["selected_bytes"],
        "natural_owner_proposal": context["natural_owner_proposal"],
        "evidence_sufficiency": context["evidence_sufficiency"],
    }
    compilation_packet: dict[str, object] = {
        "packet_version": _SUBSCRIPTION_COMPILATION_PACKET_VERSION,
        "authority_packet_sha256": packet["packet_sha256"],
        "repository_root_identity_sha256": packet[
            "repository_root_identity_sha256"
        ],
        "expected_head": packet["expected_head"],
        "context_sha256": snapshot["context_sha256"],
        "compilation_sha256": compilation["compilation_sha256"],
        "milestone_ids": list(packet["milestone_ids"]),
        "repository_read_authorized": packet["repository_read_authorized"],
        "repository_read_binding_sha256": packet[
            "repository_read_binding_sha256"
        ],
        "legacy_isolated_fixture_alias_used": (
            isolated_fixture_repository is True
            and repository_read_authorized is not True
        ),
        "worker_execution_authorized": False,
        "local_git_write_authorized": False,
    }
    compilation_packet["packet_sha256"] = hashlib.sha256(
        json.dumps(
            compilation_packet,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        **_subscription_context_compilation_boundary(
            status="PASS",
            terminal_code="SUBSCRIPTION_CONTEXT_COMPILATION_PASS",
            reasons=[],
            repository_context_built=True,
            blueprint_compiled=True,
            local_git_read_only_context_authorized=True,
        ),
        "authority_packet_sha256": packet["packet_sha256"],
        "context_evidence": context_evidence,
        "blueprint_compilation": compilation,
        "compilation_packet": compilation_packet,
    }


def _subscription_pipeline_boundary_record(
    *,
    status: str,
    adapter_kind: str,
    terminal_code: str | None = None,
    reasons: list[str] | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "mode": "subscription_worker_development_pipeline",
        "adapter_kind": adapter_kind,
        "terminal_code": terminal_code,
        "reasons": list(reasons or []),
        "api_mode_enabled": False,
        "provider_invocations": 0,
        "provider_credential_value_accesses": 0,
        "target_repo_mutations": 0,
        "remote_repository_operations": 0,
        "local_git_operations": 0,
    }


def run_subscription_development_pipeline(
    *,
    contract: FrozenDevelopmentContract,
    baseline_files: Mapping[str, object],
    adapter: WorkerAdapter,
    adapter_request: AdapterRequest,
    validator: Callable[[Mapping[str, str]], Mapping[str, object]],
    code_reviewer: Callable[[Mapping[str, object]], Mapping[str, object]],
    contract_reviewer: Callable[[Mapping[str, object]], Mapping[str, object]],
    limits: DevelopmentLoopLimits | None = None,
    resume_state: Mapping[str, object] | None = None,
    cancellation_requested: Callable[[], bool] | None = None,
) -> dict[str, object]:
    """Run the bounded loop through the guarded subscription-worker adapter."""

    adapter_kind = str(getattr(adapter, "adapter_kind", "unknown"))
    if adapter_kind != _SUBSCRIPTION_WORKER_ADAPTER_KIND:
        return _subscription_pipeline_boundary_record(
            status="BLOCK",
            adapter_kind=adapter_kind,
            terminal_code="UNSUPPORTED_SUBSCRIPTION_WORKER_ADAPTER",
            reasons=["only the guarded Codex CLI subscription adapter is accepted"],
        )

    worker = build_subscription_development_worker(
        adapter=adapter,
        request_template=adapter_request,
    )
    result = run_development_loop(
        contract=contract,
        baseline_files=baseline_files,
        worker=worker,
        validator=validator,
        code_reviewer=code_reviewer,
        contract_reviewer=contract_reviewer,
        limits=limits,
        resume_state=resume_state,
        cancellation_requested=cancellation_requested,
    )
    return {
        **result,
        **_subscription_pipeline_boundary_record(
            status=str(result.get("status", "BLOCK")),
            adapter_kind=adapter_kind,
            terminal_code=(
                str(result["terminal_code"])
                if result.get("terminal_code") is not None
                else None
            ),
            reasons=[str(reason) for reason in result.get("reasons", [])],
        ),
        "subscription_worker_invocations": int(
            result.get("worker_call_count", 0)
        ),
    }



def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _private_path_identity(raw_path: str | Path, label: str) -> tuple[Path, str]:
    path = Path(raw_path)
    if not path.is_absolute() or "\x00" in str(path):
        raise ValueError(f"{label} must be one absolute local path")
    if path.exists() and path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    return path, hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _normalized_codex_configuration(
    value: CodexCLIAdapterConfig | Mapping[str, object],
) -> CodexCLIAdapterConfig:
    if isinstance(value, CodexCLIAdapterConfig):
        return value
    if not isinstance(value, Mapping) or set(value) != {
        "executable",
        "enabled",
        "timeout_seconds",
        "termination_grace_seconds",
        "max_prompt_bytes",
        "max_output_bytes",
    }:
        raise ValueError("SUBSCRIPTION_EXECUTION_WORKER_CONFIG_INVALID")
    try:
        return CodexCLIAdapterConfig(**dict(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "SUBSCRIPTION_EXECUTION_WORKER_CONFIG_INVALID"
        ) from exc


def _worker_configuration_sha256(config: CodexCLIAdapterConfig) -> str:
    return _canonical_sha256(
        {
            "executable": config.executable,
            "enabled": config.enabled,
            "timeout_seconds": config.timeout_seconds,
            "termination_grace_seconds": config.termination_grace_seconds,
            "max_prompt_bytes": config.max_prompt_bytes,
            "max_output_bytes": config.max_output_bytes,
            "inherited_environment_names": list(
                config.inherited_environment_names
            ),
        }
    )


def _subscription_durable_lease_seconds(
    *,
    binding: Mapping[str, object],
    config: CodexCLIAdapterConfig,
) -> float:
    """Derive one renewable stage lease from the frozen execution envelope."""

    validation_set = binding["validation_set"]
    if not isinstance(validation_set, list):
        raise TypeError("SUBSCRIPTION_EXECUTION_VALIDATION_SET_INVALID")
    validation_timeout = binding["validation_timeout_seconds"]
    if type(validation_timeout) is not int:
        raise TypeError("SUBSCRIPTION_EXECUTION_VALIDATION_BUDGET_INVALID")
    worker_stage = (
        config.timeout_seconds + (2 * config.termination_grace_seconds)
    )
    validation_stage = (
        _SUBSCRIPTION_VALIDATION_GIT_COMMAND_LIMIT
        * _SUBSCRIPTION_GIT_COMMAND_TIMEOUT_SECONDS
        + len(validation_set) * validation_timeout
    )
    local_commit_stage = (
        _SUBSCRIPTION_LOCAL_COMMIT_GIT_COMMAND_LIMIT
        * _SUBSCRIPTION_GIT_COMMAND_TIMEOUT_SECONDS
    )
    return float(
        max(worker_stage, validation_stage, local_commit_stage)
        + _SUBSCRIPTION_LEASE_RENEWAL_MARGIN_SECONDS
    )


def _captured_plan_commands(plan_bytes: bytes) -> tuple[str, ...]:
    try:
        plan = yaml.load(
            plan_bytes.decode("utf-8"),
            Loader=_SubscriptionUniqueKeyLoader,
        )
        if not isinstance(plan, dict):
            raise ValueError("SUBSCRIPTION_EXECUTION_PLAN_INVALID")
        commands = commands_from_change_plan(plan)
    except (UnicodeError, ValueError, yaml.YAMLError) as exc:
        raise ValueError("SUBSCRIPTION_EXECUTION_PLAN_INVALID") from exc
    if not commands or len(commands) > 32 or len(set(commands)) != len(commands):
        raise ValueError("SUBSCRIPTION_EXECUTION_VALIDATION_SET_INVALID")
    if any(
        not command.strip() or len(command.encode("utf-8")) > 4_096
        for command in commands
    ):
        raise ValueError("SUBSCRIPTION_EXECUTION_VALIDATION_SET_INVALID")
    return tuple(commands)


def _acceptance_item_sha256(acceptance_item: str) -> str:
    return _canonical_sha256({"acceptance_item": acceptance_item})


def _validation_command_sha256(validation_command: str) -> str:
    return _canonical_sha256({"validation_command": validation_command})


def _candidate_tree_sha256(files: Mapping[str, str]) -> str:
    return _canonical_sha256(
        {
            path: hashlib.sha256(content.encode("utf-8")).hexdigest()
            for path, content in sorted(files.items())
        }
    )


def _candidate_diff_paths(
    *,
    baseline_files: Mapping[str, str],
    candidate_files: Mapping[str, str],
    allowed_scope: Sequence[str],
) -> tuple[str, ...]:
    if (
        not isinstance(candidate_files, Mapping)
        or not set(candidate_files) <= set(allowed_scope)
        or any(not isinstance(value, str) for value in candidate_files.values())
    ):
        raise ValueError("SUBSCRIPTION_ACCEPTANCE_CANDIDATE_INVALID")
    return tuple(
        path
        for path in allowed_scope
        if (path in baseline_files) != (path in candidate_files)
        or baseline_files.get(path) != candidate_files.get(path)
    )


def _normalize_acceptance_evidence_obligations(
    value: object,
    *,
    acceptance_set: tuple[str, ...],
    validation_set: tuple[str, ...],
    allowed_scope: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    if (
        not isinstance(value, list)
        or len(value) != len(acceptance_set)
        or len(validation_set) != len(acceptance_set)
    ):
        raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_COVERAGE_MISMATCH")
    normalized: list[dict[str, object]] = []
    seen_commands: set[str] = set()
    expected_keys = {
        "obligation_version",
        "acceptance_item",
        "acceptance_item_sha256",
        "evidence_type",
        "validation_command",
        "validation_command_sha256",
        "expected_stdout_sha256",
        "expected_stderr_sha256",
        "expected_diff_paths",
        "candidate_assertions",
        "obligation_sha256",
    }
    for acceptance_item, expected_command, raw in zip(
        acceptance_set,
        validation_set,
        value,
        strict=True,
    ):
        if not isinstance(raw, Mapping) or set(raw) != expected_keys:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_SHAPE_MISMATCH")
        if raw["obligation_version"] != _SUBSCRIPTION_ACCEPTANCE_OBLIGATION_VERSION:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_VERSION_MISMATCH")
        if raw["acceptance_item"] != acceptance_item:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ITEM_MISMATCH")
        acceptance_digest = _acceptance_item_sha256(acceptance_item)
        if raw["acceptance_item_sha256"] != acceptance_digest:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ITEM_DIGEST_MISMATCH")
        evidence_type = raw["evidence_type"]
        if evidence_type not in _SUBSCRIPTION_ACCEPTANCE_EVIDENCE_TYPES:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_TYPE_UNSUPPORTED")
        command = raw["validation_command"]
        if (
            not isinstance(command, str)
            or command != expected_command
            or command in seen_commands
        ):
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_COMMAND_MISMATCH")
        seen_commands.add(command)
        command_digest = _validation_command_sha256(command)
        if raw["validation_command_sha256"] != command_digest:
            raise ValueError(
                "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_COMMAND_DIGEST_MISMATCH"
            )
        for field in ("expected_stdout_sha256", "expected_stderr_sha256"):
            if (
                not isinstance(raw[field], str)
                or _SHA256.fullmatch(str(raw[field])) is None
            ):
                raise ValueError(
                    "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_OUTPUT_DIGEST_INVALID"
                )
        expected_diff_paths = _bounded_subscription_values(
            raw["expected_diff_paths"],
            field="acceptance_evidence.expected_diff_paths",
            maximum=128,
            repository_paths=True,
        )
        if not set(expected_diff_paths) <= set(allowed_scope):
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_SCOPE_DRIFT")
        assertions = raw["candidate_assertions"]
        if not isinstance(assertions, list) or len(assertions) != len(
            expected_diff_paths
        ):
            raise ValueError(
                "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_COVERAGE_MISMATCH"
            )
        normalized_assertions: list[dict[str, str]] = []
        for path, assertion in zip(expected_diff_paths, assertions, strict=True):
            if not isinstance(assertion, Mapping) or assertion.get("path") != path:
                raise ValueError(
                    "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_PATH_MISMATCH"
                )
            state = assertion.get("state")
            if state == "present":
                if set(assertion) != {"path", "state", "content_sha256"}:
                    raise ValueError(
                        "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_SHAPE_MISMATCH"
                    )
                content_sha256 = assertion.get("content_sha256")
                if (
                    not isinstance(content_sha256, str)
                    or _SHA256.fullmatch(content_sha256) is None
                ):
                    raise ValueError(
                        "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_DIGEST_INVALID"
                    )
                normalized_assertions.append(
                    {
                        "path": path,
                        "state": "present",
                        "content_sha256": content_sha256,
                    }
                )
            elif state == "absent":
                if set(assertion) != {"path", "state"}:
                    raise ValueError(
                        "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_SHAPE_MISMATCH"
                    )
                normalized_assertions.append({"path": path, "state": "absent"})
            else:
                raise ValueError(
                    "SUBSCRIPTION_ACCEPTANCE_EVIDENCE_ASSERTION_STATE_INVALID"
                )
        body: dict[str, object] = {
            "obligation_version": _SUBSCRIPTION_ACCEPTANCE_OBLIGATION_VERSION,
            "acceptance_item": acceptance_item,
            "acceptance_item_sha256": acceptance_digest,
            "evidence_type": evidence_type,
            "validation_command": command,
            "validation_command_sha256": command_digest,
            "expected_stdout_sha256": raw["expected_stdout_sha256"],
            "expected_stderr_sha256": raw["expected_stderr_sha256"],
            "expected_diff_paths": list(expected_diff_paths),
            "candidate_assertions": normalized_assertions,
        }
        obligation = {**body, "obligation_sha256": _canonical_sha256(body)}
        if dict(raw) != obligation:
            raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_DIGEST_MISMATCH")
        normalized.append(obligation)
    if seen_commands != set(validation_set):
        raise ValueError("SUBSCRIPTION_ACCEPTANCE_EVIDENCE_COMMAND_COVERAGE_MISMATCH")
    return tuple(normalized)


def _candidate_assertions_match(
    candidate_files: Mapping[str, str],
    obligation: Mapping[str, object],
) -> bool:
    assertions = obligation.get("candidate_assertions")
    if not isinstance(assertions, list):
        return False
    for assertion in assertions:
        if not isinstance(assertion, Mapping):
            return False
        path = assertion.get("path")
        if not isinstance(path, str):
            return False
        state = assertion.get("state")
        if state == "present":
            content = candidate_files.get(path)
            if (
                not isinstance(content, str)
                or hashlib.sha256(content.encode("utf-8")).hexdigest()
                != assertion.get("content_sha256")
            ):
                return False
        elif state == "absent":
            if path in candidate_files:
                return False
        else:
            return False
    return True


def _acceptance_evidence_receipt(
    *,
    contract: FrozenDevelopmentContract,
    obligation: Mapping[str, object],
    candidate_tree: str,
    actual_diff_paths: tuple[str, ...],
) -> dict[str, object]:
    body: dict[str, object] = {
        "receipt_version": _SUBSCRIPTION_ACCEPTANCE_RECEIPT_VERSION,
        "acceptance_item_sha256": obligation["acceptance_item_sha256"],
        "evidence_obligation_sha256": obligation["obligation_sha256"],
        "evidence_type": obligation["evidence_type"],
        "contract_digest": contract.task_digest,
        "candidate_tree": candidate_tree,
        "actual_diff_paths": list(actual_diff_paths),
        "validation_command_sha256": obligation["validation_command_sha256"],
        "exit_code": 0,
        "stdout_sha256": obligation["expected_stdout_sha256"],
        "stderr_sha256": obligation["expected_stderr_sha256"],
        "candidate_assertions_sha256": _canonical_sha256(
            obligation["candidate_assertions"]
        ),
        "status": "PASS",
    }
    return {**body, "receipt_sha256": _canonical_sha256(body)}


def _receipt_from_validation_record(record: object) -> Mapping[str, object] | None:
    if not isinstance(record, Mapping) or record.get("status") != "PASS":
        return None
    diagnostic = record.get("diagnostic")
    if not isinstance(diagnostic, str):
        return None
    try:
        receipt = json.loads(diagnostic)
    except (json.JSONDecodeError, TypeError):
        return None
    return receipt if isinstance(receipt, Mapping) else None


def _execution_binding(
    *,
    manifest: Mapping[str, object],
    repository_identity_sha256: str,
    workspace_identity_sha256: str,
    durable_state_identity_sha256: str,
    expected_head: str,
    expected_tree: str,
    acceptance_set: tuple[str, ...],
    validation_set: tuple[str, ...],
    worker_configuration_sha256: str,
    task_pair_sha256: str,
    authority_flags: Mapping[str, bool],
) -> tuple[dict[str, object], FrozenDevelopmentContract, DevelopmentLoopLimits]:
    observed = manifest.get("subscription_public_entry_execution")
    if not isinstance(observed, Mapping):
        raise ValueError("SUBSCRIPTION_EXECUTION_BINDING_MISSING")
    exact_keys = {
        "binding_version",
        "enabled",
        "repository_root_identity_sha256",
        "workspace_root_identity_sha256",
        "durable_state_identity_sha256",
        "expected_head",
        "expected_tree",
        "existing_scope_paths",
        "addable_scope_paths",
        "allowed_scope",
        "acceptance_set",
        "acceptance_evidence_obligations",
        "validation_set",
        "worker_configuration_sha256",
        "branch_name",
        "commit_message",
        "finite_budgets",
        "validation_timeout_seconds",
        "max_validation_output_bytes",
        "repository_read_authorized",
        "worker_execution_authorized",
        "validation_execution_authorized",
        "subscription_data_transfer_authorized",
        "local_git_write_authorized",
        "api_mode_enabled",
        "provider_execution_authorized",
        "credential_value_access_authorized",
        "remote_repository_operations_authorized",
        "target_repo_mutation_authorized",
        "production_operation_authorized",
        "cleanup_execution_authorized",
        "rollback_execution_authorized",
        "max_local_commits",
    }
    if set(observed) != exact_keys:
        raise ValueError("SUBSCRIPTION_EXECUTION_BINDING_SHAPE_MISMATCH")
    existing_scope = _bounded_subscription_values(
        observed["existing_scope_paths"],
        field="existing_scope_paths",
        maximum=128,
        repository_paths=True,
        required=False,
    )
    addable_scope = _bounded_subscription_values(
        observed["addable_scope_paths"],
        field="addable_scope_paths",
        maximum=128,
        repository_paths=True,
        required=False,
    )
    if set(existing_scope).intersection(addable_scope):
        raise ValueError("SUBSCRIPTION_EXECUTION_SCOPE_OVERLAP")
    allowed_scope = _bounded_subscription_values(
        observed["allowed_scope"],
        field="allowed_scope",
        maximum=128,
        repository_paths=True,
    )
    if tuple([*existing_scope, *addable_scope]) != allowed_scope:
        raise ValueError("SUBSCRIPTION_EXECUTION_SCOPE_TOPOLOGY_MISMATCH")
    observed_acceptance = _bounded_subscription_values(
        observed["acceptance_set"],
        field="acceptance_set",
        maximum=64,
    )
    observed_validation = _bounded_subscription_values(
        observed["validation_set"],
        field="validation_set",
        maximum=32,
    )
    if observed_acceptance != acceptance_set:
        raise ValueError("SUBSCRIPTION_EXECUTION_ACCEPTANCE_MISMATCH")
    if observed_validation != validation_set:
        raise ValueError("SUBSCRIPTION_EXECUTION_VALIDATION_MISMATCH")
    evidence_obligations = _normalize_acceptance_evidence_obligations(
        observed["acceptance_evidence_obligations"],
        acceptance_set=acceptance_set,
        validation_set=validation_set,
        allowed_scope=allowed_scope,
    )
    finite = observed["finite_budgets"]
    if not isinstance(finite, Mapping) or set(finite) != {
        "max_cycles",
        "max_worker_calls",
        "max_patch_operations_per_cycle",
        "max_total_duration_ms",
        "max_total_cost_microunits",
    }:
        raise ValueError("SUBSCRIPTION_EXECUTION_BUDGET_SHAPE_MISMATCH")
    try:
        limits = DevelopmentLoopLimits(
            max_cycles=int(finite["max_cycles"]),
            max_worker_calls=int(finite["max_worker_calls"]),
            max_patch_operations_per_cycle=int(
                finite["max_patch_operations_per_cycle"]
            ),
            max_total_duration_ms=int(finite["max_total_duration_ms"]),
            max_total_cost_microunits=int(
                finite["max_total_cost_microunits"]
            ),
        )
        limits.validate()
    except (TypeError, ValueError) as exc:
        raise ValueError("SUBSCRIPTION_EXECUTION_BUDGET_INVALID") from exc
    if any(
        isinstance(finite[name], bool) or type(finite[name]) is not int
        for name in finite
    ):
        raise ValueError("SUBSCRIPTION_EXECUTION_BUDGET_INVALID")
    validation_timeout = observed["validation_timeout_seconds"]
    validation_output = observed["max_validation_output_bytes"]
    if (
        type(validation_timeout) is not int
        or validation_timeout < 1
        or validation_timeout > 3_600
        or type(validation_output) is not int
        or validation_output < 1
        or validation_output > 16_777_216
    ):
        raise ValueError("SUBSCRIPTION_EXECUTION_VALIDATION_BUDGET_INVALID")
    branch_name = observed["branch_name"]
    commit_message = observed["commit_message"]
    if not isinstance(branch_name, str) or not isinstance(commit_message, str):
        raise ValueError("SUBSCRIPTION_EXECUTION_GIT_IDENTITY_INVALID")
    expected: dict[str, object] = {
        "binding_version": _SUBSCRIPTION_EXECUTION_BINDING_VERSION,
        "enabled": True,
        "repository_root_identity_sha256": repository_identity_sha256,
        "workspace_root_identity_sha256": workspace_identity_sha256,
        "durable_state_identity_sha256": durable_state_identity_sha256,
        "expected_head": expected_head,
        "expected_tree": expected_tree,
        "existing_scope_paths": list(existing_scope),
        "addable_scope_paths": list(addable_scope),
        "allowed_scope": list(allowed_scope),
        "acceptance_set": list(acceptance_set),
        "acceptance_evidence_obligations": [
            dict(obligation) for obligation in evidence_obligations
        ],
        "validation_set": list(validation_set),
        "worker_configuration_sha256": worker_configuration_sha256,
        "branch_name": branch_name,
        "commit_message": commit_message,
        "finite_budgets": dict(finite),
        "validation_timeout_seconds": validation_timeout,
        "max_validation_output_bytes": validation_output,
        **dict(authority_flags),
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
    if dict(observed) != expected:
        raise ValueError("SUBSCRIPTION_EXECUTION_BINDING_MISMATCH")
    task_digest = _canonical_sha256(
        {
            "execution_binding": expected,
            "task_pair_sha256": task_pair_sha256,
        }
    )
    contract = FrozenDevelopmentContract(
        task_digest=task_digest,
        baseline_tree=expected_tree,
        allowed_scope=allowed_scope,
        acceptance_set=acceptance_set,
        validation_set=validation_set,
    )
    contract.validate()
    LocalGitIdentity(
        expected_head_sha=expected_head,
        expected_tree_sha=expected_tree,
        branch_name=branch_name,
        commit_message=commit_message,
    ).validate()
    return expected, contract, limits


def _selected_text_files(context: Mapping[str, object]) -> dict[str, str]:
    selected = context.get("selected_context")
    if not isinstance(selected, list):
        raise ValueError("SUBSCRIPTION_EXECUTION_CONTEXT_INVALID")
    result: dict[str, str] = {}
    for record in selected:
        if (
            not isinstance(record, Mapping)
            or not isinstance(record.get("path"), str)
            or not isinstance(record.get("content"), str)
            or record["path"] in result
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_CONTEXT_INVALID")
        result[str(record["path"])] = str(record["content"])
    return result


def _write_text_files(root: Path, files: Mapping[str, str]) -> None:
    for raw_path, content in files.items():
        path = PurePosixPath(raw_path)
        if (
            path.is_absolute()
            or str(path) != raw_path
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_PATH_INVALID")
        target = root.joinpath(*path.parts)
        parent = root
        for part in path.parts[:-1]:
            parent /= part
            if parent.is_symlink() or (
                parent.exists() and not parent.is_dir()
            ):
                raise ValueError("SUBSCRIPTION_EXECUTION_PATH_UNSAFE")
        if target.is_symlink() or (
            target.exists() and not target.is_file()
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_PATH_UNSAFE")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _materialize_candidate(
    *,
    root: Path,
    baseline_files: Mapping[str, str],
    candidate_files: Mapping[str, str],
    allowed_scope: tuple[str, ...],
) -> None:
    if not set(candidate_files) <= set(allowed_scope):
        raise ValueError("SUBSCRIPTION_EXECUTION_CANDIDATE_SCOPE_DRIFT")
    for content in candidate_files.values():
        if not isinstance(content, str):
            raise ValueError("SUBSCRIPTION_EXECUTION_CANDIDATE_INVALID")
    changed = [
        path
        for path in allowed_scope
        if (path in baseline_files) != (path in candidate_files)
        or baseline_files.get(path) != candidate_files.get(path)
    ]
    for path in changed:
        parts = PurePosixPath(path).parts
        target = root.joinpath(*parts)
        parent = root
        for part in parts[:-1]:
            parent /= part
            if parent.is_symlink() or (
                parent.exists() and not parent.is_dir()
            ):
                raise ValueError("SUBSCRIPTION_EXECUTION_CANDIDATE_PATH_UNSAFE")
        if target.is_symlink() or (
            target.exists() and not target.is_file()
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_CANDIDATE_PATH_UNSAFE")
        if path in candidate_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(candidate_files[path], encoding="utf-8")
        else:
            if not target.is_file():
                raise ValueError("SUBSCRIPTION_EXECUTION_DELETE_DRIFT")
            target.unlink()


def _build_public_entry_validator(
    *,
    source_repository_root: Path,
    expected_head: str,
    expected_tree: str,
    task_manifest_path: Path,
    change_plan_path: Path,
    process_authority_path: str | Path,
    policy_path: str | Path,
    autonomy_policy_path: str | Path,
    baseline_files: Mapping[str, str],
    contract: FrozenDevelopmentContract,
    evidence_obligations: tuple[dict[str, object], ...],
    timeout_seconds: int,
    max_output_bytes: int,
    cancellation_requested: Callable[[], bool] | None,
) -> Callable[[Mapping[str, str]], Mapping[str, object]]:
    def validator(candidate_files: Mapping[str, str]) -> Mapping[str, object]:
        with tempfile.TemporaryDirectory(
            prefix="tool-system-candidate-validation-"
        ) as temporary_directory:
            temporary_root = Path(temporary_directory)
            os.chmod(temporary_root, 0o700)
            validation_root = temporary_root / "repository"
            workspace = create_isolated_local_workspace(
                source_repository_root=source_repository_root,
                workspace_root=validation_root,
                expected_head_sha=expected_head,
                expected_tree_sha=expected_tree,
            )
            if workspace.get("status") != "PASS":
                return {
                    "validation_results": {
                        name: {
                            "status": "BLOCK",
                            "diagnostic": "isolated validation workspace blocked",
                        }
                        for name in contract.validation_set
                    },
                    "satisfied_acceptance_items": [],
                }
            _materialize_candidate(
                root=validation_root,
                baseline_files=baseline_files,
                candidate_files=candidate_files,
                allowed_scope=contract.allowed_scope,
            )
            command_result = run_commands(
                task_manifest_path=task_manifest_path,
                change_plan_path=change_plan_path,
                process_authority_path=process_authority_path,
                policy_path=policy_path,
                autonomy_policy_path=autonomy_policy_path,
                cwd=validation_root,
                timeout_seconds=timeout_seconds,
                max_output_bytes=max_output_bytes,
                cancellation_requested=cancellation_requested,
                inherited_environment_names=(
                    "PATH",
                    "LANG",
                    "LC_ALL",
                    "PYTHONPATH",
                    "VIRTUAL_ENV",
                    "SYSTEMROOT",
                    "WINDIR",
                    "TMPDIR",
                    "TEMP",
                    "TMP",
                ),
            )
            observed_results = {
                str(record.get("name")): record
                for record in command_result.get("command_results", [])
                if isinstance(record, Mapping)
            }
            try:
                actual_diff_paths = _candidate_diff_paths(
                    baseline_files=baseline_files,
                    candidate_files=candidate_files,
                    allowed_scope=contract.allowed_scope,
                )
                candidate_tree = _candidate_tree_sha256(candidate_files)
            except ValueError:
                actual_diff_paths = ()
                candidate_tree = ""
            obligation_by_command = {
                str(obligation["validation_command"]): obligation
                for obligation in evidence_obligations
            }
            validation_results: dict[str, dict[str, object]] = {}
            satisfied_acceptance_items: list[str] = []
            for command in contract.validation_set:
                record = observed_results.get(command)
                obligation = obligation_by_command.get(command)
                passed = (
                    command_result.get("status") == "PASS"
                    and isinstance(record, Mapping)
                    and record.get("exit_code") == 0
                    and isinstance(record.get("stdout"), str)
                    and isinstance(record.get("stderr"), str)
                    and isinstance(obligation, Mapping)
                    and hashlib.sha256(
                        str(record["stdout"]).encode("utf-8")
                    ).hexdigest()
                    == obligation.get("expected_stdout_sha256")
                    and hashlib.sha256(
                        str(record["stderr"]).encode("utf-8")
                    ).hexdigest()
                    == obligation.get("expected_stderr_sha256")
                    and tuple(obligation.get("expected_diff_paths", ()))
                    == actual_diff_paths
                    and bool(actual_diff_paths)
                    and _candidate_assertions_match(candidate_files, obligation)
                )
                diagnostic = None
                if passed:
                    receipt = _acceptance_evidence_receipt(
                        contract=contract,
                        obligation=obligation,
                        candidate_tree=candidate_tree,
                        actual_diff_paths=actual_diff_paths,
                    )
                    diagnostic = json.dumps(
                        receipt,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    satisfied_acceptance_items.append(
                        str(obligation["acceptance_item"])
                    )
                else:
                    diagnostic = (
                        f"exit_code={record.get('exit_code')}"
                        if isinstance(record, Mapping)
                        else "machine-verifiable acceptance evidence did not complete"
                    )
                validation_results[command] = {
                    "status": "PASS" if passed else "BLOCK",
                    "diagnostic": diagnostic,
                }
            return {
                "validation_results": validation_results,
                "satisfied_acceptance_items": satisfied_acceptance_items,
            }

    return validator


def _public_entry_code_reviewer(
    contract: FrozenDevelopmentContract,
    *,
    baseline_files: Mapping[str, str],
    evidence_obligations: tuple[dict[str, object], ...],
) -> Callable[[Mapping[str, object]], Mapping[str, object]]:
    def reviewer(review_input: Mapping[str, object]) -> Mapping[str, object]:
        files = review_input.get("candidate_files")
        violations: list[str] = []
        try:
            if not isinstance(files, Mapping):
                raise TypeError
            candidate_files = dict(files)
            actual_diff_paths = _candidate_diff_paths(
                baseline_files=baseline_files,
                candidate_files=candidate_files,
                allowed_scope=contract.allowed_scope,
            )
            candidate_tree = _candidate_tree_sha256(candidate_files)
        except (AttributeError, TypeError, ValueError):
            candidate_files = {}
            actual_diff_paths = ()
            candidate_tree = ""
        validation = review_input.get("validation_results")
        for obligation in evidence_obligations:
            item = str(obligation["acceptance_item"])
            command = str(obligation["validation_command"])
            record = validation.get(command) if isinstance(validation, Mapping) else None
            receipt = _receipt_from_validation_record(record)
            if (
                tuple(obligation["expected_diff_paths"]) != actual_diff_paths
                or not actual_diff_paths
                or review_input.get("task_digest") != contract.task_digest
                or candidate_tree != review_input.get("candidate_tree")
                or not _candidate_assertions_match(candidate_files, obligation)
                or receipt
                != _acceptance_evidence_receipt(
                    contract=contract,
                    obligation=obligation,
                    candidate_tree=candidate_tree,
                    actual_diff_paths=actual_diff_paths,
                )
            ):
                violations.append(item)
        return {
            "violated_acceptance_items": violations,
            "suggestions": [],
        }

    return reviewer


def _public_entry_contract_reviewer(
    contract: FrozenDevelopmentContract,
    *,
    evidence_obligations: tuple[dict[str, object], ...],
) -> Callable[[Mapping[str, object]], Mapping[str, object]]:
    def reviewer(review_input: Mapping[str, object]) -> Mapping[str, object]:
        validation = review_input.get("validation_results")
        violations: list[str] = []
        exact_topology = (
            isinstance(validation, Mapping)
            and set(validation) == set(contract.validation_set)
            and review_input.get("task_digest") == contract.task_digest
            and tuple(review_input.get("acceptance_set", ()))
            == contract.acceptance_set
            and len(evidence_obligations) == len(contract.acceptance_set)
            and tuple(
                str(obligation["acceptance_item"])
                for obligation in evidence_obligations
            )
            == contract.acceptance_set
            and len(
                {
                    str(obligation["acceptance_item_sha256"])
                    for obligation in evidence_obligations
                }
            )
            == len(contract.acceptance_set)
        )
        candidate_tree = review_input.get("candidate_tree")
        for obligation in evidence_obligations:
            item = str(obligation["acceptance_item"])
            command = str(obligation["validation_command"])
            record = validation.get(command) if isinstance(validation, Mapping) else None
            receipt = _receipt_from_validation_record(record)
            if (
                not exact_topology
                or not isinstance(receipt, Mapping)
                or set(receipt) != _SUBSCRIPTION_ACCEPTANCE_RECEIPT_KEYS
                or receipt.get("receipt_version")
                != _SUBSCRIPTION_ACCEPTANCE_RECEIPT_VERSION
                or receipt.get("acceptance_item_sha256")
                != obligation["acceptance_item_sha256"]
                or receipt.get("evidence_obligation_sha256")
                != obligation["obligation_sha256"]
                or receipt.get("evidence_type") != obligation["evidence_type"]
                or receipt.get("contract_digest") != contract.task_digest
                or receipt.get("candidate_tree") != candidate_tree
                or receipt.get("validation_command_sha256")
                != obligation["validation_command_sha256"]
                or receipt.get("stdout_sha256")
                != obligation["expected_stdout_sha256"]
                or receipt.get("stderr_sha256")
                != obligation["expected_stderr_sha256"]
                or receipt.get("candidate_assertions_sha256")
                != _canonical_sha256(obligation["candidate_assertions"])
                or receipt.get("actual_diff_paths")
                != obligation["expected_diff_paths"]
                or receipt.get("status") != "PASS"
                or receipt.get("exit_code") != 0
                or receipt.get("receipt_sha256")
                != _canonical_sha256(
                    {
                        key: value
                        for key, value in receipt.items()
                        if key != "receipt_sha256"
                    }
                )
            ):
                violations.append(item)
        return {
            "violated_acceptance_items": violations,
            "suggestions": [],
        }

    return reviewer


def _subscription_execution_boundary(
    *,
    status: str,
    terminal_code: str,
    reasons: Sequence[str] = (),
) -> dict[str, object]:
    return {
        "status": status,
        "mode": "subscription_worker_public_entry_execution",
        "terminal_code": terminal_code,
        "reasons": [str(reason) for reason in reasons],
        "repository_context_built": False,
        "blueprint_compiled": False,
        "worker_execution_authorized": False,
        "worker_invocations": 0,
        "validation_command_invocations": 0,
        "durable_lease_seconds": 0,
        "local_workspace_created": False,
        "local_git_operations": 0,
        "api_mode_enabled": False,
        "provider_invocations": 0,
        "provider_credential_value_accesses": 0,
        "target_repo_mutations": 0,
        "remote_repository_operations": 0,
        "production_operations": 0,
        "cleanup_operations": 0,
        "rollback_operations": 0,
    }


def run_subscription_public_entry_execution(
    *,
    task_manifest_path: str | Path,
    change_plan_path: str | Path,
    repository_root: str | Path,
    workspace_root: str | Path,
    durable_state_path: str | Path,
    expected_head: str,
    expected_tree: str,
    blueprint_path: str,
    module_registry_path: str,
    milestone_ids: Sequence[str],
    acceptance_requirements: Sequence[str],
    governance_paths: Sequence[str],
    query_terms: Sequence[str],
    seed_paths: Sequence[str] = (),
    codex_config: CodexCLIAdapterConfig | Mapping[str, object],
    repository_read_authorized: bool = False,
    worker_execution_authorized: bool = False,
    validation_execution_authorized: bool = False,
    subscription_data_transfer_authorized: bool = False,
    local_git_write_authorized: bool = False,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    repository_context_limits: RepositoryContextLimits | None = None,
    blueprint_compiler_limits: BlueprintCompilerLimits | None = None,
    cancellation_requested: Callable[[], bool] | None = None,
    adapter: WorkerAdapter | None = None,
) -> dict[str, object]:
    """Run one exact subscription-primary workflow in an isolated local clone."""

    authority_flags = {
        "repository_read_authorized": repository_read_authorized,
        "worker_execution_authorized": worker_execution_authorized,
        "validation_execution_authorized": validation_execution_authorized,
        "subscription_data_transfer_authorized": (
            subscription_data_transfer_authorized
        ),
        "local_git_write_authorized": local_git_write_authorized,
    }
    if any(value is not True for value in authority_flags.values()):
        return _subscription_execution_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_EXECUTION_NOT_EXPLICITLY_REQUESTED",
            reasons=["all execution authority requests must be explicit"],
        )
    if _COMMIT_SHA.fullmatch(str(expected_tree)) is None:
        return _subscription_execution_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_EXECUTION_TREE_INVALID",
            reasons=["expected_tree must be one lowercase 40-character SHA"],
        )
    try:
        source_path, repository_identity = _private_path_identity(
            repository_root,
            "repository_root",
        )
        workspace_path, workspace_identity = _private_path_identity(
            workspace_root,
            "workspace_root",
        )
        state_path, state_identity = _private_path_identity(
            durable_state_path,
            "durable_state_path",
        )
        captured_manifest, captured_plan, manifest = (
            _capture_subscription_authority_inputs(
                task_manifest_path,
                change_plan_path,
            )
        )
        validation_set = _captured_plan_commands(captured_plan)
        acceptance_set = _bounded_subscription_values(
            acceptance_requirements,
            field="acceptance_requirements",
            maximum=64,
        )
        normalized_codex_config = _normalized_codex_configuration(
            codex_config
        )
        if (
            normalized_codex_config.enabled is not True
            or normalized_codex_config.violations()
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_WORKER_CONFIG_INVALID")
    except (OSError, TypeError, ValueError) as exc:
        return _subscription_execution_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_EXECUTION_INPUT_BLOCKED",
            reasons=[str(exc)],
        )

    context_result = run_subscription_public_entry_context_compilation(
        task_manifest_path=task_manifest_path,
        change_plan_path=change_plan_path,
        repository_root=source_path,
        expected_head=expected_head,
        blueprint_path=blueprint_path,
        module_registry_path=module_registry_path,
        milestone_ids=milestone_ids,
        acceptance_requirements=acceptance_requirements,
        governance_paths=governance_paths,
        query_terms=query_terms,
        seed_paths=seed_paths,
        repository_read_authorized=True,
        repository_context_limits=repository_context_limits,
        blueprint_compiler_limits=blueprint_compiler_limits,
        policy_path=policy_path,
        autonomy_policy_path=autonomy_policy_path,
        process_authority_path=process_authority_path,
    )
    if context_result.get("status") != "PASS":
        return {
            **_subscription_execution_boundary(
                status="BLOCK",
                terminal_code="SUBSCRIPTION_EXECUTION_CONTEXT_BLOCKED",
                reasons=[
                    str(reason)
                    for reason in context_result.get("reasons", [])
                ],
            ),
            "context_result": context_result,
        }

    try:
        if (
            Path(task_manifest_path).read_bytes() != captured_manifest
            or Path(change_plan_path).read_bytes() != captured_plan
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_AUTHORITY_INPUT_DRIFT")
        context_governance = tuple(
            dict.fromkeys([*governance_paths, module_registry_path])
        )
        context = build_repository_context(
            source_path,
            expected_head=expected_head,
            blueprint_path=blueprint_path,
            governance_paths=context_governance,
            query_terms=query_terms,
            seed_paths=seed_paths,
            limits=repository_context_limits or RepositoryContextLimits(),
        )
        snapshot = context["snapshot"]
        if (
            not isinstance(snapshot, Mapping)
            or snapshot.get("tree") != expected_tree
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_TREE_DRIFT")
        compilation_packet = context_result.get("compilation_packet")
        if (
            not isinstance(compilation_packet, Mapping)
            or compilation_packet.get("context_sha256")
            != snapshot.get("context_sha256")
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_CONTEXT_DRIFT")
        selected_files = _selected_text_files(context)
        index = context.get("repository_index")
        if not isinstance(index, list):
            raise ValueError("SUBSCRIPTION_EXECUTION_CONTEXT_INVALID")
        index_paths = {
            str(record["path"])
            for record in index
            if isinstance(record, Mapping)
            and isinstance(record.get("path"), str)
        }
        binding, contract, limits = _execution_binding(
            manifest=manifest,
            repository_identity_sha256=repository_identity,
            workspace_identity_sha256=workspace_identity,
            durable_state_identity_sha256=state_identity,
            expected_head=expected_head,
            expected_tree=expected_tree,
            acceptance_set=acceptance_set,
            validation_set=validation_set,
            worker_configuration_sha256=_worker_configuration_sha256(
                normalized_codex_config
            ),
            task_pair_sha256=_canonical_sha256(
                {
                    "task_manifest_sha256": hashlib.sha256(
                        captured_manifest
                    ).hexdigest(),
                    "change_plan_sha256": hashlib.sha256(
                        captured_plan
                    ).hexdigest(),
                }
            ),
            authority_flags=authority_flags,
        )
        durable_lease_seconds = _subscription_durable_lease_seconds(
            binding=binding,
            config=normalized_codex_config,
        )
        evidence_obligations = tuple(
            dict(obligation)
            for obligation in binding["acceptance_evidence_obligations"]
        )
        existing_scope = tuple(binding["existing_scope_paths"])
        addable_scope = tuple(binding["addable_scope_paths"])
        if (
            not set(existing_scope) <= set(seed_paths)
            or not set(existing_scope) <= index_paths
            or not set(existing_scope) <= set(selected_files)
            or set(addable_scope).intersection(index_paths)
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_SCOPE_TOPOLOGY_DRIFT")
        baseline_files = {
            path: selected_files[path] for path in existing_scope
        }
        freshness = validate_repository_context_freshness(
            source_path,
            snapshot,
            max_tracked_files=(
                repository_context_limits or RepositoryContextLimits()
            ).max_tracked_files,
        )
        if freshness.get("status") != "PASS":
            raise ValueError("SUBSCRIPTION_EXECUTION_SOURCE_STALE")
        if (
            Path(task_manifest_path).read_bytes() != captured_manifest
            or Path(change_plan_path).read_bytes() != captured_plan
        ):
            raise ValueError("SUBSCRIPTION_EXECUTION_AUTHORITY_INPUT_DRIFT")
    except (
        OSError,
        BlueprintCompilerError,
        RepositoryContextError,
        TypeError,
        ValueError,
    ) as exc:
        reason = (
            exc.code
            if isinstance(exc, (BlueprintCompilerError, RepositoryContextError))
            else str(exc)
        )
        return _subscription_execution_boundary(
            status="BLOCK",
            terminal_code="SUBSCRIPTION_EXECUTION_BINDING_BLOCKED",
            reasons=[reason],
        )

    workspace_result = create_isolated_local_workspace(
        source_repository_root=source_path,
        workspace_root=workspace_path,
        expected_head_sha=expected_head,
        expected_tree_sha=expected_tree,
    )
    if workspace_result.get("status") != "PASS":
        return {
            **_subscription_execution_boundary(
                status="BLOCK",
                terminal_code=str(
                    workspace_result.get(
                        "terminal_code",
                        "SUBSCRIPTION_EXECUTION_WORKSPACE_BLOCKED",
                    )
                ),
            ),
            "workspace_result": workspace_result,
        }

    try:
        state_parent = state_path.parent.resolve(strict=True)
        store = create_durable_local_git_store(
            database_path=state_path,
            forbidden_roots=(source_path, workspace_path),
        )
        concrete_adapter = adapter or CodexCLISubscriptionWorkerAdapter(
            normalized_codex_config
        )
        with tempfile.TemporaryDirectory(
            prefix="tool-system-subscription-context-"
        ) as temporary_directory:
            context_root = Path(temporary_directory)
            os.chmod(context_root, 0o700)
            _write_text_files(context_root, selected_files)
            adapter_request = AdapterRequest(
                adapter_id="subscription-" + contract.task_digest[:16],
                role="implementation",
                action="bounded_public_entry_development",
                task_id=contract.task_digest,
                input_refs=[
                    str(snapshot["context_sha256"]),
                    str(context_result["compilation_packet"]["compilation_sha256"]),
                ],
                context={
                    "workspace": str(context_root),
                    "subscription_worker_authorized": True,
                    "repository_context_sha256": snapshot["context_sha256"],
                },
                execute=True,
                calls_external_worker=True,
                writes_target_repo=False,
                executes_target_repo_mutation=False,
                production_deployment=False,
            )
            worker = build_subscription_development_worker(
                adapter=concrete_adapter,
                request_template=adapter_request,
            )
            validator = _build_public_entry_validator(
                source_repository_root=source_path,
                expected_head=expected_head,
                expected_tree=expected_tree,
                task_manifest_path=Path(task_manifest_path).resolve(strict=True),
                change_plan_path=Path(change_plan_path).resolve(strict=True),
                process_authority_path=process_authority_path,
                policy_path=policy_path,
                autonomy_policy_path=autonomy_policy_path,
                baseline_files=baseline_files,
                contract=contract,
                evidence_obligations=evidence_obligations,
                timeout_seconds=int(binding["validation_timeout_seconds"]),
                max_output_bytes=int(binding["max_validation_output_bytes"]),
                cancellation_requested=cancellation_requested,
            )
            identity = LocalGitIdentity(
                expected_head_sha=expected_head,
                expected_tree_sha=expected_tree,
                branch_name=str(binding["branch_name"]),
                commit_message=str(binding["commit_message"]),
            )
            local_result = run_durable_local_git(
                repository_root=workspace_path,
                store=store,
                run_id="subscription-" + contract.task_digest[:24],
                task_id="bounded-change",
                lease_owner="subscription-public-entry",
                identity=identity,
                contract=contract,
                baseline_files=baseline_files,
                worker=worker,
                validator=validator,
                code_reviewer=_public_entry_code_reviewer(
                    contract,
                    baseline_files=baseline_files,
                    evidence_obligations=evidence_obligations,
                ),
                contract_reviewer=_public_entry_contract_reviewer(
                    contract,
                    evidence_obligations=evidence_obligations,
                ),
                limits=limits,
                lease_seconds=durable_lease_seconds,
                cancellation_requested=cancellation_requested,
            )
    except Exception as exc:  # noqa: BLE001 - fail closed at runtime boundary
        return {
            **_subscription_execution_boundary(
                status="BLOCK",
                terminal_code="SUBSCRIPTION_EXECUTION_RUNTIME_BLOCKED",
                reasons=[type(exc).__name__],
            ),
            "workspace_identity_sha256": workspace_identity,
            "durable_state_identity_sha256": state_identity,
            "local_workspace_created": bool(
                workspace_result.get("workspace_created")
            ),
        }

    status = str(local_result.get("status", "BLOCK"))
    worker_calls = int(local_result.get("worker_call_count", 0))
    result = {
        **_subscription_execution_boundary(
            status=status,
            terminal_code=str(
                local_result.get(
                    "terminal_code",
                    "SUBSCRIPTION_EXECUTION_RUNTIME_BLOCKED",
                )
            ),
        ),
        "repository_context_built": True,
        "blueprint_compiled": True,
        "worker_execution_authorized": True,
        "worker_invocations": worker_calls,
        "validation_command_invocations": (
            len(validation_set) * worker_calls
        ),
        "durable_lease_seconds": durable_lease_seconds,
        "local_workspace_created": bool(
            workspace_result.get("workspace_created")
        ),
        "local_git_operations": 2 if status == "PASS" else 0,
        "repository_root_identity_sha256": repository_identity,
        "workspace_root_identity_sha256": workspace_identity,
        "durable_state_identity_sha256": state_identity,
        "authority_binding_sha256": _canonical_sha256(binding),
        "context_sha256": snapshot["context_sha256"],
        "compilation_sha256": context_result["compilation_packet"][
            "compilation_sha256"
        ],
        "task_digest": contract.task_digest,
        "candidate_tree": local_result.get("candidate_tree"),
        "branch": local_result.get("branch"),
        "commit": local_result.get("commit"),
        "tree": local_result.get("tree"),
        "worker_usage": {
            "duration_ms": int(local_result.get("total_duration_ms", 0)),
            "cost_microunits": int(
                local_result.get("total_cost_microunits", 0)
            ),
        },
        "rollback_plan": local_result.get("rollback_plan"),
        "cleanup_plan": local_result.get("cleanup_plan"),
        "draft_pr_plan": local_result.get("draft_pr_plan"),
        "state_parent_identity_sha256": hashlib.sha256(
            str(state_parent).encode("utf-8")
        ).hexdigest(),
    }
    return result


def _status_from_reasons(reasons: list[str]) -> str:
    return "PASS" if not reasons else "BLOCK"


def _resolved_plan_path(
    task_manifest_path: Path,
    change_plan_path: str | Path | None,
    active_gates_path: str | Path | None,
    execute_commands: bool,
) -> tuple[Path | None, str | None, list[str]]:
    if change_plan_path is not None:
        return Path(change_plan_path), "explicit_process_input", []
    if active_gates_path is None:
        return None, None, []
    if execute_commands:
        return None, "legacy_replay_blocked", [
            "legacy active-gate resolution is replay-only and cannot authorize command execution"
        ]
    if not paths_match(active_gates_path, "examples/active_gates.yaml"):
        return None, "legacy_replay_blocked", [
            "legacy replay requires the canonical examples/active_gates.yaml index"
        ]
    resolved = resolve_change_plan_from_active_gates(task_manifest_path, active_gates_path)
    return resolved, "legacy_replay" if resolved is not None else None, []


def run_task_pipeline(
    task_manifest_path: str | Path,
    change_plan_path: str | Path | None = None,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    manifest_path = Path(task_manifest_path)
    plan_path, plan_resolution_source, resolution_reasons = _resolved_plan_path(
        manifest_path,
        change_plan_path,
        active_gates_path,
        execute_commands,
    )
    policy = Path(policy_path)
    autonomy_policy = Path(autonomy_policy_path)
    process_authority = Path(process_authority_path)

    manifest_result = validate_task_manifest(manifest_path, policy, autonomy_policy)
    process_authority_result = validate_process_authority(process_authority)
    plan_result: dict[str, object] | None = None
    pair_binding_result: dict[str, object] | None = None
    protected_execution_result: dict[str, object] | None = None
    command_results: list[dict[str, Any]] = []
    preflight_reasons = list(resolution_reasons)
    if manifest_result["status"] != "PASS":
        preflight_reasons.extend(
            str(reason) for reason in manifest_result.get("reasons", [])
        )
    if process_authority_result["status"] != "PASS":
        preflight_reasons.extend(
            str(reason) for reason in process_authority_result.get("reasons", [])
        )

    if plan_path is not None:
        pair_binding_result = validate_explicit_task_pair(manifest_path, plan_path)
        plan_result = validate_change_plan(plan_path)
        if pair_binding_result["status"] != "PASS":
            preflight_reasons.extend(
                str(reason) for reason in pair_binding_result.get("reasons", [])
            )
        if plan_result["status"] != "PASS":
            preflight_reasons.extend(
                str(reason) for reason in plan_result.get("reasons", [])
            )
    else:
        preflight_reasons.append("change plan is required")

    if execute_commands and not preflight_reasons and plan_path is not None:
        protected_execution_result = run_commands(
            task_manifest_path=manifest_path,
            change_plan_path=plan_path,
            process_authority_path=process_authority,
            policy_path=policy,
            autonomy_policy_path=autonomy_policy,
            cwd=cwd or Path.cwd(),
        )
        command_results = list(
            protected_execution_result.get("command_results") or []
        )
        if protected_execution_result["status"] == "PASS":
            gate_decision = build_gate_decision(
                plan_ok=True,
                plan_reasons=[],
                command_results=command_results,
            )
        else:
            gate_decision = {
                "status": "BLOCK",
                "reasons": list(
                    protected_execution_result.get("reasons") or []
                ),
            }
    else:
        gate_decision = {
            "status": "PASS" if not preflight_reasons else "BLOCK",
            "reasons": preflight_reasons,
        }

    reasons = (
        []
        if gate_decision["status"] == "PASS"
        else [str(reason) for reason in gate_decision.get("reasons", [])]
    )

    output = {
        "status": _status_from_reasons(reasons),
        "mode": "tool_system_task_runner",
        "task_manifest_path": str(manifest_path),
        "change_plan_path": str(plan_path) if plan_path is not None else None,
        "change_plan_resolution_source": plan_resolution_source,
        "process_authority_path": str(process_authority),
        "legacy_active_gates_path": (
            str(active_gates_path) if active_gates_path is not None else None
        ),
        "policy_path": str(policy),
        "autonomy_policy_path": str(autonomy_policy),
        "manifest_result": manifest_result,
        "process_authority_result": process_authority_result,
        "pair_binding_result": pair_binding_result,
        "change_plan_result": plan_result,
        "protected_execution_result": protected_execution_result,
        "gate_decision": gate_decision,
        "command_results": command_results,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output


def _resolve_batch_path(raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    return Path(raw_path)


def run_batch_pipeline(
    batch: dict[str, Any],
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    reasons: list[str] = []
    raw_tasks = batch.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        reasons.append("batch.tasks must be a non-empty list")
        raw_tasks = []

    halt_on_failure = batch.get("halt_on_failure", True) is not False
    task_results: list[dict[str, object]] = []
    for index, entry in enumerate(raw_tasks):
        if not isinstance(entry, dict):
            reasons.append(f"batch task {index} must be a mapping")
            if halt_on_failure:
                break
            continue
        manifest_path = _resolve_batch_path(entry.get("task_manifest"))
        if manifest_path is None:
            reasons.append(f"batch task {index} requires task_manifest")
            if halt_on_failure:
                break
            continue
        plan_path = _resolve_batch_path(entry.get("change_plan"))
        result = run_task_pipeline(
            task_manifest_path=manifest_path,
            change_plan_path=plan_path,
            policy_path=policy_path,
            autonomy_policy_path=autonomy_policy_path,
            process_authority_path=process_authority_path,
            active_gates_path=entry.get("active_gates") or active_gates_path,
            cwd=entry.get("cwd") or cwd,
            execute_commands=execute_commands,
        )
        task_results.append(result)
        if result["status"] != "PASS":
            reasons.append(f"batch task {index} failed")
            reasons.extend(str(reason) for reason in result.get("reasons", []))
            if halt_on_failure:
                break

    output = {
        "status": _status_from_reasons(reasons),
        "mode": "tool_system_batch_runner",
        "task_count": len(raw_tasks),
        "completed_task_count": len(task_results),
        "process_authority_path": str(process_authority_path),
        "legacy_active_gates_path": (
            str(active_gates_path) if active_gates_path is not None else None
        ),
        "task_results": task_results,
        "writes_target_repo": False,
        "executes_target_repo_mutation": False,
        "reasons": reasons,
    }
    if audit_path is not None:
        artifact_path = write_jsonl_record(audit_path, output)
        output["audit_path"] = str(artifact_path)
    return output


def run_batch_file(
    batch_path: str | Path,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
    active_gates_path: str | Path | None = None,
    cwd: str | Path | None = None,
    audit_path: str | Path | None = None,
    execute_commands: bool = True,
) -> dict[str, object]:
    batch_file = Path(batch_path)
    batch = load_yaml_file(batch_file)
    output = run_batch_pipeline(
        batch=batch,
        policy_path=policy_path,
        autonomy_policy_path=autonomy_policy_path,
        process_authority_path=process_authority_path,
        active_gates_path=active_gates_path,
        cwd=cwd,
        audit_path=audit_path,
        execute_commands=execute_commands,
    )
    return {**output, "batch_path": str(batch_file)}
