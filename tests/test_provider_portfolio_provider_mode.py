from __future__ import annotations

import ast
from dataclasses import fields, replace
from pathlib import Path

import pytest

from tool_system.provider_portfolio import (
    ProviderAuthorizationState,
    ProviderAvailabilityState,
    ProviderModeDecisionStatus,
    ProviderModeError,
    ProviderModeEvaluationDisposition,
    ProviderModeRoute,
    ProviderModeSnapshot,
    select_provider_mode_route,
)

ROOT = Path(__file__).resolve().parents[1]


def _route(
    provider_id: str,
    model_id: str,
    *,
    enabled: bool = True,
    availability: ProviderAvailabilityState = ProviderAvailabilityState.AVAILABLE,
    transfer: bool = True,
    fake_io: bool = True,
    budget: int = 1_000,
    reservation: int = 100,
    duration: int = 10,
    strength: int = 1,
) -> ProviderModeRoute:
    return ProviderModeRoute(
        provider_id=provider_id,
        requested_model_id=model_id,
        enabled=enabled,
        availability_state=availability,
        provider_data_transfer_authorized=transfer,
        adapter_fake_io_contract_passed=fake_io,
        provider_budget_microunits=budget,
        reserved_cost_microunits=reservation,
        logical_duration_ms=duration,
        strength_rank=strength,
    )


def _snapshot(*routes: ProviderModeRoute, enabled: bool = True) -> ProviderModeSnapshot:
    return ProviderModeSnapshot(
        configuration_version="operator-snapshot-v1",
        policy_version="provider-mode-policy-v1",
        authorization_id="local-provider-mode-authorization-v1",
        routes=routes,
        api_mode_enabled=enabled,
        authorization_state=ProviderAuthorizationState.ACTIVE,
        policy_preconditions_current=True,
        source_preconditions_current=True,
        total_budget_microunits=10_000,
        max_attempts=3,
        max_retries=1,
    )


def test_every_api_route_stays_off_without_explicit_api_mode() -> None:
    snapshot = replace(
        _snapshot(
            _route("provider-a", "moving-alias"),
            _route("provider-b", "operator-model"),
        ),
        api_mode_enabled=False,
        authorization_state=ProviderAuthorizationState.NOT_AUTHORIZED,
        policy_preconditions_current=False,
        source_preconditions_current=False,
        total_budget_microunits=0,
        max_attempts=0,
        max_retries=0,
    )

    decision = select_provider_mode_route(snapshot)

    assert decision.status is ProviderModeDecisionStatus.API_DISABLED
    assert decision.selected_route_id is None
    assert decision.stop_reason == "API_DISABLED"
    assert decision.skipped_route_ids == (
        "provider-a/moving-alias",
        "provider-b/operator-model",
    )
    assert {
        evaluation.disposition for evaluation in decision.evaluations
    } == {ProviderModeEvaluationDisposition.SKIPPED}
    assert decision.dispatch_authorized is False
    assert set(decision.to_record()["operations"].values()) == {0}


def test_external_priority_skips_unusable_routes_and_preserves_moving_aliases() -> None:
    snapshot = _snapshot(
        _route(
            "provider-a",
            "",
            availability=ProviderAvailabilityState.UNCONFIGURED,
            budget=0,
            reservation=0,
        ),
        _route(
            "provider-b",
            "latest-model",
            availability=ProviderAvailabilityState.UNFUNDED,
            budget=0,
            reservation=0,
        ),
        _route("future-provider", "current-moving-alias", reservation=300, strength=2),
        _route("provider-c", "operator-selected-model", reservation=1, strength=3),
    )

    first = select_provider_mode_route(snapshot)
    second = select_provider_mode_route(snapshot)

    assert first == second
    assert first.status is ProviderModeDecisionStatus.SELECTED
    assert (first.selected_provider_id, first.requested_model_id) == (
        "future-provider",
        "current-moving-alias",
    )
    assert first.skipped_route_ids == (
        "provider-a/UNCONFIGURED",
        "provider-b/latest-model",
    )
    assert first.ordered_eligible_route_ids == (
        "future-provider/current-moving-alias",
        "provider-c/operator-selected-model",
    )
    assert first.availability_failover_route_ids == (
        "provider-c/operator-selected-model",
    )
    assert first.quality_escalation_route_ids == (
        "provider-c/operator-selected-model",
    )
    assert first.same_route_repair_limit == 1
    assert len(first.evidence_sha256) == 64


def test_operator_priority_is_not_rewritten_by_repository_economics() -> None:
    expensive_first = _route(
        "provider-a",
        "operator-first",
        reservation=900,
        duration=100,
    )
    cheaper_second = _route(
        "provider-b",
        "operator-second",
        reservation=1,
        duration=1,
    )

    decision = select_provider_mode_route(_snapshot(expensive_first, cheaper_second))

    assert decision.status is ProviderModeDecisionStatus.SELECTED
    assert decision.selected_route_id == expensive_first.route_id
    assert decision.ordered_eligible_route_ids == (
        expensive_first.route_id,
        cheaper_second.route_id,
    )


