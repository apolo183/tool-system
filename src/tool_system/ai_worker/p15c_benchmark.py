from __future__ import annotations

import hashlib
import http.client
import json
import math
import ssl
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import urlsplit

import yaml

from tool_system.ai_worker.p15c_controls import (
    OwnerOnlyCredentialResolver,
    P15C_CASE_IDS,
    P15C_ENABLED_PROVIDER_IDS,
    P15CControlError,
    P15CExecutionPolicy,
    P15CSnapshotFile,
    P15CTargetPacket,
    P15CUsageLedger,
    build_execution_source_seal,
    load_execution_policy,
    validate_target_snapshot,
)

P15C_PACKET_SET_ID = "p15c-execution-packet-freeze-v1"
P15C_REQUESTED_OUTPUT_TOKENS = 2_048
P15C_MAX_PROMPT_BYTES = 65_536
P15C_MAX_RESPONSE_BYTES = 1_048_576
P15C_PROMPT_VERSION = "p15c-read-only-code-review-v1"
P15C_FINDING_LIMIT = 32
P15C_FINDING_SUMMARY_MAX_CHARS = 512
P15C_FINDING_CATEGORIES = (
    "correctness",
    "maintainability",
    "reliability",
    "security",
    "testability",
)
P15C_FINDING_SEVERITIES = ("critical", "high", "low", "medium")
P15C_CRITICAL_SOURCE_PATHS = (
    ".github/workflows/p15c-read-only-benchmark.yml",
    "config/p15c_execution_packet_freeze_v1.yaml",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "src/tool_system/ai_worker/p15c_controls.py",
    "src/tool_system/ai_worker/p15c_entry.py",
    "src/tool_system/ai_worker/p15c_hosted.py",
)
P15C_DETERMINISTIC_EXPECTED_FINDING_PATHS = frozenset(
    {
        "tests/fixtures/p14h/python_cli/src/calculator.py",
        "tests/fixtures/p14h/typescript_package/src/index.ts",
        "tests/fixtures/p14h/typescript_package/src/legacy.ts",
    }
)


class P15CBenchmarkError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class P15CCancellationSignal(Protocol):
    def is_cancelled(self) -> bool:
        ...


@dataclass(frozen=True)
class P15CProviderPacket:
    packet_id: str
    provider_id: str
    execution_surface_id: str
    model_id: str
    exact_model_version: str
    host: str
    path: str
    credential_reference: str
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    request_timeout_seconds: int
    wall_clock_timeout_seconds: int
    per_attempt_hard_cap_micro_usd: int
    packet_sha256: str

    def public_record(self) -> dict[str, object]:
        return {
            "packet_id": self.packet_id,
            "provider_id": self.provider_id,
            "execution_surface_id": self.execution_surface_id,
            "model_id": self.model_id,
            "exact_model_version": self.exact_model_version,
            "host": self.host,
            "path": self.path,
            "credential_reference": self.credential_reference,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_total_tokens": self.max_total_tokens,
            "request_timeout_seconds": self.request_timeout_seconds,
            "wall_clock_timeout_seconds": self.wall_clock_timeout_seconds,
            "requested_output_tokens": P15C_REQUESTED_OUTPUT_TOKENS,
            "per_attempt_hard_cap_micro_usd": self.per_attempt_hard_cap_micro_usd,
            "max_attempts": 1,
            "max_retries": 0,
            "streaming": False,
            "tools_enabled": False,
            "provider_web_search_enabled": False,
            "response_storage_requested": False,
            "packet_sha256": self.packet_sha256,
        }


@dataclass(frozen=True)
class P15CBenchmarkCase:
    case_id: str
    files: tuple[P15CSnapshotFile, ...]
    case_sha256: str
    expected_finding_paths: frozenset[str]
    private_target: bool

    @property
    def allowed_paths(self) -> frozenset[str]:
        return frozenset(item.path for item in self.files)


