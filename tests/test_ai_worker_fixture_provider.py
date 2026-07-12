from __future__ import annotations

import builtins
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from tool_system.ai_worker import (
    AIModelSpec,
    AIWorkerBudget,
    AIWorkerErrorCode,
    AIWorkerRequest,
    AIWorkerRuntime,
    AIWorkerUsage,
    CancellationToken,
    ContentAddressedInput,
    DeterministicFixtureProvider,
    FixtureScenario,
    PromptSpec,
    ProviderResponse,
    canonical_sha256,
)


def _request() -> AIWorkerRequest:
    return AIWorkerRequest(
        request_id="request-001",
        idempotency_key="fixture:request-001",
        attempt_number=1,
        operation="generate-patch",
        model=AIModelSpec(
            provider_id="deterministic-fixture",
            model_id="fixture-v1",
            capabilities=("structured-output", "tool-free-generation"),
            context_window_tokens=256,
        ),
        prompt=PromptSpec("implementation-prompt", "v1"),
        inputs=(
            ContentAddressedInput.build(
                input_id="blueprint",
                kind="approved-blueprint",
                media_type="application/json",
                payload={"objective": "build CLI"},
            ),
        ),
        required_capabilities=("structured-output",),
        required_output_keys=("patch", "summary"),
        budget=AIWorkerBudget(64, 64, 128, 100, 0),
        metadata={"trace_id": "trace-private-value"},
    )


def _provider(**scenario_overrides: object) -> DeterministicFixtureProvider:
    scenario = FixtureScenario(
        output={
            "patch": "diff --git a/app.py b/app.py",
            "summary": "add CLI",
        },
        **scenario_overrides,
    )
    return DeterministicFixtureProvider({"generate-patch": scenario})


def test_fixture_success_is_structured_deterministic_and_audit_redacted() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)

    result = runtime.run(_request())

    assert result.status == "PASS"
    assert result.error is None
    assert result.output == {
        "patch": "diff --git a/app.py b/app.py",
        "summary": "add CLI",
    }
    assert result.output_sha256 is not None
    assert provider.call_count == 1
    audit = json.dumps(result.to_audit_record(), sort_keys=True)
    assert "diff --git" not in audit
    assert "trace-private-value" not in audit
    assert result.output_sha256 in audit


def test_identical_replay_does_not_reinvoke_and_conflict_does_not_replace() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)
    request = _request()

    first = runtime.run(request)
    replay = runtime.run(request)
    conflict = runtime.run(replace(request, prompt=PromptSpec("implementation-prompt", "v2")))

    assert first.status == "PASS"
    assert first.replayed is False
    assert replay.status == "PASS"
    assert replay.replayed is True
    assert replay.output_sha256 == first.output_sha256
    assert conflict.status == "BLOCK"
    assert conflict.error is not None
    assert conflict.error.code is AIWorkerErrorCode.REPLAY_CONFLICT
    assert provider.call_count == 1


def test_caller_output_mutation_cannot_corrupt_stored_replay() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)
    request = _request()

    first = runtime.run(request)
    assert first.output is not None
    first.output["patch"] = "caller-corruption"
    replay = runtime.run(request)

    assert replay.output is not None
    assert replay.output["patch"] == "diff --git a/app.py b/app.py"
    assert replay.output_sha256 == first.output_sha256
    assert replay.output_sha256 == canonical_sha256(replay.output)
    assert provider.call_count == 1


def test_concurrent_duplicate_requests_invoke_provider_exactly_once() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)
    request = _request()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: runtime.run(request), range(16)))

    assert all(result.status == "PASS" for result in results)
    assert sum(not result.replayed for result in results) == 1
    assert provider.call_count == 1


def test_precancelled_request_never_invokes_provider() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)
    cancellation = CancellationToken()
    cancellation.cancel()

    result = runtime.run(_request(), cancellation=cancellation)

    assert result.status == "CANCELLED"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.CANCELLED
    assert provider.call_count == 0


@pytest.mark.parametrize(
    ("scenario", "expected_code"),
    [
        ({"output_tokens": 65}, AIWorkerErrorCode.BUDGET_EXCEEDED),
        ({"input_tokens": 65}, AIWorkerErrorCode.BUDGET_EXCEEDED),
        ({"logical_duration_ms": 101}, AIWorkerErrorCode.TIMEOUT),
        ({"cost_microunits": 1}, AIWorkerErrorCode.BUDGET_EXCEEDED),
    ],
)
def test_provider_usage_cannot_exceed_any_budget(
    scenario: dict[str, object],
    expected_code: AIWorkerErrorCode,
) -> None:
    result = AIWorkerRuntime(_provider(**scenario)).run(_request())

    assert result.status in {"BLOCK", "ERROR"}
    assert result.error is not None
    assert result.error.code is expected_code
    assert result.output is None


