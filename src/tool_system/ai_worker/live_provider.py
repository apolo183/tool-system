from __future__ import annotations

import hashlib
import http.client
import json
import os
import socket
import ssl
import threading
import time
from dataclasses import asdict, dataclass
from typing import Callable, Mapping, Protocol

from tool_system.ai_worker.contract import (
    AIModelSpec,
    AIWorkerBudget,
    AIWorkerError,
    AIWorkerErrorCode,
    AIWorkerRequest,
    AIWorkerResult,
    AIWorkerUsage,
    CancellationSignal,
    ContentAddressedInput,
    PromptSpec,
    ProviderResponse,
    RequestValidation,
    canonical_json_bytes,
    canonical_sha256,
    validate_ai_worker_request_for_mode,
)
from tool_system.ai_worker.runtime import AIWorkerRuntime, InMemoryReplayStore


P14C_SYNTHETIC_FIXTURE: Mapping[str, object] = {
    "constraints": [
        "use only this synthetic fixture",
        "perform no repository access",
        "perform no mutation",
    ],
    "fixture_id": "P14C-001",
    "objective": "Normalize this synthetic provider-boundary verification task.",
}
P14C_SYNTHETIC_FIXTURE_SHA256 = canonical_sha256(P14C_SYNTHETIC_FIXTURE)
P14C_REQUIRED_OUTPUT_KEYS = ("fixture_id", "status", "summary")
P14C_MODEL_CAPABILITIES = ("structured-output", "tool-free-generation")
P14C_RETRYABLE_HTTP_STATUSES = (408, 429, 500, 502, 503, 504)
P14C_RETRYABLE_TRANSPORT_EVENTS = ("connection_failure", "timeout")


@dataclass(frozen=True)
class P14CLiveExecutionPacket:
    packet_id: str
    authorized_by: str
    provider_id: str
    model_id: str
    api_method: str
    api_host: str
    api_port: int
    api_path: str
    tls_verification_required: bool
    redirects_allowed: bool
    proxy_environment_used: bool
    credential_reference: str
    reasoning_effort: str
    store: bool
    tools_allowed: bool
    operation: str
    prompt_id: str
    prompt_version: str
    synthetic_fixture_sha256: str
    max_input_tokens_per_attempt: int
    max_output_tokens_per_attempt: int
    max_total_tokens_per_attempt: int
    max_attempts: int
    max_cumulative_tokens: int
    request_timeout_ms: int
    live_evidence_wall_clock_ms: int
    max_cumulative_cost_microusd: int
    input_price_microusd_per_token: int
    output_price_microusd_per_token: int
    retryable_http_statuses: tuple[int, ...]
    retryable_transport_events: tuple[str, ...]
    max_retry_after_ms: int
    default_backoff_ms: int
    max_response_bytes: int
    remote_target_mutation_authorized: bool
    production_deployment_authorized: bool
    provider_or_model_fallback_allowed: bool

    def canonical_record(self) -> dict[str, object]:
        record = asdict(self)
        record["retryable_http_statuses"] = list(self.retryable_http_statuses)
        record["retryable_transport_events"] = list(self.retryable_transport_events)
        return record

    def sha256(self) -> str:
        return canonical_sha256(self.canonical_record())