@dataclass(frozen=True)
class P15CHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class P15CTransport(Protocol):
    transport_kind: str

    def send(
        self,
        *,
        host: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> P15CHTTPResponse:
        ...


class P15CTransportFailure(RuntimeError):
    def __init__(self, failure_code: str) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code


class P15CDirectTLSTransport:
    """Direct verified TLS with fixed routes and no proxy or redirect support."""

    transport_kind = "p15c_direct_tls"
    _allowed_routes = frozenset(
        {
            ("api.deepseek.com", "/chat/completions"),
            ("api.openai.com", "/v1/responses"),
        }
    )

    def send(
        self,
        *,
        host: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> P15CHTTPResponse:
        if (
            (host, path) not in self._allowed_routes
            or not isinstance(body, bytes)
            or not body
            or not 0 < timeout_seconds <= 90
        ):
            raise P15CTransportFailure("TRANSPORT_PRECONDITION")
        connection = http.client.HTTPSConnection(
            host,
            443,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request("POST", path, body=body, headers=dict(headers))
            response = connection.getresponse()
            response_body = response.read(P15C_MAX_RESPONSE_BYTES + 1)
            if len(response_body) > P15C_MAX_RESPONSE_BYTES:
                raise P15CTransportFailure("RESPONSE_TOO_LARGE")
            return P15CHTTPResponse(
                status_code=response.status,
                headers={key.lower(): value for key, value in response.getheaders()},
                body=response_body,
            )
        except P15CTransportFailure:
            raise
        except TimeoutError:
            raise P15CTransportFailure("TRANSPORT_TIMEOUT") from None
        except (OSError, ssl.SSLError, http.client.HTTPException):
            raise P15CTransportFailure("TRANSPORT_CONNECTION") from None
        finally:
            connection.close()


@dataclass(frozen=True)
class P15CParsedResponse:
    output: Mapping[str, object]
    output_sha256: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class P15CAttemptOutcome:
    attempt_id: str
    provider_id: str
    model_id: str
    case_id: str
    status: str
    request_sha256: str
    output_sha256: str | None
    input_tokens: int
    output_tokens: int
    duration_ms: int
    charged_micro_usd: int
    metrics: Mapping[str, object] | None
    failure_code: str | None

    def public_record(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "case_id": self.case_id,
            "status": self.status,
            "request_sha256": self.request_sha256,
            "output_sha256": self.output_sha256,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
                "duration_ms": self.duration_ms,
                "charged_micro_usd": self.charged_micro_usd,
            },
            "metrics": dict(self.metrics) if self.metrics is not None else None,
            "failure_code": self.failure_code,
            "credential_value_recorded": False,
            "raw_provider_output_recorded": False,
            "private_target_identity_recorded": False,
            "private_target_paths_recorded": False,
            "target_mutation_count": 0,
        }


def load_p15c_provider_packets(
    packet_config_path: str | Path,
) -> tuple[P15CProviderPacket, ...]:
    path = Path(packet_config_path)
    try:
        raw = path.read_bytes()
        root = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise P15CBenchmarkError(
            "PACKET_CONFIG_INVALID",
            "P15C packet config is unavailable or invalid",
        ) from exc
    if not isinstance(root, dict) or root.get("packet_set_id") != P15C_PACKET_SET_ID:
        raise P15CBenchmarkError(
            "PACKET_SET_INVALID",
            "P15C packet-set identity is invalid",
        )
    limits = root.get("common_attempt_limits")
    expected_limits = {
        "max_input_tokens": 65_536,
        "max_output_tokens": 8_192,
        "max_total_tokens": 73_728,
        "max_attempts": 1,
        "max_retries": 0,
        "request_timeout_seconds": 90,
        "wall_clock_timeout_seconds": 120,
        "cancellation_required": True,
        "no_progress_stop_required": True,
        "streaming": False,
        "provider_tools_enabled": False,
        "provider_web_search_enabled": False,
        "response_storage_requested": False,
    }
    if limits != expected_limits:
        raise P15CBenchmarkError(
            "PACKET_LIMIT_DRIFT",
            "P15C common attempt limits changed",
        )
    raw_packets = root.get("provider_packets")
    if not isinstance(raw_packets, list) or len(raw_packets) != 3:
        raise P15CBenchmarkError(
            "PACKET_PROVIDER_SET",
            "P15C provider packet set is invalid",
        )
    by_provider = {
        item.get("provider_id"): item for item in raw_packets if isinstance(item, dict)
    }
    if set(by_provider) != {"deepseek", "openai", "qwen"}:
        raise P15CBenchmarkError(
            "PACKET_PROVIDER_SET",
            "P15C provider packet set is invalid",
        )
    qwen = by_provider["qwen"]
    if (
        qwen.get("packet_status") != "BLOCKED_NOT_FUNDED"
        or qwen.get("pricing_snapshot", {}).get(
            "shared_usd_budget_allocation_micro_usd"
        )
        != 0
    ):
        raise P15CBenchmarkError("QWEN_NOT_DISABLED", "Qwen packet is not disabled")
    exact = {
        "deepseek": {
            "packet_id": "P15C-DEEPSEEK-V4-FLASH-READONLY-v1",
            "execution_surface_id": "deepseek-openai-compatible-chat",
            "model_id": "deepseek-v4-flash",
            "exact_model_version": "DeepSeek-V4-Flash",
            "base_url": "https://api.deepseek.com",
            "operation": "chat.completions.create",
            "credential_reference": (
                "private-control:credentials#providers.deepseek.api_key"
            ),
            "path": "/chat/completions",
        },
        "openai": {
            "packet_id": "P15C-OPENAI-GPT-5.6-LUNA-READONLY-v1",
            "execution_surface_id": "openai-responses-api",
            "model_id": "gpt-5.6-luna",
            "exact_model_version": "gpt-5.6-luna",
            "base_url": "https://api.openai.com/v1",
            "operation": "responses.create",
            "credential_reference": (
                "private-control:credentials#providers.openai.api_key"
            ),
            "path": "/v1/responses",
        },
    }
    result: list[P15CProviderPacket] = []
    for provider_id in P15C_ENABLED_PROVIDER_IDS:
        item = by_provider[provider_id]
        expected = exact[provider_id]
        for field in (
            "packet_id",
            "execution_surface_id",
            "model_id",
            "exact_model_version",
            "base_url",
            "operation",
            "credential_reference",
        ):
            if item.get(field) != expected[field]:
                raise P15CBenchmarkError(
                    "PACKET_FIELD_DRIFT",
                    f"P15C {provider_id} packet field {field} changed",
                )
        if item.get("attempt_limits") != expected_limits:
            raise P15CBenchmarkError(
                "PACKET_LIMIT_DRIFT",
                f"P15C {provider_id} attempt limits changed",
            )
        price = item.get("pricing_snapshot")
        if (
            not isinstance(price, dict)
            or price.get("calculated_worst_case_micro_usd") != 22_400
            or price.get("per_attempt_hard_cap_micro_usd") != 25_000
        ):
            raise P15CBenchmarkError(
                "PACKET_PRICE_DRIFT",
                f"P15C {provider_id} pricing ceiling changed",
            )
        parsed_url = urlsplit(str(item["base_url"]))
        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname is None
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise P15CBenchmarkError(
                "PACKET_ROUTE_INVALID",
                f"P15C {provider_id} route is invalid",
            )
        packet_record = {
            "packet_set_sha256": hashlib.sha256(raw).hexdigest(),
            "provider_packet": item,
            "runtime_prompt_version": P15C_PROMPT_VERSION,
            "requested_output_tokens": P15C_REQUESTED_OUTPUT_TOKENS,
        }
        result.append(
            P15CProviderPacket(
                packet_id=str(item["packet_id"]),
                provider_id=provider_id,
                execution_surface_id=str(item["execution_surface_id"]),
                model_id=str(item["model_id"]),
                exact_model_version=str(item["exact_model_version"]),
                host=parsed_url.hostname,
                path=str(expected["path"]),
                credential_reference=str(item["credential_reference"]),
                max_input_tokens=int(expected_limits["max_input_tokens"]),
                max_output_tokens=int(expected_limits["max_output_tokens"]),
                max_total_tokens=int(expected_limits["max_total_tokens"]),
                request_timeout_seconds=int(
                    expected_limits["request_timeout_seconds"]
                ),
                wall_clock_timeout_seconds=int(
                    expected_limits["wall_clock_timeout_seconds"]
                ),
                per_attempt_hard_cap_micro_usd=int(
                    price["per_attempt_hard_cap_micro_usd"]
                ),
                packet_sha256=_canonical_sha256(packet_record),
            )
        )
    return tuple(result)


def load_p15c_deterministic_case(
    repository_root: str | Path,
    packet_config_path: str | Path,
) -> P15CBenchmarkCase:
    root = Path(repository_root).resolve(strict=True)
    try:
        config = yaml.safe_load(Path(packet_config_path).read_bytes())
        corpus = config["deterministic_corpus"]
        raw_files = corpus["files"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise P15CBenchmarkError(
            "CORPUS_CONFIG_INVALID",
            "P15C deterministic corpus config is invalid",
        ) from exc
    if not isinstance(raw_files, list) or len(raw_files) != 12:
        raise P15CBenchmarkError(
            "CORPUS_FILE_SET",
            "P15C deterministic corpus file set is invalid",
        )
    aggregate_source = "".join(
        f"{item['git_blob_sha']} {item['path']}\n" for item in raw_files
    ).encode("utf-8")
    if hashlib.sha256(aggregate_source).hexdigest() != corpus.get("aggregate_sha256"):
        raise P15CBenchmarkError(
            "CORPUS_AGGREGATE_DRIFT",
            "P15C deterministic corpus aggregate changed",
        )
    loaded: list[P15CSnapshotFile] = []
    for item in raw_files:
        if not isinstance(item, dict) or set(item) != {"path", "git_blob_sha"}:
            raise P15CBenchmarkError(
                "CORPUS_ITEM_INVALID",
                "P15C deterministic corpus item is invalid",
            )
        relative = _repository_relative_path(item["path"])
        path = root.joinpath(*PurePosixPath(relative).parts)
        try:
            resolved = path.resolve(strict=True)
            content_bytes = path.read_bytes()
            content = content_bytes.decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            raise P15CBenchmarkError(
                "CORPUS_FILE_INVALID",
                "P15C deterministic corpus file is invalid",
            ) from exc
        if resolved != path or not resolved.is_relative_to(root):
            raise P15CBenchmarkError(
                "CORPUS_FILE_UNSAFE",
                "P15C deterministic corpus path is unsafe",
            )
        blob = _git_blob_sha(content_bytes)
        if blob != item["git_blob_sha"]:
            raise P15CBenchmarkError(
                "CORPUS_BLOB_DRIFT",
                "P15C deterministic corpus content changed",
            )
        loaded.append(
            P15CSnapshotFile(
                path=relative,
                sha256=hashlib.sha256(content_bytes).hexdigest(),
                git_blob_sha=blob,
                content=content,
            )
        )
    if tuple(item.path for item in loaded) != tuple(
        sorted(item.path for item in loaded)
    ):
        raise P15CBenchmarkError(
            "CORPUS_ORDER",
            "P15C deterministic corpus must be sorted",
        )
    case_record = {
        "case_id": "deterministic-corpus",
        "corpus_aggregate_sha256": corpus["aggregate_sha256"],
        "files": [
            {
                "path": item.path,
                "sha256": item.sha256,
                "git_blob_sha": item.git_blob_sha,
            }
            for item in loaded
        ],
        "prompt_version": P15C_PROMPT_VERSION,
    }
    return P15CBenchmarkCase(
        case_id="deterministic-corpus",
        files=tuple(loaded),
        case_sha256=_canonical_sha256(case_record),
        expected_finding_paths=P15C_DETERMINISTIC_EXPECTED_FINDING_PATHS,
        private_target=False,
    )


def build_p15c_private_case(
    packet: P15CTargetPacket,
    snapshot: Sequence[P15CSnapshotFile],
) -> P15CBenchmarkCase:
    packet.assert_read_only_authority()
    files = validate_target_snapshot(packet, snapshot)
    if not files or tuple(item.path for item in files) != packet.exact_file_allowlist:
        raise P15CBenchmarkError(
            "PRIVATE_CASE_FILE_SET",
            "private benchmark snapshot does not match its packet",
        )
    for provider_id in P15C_ENABLED_PROVIDER_IDS:
        if packet.provider_transfer_authority_by_provider[provider_id] is not True:
            raise P15CBenchmarkError(
                "PRIVATE_CASE_TRANSFER_AUTHORITY",
                "private benchmark transfer authority is incomplete",
            )
    case_record = {
        "case_id": "private-target",
        "target_packet_sha256": packet.packet_sha256,
        "files": [
            {
                "path": item.path,
                "sha256": item.sha256,
                "git_blob_sha": item.git_blob_sha,
            }
            for item in files
        ],
        "prompt_version": P15C_PROMPT_VERSION,
    }
    return P15CBenchmarkCase(
        case_id="private-target",
        files=files,
        case_sha256=_canonical_sha256(case_record),
        expected_finding_paths=frozenset(),
        private_target=True,
    )


def build_p15c_request(
    packet: P15CProviderPacket,
    case: P15CBenchmarkCase,
) -> tuple[bytes, str]:
    if case.case_id not in P15C_CASE_IDS:
        raise P15CBenchmarkError("CASE_ID", "P15C benchmark case is invalid")
    review_input = {
        "case_id": case.case_id,
        "review_mode": "read-only",
        "allowed_paths": sorted(case.allowed_paths),
        "files": [item.private_record() for item in case.files],
    }
    review_json = _canonical_json(review_input).decode("utf-8")
    system_prompt = (
        "Perform a read-only code review of only the supplied snapshot. Do not use "
        "tools, external knowledge, or network access. Do not propose or imply that "
        "you changed a repository. Return json only. Every finding path must be one "
        "of allowed_paths. Report only concrete issues grounded in the supplied "
        "bytes. Use lowercase category and severity values."
    )
    user_prompt = (
        "Review this snapshot and return the required JSON object with exact keys "
        "assessment, confidence_micros, and findings. Each finding must have exact "
        "keys path, category, severity, and summary. assessment is clean or "
        "issues_found. confidence_micros is an integer from 0 through 1000000. "
        "findings is an array. category is correctness, maintainability, reliability, "
        "security, or testability. severity is critical, high, medium, or low. "
        "summary must be concise and must not quote secrets.\n\nSNAPSHOT_JSON:\n"
        + review_json
    )
    if packet.provider_id == "openai":
        request = {
            "model": packet.model_id,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_output_tokens": P15C_REQUESTED_OUTPUT_TOKENS,
            "store": False,
            "tools": [],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "p15c_read_only_code_review",
                    "strict": True,
                    "schema": _p15c_output_schema(),
                }
            },
        }
    elif packet.provider_id == "deepseek":
        request = {
            "model": packet.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": P15C_REQUESTED_OUTPUT_TOKENS,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
            "tools": [],
        }
    else:
        raise P15CBenchmarkError(
            "PROVIDER_NOT_ENABLED",
            "P15C provider is not enabled",
        )
    body = _canonical_json(request)
    # Byte count is a deliberately conservative tokenizer-independent ceiling:
    # byte-fallback tokenizers cannot consume more than one token per byte.
    estimated_input_tokens = len(body)
    if len(body) > P15C_MAX_PROMPT_BYTES or estimated_input_tokens > packet.max_input_tokens:
        raise P15CBenchmarkError(
            "REQUEST_INPUT_BUDGET",
            "P15C benchmark request exceeds its input budget",
        )
    if P15C_REQUESTED_OUTPUT_TOKENS > packet.max_output_tokens:
        raise P15CBenchmarkError(
            "REQUEST_OUTPUT_BUDGET",
            "P15C benchmark request exceeds its output budget",
        )
    request_sha256 = hashlib.sha256(body).hexdigest()
    return body, request_sha256


def parse_p15c_provider_response(
    packet: P15CProviderPacket,
    response: P15CHTTPResponse,
) -> P15CParsedResponse:
    if response.status_code != 200:
        if response.status_code == 401:
            code = "AUTH_INVALID_KEY"
        elif response.status_code == 403:
            code = "ACCESS_FORBIDDEN"
        elif response.status_code == 429:
            code = "RATE_LIMIT"
        elif 500 <= response.status_code <= 599:
            code = "PROVIDER_OUTAGE"
        else:
            code = "PROVIDER_REJECTED_REQUEST"
        raise P15CBenchmarkError(code, "provider returned a redacted HTTP failure")
    try:
        root = json.loads(
            response.body.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise P15CBenchmarkError(
            "PROVIDER_RESPONSE_INVALID",
            "provider response is not valid JSON",
        ) from exc
    if not isinstance(root, dict):
        raise P15CBenchmarkError(
            "PROVIDER_RESPONSE_INVALID",
            "provider response root is invalid",
        )
    if root.get("model") != packet.model_id:
        raise P15CBenchmarkError(
            "PROVIDER_MODEL_DRIFT",
            "provider response model does not match the frozen packet",
        )
    if packet.provider_id == "openai":
        if root.get("status") != "completed":
            raise P15CBenchmarkError(
                "OPENAI_RESPONSE_INCOMPLETE",
                "OpenAI response did not complete",
            )
        text = _openai_output_text(root)
        usage = root.get("usage")
        if not isinstance(usage, dict):
            raise P15CBenchmarkError("USAGE_INVALID", "provider usage is invalid")
        input_tokens = _nonnegative_int(usage.get("input_tokens"), "input tokens")
        output_tokens = _nonnegative_int(
            usage.get("output_tokens"), "output tokens"
        )
        details = usage.get("input_tokens_details", {})
        cached = (
            _nonnegative_int(details.get("cached_tokens", 0), "cached tokens")
            if isinstance(details, dict)
            else 0
        )
    elif packet.provider_id == "deepseek":
        choices = root.get("choices")
        if not isinstance(choices, list) or len(choices) != 1:
            raise P15CBenchmarkError(
                "DEEPSEEK_RESPONSE_INVALID",
                "DeepSeek response choices are invalid",
            )
        choice = choices[0]
        if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
            raise P15CBenchmarkError(
                "DEEPSEEK_RESPONSE_INCOMPLETE",
                "DeepSeek response did not complete",
            )
        message = choice.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise P15CBenchmarkError(
                "DEEPSEEK_RESPONSE_INVALID",
                "DeepSeek response content is invalid",
            )
        text = message["content"]
        usage = root.get("usage")
        if not isinstance(usage, dict):
            raise P15CBenchmarkError("USAGE_INVALID", "provider usage is invalid")
        input_tokens = _nonnegative_int(usage.get("prompt_tokens"), "input tokens")
        output_tokens = _nonnegative_int(
            usage.get("completion_tokens"), "output tokens"
        )
        cached = 0
    else:
        raise P15CBenchmarkError("PROVIDER_NOT_ENABLED", "provider is not enabled")
    if (
        input_tokens > packet.max_input_tokens
        or output_tokens > packet.max_output_tokens
        or input_tokens + output_tokens > packet.max_total_tokens
    ):
        raise P15CBenchmarkError(
            "PROVIDER_USAGE_ABOVE_PACKET",
            "provider usage exceeds the frozen packet",
        )
    try:
        output = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError) as exc:
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_JSON",
            "model output is not valid JSON",
        ) from exc
    if not isinstance(output, dict):
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_SCHEMA",
            "model output root is invalid",
        )
    _validate_p15c_output(output)
    return P15CParsedResponse(
        output=output,
        output_sha256=_canonical_sha256(output),
        input_tokens=input_tokens,
        cached_input_tokens=min(cached, input_tokens),
        output_tokens=output_tokens,
    )


