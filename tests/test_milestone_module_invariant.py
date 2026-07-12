from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
ACTIVE_GATES = ROOT / "examples" / "active_gates.yaml"
REPORT = ROOT / "docs" / "reports" / "p14mr_milestone_module_invariant.md"


def _blueprint() -> dict[str, object]:
    return load_yaml_file(BLUEPRINT)


def _invariant() -> dict[str, object]:
    return _blueprint()["milestone_module_invariant"]


def test_invariant_applies_only_to_tool_system_durable_modules() -> None:
    invariant = _invariant()

    assert invariant["id"] == "durable_module_and_milestone_change_boundary"
    assert invariant["contract_active"] is True
    assert "status" not in invariant
    assert set(invariant["applies_to"]) == {
        "tool_system_durable_modules",
        "tool_system_module_interfaces",
        "tool_system_module_dependency_boundaries",
        "tool_system_milestone_change_bindings",
    }
    assert invariant["module_definition"] == {
        "persistent_functional_boundary": True,
        "replaceable": True,
        "single_responsibility": True,
        "versioned_public_interface_required": True,
    }
    assert invariant["milestone_definition"] == {
        "controlled_change_and_acceptance_unit": True,
        "persistent_module_by_existence": False,
        "normally_changes_one_module_or_versioned_public_interface": True,
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
        "single_responsibility",
        "blueprint_objective_ref",
        "natural_owner_paths",
        "public_interface_version",
        "input_contract",
        "output_contract",
        "error_semantics",
        "externally_visible_side_effects",
        "code_boundary",
        "data_boundary",
        "test_boundary",
        "runtime_artifact_boundary",
        "cleanup_boundary",
        "upstream_dependency_module_ids_and_versions",
        "downstream_dependency_module_ids_and_versions",
        "content_hashes_and_expected_preconditions",
        "authorization_envelope",
        "acceptance_evidence",
        "rollback_evidence",
        "replacement_evidence",
    }


def test_fault_rules_do_not_create_unregistered_lifecycle_enums() -> None:
    invariant = _invariant()

    assert "lifecycle" not in invariant
    serialized = repr(invariant)
    for unregistered_state in (
        "DEFINED",
        "IMPLEMENTING",
        "VALIDATING",
        "INVALIDATED",
        "ISOLATED",
        "REVALIDATED",
        "RETIRED",
    ):
        assert unregistered_state not in serialized
    assert invariant["defect_disposition"] == {
        "implementation_defect_with_valid_contract": (
            "repair_inside_module_boundary_and_reaccept"
        ),
        "contract_or_blueprint_drift": (
            "isolate_module_stop_outputs_and_require_accepted_replacement"
        ),
    }


def test_failure_isolation_preserves_unrelated_modules() -> None:
    invariant = _invariant()

    assert invariant["failure_isolation"] == {
        "failed_or_drifted_module_isolated_from_active_output": True,
        "dependent_modules_pause_consumption_until_current_revalidation": True,
        "affected_downstream_dependency_closure_requires_revalidation": True,
        "unrelated_modules_and_acceptance_remain_valid": True,
        "hidden_dependency_discovery_expands_explicit_impact_set": True,
    }
    assert invariant["compatibility_replacement"] == {
        "replacement_module_requires_revalidation": True,
        "public_upstream_and_downstream_boundaries_require_revalidation": True,
        "affected_downstream_dependency_closure_requires_revalidation": True,
        "interface_compatible_replacement_changes_unaffected_modules": False,
        "unrelated_modules_and_acceptance_remain_valid": True,
        "direct_dependents_require_reimplementation_by_default": False,
        "interface_incompatible_change_requires_versioned_migration": True,
        "global_blueprint_change_requires_impacted_module_replanning": True,
        "shared_foundation_change_requires_explicit_blast_radius_review": True,
    }


def test_replacement_cleanup_and_downstream_authority_fail_closed() -> None:
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
    assert invariant["tooling_boundary"] == {
        "may_offer_tools_and_recommendations": True,
        "downstream_use_requires_downstream_authorization": True,
        "downstream_governance_authority": False,
        "may_change_downstream_owner_authority_status_or_write_authorization": False,
        "external_project_retroactive_mutation_automatic": False,
    }
    assert invariant["enforcement"] == {
        "current_contract_scope": "local_declaration_and_alignment_tests",
        "runtime_module_enforcement_implemented": False,
        "machine_alignment_tests_required": True,
        "module_graph_validation_required": True,
        "interface_compatibility_evidence_required": True,
        "fault_isolation_blast_radius_record_required": True,
        "blueprint_compiler_owner": "P14E_BLUEPRINT_COMPILER",
        "multi_project_acceptance_owner": "P15_MULTI_PROJECT_BENCHMARK",
    }