P14C_OPENAI_GPT56_LUNA_PACKET = P14CLiveExecutionPacket(
    packet_id="p14c-openai-gpt56-luna-v1",
    authorized_by="user_approved_p14c_named_execution_packet_and_full_lifecycle",
    provider_id="openai",
    model_id="gpt-5.6-luna",
    api_method="POST",
    api_host="api.openai.com",
    api_port=443,
    api_path="/v1/responses",
    tls_verification_required=True,
    redirects_allowed=False,
    proxy_environment_used=False,
    credential_reference="env:OPENAI_API_KEY",
    reasoning_effort="none",
    store=False,
    tools_allowed=False,
    operation="p14c-synthetic-normalize",
    prompt_id="p14c-synthetic-normalizer",
    prompt_version="v1",
    synthetic_fixture_sha256=P14C_SYNTHETIC_FIXTURE_SHA256,
    max_input_tokens_per_attempt=4096,
    max_output_tokens_per_attempt=512,
    max_total_tokens_per_attempt=4608,
    max_attempts=2,
    max_cumulative_tokens=9216,
    request_timeout_ms=20_000,
    live_evidence_wall_clock_ms=45_000,
    max_cumulative_cost_microusd=20_000,
    input_price_microusd_per_token=1,
    output_price_microusd_per_token=6,
    retryable_http_statuses=P14C_RETRYABLE_HTTP_STATUSES,
    retryable_transport_events=P14C_RETRYABLE_TRANSPORT_EVENTS,
    max_retry_after_ms=2000,
    default_backoff_ms=250,
    max_response_bytes=131_072,
    remote_target_mutation_authorized=False,
    production_deployment_authorized=False,
    provider_or_model_fallback_allowed=False,
)


def validate_p14c_packet(packet: object) -> tuple[str, ...]:
    if not isinstance(packet, P14CLiveExecutionPacket):
        return ("execution packet must be P14CLiveExecutionPacket",)
    approved = P14C_OPENAI_GPT56_LUNA_PACKET.canonical_record()
    supplied = packet.canonical_record()
    reasons = [
        f"execution packet field drift: {key}"
        for key in sorted(approved)
        if supplied.get(key) != approved[key]
    ]
    if set(supplied) != set(approved):
        reasons.append("execution packet field set drift")
    return tuple(reasons)


def build_p14c_synthetic_request() -> AIWorkerRequest:
    return AIWorkerRequest(
        request_id="p14c-live-P14C-001",
        idempotency_key="p14c-openai-gpt56-luna-v1:P14C-001",
        attempt_number=1,
        operation=P14C_OPENAI_GPT56_LUNA_PACKET.operation,
        execution_mode="live",
        model=AIModelSpec(
            provider_id=P14C_OPENAI_GPT56_LUNA_PACKET.provider_id,
            model_id=P14C_OPENAI_GPT56_LUNA_PACKET.model_id,
            capabilities=P14C_MODEL_CAPABILITIES,
            context_window_tokens=1_050_000,
        ),
        prompt=PromptSpec(
            prompt_id=P14C_OPENAI_GPT56_LUNA_PACKET.prompt_id,
            prompt_version=P14C_OPENAI_GPT56_LUNA_PACKET.prompt_version,
        ),
        inputs=(
            ContentAddressedInput.build(
                input_id="synthetic-fixture",
                kind="p14c-fixture",
                media_type="application/json",
                payload=dict(P14C_SYNTHETIC_FIXTURE),
                sensitivity="public",
            ),
        ),
        required_capabilities=P14C_MODEL_CAPABILITIES,
        required_output_keys=P14C_REQUIRED_OUTPUT_KEYS,
        budget=AIWorkerBudget(
            max_input_tokens=(
                P14C_OPENAI_GPT56_LUNA_PACKET.max_input_tokens_per_attempt
            ),
            max_output_tokens=(
                P14C_OPENAI_GPT56_LUNA_PACKET.max_output_tokens_per_attempt
            ),
            max_total_tokens=(
                P14C_OPENAI_GPT56_LUNA_PACKET.max_total_tokens_per_attempt
            ),
            timeout_ms=P14C_OPENAI_GPT56_LUNA_PACKET.request_timeout_ms,
            max_cost_microunits=(
                P14C_OPENAI_GPT56_LUNA_PACKET.max_cumulative_cost_microusd
            ),
        ),
        metadata={},
        writes_target_repo=False,
        executes_target_repo_mutation=False,
        production_deployment=False,
    )


