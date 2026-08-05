from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.provider_portfolio import (
    CycleObservation,
    EconomicCandidate,
    FailureClass,
    FailureControlAction,
    FailureControlRequest,
    NoProgressStatus,
    PortfolioFixtureError,
    ProviderAuthorizationState,
    ProviderAvailabilityState,
    ProviderModeRoute,
    ProviderModeSnapshot,
    RouteDecision,
    RouteDecisionStatus,
    RouteEvaluation,
    TotalEconomicCost,
    build_module_isolation_plan,
    evaluate_no_progress,
    plan_failure_control,
    select_lowest_total_economic_cost,
    select_provider_mode_route,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "config/p15d_failure_economics_corpus_prerequisite_v1.yaml"
PROJECT_STATE = ROOT / "docs/tool_system_project_state_v1.yaml"
REPORT = (
    ROOT / "docs/reports/p15d_prerequisite_failure_control_fixture_implementation.md"
)
MANIFEST = (
    ROOT
    / "examples/task_manifests/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml"
)
PLAN = (
    ROOT
    / "examples/change_plans/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml"
)
REPO_WRITE_POLICY = ROOT / "policy/repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy/autonomy_policy.yaml"
EXACT_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15d_prerequisite_failure_control_fixture_implementation.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml",
    "examples/task_manifests/tool_system_p15d_prerequisite_failure_control_fixture_v1.yaml",
    "src/tool_system/provider_portfolio/__init__.py",
    "src/tool_system/provider_portfolio/failure_control.py",
    "tests/test_module_registry.py",
    "tests/test_provider_portfolio_failure_control.py",
    "tests/test_repo_manifest.py",
}
ROUTE_ALPHA = "fixture-alpha/model-v1@1.0.0"
ROUTE_BETA = "fixture-beta/model-v1@1.0.0"
ROUTE_GAMMA = "fixture-gamma/model-v1@1.0.0"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _route_decision() -> RouteDecision:
    evaluations = tuple(
        RouteEvaluation(
            route_id=route_id,
            eligible=True,
            hard_floor_reasons=(),
            expected_total_economic_cost_microunits=cost,
            logical_duration_ms=10,
            strength_rank=strength,
        )
        for route_id, cost, strength in (
            (ROUTE_ALPHA, 100, 1),
            (ROUTE_BETA, 120, 1),
            (ROUTE_GAMMA, 200, 2),
        )
    )
    return RouteDecision(
        status=RouteDecisionStatus.SELECTED,
        policy_version="fixture-failure-policy-v1",
        catalog_version="fixture-catalog-v1",
        authorization_id="fixture-authorization-v1",
        profile_sha256=_sha("profile"),
        selected_route_id=ROUTE_ALPHA,
        ordered_eligible_route_ids=(ROUTE_ALPHA, ROUTE_BETA, ROUTE_GAMMA),
        availability_failover_route_ids=(ROUTE_BETA, ROUTE_GAMMA),
        quality_escalation_route_ids=(ROUTE_GAMMA,),
        same_route_repair_limit=1,
        evaluations=evaluations,
        stop_reason=None,
        evidence_sha256=_sha("route-decision"),
    )


def _request(
    failure_class: FailureClass,
    *,
    current_route_id: str = ROUTE_ALPHA,
    attempted_route_ids: tuple[str, ...] = (ROUTE_ALPHA,),
    total_attempts: int = 1,
    max_attempts: int = 3,
    same_route_repair_attempts: int = 0,
    no_progress_decision=None,
) -> FailureControlRequest:
    return FailureControlRequest(
        route_decision=_route_decision(),
        failure_class=failure_class,
        current_route_id=current_route_id,
        attempted_route_ids=attempted_route_ids,
        total_attempts=total_attempts,
        max_attempts=max_attempts,
        same_route_repair_attempts=same_route_repair_attempts,
        no_progress_decision=no_progress_decision,
    )


