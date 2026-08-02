from __future__ import annotations

import http.client
import json
import os
import ssl
import stat
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]

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
from tool_system.process_authority.live_provider_approval import (
    P14C_APPROVAL_ACTION,
    P14C_APPROVAL_REPOSITORY,
    P14C_LIVE_EXECUTION_AUTHORIZATION_ID,
    P14C_LIVE_TRANSPORT_KIND,
    P14CExecutionSourceSeal,
    P14CLiveExecutionBinding,
    build_p14c_execution_source_seal,
    build_p14c_live_execution_approval_body,
    issue_p14c_live_execution_grant,
    validate_p14c_execution_source_seal,
)

P14C_AUTHORIZATION_PACKET = "P14C-DEEPSEEK-RECOVERY-v1"
P14C_IMPLEMENTATION_AUTHORIZATION_BASE_SHA = (
    "d9c211324487e3bfd31c1276763ed2ed781cc085"
)
P14C_FIXTURE_ID = "P14C-001"
DEEPSEEK_PROVIDER_ID = "deepseek"
DEEPSEEK_MODEL_ID = "deepseek-v4-flash"
DEEPSEEK_HOST = "api.deepseek.com"
DEEPSEEK_PATH = "/chat/completions"
DEEPSEEK_CREDENTIAL_REFERENCE = (
    "file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key"
)
DEEPSEEK_CREDENTIAL_FILE = Path("~/.config/tool-system/credentials.toml")
P14C_PROMPT_ID = "p14c-bounded-provider-proof"
P14C_PROMPT_VERSION = "v1"
MAX_RESPONSE_BYTES = 1_048_576
RETRYABLE_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class P14CExecutionPacket:
    packet_id: str
    implementation_authorization_base_sha: str
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
            "implementation_authorization_base_sha": (
                self.implementation_authorization_base_sha
            ),
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
        implementation_authorization_base_sha=(
            P14C_IMPLEMENTATION_AUTHORIZATION_BASE_SHA
        ),
        fixture_id=P14C_FIXTURE_ID,
        provider_id=DEEPSEEK_PROVIDER_ID,
        model_id=DEEPSEEK_MODEL_ID,
        method="POST",
        host=DEEPSEEK_HOST,
        path=DEEPSEEK_PATH,
        credential_reference=DEEPSEEK_CREDENTIAL_REFERENCE,
        prompt_id=P14C_PROMPT_ID,
        prompt_version=P14C_PROMPT_VERSION,
        required_capabilities=("structured-output", "tool-free-generation"),
        required_output_keys=("summary", "control_status"),
        reasoning_effort="none",
        store=False,
        tools_allowed=False,
        per_attempt_input_tokens=1_024,
        per_attempt_output_tokens=128,
        per_attempt_total_tokens=1_152,
        max_attempts=1,
        cumulative_token_ceiling=1_152,
        request_timeout_ms=20_000,
        total_wall_clock_ms=25_000,
        cumulative_cost_microusd=2_000,
        input_price_microusd_per_token=1,
        output_price_microusd_per_token=2,
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
            reasons.append(
                f"packet field {key} does not match {P14C_AUTHORIZATION_PACKET}"
            )
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
            context_window_tokens=1_000_000,
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


class P14CTransport(Protocol):
    transport_kind: str

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
    def __init__(
        self,
        message: str,
        *,
        failure_class: str = "KEY_MISSING_OR_UNREADABLE",
    ) -> None:
        super().__init__(message)
        self.failure_class = failure_class


class TransportFailure(RuntimeError):
    def __init__(self, failure_class: str, *, retryable: bool) -> None:
        super().__init__(failure_class)
        self.failure_class = failure_class
        self.retryable = retryable


