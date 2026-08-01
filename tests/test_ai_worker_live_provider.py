from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace

import pytest

from tool_system.ai_worker.contract import AIWorkerErrorCode
from tool_system.ai_worker.live_evidence import build_packet_validation_evidence
from tool_system.ai_worker.live_provider import (
    HTTPTransportResponse,
    OpenAIResponsesProvider,
    OpenAIResponsesTransport,
    P14CLiveExecutionCapability,
    P14CLiveExecutionGuard,
    TransportFailure,
    _issue_p14c_fake_transport_capability,
    build_p14c_execution_packet,
    build_p14c_synthetic_request,
    validate_p14c_execution_packet,
)
from tool_system.ai_worker.runtime import AIWorkerRuntime, CancellationToken


class _FakeCredentialResolver:
    def __init__(self, value: str = "test-key-never-log") -> None:
        self.value = value
        self.call_count = 0

    def resolve(self, reference: str) -> str:
        assert reference == "env:OPENAI_API_KEY"
        self.call_count += 1
        return self.value


class _FakeTransport:
    transport_kind = "injected_fake"

    def __init__(
        self,
        responses: list[HTTPTransportResponse | TransportFailure],
    ) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def send(
        self,
        *,
        method: str,
        host: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> HTTPTransportResponse:
        self.calls.append(
            {
                "method": method,
                "host": host,
                "path": path,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, TransportFailure):
            raise response
        return response


class _FakeClock:
    def __init__(self) -> None:
        self.value = 100.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


def _success_response(
    *,
    input_tokens: int = 64,
    output_tokens: int = 16,
    status: str = "completed",
    model: str = "gpt-5.6-luna",
    content: list[dict[str, object]] | None = None,
) -> HTTPTransportResponse:
    output_content = content or [
        {
            "type": "output_text",
            "text": json.dumps(
                {
                    "summary": "synthetic control is bounded",
                    "control_status": "PASS",
                }
            ),
        }
    ]
    body = {
        "id": "resp_synthetic",
        "model": model,
        "status": status,
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": output_content,
            }
        ],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }
    return HTTPTransportResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body=json.dumps(body).encode("utf-8"),
    )


def _runtime(
    responses: list[HTTPTransportResponse | TransportFailure],
    *,
    capability_present: bool = True,
) -> tuple[
    AIWorkerRuntime,
    _FakeCredentialResolver,
    _FakeTransport,
    _FakeClock,
]:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = _FakeTransport(responses)
    capability = (
        _issue_p14c_fake_transport_capability(packet, request, transport)
        if capability_present
        else None
    )
    resolver = _FakeCredentialResolver()
    clock = _FakeClock()
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=resolver,
        execution_capability=capability,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    guard = P14CLiveExecutionGuard(
        packet_sha256=packet.sha256(),
        capability=capability,
    )
    return (
        AIWorkerRuntime(provider, execution_guard=guard),
        resolver,
        transport,
        clock,
    )


def test_packet_is_exact_and_packet_only_evidence_performs_zero_access() -> None:
    packet = build_p14c_execution_packet()

    assert validate_p14c_execution_packet(packet) == ()
    assert (
        packet.sha256()
        == "a4a4efecf35b8a1a49b79c7d1e0000925c1a737b32588f463dec6db7bc1f21a7"
    )
    evidence = build_packet_validation_evidence()
    assert evidence["status"] == "PASS"
    assert evidence["credential_value_access_count"] == 0
    assert evidence["provider_call_count"] == 0
    assert evidence["transport_call_count"] == 0
    assert evidence["live_provider_execution_authorized"] is False


def test_packet_drift_is_rejected() -> None:
    packet = replace(build_p14c_execution_packet(), max_attempts=3)

    assert validate_p14c_execution_packet(packet) == (
        "packet field max_attempts does not match P14C-IMPL-v2",
    )


def test_default_runtime_guard_blocks_live_provider_before_secret_or_transport() -> (
    None
):
    packet = build_p14c_execution_packet()
    resolver = _FakeCredentialResolver()
    transport = _FakeTransport([_success_response()])
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=resolver,
    )

    result = AIWorkerRuntime(provider).run(build_p14c_synthetic_request(packet))

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert result.evidence == ("ai_worker.execution_guard.block",)
    assert resolver.call_count == 0
    assert transport.calls == []


def test_missing_live_capability_blocks_before_secret_or_transport() -> None:
    runtime, resolver, transport, _ = _runtime(
        [_success_response()],
        capability_present=False,
    )

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.reasons == ("live execution capability is absent",)
    assert resolver.call_count == 0
    assert transport.calls == []


def test_provider_entrypoint_blocks_without_capability_before_access() -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    resolver = _FakeCredentialResolver()
    transport = _FakeTransport([_success_response()])
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=resolver,
    )

    response = provider.invoke(request)

    assert response.error is not None
    assert response.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert response.error.reasons == ("live execution capability is absent",)
    assert resolver.call_count == 0
    assert transport.calls == []


def test_fake_capability_cannot_authorize_live_network_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    fake_transport = _FakeTransport([_success_response()])
    capability = _issue_p14c_fake_transport_capability(
        packet,
        request,
        fake_transport,
    )
    resolver = _FakeCredentialResolver()
    transport = OpenAIResponsesTransport()
    transport_calls: list[dict[str, object]] = []

    def forbidden_send(**kwargs: object) -> HTTPTransportResponse:
        transport_calls.append(dict(kwargs))
        raise AssertionError("network transport must not be reached")

    monkeypatch.setattr(transport, "send", forbidden_send)
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=resolver,
        execution_capability=capability,
    )

    response = provider.invoke(request)

    assert response.error is not None
    assert response.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert response.error.reasons == (
        "live execution capability transport does not match",
        "live execution capability transport instance does not match",
    )
    assert resolver.call_count == 0
    assert transport_calls == []


