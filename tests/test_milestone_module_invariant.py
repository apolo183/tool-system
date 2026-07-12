from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
GLOBAL_PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
REPORT = ROOT / "docs" / "reports" / "p14mr_milestone_module_invariant.md"
MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14mr_milestone_module_invariant.yaml"
)


def _invariant() -> dict[str, object]:
    return load_yaml_file(BLUEPRINT)["milestone_module_invariant"]


def test_invariant_applies_to_every_controlled_project_and_milestone() -> None:
    invariant = _invariant()

    assert invariant["id"] == "replaceable_milestone_capability_modules"
    assert invariant["status"] == "active"
    assert set(invariant["applies_to"]) == {
        "tool_system",
        "every_project_generated_by_tool_system",
        "every_project_controlled_by_tool_system",
        "every_project_adopted_into_tool_system",
        "every_major_milestone",
        "every_sub_milestone",
    }
    assert invariant["project_architecture"] == {
        "module_graph_required": True,
        "dependency_graph_type": "directed_acyclic_graph",
        "one_active_implementation_per_module": True,
        "shared_foundations_minimized_and_versioned": True,
        "hidden_cross_module_dependencies_allowed": False,
        "direct_internal_state_access_across_modules_allowed": False,
    }


def test_every_module_has_a_versioned_auditable_contract() -> None:
    assert set(_invariant()["required_module_contract_fields"]) == {
        "module_id",
        "module_version",
        "blueprint_objective_ref",
        "direct_parent_refs",
        "natural_owner_paths",
        "input_contract",
        "output_contract",
        "public_interface",
        "dependency_module_ids_and_versions",
        "content_hashes_and_expected_preconditions",
        "authorization_envelope",
        "acceptance_tests_and_evidence",
        "invalidation_conditions",
        "rollback_and_cleanup_disposition",
        "replacement_or_supersession_ref",
    }


def test_module_lifecycle_separates_repair_from_drift_replacement() -> None:
    invariant = _invariant()

    assert invariant["lifecycle"] == {
        "states": [
            "DEFINED",
            "IMPLEMENTING",
            "VALIDATING",
            "ACCEPTED",
            "ACTIVE",
            "INVALIDATED",
            "ISOLATED",
            "REPLACED",
            "REVALIDATED",
            "RETIRED",
        ],
        "invalidated_module_may_remain_active": False,
        "replacement_activation_requires_acceptance": True,
        "active_swap_is_atomic": True,
    }
    assert invariant["defect_disposition"] == {
        "implementation_defect_with_valid_contract": (
            "repair_inside_module_boundary_and_reaccept"
        ),
        "contract_or_blueprint_drift": "invalidate_isolate_and_replace_module",
    }


def test_failure_isolation_preserves_unrelated_modules() -> None:
    invariant = _invariant()

    assert invariant["failure_isolation"] == {
        "invalid_module_removed_from_active_graph": True,
        "dependent_modules_blocked_until_revalidation": True,
        "descendant_acceptance_suspect_until_revalidated": True,
        "unrelated_modules_remain_active": True,
        "hidden_dependency_discovery_expands_explicit_impact_set": True,
    }
    assert invariant["compatibility_replacement"] == {
        "interface_compatible_replacement_changes_unaffected_modules": False,
        "direct_dependents_require_revalidation": True,
        "direct_dependents_require_reimplementation_by_default": False,
        "interface_incompatible_change_requires_versioned_migration": True,
        "global_blueprint_change_requires_impacted_module_replanning": True,
        "shared_foundation_change_requires_explicit_blast_radius_review": True,
    }


def test_replacement_cleanup_and_project_adoption_fail_closed() -> None:
    invariant = _invariant()

    assert invariant["replacement_and_cleanup"] == {
        "replacement_must_align_with_parent_and_global_blueprint": True,
        "replacement_must_pass_before_active_swap": True,
        "superseded_active_route_removed_after_replacement_acceptance": True,
        "parallel_active_mainlines_allowed": False,
        "audit_and_git_history_retained": True,
        "creator_owned_temporary_cleanup_required": True,
        "destructive_cleanup_requires_separate_authorization": True,
    }
    assert invariant["project_adoption_gate"] == {
        "inheritance_or_equivalent_embedded_contract_required": True,
        "missing_adoption_blocks_phase_entry_and_write": True,
        "adoption_verified_before_next_controlled_write": True,
        "existing_project_retroactive_mutation_automatic": False,
    }
    assert invariant["enforcement"] == {
        "machine_alignment_tests_required": True,
        "module_graph_validation_required": True,
        "interface_compatibility_evidence_required": True,
        "invalidation_blast_radius_record_required": True,
        "blueprint_compiler_owner": "P14E_BLUEPRINT_COMPILER",
        "multi_project_acceptance_owner": "P15_MULTI_PROJECT_BENCHMARK",
    }


def test_global_public_contracts_and_packet_agree() -> None:
    principles = GLOBAL_PRINCIPLES.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    manifest = load_yaml_file(MANIFEST)

    for text in (principles, agents, readme, report):
        assert "versioned" in text
        assert "module" in text.lower()
        assert "unaffected" in text
    assert "Hidden dependencies" in principles
    assert "whole-project rewrite" in principles
    assert "parallel active implementations" in readme
    assert "P14C" in report
    assert manifest["alignment"]["global"]["section_or_key"] == (
        "product_objective"
    )
    assert set(manifest["scope"]["out_of_scope"]) >= {
        "runtime source or policy changes",
        "automatic module replacement implementation",
        "modification of existing external projects",
        "P14C live provider, model, credential, network, or cost execution",
    }


def test_p14mr_precedes_p14c_and_future_stages_own_enforcement() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["execution_boundary"] == (
        "governance_only"
    )
    assert "P14MR_MILESTONE_MODULE_INVARIANT accepted" in stages[
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    ]["entry_requires"]
    assert "versioned milestone modules" in stages["P14E_BLUEPRINT_COMPILER"][
        "objective"
    ]
    assert "every benchmark project passes the milestone-module adoption gate" in (
        blueprint["milestones"]["P15_MULTI_PROJECT_BENCHMARK"]["entry_requires"]
    )
    assert "milestone_module_governance" in blueprint["boundaries"]["owns"]
