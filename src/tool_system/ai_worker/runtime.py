from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, replace
from typing import Mapping, Protocol

from tool_system.ai_worker.contract import (
    AIWorkerError,
    AIWorkerErrorCode,
    AIWorkerProvider,
    AIWorkerRequest,
    AIWorkerResult,
    AIWorkerUsage,
    CancellationSignal,
    ProviderResponse,
    RequestValidation,
    canonical_json_bytes,
    validate_ai_worker_request,
    validate_structured_output,
    validate_usage,
)


class AIWorkerExecutionGuard(Protocol):
    boundary_name: str
    invocation_evidence: str

    def validate_request(self, request: AIWorkerRequest) -> RequestValidation: ...

    def provider_boundary_reasons(self, provider: object) -> tuple[str, ...]: ...


class FixtureExecutionGuard:
    boundary_name = "P14B fixture"
    invocation_evidence = "ai_worker.fixture_provider.invoked"

    def validate_request(self, request: AIWorkerRequest) -> RequestValidation:
        return validate_ai_worker_request(request)

    def provider_boundary_reasons(self, provider: object) -> tuple[str, ...]:
        return _fixture_provider_boundary_reasons(provider)


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class ReplayEntry:
    request_sha256: str
    result: AIWorkerResult


class InMemoryReplayStore:
    """Single-process replay evidence; durable integration belongs to P14G."""

    def __init__(self) -> None:
        self._entries: dict[str, ReplayEntry] = {}

    def get(self, idempotency_key: str) -> ReplayEntry | None:
        return self._entries.get(idempotency_key)

    def put(self, idempotency_key: str, entry: ReplayEntry) -> None:
        existing = self._entries.get(idempotency_key)
        if existing is not None and existing != entry:
            raise ValueError("idempotency entry already exists")
        self._entries[idempotency_key] = entry

    def __len__(self) -> int:
        return len(self._entries)