class P15CBenchmarkExecutor:
    def __init__(
        self,
        *,
        repository_root: str | Path,
        packet_config_path: str | Path,
        policy_path: str | Path,
        credential_resolver: OwnerOnlyCredentialResolver,
        ledger: P15CUsageLedger,
        transport: P15CTransport,
        target_packet: P15CTargetPacket,
        monotonic: object = time.monotonic,
    ) -> None:
        self._repository_root = Path(repository_root).resolve(strict=True)
        self._packet_config_path = Path(packet_config_path).resolve(strict=True)
        self._policy_path = Path(policy_path)
        self._credential_resolver = credential_resolver
        self._ledger = ledger
        self._transport = transport
        self._target_packet = target_packet
        if not callable(monotonic):
            raise TypeError("monotonic must be callable")
        self._monotonic = monotonic

    def preflight(
        self,
        packets: Sequence[P15CProviderPacket],
        cases: Sequence[P15CBenchmarkCase],
    ) -> dict[str, object]:
        policy = load_execution_policy(self._policy_path)
        policy.assert_active()
        packet_tuple = tuple(packets)
        case_tuple = tuple(cases)
        self._assert_complete_matrix(policy, packet_tuple, case_tuple)
        source_seal = self._source_seal(policy)
        if self._ledger.attempts():
            raise P15CBenchmarkError(
                "LEDGER_NOT_EMPTY",
                "P15C preflight requires an unused usage ledger",
            )
        request_hashes: list[str] = []
        credential_references_resolved = 0
        for packet in packet_tuple:
            for case in case_tuple:
                _, request_sha256 = build_p15c_request(packet, case)
                request_hashes.append(request_sha256)
            value = self._credential_resolver.resolve(
                packet.credential_reference,
                packet.provider_id,
            )
            credential_references_resolved += 1
            del value
        return {
            "status": "PASS",
            "authorization_id": policy.authorization_id,
            "policy_sha256": policy.policy_sha256,
            "source_seal": source_seal.audit_record(),
            "packet_count": len(packet_tuple),
            "case_count": len(case_tuple),
            "planned_provider_invocations": len(packet_tuple) * len(case_tuple),
            "request_set_sha256": _canonical_sha256(sorted(request_hashes)),
            "credential_references_resolved": credential_references_resolved,
            "credential_values_recorded": 0,
            "target_packet_sha256": self._target_packet.packet_sha256,
            "target_identity_recorded": False,
            "target_paths_recorded": False,
            "target_mutations": 0,
            "provider_invocations": 0,
            "network_operations": 0,
        }

    def execute(
        self,
        packet: P15CProviderPacket,
        case: P15CBenchmarkCase,
        *,
        cancellation: P15CCancellationSignal | None = None,
    ) -> P15CAttemptOutcome:
        policy = load_execution_policy(self._policy_path)
        policy.assert_active()
        self._assert_route(policy, packet, case)
        self._source_seal(policy)
        body, request_sha256 = build_p15c_request(packet, case)
        attempt_id = self._attempt_id(packet, case)
        previous = self._ledger.attempt(attempt_id)
        if previous is not None:
            return P15CAttemptOutcome(
                attempt_id=previous.attempt_id,
                provider_id=previous.provider_id,
                model_id=packet.model_id,
                case_id=previous.case_id,
                status=previous.status,
                request_sha256=previous.request_sha256,
                output_sha256=previous.output_sha256,
                input_tokens=previous.input_tokens,
                output_tokens=previous.output_tokens,
                duration_ms=previous.duration_ms,
                charged_micro_usd=previous.charged_micro_usd,
                metrics=previous.metrics,
                failure_code=previous.failure_code or "LEDGER_REPLAY_BLOCKED",
            )
        self._ledger.reserve(
            attempt_id=attempt_id,
            provider_id=packet.provider_id,
            case_id=case.case_id,
            request_sha256=request_sha256,
            reservation_micro_usd=packet.per_attempt_hard_cap_micro_usd,
            total_budget_micro_usd=policy.total_budget_micro_usd,
            provider_budget_micro_usd=policy.provider_budget_micro_usd[
                packet.provider_id
            ],
        )
        if cancellation is not None and cancellation.is_cancelled():
            self._ledger.release_without_transport(attempt_id)
            return _failed_outcome(
                attempt_id,
                packet,
                case,
                request_sha256,
                status="CANCELLED",
                failure_code="CANCELLED_PRETRANSPORT",
            )
        try:
            current_policy = load_execution_policy(self._policy_path)
            current_policy.assert_active()
            self._assert_route(current_policy, packet, case)
            self._source_seal(current_policy)
            credential = self._credential_resolver.resolve(
                packet.credential_reference,
                packet.provider_id,
            )
        except (P15CControlError, P15CBenchmarkError) as exc:
            self._ledger.release_without_transport(attempt_id)
            code = getattr(exc, "code", "PRETRANSPORT_BLOCK")
            return _failed_outcome(
                attempt_id,
                packet,
                case,
                request_sha256,
                status="BLOCKED",
                failure_code=str(code),
            )
        headers = {
            "authorization": f"Bearer {credential}",
            "content-type": "application/json",
            "user-agent": "tool-system-p15c-read-only-benchmark/1",
        }
        del credential
        if cancellation is not None and cancellation.is_cancelled():
            self._ledger.release_without_transport(attempt_id)
            return _failed_outcome(
                attempt_id,
                packet,
                case,
                request_sha256,
                status="CANCELLED",
                failure_code="CANCELLED_PRETRANSPORT",
            )
        self._ledger.mark_transport_started(attempt_id)
        started = float(self._monotonic())
        try:
            response = self._transport.send(
                host=packet.host,
                path=packet.path,
                headers=headers,
                body=body,
                timeout_seconds=float(packet.request_timeout_seconds),
            )
            parsed = parse_p15c_provider_response(packet, response)
            duration_ms = max(0, math.ceil((float(self._monotonic()) - started) * 1000))
            if duration_ms > packet.wall_clock_timeout_seconds * 1000:
                raise P15CBenchmarkError(
                    "WALL_CLOCK_TIMEOUT",
                    "P15C attempt exceeded its wall-clock limit",
                )
            metrics = build_p15c_metrics(parsed.output, case)
            charged = calculate_p15c_cost_micro_usd(packet, parsed)
            if charged > packet.per_attempt_hard_cap_micro_usd:
                raise P15CBenchmarkError(
                    "COST_ABOVE_PACKET",
                    "P15C provider cost exceeds its packet",
                )
            if cancellation is not None and cancellation.is_cancelled():
                metrics = {**metrics, "cancelled_after_transport": True}
                terminal_status = "CANCELLED"
            else:
                terminal_status = "PASS"
            self._ledger.settle(
                attempt_id,
                charged_micro_usd=charged,
                output_sha256=parsed.output_sha256,
                input_tokens=parsed.input_tokens,
                output_tokens=parsed.output_tokens,
                duration_ms=duration_ms,
                metrics=metrics,
            )
            return P15CAttemptOutcome(
                attempt_id=attempt_id,
                provider_id=packet.provider_id,
                model_id=packet.model_id,
                case_id=case.case_id,
                status=terminal_status,
                request_sha256=request_sha256,
                output_sha256=parsed.output_sha256,
                input_tokens=parsed.input_tokens,
                output_tokens=parsed.output_tokens,
                duration_ms=duration_ms,
                charged_micro_usd=charged,
                metrics=metrics,
                failure_code=(
                    "CANCELLED_AFTER_TRANSPORT"
                    if terminal_status == "CANCELLED"
                    else None
                ),
            )
        except KeyboardInterrupt:
            self._ledger.record_transport_failure(attempt_id, "INTERRUPTED")
            raise
        except P15CTransportFailure as exc:
            self._ledger.record_transport_failure(attempt_id, exc.failure_code)
            return _failed_outcome(
                attempt_id,
                packet,
                case,
                request_sha256,
                status="ERROR",
                failure_code=exc.failure_code,
                charged_micro_usd=packet.per_attempt_hard_cap_micro_usd,
            )
        except P15CBenchmarkError as exc:
            self._ledger.record_transport_failure(attempt_id, exc.code)
            return _failed_outcome(
                attempt_id,
                packet,
                case,
                request_sha256,
                status="ERROR",
                failure_code=exc.code,
                charged_micro_usd=packet.per_attempt_hard_cap_micro_usd,
            )

    def _assert_complete_matrix(
        self,
        policy: P15CExecutionPolicy,
        packets: tuple[P15CProviderPacket, ...],
        cases: tuple[P15CBenchmarkCase, ...],
    ) -> None:
        if tuple(packet.provider_id for packet in packets) != P15C_ENABLED_PROVIDER_IDS:
            raise P15CBenchmarkError(
                "PROVIDER_MATRIX",
                "P15C provider matrix is incomplete",
            )
        if tuple(case.case_id for case in cases) != P15C_CASE_IDS:
            raise P15CBenchmarkError("CASE_MATRIX", "P15C case matrix is incomplete")
        if policy.max_provider_invocations != len(packets) * len(cases):
            raise P15CBenchmarkError(
                "INVOCATION_MATRIX",
                "P15C invocation ceiling does not equal the exact matrix",
            )
        required_total_budget = sum(
            packet.per_attempt_hard_cap_micro_usd * len(cases)
            for packet in packets
        )
        if policy.total_budget_micro_usd < required_total_budget:
            raise P15CBenchmarkError(
                "TOTAL_POLICY_BUDGET",
                "private total budget cannot cover the exact matrix",
            )
        for packet in packets:
            for case in cases:
                self._assert_route(policy, packet, case)

    def _assert_route(
        self,
        policy: P15CExecutionPolicy,
        packet: P15CProviderPacket,
        case: P15CBenchmarkCase,
    ) -> None:
        if packet.provider_id not in P15C_ENABLED_PROVIDER_IDS:
            raise P15CBenchmarkError("PROVIDER_NOT_ENABLED", "provider is not enabled")
        if policy.max_provider_invocations != len(P15C_ENABLED_PROVIDER_IDS) * len(
            P15C_CASE_IDS
        ):
            raise P15CBenchmarkError(
                "INVOCATION_MATRIX",
                "P15C invocation ceiling does not equal the exact matrix",
            )
        frozen_packets = {
            item.provider_id: item
            for item in load_p15c_provider_packets(self._packet_config_path)
        }
        if frozen_packets.get(packet.provider_id) != packet:
            raise P15CBenchmarkError(
                "PROVIDER_PACKET_DRIFT",
                "provider packet does not match the frozen catalog",
            )
        if policy.expected_target_packet_sha256 != self._target_packet.packet_sha256:
            raise P15CBenchmarkError(
                "TARGET_PACKET_POLICY_DRIFT",
                "private policy does not bind the exact target packet",
            )
        if policy.provider_enabled[packet.provider_id] is not True:
            raise P15CBenchmarkError(
                "PROVIDER_POLICY_DISABLED",
                "provider is disabled by private policy",
            )
        minimum_allocation = packet.per_attempt_hard_cap_micro_usd * len(P15C_CASE_IDS)
        if policy.provider_budget_micro_usd[packet.provider_id] < minimum_allocation:
            raise P15CBenchmarkError(
                "PROVIDER_POLICY_BUDGET",
                "provider private sub-budget cannot cover the exact matrix",
            )
        if case.case_id not in policy.allowed_case_ids:
            raise P15CBenchmarkError("CASE_NOT_AUTHORIZED", "case is not authorized")
        if case.case_id == "deterministic-corpus":
            expected_case = load_p15c_deterministic_case(
                self._repository_root,
                self._packet_config_path,
            )
        elif case.case_id == "private-target":
            expected_case = build_p15c_private_case(
                self._target_packet,
                case.files,
            )
        else:  # pragma: no cover - policy validation fixes the case set
            raise P15CBenchmarkError("CASE_NOT_AUTHORIZED", "case is not authorized")
        if expected_case != case:
            raise P15CBenchmarkError(
                "BENCHMARK_CASE_DRIFT",
                "benchmark case does not match its frozen source",
            )
        if case.private_target:
            if (
                policy.private_repository_transfer_enabled is not True
                or policy.provider_transfer_enabled[packet.provider_id] is not True
                or self._target_packet.provider_transfer_authority_by_provider[
                    packet.provider_id
                ]
                is not True
            ):
                raise P15CBenchmarkError(
                    "PRIVATE_TRANSFER_NOT_AUTHORIZED",
                    "private repository transfer is not authorized",
                )

    def _source_seal(self, policy: P15CExecutionPolicy):
        return build_execution_source_seal(
            self._repository_root,
            expected_commit_sha=policy.expected_tool_system_commit,
            expected_tree_sha=policy.expected_tool_system_tree,
            critical_source_paths=P15C_CRITICAL_SOURCE_PATHS,
        )

    def _attempt_id(
        self,
        packet: P15CProviderPacket,
        case: P15CBenchmarkCase,
    ) -> str:
        binding = {
            "authorization_id": "P15C-CROSS-PROVIDER-READ-ONLY-BENCHMARK-LIFECYCLE-v1",
            "canonical_tree": load_execution_policy(
                self._policy_path
            ).expected_tool_system_tree,
            "packet_sha256": packet.packet_sha256,
            "case_sha256": case.case_sha256,
            "target_packet_sha256": self._target_packet.packet_sha256,
        }
        return (
            f"p15c-{_canonical_sha256(binding)[:24]}-"
            f"{packet.provider_id}-{case.case_id}"
        )