class P14CLiveExecutionGuard:
    boundary_name = "P14C named live-provider"
    invocation_evidence = "ai_worker.p14c_live_provider.invoked"

    def __init__(self, packet: P14CLiveExecutionPacket) -> None:
        reasons = validate_p14c_packet(packet)
        if reasons:
            raise ValueError("; ".join(reasons))
        self.packet = packet

    def validate_request(self, request: AIWorkerRequest) -> RequestValidation:
        base = validate_ai_worker_request_for_mode(
            request,
            expected_execution_mode="live",
            stage_label="P14C",
        )
        reasons = list(base.reasons)
        expected = build_p14c_synthetic_request()

        exact_fields = {
            "request_id": (request.request_id, expected.request_id),
            "idempotency_key": (
                request.idempotency_key,
                expected.idempotency_key,
            ),
            "attempt_number": (request.attempt_number, expected.attempt_number),
            "operation": (request.operation, expected.operation),
            "model": (request.model, expected.model),
            "prompt": (request.prompt, expected.prompt),
            "required_capabilities": (
                request.required_capabilities,
                expected.required_capabilities,
            ),
            "required_output_keys": (
                request.required_output_keys,
                expected.required_output_keys,
            ),
            "budget": (request.budget, expected.budget),
            "metadata": (dict(request.metadata), {}),
        }
        for name, (actual, wanted) in exact_fields.items():
            if actual != wanted:
                reasons.append(f"P14C request field drift: {name}")

        if len(request.inputs) != 1:
            reasons.append("P14C requires exactly one synthetic input")
        elif request.inputs[0] != expected.inputs[0]:
            reasons.append("P14C synthetic fixture or content hash drift")

        if reasons:
            return RequestValidation(
                error_code=base.error_code or AIWorkerErrorCode.INVALID_REQUEST,
                reasons=tuple(dict.fromkeys(reasons)),
            )
        return RequestValidation(error_code=None, reasons=())

    def provider_boundary_reasons(self, provider: object) -> tuple[str, ...]:
        expected = {
            "provider_id": self.packet.provider_id,
            "model_id": self.packet.model_id,
            "capabilities": P14C_MODEL_CAPABILITIES,
            "provider_kind": "live_provider",
            "execution_mode": "live",
            "calls_external_provider": True,
            "uses_credentials": True,
            "network_access": True,
            "packet_sha256": self.packet.sha256(),
        }
        reasons: list[str] = []
        for name, value in expected.items():
            actual = getattr(provider, name, None)
            matches = actual is value if isinstance(value, bool) else actual == value
            if not matches:
                reasons.append(f"provider {name} must match P14C packet")
        return tuple(reasons)


@dataclass(frozen=True)
class HTTPJSONResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class LiveTransportError(Exception):
    stable_code = "connection_failure"
    retryable = True


class LiveTransportTimeout(LiveTransportError):
    stable_code = "timeout"


class LiveTransportCancelled(LiveTransportError):
    stable_code = "cancelled"
    retryable = False


class LiveTransportResponseTooLarge(LiveTransportError):
    stable_code = "response_too_large"
    retryable = False


class LiveJSONTransport(Protocol):
    def post_json(
        self,
        *,
        host: str,
        port: int,
        path: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_ms: int,
        cancellation: CancellationSignal | None,
        max_response_bytes: int,
    ) -> HTTPJSONResponse: ...