class AIWorkerRuntime:
    def __init__(
        self,
        provider: AIWorkerProvider,
        *,
        replay_store: InMemoryReplayStore | None = None,
        execution_guard: AIWorkerExecutionGuard | None = None,
    ) -> None:
        self.provider = provider
        self.execution_guard = execution_guard or FixtureExecutionGuard()
        self.replay_store = (
            replay_store if replay_store is not None else InMemoryReplayStore()
        )
        self._execution_lock = threading.RLock()

    def run(
        self,
        request: AIWorkerRequest,
        *,
        cancellation: CancellationSignal | None = None,
    ) -> AIWorkerResult:
        validation = self.execution_guard.validate_request(request)
        request_sha256 = _request_sha256_or_fallback(request)
        if not validation.ok:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=validation.error_code or AIWorkerErrorCode.INVALID_REQUEST,
                message="AI worker request failed validation",
                reasons=validation.reasons,
                evidence=("ai_worker.request_validation.block",),
            )

        with self._execution_lock:
            replay = self.replay_store.get(request.idempotency_key)
            if replay is not None:
                if replay.request_sha256 != request_sha256:
                    return _terminal_error(
                        request,
                        request_sha256=request_sha256,
                        status="BLOCK",
                        code=AIWorkerErrorCode.REPLAY_CONFLICT,
                        message="idempotency key is bound to another request",
                        reasons=(
                            "same idempotency_key has a different request_sha256",
                        ),
                        evidence=("ai_worker.replay.conflict",),
                    )
                return replace(
                    _copy_result(replay.result),
                    replayed=True,
                    evidence=replay.result.evidence + ("ai_worker.replay.hit",),
                )

            result = self._execute_once(
                request,
                request_sha256=request_sha256,
                cancellation=cancellation,
            )
            stored_result = _copy_result(result)
            self.replay_store.put(
                request.idempotency_key,
                ReplayEntry(request_sha256=request_sha256, result=stored_result),
            )
            return result

    def _execute_once(
        self,
        request: AIWorkerRequest,
        *,
        request_sha256: str,
        cancellation: CancellationSignal | None,
    ) -> AIWorkerResult:
        boundary_reasons = self.execution_guard.provider_boundary_reasons(self.provider)
        if boundary_reasons:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.PROVIDER_MISMATCH,
                message=(
                    "runtime provider is outside the "
                    f"{self.execution_guard.boundary_name} boundary"
                ),
                reasons=boundary_reasons,
                evidence=("ai_worker.provider_boundary.block",),
            )
        provider_id = getattr(self.provider, "provider_id", None)
        model_id = getattr(self.provider, "model_id", None)
        provider_capabilities = getattr(self.provider, "capabilities", None)
        if not isinstance(provider_id, str) or not isinstance(model_id, str):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.PROVIDER_MISMATCH,
                message="runtime provider identity is invalid",
                reasons=(
                    "provider identity must contain string provider_id and model_id",
                ),
                evidence=("ai_worker.provider_contract.block",),
            )
        if not isinstance(provider_capabilities, tuple) or not all(
            isinstance(item, str) for item in provider_capabilities
        ):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.CAPABILITY_MISMATCH,
                message="runtime provider capabilities are invalid",
                reasons=("provider capabilities must be a tuple of strings",),
                evidence=("ai_worker.provider_contract.block",),
            )
        if request.model.provider_id != provider_id:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.PROVIDER_MISMATCH,
                message="request provider does not match runtime provider",
                reasons=("provider_id mismatch",),
                evidence=("ai_worker.provider_binding.block",),
            )
        if request.model.model_id != model_id:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.PROVIDER_MISMATCH,
                message="request model does not match runtime model",
                reasons=("model_id mismatch",),
                evidence=("ai_worker.model_binding.block",),
            )
        missing = sorted(
            set(request.required_capabilities) - set(provider_capabilities)
        )
        if missing:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.CAPABILITY_MISMATCH,
                message="runtime provider lacks required capabilities",
                reasons=("provider is missing capabilities: " + ", ".join(missing),),
                evidence=("ai_worker.provider_capability.block",),
            )
        if cancellation is not None and cancellation.is_cancelled():
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="CANCELLED",
                code=AIWorkerErrorCode.CANCELLED,
                message="AI worker request was cancelled",
                evidence=("ai_worker.cancellation.pre_invoke",),
            )

        try:
            response = self.provider.invoke(request, cancellation)
        except Exception as exc:  # provider boundary must fail closed
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="ERROR",
                code=AIWorkerErrorCode.PROVIDER_FAILURE,
                message=f"provider raised {type(exc).__name__}",
                retryable=True,
                evidence=("ai_worker.provider.exception_sanitized",),
            )

        try:
            post_invoke_sha256 = request.sha256()
        except (AttributeError, TypeError, ValueError):
            post_invoke_sha256 = ""
        if post_invoke_sha256 != request_sha256:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider mutated the request",
                reasons=("request_sha256 changed across provider invocation",),
                evidence=("ai_worker.request_integrity.post_invoke_block",),
            )

        if not isinstance(response, ProviderResponse):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned an invalid response object",
                reasons=("provider response must be ProviderResponse",),
                evidence=("ai_worker.response_contract.block",),
            )
        if not isinstance(response.usage, AIWorkerUsage):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned invalid usage",
                reasons=("provider usage must be AIWorkerUsage",),
                evidence=("ai_worker.response_contract.block",),
            )
        if cancellation is not None and cancellation.is_cancelled():
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="CANCELLED",
                code=AIWorkerErrorCode.CANCELLED,
                message="AI worker request was cancelled",
                usage=response.usage,
                evidence=("ai_worker.cancellation.post_invoke",),
            )
        if response.error is not None and not isinstance(response.error, AIWorkerError):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned an invalid error object",
                reasons=("provider error must be AIWorkerError",),
                usage=response.usage,
                evidence=("ai_worker.response_contract.block",),
            )
        if response.error is not None and not isinstance(
            response.error.code, AIWorkerErrorCode
        ):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned an invalid error code",
                reasons=("provider error code must be AIWorkerErrorCode",),
                usage=response.usage,
                evidence=("ai_worker.response_contract.block",),
            )
        if response.error is not None and not isinstance(
            response.error.retryable, bool
        ):
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned invalid retryability metadata",
                reasons=("provider error retryable must be boolean",),
                usage=response.usage,
                evidence=("ai_worker.response_contract.block",),
            )
        if response.error is not None and response.output is not None:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider returned output and error together",
                reasons=("provider output and error are mutually exclusive",),
                usage=response.usage,
                evidence=("ai_worker.response_contract.block",),
            )

        usage_reasons = validate_usage(response.usage, request.budget)
        if usage_reasons:
            invalid_usage = any("must be" in reason for reason in usage_reasons)
            timeout_only = all("duration" in reason for reason in usage_reasons)
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="ERROR" if timeout_only else "BLOCK",
                code=(
                    AIWorkerErrorCode.INVALID_RESPONSE
                    if invalid_usage
                    else (
                        AIWorkerErrorCode.TIMEOUT
                        if timeout_only
                        else AIWorkerErrorCode.BUDGET_EXCEEDED
                    )
                ),
                message=(
                    "provider usage was invalid"
                    if invalid_usage
                    else (
                        "provider exceeded the logical timeout"
                        if timeout_only
                        else "provider usage exceeded the request budget"
                    )
                ),
                reasons=usage_reasons,
                usage=response.usage,
                evidence=("ai_worker.response_usage.block",),
            )

        if response.error is not None:
            status = (
                "CANCELLED"
                if response.error.code is AIWorkerErrorCode.CANCELLED
                else "ERROR"
            )
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status=status,
                code=response.error.code,
                message=f"provider returned {response.error.code.value}",
                retryable=response.error.retryable,
                usage=response.usage,
                evidence=("ai_worker.provider.terminal_error",),
            )

        output_reasons = validate_structured_output(
            response.output,
            request.required_output_keys,
        )
        if output_reasons:
            return _terminal_error(
                request,
                request_sha256=request_sha256,
                status="BLOCK",
                code=AIWorkerErrorCode.INVALID_RESPONSE,
                message="provider output failed structured validation",
                reasons=output_reasons,
                usage=response.usage,
                evidence=("ai_worker.response_validation.block",),
            )

        output = _canonical_mapping(response.output)
        return AIWorkerResult(
            status="PASS",
            request_id=request.request_id,
            idempotency_key=request.idempotency_key,
            request_sha256=request_sha256,
            provider_id=request.model.provider_id,
            model_id=request.model.model_id,
            prompt_id=request.prompt.prompt_id,
            prompt_version=request.prompt.prompt_version,
            usage=response.usage,
            output=output,
            output_sha256=hashlib.sha256(canonical_json_bytes(output)).hexdigest(),
            evidence=(
                "ai_worker.request.validated",
                self.execution_guard.invocation_evidence,
                "ai_worker.response.validated",
            ),
        )


