from __future__ import annotations

import http.client
import json
import os
import ssl
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from tool_system.ai_worker.contract import (
    AIModelSpec,
    AIWorkerBudget,
    AIWorkerError,
    AIWorkerErrorCode,
    AIWorkerProvider,
    AIWorkerRequest,
    AIWorkerUsage,
    CancellationSignal,
    ContentAddressedInput,
    PromptSpec,
    ProviderResponse,
    canonical_json_bytes,
    canonical_sha256,
    validate_ai_worker_request,
)

P14C_AUTHORIZATION_PACKET = "P14C-IMPL-v2"
P14C_TOOL_SYSTEM_BASE = "637fe60782ed9e15d58795a0113b84965d6664d2"
P14C_CENTRAL_GOVERNANCE_BASE = "71c89101d3e5f90adfb469f7effef8fe39ddf394"
P14C_FIXTURE_ID = "P14C-001"
OPENAI_PROVIDER_ID = "openai"
OPENAI_MODEL_ID = "gpt-5.6-luna"
OPENAI_HOST = "api.openai.com"
OPENAI_PATH = "/v1/responses"
OPENAI_CREDENTIAL_REFERENCE = "env:OPENAI_API_KEY"
P14C_PROMPT_ID = "p14c-bounded-provider-proof"
P14C_PROMPT_VERSION = "v1"
MAX_RESPONSE_BYTES = 1_048_576
RETRYABLE_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class P14CExecutionPacket:
    packet_id: str
    tool_system_base: str
    central_governance_base: str
    fixture_id: str
    provider_id: str
    model_id: str
    method: str
    host: str
    path: str
    credential_reference: str
    prompt_id: str
    prompt_version: str
    required_capabilities: tuple[str, ...]
    required_output_keys: tuple[str, ...]
    reasoning_effort: str
    store: bool
    tools_allowed: bool
    per_attempt_input_tokens: int
    per_attempt_output_tokens: int
    per_attempt_total_tokens: int
    max_attempts: int
    cumulative_token_ceiling: int
    request_timeout_ms: int
    total_wall_clock_ms: int
    cumulative_cost_microusd: int
    input_price_microusd_per_token: int
    output_price_microusd_per_token: int
    retry_after_cap_ms: int
    default_backoff_ms: int
    tls_verification: bool
    redirects_allowed: bool
    proxy_environment_allowed: bool
    fallback_allowed: bool

    def canonical_record(self) -> dict[str, object]:
        return {
            "packet_id": self.packet_id,
            "tool_system_base": self.tool_system_base,
            "central_governance_base": self.central_governance_base,
            "fixture_id": self.fixture_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "method": self.method,
            "host": self.host,
            "path": self.path,
            "credential_reference": self.credential_reference,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "required_capabilities": list(self.required_capabilities),
            "required_output_keys": list(self.required_output_keys),
            "reasoning_effort": self.reasoning_effort,
            "store": self.store,
            "tools_allowed": self.tools_allowed,
            "per_attempt_input_tokens": self.per_attempt_input_tokens,
            "per_attempt_output_tokens": self.per_attempt_output_tokens,
            "per_attempt_total_tokens": self.per_attempt_total_tokens,
            "max_attempts": self.max_attempts,
            "cumulative_token_ceiling": self.cumulative_token_ceiling,
            "request_timeout_ms": self.request_timeout_ms,
            "total_wall_clock_ms": self.total_wall_clock_ms,
            "cumulative_cost_microusd": self.cumulative_cost_microusd,
            "input_price_microusd_per_token": (self.input_price_microusd_per_token),
            "output_price_microusd_per_token": (self.output_price_microusd_per_token),
            "retryable_http_statuses": sorted(RETRYABLE_HTTP_STATUSES),
            "retry_after_cap_ms": self.retry_after_cap_ms,
            "default_backoff_ms": self.default_backoff_ms,
            "tls_verification": self.tls_verification,
            "redirects_allowed": self.redirects_allowed,
            "proxy_environment_allowed": self.proxy_environment_allowed,
            "fallback_allowed": self.fallback_allowed,
        }

    def sha256(self) -> str:
        return canonical_sha256(self.canonical_record())

    def audit_record(self) -> dict[str, object]:
        return {
            **self.canonical_record(),
            "packet_sha256": self.sha256(),
            "credential_value_accessed": False,
            "provider_call_performed": False,
        }