def build_p15c_metrics(
    output: Mapping[str, object],
    case: P15CBenchmarkCase,
) -> dict[str, object]:
    _validate_p15c_output(output)
    findings = output["findings"]
    assert isinstance(findings, list)
    severity_counts = {severity: 0 for severity in P15C_FINDING_SEVERITIES}
    category_counts = {category: 0 for category in P15C_FINDING_CATEGORIES}
    grounded_paths: set[str] = set()
    for finding in findings:
        assert isinstance(finding, dict)
        severity_counts[str(finding["severity"])] += 1
        category_counts[str(finding["category"])] += 1
        path = str(finding["path"])
        if path in case.allowed_paths:
            grounded_paths.add(path)
    finding_count = len(findings)
    grounded_finding_count = sum(
        1
        for finding in findings
        if isinstance(finding, dict) and finding.get("path") in case.allowed_paths
    )
    grounded_ratio = (
        1_000_000
        if finding_count == 0
        else grounded_finding_count * 1_000_000 // finding_count
    )
    expected_recall: int | None = None
    if case.expected_finding_paths:
        expected_recall = (
            len(grounded_paths & case.expected_finding_paths)
            * 1_000_000
            // len(case.expected_finding_paths)
        )
    return {
        "assessment": output["assessment"],
        "schema_valid": True,
        "finding_count": finding_count,
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "grounded_finding_count": grounded_finding_count,
        "grounded_path_ratio_micros": grounded_ratio,
        "expected_path_recall_micros": expected_recall,
        "confidence_micros": output["confidence_micros"],
    }


