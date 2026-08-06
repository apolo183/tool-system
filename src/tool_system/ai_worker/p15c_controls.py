from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]

P15C_AUTHORIZATION_ID = "P15C-CROSS-PROVIDER-READ-ONLY-BENCHMARK-LIFECYCLE-v1"
P15C_POLICY_SCHEMA_VERSION = 4
P15C_SINGLE_PROVIDER_POLICY_SCHEMA_VERSION = 3
P15C_MATRIX_POLICY_SCHEMA_VERSION = 2
P15C_LEGACY_POLICY_SCHEMA_VERSION = 1
P15C_TARGET_PACKET_SCHEMA_VERSION = 1
P15C_LEDGER_SCHEMA_VERSION = 1
P15C_DEFAULT_SETTINGS_PATH = Path("~/.config/tool-system/settings.toml")
P15C_DEFAULT_CREDENTIALS_PATH = Path("~/.config/tool-system/credentials.toml")
P15C_DEFAULT_TARGET_PACKET_PATH = Path("~/.config/tool-system/p15c-target-packet.json")
P15C_DEFAULT_LEDGER_PATH = Path("~/.local/state/tool-system/p15c-usage.sqlite3")
P15C_PROVIDER_IDS = ("deepseek", "openai", "qwen")
P15C_DEFAULT_EXECUTION_PROVIDER_IDS = ("deepseek", "openai")
P15C_CASE_IDS = ("deterministic-corpus", "private-target")
P15C_BACKUP_SMOKE_CASE_IDS = ("deterministic-corpus",)
P15C_MAX_PROVIDER_INVOCATIONS = 4
P15C_PUBLIC_BUDGET_CEILING_MICRO_USD = 20_000_000
P15C_MIN_CNY_TO_MICRO_USD_CEILING = 1_000_000
P15C_MAX_CNY_TO_MICRO_USD_CEILING = 20_000_000
P15C_MAX_TARGET_FILES = 64
P15C_MAX_TARGET_FILE_BYTES = 262_144
P15C_MAX_TARGET_TOTAL_BYTES = 1_048_576
P15C_CANONICAL_REMOTES = frozenset(
    {
        "https://github.com/apolo183/tool-system",
        "https://github.com/apolo183/tool-system.git",
        "git@github.com:apolo183/tool-system.git",
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PACKET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_REPOSITORY_ID_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?/[A-Za-z0-9_.-]{1,100}$"
)
_UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_FORBIDDEN_PATH_PARTS = frozenset(
    {
        ".git",
        ".env",
        ".aws",
        ".ssh",
        "credentials",
        "credential",
        "secrets",
        "secret",
    }
)
_FORBIDDEN_SUFFIXES = frozenset({".key", ".pem", ".p12", ".pfx"})
_SECRET_CONTENT_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?<![A-Za-z0-9_-])gh[opusr]_[A-Za-z0-9]{8,}"),
    re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(
        r"(?i)(?:api[_-]?key|password|private[_-]?key)\s*[:=]\s*[\"'][^\"']{4,}[\"']"
    ),
)


class P15CControlError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class P15CExecutionPolicy:
    schema_version: int
    authorization_id: str
    enabled: bool
    total_budget_micro_usd: int
    expires_at_utc: str
    expected_tool_system_commit: str
    expected_tool_system_tree: str
    expected_target_packet_sha256: str | None
    provider_priority: tuple[str, ...]
    provider_model: Mapping[str, str]
    provider_enabled: Mapping[str, bool]
    provider_budget_micro_usd: Mapping[str, int]
    private_repository_transfer_enabled: bool
    provider_transfer_enabled: Mapping[str, bool]
    cny_to_micro_usd_ceiling: int
    allowed_case_ids: tuple[str, ...]
    max_provider_invocations: int
    transport_mode: str
    proxy_host: str | None
    proxy_port: int | None
    policy_sha256: str

    def assert_active(self, *, now: datetime | None = None) -> None:
        if not self.enabled:
            raise P15CControlError("POLICY_DISABLED", "execution policy is disabled")
        current = now or datetime.now(timezone.utc)
        expiry = _parse_utc(self.expires_at_utc)
        if current >= expiry:
            raise P15CControlError("POLICY_EXPIRED", "execution policy has expired")


@dataclass(frozen=True)
class P15CTargetInventoryItem:
    path: str
    sha256: str
    git_blob_sha: str
    size_bytes: int


@dataclass(frozen=True)
class P15CTargetPacket:
    packet_id: str
    repository_identity: str
    visibility: str
    branch: str
    exact_commit: str
    exact_file_allowlist: tuple[str, ...]
    content_addressed_inventory: tuple[P15CTargetInventoryItem, ...]
    durable_module_contract: Mapping[str, object]
    inventory_read_authority: bool
    benchmark_read_authority: bool
    provider_transfer_authority_by_provider: Mapping[str, bool]
    mutation_authority: bool
    snapshot_root: Path
    packet_sha256: str

    def assert_read_only_authority(self) -> None:
        if not self.inventory_read_authority or not self.benchmark_read_authority:
            raise P15CControlError(
                "TARGET_READ_NOT_AUTHORIZED",
                "private target read authority is incomplete",
            )
        if self.mutation_authority is not False:
            raise P15CControlError(
                "TARGET_MUTATION_NOT_DENIED",
                "private target packet must deny mutation",
            )


@dataclass(frozen=True)
class P15CSnapshotFile:
    path: str
    sha256: str
    git_blob_sha: str
    content: str

    def private_record(self) -> dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "git_blob_sha": self.git_blob_sha,
            "content": self.content,
        }


@dataclass(frozen=True)
class P15CExecutionSourceSeal:
    canonical_commit_sha: str
    canonical_tree_sha: str
    local_head_sha: str
    local_tree_sha: str
    clean_worktree: bool
    source_manifest_sha256: str

    def audit_record(self) -> dict[str, object]:
        return {
            "canonical_commit_sha": self.canonical_commit_sha,
            "canonical_tree_sha": self.canonical_tree_sha,
            "local_head_sha": self.local_head_sha,
            "local_tree_sha": self.local_tree_sha,
            "clean_worktree": self.clean_worktree,
            "source_manifest_sha256": self.source_manifest_sha256,
        }


