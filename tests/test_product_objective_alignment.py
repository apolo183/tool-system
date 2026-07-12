from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
P14R_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14r_blueprint_product_objective_roadmap_reconciliation.yaml"
)


def test_product_objective_controls_the_end_to_end_flow() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    objective = blueprint["product_objective"]
    contract = blueprint["product_contract"]
    alignment = blueprint["global_alignment"]

    assert blueprint["schema_version"] == 0.4
    assert objective["id"] == "blueprint_driven_autonomous_software_development"
    assert set(objective["required_end_to_end_flow"]) == {
        "ingest_approved_blueprint",
        "inspect_repository_state",
        "build_repository_context",
        "decompose_milestones",
        "generate_task_dag",
        "generate_phase_documents",
        "generate_task_manifests",
        "generate_change_plans",
        "identify_natural_owners",
        "invoke_bounded_real_ai_worker",
        "implement_code_changes",
        "validate_file_scope",
        "run_tests",
        "diagnose_failures",
        "repair_with_bounded_retry",
        "review_parent_alignment",
        "review_global_product_objective_alignment",
        "create_local_git_commits",
        "produce_draft_pull_request_plan",
        "prepare_separately_authorized_repository_publish_action",
        "produce_acceptance_evidence",
        "close_completed_milestones",
    }
    assert "approved_project_blueprint" in contract["inputs"]
    assert "authorization_envelope" in contract["inputs"]
    assert "bounded_code_patches" in contract["outputs"]
    assert "separately_authorized_draft_pull_request" in contract["outputs"]
    assert "acceptance_and_closure_record" in contract["outputs"]
    assert alignment == {
        "required_for_every_milestone": True,
        "required_for_every_task_manifest": True,
        "required_for_every_change_plan": True,
        "required_for_every_acceptance_record": True,
        "require_direct_parent_alignment": True,
        "require_global_product_objective_alignment": True,
        "product_objective_ref": "product_objective",
        "fail_closed_on_missing_alignment": True,
    }


def test_completion_and_non_goals_prevent_false_product_claims() -> None:
    objective = load_yaml_file(BLUEPRINT)["product_objective"]

    assert set(objective["completion_definition"]) >= {
        "approved_blueprint_converts_to_executable_task_graph",
        "bounded_projects_complete_end_to_end_in_isolated_repositories",
        "real_ai_worker_performs_controlled_implementation_and_repair",
        "every_milestone_proves_parent_and_global_objective_alignment",
        "failed_runs_stop_or_rollback_without_silent_scope_expansion",
    }
    assert set(objective["non_goals"]) >= {
        "unrestricted_remote_repository_mutation",
        "autonomous_production_deployment",
        "bypassing_human_authorization_boundaries",
        "claiming_codex_replacement_without_independent_evidence",
    }


def test_successor_chain_builds_product_before_benchmark_and_operations() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    milestones = blueprint["milestones"]
    p14 = milestones["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    p15 = milestones["P15_MULTI_PROJECT_BENCHMARK"]
    p16 = milestones["P16_PRODUCTION_OPERATIONS_ACCEPTANCE"]

    assert "P14_MULTI_REPO_BENCHMARK" not in milestones
    assert "P15_PRODUCTION_OPERATIONS_ACCEPTANCE" not in milestones
    assert "P13_SECURITY_RELIABILITY_HARDENING accepted" in p14["entry_requires"]
    assert "explicit P14 phase-entry authorization" in p14["entry_requires"]
    assert "implementation begins in isolated local fixture repositories only" in (
        p14["entry_requires"]
    )
    assert "autonomous patch-test-diagnose-repair-review loop" in p14["outputs"]
    assert "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT accepted" in (
        p15["entry_requires"]
    )
    assert "each real repository mutation separately authorized" in (
        p15["entry_requires"]
    )
    assert "P15_MULTI_PROJECT_BENCHMARK accepted" in p16["entry_requires"]
    assert "production deployment remains separately approved only" in (
        p16["entry_requires"]
    )


def test_public_contracts_and_p14r_manifest_reference_global_objective() -> None:
    readme = README.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    manifest = load_yaml_file(P14R_MANIFEST)

    assert "permanent product objective" in readme
    assert "P14 Blueprint-to-Code Autonomous Development" in readme
    assert "permanent product objective" in agents
    assert "product_objective" in agents
    assert manifest["alignment"]["global"] == {
        "document": "blueprint/tool_system_v0.yaml",
        "section_or_key": "product_objective",
        "scope": (
            "Make bounded blueprint-to-code autonomous development the permanent "
            "global objective controlling P14-P16."
        ),
    }
    assert set(manifest["scope"]["out_of_scope"]) >= {
        "policy or runtime source changes",
        "P14 phase entry or implementation",
    }