def calculate_p15c_cost_micro_usd(
    packet: P15CProviderPacket,
    parsed: P15CParsedResponse,
) -> int:
    if packet.provider_id == "openai":
        uncached = parsed.input_tokens - parsed.cached_input_tokens
        numerator = (
            uncached * 200_000
            + parsed.cached_input_tokens * 20_000
            + parsed.output_tokens * 1_200_000
        )
    elif packet.provider_id == "deepseek":
        numerator = (
            parsed.input_tokens * 280_000 + parsed.output_tokens * 560_000
        )
    else:
        raise P15CBenchmarkError("PROVIDER_NOT_ENABLED", "provider is not enabled")
    return math.ceil(numerator / 1_000_000)


def _failed_outcome(
    attempt_id: str,
    packet: P15CProviderPacket,
    case: P15CBenchmarkCase,
    request_sha256: str,
    *,
    status: str,
    failure_code: str,
    charged_micro_usd: int = 0,
) -> P15CAttemptOutcome:
    return P15CAttemptOutcome(
        attempt_id=attempt_id,
        provider_id=packet.provider_id,
        model_id=packet.model_id,
        case_id=case.case_id,
        status=status,
        request_sha256=request_sha256,
        output_sha256=None,
        input_tokens=0,
        output_tokens=0,
        duration_ms=0,
        charged_micro_usd=charged_micro_usd,
        metrics=None,
        failure_code=failure_code,
    )


