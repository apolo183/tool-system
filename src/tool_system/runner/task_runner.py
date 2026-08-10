from __future__ import annotations

import hashlib
import json
import re
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
from tool_system.gate.command_runner import run_commands
from tool_system.gate.test_gate import build_gate_decision
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
    WorkerAdapter,
    build_subscription_development_worker,
)


_SUBSCRIPTION_WORKER_ADAPTER_KIND = "codex_cli_subscription_worker_adapter"
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SUBSCRIPTION_PACKET_VERSION = "subscription_development_authority_packet_v1"
_SUBSCRIPTION_COMPILATION_PACKET_VERSION = (
    "subscription_development_context_compilation_packet_v1"
)
_SUBSCRIPTION_AUTHORITY_BINDING_VERSION = (
    "subscription_public_entry_authority_binding_v1"
)
_SUBSCRIPTION_AUTHORITY_INPUT_MAX_BYTES = 1_048_576


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
        "repository_read_mode": "isolated_fixture_only",
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
        "real_downstream_repository_accesses": 0,
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
    isolated_fixture_repository: bool = False,
    repository_context_limits: RepositoryContextLimits | None = None,
    blueprint_compiler_limits: BlueprintCompilerLimits | None = None,
    policy_path: str | Path = "policy/repo_write_policy.yaml",
    autonomy_policy_path: str | Path = "policy/autonomy_policy.yaml",
    process_authority_path: str | Path = "config/process_authority_v1.yaml",
) -> dict[str, object]:
    """Compose current authority, read-only context, and pure compilation."""

    if isolated_fixture_repository is not True:
        return {
            **_subscription_context_compilation_boundary(
                status="BLOCK",
                terminal_code="SUBSCRIPTION_CONTEXT_REPOSITORY_CLASS_NOT_AUTHORIZED",
                reasons=["only an explicitly selected isolated fixture is accepted"],
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
                "isolated_fixture_repositories_only": True,
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
        "isolated_fixture_repository": True,
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