class HTTPSJSONTransport:
    """Direct TLS transport. It never reads proxy environment variables."""

    def post_json(
        self,
        *,
        host: str,
        port: int,
        path: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_ms: int,
        cancellation: CancellationSignal | None,
        max_response_bytes: int,
    ) -> HTTPJSONResponse:
        packet = P14C_OPENAI_GPT56_LUNA_PACKET
        if (host, port, path) != (packet.api_host, packet.api_port, packet.api_path):
            raise LiveTransportError("network destination is outside P14C packet")
        if cancellation is not None and cancellation.is_cancelled():
            raise LiveTransportCancelled("cancelled before transport")

        body = canonical_json_bytes(dict(payload))
        context = ssl.create_default_context()
        connection = http.client.HTTPSConnection(
            host=host,
            port=port,
            timeout=max(0.001, timeout_ms / 1000),
            context=context,
        )
        done = threading.Event()
        outcome: dict[str, object] = {}

        def execute() -> None:
            try:
                connection.request(
                    "POST",
                    path,
                    body=body,
                    headers=dict(headers),
                )
                response = connection.getresponse()
                chunks: list[bytes] = []
                length = 0
                while True:
                    chunk = response.read(16_384)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > max_response_bytes:
                        raise LiveTransportResponseTooLarge(
                            "provider response exceeded byte ceiling"
                        )
                    chunks.append(chunk)
                outcome["response"] = HTTPJSONResponse(
                    status=response.status,
                    headers={
                        key.lower(): value for key, value in response.getheaders()
                    },
                    body=b"".join(chunks),
                )
            except LiveTransportError as exc:
                outcome["error"] = exc
            except (TimeoutError, socket.timeout) as exc:
                outcome["error"] = LiveTransportTimeout(type(exc).__name__)
            except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
                outcome["error"] = LiveTransportError(type(exc).__name__)
            except Exception as exc:  # fail closed and expose type only
                outcome["error"] = LiveTransportError(type(exc).__name__)
            finally:
                connection.close()
                done.set()

        worker = threading.Thread(target=execute, name="p14c-openai-https", daemon=True)
        worker.start()
        deadline = time.monotonic() + (timeout_ms / 1000)
        terminal: LiveTransportError | None = None
        while not done.wait(0.025):
            if cancellation is not None and cancellation.is_cancelled():
                terminal = LiveTransportCancelled("cancelled in flight")
                connection.close()
                break
            if time.monotonic() >= deadline:
                terminal = LiveTransportTimeout("transport deadline exceeded")
                connection.close()
                break

        if terminal is not None:
            worker.join(max(0.1, timeout_ms / 1000 + 0.5))
            raise terminal
        worker.join()
        error = outcome.get("error")
        if isinstance(error, LiveTransportError):
            raise error
        response = outcome.get("response")
        if not isinstance(response, HTTPJSONResponse):
            raise LiveTransportError("transport produced no response")
        return response


@dataclass(frozen=True)
class LiveAttemptAudit:
    attempt_number: int
    terminal: str
    http_status_class: str | None
    transport_code: str | None
    duration_ms: int
    retryable: bool
    conservative_cost_microusd: int

    def to_record(self) -> dict[str, object]:
        return asdict(self)


class CredentialUnavailableError(Exception):
    pass


def credential_reference_available(
    reference: str = P14C_OPENAI_GPT56_LUNA_PACKET.credential_reference,
) -> bool:
    try:
        _resolve_environment_credential(reference)
    except CredentialUnavailableError:
        return False
    return True


def _resolve_environment_credential(reference: str) -> str:
    if reference != "env:OPENAI_API_KEY":
        raise CredentialUnavailableError("credential reference mismatch")
    value = os.environ.get("OPENAI_API_KEY")
    if not isinstance(value, str) or not value.strip():
        raise CredentialUnavailableError("credential reference unavailable")
    if value != value.strip() or len(value) > 4096:
        raise CredentialUnavailableError("credential format invalid")
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        raise CredentialUnavailableError("credential format invalid")
    return value


