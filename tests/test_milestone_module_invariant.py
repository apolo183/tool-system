from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
REPORT = ROOT / "docs" / "reports" / "p14mr_milestone_module_invariant.md"


def _blueprint() -> dict[str, object]:
    return load_yaml_file(BLUEPRINT)


def _invariant() -> dict[str, object]:
    return _blueprint()["milestone_module_invariant"]


def test_invariant_applies_only_to_tool_system_durable_modules() -> None:
    invariant = _invariant()

    assert invariant["id"] == "durable_module_and_milestone_change_boundary"
    assert invariant["required"] is True
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
        "module_registry_path": "config/module_registry_v1.yaml",
        "module_registry_schema_path": "config/module_registry_schema_v1.json",
        "required_validations": [
            "module_registry_structure",
            "declared_dependency_dag",
            "natural_owner_overlap",
            "source_ownership_coverage",
            "source_import_edges",
            "contract_reference_hashes",
            "side_effect_target_bindings",
        ],
        "runtime_module_enforcement_required": True,
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
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}

    assert authority == {
        "repository": "tool-system",
        "governs_other_repositories": False,
        "may_offer_tools_and_recommendations": True,
        "may_change_downstream_owner_authority_status_or_write_authorization": False,
    }
    assert "active_phase_execution" not in blueprint
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
    project_state = load_yaml_file(PROJECT_STATE)
    current_phase = project_state["current_phase"]

    assert REPORT.is_file()
    assert project_state["prior_acceptance"]["phase"] == (
        "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
    )
    assert project_state["p14i"]["acceptance_status"] == "accepted_and_closed"
    assert current_phase["last_accepted_stage_record"] == (
        "docs/reports/p15b_adapter_router_profiler_fixture_acceptance.md"
    )
    assert current_phase["last_accepted_stage"] == (
        "P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES"
    )
    assert project_state["authority_effect"] == "none"


def test_process_authority_boundary_is_stable_and_non_authorizing() -> None:
    boundary = _invariant()["process_authority_boundary"]

    assert boundary == {
        "process_authority_contract_path": "config/process_authority_v1.yaml",
        "canonical_replay_snapshot_path": "config/replay_snapshot_v1.yaml",
        "repository_manifest_path": "REPO_MANIFEST.md",
        "task_authority_mode": "explicit_manifest_change_plan_pair",
        "implicit_repository_index_allowed": False,
        "replay_inputs_grant_authority": False,
        "retained_evidence_grants_authority": False,
        "destructive_disposition_requires_separate_authorization": True,
    }


def test_p14mr_precedes_p14c_and_future_stages_own_enforcement() -> None:
    blueprint = _blueprint()
    project_state = load_yaml_file(PROJECT_STATE)
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}
    current_phase = project_state["current_phase"]

    assert "phase" not in blueprint
    assert "status" not in blueprint
    assert current_phase["id"] == "P15_MULTI_PROJECT_BENCHMARK"
    assert current_phase["last_accepted_stage"] == (
        "P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES"
    )
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
    assert project_state["prior_acceptance"]["phase"] == (
        "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
    )
    assert project_state["p14i"]["acceptance_status"] == "accepted_and_closed"
    assert current_phase["status"] == "active"
    assert current_phase["next_stage"] == (
        "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK"
    )
    assert current_phase["next_stage_authorized"] is False
    assert current_phase["next_phase"] == "P16_PRODUCTION_OPERATIONS_ACCEPTANCE"
    assert current_phase["next_phase_entry_authorized"] is False
    assert (
        project_state["authorization_boundaries"]
        ["live_model_provider_execution_authorized"]
        is False
    )