def build_p14c_execution_packet() -> P14CExecutionPacket:
    return P14CExecutionPacket(
        packet_id=P14C_AUTHORIZATION_PACKET,
        tool_system_base=P14C_TOOL_SYSTEM_BASE,
        central_governance_base=P14C_CENTRAL_GOVERNANCE_BASE,
        fixture_id=P14C_FIXTURE_ID,
        provider_id=OPENAI_PROVIDER_ID,
        model_id=OPENAI_MODEL_ID,
        method="POST",
        host=OPENAI_HOST,
        path=OPENAI_PATH,
        credential_reference=OPENAI_CREDENTIAL_REFERENCE,
        prompt_id=P14C_PROMPT_ID,
        prompt_version=P14C_PROMPT_VERSION,
        required_capabilities=("structured-output", "tool-free-generation"),
        required_output_keys=("summary", "control_status"),
        reasoning_effort="none",
        store=False,
        tools_allowed=False,
        per_attempt_input_tokens=4_096,
        per_attempt_output_tokens=512,
        per_attempt_total_tokens=4_608,
        max_attempts=2,
        cumulative_token_ceiling=9_216,
        request_timeout_ms=20_000,
        total_wall_clock_ms=45_000,
        cumulative_cost_microusd=20_000,
        input_price_microusd_per_token=1,
        output_price_microusd_per_token=6,
        retry_after_cap_ms=2_000,
        default_backoff_ms=250,
        tls_verification=True,
        redirects_allowed=False,
        proxy_environment_allowed=False,
        fallback_allowed=False,
    )


def validate_p14c_execution_packet(
    packet: P14CExecutionPacket,
) -> tuple[str, ...]:
    if not isinstance(packet, P14CExecutionPacket):
        return ("packet must be P14CExecutionPacket",)
    expected = build_p14c_execution_packet()
    reasons: list[str] = []
    for key, expected_value in expected.canonical_record().items():
        actual_value = packet.canonical_record().get(key)
        if actual_value != expected_value:
            reasons.append(f"packet field {key} does not match P14C-IMPL-v2")
    return tuple(reasons)


def build_p14c_synthetic_request(
    packet: P14CExecutionPacket | None = None,
) -> AIWorkerRequest:
    active_packet = packet or build_p14c_execution_packet()
    payload = {
        "fixture_id": active_packet.fixture_id,
        "instruction": "Return a concise assessment of this synthetic control.",
        "control": {
            "scope": "public-synthetic-only",
            "target_repository_mutation_allowed": False,
            "production_operation_allowed": False,
        },
    }
    return AIWorkerRequest(
        request_id="p14c-001",
        idempotency_key=f"p14c:{active_packet.fixture_id}:{active_packet.sha256()}",
        attempt_number=1,
        operation="assess-synthetic-control",
        model=AIModelSpec(
            provider_id=active_packet.provider_id,
            model_id=active_packet.model_id,
            capabilities=active_packet.required_capabilities,
            context_window_tokens=1_050_000,
        ),
        prompt=PromptSpec(
            prompt_id=active_packet.prompt_id,
            prompt_version=active_packet.prompt_version,
        ),
        inputs=(
            ContentAddressedInput.build(
                input_id=active_packet.fixture_id,
                kind="public-synthetic-fixture",
                media_type="application/json",
                payload=payload,
                sensitivity="public",
            ),
        ),
        required_capabilities=active_packet.required_capabilities,
        required_output_keys=active_packet.required_output_keys,
        budget=AIWorkerBudget(
            max_input_tokens=active_packet.per_attempt_input_tokens,
            max_output_tokens=active_packet.per_attempt_output_tokens,
            max_total_tokens=active_packet.per_attempt_total_tokens,
            timeout_ms=active_packet.total_wall_clock_ms,
            max_cost_microunits=active_packet.cumulative_cost_microusd,
        ),
        metadata={
            "control_packet_id": active_packet.packet_id,
            "fixture_id": active_packet.fixture_id,
            "packet_sha256": active_packet.sha256(),
        },
        execution_mode="live",
        writes_target_repo=False,
        executes_target_repo_mutation=False,
        production_deployment=False,
    )


