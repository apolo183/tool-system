"""Compile approved blueprint milestones into bounded, non-authorizing plans.

The compiler is deliberately pure: it accepts already-collected repository and
registry evidence, returns JSON-compatible values, and never reads or writes a
repository, credential, network endpoint, database, or provider.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_CHANGE_KINDS = {"add", "modify", "replace"}
_TASK_TEMPLATES = (
    ("evidence", "evidence_collector", "evidence", ()),
    ("policy", "policy_guard", "gate", ("evidence",)),
    ("architecture", "blueprint_architect", "document", ("policy",)),
    ("plan", "change_planner", "plan", ("architecture",)),
    ("implement", "patch_author", "implementation", ("plan",)),
    ("test", "test_engineer", "verification", ("implement",)),
    ("code-review", "code_reviewer", "review", ("test",)),
    ("contract-review", "contract_reviewer", "review", ("test",)),
    ("audit", "audit_recorder", "acceptance", ("code-review", "contract-review")),
    ("rollback", "audit_recorder", "rollback", ("implement",)),
)


class BlueprintCompilerError(ValueError):
    """Fail-closed compiler error carrying only a stable classification."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class BlueprintCompilerLimits:
    """Finite compiler input and output ceilings."""

    max_milestones: int = 16
    max_tasks: int = 160
    max_allowed_files_per_milestone: int = 64
    max_acceptance_items_per_milestone: int = 64
    max_validation_items_per_milestone: int = 32

    def validate(self) -> None:
        if any(not isinstance(value, int) or value <= 0 for value in asdict(self).values()):
            raise BlueprintCompilerError("INVALID_LIMITS")


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise BlueprintCompilerError(code)
    return value


def _path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise BlueprintCompilerError("INVALID_REPOSITORY_PATH")
    if value.startswith("/") or posixpath.normpath(value) != value:
        raise BlueprintCompilerError("INVALID_REPOSITORY_PATH")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise BlueprintCompilerError("INVALID_REPOSITORY_PATH")
    return value