class LocalCredentialFileResolver:
    """Read one exact DeepSeek key from an owner-only local TOML file."""

    def __init__(self, credential_file: str | Path | None = None) -> None:
        selected = (
            credential_file
            if credential_file is not None
            else DEEPSEEK_CREDENTIAL_FILE
        )
        self._credential_file = Path(selected).expanduser()

    def resolve(self, reference: str) -> str:
        if reference != DEEPSEEK_CREDENTIAL_REFERENCE:
            raise CredentialResolutionFailure("credential reference is not approved")
        path = self._credential_file
        try:
            path_stat = path.lstat()
            parent_stat = path.parent.lstat()
        except OSError:
            raise CredentialResolutionFailure(
                "approved credential file is unavailable"
            ) from None
        if (
            stat.S_ISLNK(path_stat.st_mode)
            or not stat.S_ISREG(path_stat.st_mode)
            or path_stat.st_nlink != 1
            or path_stat.st_uid != os.getuid()
            or path_stat.st_mode & 0o077
        ):
            raise CredentialResolutionFailure(
                "approved credential file is not owner-only regular storage"
            )
        if (
            stat.S_ISLNK(parent_stat.st_mode)
            or not stat.S_ISDIR(parent_stat.st_mode)
            or parent_stat.st_uid != os.getuid()
            or parent_stat.st_mode & 0o077
        ):
            raise CredentialResolutionFailure(
                "approved credential directory is not owner-only"
            )
        try:
            with path.open("rb") as handle:
                record = tomllib.load(handle)
            value = record["providers"]["deepseek"]["api_key"]
        except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
            raise CredentialResolutionFailure(
                "approved credential record is unavailable"
            ) from None
        if not isinstance(value, str) or not value:
            raise CredentialResolutionFailure("approved credential is unavailable")
        if any(character.isspace() for character in value):
            raise CredentialResolutionFailure(
                "approved credential contains whitespace",
                failure_class="KEY_INVALID",
            )
        return value


class DeepSeekChatCompletionsTransport:
    """Direct TLS transport that ignores proxy environment and refuses redirects."""

    transport_kind = "live_network"

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
            or host != DEEPSEEK_HOST
            or path != DEEPSEEK_PATH
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


_P14C_CAPABILITY_ISSUER = object()
_P14C_FAKE_TRANSPORT_KIND = "injected_fake"
_P14C_FAKE_AUTHORIZATION_ID = "P14C-CORR-v1:fake-transport-test"


