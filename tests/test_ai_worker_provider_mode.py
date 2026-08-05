from __future__ import annotations

from dataclasses import dataclass

from tool_system.ai_worker.contract import AIModelSpec
from tool_system.ai_worker.runtime import (
    DefaultDisabledAPIExecutionGuard,
    ProviderRouteConfig,
    select_enabled_provider,
)


def _model(provider_id: str = "openai", model_id: str = "configured-model") -> AIModelSpec:
    return AIModelSpec(
        provider_id=provider_id,
        model_id=model_id,
        capabilities=(),
        context_window_tokens=1,
    )


def test_all_api_routes_are_disabled_without_explicit_api_mode() -> None:
    decision = select_enabled_provider(
        (
            ProviderRouteConfig("openai", "operator-model", enabled=True, available=True),
            ProviderRouteConfig("qwen", "moving-alias", enabled=True, available=True),
        )
    )

    assert decision.status == "API_DISABLED"
    assert decision.provider_id is None
    assert decision.credential_resolver_invocations == 0
    assert decision.credential_value_accesses == 0
    assert decision.provider_invocations == 0
    assert decision.network_operations == 0


def test_unconfigured_or_unavailable_providers_skip_to_one_usable_route() -> None:
    decision = select_enabled_provider(
        (
            ProviderRouteConfig("openai", "operator-model"),
            ProviderRouteConfig("qwen", "moving-alias", enabled=True, available=False),
            ProviderRouteConfig("future", "current-model", enabled=True, available=True),
        ),
        api_mode_enabled=True,
    )

    assert decision.status == "ROUTE_SELECTED"
    assert (decision.provider_id, decision.model_id) == ("future", "current-model")
    assert decision.skipped_provider_ids == ("openai", "qwen")
    assert decision.credential_resolver_invocations == 0
    assert decision.credential_value_accesses == 0
    assert decision.provider_invocations == 0
    assert decision.network_operations == 0


def test_no_usable_enabled_provider_is_stable_and_side_effect_free() -> None:
    decision = select_enabled_provider(
        (
            ProviderRouteConfig("deepseek", "moving-model", enabled=True),
            ProviderRouteConfig("qwen", "operator-model", available=True),
        ),
        api_mode_enabled=True,
    )

    assert decision.status == "NO_AVAILABLE_PROVIDER"
    assert decision.skipped_provider_ids == ("deepseek", "qwen")
    assert decision.provider_invocations == 0
    assert decision.network_operations == 0


def test_malformed_or_duplicate_external_routes_fail_closed() -> None:
    malformed = select_enabled_provider(
        (ProviderRouteConfig("", "model", enabled=True, available=True),),
        api_mode_enabled=True,
    )
    duplicate = select_enabled_provider(
        (
            ProviderRouteConfig("openai", "first", enabled=False),
            ProviderRouteConfig("openai", "second", enabled=True, available=True),
        ),
        api_mode_enabled=True,
    )

    assert malformed.status == "INVALID_EXTERNAL_CONFIGURATION"
    assert duplicate.status == "INVALID_EXTERNAL_CONFIGURATION"
    assert duplicate.provider_id is None


@dataclass
class _FakeProvider:
    provider_id: str = "openai"
    model_id: str = "configured-model"


@dataclass
class _FakeRequest:
    model: AIModelSpec


def test_api_guard_requires_exact_repository_external_selection() -> None:
    request = _FakeRequest(_model())
    provider = _FakeProvider()

    assert DefaultDisabledAPIExecutionGuard().validate(request, provider) == (
        "large-model API mode is disabled",
        "no repository-external provider/model route is selected",
    )
    enabled = DefaultDisabledAPIExecutionGuard(
        api_mode_enabled=True,
        selected_provider_id="openai",
        selected_model_id="configured-model",
    )
    assert enabled.validate(request, provider) == ()


def test_api_guard_rejects_request_and_runtime_route_drift() -> None:
    guard = DefaultDisabledAPIExecutionGuard(
        api_mode_enabled=True,
        selected_provider_id="openai",
        selected_model_id="configured-model",
    )

    assert guard.validate(_FakeRequest(_model("qwen", "other")), _FakeProvider()) == (
        "request provider is not the explicitly selected route",
        "request model is not the explicitly selected route",
    )
    assert guard.validate(
        _FakeRequest(_model()),
        _FakeProvider(provider_id="qwen", model_id="other"),
    ) == (
        "runtime provider is not the explicitly selected route",
        "runtime model is not the explicitly selected route",
    )


def test_key_presence_is_not_an_input_to_route_authorization() -> None:
    fields = ProviderRouteConfig.__dataclass_fields__
    assert "credential" not in fields
    assert "api_key" not in fields