@pytest.mark.parametrize(
    "availability",
    [
        ProviderAvailabilityState.UNCONFIGURED,
        ProviderAvailabilityState.UNFUNDED,
        ProviderAvailabilityState.MISSING_CREDENTIAL,
        ProviderAvailabilityState.INVALID_CREDENTIAL,
        ProviderAvailabilityState.EXPIRED_CREDENTIAL,
        ProviderAvailabilityState.QUOTA_EXHAUSTED,
        ProviderAvailabilityState.RATE_LIMITED,
        ProviderAvailabilityState.UNAVAILABLE,
    ],
)
def test_unavailable_states_are_skips_not_completion_failures(
    availability: ProviderAvailabilityState,
) -> None:
    route = _route(
        "provider-a",
        "moving-model",
        availability=availability,
        budget=0 if availability is ProviderAvailabilityState.UNFUNDED else 1_000,
    )

    decision = select_provider_mode_route(_snapshot(route))

    assert decision.status is ProviderModeDecisionStatus.NO_AVAILABLE_PROVIDER
    assert decision.stop_reason == "NO_AVAILABLE_PROVIDER"
    assert decision.skipped_route_ids == (route.route_id,)
    assert decision.evaluations[0].disposition is (
        ProviderModeEvaluationDisposition.SKIPPED
    )
    assert decision.dispatch_authorized is False


@pytest.mark.parametrize(
    ("route_changes", "expected_reason"),
    [
        ({"provider_data_transfer_authorized": False}, "PROVIDER_TRANSFER_NOT_AUTHORIZED"),
        ({"adapter_fake_io_contract_passed": False}, "FAKE_IO_CONTRACT_UNVERIFIED"),
        (
            {
                "availability_state": ProviderAvailabilityState.UNAVAILABLE,
                "adapter_fake_io_contract_passed": False,
            },
            "FAKE_IO_CONTRACT_UNVERIFIED",
        ),
        ({"provider_budget_microunits": 50}, "PROVIDER_POLICY_BUDGET"),
    ],
)
def test_route_hard_failures_cannot_be_bypassed_by_another_provider(
    route_changes: dict[str, object],
    expected_reason: str,
) -> None:
    blocked = replace(_route("provider-a", "model-a"), **route_changes)
    usable = _route("provider-b", "model-b")

    decision = select_provider_mode_route(_snapshot(blocked, usable))

    assert decision.status is ProviderModeDecisionStatus.BLOCKED
    assert decision.selected_route_id is None
    assert decision.stop_reason == expected_reason
    assert decision.evaluations[0].disposition is (
        ProviderModeEvaluationDisposition.BLOCKED
    )


@pytest.mark.parametrize(
    ("snapshot_changes", "expected_reason"),
    [
        (
            {"authorization_state": ProviderAuthorizationState.NOT_AUTHORIZED},
            "AUTHORIZATION_NOT_ACTIVE",
        ),
        (
            {"authorization_state": ProviderAuthorizationState.EXPIRED},
            "AUTHORIZATION_EXPIRED",
        ),
        ({"policy_preconditions_current": False}, "POLICY_PRECONDITION_STALE"),
        ({"source_preconditions_current": False}, "SOURCE_PRECONDITION_STALE"),
        ({"cancellation_requested": True}, "CANCELLED"),
        ({"total_budget_microunits": 0}, "HARD_BUDGET_EXHAUSTED"),
        ({"max_attempts": 0, "max_retries": 0}, "ATTEMPT_ENVELOPE_EMPTY"),
    ],
)
def test_global_hard_controls_stop_before_route_selection(
    snapshot_changes: dict[str, object],
    expected_reason: str,
) -> None:
    decision = select_provider_mode_route(
        replace(_snapshot(_route("provider-a", "model-a")), **snapshot_changes)
    )

    assert decision.status is ProviderModeDecisionStatus.BLOCKED
    assert decision.selected_provider_id is None
    assert decision.stop_reason == expected_reason
    assert set(decision.to_record()["operations"].values()) == {0}


def test_snapshot_rejects_duplicate_providers_and_contains_no_key_authority_field() -> None:
    with pytest.raises(ProviderModeError, match="unique provider IDs"):
        _snapshot(
            _route("provider-a", "first-model"),
            _route("provider-a", "second-model"),
        )

    field_names = {
        field.name
        for data_class in (ProviderModeRoute, ProviderModeSnapshot)
        for field in fields(data_class)
    }
    assert not any(
        fragment in name
        for name in field_names
        for fragment in ("api_key", "secret", "credential_value")
    )


def test_provider_mode_source_has_no_provider_names_or_external_io() -> None:
    source = ROOT / "src/tool_system/provider_portfolio/provider_mode.py"
    text = source.read_text(encoding="utf-8")
    tree = ast.parse(text)
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
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert imported_roots.isdisjoint(
        {"http", "os", "pathlib", "requests", "socket", "subprocess", "urllib"}
    )
    assert calls.isdisjoint({"connect", "open", "send", "write", "write_text"})
    assert all(
        provider_name not in text.lower()
        for provider_name in ("deepseek", "openai", "qwen")
    )