def _p15c_output_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["assessment", "confidence_micros", "findings"],
        "properties": {
            "assessment": {"type": "string", "enum": ["clean", "issues_found"]},
            "confidence_micros": {"type": "integer"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "category", "severity", "summary"],
                    "properties": {
                        "path": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": list(P15C_FINDING_CATEGORIES),
                        },
                        "severity": {
                            "type": "string",
                            "enum": list(P15C_FINDING_SEVERITIES),
                        },
                        "summary": {"type": "string"},
                    },
                },
            },
        },
    }


def _validate_p15c_output(output: Mapping[str, object]) -> None:
    if set(output) != {"assessment", "confidence_micros", "findings"}:
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_SCHEMA",
            "model output fields are invalid",
        )
    if output["assessment"] not in {"clean", "issues_found"}:
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_SCHEMA",
            "model assessment is invalid",
        )
    confidence = output["confidence_micros"]
    if type(confidence) is not int or not 0 <= confidence <= 1_000_000:
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_SCHEMA",
            "model confidence is invalid",
        )
    findings = output["findings"]
    if not isinstance(findings, list) or len(findings) > P15C_FINDING_LIMIT:
        raise P15CBenchmarkError(
            "MODEL_OUTPUT_INVALID_SCHEMA",
            "model findings are invalid",
        )
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != {
            "path",
            "category",
            "severity",
            "summary",
        }:
            raise P15CBenchmarkError(
                "MODEL_OUTPUT_INVALID_SCHEMA",
                "model finding fields are invalid",
            )
        if (
            not isinstance(finding["path"], str)
            or not finding["path"]
            or finding["category"] not in P15C_FINDING_CATEGORIES
            or finding["severity"] not in P15C_FINDING_SEVERITIES
            or not isinstance(finding["summary"], str)
            or not 1 <= len(finding["summary"]) <= P15C_FINDING_SUMMARY_MAX_CHARS
        ):
            raise P15CBenchmarkError(
                "MODEL_OUTPUT_INVALID_SCHEMA",
                "model finding value is invalid",
            )


def _openai_output_text(root: Mapping[str, object]) -> str:
    output = root.get("output")
    if not isinstance(output, list):
        raise P15CBenchmarkError(
            "OPENAI_RESPONSE_INVALID",
            "OpenAI output is invalid",
        )
    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "refusal":
                raise P15CBenchmarkError(
                    "OPENAI_REFUSAL",
                    "OpenAI returned a refusal",
                )
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
    if len(texts) != 1:
        raise P15CBenchmarkError(
            "OPENAI_RESPONSE_INVALID",
            "OpenAI output text is invalid",
        )
    return texts[0]


def _canonical_json(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise P15CBenchmarkError("CANONICAL_JSON", "value is not canonical JSON") from exc
    return rendered.encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise P15CBenchmarkError("USAGE_INVALID", f"{label} is invalid")
    return value


def _repository_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise P15CBenchmarkError("PATH_INVALID", "repository path is invalid")
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(
        part in {"", ".", ".."} for part in pure.parts
    ):
        raise P15CBenchmarkError("PATH_INVALID", "repository path is invalid")
    return value


def _git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()