class OpenAIResponsesProvider:
    provider_id = "openai"
    model_id = "gpt-5.6-luna"
    capabilities = P14C_MODEL_CAPABILITIES
    provider_kind = "live_provider"
    execution_mode = "live"
    calls_external_provider = True
    uses_credentials = True
    network_access = True

    def __init__(
        self,
        packet: P14CLiveExecutionPacket = P14C_OPENAI_GPT56_LUNA_PACKET,
        *,
        transport: LiveJSONTransport | None = None,
        credential_resolver: Callable[[str], str] = _resolve_environment_credential,
        sleeper: Callable[[float], None] = time.sleep,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        reasons = validate_p14c_packet(packet)
        if reasons:
            raise ValueError("; ".join(reasons))
        self.packet = packet
        self.packet_sha256 = packet.sha256()
        self.transport = transport or HTTPSJSONTransport()
        self.credential_resolver = credential_resolver
        self.sleeper = sleeper
        self.clock_ms = clock_ms or (lambda: time.monotonic_ns() // 1_000_000)
        self._attempt_audit: tuple[LiveAttemptAudit, ...] = ()
        self._audit_lock = threading.Lock()

    @property
    def attempt_count(self) -> int:
        with self._audit_lock:
            return len(self._attempt_audit)

    def live_audit_record(self) -> dict[str, object]:
        with self._audit_lock:
            attempts = [item.to_record() for item in self._attempt_audit]
        return {
            "packet_id": self.packet.packet_id,
            "packet_sha256": self.packet_sha256,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "credential_reference": self.packet.credential_reference,
            "attempt_count": len(attempts),
            "attempts": attempts,
            "remote_target_mutation": False,
            "production_deployment": False,
        }

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: CancellationSignal | None = None,
    ) -> ProviderResponse:
        self._set_audits([])
        guard = P14CLiveExecutionGuard(self.packet)
        validation = guard.validate_request(request)
        if not validation.ok:
            return _provider_error(
                AIWorkerErrorCode.INVALID_REQUEST,
                "P14C live request failed exact packet validation",
                retryable=False,
            )
        if cancellation is not None and cancellation.is_cancelled():
            return _provider_error(
                AIWorkerErrorCode.CANCELLED,
                "P14C live request cancelled before credential access",
                retryable=False,
            )

        try:
            credential = self.credential_resolver(self.packet.credential_reference)
        except CredentialUnavailableError:
            return _provider_error(
                AIWorkerErrorCode.PROVIDER_FAILURE,
                "credential reference unavailable",
                retryable=False,
            )
        except Exception as exc:
            return _provider_error(
                AIWorkerErrorCode.PROVIDER_FAILURE,
                f"credential resolver raised {type(exc).__name__}",
                retryable=False,
            )

        payload = _responses_request_payload(request)
        headers = {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
            "User-Agent": "tool-system-p14c/1.0",
        }
        start_ms = self.clock_ms()
        reserved_cost = 0
        audits: list[LiveAttemptAudit] = []

        for attempt in range(1, self.packet.max_attempts + 1):
            elapsed = max(0, self.clock_ms() - start_ms)
            remaining = self.packet.live_evidence_wall_clock_ms - elapsed
            if remaining <= 0:
                self._set_audits(audits)
                return _provider_error(
                    AIWorkerErrorCode.TIMEOUT,
                    "P14C live evidence wall-clock budget exhausted",
                    retryable=False,
                    usage=AIWorkerUsage(
                        duration_ms=elapsed,
                        cost_microunits=reserved_cost,
                    ),
                )
            if cancellation is not None and cancellation.is_cancelled():
                self._set_audits(audits)
                return _provider_error(
                    AIWorkerErrorCode.CANCELLED,
                    "P14C live request cancelled before dispatch",
                    retryable=False,
                    usage=AIWorkerUsage(
                        duration_ms=elapsed,
                        cost_microunits=reserved_cost,
                    ),
                )

            attempt_start = self.clock_ms()
            try:
                response = self.transport.post_json(
                    host=self.packet.api_host,
                    port=self.packet.api_port,
                    path=self.packet.api_path,
                    headers=headers,
                    payload=payload,
                    timeout_ms=min(self.packet.request_timeout_ms, remaining),
                    cancellation=cancellation,
                    max_response_bytes=self.packet.max_response_bytes,
                )
            except LiveTransportCancelled:
                reserved_cost += self._max_attempt_cost()
                audits.append(
                    self._attempt_audit_record(
                        attempt,
                        attempt_start,
                        terminal="CANCELLED",
                        transport_code="cancelled",
                        retryable=False,
                        cost=reserved_cost,
                    )
                )
                self._set_audits(audits)
                return _provider_error(
                    AIWorkerErrorCode.CANCELLED,
                    "P14C transport cancelled",
                    retryable=False,
                    usage=self._terminal_usage(start_ms, reserved_cost),
                )
            except LiveTransportError as exc:
                reserved_cost += self._max_attempt_cost()
                retryable = (
                    exc.retryable
                    and exc.stable_code in self.packet.retryable_transport_events
                    and attempt < self.packet.max_attempts
                )
                audits.append(
                    self._attempt_audit_record(
                        attempt,
                        attempt_start,
                        terminal="TRANSPORT_ERROR",
                        transport_code=exc.stable_code,
                        retryable=retryable,
                        cost=reserved_cost,
                    )
                )
                if retryable and self._retry_budget_allows(
                    start_ms, reserved_cost, self.packet.default_backoff_ms
                ):
                    if not self._sleep_with_cancellation(
                        self.packet.default_backoff_ms,
                        cancellation,
                    ):
                        self._set_audits(audits)
                        return _provider_error(
                            AIWorkerErrorCode.CANCELLED,
                            "P14C retry backoff cancelled",
                            retryable=False,
                            usage=self._terminal_usage(start_ms, reserved_cost),
                        )
                    continue
                self._set_audits(audits)
                code = (
                    AIWorkerErrorCode.TIMEOUT
                    if exc.stable_code == "timeout"
                    else AIWorkerErrorCode.PROVIDER_FAILURE
                )
                return _provider_error(
                    code,
                    f"P14C transport returned {exc.stable_code}",
                    retryable=retryable,
                    usage=self._terminal_usage(start_ms, reserved_cost),
                )

            if cancellation is not None and cancellation.is_cancelled():
                reserved_cost += self._max_attempt_cost()
                audits.append(
                    self._attempt_audit_record(
                        attempt,
                        attempt_start,
                        terminal="CANCELLED",
                        http_status=response.status,
                        retryable=False,
                        cost=reserved_cost,
                    )
                )
                self._set_audits(audits)
                return _provider_error(
                    AIWorkerErrorCode.CANCELLED,
                    "P14C live request cancelled after transport",
                    retryable=False,
                    usage=self._terminal_usage(start_ms, reserved_cost),
                )

            if not 200 <= response.status < 300:
                reserved_cost += self._max_attempt_cost()
                retryable = (
                    response.status in self.packet.retryable_http_statuses
                    and attempt < self.packet.max_attempts
                )
                retry_after_header = response.headers.get("retry-after")
                retry_after_ms = _retry_after_ms(
                    retry_after_header,
                    maximum=self.packet.max_retry_after_ms,
                )
                if retry_after_header is None:
                    retry_after_ms = self.packet.default_backoff_ms
                elif retry_after_ms is None:
                    retryable = False
                audits.append(
                    self._attempt_audit_record(
                        attempt,
                        attempt_start,
                        terminal="HTTP_ERROR",
                        http_status=response.status,
                        retryable=retryable,
                        cost=reserved_cost,
                    )
                )
                if retryable and self._retry_budget_allows(
                    start_ms, reserved_cost, retry_after_ms
                ):
                    if not self._sleep_with_cancellation(
                        retry_after_ms,
                        cancellation,
                    ):
                        self._set_audits(audits)
                        return _provider_error(
                            AIWorkerErrorCode.CANCELLED,
                            "P14C retry backoff cancelled",
                            retryable=False,
                            usage=self._terminal_usage(start_ms, reserved_cost),
                        )
                    continue
                self._set_audits(audits)
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    f"P14C provider returned HTTP {response.status}",
                    retryable=retryable,
                    usage=self._terminal_usage(start_ms, reserved_cost),
                )

            parsed = _parse_openai_response(response.body, self.packet)
            if isinstance(parsed, AIWorkerError):
                audits.append(
                    self._attempt_audit_record(
                        attempt,
                        attempt_start,
                        terminal="INVALID_RESPONSE",
                        http_status=response.status,
                        retryable=False,
                        cost=reserved_cost,
                    )
                )
                self._set_audits(audits)
                return ProviderResponse(
                    output=None,
                    usage=self._terminal_usage(start_ms, reserved_cost),
                    error=parsed,
                )

            output, input_tokens, output_tokens = parsed
            cost = (
                reserved_cost
                + input_tokens * self.packet.input_price_microusd_per_token
                + output_tokens * self.packet.output_price_microusd_per_token
            )
            usage = AIWorkerUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=max(0, self.clock_ms() - start_ms),
                cost_microunits=cost,
            )
            audits.append(
                self._attempt_audit_record(
                    attempt,
                    attempt_start,
                    terminal="PASS",
                    http_status=response.status,
                    retryable=False,
                    cost=cost,
                )
            )
            self._set_audits(audits)
            if cost > self.packet.max_cumulative_cost_microusd:
                return _provider_error(
                    AIWorkerErrorCode.BUDGET_EXCEEDED,
                    "P14C cumulative cost exceeded",
                    retryable=False,
                    usage=usage,
                )
            return ProviderResponse(output=output, usage=usage)

        self._set_audits(audits)
        return _provider_error(
            AIWorkerErrorCode.INTERNAL_FAILURE,
            "P14C attempt loop ended unexpectedly",
            retryable=False,
            usage=self._terminal_usage(start_ms, reserved_cost),
        )

    def _max_attempt_cost(self) -> int:
        return (
            self.packet.max_input_tokens_per_attempt
            * self.packet.input_price_microusd_per_token
            + self.packet.max_output_tokens_per_attempt
            * self.packet.output_price_microusd_per_token
        )

    def _terminal_usage(self, start_ms: int, cost: int) -> AIWorkerUsage:
        return AIWorkerUsage(
            duration_ms=max(0, self.clock_ms() - start_ms),
            cost_microunits=min(cost, self.packet.max_cumulative_cost_microusd),
        )

    def _attempt_audit_record(
        self,
        attempt: int,
        start_ms: int,
        *,
        terminal: str,
        retryable: bool,
        cost: int,
        http_status: int | None = None,
        transport_code: str | None = None,
    ) -> LiveAttemptAudit:
        return LiveAttemptAudit(
            attempt_number=attempt,
            terminal=terminal,
            http_status_class=(
                f"{http_status // 100}xx" if http_status is not None else None
            ),
            transport_code=transport_code,
            duration_ms=max(0, self.clock_ms() - start_ms),
            retryable=retryable,
            conservative_cost_microusd=min(
                cost,
                self.packet.max_cumulative_cost_microusd,
            ),
        )

    def _retry_budget_allows(
        self,
        start_ms: int,
        reserved_cost: int,
        delay_ms: int,
    ) -> bool:
        next_max_cost = reserved_cost + self._max_attempt_cost()
        elapsed = max(0, self.clock_ms() - start_ms)
        next_deadline = elapsed + delay_ms + self.packet.request_timeout_ms
        return (
            next_max_cost <= self.packet.max_cumulative_cost_microusd
            and next_deadline <= self.packet.live_evidence_wall_clock_ms
        )

    def _sleep_with_cancellation(
        self,
        delay_ms: int,
        cancellation: CancellationSignal | None,
    ) -> bool:
        remaining = delay_ms
        while remaining > 0:
            if cancellation is not None and cancellation.is_cancelled():
                return False
            step = min(remaining, 50)
            self.sleeper(step / 1000)
            remaining -= step
        return cancellation is None or not cancellation.is_cancelled()

    def _set_audits(self, audits: list[LiveAttemptAudit]) -> None:
        with self._audit_lock:
            self._attempt_audit = tuple(audits)