@dataclass(frozen=True)
class P15CLedgerAttempt:
    attempt_id: str
    provider_id: str
    case_id: str
    status: str
    reserved_micro_usd: int
    charged_micro_usd: int
    request_sha256: str
    output_sha256: str | None
    input_tokens: int
    output_tokens: int
    duration_ms: int
    metrics: Mapping[str, object] | None
    failure_code: str | None

    def audit_record(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "provider_id": self.provider_id,
            "case_id": self.case_id,
            "status": self.status,
            "reserved_micro_usd": self.reserved_micro_usd,
            "charged_micro_usd": self.charged_micro_usd,
            "request_sha256": self.request_sha256,
            "output_sha256": self.output_sha256,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "metrics": dict(self.metrics) if self.metrics is not None else None,
            "failure_code": self.failure_code,
        }


def load_execution_policy(path: str | Path) -> P15CExecutionPolicy:
    selected = Path(path).expanduser()
    if selected.suffix.lower() == ".toml":
        settings = _load_owner_only_toml(selected, label="operator settings")
        source = settings.get("p15c")
        if not isinstance(source, dict):
            raise P15CControlError(
                "POLICY_SETTINGS_SECTION",
                "operator settings must contain one P15C table",
            )
    else:
        source = _load_owner_only_json(selected, label="execution policy")
    legacy_common_fields = {
        "schema_version",
        "authorization_id",
        "enabled",
        "total_budget_micro_usd",
        "expires_at_utc",
        "expected_tool_system_commit",
        "expected_tool_system_tree",
        "expected_target_packet_sha256",
        "provider_enabled",
        "provider_budget_micro_usd",
        "private_repository_transfer_enabled",
        "provider_transfer_enabled",
        "allowed_case_ids",
        "max_provider_invocations",
    }
    schema_version = source.get("schema_version")
    single_provider_fields = {
        "schema_version",
        "authorization_id",
        "enabled",
        "total_budget_micro_usd",
        "expires_at_utc",
        "expected_tool_system_commit",
        "expected_tool_system_tree",
        "provider_priority",
        "provider_model",
        "provider_enabled",
        "provider_budget_micro_usd",
        "private_repository_transfer_enabled",
        "provider_transfer_enabled",
        "allowed_case_ids",
        "max_provider_invocations",
        "cny_to_micro_usd_ceiling",
    }
    if schema_version == P15C_POLICY_SCHEMA_VERSION:
        expected_fields = single_provider_fields | {
            "transport_mode",
            "proxy_host",
            "proxy_port",
        }
    elif schema_version == P15C_SINGLE_PROVIDER_POLICY_SCHEMA_VERSION:
        expected_fields = single_provider_fields
    elif schema_version == P15C_MATRIX_POLICY_SCHEMA_VERSION:
        expected_fields = legacy_common_fields | {"cny_to_micro_usd_ceiling"}
    elif schema_version == P15C_LEGACY_POLICY_SCHEMA_VERSION:
        expected_fields = legacy_common_fields
    else:
        raise P15CControlError("POLICY_SCHEMA", "execution policy schema is invalid")
    _require_exact_fields(source, expected_fields, "execution policy")
    if source["authorization_id"] != P15C_AUTHORIZATION_ID:
        raise P15CControlError(
            "POLICY_AUTHORIZATION",
            "execution policy authorization does not match P15C",
        )
    _require_bool(source["enabled"], "enabled")
    _require_bool(
        source["private_repository_transfer_enabled"],
        "private_repository_transfer_enabled",
    )
    budget = _require_int(
        source["total_budget_micro_usd"],
        "total_budget_micro_usd",
        minimum=0,
    )
    if source["enabled"] is True and budget == 0:
        raise P15CControlError(
            "POLICY_BUDGET_REQUIRED",
            "enabled execution policy requires a positive total budget",
        )
    if budget > P15C_PUBLIC_BUDGET_CEILING_MICRO_USD:
        raise P15CControlError(
            "POLICY_BUDGET_ABOVE_AUTHORIZATION",
            "execution policy budget exceeds the public P15C ceiling",
        )
    if schema_version in {
        P15C_POLICY_SCHEMA_VERSION,
        P15C_SINGLE_PROVIDER_POLICY_SCHEMA_VERSION,
        P15C_MATRIX_POLICY_SCHEMA_VERSION,
    }:
        cny_to_micro_usd_ceiling = _require_int(
            source["cny_to_micro_usd_ceiling"],
            "cny_to_micro_usd_ceiling",
            minimum=P15C_MIN_CNY_TO_MICRO_USD_CEILING,
        )
        if cny_to_micro_usd_ceiling > P15C_MAX_CNY_TO_MICRO_USD_CEILING:
            raise P15CControlError(
                "POLICY_CURRENCY_CEILING",
                "CNY accounting ceiling exceeds its fail-closed bound",
            )
    else:
        cny_to_micro_usd_ceiling = P15C_MIN_CNY_TO_MICRO_USD_CEILING
    expires_at = source["expires_at_utc"]
    if not isinstance(expires_at, str):
        raise P15CControlError("POLICY_EXPIRY", "execution policy expiry is invalid")
    _parse_utc(expires_at)
    commit = _require_sha(source["expected_tool_system_commit"], "commit")
    tree = _require_sha(source["expected_tool_system_tree"], "tree")
    is_single_provider_policy = schema_version in {
        P15C_POLICY_SCHEMA_VERSION,
        P15C_SINGLE_PROVIDER_POLICY_SCHEMA_VERSION,
    }
    target_packet_sha256 = (
        None
        if is_single_provider_policy
        else _require_sha256(source["expected_target_packet_sha256"], "target packet")
    )
    provider_enabled = _provider_bool_mapping(
        source["provider_enabled"], "provider_enabled"
    )
    provider_transfer = _provider_bool_mapping(
        source["provider_transfer_enabled"], "provider_transfer_enabled"
    )
    provider_budgets = _provider_int_mapping(source["provider_budget_micro_usd"])
    if is_single_provider_policy:
        provider_priority = _provider_priority(source["provider_priority"])
        provider_model = _provider_model_mapping(source["provider_model"])
        if source["private_repository_transfer_enabled"] is not False:
            raise P15CControlError(
                "PRIVATE_TRANSFER_NOT_ALLOWED",
                "single-provider backup smoke must not enable private transfer",
            )
        if source["enabled"] is True:
            enabled_in_priority = tuple(
                provider
                for provider in provider_priority
                if provider_enabled[provider] is True
            )
            if not enabled_in_priority:
                raise P15CControlError(
                    "NO_ENABLED_PROVIDER",
                    "enabled API mode requires an enabled prioritized provider",
                )
            if any(
                enabled and provider not in provider_priority
                for provider, enabled in provider_enabled.items()
            ):
                raise P15CControlError(
                    "ENABLED_PROVIDER_NOT_PRIORITIZED",
                    "each enabled provider must appear in provider priority",
                )
            if any(not provider_model[provider] for provider in enabled_in_priority):
                raise P15CControlError(
                    "PROVIDER_MODEL_REQUIRED",
                    "each enabled prioritized provider requires a model",
                )
    else:
        provider_priority = tuple(
            provider for provider in P15C_PROVIDER_IDS if provider_enabled[provider]
        )
        provider_model = {provider: "" for provider in P15C_PROVIDER_IDS}
    if schema_version == P15C_LEGACY_POLICY_SCHEMA_VERSION and (
        provider_enabled["qwen"] is not False
        or provider_transfer["qwen"] is not False
        or provider_budgets["qwen"] != 0
    ):
        raise P15CControlError(
            "LEGACY_QWEN_NOT_DISABLED",
            "legacy execution policy must keep Qwen disabled",
        )
    if any(value > budget for value in provider_budgets.values()):
        raise P15CControlError(
            "PROVIDER_BUDGET_ABOVE_TOTAL",
            "provider budget exceeds total policy budget",
        )
    if schema_version == P15C_POLICY_SCHEMA_VERSION:
        transport_mode = source["transport_mode"]
        proxy_host = source["proxy_host"]
        proxy_port = source["proxy_port"]
        if transport_mode not in {"direct_tls", "http_connect"}:
            raise P15CControlError(
                "TRANSPORT_MODE",
                "transport mode must be direct_tls or http_connect",
            )
        if transport_mode == "direct_tls":
            if proxy_host != "" or proxy_port != 0:
                raise P15CControlError(
                    "PROXY_CONFIGURATION",
                    "direct TLS must not configure a proxy endpoint",
                )
            private_proxy_host = None
            private_proxy_port = None
        else:
            if proxy_host not in {"127.0.0.1", "::1", "localhost"}:
                raise P15CControlError(
                    "PROXY_HOST",
                    "HTTP CONNECT proxy must be an explicit loopback endpoint",
                )
            private_proxy_host = str(proxy_host)
            private_proxy_port = _require_int(proxy_port, "proxy_port", minimum=1)
            if private_proxy_port > 65535:
                raise P15CControlError(
                    "PROXY_PORT",
                    "proxy port is outside the valid range",
                )
    else:
        transport_mode = "direct_tls"
        private_proxy_host = None
        private_proxy_port = None
    cases = source["allowed_case_ids"]
    expected_cases = (
        P15C_BACKUP_SMOKE_CASE_IDS
        if is_single_provider_policy
        else P15C_CASE_IDS
    )
    if not isinstance(cases, list) or tuple(cases) != expected_cases:
        raise P15CControlError(
            "POLICY_CASE_SET",
            "execution policy must name its exact case set",
        )
    invocation_ceiling = _require_int(
        source["max_provider_invocations"],
        "max_provider_invocations",
        minimum=1,
    )
    invocation_limit = (
        len(P15C_PROVIDER_IDS)
        if is_single_provider_policy
        else P15C_MAX_PROVIDER_INVOCATIONS
    )
    if invocation_ceiling > invocation_limit:
        raise P15CControlError(
            "POLICY_INVOCATION_CEILING",
            "execution policy invocation ceiling exceeds P15C",
        )
    audit_source = dict(source)
    if schema_version == P15C_POLICY_SCHEMA_VERSION:
        audit_source["proxy_host"] = "<private>" if private_proxy_host else ""
        audit_source["proxy_port"] = 0
    canonical = _canonical_json(audit_source)
    return P15CExecutionPolicy(
        schema_version=int(schema_version),
        authorization_id=P15C_AUTHORIZATION_ID,
        enabled=source["enabled"],
        total_budget_micro_usd=budget,
        expires_at_utc=expires_at,
        expected_tool_system_commit=commit,
        expected_tool_system_tree=tree,
        expected_target_packet_sha256=target_packet_sha256,
        provider_priority=provider_priority,
        provider_model=provider_model,
        provider_enabled=provider_enabled,
        provider_budget_micro_usd=provider_budgets,
        private_repository_transfer_enabled=source[
            "private_repository_transfer_enabled"
        ],
        provider_transfer_enabled=provider_transfer,
        cny_to_micro_usd_ceiling=cny_to_micro_usd_ceiling,
        allowed_case_ids=tuple(cases),
        max_provider_invocations=invocation_ceiling,
        transport_mode=transport_mode,
        proxy_host=private_proxy_host,
        proxy_port=private_proxy_port,
        policy_sha256=hashlib.sha256(canonical).hexdigest(),
    )