class P14CLiveExecutionCapability:
    """Opaque, exact-action authorization consumed by the provider entrypoint."""

    __slots__ = (
        "_approval_comment_id",
        "_approval_issue_number",
        "_approval_record_sha256",
        "_authorization_id",
        "_consumed",
        "_expires_at_epoch_seconds",
        "_lock",
        "_packet_sha256",
        "_request_sha256",
        "_repository_root",
        "_replay_ledger",
        "_sealed",
        "_source_seal",
        "_transport",
        "_transport_kind",
    )

    def __init__(
        self,
        *,
        authorization_id: str,
        packet_sha256: str,
        request_sha256: str,
        transport_kind: str,
        transport: P14CTransport,
        approval_record_sha256: str | None = None,
        approval_comment_id: int | None = None,
        approval_issue_number: int | None = None,
        expires_at_epoch_seconds: int | None = None,
        source_seal: P14CExecutionSourceSeal | None = None,
        repository_root: Path | None = None,
        replay_ledger: object | None = None,
        _issuer: object,
    ) -> None:
        if _issuer is not _P14C_CAPABILITY_ISSUER:
            raise TypeError("P14C live execution capabilities require an approved issuer")
        fake_capability = (
            authorization_id == _P14C_FAKE_AUTHORIZATION_ID
            and transport_kind == _P14C_FAKE_TRANSPORT_KIND
            and getattr(transport, "transport_kind", None)
            == _P14C_FAKE_TRANSPORT_KIND
            and approval_record_sha256 is None
            and approval_comment_id is None
            and approval_issue_number is None
            and expires_at_epoch_seconds is None
            and source_seal is None
            and repository_root is None
            and replay_ledger is None
        )
        live_capability = (
            authorization_id == P14C_LIVE_EXECUTION_AUTHORIZATION_ID
            and transport_kind == P14C_LIVE_TRANSPORT_KIND
            and type(transport) is DeepSeekChatCompletionsTransport
            and isinstance(approval_record_sha256, str)
            and len(approval_record_sha256) == 64
            and isinstance(approval_comment_id, int)
            and not isinstance(approval_comment_id, bool)
            and approval_comment_id > 0
            and isinstance(approval_issue_number, int)
            and not isinstance(approval_issue_number, bool)
            and approval_issue_number > 0
            and isinstance(expires_at_epoch_seconds, int)
            and not isinstance(expires_at_epoch_seconds, bool)
            and expires_at_epoch_seconds > 0
            and isinstance(source_seal, P14CExecutionSourceSeal)
            and isinstance(repository_root, Path)
            and replay_ledger is not None
        )
        if not fake_capability and not live_capability:
            raise TypeError("P14C live-network capability issuance is unavailable")
        object.__setattr__(self, "_authorization_id", authorization_id)
        object.__setattr__(self, "_packet_sha256", packet_sha256)
        object.__setattr__(self, "_request_sha256", request_sha256)
        object.__setattr__(self, "_transport_kind", transport_kind)
        object.__setattr__(self, "_transport", transport)
        object.__setattr__(self, "_source_seal", source_seal)
        object.__setattr__(self, "_repository_root", repository_root)
        object.__setattr__(self, "_replay_ledger", replay_ledger)
        object.__setattr__(
            self,
            "_approval_record_sha256",
            approval_record_sha256,
        )
        object.__setattr__(self, "_approval_comment_id", approval_comment_id)
        object.__setattr__(self, "_approval_issue_number", approval_issue_number)
        object.__setattr__(
            self,
            "_expires_at_epoch_seconds",
            expires_at_epoch_seconds,
        )
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_consumed", threading.Event())
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("P14C live execution capability is immutable")
        object.__setattr__(self, name, value)

    @property
    def authorization_id(self) -> str:
        return self._authorization_id

    @property
    def packet_sha256(self) -> str:
        return self._packet_sha256

    @property
    def request_sha256(self) -> str:
        return self._request_sha256

    @property
    def transport_kind(self) -> str:
        return self._transport_kind

    @property
    def approval_record_sha256(self) -> str | None:
        return self._approval_record_sha256

    @property
    def approval_comment_id(self) -> int | None:
        return self._approval_comment_id

    @property
    def approval_issue_number(self) -> int | None:
        return self._approval_issue_number

    @property
    def expires_at_epoch_seconds(self) -> int | None:
        return self._expires_at_epoch_seconds

    @property
    def source_seal(self) -> P14CExecutionSourceSeal | None:
        return self._source_seal

    def execution_source_reasons(self) -> tuple[str, ...]:
        if self._source_seal is None:
            return ()
        assert self._repository_root is not None
        assert self._replay_ledger is not None
        return validate_p14c_execution_source_seal(
            self._source_seal,
            repository_root=self._repository_root,
            replay_ledger=self._replay_ledger,  # type: ignore[arg-type]
        )

    def binding_reasons(
        self,
        *,
        packet: P14CExecutionPacket,
        request: AIWorkerRequest,
        transport: object,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.packet_sha256 != packet.sha256():
            reasons.append("live execution capability packet does not match")
        try:
            request_sha256 = request.sha256()
        except (AttributeError, TypeError, ValueError):
            request_sha256 = ""
        if self.request_sha256 != request_sha256:
            reasons.append("live execution capability request does not match")
        if self.transport_kind != getattr(transport, "transport_kind", None):
            reasons.append("live execution capability transport does not match")
        if self._transport is not transport:
            reasons.append("live execution capability transport instance does not match")
        if (
            self._expires_at_epoch_seconds is not None
            and time.time() > self._expires_at_epoch_seconds
        ):
            reasons.append("live execution capability has expired")
        reasons.extend(self.execution_source_reasons())
        return tuple(reasons)

    def consume(
        self,
        *,
        packet: P14CExecutionPacket,
        request: AIWorkerRequest,
        transport: object,
    ) -> tuple[str, ...]:
        reasons = self.binding_reasons(
            packet=packet,
            request=request,
            transport=transport,
        )
        if reasons:
            return reasons
        with self._lock:
            if (
                self._expires_at_epoch_seconds is not None
                and time.time() > self._expires_at_epoch_seconds
            ):
                return ("live execution capability has expired",)
            if self._consumed.is_set():
                return ("live execution capability was already consumed",)
            self._consumed.set()
        return ()


def _issue_p14c_fake_transport_capability(
    packet: P14CExecutionPacket,
    request: AIWorkerRequest,
    transport: P14CTransport,
) -> P14CLiveExecutionCapability:
    """Issue only a fake-transport capability for isolated contract tests."""

    reasons = list(validate_p14c_execution_packet(packet))
    try:
        request_sha256 = request.sha256()
    except (AttributeError, TypeError, ValueError):
        request_sha256 = ""
    expected_request_sha256 = build_p14c_synthetic_request(packet).sha256()
    if request_sha256 != expected_request_sha256:
        reasons.append("request is not the exact P14C-001 synthetic fixture")
    if getattr(transport, "transport_kind", None) != _P14C_FAKE_TRANSPORT_KIND:
        reasons.append("test capability transport is not injected_fake")
    if reasons:
        raise ValueError("; ".join(reasons))
    return P14CLiveExecutionCapability(
        authorization_id=_P14C_FAKE_AUTHORIZATION_ID,
        packet_sha256=packet.sha256(),
        request_sha256=request_sha256,
        transport_kind=_P14C_FAKE_TRANSPORT_KIND,
        transport=transport,
        _issuer=_P14C_CAPABILITY_ISSUER,
    )


def build_p14c_live_execution_binding(
    packet: P14CExecutionPacket,
    request: AIWorkerRequest,
    source_seal: P14CExecutionSourceSeal,
) -> P14CLiveExecutionBinding:
    reasons = list(validate_p14c_execution_packet(packet))
    try:
        request_sha256 = request.sha256()
    except (AttributeError, TypeError, ValueError):
        request_sha256 = ""
    if request_sha256 != build_p14c_synthetic_request(packet).sha256():
        reasons.append("request is not the exact P14C-001 synthetic fixture")
    if not isinstance(source_seal, P14CExecutionSourceSeal):
        reasons.append("execution source seal is invalid")
    if reasons:
        raise ValueError("; ".join(reasons))
    return P14CLiveExecutionBinding(
        authorization_id=P14C_LIVE_EXECUTION_AUTHORIZATION_ID,
        repository=P14C_APPROVAL_REPOSITORY,
        action=P14C_APPROVAL_ACTION,
        implementation_authorization_base_sha=(
            packet.implementation_authorization_base_sha
        ),
        execution_commit_sha=source_seal.execution_commit_sha,
        execution_tree_sha=source_seal.execution_tree_sha,
        source_manifest_sha256=source_seal.source_manifest_sha256,
        clean_worktree=source_seal.clean_worktree,
        execution_host_id=source_seal.execution_host_id,
        replay_ledger_instance_id=source_seal.replay_ledger_instance_id,
        packet_sha256=packet.sha256(),
        request_sha256=request_sha256,
        fixture_id=packet.fixture_id,
        provider_id=packet.provider_id,
        model_id=packet.model_id,
        method=packet.method,
        host=packet.host,
        path=packet.path,
        credential_reference=packet.credential_reference,
        transport_kind=P14C_LIVE_TRANSPORT_KIND,
        provider_invocation_ceiling=1,
        max_attempts=packet.max_attempts,
        cumulative_token_ceiling=packet.cumulative_token_ceiling,
        request_timeout_ms=packet.request_timeout_ms,
        total_wall_clock_ms=packet.total_wall_clock_ms,
        cumulative_cost_microusd=packet.cumulative_cost_microusd,
        target_repo_mutation_authorized=False,
        production_deployment_authorized=False,
        cleanup_execution_authorized=False,
        p14d_authorized=False,
    )


def build_p14c_github_approval_body(
    *,
    expires_at_utc: str,
    nonce: str,
    repository_root: str | Path,
    replay_ledger: object,
    packet: P14CExecutionPacket | None = None,
    request: AIWorkerRequest | None = None,
) -> str:
    active_packet = packet or build_p14c_execution_packet()
    active_request = request or build_p14c_synthetic_request(active_packet)
    source_seal = build_p14c_execution_source_seal(
        repository_root,
        replay_ledger,  # type: ignore[arg-type]
    )
    return build_p14c_live_execution_approval_body(
        build_p14c_live_execution_binding(
            active_packet, active_request, source_seal
        ),
        expires_at_utc=expires_at_utc,
        nonce=nonce,
    )


def issue_p14c_live_network_capability(
    *,
    comment_id: int,
    packet: P14CExecutionPacket,
    request: AIWorkerRequest,
    transport: DeepSeekChatCompletionsTransport,
    repository_root: str | Path,
    replay_ledger: object,
) -> P14CLiveExecutionCapability:
    """Authenticate GitHub owner authority and mint one exact live capability."""

    if type(transport) is not DeepSeekChatCompletionsTransport:
        raise TypeError("live capability requires the exact DeepSeek TLS transport")
    source_seal = build_p14c_execution_source_seal(
        repository_root,
        replay_ledger,  # type: ignore[arg-type]
    )
    binding = build_p14c_live_execution_binding(
        packet, request, source_seal
    )
    grant = issue_p14c_live_execution_grant(
        comment_id=comment_id,
        binding=binding,
        repository_root=repository_root,
        replay_ledger=replay_ledger,  # type: ignore[arg-type]
    )
    grant_reasons = grant.consume_for_capability(binding)
    if grant_reasons:
        raise ValueError("; ".join(grant_reasons))
    return P14CLiveExecutionCapability(
        authorization_id=binding.authorization_id,
        packet_sha256=binding.packet_sha256,
        request_sha256=binding.request_sha256,
        transport_kind=binding.transport_kind,
        transport=transport,
        approval_record_sha256=grant.approval_record_sha256,
        approval_comment_id=grant.comment_id,
        approval_issue_number=grant.issue_number,
        expires_at_epoch_seconds=grant.expires_at_epoch_seconds,
        source_seal=source_seal,
        repository_root=Path(repository_root).resolve(strict=True),
        replay_ledger=replay_ledger,
        _issuer=_P14C_CAPABILITY_ISSUER,
    )


@dataclass(frozen=True)
class P14CLiveExecutionGuard:
    packet_sha256: str
    capability: P14CLiveExecutionCapability | None = None

    def validate(
        self,
        request: AIWorkerRequest,
        provider: AIWorkerProvider,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.capability is None:
            reasons.append("live execution capability is absent")
        elif not isinstance(self.capability, P14CLiveExecutionCapability):
            reasons.append("live execution capability is invalid")
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
        provider_capability = getattr(provider, "execution_capability", None)
        if provider_capability is not self.capability:
            reasons.append("provider does not hold the execution guard capability")
        if isinstance(self.capability, P14CLiveExecutionCapability):
            reasons.extend(
                self.capability.binding_reasons(
                    packet=packet,
                    request=request,
                    transport=getattr(provider, "_transport", None),
                )
            )
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


class DeepSeekChatCompletionsProvider:
    provider_id = DEEPSEEK_PROVIDER_ID
    model_id = DEEPSEEK_MODEL_ID
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
        transport: P14CTransport,
        credential_resolver: CredentialResolver,
        execution_capability: P14CLiveExecutionCapability | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.packet = packet
        self.execution_capability = execution_capability
        self.transport_kind = getattr(transport, "transport_kind", None)
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

        if not isinstance(
            self.execution_capability,
            P14CLiveExecutionCapability,
        ):
            capability_reasons = ("live execution capability is absent",)
        else:
            capability_reasons = self.execution_capability.consume(
                packet=self.packet,
                request=request,
                transport=self._transport,
            )
        if capability_reasons:
            return _provider_error(
                AIWorkerErrorCode.PROVIDER_MISMATCH,
                "P14C provider execution capability denied invocation",
                reasons=capability_reasons,
            )

        body = _build_chat_completions_request_body(request, self.packet)
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

            assert isinstance(
                self.execution_capability, P14CLiveExecutionCapability
            )
            source_reasons = self.execution_capability.execution_source_reasons()
            if source_reasons:
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_MISMATCH,
                    "P14C execution source seal changed before credential access",
                    reasons=source_reasons,
                    duration_ms=elapsed_ms,
                )
            try:
                credential = self._credential_resolver.resolve(
                    self.packet.credential_reference
                )
            except CredentialResolutionFailure as exc:
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "approved provider credential is unavailable",
                    retryable=False,
                    reasons=(exc.failure_class,),
                    duration_ms=elapsed_ms,
                )
            except Exception:  # noqa: BLE001 - injected resolver must fail closed
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "credential resolver failed",
                    retryable=False,
                    reasons=("KEY_RESOLUTION_FAILED",),
                    duration_ms=elapsed_ms,
                )
            if not isinstance(credential, str) or not credential:
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "credential resolver returned an invalid value",
                    retryable=False,
                    reasons=("KEY_INVALID",),
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
                        reasons=("NETWORK_FAILED",),
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                retry_delay_ms = self.packet.default_backoff_ms
            except Exception:  # noqa: BLE001 - injected transport must fail closed
                return _provider_error(
                    AIWorkerErrorCode.PROVIDER_FAILURE,
                    "provider transport raised an unexpected exception",
                    retryable=False,
                    reasons=("PROVIDER_FAILED",),
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
                        reasons=(_classify_http_failure(response),),
                        duration_ms=_elapsed_ms(started_at, self._monotonic()),
                    )
                if attempt == self.packet.max_attempts:
                    return _provider_error(
                        AIWorkerErrorCode.PROVIDER_FAILURE,
                        "provider retry budget was exhausted",
                        retryable=True,
                        reasons=(_classify_http_failure(response),),
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


def _build_chat_completions_request_body(
    request: AIWorkerRequest,
    packet: P14CExecutionPacket,
) -> bytes:
    payload = request.inputs[0].payload
    body = {
        "model": packet.model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Evaluate only the supplied public synthetic control. "
                    "Return one valid json object with exactly summary and "
                    "control_status; use PASS or BLOCK and do not request tools."
                ),
            },
            {
                "role": "user",
                "content": canonical_json_bytes(payload).decode("utf-8"),
            },
        ],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "max_tokens": packet.per_attempt_output_tokens,
        "stream": False,
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
    choices = record.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response must contain exactly one choice",
            duration_ms=duration_ms,
        )
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response did not finish normally",
            duration_ms=duration_ms,
        )
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response assistant message is invalid",
            duration_ms=duration_ms,
        )
    output_text = message.get("content")
    if not isinstance(output_text, str):
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider response content is invalid",
            duration_ms=duration_ms,
        )
    try:
        output = json.loads(output_text)
    except json.JSONDecodeError:
        return _provider_error(
            AIWorkerErrorCode.INVALID_RESPONSE,
            "provider content is not valid JSON",
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
    input_tokens = usage_record.get("prompt_tokens")
    output_tokens = usage_record.get("completion_tokens")
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


def _classify_http_failure(response: HTTPTransportResponse) -> str:
    provider_code = ""
    try:
        record = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        record = None
    if isinstance(record, dict):
        error = record.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            provider_code = error["code"].lower()
        elif isinstance(record.get("code"), str):
            provider_code = record["code"].lower()
    if response.status_code == 401:
        return "AUTH_INVALID_KEY"
    if response.status_code == 403:
        return "ACCESS_FORBIDDEN"
    if response.status_code == 402 or any(
        marker in provider_code
        for marker in ("arrearage", "balance", "quota", "allocation")
    ):
        return "BALANCE_OR_QUOTA"
    if response.status_code == 429 or any(
        marker in provider_code for marker in ("throttl", "rate")
    ):
        return "RATE_LIMITED"
    if response.status_code >= 500:
        return "PROVIDER_FAILED"
    return "REQUEST_REJECTED"


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