class CredentialResolver(Protocol):
    def resolve(self, reference: str) -> str: ...


class ResponsesTransport(Protocol):
    def send(
        self,
        *,
        method: str,
        host: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> HTTPTransportResponse: ...


@dataclass(frozen=True)
class HTTPTransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class CredentialResolutionFailure(RuntimeError):
    pass


class TransportFailure(RuntimeError):
    def __init__(self, failure_class: str, *, retryable: bool) -> None:
        super().__init__(failure_class)
        self.failure_class = failure_class
        self.retryable = retryable


class EnvironmentCredentialResolver:
    def resolve(self, reference: str) -> str:
        if reference != OPENAI_CREDENTIAL_REFERENCE:
            raise CredentialResolutionFailure("credential reference is not approved")
        value = os.environ.get("OPENAI_API_KEY")
        if not isinstance(value, str) or not value:
            raise CredentialResolutionFailure("approved credential is unavailable")
        return value


class OpenAIResponsesTransport:
    """Direct TLS transport that ignores proxy environment and refuses redirects."""

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
        if (
            method != "POST"
            or host != OPENAI_HOST
            or path != OPENAI_PATH
            or timeout_seconds <= 0
        ):
            raise TransportFailure("transport_precondition", retryable=False)
        connection = http.client.HTTPSConnection(
            host,
            443,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request(
                method,
                path,
                body=body,
                headers=dict(headers),
            )
            response = connection.getresponse()
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(response_body) > MAX_RESPONSE_BYTES:
                raise TransportFailure("response_too_large", retryable=False)
            return HTTPTransportResponse(
                status_code=response.status,
                headers={key.lower(): value for key, value in response.getheaders()},
                body=response_body,
            )
        except TransportFailure:
            raise
        except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
            failure_class = "timeout" if isinstance(exc, TimeoutError) else "connection"
            raise TransportFailure(failure_class, retryable=True) from None
        finally:
            connection.close()


@dataclass(frozen=True)
class P14CLiveExecutionGuard:
    packet_sha256: str
    live_execution_authorized: bool = False

    def validate(
        self,
        request: AIWorkerRequest,
        provider: AIWorkerProvider,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.live_execution_authorized is not True:
            reasons.append("live provider execution is not authorized")
        packet = getattr(provider, "packet", None)
        if not isinstance(packet, P14CExecutionPacket):
            reasons.append("provider does not expose a P14C execution packet")
            return tuple(reasons)
        reasons.extend(validate_p14c_execution_packet(packet))
        if self.packet_sha256 != packet.sha256():
            reasons.append(
                "execution guard packet_sha256 does not match provider packet"
            )
        expected_request = build_p14c_synthetic_request(packet)
        try:
            actual_request_sha256 = request.sha256()
        except (AttributeError, TypeError, ValueError):
            actual_request_sha256 = ""
        if actual_request_sha256 != expected_request.sha256():
            reasons.append("request is not the exact P14C-001 synthetic fixture")
        expected_provider_metadata: dict[str, object] = {
            "provider_id": packet.provider_id,
            "model_id": packet.model_id,
            "capabilities": packet.required_capabilities,
            "provider_kind": "live_provider",
            "execution_mode": "live",
            "calls_external_provider": True,
            "uses_credentials": True,
            "network_access": True,
        }
        for name, expected_value in expected_provider_metadata.items():
            if getattr(provider, name, None) != expected_value:
                reasons.append(f"provider {name} does not match P14C execution packet")
        return tuple(reasons)


class OpenAIResponsesProvider:
    provider_id = OPENAI_PROVIDER_ID
    model_id = OPENAI_MODEL_ID
    capabilities = ("structured-output", "tool-free-generation")
    provider_kind = "live_provider"
    execution_mode = "live"
    calls_external_provider = True
    uses_credentials = True
    network_access = True

    def __init__(
        self,
        *,
        packet: P14CExecutionPacket,
        transport: ResponsesTransport,
        credential_resolver: CredentialResolver,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.packet = packet
        self._transport = transport
        self._credential_resolver = credential_resolver
        self._monotonic = monotonic
        self._sleep = sleep

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: CancellationSignal | None = None,
    ) -> ProviderResponse:
        preflight_reasons = list(validate_p14c_execution_packet(self.packet))
        request_validation = validate_ai_worker_request(request)
        if not request_validation.ok:
            preflight_reasons.extend(request_validation.reasons)
        if request.sha256() != build_p14c_synthetic_request(self.packet).sha256():
            preflight_reasons.append(
                "request is not the exact P14C-001 synthetic fixture"
            )
        if preflight_reasons:
            return _provider_error(
                AIWorkerErrorCode.INVALID_REQUEST,
                "P14C provider preflight failed",
                reasons=tuple(preflight_reasons),
            )
        if cancellation is not None and cancellation.is_cancelled():
            return _provider_error(
                AIWorkerErrorCode.CANCELLED,
                "P14C provider invocation cancelled before credential access",
            )

        body = _build_responses_request_body(request, self.packet)
        started_at = self._monotonic()
        last_failure_code = AIWorkerErrorCode.PROVIDER_FAILURE

        for attempt in range(1, self.packet.max_attempts + 1):
            elapsed_ms = _elapsed_ms(started_at, self._monotonic())
            if elapsed_ms >= self.packet.total_wall_clock_ms:
                return _provider_error(
                    AIWorkerErrorCode.TIMEOUT,
                    "P14C provider wall-clock ceiling reached",
                    retryable=False,
                    duration_ms=elapsed_ms,
                )
            if cancellation is not None and cancellation.is_cancelled():
                return _provider_error(
                    AIWorkerErrorCode.CANCELLED,
                    "P14C provider invocation cancelled before credential access",
                    duration_ms=elapsed_ms,
                )

            try:
                credential = self._credential_resolver.resolve(
                    self.packet.credential_reference
                )
            except CredentialResolutionFailure:
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "approved provider credential is unavailable",
                    retryable=False,
                    duration_ms=elapsed_ms,
                )
            except Exception:  # noqa: BLE001 - injected resolver must fail closed
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "credential resolver failed",
                    retryable=False,
                    duration_ms=elapsed_ms,
                )
            if not isinstance(credential, str) or not credential:
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "credential resolver returned an invalid value",
                    retryable=False,
                    duration_ms=elapsed_ms,
                )
            if cancellation is not None and cancellation.is_cancelled():
                return _provider_error(
                    AIWorkerErrorCode.CANCELLED,
                    "P14C provider invocation cancelled before transport",
                    duration_ms=_elapsed_ms(started_at, self._monotonic()),
                )

            remaining_seconds = max(
                0.001,
                (
                    self.packet.total_wall_clock_ms
                    - _elapsed_ms(started_at, self._monotonic())
                )
                / 1_000,
            )
            timeout_seconds = min(
                self.packet.request_timeout_ms / 1_000,
                remaining_seconds,
            )
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {credential}",
                "content-type": "application/json",
                "idempotency-key": request.idempotency_key,
            }
            try:
                response = self._transport.send(
                    method=self.packet.method,
                    host=self.packet.host,
                    path=self.packet.path,
                    headers=headers,
                    body=body,
                    timeout_seconds=timeout_seconds,
                )
            except TransportFailure as exc:
                last_failure_code = (
                    AIWorkerErrorCode.TIMEOUT
                    if exc.failure_class == "timeout"
                    else AIWorkerErrorCode.PROVIDER_FAILURE
                )
                if not exc.retryable or attempt == self.packet.max_attempts:
                    return _provider_error(
                        last_failure_code,
                        "provider transport failed",
                        retryable=exc.retryable,
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                retry_delay_ms = self.packet.default_backoff_ms
            except Exception:  # noqa: BLE001 - injected transport must fail closed
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "provider transport raised an unexpected exception",
                    retryable=False,
                    duration_ms=_elapsed_ms(started_at, self._monotonic()),
                )
            else:
                if cancellation is not None and cancellation.is_cancelled():
                    return _provider_error(
                        AIWorkerErrorCode.CANCELLED,
                        "P14C provider invocation cancelled after transport",
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                if response.status_code == 200:
                    return _parse_success_response(
                        response,
                        request,
                        self.packet,
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                if response.status_code not in RETRYABLE_HTTP_STATUSES:
                    return _provider_error(
                        AIWorkerErrorCode.PROVIDER_FAILURE,
                        "provider returned a non-retryable HTTP status",
                        retryable=False,
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                if attempt == self.packet.max_attempts:
                    return _provider_error(
                        AIWorkerErrorCode.PROVIDER_FAILURE,
                        "provider retry budget was exhausted",
                        retryable=True,
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                retry_delay_ms = _retry_delay_ms(response.headers, self.packet)

            projected_ms = _elapsed_ms(started_at, self._monotonic()) + retry_delay_ms
            if projected_ms >= self.packet.total_wall_clock_ms:
                return _provider_error(
                    AIWorkerErrorCode.TIMEOUT,
                    "retry delay would exceed the P14C wall-clock ceiling",
                    duration_ms=_elapsed_ms(started_at, self._monotonic()),
                )
            self._sleep(retry_delay_ms / 1_000)

        return _provider_error(
            last_failure_code,
            "provider retry loop ended without a terminal response",
            duration_ms=_elapsed_ms(started_at, self._monotonic()),
        )


def _build_responses_request_body(
    request: AIWorkerRequest,
    packet: P14CExecutionPacket,
) -> bytes:
    payload = request.inputs[0].payload
    body = {
        "model": packet.model_id,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Evaluate only the supplied public synthetic control. "
                            "Return the required JSON object and do not request tools."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": canonical_json_bytes(payload).decode("utf-8"),
                    }
                ],
            },
        ],
        "reasoning": {"effort": packet.reasoning_effort},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "p14c_bounded_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "control_status": {
                            "type": "string",
                            "enum": ["PASS", "BLOCK"],
                        },
                    },
                    "required": list(packet.required_output_keys),
                    "additionalProperties": False,
                },
                "strict": True,
            }
        },
        "max_output_tokens": packet.per_attempt_output_tokens,
        "store": packet.store,
    }
    return canonical_json_bytes(body)