def test_missing_required_output_key_is_invalid_response() -> None:
    provider = DeterministicFixtureProvider(
        {"generate-patch": FixtureScenario(output={"summary": "missing patch"})}
    )

    result = AIWorkerRuntime(provider).run(_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.INVALID_RESPONSE


def test_provider_and_runtime_capabilities_are_bound_before_invocation() -> None:
    provider = _provider()
    runtime = AIWorkerRuntime(provider)
    wrong_provider = replace(
        _request(),
        model=replace(_request().model, provider_id="unexpected-provider"),
    )
    extra_capability = replace(
        _request(),
        idempotency_key="fixture:capability",
        model=replace(
            _request().model,
            capabilities=(
                "structured-output",
                "tool-free-generation",
                "code-generation",
            ),
        ),
        required_capabilities=("code-generation",),
    )

    mismatch = runtime.run(wrong_provider)
    capability = runtime.run(extra_capability)

    assert mismatch.error is not None
    assert mismatch.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert capability.error is not None
    assert capability.error.code is AIWorkerErrorCode.CAPABILITY_MISMATCH
    assert provider.call_count == 0


class _ExplodingProvider:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def invoke(self, request: AIWorkerRequest, cancellation: object = None) -> ProviderResponse:
        raise RuntimeError("raw-provider-secret-must-not-escape")


class _InvalidUsageProvider:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def invoke(self, request: AIWorkerRequest, cancellation: object = None) -> ProviderResponse:
        return ProviderResponse(
            output={"patch": "x", "summary": "y"},
            usage=AIWorkerUsage(output_tokens=-1),
        )


class _InvalidResponseProvider:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def invoke(self, request: AIWorkerRequest, cancellation: object = None) -> object:
        return {"output": "not-a-provider-response"}


class _RequestMutatingProvider:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "deterministic_fixture"
    execution_mode = "fixture"
    calls_external_provider = False
    uses_credentials = False
    network_access = False

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: object = None,
    ) -> ProviderResponse:
        payload = request.inputs[0].payload
        assert isinstance(payload, dict)
        payload["provider_mutation"] = True
        return ProviderResponse(
            output={"patch": "x", "summary": "y"},
            usage=AIWorkerUsage(input_tokens=1, output_tokens=1),
        )


def test_provider_exception_is_sanitized_and_invalid_usage_is_rejected() -> None:
    failure = AIWorkerRuntime(_ExplodingProvider()).run(_request())
    invalid_usage = AIWorkerRuntime(_InvalidUsageProvider()).run(
        replace(_request(), idempotency_key="fixture:invalid-usage")
    )

    assert failure.error is not None
    assert failure.error.code is AIWorkerErrorCode.PROVIDER_FAILURE
    assert failure.error.message == "provider raised RuntimeError"
    assert "raw-provider-secret" not in json.dumps(failure.to_record())
    assert invalid_usage.error is not None
    assert invalid_usage.error.code is AIWorkerErrorCode.INVALID_RESPONSE


def test_invalid_provider_response_object_fails_closed() -> None:
    result = AIWorkerRuntime(_InvalidResponseProvider()).run(_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.INVALID_RESPONSE


def test_provider_cannot_mutate_content_addressed_request() -> None:
    result = AIWorkerRuntime(_RequestMutatingProvider()).run(_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.INVALID_RESPONSE
    assert result.error.reasons == (
        "request_sha256 changed across provider invocation",
    )


class _ExternalProviderStub:
    provider_id = "deterministic-fixture"
    model_id = "fixture-v1"
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "live_provider"
    execution_mode = "live"
    calls_external_provider = True
    uses_credentials = True
    network_access = True

    def __init__(self) -> None:
        self.call_count = 0

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: object = None,
    ) -> ProviderResponse:
        self.call_count += 1
        raise AssertionError("P14B must block before invocation")


def test_live_provider_metadata_is_blocked_before_invocation() -> None:
    provider = _ExternalProviderStub()

    result = AIWorkerRuntime(provider).run(_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert provider.call_count == 0


def test_fixture_provider_performs_no_filesystem_or_network_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("external IO attempted")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)

    result = AIWorkerRuntime(_provider()).run(_request())

    assert result.status == "PASS"