class BoundedLiveAIWorkerRuntime:
    def __init__(
        self,
        packet: P14CLiveExecutionPacket = P14C_OPENAI_GPT56_LUNA_PACKET,
        *,
        provider: OpenAIResponsesProvider | None = None,
        replay_store: InMemoryReplayStore | None = None,
    ) -> None:
        reasons = validate_p14c_packet(packet)
        if reasons:
            raise ValueError("; ".join(reasons))
        self.packet = packet
        self.provider = provider or OpenAIResponsesProvider(packet)
        self._runtime = AIWorkerRuntime(
            self.provider,
            replay_store=replay_store,
            execution_guard=P14CLiveExecutionGuard(packet),
        )

    def run(
        self,
        request: AIWorkerRequest,
        *,
        cancellation: CancellationSignal | None = None,
    ) -> AIWorkerResult:
        return self._runtime.run(request, cancellation=cancellation)

    def live_audit_record(self) -> dict[str, object]:
        return self.provider.live_audit_record()


def _responses_request_payload(request: AIWorkerRequest) -> dict[str, object]:
    input_payload = {
        "inputs": [
            {
                "input_id": item.input_id,
                "kind": item.kind,
                "payload": item.payload,
                "payload_sha256": item.payload_sha256,
            }
            for item in request.inputs
        ],
        "operation": request.operation,
        "prompt_id": request.prompt.prompt_id,
        "prompt_version": request.prompt.prompt_version,
    }
    return {
        "model": request.model.model_id,
        "instructions": (
            "Normalize only the supplied synthetic fixture. Return the strict JSON "
            "schema. Do not use tools, external data, repository data, or mutations."
        ),
        "input": canonical_json_bytes(input_payload).decode("utf-8"),
        "reasoning": {"effort": "none"},
        "max_output_tokens": request.budget.max_output_tokens,
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "p14c_synthetic_fixture_result",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "fixture_id": {
                            "type": "string",
                            "enum": ["P14C-001"],
                        },
                        "status": {"type": "string", "enum": ["PASS"]},
                        "summary": {
                            "type": "string",
                        },
                    },
                    "required": list(P14C_REQUIRED_OUTPUT_KEYS),
                    "additionalProperties": False,
                },
            }
        },
    }