def _strings(value: object, code: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise BlueprintCompilerError(code)
    if not all(isinstance(item, str) and item for item in value):
        raise BlueprintCompilerError(code)
    if len(value) != len(set(value)):
        raise BlueprintCompilerError(code)
    return list(value)


def _registry_modules(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    modules = registry.get("modules")
    if not isinstance(modules, list):
        raise BlueprintCompilerError("INVALID_MODULE_REGISTRY")
    result: dict[str, Mapping[str, Any]] = {}
    for module in modules:
        if not isinstance(module, Mapping):
            raise BlueprintCompilerError("INVALID_MODULE_REGISTRY")
        module_id = _identifier(module.get("module_id"), "INVALID_MODULE_REGISTRY")
        if module_id in result:
            raise BlueprintCompilerError("INVALID_MODULE_REGISTRY")
        result[module_id] = module
    return result


def _repository_paths(context: Mapping[str, Any]) -> set[str]:
    if context.get("status") != "PASS":
        raise BlueprintCompilerError("REPOSITORY_CONTEXT_NOT_ACCEPTED")
    snapshot = context.get("snapshot")
    proposal = context.get("natural_owner_proposal")
    index = context.get("repository_index")
    if not isinstance(snapshot, Mapping) or snapshot.get("clean_worktree") is not True:
        raise BlueprintCompilerError("REPOSITORY_CONTEXT_NOT_ACCEPTED")
    if not isinstance(snapshot.get("head"), str) or not isinstance(snapshot.get("tree"), str):
        raise BlueprintCompilerError("REPOSITORY_CONTEXT_NOT_ACCEPTED")
    if not isinstance(proposal, Mapping) or proposal.get("authority_effect") != "none":
        raise BlueprintCompilerError("OWNER_PROPOSAL_MUST_BE_NON_AUTHORIZING")
    if not isinstance(index, list) or not index:
        raise BlueprintCompilerError("REPOSITORY_CONTEXT_NOT_ACCEPTED")
    paths: set[str] = set()
    for record in index:
        if not isinstance(record, Mapping):
            raise BlueprintCompilerError("REPOSITORY_CONTEXT_NOT_ACCEPTED")
        paths.add(_path(record.get("path")))
    return paths


def _authorization(envelope: Mapping[str, Any]) -> None:
    required = {
        "blueprint_approved": True,
        "isolated_fixture_repositories_only": True,
        "target_repo_mutation_authorized": False,
        "provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
    }
    if any(envelope.get(key) is not value for key, value in required.items()):
        raise BlueprintCompilerError("AUTHORIZATION_ENVELOPE_BLOCKED")


def _module_change(
    milestone_id: str,
    milestone: Mapping[str, Any],
    tracked_paths: set[str],
    registered_modules: Mapping[str, Mapping[str, Any]],
    limits: BlueprintCompilerLimits,
) -> dict[str, Any]:
    raw = milestone.get("module_change")
    if not isinstance(raw, Mapping):
        raise BlueprintCompilerError("MISSING_MODULE_CHANGE_BINDING")
    module_id = _identifier(raw.get("module_id"), "INVALID_MODULE_CHANGE")
    interface_id = _identifier(raw.get("interface_id"), "INVALID_MODULE_CHANGE")
    module_version = _identifier(raw.get("module_version"), "INVALID_MODULE_CHANGE")
    interface_version = _identifier(raw.get("interface_version"), "INVALID_MODULE_CHANGE")
    if _SEMVER.fullmatch(module_version) is None or _SEMVER.fullmatch(interface_version) is None:
        raise BlueprintCompilerError("INVALID_MODULE_CHANGE")
    change_kind = raw.get("change_kind")
    if change_kind not in _CHANGE_KINDS:
        raise BlueprintCompilerError("INVALID_MODULE_CHANGE")
    exists = module_id in registered_modules
    if (change_kind == "add" and exists) or (change_kind != "add" and not exists):
        raise BlueprintCompilerError("MODULE_CHANGE_PRECONDITION_FAILED")
    allowed_files = [_path(item) for item in _strings(raw.get("allowed_files"), "INVALID_ALLOWED_SCOPE")]
    if len(allowed_files) > limits.max_allowed_files_per_milestone:
        raise BlueprintCompilerError("ALLOWED_SCOPE_LIMIT_EXCEEDED")
    if change_kind != "add" and not set(allowed_files) <= tracked_paths:
        raise BlueprintCompilerError("ALLOWED_SCOPE_NOT_IN_SNAPSHOT")
    owner_paths = [_path(item) for item in _strings(raw.get("natural_owner_paths"), "INVALID_OWNER_PATHS")]
    tests = [_path(item) for item in _strings(raw.get("test_paths"), "INVALID_TEST_PATHS")]
    if not set(tests) <= set(allowed_files):
        raise BlueprintCompilerError("TEST_PATH_OUTSIDE_ALLOWED_SCOPE")
    if any(
        not any(path == owner or path.startswith(owner.rstrip("/") + "/") for path in allowed_files)
        for owner in owner_paths
    ):
        raise BlueprintCompilerError("OWNER_PATH_OUTSIDE_ALLOWED_SCOPE")
    dependencies = _strings(raw.get("depends_on_module_ids", []), "INVALID_MODULE_DEPENDENCIES", nonempty=False)
    if any(dependency not in registered_modules for dependency in dependencies):
        raise BlueprintCompilerError("UNKNOWN_MODULE_DEPENDENCY")
    acceptance = _strings(raw.get("acceptance"), "INVALID_ACCEPTANCE_SET")
    validations = _strings(raw.get("validations"), "INVALID_VALIDATION_SET")
    if len(acceptance) > limits.max_acceptance_items_per_milestone:
        raise BlueprintCompilerError("ACCEPTANCE_SET_LIMIT_EXCEEDED")
    if len(validations) > limits.max_validation_items_per_milestone:
        raise BlueprintCompilerError("VALIDATION_SET_LIMIT_EXCEEDED")
    objective = milestone.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        raise BlueprintCompilerError("INVALID_MILESTONE_OBJECTIVE")
    return {
        "milestone_id": milestone_id,
        "objective": objective,
        "module_id": module_id,
        "module_version": module_version,
        "interface_id": interface_id,
        "interface_version": interface_version,
        "change_kind": change_kind,
        "natural_owner_paths": owner_paths,
        "allowed_files": allowed_files,
        "test_paths": tests,
        "depends_on_module_ids": dependencies,
        "acceptance": acceptance,
        "validations": validations,
    }


def _module_order(bindings: Sequence[Mapping[str, Any]]) -> list[str]:
    by_module = {str(binding["module_id"]): binding for binding in bindings}
    milestone_modules = set(by_module)
    indegree = {module_id: 0 for module_id in milestone_modules}
    children: dict[str, list[str]] = defaultdict(list)
    for module_id, binding in by_module.items():
        for provider in binding["depends_on_module_ids"]:
            if provider in milestone_modules:
                indegree[module_id] += 1
                children[provider].append(module_id)
    queue = deque(sorted(key for key, value in indegree.items() if value == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(milestone_modules):
        raise BlueprintCompilerError("MODULE_DEPENDENCY_CYCLE")
    return order


def _task_records(binding: Mapping[str, Any]) -> list[dict[str, Any]]:
    milestone_slug = str(binding["milestone_id"]).lower().replace("_", "-")
    records: list[dict[str, Any]] = []
    for suffix, role, node_kind, local_dependencies in _TASK_TEMPLATES:
        task_id = f"{milestone_slug}-{suffix}"
        records.append(
            {
                "task_id": task_id,
                "role": role,
                "node_kind": node_kind,
                "task_manifest": f"generated/{milestone_slug}/task_manifests/{task_id}.yaml",
                "change_plan": f"generated/{milestone_slug}/change_plans/{task_id}.yaml",
                "depends_on": [f"{milestone_slug}-{item}" for item in local_dependencies],
                "module_id": binding["module_id"],
                "allowed_files": list(binding["allowed_files"]),
                "activation": "on_failure" if node_kind == "rollback" else "normal",
            }
        )
    return records


def _validate_compiled_graph(
    graph: Mapping[str, Any],
    allowed_roles: set[str],
) -> dict[str, Any]:
    tasks = graph.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
    task_ids = {str(task.get("task_id")) for task in tasks if isinstance(task, Mapping)}
    if len(task_ids) != len(tasks) or "None" in task_ids:
        raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
    roles = {str(task.get("role")) for task in tasks if isinstance(task, Mapping)}
    if not roles <= allowed_roles or not {
        "evidence_collector",
        "policy_guard",
        "test_engineer",
        "audit_recorder",
    } <= roles:
        raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
    indegree = {task_id: 0 for task_id in task_ids}
    children: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        dependencies = task.get("depends_on")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) and item in task_ids for item in dependencies
        ):
            raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
        task_id = str(task["task_id"])
        for dependency in dependencies:
            if dependency == task_id:
                raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
            indegree[task_id] += 1
            children[dependency].append(task_id)
    queue = deque(sorted(key for key, value in indegree.items() if value == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(tasks):
        raise BlueprintCompilerError("COMPILED_TASK_GRAPH_INVALID")
    return {"status": "PASS", "task_count": len(tasks), "execution_order": order}


def compile_blueprint(
    blueprint: Mapping[str, Any],
    repository_context: Mapping[str, Any],
    module_registry: Mapping[str, Any],
    authorization_envelope: Mapping[str, Any],
    *,
    milestone_ids: Sequence[str],
    acceptance_requirements: Sequence[str],
    limits: BlueprintCompilerLimits | None = None,
) -> dict[str, Any]:
    """Return one deterministic bounded compilation result or fail closed."""

    bounded = limits or BlueprintCompilerLimits()
    bounded.validate()
    _authorization(authorization_envelope)
    tracked_paths = _repository_paths(repository_context)
    registered_modules = _registry_modules(module_registry)
    product_objective = blueprint.get("product_objective")
    milestones = blueprint.get("milestones")
    agents = blueprint.get("agents")
    if not isinstance(product_objective, Mapping) or not isinstance(product_objective.get("id"), str):
        raise BlueprintCompilerError("INVALID_PRODUCT_OBJECTIVE")
    if not isinstance(milestones, Mapping) or not isinstance(agents, Mapping):
        raise BlueprintCompilerError("INVALID_BLUEPRINT")
    selected = [_identifier(item, "INVALID_MILESTONE_ID") for item in milestone_ids]
    if not selected or len(selected) != len(set(selected)):
        raise BlueprintCompilerError("INVALID_MILESTONE_SELECTION")
    if len(selected) > bounded.max_milestones:
        raise BlueprintCompilerError("MILESTONE_LIMIT_EXCEEDED")
    global_acceptance = list(acceptance_requirements)
    if not global_acceptance or not all(isinstance(item, str) and item for item in global_acceptance):
        raise BlueprintCompilerError("INVALID_ACCEPTANCE_REQUIREMENTS")
    if len(global_acceptance) > bounded.max_acceptance_items_per_milestone:
        raise BlueprintCompilerError("ACCEPTANCE_SET_LIMIT_EXCEEDED")

    bindings: list[dict[str, Any]] = []
    for milestone_id in selected:
        milestone = milestones.get(milestone_id)
        if not isinstance(milestone, Mapping):
            raise BlueprintCompilerError("UNKNOWN_MILESTONE")
        bindings.append(
            _module_change(
                milestone_id,
                milestone,
                tracked_paths,
                registered_modules,
                bounded,
            )
        )
    module_ids = [str(binding["module_id"]) for binding in bindings]
    if len(module_ids) != len(set(module_ids)):
        raise BlueprintCompilerError("MULTIPLE_MILESTONES_CHANGE_ONE_MODULE")
    owner_claims: dict[str, str] = {}
    for binding in bindings:
        for path in binding["allowed_files"]:
            prior = owner_claims.setdefault(path, str(binding["module_id"]))
            if prior != binding["module_id"]:
                raise BlueprintCompilerError("OVERLAPPING_MILESTONE_SCOPE")

    module_order = _module_order(bindings)
    by_module = {str(binding["module_id"]): binding for binding in bindings}
    ordered_bindings = [by_module[module_id] for module_id in module_order]
    tasks = [task for binding in ordered_bindings for task in _task_records(binding)]
    task_by_id = {str(task["task_id"]): task for task in tasks}
    for binding in ordered_bindings:
        slug = str(binding["milestone_id"]).lower().replace("_", "-")
        evidence_task = task_by_id[f"{slug}-evidence"]
        for dependency in binding["depends_on_module_ids"]:
            if dependency not in by_module:
                continue
            dependency_slug = str(by_module[dependency]["milestone_id"]).lower().replace("_", "-")
            evidence_task["depends_on"].append(f"{dependency_slug}-audit")
    if len(tasks) > bounded.max_tasks:
        raise BlueprintCompilerError("TASK_LIMIT_EXCEEDED")
    graph = {
        "graph_id": "blueprint-" + _digest({"objective": product_objective, "milestones": selected})[:16],
        "phase": "BLUEPRINT_COMPILED_DEVELOPMENT",
        "tasks": tasks,
    }
    graph_validation = _validate_compiled_graph(graph, set(str(role) for role in agents))

    documents: list[dict[str, Any]] = []
    for binding in ordered_bindings:
        slug = str(binding["milestone_id"]).lower().replace("_", "-")
        base = {
            "milestone_id": binding["milestone_id"],
            "product_objective_ref": "product_objective",
            "module_id": binding["module_id"],
            "authority_effect": "none",
        }
        documents.extend(
            [
                {**base, "document_kind": "phase", "path": f"generated/{slug}/phase.yaml"},
                {**base, "document_kind": "module_contract", "path": f"generated/{slug}/module-contract.yaml"},
                {**base, "document_kind": "acceptance", "path": f"generated/{slug}/acceptance.yaml"},
            ]
        )
    result: dict[str, Any] = {
        "status": "PASS",
        "mode": "tool_system_bounded_blueprint_compile",
        "authority_effect": "none",
        "product_objective_id": product_objective["id"],
        "repository_snapshot": {
            key: repository_context["snapshot"][key]
            for key in ("head", "tree", "tracked_set_sha256", "context_sha256")
        },
        "limits": asdict(bounded),
        "milestone_order": [binding["milestone_id"] for binding in ordered_bindings],
        "module_order": module_order,
        "milestone_module_bindings": ordered_bindings,
        "module_dependency_dag": [
            {"module_id": binding["module_id"], "depends_on": binding["depends_on_module_ids"]}
            for binding in ordered_bindings
        ],
        "executable_task_dag": graph,
        "task_graph_validation": graph_validation,
        "generated_documents": documents,
        "acceptance_requirements": global_acceptance,
        "isolation_paths": sorted(owner_claims),
        "replacement_nodes": [
            binding["module_id"]
            for binding in ordered_bindings
            if binding["change_kind"] == "replace"
        ],
        "rollback_nodes": [task["task_id"] for task in tasks if task["node_kind"] == "rollback"],
        "side_effects": {
            "repository_reads": 0,
            "repository_writes": 0,
            "network_operations": 0,
            "provider_invocations": 0,
            "credential_accesses": 0,
        },
    }
    result["compilation_sha256"] = _digest(result)
    return result