def _provider_mode_decision():
    return select_provider_mode_route(
        ProviderModeSnapshot(
            configuration_version="operator-snapshot-v1",
            policy_version="provider-mode-policy-v1",
            authorization_id="provider-mode-authorization-v1",
            routes=(
                ProviderModeRoute(
                    provider_id="fixture-alpha",
                    requested_model_id="moving-model",
                    enabled=True,
                    availability_state=ProviderAvailabilityState.AVAILABLE,
                    provider_data_transfer_authorized=True,
                    adapter_fake_io_contract_passed=True,
                    provider_budget_microunits=1_000,
                    reserved_cost_microunits=100,
                    logical_duration_ms=10,
                    strength_rank=1,
                ),
                ProviderModeRoute(
                    provider_id="fixture-beta",
                    requested_model_id="fallback-model",
                    enabled=True,
                    availability_state=ProviderAvailabilityState.AVAILABLE,
                    provider_data_transfer_authorized=True,
                    adapter_fake_io_contract_passed=True,
                    provider_budget_microunits=1_000,
                    reserved_cost_microunits=120,
                    logical_duration_ms=20,
                    strength_rank=2,
                ),
            ),
            api_mode_enabled=True,
            authorization_state=ProviderAuthorizationState.ACTIVE,
            policy_preconditions_current=True,
            source_preconditions_current=True,
            total_budget_microunits=2_000,
            max_attempts=2,
            max_retries=0,
        )
    )


def _cycle(
    attempt_number: int,
    *,
    tree: str,
    blockers: tuple[str, ...] = ("acceptance-blocked",),
    satisfied: tuple[str, ...] = (),
    material: str = "unchanged-material-result",
) -> CycleObservation:
    return CycleObservation(
        task_digest_sha256=_sha("frozen-task"),
        candidate_tree_sha256=_sha(tree),
        acceptance_digest_sha256=_sha("frozen-acceptance"),
        blocker_ids=blockers,
        satisfied_acceptance_items=satisfied,
        validation_results=("focused-tests-pass",),
        material_acceptance_result_sha256=_sha(material),
        attempt_number=attempt_number,
    )


def _small_cost(total: int) -> TotalEconomicCost:
    return TotalEconomicCost(
        provider_usage=total,
        subscription_or_renewal_allocation=0,
        critical_path_time=0,
        local_compute_and_electricity=0,
        verification=0,
        retry=0,
        rework=0,
        recovery=0,
        rollback=0,
        opportunity_cost=0,
    )


def test_failure_control_consumes_selected_provider_mode_decision_without_dispatch() -> None:
    route_decision = _provider_mode_decision()
    selected_route = "fixture-alpha/moving-model"
    fallback_route = "fixture-beta/fallback-model"

    decision = plan_failure_control(
        FailureControlRequest(
            route_decision=route_decision,
            failure_class=FailureClass.PROVIDER_OUTAGE,
            current_route_id=selected_route,
            attempted_route_ids=(selected_route,),
            total_attempts=1,
            max_attempts=2,
            same_route_repair_attempts=0,
        )
    )

    assert decision.action is FailureControlAction.AVAILABILITY_FAILOVER
    assert decision.planned_route_id == fallback_route
    assert decision.provider_switch_planned is True
    assert decision.dispatch_authorized is False
    assert decision.candidate_application_authorized is False
    assert decision.authority_effect == "none"


