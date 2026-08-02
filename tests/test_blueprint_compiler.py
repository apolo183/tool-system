from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tool_system.blueprint_compiler import (
    BlueprintCompilerError,
    BlueprintCompilerLimits,
    compile_blueprint,
)
from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.planner.task_graph import validate_task_graph


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "examples/task_manifests/tool_system_p14e_blueprint_compiler_v1.yaml"
PLAN = ROOT / "examples/change_plans/tool_system_p14e_blueprint_compiler_v1.yaml"
POLICY = ROOT / "policy/repo_write_policy.yaml"
AUTONOMY = ROOT / "policy/autonomy_policy.yaml"
P14E_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/blueprint-compiler-contract-v1.md",
    "docs/reports/p14e_blueprint_compiler_acceptance.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p14e_blueprint_compiler_v1.yaml",
    "examples/task_manifests/tool_system_p14e_blueprint_compiler_v1.yaml",
    "src/tool_system/blueprint_compiler/__init__.py",
    "src/tool_system/blueprint_compiler/compiler.py",
    "tests/test_blueprint_compiler.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_module_contracts.py",
    "tests/test_module_registry.py",
    "tests/test_p14_phase_entry_contract.py",
    "tests/test_p14c_execution_contract.py",
    "tests/test_phase_alignment.py",
    "tests/test_repo_manifest.py",
    "tests/test_repository_context_builder.py",
}


def _agents() -> dict[str, dict[str, str]]:
    return {
        role: {"role": role}
        for role in (
            "evidence_collector",
            "policy_guard",
            "blueprint_architect",
            "change_planner",
            "patch_author",
            "test_engineer",
            "code_reviewer",
            "contract_reviewer",
            "audit_recorder",
        )
    }


def _change(module_id: str = "billing", *, kind: str = "add") -> dict[str, object]:
    return {
        "module_id": module_id,
        "module_version": "1.0.0",
        "interface_id": f"{module_id}-api",
        "interface_version": "1.0.0",
        "change_kind": kind,
        "natural_owner_paths": [f"src/{module_id}"],
        "allowed_files": [f"src/{module_id}/service.py", f"tests/test_{module_id}.py"],
        "test_paths": [f"tests/test_{module_id}.py"],
        "depends_on_module_ids": [],
        "acceptance": [f"{module_id} behavior passes"],
        "validations": [f"pytest tests/test_{module_id}.py"],
    }


def _blueprint() -> dict[str, object]:
    return {
        "product_objective": {"id": "bounded-fixture", "statement": "build fixture"},
        "agents": _agents(),
        "milestones": {
            "M1_BILLING": {
                "objective": "add bounded billing",
                "module_change": _change(),
            }
        },
    }


def _context() -> dict[str, object]:
    return {
        "status": "PASS",
        "snapshot": {
            "head": "1" * 40,
            "tree": "2" * 40,
            "tracked_set_sha256": "3" * 64,
            "context_sha256": "4" * 64,
            "clean_worktree": True,
        },
        "repository_index": [
            {"path": "blueprint.yaml"},
            {"path": "GOVERNANCE.md"},
            {"path": "src/existing.py"},
            {"path": "tests/test_existing.py"},
        ],
        "natural_owner_proposal": {
            "authority_effect": "none",
            "owner_path": "src",
        },
    }


def _registry(*module_ids: str) -> dict[str, object]:
    return {
        "modules": [
            {"module_id": module_id, "module_version": "1.0.0"}
            for module_id in module_ids
        ]
    }


def _authorization() -> dict[str, bool]:
    return {
        "blueprint_approved": True,
        "isolated_fixture_repositories_only": True,
        "target_repo_mutation_authorized": False,
        "provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
    }


def _compile(**overrides: object) -> dict[str, object]:
    arguments: dict[str, object] = {
        "blueprint": _blueprint(),
        "repository_context": _context(),
        "module_registry": _registry("existing"),
        "authorization_envelope": _authorization(),
        "milestone_ids": ("M1_BILLING",),
        "acceptance_requirements": ("all milestone acceptance passes",),
    }
    arguments.update(overrides)
    return compile_blueprint(**arguments)  # type: ignore[arg-type]


def test_compiler_is_deterministic_bounded_and_task_graph_compatible() -> None:
    first = _compile()
    second = _compile()

    assert first == second
    assert first["status"] == "PASS"
    assert first["authority_effect"] == "none"
    assert first["milestone_order"] == ["M1_BILLING"]
    assert first["module_order"] == ["billing"]
    assert first["task_graph_validation"]["status"] == "PASS"
    assert validate_task_graph(first["executable_task_dag"], _blueprint())["status"] == "PASS"
    tasks = first["executable_task_dag"]["tasks"]
    assert len(tasks) == 10
    assert {task["role"] for task in tasks} >= {
        "evidence_collector",
        "policy_guard",
        "test_engineer",
        "audit_recorder",
    }
    assert first["rollback_nodes"] == ["m1-billing-rollback"]
    assert len(first["compilation_sha256"]) == 64
    assert first["side_effects"] == {
        "repository_reads": 0,
        "repository_writes": 0,
        "network_operations": 0,
        "provider_invocations": 0,
        "credential_accesses": 0,
    }