def _terminal_error(
    request: AIWorkerRequest,
    *,
    request_sha256: str,
    status: str,
    code: AIWorkerErrorCode,
    message: str,
    reasons: tuple[str, ...] = (),
    retryable: bool = False,
    usage: AIWorkerUsage | None = None,
    evidence: tuple[str, ...] = (),
) -> AIWorkerResult:
    model = getattr(request, "model", None)
    prompt = getattr(request, "prompt", None)
    return AIWorkerResult(
        status=status,
        request_id=str(getattr(request, "request_id", "")),
        idempotency_key=str(getattr(request, "idempotency_key", "")),
        request_sha256=request_sha256,
        provider_id=str(getattr(model, "provider_id", "")),
        model_id=str(getattr(model, "model_id", "")),
        prompt_id=str(getattr(prompt, "prompt_id", "")),
        prompt_version=str(getattr(prompt, "prompt_version", "")),
        usage=usage or AIWorkerUsage(),
        error=AIWorkerError(
            code=code,
            message=message,
            retryable=retryable,
            reasons=reasons,
        ),
        evidence=evidence,
    )


def _request_sha256_or_fallback(request: AIWorkerRequest) -> str:
    try:
        return request.sha256()
    except (AttributeError, TypeError, ValueError):
        identity = (
            f"{getattr(request, 'request_id', '')}\0"
            f"{getattr(request, 'idempotency_key', '')}"
        ).encode("utf-8")
        return hashlib.sha256(identity).hexdigest()


def _canonical_mapping(value: Mapping[str, object] | None) -> dict[str, object]:
    if value is None:
        raise ValueError("mapping is required")
    return json.loads(canonical_json_bytes(dict(value)).decode("utf-8"))


def _copy_result(result: AIWorkerResult) -> AIWorkerResult:
    output = _canonical_mapping(result.output) if result.output is not None else None
    return replace(result, output=output)


def _fixture_provider_boundary_reasons(provider: object) -> tuple[str, ...]:
    expected = {
        "provider_kind": "deterministic_fixture",
        "execution_mode": "fixture",
        "calls_external_provider": False,
        "uses_credentials": False,
        "network_access": False,
    }
    reasons: list[str] = []
    for name, value in expected.items():
        actual = getattr(provider, name, None)
        matches = actual is value if isinstance(value, bool) else actual == value
        if not matches:
            reasons.append(f"provider {name} must be {value!r} in P14B")
    return tuple(reasons)