def load_target_packet(path: str | Path) -> P15CTargetPacket:
    source = _load_owner_only_json(path, label="target packet")
    expected_fields = {
        "schema_version",
        "packet_id",
        "repository_identity",
        "visibility",
        "branch",
        "exact_commit",
        "exact_file_allowlist",
        "content_addressed_inventory",
        "durable_module_contract",
        "inventory_read_authority",
        "benchmark_read_authority",
        "provider_transfer_authority_by_provider",
        "mutation_authority",
        "snapshot_root",
    }
    _require_exact_fields(source, expected_fields, "target packet")
    if source["schema_version"] != P15C_TARGET_PACKET_SCHEMA_VERSION:
        raise P15CControlError("TARGET_SCHEMA", "target packet schema is invalid")
    packet_id = source["packet_id"]
    if not isinstance(packet_id, str) or _PACKET_ID_RE.fullmatch(packet_id) is None:
        raise P15CControlError("TARGET_PACKET_ID", "target packet ID is invalid")
    repository_identity = source["repository_identity"]
    if (
        not isinstance(repository_identity, str)
        or _REPOSITORY_ID_RE.fullmatch(repository_identity) is None
    ):
        raise P15CControlError(
            "TARGET_REPOSITORY_IDENTITY",
            "target repository identity is invalid",
        )
    visibility = source["visibility"]
    if visibility not in {"public", "private"}:
        raise P15CControlError("TARGET_VISIBILITY", "target visibility is invalid")
    branch = source["branch"]
    if not isinstance(branch, str) or _PACKET_ID_RE.fullmatch(branch) is None:
        raise P15CControlError("TARGET_BRANCH", "target branch is invalid")
    exact_commit = _require_sha(source["exact_commit"], "target commit")
    allowlist = source["exact_file_allowlist"]
    if not isinstance(allowlist, list) or not allowlist:
        raise P15CControlError("TARGET_ALLOWLIST", "target allowlist is empty")
    if len(allowlist) > P15C_MAX_TARGET_FILES or len(allowlist) != len(set(allowlist)):
        raise P15CControlError(
            "TARGET_ALLOWLIST",
            "target allowlist is duplicated or exceeds its ceiling",
        )
    normalized_allowlist = tuple(_validate_target_path(item) for item in allowlist)
    if tuple(sorted(normalized_allowlist)) != normalized_allowlist:
        raise P15CControlError(
            "TARGET_ALLOWLIST_ORDER",
            "target allowlist must be sorted",
        )
    raw_inventory = source["content_addressed_inventory"]
    if not isinstance(raw_inventory, list) or len(raw_inventory) != len(allowlist):
        raise P15CControlError(
            "TARGET_INVENTORY",
            "target inventory must match the allowlist",
        )
    inventory: list[P15CTargetInventoryItem] = []
    for raw in raw_inventory:
        if not isinstance(raw, dict):
            raise P15CControlError("TARGET_INVENTORY", "target inventory is invalid")
        _require_exact_fields(
            raw,
            {"path", "sha256", "git_blob_sha", "size_bytes"},
            "target inventory item",
        )
        item_path = _validate_target_path(raw["path"])
        digest = raw["sha256"]
        blob = raw["git_blob_sha"]
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise P15CControlError("TARGET_DIGEST", "target SHA-256 is invalid")
        if not isinstance(blob, str) or _SHA_RE.fullmatch(blob) is None:
            raise P15CControlError("TARGET_BLOB", "target Git blob SHA is invalid")
        size = _require_int(raw["size_bytes"], "target size", minimum=1)
        if size > P15C_MAX_TARGET_FILE_BYTES:
            raise P15CControlError(
                "TARGET_FILE_TOO_LARGE",
                "target file exceeds the byte ceiling",
            )
        inventory.append(P15CTargetInventoryItem(item_path, digest, blob, size))
    if tuple(item.path for item in inventory) != normalized_allowlist:
        raise P15CControlError(
            "TARGET_INVENTORY_ORDER",
            "target inventory paths must equal the sorted allowlist",
        )
    if sum(item.size_bytes for item in inventory) > P15C_MAX_TARGET_TOTAL_BYTES:
        raise P15CControlError(
            "TARGET_TOTAL_TOO_LARGE",
            "target snapshot exceeds the total byte ceiling",
        )
    durable = source["durable_module_contract"]
    if not isinstance(durable, dict):
        raise P15CControlError(
            "TARGET_MODULE_CONTRACT",
            "target durable-module contract is invalid",
        )
    _require_exact_fields(
        durable,
        {"contract_id", "contract_version", "read_only"},
        "target durable-module contract",
    )
    if durable["read_only"] is not True:
        raise P15CControlError(
            "TARGET_MODULE_CONTRACT",
            "target durable-module contract must be read-only",
        )
    for field in (
        "inventory_read_authority",
        "benchmark_read_authority",
        "mutation_authority",
    ):
        _require_bool(source[field], field)
    provider_transfer = _provider_bool_mapping(
        source["provider_transfer_authority_by_provider"],
        "provider_transfer_authority_by_provider",
    )
    snapshot_root = _owner_only_directory(source["snapshot_root"], "target snapshot")
    packet = P15CTargetPacket(
        packet_id=packet_id,
        repository_identity=repository_identity,
        visibility=visibility,
        branch=branch,
        exact_commit=exact_commit,
        exact_file_allowlist=normalized_allowlist,
        content_addressed_inventory=tuple(inventory),
        durable_module_contract=dict(durable),
        inventory_read_authority=source["inventory_read_authority"],
        benchmark_read_authority=source["benchmark_read_authority"],
        provider_transfer_authority_by_provider=provider_transfer,
        mutation_authority=source["mutation_authority"],
        snapshot_root=snapshot_root,
        packet_sha256=hashlib.sha256(_canonical_json(source)).hexdigest(),
    )
    packet.assert_read_only_authority()
    return packet