def _parse_openai_response(
    body: bytes,
    packet: P14CLiveExecutionPacket,
) -> tuple[dict[str, object], int, int] | AIWorkerError:
    try:
        response = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider response is not valid JSON",
        )
    if not isinstance(response, dict):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider response must be a mapping",
        )
    if response.get("model") != packet.model_id:
        return AIWorkerError(
            code=AIWorkerErrorCode.PROVIDER_MISMATCH,
            message="provider response model does not match packet",
        )

    usage = response.get("usage")
    if not isinstance(usage, dict):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider response usage is missing",
        )
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in (input_tokens, output_tokens, total_tokens)
    ):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider response usage is invalid",
        )
    assert isinstance(input_tokens, int)
    assert isinstance(output_tokens, int)
    assert isinstance(total_tokens, int)
    if total_tokens != input_tokens + output_tokens:
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider total token usage is inconsistent",
        )

    output_items = response.get("output")
    texts: list[str] = []
    if isinstance(output_items, list):
        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    text = part.get("text")
                    if isinstance(text, str):
                        texts.append(text)
    if len(texts) != 1:
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider response must contain exactly one output_text",
        )
    try:
        output = json.loads(texts[0])
    except json.JSONDecodeError:
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider structured output is invalid JSON",
        )
    if not isinstance(output, dict):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider structured output must be a mapping",
        )
    if set(output) != set(P14C_REQUIRED_OUTPUT_KEYS):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider structured output keys do not match schema",
        )
    summary = output.get("summary")
    if (
        output.get("fixture_id") != "P14C-001"
        or output.get("status") != "PASS"
        or not isinstance(summary, str)
        or not 1 <= len(summary) <= 160
    ):
        return AIWorkerError(
            code=AIWorkerErrorCode.INVALID_RESPONSE,
            message="provider structured output values do not match schema",
        )
    return dict(output), input_tokens, output_tokens


def _retry_after_ms(value: str | None, *, maximum: int) -> int | None:
    if value is None:
        return None
    try:
        seconds = float(value.strip())
    except (TypeError, ValueError):
        return None
    if seconds < 0 or seconds * 1000 > maximum:
        return None
    return int(seconds * 1000)


def _provider_error(
    code: AIWorkerErrorCode,
    message: str,
    *,
    retryable: bool,
    usage: AIWorkerUsage | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        output=None,
        usage=usage or AIWorkerUsage(),
        error=AIWorkerError(code=code, message=message, retryable=retryable),
    )


def p14c_packet_sha256() -> str:
    return hashlib.sha256(
        canonical_json_bytes(P14C_OPENAI_GPT56_LUNA_PACKET.canonical_record())
    ).hexdigest()