def test_local_authority_does_not_govern_other_repositories() -> None:
    blueprint = _blueprint()
    invariant = blueprint["milestone_module_invariant"]
    authority = invariant["authority_scope"]
    execution = blueprint["active_phase_execution"]
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert authority == {
        "repository": "tool-system",
        "governs_other_repositories": False,
        "may_offer_tools_and_recommendations": True,
        "may_change_downstream_owner_authority_status_or_write_authorization": False,
        "immutable_group_reference_effect": (
            "pinned_candidate_reference_pending_central_repo_check"
        ),
        "group_reference_created_by_this_change": True,
        "group_cutover_completed_by_this_change": False,
    }
    assert execution["authority_effect"] == "tool_system_local_only"
    assert "authorized_scope" not in execution
    assert "authorized_scope_role" not in execution
    assert "global_milestone_module_governance_only" not in execution.values()
    assert "compatibility_identifier_semantics" not in blueprint
    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["entry_requires"] == [
        "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT accepted",
        "explicit tool-system-local durable-module governance authorization",
    ]
    assert "explicit global milestone-module governance authorization" not in stages[
        "P14MR_MILESTONE_MODULE_INVARIANT"
    ]["entry_requires"]
    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["authority_effect"] == (
        "tool_system_local_only"
    )


def test_p14mr_report_is_acceptance_evidence_not_durable_rule_owner() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    execution = blueprint["active_phase_execution"]

    assert REPORT.is_file()
    assert execution["record"] == (
        "docs/reports/p14mr_milestone_module_invariant.md"
    )
    assert execution["record_role"] == "existing_acceptance_evidence_only"
    assert execution["durable_rule_owners"] == [
        "blueprint/tool_system_v0.yaml:milestone_module_invariant",
        (
            "docs/tool_system_global_development_principles_v1.md:"
            "durable_module_and_milestone_discipline"
        ),
    ]
    assert execution["authority_effect"] == "tool_system_local_only"


def test_process_inputs_remain_pending_separate_migration() -> None:
    boundary = _invariant()["process_migration_boundary"]
    active_gates = load_yaml_file(ACTIVE_GATES)

    assert boundary == {
        "reports_task_manifests_change_plans_active_gates_are_legacy_machine_inputs": True,
        "caller_and_reference_audit_complete": False,
        "group_process_file_compliance_claimed": False,
        "deletion_or_reclassification_authorized": False,
    }
    assert isinstance(active_gates["task_manifests"], list)
    assert active_gates["task_manifests"]
    assert all(isinstance(path, str) for path in active_gates["task_manifests"])
    assert isinstance(active_gates["change_plans"], list)
    assert active_gates["change_plans"]
    assert all(isinstance(path, str) for path in active_gates["change_plans"])


def test_p14mr_precedes_p14c_and_future_stages_own_enforcement() -> None:
    blueprint = _blueprint()
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}
    execution = blueprint["active_phase_execution"]

    assert blueprint["phase"] == "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
    assert blueprint["status"] == "active"
    assert execution["current_stage"] == "P14MR_MILESTONE_MODULE_INVARIANT"
    assert execution["record_role"] == "existing_acceptance_evidence_only"
    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["execution_boundary"] == (
        "governance_only"
    )
    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["authority_effect"] == (
        "tool_system_local_only"
    )
    assert stages["P14MR_MILESTONE_MODULE_INVARIANT"]["objective"] == (
        "reconcile tool-system milestone planning with durable replaceable "
        "capability modules without treating milestone packets as modules or "
        "governing downstream repositories"
    )
    assert "P14MR_MILESTONE_MODULE_INVARIANT accepted" in stages[
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    ]["entry_requires"]
    assert (
        "each benchmark project supplies its own explicitly authorized "
        "durable-module contract"
    ) in (
        blueprint["milestones"]["P15_MULTI_PROJECT_BENCHMARK"]["entry_requires"]
    )
    assert "durable_module_and_milestone_change_governance" in blueprint[
        "boundaries"
    ]["owns"]
    assert execution["next_stage"] == "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"
    assert execution["next_stage_authorized"] is False
    assert execution["live_model_provider_execution_authorized"] is False