def test_capability_is_opaque_exact_and_single_use() -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    with pytest.raises(TypeError, match="approved issuer"):
        transport = _FakeTransport([_success_response()])
        P14CLiveExecutionCapability(
            authorization_id="caller-constructed",
            packet_sha256=packet.sha256(),
            request_sha256=request.sha256(),
            transport_kind="injected_fake",
            transport=transport,
            _issuer=object(),
        )

    transport = _FakeTransport([_success_response()])
    capability = _issue_p14c_fake_transport_capability(
        packet,
        request,
        transport,
    )
    with pytest.raises(AttributeError, match="immutable"):
        capability._transport_kind = "live_network"  # type: ignore[misc]
    resolver = _FakeCredentialResolver()
    provider = OpenAIResponsesProvider(
        packet=packet,
        transport=transport,
        credential_resolver=resolver,
        execution_capability=capability,
    )

    first = provider.invoke(request)
    second = provider.invoke(request)

    assert first.error is None
    assert second.error is not None
    assert second.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert second.error.reasons == (
        "live execution capability was already consumed",
    )
    assert resolver.call_count == 1
    assert len(transport.calls) == 1


def test_runtime_replay_does_not_reinvoke_consumed_capability() -> None:
    runtime, resolver, transport, _ = _runtime([_success_response()])
    request = build_p14c_synthetic_request()

    first = runtime.run(request)
    replay = runtime.run(request)

    assert first.status == "PASS"
    assert replay.status == "PASS"
    assert replay.replayed is True
    assert resolver.call_count == 1
    assert len(transport.calls) == 1


def test_fake_transport_success_uses_exact_bounded_responses_envelope() -> None:
    runtime, resolver, transport, _ = _runtime([_success_response()])
    request = build_p14c_synthetic_request()

    result = runtime.run(request)

    assert result.status == "PASS"
    assert result.output == {
        "summary": "synthetic control is bounded",
        "control_status": "PASS",
    }
    assert result.usage.input_tokens == 64
    assert result.usage.output_tokens == 16
    assert result.usage.cost_microunits == 160
    assert resolver.call_count == 1
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert (call["method"], call["host"], call["path"]) == (
        "POST",
        "api.openai.com",
        "/v1/responses",
    )
    headers = call["headers"]
    assert isinstance(headers, dict)
    assert headers["authorization"] == "Bearer test-key-never-log"
    body = json.loads(call["body"])
    assert body["model"] == "gpt-5.6-luna"
    assert body["reasoning"] == {"effort": "none"}
    assert body["store"] is False
    assert body["max_output_tokens"] == 512
    assert "tools" not in body
    assert body["text"]["format"]["strict"] is True
    assert body["text"]["format"]["schema"]["additionalProperties"] is False

    audit = json.dumps(result.to_audit_record(), sort_keys=True)
    assert "test-key-never-log" not in audit
    assert "synthetic control is bounded" not in audit
    assert request.inputs[0].payload not in result.to_audit_record().values()


def test_retry_is_exact_bounded_and_retry_after_is_capped() -> None:
    retry = HTTPTransportResponse(
        status_code=429,
        headers={"Retry-After": "10"},
        body=b'{"error":{"type":"rate_limit"}}',
    )
    runtime, resolver, transport, clock = _runtime([retry, _success_response()])

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "PASS"
    assert resolver.call_count == 2
    assert len(transport.calls) == 2
    assert clock.sleeps == [2.0]


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 409, 422])
def test_nonretryable_statuses_stop_after_one_fake_call(status_code: int) -> None:
    response = HTTPTransportResponse(
        status_code=status_code,
        headers={},
        body=b"{}",
    )
    runtime, resolver, transport, _ = _runtime([response])

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.PROVIDER_FAILURE
    assert result.error.retryable is False
    assert resolver.call_count == 1
    assert len(transport.calls) == 1


def test_retryable_transport_failure_is_bounded_to_two_fake_calls() -> None:
    runtime, resolver, transport, clock = _runtime(
        [
            TransportFailure("timeout", retryable=True),
            TransportFailure("timeout", retryable=True),
        ]
    )

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.TIMEOUT
    assert result.error.retryable is True
    assert resolver.call_count == 2
    assert len(transport.calls) == 2
    assert clock.sleeps == [0.25]


@pytest.mark.parametrize(
    "response",
    [
        _success_response(status="incomplete"),
        _success_response(model="different-model"),
        _success_response(content=[{"type": "refusal", "refusal": "no"}]),
        HTTPTransportResponse(status_code=200, headers={}, body=b"not-json"),
    ],
)
def test_incomplete_refusal_model_drift_and_malformed_json_fail_closed(
    response: HTTPTransportResponse,
) -> None:
    runtime, _, _, _ = _runtime([response])

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.INVALID_RESPONSE
    assert result.output is None


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [(4_097, 1), (1, 513)],
)
def test_fake_response_cannot_exceed_token_budget(
    input_tokens: int,
    output_tokens: int,
) -> None:
    runtime, _, _, _ = _runtime(
        [_success_response(input_tokens=input_tokens, output_tokens=output_tokens)]
    )

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.BUDGET_EXCEEDED
    assert result.output is None


def test_precancelled_request_never_resolves_credential_or_sends_transport() -> None:
    runtime, resolver, transport, _ = _runtime([_success_response()])
    cancellation = CancellationToken()
    cancellation.cancel()

    result = runtime.run(
        build_p14c_synthetic_request(),
        cancellation=cancellation,
    )

    assert result.status == "CANCELLED"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.CANCELLED
    assert resolver.call_count == 0
    assert transport.calls == []