def load_target_snapshot(packet: P15CTargetPacket) -> tuple[P15CSnapshotFile, ...]:
    packet.assert_read_only_authority()
    root = _owner_only_directory(packet.snapshot_root, "target snapshot")
    loaded: list[P15CSnapshotFile] = []
    for item in packet.content_addressed_inventory:
        path = root.joinpath(*PurePosixPath(item.path).parts)
        try:
            metadata = path.lstat()
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise P15CControlError(
                "TARGET_FILE_UNAVAILABLE",
                "allowlisted target file is unavailable",
            ) from exc
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or resolved != path
            or not resolved.is_relative_to(root)
        ):
            raise P15CControlError(
                "TARGET_FILE_UNSAFE",
                "allowlisted target file is not a safe regular file",
            )
        try:
            content_bytes = path.read_bytes()
        except OSError as exc:
            raise P15CControlError(
                "TARGET_FILE_UNREADABLE",
                "allowlisted target file is unreadable",
            ) from exc
        if len(content_bytes) != item.size_bytes:
            raise P15CControlError(
                "TARGET_SIZE_DRIFT",
                "allowlisted target file size changed",
            )
        if hashlib.sha256(content_bytes).hexdigest() != item.sha256:
            raise P15CControlError(
                "TARGET_CONTENT_DRIFT",
                "allowlisted target file SHA-256 changed",
            )
        if _git_blob_sha(content_bytes) != item.git_blob_sha:
            raise P15CControlError(
                "TARGET_BLOB_DRIFT",
                "allowlisted target Git blob changed",
            )
        try:
            content = content_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise P15CControlError(
                "TARGET_NOT_UTF8",
                "allowlisted target file is not UTF-8 text",
            ) from exc
        if "\x00" in content or any(
            pattern.search(content) for pattern in _SECRET_CONTENT_PATTERNS
        ):
            raise P15CControlError(
                "TARGET_SECRET_MATERIAL",
                "allowlisted target file contains blocked material",
            )
        loaded.append(
            P15CSnapshotFile(item.path, item.sha256, item.git_blob_sha, content)
        )
    return validate_target_snapshot(packet, loaded)


