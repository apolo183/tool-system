from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from tool_system.ai_worker import (
    AIModelSpec,
    AIWorkerBudget,
    AIWorkerRequest,
    AIWorkerRuntime,
    ContentAddressedInput,
    PromptSpec,
)
from tool_system.ai_worker.contract import AIWorkerErrorCode
from tool_system.ai_worker.fixture_provider import FixtureScenario
from tool_system.provider_portfolio import (
    CatalogCandidate,
    CatalogSnapshot,
    DeterministicProviderRouter,
    EconomicEstimate,
    FailureClass,
    FailureDisposition,
    FixtureAuthorizationEnvelope,
    PortfolioFixtureAdapter,
    PortfolioFixtureError,
    QualificationState,
    RouteDecisionStatus,
    build_task_profile_fixture,
    classify_failure,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_VERSION = "p15b-fixture-routing-policy-v1"
CATALOG_VERSION = "p15b-fixture-catalog-v1"
EVIDENCE_SNAPSHOT = "p15b-fixture-evidence-v1"


def _economics(total: int) -> EconomicEstimate:
    return EconomicEstimate(
        metered_usage_microunits=total,
        verification_microunits=0,
        retry_microunits=0,
        rework_microunits=0,
        recovery_microunits=0,
        critical_path_time_microunits=0,
        avoidable_renewal_microunits=0,
        allocated_operating_microunits=0,
        local_infrastructure_microunits=0,
        opportunity_cost_microunits=0,
    )


def _candidate(
    provider_id: str,
    *,
    cost: int,
    strength: int,
    quality: int = 900_000,
    confidence: int = 900_000,
    state: QualificationState = QualificationState.ELIGIBLE,
    surface: str = "isolated-fixture",
    requires_credentials: bool = False,
    calls_external_provider: bool = False,
    network_access: bool = False,
) -> CatalogCandidate:
    return CatalogCandidate(
        provider_id=provider_id,
        model_id="fixture-model-v1",
        adapter_version="1.0.0",
        interface_version="1.0.0",
        execution_surface_id=surface,
        qualification_state=state,
        task_classes=("bounded-code-change",),
        supported_languages=("python",),
        capabilities=("structured-output", "tool-free-generation"),
        context_window_tokens=8_192,
        max_output_tokens=1_024,
        quality_micros=quality,
        confidence_micros=confidence,
        maximum_security_risk=3,
        maximum_data_risk=3,
        maximum_repository_mutation_risk=1,
        maximum_operational_risk=3,
        data_policy_id="fixture-local-only",
        evidence_snapshot_id=EVIDENCE_SNAPSHOT,
        evidence_current=True,
        credential_reference_id=(
            "fixture-secret-store:provider-key" if requires_credentials else None
        ),
        requires_credentials=requires_credentials,
        calls_external_provider=calls_external_provider,
        network_access=network_access,
        logical_duration_ms=10 + strength,
        strength_rank=strength,
        economics=_economics(cost),
    )


def _catalog(*candidates: CatalogCandidate) -> CatalogSnapshot:
    return CatalogSnapshot(
        catalog_version=CATALOG_VERSION,
        policy_version=POLICY_VERSION,
        evidence_snapshot_id=EVIDENCE_SNAPSHOT,
        candidates=tuple(sorted(candidates, key=lambda candidate: candidate.route_id)),
    )


def _profile():
    return build_task_profile_fixture(
        task_id="p15b-fixture-task",
        task_class="bounded-code-change",
        language="python",
        repository_context_tokens=2_048,
        dependency_breadth=3,
        reasoning_complexity=3,
        implementation_complexity=3,
        security_risk=2,
        data_risk=1,
        repository_mutation_risk=0,
        operational_risk=2,
        required_capabilities=("structured-output", "tool-free-generation"),
        minimum_quality_micros=800_000,
        minimum_confidence_micros=800_000,
        verification_burden=3,
        repair_burden=2,
        critical_path=True,
        remaining_slack_ms=1_000,
        delay_sensitivity_micros=900_000,
        evidence_confidence_micros=950_000,
        uncertainty_reasons=("fixture-estimate-only",),
    )


def _authorization(catalog: CatalogSnapshot) -> FixtureAuthorizationEnvelope:
    return FixtureAuthorizationEnvelope(
        authorization_id="p15b-isolated-fixture-authorization-v1",
        policy_version=POLICY_VERSION,
        catalog_version=CATALOG_VERSION,
        evidence_snapshot_id=EVIDENCE_SNAPSHOT,
        authorized_route_ids=tuple(
            sorted(candidate.route_id for candidate in catalog.candidates)
        ),
        permitted_execution_surfaces=("isolated-fixture",),
        permitted_data_policy_ids=("fixture-local-only",),
        permitted_credential_reference_ids=(),
        max_total_tokens=4_096,
        max_output_tokens=512,
        max_cost_microunits=1_000,
        max_duration_ms=1_000,
        max_attempts=3,
        max_retries=1,
    )


def _request(candidate: CatalogCandidate) -> AIWorkerRequest:
    return AIWorkerRequest(
        request_id="p15b-fixture-request",
        idempotency_key="p15b-fixture-idempotency",
        attempt_number=1,
        operation="summarize",
        model=AIModelSpec(
            provider_id=candidate.provider_id,
            model_id=candidate.model_id,
            capabilities=candidate.capabilities,
            context_window_tokens=candidate.context_window_tokens,
        ),
        prompt=PromptSpec(prompt_id="p15b-fixture-prompt", prompt_version="1"),
        inputs=(
            ContentAddressedInput.build(
                input_id="fixture-input",
                kind="fixture",
                media_type="application/json",
                payload={"value": 1},
                sensitivity="public",
            ),
        ),
        required_capabilities=("structured-output",),
        required_output_keys=("summary",),
        budget=AIWorkerBudget(
            max_input_tokens=64,
            max_output_tokens=64,
            max_total_tokens=128,
            timeout_ms=100,
            max_cost_microunits=0,
        ),
    )


def test_task_profiler_fixture_is_deterministic_advisory_and_independent() -> None:
    first = _profile()
    second = _profile()

    assert first == second
    assert first.sha256() == second.sha256()
    assert first.profile_id.startswith("fixture-profile-")
    assert first.authority_effect == "none"
    assert first.security_risk != first.reasoning_complexity
    assert first.repository_mutation_risk == 0
    assert first.critical_path is True
    assert first.uncertainty_reasons == ("fixture-estimate-only",)

    with pytest.raises(
        PortfolioFixtureError,
        match="required_capabilities must be unique and canonically ordered",
    ):
        invalid = {
            key: value
            for key, value in first.to_record().items()
            if key not in {"profile_id", "source_input_sha256", "authority_effect"}
        }
        invalid["required_capabilities"] = (
            "tool-free-generation",
            "structured-output",
        )
        invalid["uncertainty_reasons"] = tuple(invalid["uncertainty_reasons"])
        build_task_profile_fixture(**invalid)


def test_router_applies_hard_floors_before_integer_economics_deterministically() -> None:
    selected = _candidate("fixture-alpha", cost=100, strength=1)
    stronger = _candidate("fixture-beta", cost=220, strength=3)
    cheaper_but_unqualified = _candidate(
        "fixture-gamma", cost=1, strength=2, quality=700_000
    )
    catalog = _catalog(selected, stronger, cheaper_but_unqualified)
    router = DeterministicProviderRouter(POLICY_VERSION)

    first = router.route(_profile(), _authorization(catalog), catalog)
    second = router.route(_profile(), _authorization(catalog), catalog)

    assert first == second
    assert first.status is RouteDecisionStatus.SELECTED
    assert first.selected_route_id == selected.route_id
    assert first.ordered_eligible_route_ids == (
        selected.route_id,
        stronger.route_id,
    )
    assert first.availability_failover_route_ids == (stronger.route_id,)
    assert first.quality_escalation_route_ids == (stronger.route_id,)
    assert first.same_route_repair_limit == 1
    rejected = next(
        item for item in first.evaluations if item.route_id == cheaper_but_unqualified.route_id
    )
    assert rejected.eligible is False
    assert rejected.hard_floor_reasons == ("QUALITY_FLOOR_UNMET",)
    assert first.authority_effect == "none"
    assert first.provider_invocations == first.network_operations == 0
    assert first.credential_value_accesses == 0
    assert len(first.evidence_sha256) == 64


def test_router_blocks_stale_live_or_authority_expanding_inputs_without_bypass() -> None:
    live = _candidate(
        "fixture-live-shaped",
        cost=1,
        strength=5,
        surface="live-api",
        requires_credentials=True,
        calls_external_provider=True,
        network_access=True,
    )
    catalog = _catalog(live)
    authorization = replace(
        _authorization(catalog),
        permitted_execution_surfaces=("live-api",),
        permitted_credential_reference_ids=("fixture-secret-store:provider-key",),
    )

    decision = DeterministicProviderRouter(POLICY_VERSION).route(
        _profile(), authorization, catalog
    )

    assert decision.status is RouteDecisionStatus.BLOCKED
    assert decision.selected_route_id is None
    assert decision.ordered_eligible_route_ids == ()
    assert decision.stop_reason == FailureClass.EMPTY_ELIGIBLE_SET.value
    reasons = decision.evaluations[0].hard_floor_reasons
    assert {
        "CREDENTIAL_USE_FORBIDDEN",
        "EXTERNAL_PROVIDER_FORBIDDEN",
        "NETWORK_ACCESS_FORBIDDEN",
        "NON_FIXTURE_SURFACE_FORBIDDEN",
    } <= set(reasons)

    expanded = replace(authorization, live_provider_execution_authorized=True)
    expanded_decision = DeterministicProviderRouter(POLICY_VERSION).route(
        _profile(), expanded, catalog
    )
    assert expanded_decision.stop_reason == "P15B_EXTERNAL_AUTHORITY_FORBIDDEN"
    assert all(
        "P15B_EXTERNAL_AUTHORITY_FORBIDDEN" in item.hard_floor_reasons
        for item in expanded_decision.evaluations
    )


def test_catalog_policy_evidence_and_cost_drift_fail_closed() -> None:
    candidate = _candidate("fixture-alpha", cost=100, strength=1)
    catalog = _catalog(candidate)
    authorization = _authorization(catalog)
    router = DeterministicProviderRouter(POLICY_VERSION)

    mismatched = router.route(
        _profile(), replace(authorization, catalog_version="wrong-catalog-v1"), catalog
    )
    over_budget = router.route(
        _profile(), replace(authorization, max_cost_microunits=99), catalog
    )

    assert mismatched.status is RouteDecisionStatus.BLOCKED
    assert mismatched.stop_reason == "CATALOG_VERSION_MISMATCH"
    assert over_budget.status is RouteDecisionStatus.BLOCKED
    assert over_budget.evaluations[0].hard_floor_reasons == (
        "HARD_COST_BUDGET_EXCEEDED",
    )


def test_failure_classification_keeps_failover_repair_block_and_stop_distinct() -> None:
    availability = classify_failure(FailureClass.RATE_LIMIT)
    quality = classify_failure(FailureClass.QUALITY_REJECTED)
    blocked = classify_failure(FailureClass.DATA_POLICY_DENIED)
    stopped = classify_failure(FailureClass.NO_PROGRESS)

    assert availability.disposition is FailureDisposition.AVAILABILITY_FAILOVER
    assert availability.provider_switch_allowed is True
    assert availability.same_route_repair_allowed is False
    assert quality.disposition is FailureDisposition.SAME_ROUTE_REPAIR_THEN_ESCALATE
    assert quality.same_route_repair_allowed is True
    assert quality.stronger_route_escalation_allowed is True
    assert quality.provider_switch_allowed is True
    assert blocked.disposition is FailureDisposition.BLOCK_NO_PROVIDER_BYPASS
    assert blocked.provider_switch_allowed is False
    assert blocked.terminal is True
    assert stopped.disposition is FailureDisposition.STOP
    assert stopped.terminal is True

    assert {classify_failure(item).failure_class for item in FailureClass} == set(
        FailureClass
    )


def test_fixture_adapter_implements_existing_runtime_boundary_without_external_io() -> None:
    candidate = _candidate("fixture-alpha", cost=100, strength=1)
    adapter = PortfolioFixtureAdapter(
        candidate,
        {"summarize": FixtureScenario(output={"summary": "fixture-ok"})},
    )

    result = AIWorkerRuntime(adapter).run(_request(candidate))

    assert result.status == "PASS"
    assert result.output == {"summary": "fixture-ok"}
    assert result.provider_id == candidate.provider_id
    assert result.model_id == candidate.model_id
    assert adapter.call_count == 1
    assert adapter.provider_kind == "deterministic_fixture"
    assert adapter.execution_mode == "fixture"
    assert adapter.calls_external_provider is False
    assert adapter.uses_credentials is False
    assert adapter.network_access is False


def test_fixture_adapter_rejects_model_live_and_external_surface_mismatches() -> None:
    candidate = _candidate("fixture-alpha", cost=100, strength=1)
    adapter = PortfolioFixtureAdapter(
        candidate,
        {"summarize": FixtureScenario(output={"summary": "fixture-ok"})},
    )
    mismatch = replace(
        _request(candidate),
        model=replace(_request(candidate).model, model_id="wrong-model"),
    )
    live = replace(_request(candidate), execution_mode="live")

    mismatch_response = adapter.invoke(mismatch)
    live_response = adapter.invoke(live)

    assert mismatch_response.error is not None
    assert mismatch_response.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert live_response.error is not None
    assert live_response.error.code is AIWorkerErrorCode.INVALID_REQUEST
    assert adapter.call_count == 0

    external = _candidate(
        "fixture-external",
        cost=1,
        strength=1,
        surface="live-api",
        requires_credentials=True,
        calls_external_provider=True,
        network_access=True,
    )
    with pytest.raises(
        PortfolioFixtureError,
        match="FIXTURE_ADAPTER_EXTERNAL_SURFACE_FORBIDDEN",
    ):
        PortfolioFixtureAdapter(external, {})


def test_portfolio_module_has_no_filesystem_process_or_network_imports() -> None:
    source = ROOT / "src/tool_system/provider_portfolio/fixtures.py"
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

    assert imported_roots.isdisjoint(
        {"http", "os", "pathlib", "requests", "socket", "subprocess", "urllib"}
    )
    forbidden_calls = {"open", "write", "write_bytes", "write_text", "connect", "send"}
    observed_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert observed_calls.isdisjoint(forbidden_calls)