def _parse_success_response(
    response: HTTPTransportResponse,
    request: AIWorkerRequest,
    packet: P14CExecutionPacket,
    *,
    duration_ms: int,
) -> ProviderResponse:
    if not isinstance(response.body, bytes) or len(response.body) > MAX_RESPONSE_BYTES:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response body is invalid",
            duration_ms=duration_ms,
        )
    try:
        record = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response is not valid JSON",
            duration_ms=duration_ms,
        )
    if not isinstance(record, dict):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response must be an object",
            duration_ms=duration_ms,
        )
    if record.get("model") != packet.model_id:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response model does not match the packet",
            duration_ms=duration_ms,
        )
    if record.get("status") != "completed":
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response did not complete",
            duration_ms=duration_ms,
        )

    output_texts: list[str] = []
    refusal_seen = False
    output_items = record.get("output")
    if isinstance(output_items, list):
        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "refusal":
                    refusal_seen = True
                elif part.get("type") == "output_text" and isinstance(
                    part.get("text"), str
                ):
                    output_texts.append(part["text"])
    if refusal_seen:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider refused the synthetic request",
            duration_ms=duration_ms,
        )
    if len(output_texts) != 1:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response must contain exactly one output_text item",
            duration_ms=duration_ms,
        )
    try:
        output = json.loads(output_texts[0])
    except json.JSONDecodeError:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider output_text is not valid JSON",
            duration_ms=duration_ms,
        )
    if not isinstance(output, dict) or set(output) != set(request.required_output_keys):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider structured output keys do not match the contract",
            duration_ms=duration_ms,
        )
    if not isinstance(output.get("summary"), str) or output.get(
        "control_status"
    ) not in {"PASS", "BLOCK"}:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider structured output values do not match the contract",
            duration_ms=duration_ms,
        )

    usage_record = record.get("usage")
    if not isinstance(usage_record, dict):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider usage is missing",
            duration_ms=duration_ms,
        )
    input_tokens = usage_record.get("input_tokens")
    output_tokens = usage_record.get("output_tokens")
    if not _non_negative_int(input_tokens) or not _non_negative_int(output_tokens):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider usage tokens are invalid",
            duration_ms=duration_ms,
        )
    total_tokens = input_tokens + output_tokens
    cost = (
        input_tokens * packet.input_price_microusd_per_token
        + output_tokens * packet.output_price_microusd_per_token
    )
    usage = AIWorkerUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        cost_microunits=cost,
    )
    budget_reasons: list[str] = []
    if input_tokens > packet.per_attempt_input_tokens:
        budget_reasons.append("input token ceiling exceeded")
    if output_tokens > packet.per_attempt_output_tokens:
        budget_reasons.append("output token ceiling exceeded")
    if total_tokens > packet.per_attempt_total_tokens:
        budget_reasons.append("per-attempt token ceiling exceeded")
    if total_tokens > packet.cumulative_token_ceiling:
        budget_reasons.append("cumulative token ceiling exceeded")
    if cost > packet.cumulative_cost_microusd:
        budget_reasons.append("cumulative cost ceiling exceeded")
    if duration_ms > packet.total_wall_clock_ms:
        budget_reasons.append("wall-clock ceiling exceeded")
    if budget_reasons:
        return _provider_error(
            AIWorkerErrorCode.BUDGET_EXCEEDED,
            "provider usage exceeded the P14C packet",
            reasons=tuple(budget_reasons),
            duration_ms=duration_ms,
            usage=usage,
        )
    return ProviderResponse(output=output, usage=usage)


def _retry_delay_ms(
    headers: Mapping[str, str],
    packet: P14CExecutionPacket,
) -> int:
    value = next(
        (
            header_value
            for header_name, header_value in headers.items()
            if header_name.lower() == "retry-after"
        ),
        None,
    )
    if isinstance(value, str):
        try:
            seconds = float(value.strip())
        except ValueError:
            seconds = -1
        if seconds >= 0:
            return min(int(seconds * 1_000), packet.retry_after_cap_ms)
    return packet.default_backoff_ms


def _provider_error(
    code: AIWorkerErrorCode,
    message: str,
    *,
    retryable: bool = False,
    reasons: tuple[str, ...] = (),
    duration_ms: int = 0,
    usage: AIWorkerUsage | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        output=None,
        usage=usage or AIWorkerUsage(duration_ms=max(0, duration_ms)),
        error=AIWorkerError(
            code=code,
            message=message,
            retryable=retryable,
            reasons=reasons,
        ),
    )


def _elapsed_ms(started_at: float, current: float) -> int:
    return max(0, int((current - started_at) * 1_000))


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