def test_failure_control_distinguishes_bounded_actions_without_dispatch() -> None:
    availability = plan_failure_control(_request(FailureClass.RATE_LIMIT))
    repair = plan_failure_control(_request(FailureClass.QUALITY_REJECTED))
    escalation = plan_failure_control(
        _request(
            FailureClass.QUALITY_REJECTED,
            total_attempts=2,
            same_route_repair_attempts=1,
        )
    )
    blocked = plan_failure_control(_request(FailureClass.DATA_POLICY_DENIED))
    cancelled = plan_failure_control(_request(FailureClass.CANCELLED))
    exhausted = plan_failure_control(
        _request(
            FailureClass.RATE_LIMIT,
            current_route_id=ROUTE_GAMMA,
            attempted_route_ids=(ROUTE_ALPHA, ROUTE_BETA, ROUTE_GAMMA),
            total_attempts=3,
            max_attempts=3,
        )
    )

    assert availability.action is FailureControlAction.AVAILABILITY_FAILOVER
    assert availability.planned_route_id == ROUTE_BETA
    assert availability.provider_switch_planned is True
    assert repair.action is FailureControlAction.SAME_ROUTE_REPAIR
    assert repair.planned_route_id == ROUTE_ALPHA
    assert repair.same_route_repair_planned is True
    assert escalation.action is FailureControlAction.QUALITY_ESCALATION
    assert escalation.planned_route_id == ROUTE_GAMMA
    assert escalation.stronger_route_escalation_planned is True
    assert blocked.action is FailureControlAction.BLOCK_NO_PROVIDER_BYPASS
    assert blocked.planned_route_id is None
    assert cancelled.action is FailureControlAction.STOP
    assert "before dispatch or candidate application" in cancelled.stable_reason
    assert exhausted.action is FailureControlAction.STOP
    assert "attempt envelope is exhausted" in exhausted.stable_reason
    assert plan_failure_control(_request(FailureClass.RATE_LIMIT)) == availability

    for decision in (
        availability,
        repair,
        escalation,
        blocked,
        cancelled,
        exhausted,
    ):
        record = decision.to_record()
        assert decision.dispatch_authorized is False
        assert decision.candidate_application_authorized is False
        assert decision.authority_effect == "none"
        assert set(record["operations"].values()) == {0}
        assert len(decision.evidence_sha256) == 64


def test_recurrence_fingerprint_and_two_cycle_no_progress_stop_are_exact() -> None:
    first = _cycle(1, tree="tree-a")
    repeated_attempt = replace(first, attempt_number=2)
    repeated = evaluate_no_progress((first, repeated_attempt))

    assert first.recurrence_fingerprint == repeated_attempt.recurrence_fingerprint
    assert repeated.status is NoProgressStatus.STOPPED_REPEATED_FINGERPRINT
    assert repeated.terminal is True

    distinct = evaluate_no_progress(
        (
            _cycle(1, tree="tree-a"),
            _cycle(2, tree="tree-b"),
            _cycle(3, tree="tree-c"),
        )
    )
    assert distinct.status is NoProgressStatus.STOPPED_TWO_CYCLES
    assert distinct.consecutive_no_progress_cycles == 2

    progress = evaluate_no_progress(
        (
            _cycle(1, tree="tree-a", blockers=("a", "b")),
            _cycle(2, tree="tree-b", blockers=("a",)),
        )
    )
    assert progress.status is NoProgressStatus.CONTINUE
    assert progress.terminal is False

    stop = plan_failure_control(
        _request(FailureClass.NO_PROGRESS, no_progress_decision=distinct)
    )
    assert stop.action is FailureControlAction.STOP
    assert stop.terminal is True
    assert "two consecutive" in stop.stable_reason

    with pytest.raises(
        PortfolioFixtureError,
        match="terminal no-progress decision",
    ):
        _request(FailureClass.NO_PROGRESS, no_progress_decision=progress)


def test_isolation_plan_stops_only_affected_output_and_never_executes_rollback() -> (
    None
):
    plan = build_module_isolation_plan(
        failed_module_id="adaptive-model-portfolio-and-economics",
        affected_downstream_module_ids=("future-portfolio-consumer",),
        unrelated_module_ids=("architecture-registry", "manifest-validation"),
        rollback_reference="tool-system@ca04839:portfolio@1.2.0",
    )
    record = plan.to_record()

    assert record["stopped_output_module_ids"] == [
        "adaptive-model-portfolio-and-economics"
    ]
    assert record["paused_downstream_module_ids"] == ["future-portfolio-consumer"]
    assert record["preserved_unrelated_module_ids"] == [
        "architecture-registry",
        "manifest-validation",
    ]
    assert plan.machine_lifecycle_status_added is False
    assert plan.rollback_execution_authorized is False
    assert plan.cleanup_execution_authorized is False
    assert set(record["operations"].values()) == {0}

    with pytest.raises(PortfolioFixtureError, match="must be disjoint"):
        build_module_isolation_plan(
            failed_module_id="failed-module",
            affected_downstream_module_ids=("overlap",),
            unrelated_module_ids=("overlap",),
            rollback_reference="tool-system@baseline",
        )


