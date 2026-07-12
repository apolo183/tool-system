from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, Sequence


class AIWorkerErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INPUT_INTEGRITY = "INPUT_INTEGRITY"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    REPLAY_CONFLICT = "REPLAY_CONFLICT"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


AI_WORKER_STATUSES = frozenset({"PASS", "BLOCK", "CANCELLED", "ERROR"})
MAX_INPUT_COUNT = 64
MAX_INPUT_BYTES = 1_048_576
MAX_TOTAL_INPUT_BYTES = 4_194_304
MAX_METADATA_BYTES = 16_384
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEY_PARTS = frozenset(
    {
        "apikey",
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "password",
        "privatekey",
        "secret",
        "token",
    }
)


def canonical_json_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be finite canonical JSON") from exc
    return rendered.encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def estimate_json_tokens(value: object) -> int:
    byte_count = len(canonical_json_bytes(value))
    return max(1, (byte_count + 3) // 4)


@dataclass(frozen=True)
class ContentAddressedInput:
    input_id: str
    kind: str
    media_type: str
    payload: object
    payload_sha256: str
    sensitivity: str = "repository"

    @classmethod
    def build(
        cls,
        *,
        input_id: str,
        kind: str,
        media_type: str,
        payload: object,
        sensitivity: str = "repository",
    ) -> ContentAddressedInput:
        return cls(
            input_id=input_id,
            kind=kind,
            media_type=media_type,
            payload=payload,
            payload_sha256=canonical_sha256(payload),
            sensitivity=sensitivity,
        )

    def canonical_record(self, *, include_payload: bool) -> dict[str, object]:
        record: dict[str, object] = {
            "input_id": self.input_id,
            "kind": self.kind,
            "media_type": self.media_type,
            "payload_sha256": self.payload_sha256,
            "sensitivity": self.sensitivity,
        }
        if include_payload:
            record["payload"] = self.payload
        return record

    def audit_record(self) -> dict[str, object]:
        try:
            payload_bytes = canonical_json_bytes(self.payload)
        except ValueError:
            payload_bytes = b""
        return {
            **self.canonical_record(include_payload=False),
            "payload_bytes": len(payload_bytes),
        }


@dataclass(frozen=True)
class AIModelSpec:
    provider_id: str
    model_id: str
    capabilities: tuple[str, ...]
    context_window_tokens: int


@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    prompt_version: str


@dataclass(frozen=True)
class AIWorkerBudget:
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    timeout_ms: int
    max_cost_microunits: int


@dataclass(frozen=True)
class AIWorkerRequest:
    request_id: str
    idempotency_key: str
    attempt_number: int
    operation: str
    model: AIModelSpec
    prompt: PromptSpec
    inputs: tuple[ContentAddressedInput, ...]
    required_capabilities: tuple[str, ...]
    required_output_keys: tuple[str, ...]
    budget: AIWorkerBudget
    metadata: Mapping[str, object] = field(default_factory=dict)
    execution_mode: str = "fixture"
    writes_target_repo: bool = False
    executes_target_repo_mutation: bool = False
    production_deployment: bool = False

    def canonical_record(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "idempotency_key": self.idempotency_key,
            "attempt_number": self.attempt_number,
            "operation": self.operation,
            "execution_mode": self.execution_mode,
            "model": {
                "provider_id": self.model.provider_id,
                "model_id": self.model.model_id,
                "capabilities": list(self.model.capabilities),
                "context_window_tokens": self.model.context_window_tokens,
            },
            "prompt": {
                "prompt_id": self.prompt.prompt_id,
                "prompt_version": self.prompt.prompt_version,
            },
            "inputs": [
                item.canonical_record(include_payload=True) for item in self.inputs
            ],
            "required_capabilities": list(self.required_capabilities),
            "required_output_keys": list(self.required_output_keys),
            "budget": {
                "max_input_tokens": self.budget.max_input_tokens,
                "max_output_tokens": self.budget.max_output_tokens,
                "max_total_tokens": self.budget.max_total_tokens,
                "timeout_ms": self.budget.timeout_ms,
                "max_cost_microunits": self.budget.max_cost_microunits,
            },
            "metadata": dict(self.metadata),
            "writes_target_repo": self.writes_target_repo,
            "executes_target_repo_mutation": self.executes_target_repo_mutation,
            "production_deployment": self.production_deployment,
        }

    def sha256(self) -> str:
        return canonical_sha256(self.canonical_record())

    def audit_record(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "idempotency_key_sha256": hashlib.sha256(
                self.idempotency_key.encode("utf-8")
            ).hexdigest(),
            "attempt_number": self.attempt_number,
            "operation": self.operation,
            "execution_mode": self.execution_mode,
            "request_sha256": _safe_request_sha256(self),
            "provider_id": self.model.provider_id,
            "model_id": self.model.model_id,
            "model_capabilities": list(self.model.capabilities),
            "prompt_id": self.prompt.prompt_id,
            "prompt_version": self.prompt.prompt_version,
            "required_capabilities": list(self.required_capabilities),
            "required_output_keys": list(self.required_output_keys),
            "inputs": [item.audit_record() for item in self.inputs],
            "metadata_keys": sorted(
                key for key in self.metadata if isinstance(key, str)
            ),
            "budget": {
                "max_input_tokens": self.budget.max_input_tokens,
                "max_output_tokens": self.budget.max_output_tokens,
                "max_total_tokens": self.budget.max_total_tokens,
                "timeout_ms": self.budget.timeout_ms,
                "max_cost_microunits": self.budget.max_cost_microunits,
            },
            "writes_target_repo": self.writes_target_repo,
            "executes_target_repo_mutation": self.executes_target_repo_mutation,
            "production_deployment": self.production_deployment,
        }


@dataclass(frozen=True)
class AIWorkerUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    cost_microunits: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_record(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "cost_microunits": self.cost_microunits,
        }


@dataclass(frozen=True)
class AIWorkerError:
    code: AIWorkerErrorCode
    message: str
    retryable: bool = False
    reasons: tuple[str, ...] = ()

    def to_record(self, *, audit: bool = False) -> dict[str, object]:
        record: dict[str, object] = {
            "code": self.code.value,
            "retryable": self.retryable,
        }
        if not audit:
            record["message"] = self.message
            record["reasons"] = list(self.reasons)
        return record


@dataclass(frozen=True)
class ProviderResponse:
    output: Mapping[str, object] | None
    usage: AIWorkerUsage
    error: AIWorkerError | None = None


@dataclass(frozen=True)
class AIWorkerResult:
    status: str
    request_id: str
    idempotency_key: str
    request_sha256: str
    provider_id: str
    model_id: str
    prompt_id: str
    prompt_version: str
    usage: AIWorkerUsage
    output: Mapping[str, object] | None = None
    output_sha256: str | None = None
    error: AIWorkerError | None = None
    replayed: bool = False
    evidence: tuple[str, ...] = ()

    def to_record(self) -> dict[str, object]:
        return {
            **self.to_audit_record(),
            "idempotency_key": self.idempotency_key,
            "output": dict(self.output) if self.output is not None else None,
            "error": self.error.to_record() if self.error is not None else None,
        }

    def to_audit_record(self) -> dict[str, object]:
        return {
            "status": self.status,
            "request_id": self.request_id,
            "idempotency_key_sha256": hashlib.sha256(
                self.idempotency_key.encode("utf-8")
            ).hexdigest(),
            "request_sha256": self.request_sha256,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "usage": self.usage.to_record(),
            "output_sha256": self.output_sha256,
            "error": self.error.to_record(audit=True)
            if self.error is not None
            else None,
            "replayed": self.replayed,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class RequestValidation:
    error_code: AIWorkerErrorCode | None
    reasons: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.error_code is None and not self.reasons


class CancellationSignal(Protocol):
    def is_cancelled(self) -> bool: ...


class AIWorkerProvider(Protocol):
    provider_id: str
    model_id: str
    capabilities: tuple[str, ...]
    provider_kind: str
    execution_mode: str
    calls_external_provider: bool
    uses_credentials: bool
    network_access: bool

    def invoke(
        self,
        request: AIWorkerRequest,
        cancellation: CancellationSignal | None = None,
    ) -> ProviderResponse: ...


def validate_ai_worker_request(request: AIWorkerRequest) -> RequestValidation:
    return validate_ai_worker_request_for_mode(
        request,
        expected_execution_mode="fixture",
        stage_label="P14B",
    )


def validate_ai_worker_request_for_mode(
    request: AIWorkerRequest,
    *,
    expected_execution_mode: str,
    stage_label: str,
) -> RequestValidation:
    if expected_execution_mode not in {"fixture", "live"}:
        raise ValueError("expected_execution_mode must be fixture or live")
    if stage_label not in {"P14B", "P14C"}:
        raise ValueError("stage_label must be P14B or P14C")

    invalid: list[str] = []
    integrity: list[str] = []
    capability: list[str] = []
    budget: list[str] = []

    if not isinstance(request, AIWorkerRequest):
        return RequestValidation(
            error_code=AIWorkerErrorCode.INVALID_REQUEST,
            reasons=("request must be AIWorkerRequest",),
        )
    if not isinstance(request.model, AIModelSpec):
        invalid.append("model must be AIModelSpec")
    if not isinstance(request.prompt, PromptSpec):
        invalid.append("prompt must be PromptSpec")
    if not isinstance(request.budget, AIWorkerBudget):
        invalid.append("budget must be AIWorkerBudget")
    if invalid:
        return RequestValidation(
            error_code=AIWorkerErrorCode.INVALID_REQUEST,
            reasons=tuple(invalid),
        )

    for name, value in (
        ("request_id", request.request_id),
        ("operation", request.operation),
        ("provider_id", request.model.provider_id),
        ("model_id", request.model.model_id),
        ("prompt_id", request.prompt.prompt_id),
        ("prompt_version", request.prompt.prompt_version),
    ):
        if not _valid_identifier(value):
            invalid.append(f"{name} must be a bounded identifier")

    if not isinstance(request.idempotency_key, str) or not (
        1 <= len(request.idempotency_key) <= 256
    ):
        invalid.append(
            "idempotency_key must be a non-empty string of at most 256 characters"
        )
    if not _positive_int(request.attempt_number):
        invalid.append("attempt_number must be a positive integer")
    if request.execution_mode != expected_execution_mode:
        invalid.append(
            f"execution_mode must be {expected_execution_mode} in {stage_label}"
        )
    if request.writes_target_repo is not False:
        invalid.append(f"writes_target_repo must be false in {stage_label}")
    if request.executes_target_repo_mutation is not False:
        invalid.append(f"executes_target_repo_mutation must be false in {stage_label}")
    if request.production_deployment is not False:
        invalid.append(f"production_deployment must be false in {stage_label}")

    if not isinstance(request.inputs, tuple) or not (
        1 <= len(request.inputs) <= MAX_INPUT_COUNT
    ):
        invalid.append(f"inputs must contain between 1 and {MAX_INPUT_COUNT} items")
    seen_input_ids: set[str] = set()
    total_input_bytes = 0
    input_items = request.inputs if isinstance(request.inputs, tuple) else ()
    for index, item in enumerate(input_items):
        if not isinstance(item, ContentAddressedInput):
            invalid.append(f"inputs[{index}] must be ContentAddressedInput")
            continue
        if not _valid_identifier(item.input_id):
            invalid.append(f"inputs[{index}].input_id must be a bounded identifier")
        elif item.input_id in seen_input_ids:
            invalid.append(f"duplicate input_id: {item.input_id}")
        seen_input_ids.add(item.input_id)
        if not _valid_identifier(item.kind):
            invalid.append(f"input {item.input_id} kind must be a bounded identifier")
        if not isinstance(item.media_type, str) or not (
            1 <= len(item.media_type) <= 128
        ):
            invalid.append(f"input {item.input_id} media_type must be bounded")
        if item.sensitivity not in {"public", "repository"}:
            invalid.append(f"input {item.input_id} sensitivity must not be secret")
        if not isinstance(item.payload_sha256, str) or not _SHA256_PATTERN.fullmatch(
            item.payload_sha256
        ):
            integrity.append(
                f"input {item.input_id} payload_sha256 must be lowercase SHA-256"
            )
        try:
            payload_bytes = canonical_json_bytes(item.payload)
        except ValueError:
            invalid.append(
                f"input {item.input_id} payload must be finite canonical JSON"
            )
            continue
        total_input_bytes += len(payload_bytes)
        if len(payload_bytes) > MAX_INPUT_BYTES:
            budget.append(f"input {item.input_id} exceeds the byte ceiling")
        if hashlib.sha256(payload_bytes).hexdigest() != item.payload_sha256:
            integrity.append(f"input {item.input_id} payload_sha256 mismatch")
    if total_input_bytes > MAX_TOTAL_INPUT_BYTES:
        budget.append("combined input payload exceeds the byte ceiling")

    _validate_string_sequence("model capabilities", request.model.capabilities, invalid)
    _validate_string_sequence(
        "required capabilities", request.required_capabilities, invalid
    )
    _validate_string_sequence(
        "required output keys", request.required_output_keys, invalid
    )
    missing_capabilities = sorted(
        set(request.required_capabilities) - set(request.model.capabilities)
    )
    if missing_capabilities:
        capability.append(
            "model is missing required capabilities: " + ", ".join(missing_capabilities)
        )

    if not isinstance(request.metadata, Mapping):
        invalid.append("metadata must be a mapping")
    else:
        for key in request.metadata:
            if not isinstance(key, str) or not _valid_identifier(key):
                invalid.append("metadata keys must be bounded identifiers")
                continue
            if _secret_like_key(key):
                invalid.append(f"metadata key is secret-like: {key}")
        try:
            metadata_bytes = canonical_json_bytes(dict(request.metadata))
        except ValueError:
            invalid.append("metadata must be finite canonical JSON")
        else:
            if len(metadata_bytes) > MAX_METADATA_BYTES:
                budget.append("metadata exceeds the byte ceiling")

    for name, value in (
        ("max_input_tokens", request.budget.max_input_tokens),
        ("max_output_tokens", request.budget.max_output_tokens),
        ("max_total_tokens", request.budget.max_total_tokens),
        ("timeout_ms", request.budget.timeout_ms),
        ("context_window_tokens", request.model.context_window_tokens),
    ):
        if not _positive_int(value):
            invalid.append(f"{name} must be a positive integer")
    if not _non_negative_int(request.budget.max_cost_microunits):
        invalid.append("max_cost_microunits must be a non-negative integer")

    if not invalid:
        if (
            request.budget.max_input_tokens + request.budget.max_output_tokens
            > request.budget.max_total_tokens
        ):
            budget.append("input and output token ceilings exceed max_total_tokens")
        if request.budget.max_total_tokens > request.model.context_window_tokens:
            budget.append("max_total_tokens exceeds model context window")
        try:
            estimated_input_tokens = estimate_input_tokens(request.inputs)
        except ValueError:
            estimated_input_tokens = request.budget.max_input_tokens + 1
        if estimated_input_tokens > request.budget.max_input_tokens:
            budget.append("estimated input tokens exceed max_input_tokens")

    reasons = tuple(invalid + integrity + capability + budget)
    if invalid:
        code = AIWorkerErrorCode.INVALID_REQUEST
    elif integrity:
        code = AIWorkerErrorCode.INPUT_INTEGRITY
    elif capability:
        code = AIWorkerErrorCode.CAPABILITY_MISMATCH
    elif budget:
        code = AIWorkerErrorCode.BUDGET_EXCEEDED
    else:
        code = None
    return RequestValidation(error_code=code, reasons=reasons)


def estimate_input_tokens(inputs: Sequence[ContentAddressedInput]) -> int:
    return sum(estimate_json_tokens(item.payload) for item in inputs)


def validate_usage(usage: AIWorkerUsage, budget: AIWorkerBudget) -> tuple[str, ...]:
    reasons: list[str] = []
    for name, value in (
        ("input_tokens", usage.input_tokens),
        ("output_tokens", usage.output_tokens),
        ("duration_ms", usage.duration_ms),
        ("cost_microunits", usage.cost_microunits),
    ):
        if not _non_negative_int(value):
            reasons.append(f"provider usage {name} must be a non-negative integer")
    if reasons:
        return tuple(reasons)
    if usage.input_tokens > budget.max_input_tokens:
        reasons.append("provider input tokens exceed max_input_tokens")
    if usage.output_tokens > budget.max_output_tokens:
        reasons.append("provider output tokens exceed max_output_tokens")
    if usage.total_tokens > budget.max_total_tokens:
        reasons.append("provider total tokens exceed max_total_tokens")
    if usage.duration_ms > budget.timeout_ms:
        reasons.append("provider duration exceeds timeout_ms")
    if usage.cost_microunits > budget.max_cost_microunits:
        reasons.append("provider cost exceeds max_cost_microunits")
    return tuple(reasons)


def validate_structured_output(
    output: Mapping[str, object] | None,
    required_keys: Sequence[str],
) -> tuple[str, ...]:
    if not isinstance(output, Mapping):
        return ("provider output must be a mapping",)
    try:
        canonical_json_bytes(dict(output))
    except ValueError:
        return ("provider output must be finite canonical JSON",)
    missing = sorted(set(required_keys) - set(output))
    if missing:
        return ("provider output is missing required keys: " + ", ".join(missing),)
    return ()


def _safe_request_sha256(request: AIWorkerRequest) -> str:
    try:
        return request.sha256()
    except (AttributeError, TypeError, ValueError):
        fallback = f"{request.request_id}\0{request.idempotency_key}".encode("utf-8")
        return hashlib.sha256(fallback).hexdigest()


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and _IDENTIFIER_PATTERN.fullmatch(value) is not None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _secret_like_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "", key.lower())
    return any(part in normalized for part in _SECRET_KEY_PARTS)


def _validate_string_sequence(
    label: str,
    values: object,
    reasons: list[str],
) -> None:
    if not isinstance(values, tuple) or not values:
        reasons.append(f"{label} must be a non-empty tuple")
        return
    if len(values) > 64:
        reasons.append(f"{label} must contain at most 64 items")
    if not all(_valid_identifier(value) for value in values):
        reasons.append(f"{label} entries must be bounded identifiers")
        return
    if len(values) != len(set(values)):
        reasons.append(f"{label} must not contain duplicates")
