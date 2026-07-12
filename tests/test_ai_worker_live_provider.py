from __future__ import annotations

import json
import threading
from dataclasses import replace

import pytest

from tool_system.ai_worker import (
    AIWorkerErrorCode,
    AIWorkerRuntime,
    BoundedLiveAIWorkerRuntime,
    CancellationToken,
    CredentialUnavailableError,
    HTTPJSONResponse,
    HTTPSJSONTransport,
    LiveTransportCancelled,
    LiveTransportError,
    LiveTransportTimeout,
    OpenAIResponsesProvider,
    P14CLiveExecutionGuard,
    P14C_OPENAI_GPT56_LUNA_PACKET,
    build_p14c_synthetic_request,
    p14c_packet_sha256,
    validate_p14c_packet,
)


def _success_response(
    *,
    model: str = "gpt-5.6-luna",
    input_tokens: int = 100,
    output_tokens: int = 20,
    output: dict[str, object] | None = None,
) -> HTTPJSONResponse:
    structured = output or {
        "fixture_id": "P14C-001",
        "status": "PASS",
        "summary": "Synthetic fixture normalized without repository access.",
    }
    body = {
        "id": "resp_synthetic",
        "model": model,
        "output": [
            {
                "type": "reasoning",
                "summary": [],
            },
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(structured, sort_keys=True),
                    }
                ],
            },
        ],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    }
    return HTTPJSONResponse(
        status=200,
        headers={"x-request-id": "synthetic-provider-request"},
        body=json.dumps(body).encode("utf-8"),
    )


