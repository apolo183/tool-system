from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
REPORT = ROOT / "docs" / "reports" / "p14a_blueprint_to_code_phase_entry_and_contract.md"
MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14a_blueprint_to_code_phase_entry.yaml"
)


def test_p14_stage_sequence_closes_each_missing_product_link() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    p14 = blueprint["milestones"]["P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"]

    assert [stage["stage"] for stage in p14["stage_plan"]] == [
        "P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION",
        "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT",
        "P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION",
        "P14D_REPOSITORY_CONTEXT_NATURAL_OWNER",
        "P14E_BLUEPRINT_COMPILER",
        "P14F_AUTONOMOUS_PATCH_TEST_REPAIR_REVIEW",
        "P14G_DURABLE_LOCAL_GIT_ORCHESTRATION",
        "P14H_MULTI_STACK_END_TO_END_FIXTURE_ACCEPTANCE",
        "P14I_ACCEPTANCE_CLOSURE",
    ]
    boundaries = {
        stage["stage"]: stage["execution_boundary"]
        for stage in p14["stage_plan"]
    }
    assert boundaries["P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION"] == (
        "governance_only"
    )
    assert boundaries["P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT"] == (
        "no_live_provider"
    )
    assert boundaries["P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"] == (
        "separately_authorized_live_provider_no_repository_mutation"
    )
    assert boundaries["P14G_DURABLE_LOCAL_GIT_ORCHESTRATION"] == (
        "isolated_local_git_only"
    )
    stages = {stage["stage"]: stage for stage in p14["stage_plan"]}
    assert stages["P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT"][
        "entry_requires"
    ] == [
        "P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION accepted",
        "explicit P14B source-implementation authorization",
    ]
    assert stages["P14C_BOUNDED_REAL_MODEL_PROVIDER_EXECUTION"][
        "entry_requires"
    ] == [
        "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT accepted",
        "named provider-model-network-credential-cost execution packet authorized",
    ]
    assert stages["P14I_ACCEPTANCE_CLOSURE"]["entry_requires"] == [
        "P14H_MULTI_STACK_END_TO_END_FIXTURE_ACCEPTANCE accepted"
    ]


def test_p14_acceptance_fixtures_and_claim_are_bounded() -> None:
    p14 = load_yaml_file(BLUEPRINT)["milestones"][
        "P14_BLUEPRINT_TO_CODE_AUTONOMOUS_DEVELOPMENT"
    ]

    assert set(p14["required_acceptance_fixtures"]) == {
        "greenfield_python_cli",
        "existing_python_library_natural_owner_change",
        "typescript_package_language_neutral_flow",
        "bounded_failing_test_repair",
        "ambiguous_blueprint_pre_mutation_block",
        "out_of_scope_patch_block_and_rollback",
        "timeout_cancellation_cleanup_and_resume",
        "completed_side_effect_crash_without_duplicate_replay",
        "local_git_conflict_policy",
        "deterministic_content_addressed_replay",
    }
    assert "isolated repository fixture" in p14["accepted_claim"]
    assert "local Git software change" in p14["accepted_claim"]


def test_phase_entry_authorizes_specification_but_not_implementation() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    execution = blueprint["active_phase_execution"]
    manifest = load_yaml_file(MANIFEST)

    assert execution == {
        "record": "docs/reports/p14a_blueprint_to_code_phase_entry_and_contract.md",
        "current_stage": "P14A_PHASE_ENTRY_END_TO_END_SPECIFICATION",
        "phase_entry_authorized": True,
        "authorized_scope": "governance_and_end_to_end_specification_only",
        "phase_source_implementation_authorized": False,
        "next_stage": "P14B_PROVIDER_NEUTRAL_AI_WORKER_CONTRACT",
        "next_stage_authorized": False,
        "live_model_provider_execution_authorized": False,
        "remote_target_mutation_authorized": False,
        "production_deployment_authorized": False,
    }
    assert manifest["alignment"]["global"]["section_or_key"] == (
        "product_objective"
    )
    assert set(manifest["scope"]["out_of_scope"]) >= {
        "policy or runtime source changes",
        "P14B or later implementation",
        "model/provider network calls or credentials",
        "finance-us or any target-repository mutation",
    }


def test_capability_gap_record_names_current_audited_limitations() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for marker in (
        "requirement_graph.py",
        "NoMutationAgentWorker",
        "DryRunWorkerAdapter",
        "role_runtime.py",
        "patch/test/repair loop",
        "durable SQLite exists",
        "no accepted fixture proves blueprint through code",
    ):
        assert marker in report