def test_compiler_orders_selected_module_changes_by_dependency() -> None:
    blueprint = _blueprint()
    blueprint["milestones"] = {
        "M1_CORE": {"objective": "modify core", "module_change": _change("core", kind="modify")},
        "M2_UI": {"objective": "modify ui", "module_change": _change("ui", kind="modify")},
    }
    blueprint["milestones"]["M1_CORE"]["module_change"]["allowed_files"] = ["src/existing.py"]
    blueprint["milestones"]["M1_CORE"]["module_change"]["test_paths"] = ["src/existing.py"]
    blueprint["milestones"]["M1_CORE"]["module_change"]["natural_owner_paths"] = ["src"]
    blueprint["milestones"]["M2_UI"]["module_change"]["allowed_files"] = ["tests/test_existing.py"]
    blueprint["milestones"]["M2_UI"]["module_change"]["test_paths"] = ["tests/test_existing.py"]
    blueprint["milestones"]["M2_UI"]["module_change"]["natural_owner_paths"] = ["tests"]
    blueprint["milestones"]["M2_UI"]["module_change"]["depends_on_module_ids"] = ["core"]

    result = _compile(
        blueprint=blueprint,
        module_registry=_registry("core", "ui"),
        milestone_ids=("M2_UI", "M1_CORE"),
    )

    assert result["module_order"] == ["core", "ui"]
    assert result["milestone_order"] == ["M1_CORE", "M2_UI"]
    assert len(result["executable_task_dag"]["tasks"]) == 20
    tasks = {
        task["task_id"]: task
        for task in result["executable_task_dag"]["tasks"]
    }
    assert tasks["m2-ui-evidence"]["depends_on"] == ["m1-core-audit"]


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("unapproved", "AUTHORIZATION_ENVELOPE_BLOCKED"),
        ("context-block", "REPOSITORY_CONTEXT_NOT_ACCEPTED"),
        ("owner-authority", "OWNER_PROPOSAL_MUST_BE_NON_AUTHORIZING"),
        ("missing-binding", "MISSING_MODULE_CHANGE_BINDING"),
        ("unknown-dependency", "UNKNOWN_MODULE_DEPENDENCY"),
        ("modify-absent", "MODULE_CHANGE_PRECONDITION_FAILED"),
        ("unsafe-path", "INVALID_REPOSITORY_PATH"),
    ],
)
def test_fail_closed_input_boundaries(mutation: str, code: str) -> None:
    blueprint = _blueprint()
    context = _context()
    authorization = _authorization()
    registry = _registry("existing")
    if mutation == "unapproved":
        authorization["blueprint_approved"] = False
    elif mutation == "context-block":
        context["status"] = "BLOCK"
    elif mutation == "owner-authority":
        context["natural_owner_proposal"]["authority_effect"] = "execution"
    elif mutation == "missing-binding":
        del blueprint["milestones"]["M1_BILLING"]["module_change"]
    elif mutation == "unknown-dependency":
        blueprint["milestones"]["M1_BILLING"]["module_change"]["depends_on_module_ids"] = ["missing"]
    elif mutation == "modify-absent":
        blueprint["milestones"]["M1_BILLING"]["module_change"]["change_kind"] = "modify"
    elif mutation == "unsafe-path":
        blueprint["milestones"]["M1_BILLING"]["module_change"]["allowed_files"] = ["../escape.py"]

    with pytest.raises(BlueprintCompilerError, match=code):
        _compile(
            blueprint=blueprint,
            repository_context=context,
            authorization_envelope=authorization,
            module_registry=registry,
        )


def test_cycle_overlap_and_finite_limits_block() -> None:
    blueprint = _blueprint()
    blueprint["milestones"] = {
        "M1_A": {"objective": "modify a", "module_change": _change("a", kind="modify")},
        "M2_B": {"objective": "modify b", "module_change": _change("b", kind="modify")},
    }
    for milestone in blueprint["milestones"].values():
        milestone["module_change"]["allowed_files"] = ["src/existing.py"]
        milestone["module_change"]["test_paths"] = ["src/existing.py"]
        milestone["module_change"]["natural_owner_paths"] = ["src"]
    blueprint["milestones"]["M1_A"]["module_change"]["depends_on_module_ids"] = ["b"]
    blueprint["milestones"]["M2_B"]["module_change"]["depends_on_module_ids"] = ["a"]
    with pytest.raises(BlueprintCompilerError, match="OVERLAPPING_MILESTONE_SCOPE"):
        _compile(
            blueprint=blueprint,
            module_registry=_registry("a", "b"),
            milestone_ids=("M1_A", "M2_B"),
        )

    nonoverlap = copy.deepcopy(blueprint)
    nonoverlap["milestones"]["M2_B"]["module_change"]["allowed_files"] = ["tests/test_existing.py"]
    nonoverlap["milestones"]["M2_B"]["module_change"]["test_paths"] = ["tests/test_existing.py"]
    nonoverlap["milestones"]["M2_B"]["module_change"]["natural_owner_paths"] = ["tests"]
    with pytest.raises(BlueprintCompilerError, match="MODULE_DEPENDENCY_CYCLE"):
        _compile(
            blueprint=nonoverlap,
            module_registry=_registry("a", "b"),
            milestone_ids=("M1_A", "M2_B"),
        )

    with pytest.raises(BlueprintCompilerError, match="TASK_LIMIT_EXCEEDED"):
        _compile(limits=BlueprintCompilerLimits(max_tasks=9))


def test_p14e_manifest_and_plan_freeze_exact_scope() -> None:
    manifest_result = validate_task_manifest(MANIFEST, POLICY, AUTONOMY)
    plan_result = validate_change_plan(PLAN)
    manifest = load_yaml_file(MANIFEST)
    plan = load_yaml_file(PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P14E_FILES
    assert set(plan["changed_files"]) == P14E_FILES
    assert len(P14E_FILES) == 20
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["publication"]["ready_authorized"] is True
    assert manifest["publication"]["squash_merge_authorized"] is True
    assert manifest["scope"]["out_of_scope"] == [
        "P14F or later-stage implementation",
        "real downstream repository access or mutation",
        "provider execution or credential-value access",
        "production, cleanup, rollback execution, or branch deletion",
    ]