class _SequenceTransport:
    def __init__(self, outcomes: list[HTTPJSONResponse | Exception]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def post_json(self, **kwargs: object) -> HTTPJSONResponse:
        self.calls.append(dict(kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _runtime(
    transport: _SequenceTransport,
    *,
    credential: str = "p14c-test-secret-must-not-escape",
    sleeper=lambda _: None,
) -> BoundedLiveAIWorkerRuntime:
    provider = OpenAIResponsesProvider(
        transport=transport,
        credential_resolver=lambda reference: credential,
        sleeper=sleeper,
    )
    return BoundedLiveAIWorkerRuntime(provider=provider)


def test_exact_packet_and_synthetic_request_are_content_bound() -> None:
    packet = P14C_OPENAI_GPT56_LUNA_PACKET
    request = build_p14c_synthetic_request()

    assert validate_p14c_packet(packet) == ()
    assert packet.sha256() == p14c_packet_sha256()
    assert packet.packet_id == "p14c-openai-gpt56-luna-v1"
    assert packet.credential_reference == "env:OPENAI_API_KEY"
    assert packet.max_attempts == 2
    assert packet.max_cumulative_tokens == 9216
    assert packet.max_cumulative_cost_microusd == 20_000
    assert request.execution_mode == "live"
    assert request.inputs[0].sensitivity == "public"
    assert request.inputs[0].payload_sha256 == packet.synthetic_fixture_sha256
    assert request.writes_target_repo is False
    assert request.executes_target_repo_mutation is False
    assert request.production_deployment is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider_id", "other-provider"),
        ("model_id", "gpt-5.6-sol"),
        ("api_host", "example.com"),
        ("api_path", "/v1/other"),
        ("credential_reference", "env:OTHER_KEY"),
        ("max_attempts", 3),
        ("max_cumulative_cost_microusd", 20_001),
        ("provider_or_model_fallback_allowed", True),
        ("remote_target_mutation_authorized", True),
        ("production_deployment_authorized", True),
    ],
)
def test_any_packet_drift_is_rejected_before_runtime(
    field: str,
    value: object,
) -> None:
    drifted = replace(P14C_OPENAI_GPT56_LUNA_PACKET, **{field: value})

    reasons = validate_p14c_packet(drifted)

    assert reasons == (f"execution packet field drift: {field}",)
    with pytest.raises(ValueError, match="execution packet field drift"):
        P14CLiveExecutionGuard(drifted)
    with pytest.raises(ValueError, match="execution packet field drift"):
        OpenAIResponsesProvider(drifted)


def test_live_success_uses_exact_request_and_emits_only_redacted_audit() -> None:
    secret = "p14c-test-secret-must-not-escape"
    transport = _SequenceTransport([_success_response()])
    runtime = _runtime(transport, credential=secret)
    request = build_p14c_synthetic_request()

    result = runtime.run(request)

    assert result.status == "PASS"
    assert result.output == {
        "fixture_id": "P14C-001",
        "status": "PASS",
        "summary": "Synthetic fixture normalized without repository access.",
    }
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 20
    assert result.usage.cost_microunits == 220
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["host"] == "api.openai.com"
    assert call["port"] == 443
    assert call["path"] == "/v1/responses"
    headers = call["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == f"Bearer {secret}"
    payload = call["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "gpt-5.6-luna"
    assert payload["reasoning"] == {"effort": "none"}
    assert payload["store"] is False
    assert "tools" not in payload
    rendered_payload = json.dumps(payload).lower()
    assert "/workspace/" not in rendered_payload
    assert "finance-us" not in rendered_payload
    assert "src/tool_system" not in rendered_payload

    rendered = json.dumps(
        {
            "result": result.to_audit_record(),
            "live": runtime.live_audit_record(),
        },
        sort_keys=True,
    )
    assert secret not in rendered
    assert "Synthetic fixture normalized" not in rendered
    assert request.idempotency_key not in rendered
    assert runtime.live_audit_record()["attempt_count"] == 1
    assert runtime.live_audit_record()["attempts"][0]["terminal"] == "PASS"


def test_default_p14b_runtime_still_blocks_live_provider_before_credentials() -> None:
    credential_reads = 0
    transport = _SequenceTransport([_success_response()])

    def credential_resolver(reference: str) -> str:
        nonlocal credential_reads
        credential_reads += 1
        return "must-not-be-read"

    provider = OpenAIResponsesProvider(
        transport=transport,
        credential_resolver=credential_resolver,
    )

    result = AIWorkerRuntime(provider).run(build_p14c_synthetic_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.INVALID_REQUEST
    assert credential_reads == 0
    assert transport.calls == []


@pytest.mark.parametrize(
    "drift_request",
    [
        replace(build_p14c_synthetic_request(), operation="other-operation"),
        replace(
            build_p14c_synthetic_request(),
            model=replace(
                build_p14c_synthetic_request().model,
                model_id="gpt-5.6-sol",
            ),
        ),
        replace(
            build_p14c_synthetic_request(),
            metadata={"trace_id": "not-authorized"},
        ),
        replace(build_p14c_synthetic_request(), writes_target_repo=True),
    ],
)
def test_request_drift_blocks_before_credential_or_network(
    drift_request: object,
) -> None:
    credential_reads = 0
    transport = _SequenceTransport([_success_response()])

    def credential_resolver(reference: str) -> str:
        nonlocal credential_reads
        credential_reads += 1
        return "must-not-be-read"

    provider = OpenAIResponsesProvider(
        transport=transport,
        credential_resolver=credential_resolver,
    )
    runtime = BoundedLiveAIWorkerRuntime(provider=provider)

    result = runtime.run(drift_request)  # type: ignore[arg-type]

    assert result.status == "BLOCK"
    assert credential_reads == 0
    assert transport.calls == []


def test_retry_is_bounded_and_reserves_unknown_first_attempt_cost() -> None:
    transport = _SequenceTransport(
        [
            HTTPJSONResponse(status=429, headers={"retry-after": "0"}, body=b"secret"),
            _success_response(input_tokens=100, output_tokens=20),
        ]
    )
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "PASS"
    assert len(transport.calls) == 2
    assert result.usage.cost_microunits == 7_388
    audit = runtime.live_audit_record()
    assert audit["attempt_count"] == 2
    assert [item["terminal"] for item in audit["attempts"]] == [
        "HTTP_ERROR",
        "PASS",
    ]
    assert [item["http_status_class"] for item in audit["attempts"]] == [
        "4xx",
        "2xx",
    ]


def test_nonretryable_http_error_never_retries_or_leaks_body() -> None:
    marker = "raw-provider-error-secret"
    transport = _SequenceTransport(
        [HTTPJSONResponse(status=401, headers={}, body=marker.encode())]
    )
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.PROVIDER_FAILURE
    assert len(transport.calls) == 1
    assert marker not in json.dumps(result.to_record())
    assert marker not in json.dumps(runtime.live_audit_record())


def test_retry_after_above_approved_ceiling_fails_without_retry() -> None:
    transport = _SequenceTransport(
        [
            HTTPJSONResponse(
                status=429, headers={"retry-after": "3"}, body=b"discarded"
            ),
            _success_response(),
        ]
    )
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert len(transport.calls) == 1
    assert runtime.live_audit_record()["attempts"][0]["retryable"] is False


def test_transport_timeout_retries_once_then_succeeds_with_cumulative_bound() -> None:
    transport = _SequenceTransport(
        [LiveTransportTimeout("raw-timeout-secret"), _success_response()]
    )
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "PASS"
    assert len(transport.calls) == 2
    assert result.usage.cost_microunits == 7_388
    rendered = json.dumps(runtime.live_audit_record())
    assert "raw-timeout-secret" not in rendered
    assert "timeout" in rendered


def test_inflight_cancellation_is_terminal_and_never_retries() -> None:
    cancellation = CancellationToken()

    class CancellingTransport:
        calls = 0

        def post_json(self, **kwargs: object) -> HTTPJSONResponse:
            self.calls += 1
            cancellation.cancel()
            raise LiveTransportCancelled("raw-cancel-secret")

    transport = CancellingTransport()
    provider = OpenAIResponsesProvider(
        transport=transport,
        credential_resolver=lambda _: "test-secret",
    )
    runtime = BoundedLiveAIWorkerRuntime(provider=provider)

    result = runtime.run(
        build_p14c_synthetic_request(),
        cancellation=cancellation,
    )

    assert result.status == "CANCELLED"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.CANCELLED
    assert transport.calls == 1
    assert runtime.live_audit_record()["attempt_count"] == 1
    assert "raw-cancel-secret" not in json.dumps(result.to_record())


def test_cancellation_during_retry_backoff_prevents_second_attempt() -> None:
    cancellation = CancellationToken()
    transport = _SequenceTransport(
        [
            HTTPJSONResponse(status=429, headers={}, body=b"discarded"),
            _success_response(),
        ]
    )

    def sleeper(_: float) -> None:
        cancellation.cancel()

    runtime = _runtime(transport, sleeper=sleeper)

    result = runtime.run(
        build_p14c_synthetic_request(),
        cancellation=cancellation,
    )

    assert result.status == "CANCELLED"
    assert len(transport.calls) == 1


def test_credential_failure_is_sanitized_and_performs_no_network() -> None:
    marker = "raw-credential-secret"
    transport = _SequenceTransport([_success_response()])

    def unavailable(reference: str) -> str:
        raise CredentialUnavailableError(marker)

    provider = OpenAIResponsesProvider(
        transport=transport,
        credential_resolver=unavailable,
    )
    result = BoundedLiveAIWorkerRuntime(provider=provider).run(
        build_p14c_synthetic_request()
    )

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.PROVIDER_FAILURE
    assert transport.calls == []
    assert marker not in json.dumps(result.to_record())


@pytest.mark.parametrize(
    "response",
    [
        _success_response(model="gpt-5.6-sol"),
        _success_response(output={"fixture_id": "P14C-001", "status": "PASS"}),
        _success_response(
            output={
                "fixture_id": "P14C-001",
                "status": "PASS",
                "summary": "ok",
                "extra": "not allowed",
            }
        ),
    ],
)
def test_model_or_strict_output_drift_is_invalid_and_not_retried(
    response: HTTPJSONResponse,
) -> None:
    transport = _SequenceTransport([response])
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "ERROR"
    assert result.error is not None
    assert result.error.code in {
        AIWorkerErrorCode.INVALID_RESPONSE,
        AIWorkerErrorCode.PROVIDER_MISMATCH,
    }
    assert len(transport.calls) == 1


def test_usage_over_budget_is_blocked_by_reused_p14b_result_gate() -> None:
    transport = _SequenceTransport([_success_response(output_tokens=513)])
    runtime = _runtime(transport)

    result = runtime.run(build_p14c_synthetic_request())

    assert result.status == "BLOCK"
    assert result.error is not None
    assert result.error.code is AIWorkerErrorCode.BUDGET_EXCEEDED
    assert result.output is None


def test_live_replay_does_not_perform_a_second_provider_attempt() -> None:
    transport = _SequenceTransport([_success_response()])
    runtime = _runtime(transport)
    request = build_p14c_synthetic_request()

    first = runtime.run(request)
    replay = runtime.run(request)

    assert first.status == "PASS"
    assert replay.status == "PASS"
    assert replay.replayed is True
    assert len(transport.calls) == 1


def test_https_transport_closes_inflight_connection_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    close_event = threading.Event()
    cancellation = CancellationToken()

    class BlockingResponse:
        status = 200

        def getheaders(self) -> list[tuple[str, str]]:
            return []

        def read(self, size: int) -> bytes:
            close_event.wait(1)
            return b""

    class FakeConnection:
        def __init__(self, **kwargs: object) -> None:
            pass

        def request(self, *args: object, **kwargs: object) -> None:
            pass

        def getresponse(self) -> BlockingResponse:
            return BlockingResponse()

        def close(self) -> None:
            close_event.set()

    monkeypatch.setattr("http.client.HTTPSConnection", FakeConnection)
    monkeypatch.setattr("ssl.create_default_context", lambda: object())
    timer = threading.Timer(0.05, cancellation.cancel)
    timer.start()
    try:
        with pytest.raises(LiveTransportCancelled):
            HTTPSJSONTransport().post_json(
                host="api.openai.com",
                port=443,
                path="/v1/responses",
                headers={"Authorization": "Bearer test"},
                payload={"synthetic": True},
                timeout_ms=500,
                cancellation=cancellation,
                max_response_bytes=1024,
            )
    finally:
        timer.cancel()
    assert close_event.is_set()


def test_https_transport_rejects_any_other_destination_before_socket_use() -> None:
    with pytest.raises(LiveTransportError):
        HTTPSJSONTransport().post_json(
            host="example.com",
            port=443,
            path="/v1/responses",
            headers={},
            payload={},
            timeout_ms=10,
            cancellation=None,
            max_response_bytes=1024,
        )