def validate_target_snapshot(
    packet: P15CTargetPacket,
    snapshot: Sequence[P15CSnapshotFile],
) -> tuple[P15CSnapshotFile, ...]:
    """Revalidate an in-memory snapshot against its exact private packet."""

    packet.assert_read_only_authority()
    files = tuple(snapshot)
    if tuple(item.path for item in files) != packet.exact_file_allowlist:
        raise P15CControlError(
            "TARGET_SNAPSHOT_FILE_SET",
            "target snapshot does not match the exact allowlist",
        )
    for item, expected in zip(files, packet.content_addressed_inventory):
        content_bytes = item.content.encode("utf-8")
        if (
            item.path != expected.path
            or item.sha256 != expected.sha256
            or item.git_blob_sha != expected.git_blob_sha
            or len(content_bytes) != expected.size_bytes
            or hashlib.sha256(content_bytes).hexdigest() != expected.sha256
            or _git_blob_sha(content_bytes) != expected.git_blob_sha
        ):
            raise P15CControlError(
                "TARGET_SNAPSHOT_DRIFT",
                "target snapshot does not match its content-addressed inventory",
            )
        if "\x00" in item.content or any(
            pattern.search(item.content) for pattern in _SECRET_CONTENT_PATTERNS
        ):
            raise P15CControlError(
                "TARGET_SECRET_MATERIAL",
                "allowlisted target file contains blocked material",
            )
    return files