def test_integer_total_economics_uses_frozen_fixture_after_hard_floors() -> None:
    corpus = load_yaml_file(CORPUS)
    cost = TotalEconomicCost.from_fixture_mapping(
        corpus["economic_record_schema"]["synthetic_fixture"]
    )
    decision = select_lowest_total_economic_cost(
        (
            EconomicCandidate(
                route_id="fixture-cheap-unqualified/model-v1",
                hard_floors_passed=False,
                cost=_small_cost(1),
            ),
            EconomicCandidate(
                route_id="fixture-qualified/model-v1",
                hard_floors_passed=True,
                cost=cost,
            ),
        )
    )

    assert cost.total_micro_usd == 17_000
    assert decision.status is RouteDecisionStatus.SELECTED
    assert decision.selected_route_id == "fixture-qualified/model-v1"
    assert decision.evaluations[0].cost.total_micro_usd == 1
    assert set(decision.to_record()["operations"].values()) == {0}

    negative = dict(corpus["economic_record_schema"]["synthetic_fixture"])
    negative["retry"] = -1
    with pytest.raises(PortfolioFixtureError, match="non-negative integer"):
        TotalEconomicCost.from_fixture_mapping(negative)

    floating = dict(corpus["economic_record_schema"]["synthetic_fixture"])
    floating["retry"] = 0.5
    with pytest.raises(PortfolioFixtureError, match="non-negative integer"):
        TotalEconomicCost.from_fixture_mapping(floating)


def test_frozen_corpus_task_pair_state_and_non_authorizing_scope_remain_aligned() -> (
    None
):
    manifest_result = validate_task_manifest(
        MANIFEST, REPO_WRITE_POLICY, AUTONOMY_POLICY
    )
    plan_result = validate_change_plan(PLAN)
    manifest = load_yaml_file(MANIFEST)
    plan = load_yaml_file(PLAN)
    corpus = load_yaml_file(CORPUS)
    state = load_yaml_file(PROJECT_STATE)["p15d_prerequisite_failure_control_fixture"]
    report = REPORT.read_text(encoding="utf-8")

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == EXACT_FILES
    assert set(plan["changed_files"]) == EXACT_FILES
    assert len(EXACT_FILES) == 13
    assert [item["case_id"] for item in corpus["case_catalog"]] == [
        "availability-failover",
        "quality-repair-then-escalation",
        "policy-block-no-provider-bypass",
        "cancellation-before-dispatch-and-before-application",
        "repeated-or-two-cycle-no-progress-stop",
        "affected-module-isolation",
        "rollback-plan-remains-non-executing",
        "hard-floors-before-total-economics",
    ]
    assert state["module"]["previous_module_version"] == "1.2.0"
    assert state["module"]["module_version"] == "1.3.0"
    assert state["module"]["aggregate_interface_version"] == "1.0.0"
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_stage_entered"] is False
    assert state["p15d_stage_accepted"] is False
    assert state["p15e_authorized"] is False
    assert "NON_EXECUTING_PREREQUISITE_FIXTURE" in report
    assert "provider_invocations: 0" in report


def test_failure_control_source_has_no_filesystem_process_network_or_yaml_io() -> None:
    source = ROOT / "src/tool_system/provider_portfolio/failure_control.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module).split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    observed_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_roots.isdisjoint(
        {"http", "os", "pathlib", "requests", "socket", "subprocess", "urllib", "yaml"}
    )
    assert observed_calls.isdisjoint(
        {
            "connect",
            "open",
            "read_bytes",
            "read_text",
            "send",
            "write",
            "write_bytes",
            "write_text",
        }
    )