class OwnerOnlyCredentialResolver:
    """Resolve exact provider references without logging or retaining values."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()

    def resolve(self, reference: str, provider_id: str) -> str:
        expected = f"private-control:credentials#providers.{provider_id}.api_key"
        if provider_id not in P15C_PROVIDER_IDS or reference != expected:
            raise P15CControlError(
                "CREDENTIAL_REFERENCE_NOT_ALLOWED",
                "credential reference is not allowed",
            )
        try:
            path = _owner_only_file(self._path, "credential store")
        except P15CControlError as exc:
            if exc.code == "PRIVATE_FILE_UNAVAILABLE":
                raise P15CControlError(
                    "CREDENTIAL_UNAVAILABLE",
                    "credential reference is unavailable",
                ) from exc
            raise
        try:
            with path.open("rb") as handle:
                record = tomllib.load(handle)
            value = record["providers"][provider_id]["api_key"]
        except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
            raise P15CControlError(
                "CREDENTIAL_UNAVAILABLE",
                "credential reference is unavailable",
            ) from exc
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise P15CControlError(
                "CREDENTIAL_INVALID",
                "credential reference is invalid",
            )
        return value


class P15CUsageLedger:
    """Owner-only SQLite ledger with atomic conservative budget reservations."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()
        self._prepare_storage()
        self._initialize()

    @property
    def instance_id(self) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT instance_id FROM ledger_meta WHERE singleton = 1"
            ).fetchone()
        if row is None or not isinstance(row[0], str):
            raise P15CControlError("LEDGER_INVALID", "usage ledger identity is missing")
        return row[0]

    def reserve(
        self,
        *,
        attempt_id: str,
        provider_id: str,
        case_id: str,
        request_sha256: str,
        reservation_micro_usd: int,
        total_budget_micro_usd: int,
        provider_budget_micro_usd: int,
    ) -> None:
        if _PACKET_ID_RE.fullmatch(attempt_id) is None:
            raise P15CControlError("LEDGER_ATTEMPT_ID", "attempt ID is invalid")
        if provider_id not in P15C_PROVIDER_IDS or case_id not in P15C_CASE_IDS:
            raise P15CControlError("LEDGER_ROUTE", "ledger route is invalid")
        if _SHA256_RE.fullmatch(request_sha256) is None:
            raise P15CControlError(
                "LEDGER_REQUEST_SHA256",
                "usage-ledger request SHA-256 is invalid",
            )
        reservation = _require_int(
            reservation_micro_usd, "reservation_micro_usd", minimum=1
        )
        total_budget = _require_int(
            total_budget_micro_usd, "total_budget_micro_usd", minimum=1
        )
        provider_budget = _require_int(
            provider_budget_micro_usd, "provider_budget_micro_usd", minimum=1
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT 1 FROM attempts WHERE attempt_id = ?", (attempt_id,)
            ).fetchone()
            if existing is not None:
                raise P15CControlError(
                    "LEDGER_REPLAY",
                    "usage-ledger attempt was already recorded",
                )
            global_used = connection.execute(
                "SELECT COALESCE(SUM(CASE WHEN status IN ('RESERVED', 'IN_FLIGHT') THEN reserved_micro_usd ELSE charged_micro_usd END), 0) FROM attempts WHERE status IN ('RESERVED', 'IN_FLIGHT', 'SETTLED', 'UNCERTAIN')"
            ).fetchone()[0]
            provider_used = connection.execute(
                "SELECT COALESCE(SUM(CASE WHEN status IN ('RESERVED', 'IN_FLIGHT') THEN reserved_micro_usd ELSE charged_micro_usd END), 0) FROM attempts WHERE provider_id = ? AND status IN ('RESERVED', 'IN_FLIGHT', 'SETTLED', 'UNCERTAIN')",
                (provider_id,),
            ).fetchone()[0]
            if global_used + reservation > total_budget:
                raise P15CControlError(
                    "LEDGER_TOTAL_BUDGET",
                    "usage-ledger total budget is exhausted",
                )
            if provider_used + reservation > provider_budget:
                raise P15CControlError(
                    "LEDGER_PROVIDER_BUDGET",
                    "usage-ledger provider budget is exhausted",
                )
            connection.execute(
                "INSERT INTO attempts (attempt_id, provider_id, case_id, reserved_micro_usd, charged_micro_usd, status, request_sha256) VALUES (?, ?, ?, ?, 0, 'RESERVED', ?)",
                (attempt_id, provider_id, case_id, reservation, request_sha256),
            )
            connection.commit()

    def mark_transport_started(self, attempt_id: str) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE attempts SET status = 'IN_FLIGHT' WHERE attempt_id = ? AND status = 'RESERVED'",
                (attempt_id,),
            ).rowcount
            if changed != 1:
                raise P15CControlError(
                    "LEDGER_TRANSPORT_STATE",
                    "usage-ledger attempt is not reserved",
                )
            connection.commit()

    def settle(
        self,
        attempt_id: str,
        *,
        charged_micro_usd: int,
        output_sha256: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        metrics: Mapping[str, object],
    ) -> None:
        charged = _require_int(charged_micro_usd, "charged_micro_usd", minimum=0)
        if _SHA256_RE.fullmatch(output_sha256) is None:
            raise P15CControlError(
                "LEDGER_OUTPUT_SHA256",
                "usage-ledger output SHA-256 is invalid",
            )
        input_count = _require_int(input_tokens, "input_tokens", minimum=0)
        output_count = _require_int(output_tokens, "output_tokens", minimum=0)
        duration = _require_int(duration_ms, "duration_ms", minimum=0)
        try:
            metrics_json = _canonical_json(dict(metrics)).decode("utf-8")
        except (TypeError, ValueError) as exc:
            raise P15CControlError(
                "LEDGER_METRICS",
                "usage-ledger metrics are invalid",
            ) from exc
        if len(metrics_json.encode("utf-8")) > 16_384:
            raise P15CControlError(
                "LEDGER_METRICS",
                "usage-ledger metrics exceed their byte ceiling",
            )
        if any(
            blocked in metrics_json.lower()
            for blocked in ("repository_identity", "exact_file_allowlist", "content")
        ):
            raise P15CControlError(
                "LEDGER_METRICS_PRIVATE_DATA",
                "usage-ledger metrics contain private-data keys",
            )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT reserved_micro_usd, status FROM attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if row is None or row[1] != "IN_FLIGHT":
                raise P15CControlError(
                    "LEDGER_SETTLEMENT_STATE",
                    "usage-ledger attempt is not in flight",
                )
            if charged > row[0]:
                raise P15CControlError(
                    "LEDGER_SETTLEMENT_ABOVE_RESERVATION",
                    "usage-ledger charge exceeds its reservation",
                )
            connection.execute(
                "UPDATE attempts SET charged_micro_usd = ?, status = 'SETTLED', output_sha256 = ?, input_tokens = ?, output_tokens = ?, duration_ms = ?, metrics_json = ? WHERE attempt_id = ?",
                (
                    charged,
                    output_sha256,
                    input_count,
                    output_count,
                    duration,
                    metrics_json,
                    attempt_id,
                ),
            )
            connection.commit()

    def record_transport_failure(self, attempt_id: str, failure_code: str) -> None:
        if (
            not isinstance(failure_code, str)
            or _PACKET_ID_RE.fullmatch(failure_code) is None
        ):
            raise P15CControlError(
                "LEDGER_FAILURE_CODE",
                "usage-ledger failure code is invalid",
            )
        self._finish_failed(
            attempt_id,
            status="UNCERTAIN",
            charge_reservation=True,
            failure_code=failure_code,
        )

    def release_without_transport(self, attempt_id: str) -> None:
        self._finish_failed(
            attempt_id,
            status="RELEASED",
            charge_reservation=False,
            failure_code="PRETRANSPORT_RELEASE",
        )

    def mark_transport_cost_uncertain(self, attempt_id: str) -> None:
        self._finish_failed(
            attempt_id,
            status="UNCERTAIN",
            charge_reservation=True,
            failure_code="TRANSPORT_COST_UNCERTAIN",
        )

    def attempt(self, attempt_id: str) -> P15CLedgerAttempt | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT attempt_id, provider_id, case_id, status, reserved_micro_usd, charged_micro_usd, request_sha256, output_sha256, input_tokens, output_tokens, duration_ms, metrics_json, failure_code FROM attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _ledger_attempt_from_row(row) if row is not None else None

    def attempts(self) -> tuple[P15CLedgerAttempt, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT attempt_id, provider_id, case_id, status, reserved_micro_usd, charged_micro_usd, request_sha256, output_sha256, input_tokens, output_tokens, duration_ms, metrics_json, failure_code FROM attempts ORDER BY provider_id, case_id, attempt_id"
            ).fetchall()
        return tuple(_ledger_attempt_from_row(row) for row in rows)

    def summary(self) -> dict[str, object]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT provider_id, status, COUNT(*), SUM(charged_micro_usd), SUM(reserved_micro_usd) FROM attempts GROUP BY provider_id, status ORDER BY provider_id, status"
            ).fetchall()
        return {
            "ledger_instance_id": self.instance_id,
            "rows": [
                {
                    "provider_id": row[0],
                    "status": row[1],
                    "attempt_count": row[2],
                    "charged_micro_usd": row[3] or 0,
                    "reserved_micro_usd": row[4] or 0,
                }
                for row in rows
            ],
        }

    def _finish_failed(
        self,
        attempt_id: str,
        *,
        status: str,
        charge_reservation: bool,
        failure_code: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT reserved_micro_usd, status FROM attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            allowed_status = "IN_FLIGHT" if charge_reservation else "RESERVED"
            if row is None or row[1] != allowed_status:
                raise P15CControlError(
                    "LEDGER_FAILURE_STATE",
                    "usage-ledger attempt is not reserved",
                )
            charged = row[0] if charge_reservation else 0
            connection.execute(
                "UPDATE attempts SET charged_micro_usd = ?, status = ?, failure_code = ? WHERE attempt_id = ?",
                (charged, status, failure_code, attempt_id),
            )
            connection.commit()

    def _prepare_storage(self) -> None:
        parent = _owner_only_directory(self._path.parent, "usage-ledger parent")
        candidate = parent / self._path.name
        if candidate.exists() or candidate.is_symlink():
            _owner_only_file(candidate, "usage ledger")
            self._path = candidate
            return
        try:
            descriptor = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except OSError as exc:
            raise P15CControlError(
                "LEDGER_CREATE_FAILED",
                "usage ledger could not be created",
            ) from exc
        self._path = _owner_only_file(candidate, "usage ledger")

    def _connect(self) -> sqlite3.Connection:
        _owner_only_file(self._path, "usage ledger")
        connection = sqlite3.connect(self._path, timeout=5.0, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS ledger_meta (singleton INTEGER PRIMARY KEY CHECK (singleton = 1), schema_version INTEGER NOT NULL, instance_id TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS attempts (attempt_id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, case_id TEXT NOT NULL, reserved_micro_usd INTEGER NOT NULL, charged_micro_usd INTEGER NOT NULL, status TEXT NOT NULL CHECK (status IN ('RESERVED', 'IN_FLIGHT', 'SETTLED', 'RELEASED', 'UNCERTAIN')), request_sha256 TEXT NOT NULL, output_sha256 TEXT, input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, duration_ms INTEGER NOT NULL DEFAULT 0, metrics_json TEXT, failure_code TEXT)"
            )
            meta_columns = tuple(
                row[1] for row in connection.execute("PRAGMA table_info(ledger_meta)")
            )
            attempt_columns = tuple(
                row[1] for row in connection.execute("PRAGMA table_info(attempts)")
            )
            if meta_columns != ("singleton", "schema_version", "instance_id") or (
                attempt_columns
                != (
                    "attempt_id",
                    "provider_id",
                    "case_id",
                    "reserved_micro_usd",
                    "charged_micro_usd",
                    "status",
                    "request_sha256",
                    "output_sha256",
                    "input_tokens",
                    "output_tokens",
                    "duration_ms",
                    "metrics_json",
                    "failure_code",
                )
            ):
                raise P15CControlError(
                    "LEDGER_SCHEMA",
                    "usage ledger schema does not match P15C",
                )
            row = connection.execute(
                "SELECT schema_version FROM ledger_meta WHERE singleton = 1"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO ledger_meta (singleton, schema_version, instance_id) VALUES (1, ?, ?)",
                    (P15C_LEDGER_SCHEMA_VERSION, secrets.token_hex(32)),
                )
            elif row[0] != P15C_LEDGER_SCHEMA_VERSION:
                raise P15CControlError(
                    "LEDGER_SCHEMA",
                    "usage ledger schema does not match P15C",
                )
            connection.commit()
        os.chmod(self._path, 0o600)


def _ledger_attempt_from_row(row: Sequence[object]) -> P15CLedgerAttempt:
    metrics: Mapping[str, object] | None = None
    if row[11] is not None:
        try:
            decoded = json.loads(str(row[11]), object_pairs_hook=_reject_duplicate_keys)
        except (ValueError, json.JSONDecodeError) as exc:
            raise P15CControlError(
                "LEDGER_INVALID",
                "usage-ledger metrics are invalid",
            ) from exc
        if not isinstance(decoded, dict):
            raise P15CControlError(
                "LEDGER_INVALID",
                "usage-ledger metrics must be an object",
            )
        metrics = decoded
    return P15CLedgerAttempt(
        attempt_id=str(row[0]),
        provider_id=str(row[1]),
        case_id=str(row[2]),
        status=str(row[3]),
        reserved_micro_usd=int(row[4]),
        charged_micro_usd=int(row[5]),
        request_sha256=str(row[6]),
        output_sha256=str(row[7]) if row[7] is not None else None,
        input_tokens=int(row[8]),
        output_tokens=int(row[9]),
        duration_ms=int(row[10]),
        metrics=metrics,
        failure_code=str(row[12]) if row[12] is not None else None,
    )


def build_execution_source_seal(
    repository_root: str | Path,
    *,
    expected_commit_sha: str,
    expected_tree_sha: str,
    critical_source_paths: Sequence[str],
) -> P15CExecutionSourceSeal:
    root = Path(repository_root)
    if root.is_symlink():
        raise P15CControlError("SOURCE_ROOT", "execution source root is a symlink")
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise P15CControlError(
            "SOURCE_ROOT", "execution source root is unavailable"
        ) from exc
    if _git_output(root, "rev-parse", "--show-toplevel") != str(root):
        raise P15CControlError("SOURCE_ROOT", "execution source is not the Git root")
    if _git_output(root, "remote", "get-url", "origin") not in P15C_CANONICAL_REMOTES:
        raise P15CControlError(
            "SOURCE_REMOTE", "execution source remote is not canonical"
        )
    local_head = _require_sha(_git_output(root, "rev-parse", "HEAD"), "local head")
    local_tree = _require_sha(
        _git_output(root, "rev-parse", "HEAD^{tree}"), "local tree"
    )
    expected_commit = _require_sha(expected_commit_sha, "canonical commit")
    expected_tree = _require_sha(expected_tree_sha, "canonical tree")
    if local_tree != expected_tree:
        raise P15CControlError(
            "SOURCE_TREE_DRIFT",
            "execution source tree does not match canonical main",
        )
    if _git_output(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise P15CControlError("SOURCE_DIRTY", "execution source worktree is not clean")
    entries: list[dict[str, str]] = []
    for relative in critical_source_paths:
        safe = _validate_repository_relative_path(relative)
        path = root.joinpath(*PurePosixPath(safe).parts)
        try:
            metadata = path.lstat()
            resolved = path.resolve(strict=True)
            content = path.read_bytes()
        except OSError as exc:
            raise P15CControlError(
                "SOURCE_FILE_UNAVAILABLE",
                "critical source file is unavailable",
            ) from exc
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or resolved != path
            or not resolved.is_relative_to(root)
        ):
            raise P15CControlError(
                "SOURCE_FILE_UNSAFE",
                "critical source file is unsafe",
            )
        entries.append({"path": safe, "sha256": hashlib.sha256(content).hexdigest()})
    manifest = _canonical_json({"version": 1, "files": entries})
    return P15CExecutionSourceSeal(
        canonical_commit_sha=expected_commit,
        canonical_tree_sha=expected_tree,
        local_head_sha=local_head,
        local_tree_sha=local_tree,
        clean_worktree=True,
        source_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
    )


def _load_owner_only_json(path: str | Path, *, label: str) -> dict[str, Any]:
    resolved = _owner_only_file(path, label)
    try:
        payload = resolved.read_text(encoding="utf-8", errors="strict")
        value = json.loads(payload, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P15CControlError(
            "PRIVATE_CONTROL_INVALID",
            f"{label} is unavailable or invalid",
        ) from exc
    if not isinstance(value, dict):
        raise P15CControlError("PRIVATE_CONTROL_INVALID", f"{label} must be an object")
    return value


def _load_owner_only_toml(path: str | Path, *, label: str) -> dict[str, Any]:
    resolved = _owner_only_file(path, label)
    try:
        with resolved.open("rb") as handle:
            value = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise P15CControlError(
            "PRIVATE_CONTROL_INVALID",
            f"{label} is unavailable or invalid",
        ) from exc
    if not isinstance(value, dict):
        raise P15CControlError(
            "PRIVATE_CONTROL_INVALID",
            f"{label} must be a table",
        )
    return value


def _owner_only_file(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    try:
        metadata = candidate.lstat()
        parent = candidate.parent.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise P15CControlError(
            "PRIVATE_FILE_UNAVAILABLE", f"{label} is unavailable"
        ) from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o077
        or resolved != candidate.absolute()
    ):
        raise P15CControlError(
            "PRIVATE_FILE_PERMISSIONS",
            f"{label} must be an owner-only regular file",
        )
    if (
        stat.S_ISLNK(parent.st_mode)
        or not stat.S_ISDIR(parent.st_mode)
        or parent.st_uid != os.getuid()
        or parent.st_mode & 0o077
    ):
        raise P15CControlError(
            "PRIVATE_DIRECTORY_PERMISSIONS",
            f"{label} parent must be owner-only",
        )
    return resolved


def _owner_only_directory(path: object, label: str) -> Path:
    if not isinstance(path, (str, Path)):
        raise P15CControlError("PRIVATE_DIRECTORY", f"{label} path is invalid")
    candidate = Path(path).expanduser()
    try:
        metadata = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise P15CControlError("PRIVATE_DIRECTORY", f"{label} is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o077
        or resolved != candidate.absolute()
    ):
        raise P15CControlError(
            "PRIVATE_DIRECTORY_PERMISSIONS",
            f"{label} must be an owner-only directory",
        )
    return resolved


def _provider_bool_mapping(value: object, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != set(P15C_PROVIDER_IDS):
        raise P15CControlError("PROVIDER_MAPPING", f"{label} provider set is invalid")
    result: dict[str, bool] = {}
    for provider in P15C_PROVIDER_IDS:
        _require_bool(value[provider], f"{label}.{provider}")
        result[provider] = value[provider]
    return result


def _provider_int_mapping(value: object) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(P15C_PROVIDER_IDS):
        raise P15CControlError(
            "PROVIDER_BUDGET_MAPPING",
            "provider budget provider set is invalid",
        )
    return {
        provider: _require_int(
            value[provider], f"provider_budget_micro_usd.{provider}", minimum=0
        )
        for provider in P15C_PROVIDER_IDS
    }


def _provider_priority(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or any(not isinstance(provider, str) for provider in value)
        or len(value) != len(set(value))
        or any(provider not in P15C_PROVIDER_IDS for provider in value)
    ):
        raise P15CControlError(
            "PROVIDER_PRIORITY",
            "provider priority must be an ordered unique supported-provider subset",
        )
    return tuple(value)


def _provider_model_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(P15C_PROVIDER_IDS):
        raise P15CControlError(
            "PROVIDER_MODEL_MAPPING",
            "provider model provider set is invalid",
        )
    result: dict[str, str] = {}
    for provider in P15C_PROVIDER_IDS:
        model = value[provider]
        if (
            not isinstance(model, str)
            or len(model.encode("utf-8")) > 128
            or (model and (_MODEL_ID_RE.fullmatch(model) is None))
        ):
            raise P15CControlError(
                "PROVIDER_MODEL",
                f"provider_model.{provider} is invalid",
            )
        result[provider] = model
    return result


def _validate_target_path(value: object) -> str:
    path = _validate_repository_relative_path(value)
    pure = PurePosixPath(path)
    lowered = {part.lower() for part in pure.parts}
    if lowered & _FORBIDDEN_PATH_PARTS or pure.suffix.lower() in _FORBIDDEN_SUFFIXES:
        raise P15CControlError("TARGET_PATH_BLOCKED", "target path is blocked")
    return path


def _validate_repository_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 512:
        raise P15CControlError("PATH_INVALID", "repository-relative path is invalid")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or str(pure) != value
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise P15CControlError("PATH_INVALID", "repository-relative path is invalid")
    return value


def _require_exact_fields(
    value: Mapping[str, object], fields: set[str], label: str
) -> None:
    if set(value) != fields:
        raise P15CControlError("EXACT_FIELDS", f"{label} fields are invalid")


def _require_bool(value: object, label: str) -> None:
    if type(value) is not bool:
        raise P15CControlError("BOOLEAN_FIELD", f"{label} must be boolean")


def _require_int(value: object, label: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise P15CControlError("INTEGER_FIELD", f"{label} must be an integer")
    return value


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise P15CControlError("SHA_FIELD", f"{label} must be a Git SHA")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise P15CControlError("SHA256_FIELD", f"{label} must be a SHA-256")
    return value


def _parse_utc(value: str) -> datetime:
    if _UTC_RE.fullmatch(value) is None:
        raise P15CControlError("UTC_FIELD", "UTC timestamp is invalid")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise P15CControlError("UTC_FIELD", "UTC timestamp is invalid") from exc


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _git_output(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            (
                "git",
                "-c",
                "core.quotepath=false",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.hooksPath=/dev/null",
                *arguments,
            ),
            cwd=root,
            env={
                "PATH": os.defpath,
                "LANG": "C",
                "LC_ALL": "C",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
            },
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise P15CControlError(
            "SOURCE_GIT", "execution source Git evidence failed"
        ) from exc
    if result.returncode != 0:
        raise P15CControlError("SOURCE_GIT", "execution source Git evidence is invalid")
    try:
        return result.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise P15CControlError(
            "SOURCE_GIT", "execution source Git output is invalid"
        ) from exc
