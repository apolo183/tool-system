from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import socket
import ssl
import stat
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_system.orchestrator import (
    AuthorizationReplay,
    DurableOrchestratorStore,
    StateConflict,
)

P14C_APPROVAL_VERSION = "p14c-live-execution-approval-v2"
P14C_LIVE_EXECUTION_AUTHORIZATION_ID = "P14C-LIVE-EXEC-v2"
P14C_APPROVAL_REPOSITORY = "apolo183/tool-system"
P14C_APPROVAL_OWNER = "apolo183"
P14C_APPROVAL_ACTION = "p14c_live_provider_execution"
P14C_LIVE_TRANSPORT_KIND = "live_network"
GITHUB_API_HOST = "api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_RESPONSE_LIMIT_BYTES = 65_536
P14C_APPROVAL_BODY_LIMIT_BYTES = 16_384
P14C_APPROVAL_MAX_TTL_SECONDS = 900
P14C_APPROVAL_CLOCK_SKEW_SECONDS = 30
P14C_SOURCE_MANIFEST_VERSION = "p14c-critical-runtime-source-v2"
P14C_CRITICAL_SOURCE_PATHS = (
    "src/tool_system/ai_worker/live_provider.py",
    "src/tool_system/orchestrator/__init__.py",
    "src/tool_system/orchestrator/durable.py",
    "src/tool_system/process_authority/__init__.py",
    "src/tool_system/process_authority/live_provider_approval.py",
    "src/tool_system/ai_worker/live_evidence.py",
)
_P14C_CRITICAL_SOURCE_MODULES = {
    "src/tool_system/ai_worker/live_provider.py": (
        "tool_system.ai_worker.live_provider"
    ),
    "src/tool_system/orchestrator/__init__.py": "tool_system.orchestrator",
    "src/tool_system/orchestrator/durable.py": "tool_system.orchestrator.durable",
    "src/tool_system/process_authority/__init__.py": (
        "tool_system.process_authority"
    ),
    "src/tool_system/process_authority/live_provider_approval.py": __name__,
    "src/tool_system/ai_worker/live_evidence.py": (
        "tool_system.ai_worker.live_evidence"
    ),
}

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_NONCE_RE = re.compile(r"^[0-9a-f]{64}$")
_HOST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ISSUE_URL_RE = re.compile(
    r"^https://api\.github\.com/repos/apolo183/tool-system/issues/([1-9][0-9]*)$"
)
_GRANT_ISSUER = object()
_CANONICAL_TOOL_SYSTEM_REMOTES = {
    "git@github.com:apolo183/tool-system.git",
    "https://github.com/apolo183/tool-system.git",
}


class P14CLiveExecutionAuthorizationError(RuntimeError):
    """Raised when external P14C live-execution authority is absent or invalid."""


class GitHubApprovalReadError(P14CLiveExecutionAuthorizationError):
    """Raised when the pinned public GitHub approval record cannot be read."""


def open_p14c_live_execution_ledger(
    database_path: str | Path,
    *,
    repository_root: str | Path,
) -> DurableOrchestratorStore:
    """Open the hardened single-host ledger outside the execution checkout."""

    root = Path(repository_root).resolve(strict=True)
    return DurableOrchestratorStore(
        database_path,
        forbidden_roots=(root,),
    )


@dataclass(frozen=True)
class P14CExecutionSourceSeal:
    repository: str
    execution_commit_sha: str
    execution_tree_sha: str
    source_manifest_sha256: str
    clean_worktree: bool
    execution_host_id: str
    replay_ledger_instance_id: str

    def canonical_record(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "execution_commit_sha": self.execution_commit_sha,
            "execution_tree_sha": self.execution_tree_sha,
            "source_manifest_sha256": self.source_manifest_sha256,
            "clean_worktree": self.clean_worktree,
            "execution_host_id": self.execution_host_id,
            "replay_ledger_instance_id": self.replay_ledger_instance_id,
        }

    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json_bytes(self.canonical_record())).hexdigest()


@dataclass(frozen=True)
class P14CLiveExecutionBinding:
    authorization_id: str
    repository: str
    action: str
    implementation_authorization_base_sha: str
    execution_commit_sha: str
    execution_tree_sha: str
    source_manifest_sha256: str
    clean_worktree: bool
    execution_host_id: str
    replay_ledger_instance_id: str
    packet_sha256: str
    request_sha256: str
    fixture_id: str
    provider_id: str
    model_id: str
    method: str
    host: str
    path: str
    credential_reference: str
    transport_kind: str
    provider_invocation_ceiling: int
    max_attempts: int
    cumulative_token_ceiling: int
    request_timeout_ms: int
    total_wall_clock_ms: int
    cumulative_cost_microusd: int
    target_repo_mutation_authorized: bool
    production_deployment_authorized: bool
    cleanup_execution_authorized: bool
    p14d_authorized: bool

    def canonical_record(self) -> dict[str, object]:
        return {
            "authorization_id": self.authorization_id,
            "repository": self.repository,
            "action": self.action,
            "implementation_authorization_base_sha": (
                self.implementation_authorization_base_sha
            ),
            "execution_commit_sha": self.execution_commit_sha,
            "execution_tree_sha": self.execution_tree_sha,
            "source_manifest_sha256": self.source_manifest_sha256,
            "clean_worktree": self.clean_worktree,
            "execution_host_id": self.execution_host_id,
            "replay_ledger_instance_id": self.replay_ledger_instance_id,
            "packet_sha256": self.packet_sha256,
            "request_sha256": self.request_sha256,
            "fixture_id": self.fixture_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "method": self.method,
            "host": self.host,
            "path": self.path,
            "credential_reference": self.credential_reference,
            "transport_kind": self.transport_kind,
            "provider_invocation_ceiling": self.provider_invocation_ceiling,
            "max_attempts": self.max_attempts,
            "cumulative_token_ceiling": self.cumulative_token_ceiling,
            "request_timeout_ms": self.request_timeout_ms,
            "total_wall_clock_ms": self.total_wall_clock_ms,
            "cumulative_cost_microusd": self.cumulative_cost_microusd,
            "target_repo_mutation_authorized": (
                self.target_repo_mutation_authorized
            ),
            "production_deployment_authorized": (
                self.production_deployment_authorized
            ),
            "cleanup_execution_authorized": self.cleanup_execution_authorized,
            "p14d_authorized": self.p14d_authorized,
        }

    def source_seal(self) -> P14CExecutionSourceSeal:
        return P14CExecutionSourceSeal(
            repository=self.repository,
            execution_commit_sha=self.execution_commit_sha,
            execution_tree_sha=self.execution_tree_sha,
            source_manifest_sha256=self.source_manifest_sha256,
            clean_worktree=self.clean_worktree,
            execution_host_id=self.execution_host_id,
            replay_ledger_instance_id=self.replay_ledger_instance_id,
        )

    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json_bytes(self.canonical_record())).hexdigest()


@dataclass(frozen=True)
class P14CLiveExecutionApproval:
    approval_version: str
    authorization_id: str
    repository: str
    action: str
    implementation_authorization_base_sha: str
    execution_commit_sha: str
    execution_tree_sha: str
    source_manifest_sha256: str
    clean_worktree: bool
    execution_host_id: str
    replay_ledger_instance_id: str
    packet_sha256: str
    request_sha256: str
    fixture_id: str
    provider_id: str
    model_id: str
    method: str
    host: str
    path: str
    credential_reference: str
    transport_kind: str
    provider_invocation_ceiling: int
    max_attempts: int
    cumulative_token_ceiling: int
    request_timeout_ms: int
    total_wall_clock_ms: int
    cumulative_cost_microusd: int
    target_repo_mutation_authorized: bool
    production_deployment_authorized: bool
    cleanup_execution_authorized: bool
    p14d_authorized: bool
    expires_at_utc: str
    nonce: str

    def canonical_record(self) -> dict[str, object]:
        return {
            "approval_version": self.approval_version,
            **self.binding().canonical_record(),
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
        }

    def binding(self) -> P14CLiveExecutionBinding:
        return P14CLiveExecutionBinding(
            authorization_id=self.authorization_id,
            repository=self.repository,
            action=self.action,
            implementation_authorization_base_sha=(
                self.implementation_authorization_base_sha
            ),
            execution_commit_sha=self.execution_commit_sha,
            execution_tree_sha=self.execution_tree_sha,
            source_manifest_sha256=self.source_manifest_sha256,
            clean_worktree=self.clean_worktree,
            execution_host_id=self.execution_host_id,
            replay_ledger_instance_id=self.replay_ledger_instance_id,
            packet_sha256=self.packet_sha256,
            request_sha256=self.request_sha256,
            fixture_id=self.fixture_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            method=self.method,
            host=self.host,
            path=self.path,
            credential_reference=self.credential_reference,
            transport_kind=self.transport_kind,
            provider_invocation_ceiling=self.provider_invocation_ceiling,
            max_attempts=self.max_attempts,
            cumulative_token_ceiling=self.cumulative_token_ceiling,
            request_timeout_ms=self.request_timeout_ms,
            total_wall_clock_ms=self.total_wall_clock_ms,
            cumulative_cost_microusd=self.cumulative_cost_microusd,
            target_repo_mutation_authorized=(
                self.target_repo_mutation_authorized
            ),
            production_deployment_authorized=(
                self.production_deployment_authorized
            ),
            cleanup_execution_authorized=self.cleanup_execution_authorized,
            p14d_authorized=self.p14d_authorized,
        )

    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json_bytes(self.canonical_record())).hexdigest()


@dataclass(frozen=True)
class GitHubIssueCommentEvidence:
    comment_id: int
    issue_number: int
    author_login: str
    author_association: str
    created_at_utc: str
    updated_at_utc: str
    body: str


class P14CLiveExecutionGrant:
    """Opaque, one-shot authority to mint one exact provider capability."""

    __slots__ = (
        "_approval_record_sha256",
        "_binding",
        "_comment_id",
        "_consumed",
        "_expires_at_epoch_seconds",
        "_issue_number",
        "_lock",
        "_sealed",
    )

    def __init__(
        self,
        *,
        binding: P14CLiveExecutionBinding,
        approval_record_sha256: str,
        comment_id: int,
        issue_number: int,
        expires_at_epoch_seconds: int,
        _issuer: object,
    ) -> None:
        if _issuer is not _GRANT_ISSUER:
            raise TypeError("P14C live execution grants require the GitHub issuer")
        object.__setattr__(self, "_binding", binding)
        object.__setattr__(
            self,
            "_approval_record_sha256",
            approval_record_sha256,
        )
        object.__setattr__(self, "_comment_id", comment_id)
        object.__setattr__(self, "_issue_number", issue_number)
        object.__setattr__(
            self,
            "_expires_at_epoch_seconds",
            expires_at_epoch_seconds,
        )
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("P14C live execution grant is immutable")
        object.__setattr__(self, name, value)

    @property
    def approval_record_sha256(self) -> str:
        return self._approval_record_sha256

    @property
    def comment_id(self) -> int:
        return self._comment_id

    @property
    def issue_number(self) -> int:
        return self._issue_number

    @property
    def expires_at_epoch_seconds(self) -> int:
        return self._expires_at_epoch_seconds

    def consume_for_capability(
        self,
        binding: P14CLiveExecutionBinding,
    ) -> tuple[str, ...]:
        if binding != self._binding:
            return ("P14C live execution grant binding does not match",)
        with self._lock:
            if (
                datetime.now(timezone.utc).timestamp()
                > self._expires_at_epoch_seconds
            ):
                return ("P14C live execution grant has expired",)
            if self._consumed:
                return ("P14C live execution grant was already consumed",)
            object.__setattr__(self, "_consumed", True)
        return ()


def build_p14c_execution_source_seal(
    repository_root: str | Path,
    replay_ledger: DurableOrchestratorStore,
) -> P14CExecutionSourceSeal:
    """Measure the exact clean checkout, critical source, host, and ledger."""

    if not isinstance(replay_ledger, DurableOrchestratorStore):
        raise TypeError("replay_ledger must be DurableOrchestratorStore")
    root = _canonical_repository_root(repository_root)
    if _git_output(root, "remote", "get-url", "origin") not in (
        _CANONICAL_TOOL_SYSTEM_REMOTES
    ):
        raise P14CLiveExecutionAuthorizationError(
            "execution checkout origin is not apolo183/tool-system"
        )
    commit_sha = _git_output(root, "rev-parse", "HEAD")
    tree_sha = _git_output(root, "rev-parse", "HEAD^{tree}")
    if _SHA_RE.fullmatch(commit_sha) is None:
        raise P14CLiveExecutionAuthorizationError(
            "execution commit SHA is invalid"
        )
    if _SHA_RE.fullmatch(tree_sha) is None:
        raise P14CLiveExecutionAuthorizationError("execution tree SHA is invalid")
    if _git_output(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise P14CLiveExecutionAuthorizationError(
            "execution worktree must be exactly clean"
        )

    source_entries: list[dict[str, str]] = []
    for relative_path in P14C_CRITICAL_SOURCE_PATHS:
        path = root / relative_path
        try:
            metadata = path.lstat()
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime source is unavailable: {relative_path}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime source must be a regular non-symlink file: {relative_path}"
            )
        if resolved != path or not resolved.is_relative_to(root):
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime source escapes its exact path: {relative_path}"
            )
        loaded_module = sys.modules.get(
            _P14C_CRITICAL_SOURCE_MODULES[relative_path]
        )
        loaded_file = getattr(loaded_module, "__file__", None)
        try:
            loaded_path = Path(loaded_file).resolve(strict=True)
        except (OSError, TypeError):
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime module is not loaded from source: {relative_path}"
            ) from None
        if loaded_path != resolved:
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime module source does not match execution checkout: {relative_path}"
            )
        try:
            source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            after = path.lstat()
        except OSError as exc:
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime source could not be read: {relative_path}"
            ) from exc
        if (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise P14CLiveExecutionAuthorizationError(
                f"critical runtime source changed while sealing: {relative_path}"
            )
        source_entries.append(
            {"path": relative_path, "sha256": source_sha256}
        )
    source_manifest_sha256 = hashlib.sha256(
        _canonical_json_bytes(
            {
                "manifest_version": P14C_SOURCE_MANIFEST_VERSION,
                "files": source_entries,
            }
        )
    ).hexdigest()
    execution_host_id = socket.gethostname()
    if not isinstance(execution_host_id, str) or _HOST_ID_RE.fullmatch(
        execution_host_id
    ) is None:
        raise P14CLiveExecutionAuthorizationError(
            "execution host identity is unavailable or invalid"
        )
    ledger_instance_id = replay_ledger.authorization_ledger_instance_id
    if _SHA256_RE.fullmatch(ledger_instance_id) is None:
        raise P14CLiveExecutionAuthorizationError(
            "replay ledger instance identity is invalid"
        )
    return P14CExecutionSourceSeal(
        repository=P14C_APPROVAL_REPOSITORY,
        execution_commit_sha=commit_sha,
        execution_tree_sha=tree_sha,
        source_manifest_sha256=source_manifest_sha256,
        clean_worktree=True,
        execution_host_id=execution_host_id,
        replay_ledger_instance_id=ledger_instance_id,
    )


def validate_p14c_execution_source_seal(
    source_seal: P14CExecutionSourceSeal,
    *,
    repository_root: str | Path,
    replay_ledger: DurableOrchestratorStore,
) -> tuple[str, ...]:
    if not isinstance(source_seal, P14CExecutionSourceSeal):
        return ("P14C execution source seal is invalid",)
    try:
        actual = build_p14c_execution_source_seal(
            repository_root, replay_ledger
        )
    except (P14CLiveExecutionAuthorizationError, StateConflict, ValueError) as exc:
        return (str(exc),)
    reasons: list[str] = []
    for field_name in P14CExecutionSourceSeal.__dataclass_fields__:
        if getattr(source_seal, field_name) != getattr(actual, field_name):
            reasons.append(
                f"P14C execution source seal {field_name} does not match"
            )
    return tuple(reasons)


def _canonical_repository_root(repository_root: str | Path) -> Path:
    raw_root = Path(repository_root)
    if raw_root.is_symlink():
        raise P14CLiveExecutionAuthorizationError(
            "execution repository root must not be a symlink"
        )
    try:
        root = raw_root.resolve(strict=True)
        metadata = root.lstat()
    except OSError as exc:
        raise P14CLiveExecutionAuthorizationError(
            "execution repository root is unavailable"
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise P14CLiveExecutionAuthorizationError(
            "execution repository root must be a directory"
        )
    top_level = _git_output(root, "rev-parse", "--show-toplevel")
    if Path(top_level).resolve(strict=True) != root:
        raise P14CLiveExecutionAuthorizationError(
            "execution repository root is not the exact Git top level"
        )
    return root


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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise P14CLiveExecutionAuthorizationError(
            "execution repository Git evidence is unavailable"
        ) from exc
    if result.returncode != 0:
        raise P14CLiveExecutionAuthorizationError(
            "execution repository Git evidence is invalid"
        )
    try:
        return result.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise P14CLiveExecutionAuthorizationError(
            "execution repository Git evidence is not UTF-8"
        ) from exc


def build_p14c_live_execution_approval_body(
    binding: P14CLiveExecutionBinding,
    *,
    expires_at_utc: str,
    nonce: str,
) -> str:
    """Build the exact JSON body an external GitHub owner may later publish."""

    if not isinstance(binding, P14CLiveExecutionBinding):
        raise TypeError("binding must be P14CLiveExecutionBinding")
    if _parse_utc(expires_at_utc) is None:
        raise ValueError("expires_at_utc must be canonical UTC")
    if _NONCE_RE.fullmatch(nonce) is None:
        raise ValueError("nonce must be 64 lowercase hexadecimal characters")
    return _canonical_json_bytes(
        {
            "approval_version": P14C_APPROVAL_VERSION,
            **binding.canonical_record(),
            "expires_at_utc": expires_at_utc,
            "nonce": nonce,
        }
    ).decode("utf-8")


def issue_p14c_live_execution_grant(
    *,
    comment_id: int,
    binding: P14CLiveExecutionBinding,
    repository_root: str | Path,
    replay_ledger: DurableOrchestratorStore,
) -> P14CLiveExecutionGrant:
    """Authenticate one pinned GitHub owner comment and issue one exact grant."""

    if not isinstance(binding, P14CLiveExecutionBinding):
        raise TypeError("binding must be P14CLiveExecutionBinding")
    source_reasons = validate_p14c_execution_source_seal(
        binding.source_seal(),
        repository_root=repository_root,
        replay_ledger=replay_ledger,
    )
    if source_reasons:
        raise P14CLiveExecutionAuthorizationError("; ".join(source_reasons))
    evidence = _fetch_github_issue_comment(comment_id)
    reasons: list[str] = []
    if evidence.author_login != P14C_APPROVAL_OWNER:
        reasons.append("GitHub approval author is not the pinned repository owner")
    if evidence.author_association != "OWNER":
        reasons.append("GitHub approval author_association must be OWNER")
    if evidence.created_at_utc != evidence.updated_at_utc:
        reasons.append("GitHub approval comment must never have been edited")
    if len(evidence.body.encode("utf-8")) > P14C_APPROVAL_BODY_LIMIT_BYTES:
        reasons.append("GitHub approval body exceeds the P14C limit")

    approval: P14CLiveExecutionApproval | None = None
    try:
        approval = _parse_approval(evidence.body)
    except ValueError as exc:
        reasons.append(str(exc))

    created_at = _parse_utc(evidence.created_at_utc)
    now = datetime.now(timezone.utc)
    if created_at is None:
        reasons.append("GitHub approval created_at must be canonical UTC")
    elif (created_at - now).total_seconds() > P14C_APPROVAL_CLOCK_SKEW_SECONDS:
        reasons.append("GitHub approval created_at is in the future")

    if approval is not None:
        if approval.approval_version != P14C_APPROVAL_VERSION:
            reasons.append("P14C approval version does not match")
        if approval.binding() != binding:
            reasons.append("P14C approval binding does not match the requested action")
        expires_at = _parse_utc(approval.expires_at_utc)
        if expires_at is None:
            reasons.append("P14C approval expires_at_utc must be canonical UTC")
        elif created_at is not None:
            ttl_seconds = (expires_at - created_at).total_seconds()
            if ttl_seconds <= 0:
                reasons.append("P14C approval expiry must follow comment creation")
            if ttl_seconds > P14C_APPROVAL_MAX_TTL_SECONDS:
                reasons.append("P14C approval lifetime exceeds 15 minutes")
            if now > expires_at:
                reasons.append("P14C approval has expired")
        if _NONCE_RE.fullmatch(approval.nonce) is None:
            reasons.append("P14C approval nonce is invalid")

    if reasons:
        raise P14CLiveExecutionAuthorizationError("; ".join(reasons))
    assert approval is not None
    expires_at = _parse_utc(approval.expires_at_utc)
    assert expires_at is not None
    approval_sha256 = approval.sha256()
    try:
        replay_ledger.consume_authorization_once(
            approval_source="github_issue_comment",
            repository=binding.repository,
            approval_record_id=str(evidence.comment_id),
            authorization_id=binding.authorization_id,
            approval_record_sha256=approval_sha256,
            binding_sha256=binding.sha256(),
            executor_host_id=binding.execution_host_id,
            ledger_instance_id=binding.replay_ledger_instance_id,
            expires_at_epoch_seconds=expires_at.timestamp(),
        )
    except (AuthorizationReplay, StateConflict, ValueError) as exc:
        raise P14CLiveExecutionAuthorizationError(str(exc)) from None
    return P14CLiveExecutionGrant(
        binding=binding,
        approval_record_sha256=approval_sha256,
        comment_id=evidence.comment_id,
        issue_number=evidence.issue_number,
        expires_at_epoch_seconds=int(expires_at.timestamp()),
        _issuer=_GRANT_ISSUER,
    )


def _fetch_github_issue_comment(comment_id: int) -> GitHubIssueCommentEvidence:
    if (
        not isinstance(comment_id, int)
        or isinstance(comment_id, bool)
        or comment_id <= 0
    ):
        raise GitHubApprovalReadError("GitHub approval comment_id must be positive")
    path = (
        f"/repos/apolo183/tool-system/issues/comments/{comment_id}"
    )
    connection = http.client.HTTPSConnection(
        GITHUB_API_HOST,
        443,
        timeout=10.0,
        context=ssl.create_default_context(),
    )
    try:
        connection.request(
            "GET",
            path,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "tool-system-p14c-live-issuer/1.0",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
            },
        )
        response = connection.getresponse()
        payload = response.read(GITHUB_RESPONSE_LIMIT_BYTES + 1)
        if response.status != 200:
            raise GitHubApprovalReadError(
                f"GitHub approval read returned HTTP {response.status}"
            )
        if len(payload) > GITHUB_RESPONSE_LIMIT_BYTES:
            raise GitHubApprovalReadError("GitHub approval response is too large")
    except GitHubApprovalReadError:
        raise
    except (
        OSError,
        TimeoutError,
        ssl.SSLError,
        http.client.HTTPException,
    ) as exc:
        raise GitHubApprovalReadError(
            f"GitHub approval read failed: {type(exc).__name__}"
        ) from None
    finally:
        connection.close()

    try:
        value = _load_exact_json(payload.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("GitHub approval response must be an object")
        actual_comment_id = value.get("id")
        issue_url = value.get("issue_url")
        user = value.get("user")
        body = value.get("body")
        author_association = value.get("author_association")
        created_at = value.get("created_at")
        updated_at = value.get("updated_at")
        if actual_comment_id != comment_id:
            raise ValueError("GitHub approval response comment ID does not match")
        if not isinstance(issue_url, str):
            raise ValueError("GitHub approval issue_url is missing")
        issue_match = _ISSUE_URL_RE.fullmatch(issue_url)
        if issue_match is None:
            raise ValueError("GitHub approval is not from apolo183/tool-system")
        if not isinstance(user, dict) or not isinstance(user.get("login"), str):
            raise ValueError("GitHub approval author identity is missing")
        if not isinstance(body, str):
            raise ValueError("GitHub approval body is missing")
        if not isinstance(author_association, str):
            raise ValueError("GitHub approval author association is missing")
        if not isinstance(created_at, str) or not isinstance(updated_at, str):
            raise ValueError("GitHub approval timestamps are missing")
        return GitHubIssueCommentEvidence(
            comment_id=actual_comment_id,
            issue_number=int(issue_match.group(1)),
            author_login=user["login"],
            author_association=author_association,
            created_at_utc=created_at,
            updated_at_utc=updated_at,
            body=body,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise GitHubApprovalReadError(
            f"GitHub approval response is invalid: {exc}"
        ) from None


def _parse_approval(body: str) -> P14CLiveExecutionApproval:
    try:
        value = _load_exact_json(body)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"P14C approval body is invalid JSON: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError("P14C approval body must be an object")
    expected_fields = {
        "approval_version",
        *P14CLiveExecutionBinding.__dataclass_fields__,
        "expires_at_utc",
        "nonce",
    }
    if set(value) != expected_fields:
        raise ValueError(
            "P14C approval body must contain exactly the registered fields"
        )
    string_fields = expected_fields - {
        "provider_invocation_ceiling",
        "max_attempts",
        "cumulative_token_ceiling",
        "request_timeout_ms",
        "total_wall_clock_ms",
        "cumulative_cost_microusd",
        "clean_worktree",
        "target_repo_mutation_authorized",
        "production_deployment_authorized",
        "cleanup_execution_authorized",
        "p14d_authorized",
    }
    if any(type(value[field]) is not str for field in string_fields):
        raise ValueError("P14C approval string fields must be strings")
    integer_fields = {
        "provider_invocation_ceiling",
        "max_attempts",
        "cumulative_token_ceiling",
        "request_timeout_ms",
        "total_wall_clock_ms",
        "cumulative_cost_microusd",
    }
    if any(type(value[field]) is not int for field in integer_fields):
        raise ValueError("P14C approval integer fields must be integers")
    boolean_fields = {
        "clean_worktree",
        "target_repo_mutation_authorized",
        "production_deployment_authorized",
        "cleanup_execution_authorized",
        "p14d_authorized",
    }
    if any(type(value[field]) is not bool for field in boolean_fields):
        raise ValueError("P14C approval authorization fields must be booleans")
    if _SHA256_RE.fullmatch(value["packet_sha256"]) is None:
        raise ValueError("P14C approval packet_sha256 is invalid")
    if _SHA256_RE.fullmatch(value["request_sha256"]) is None:
        raise ValueError("P14C approval request_sha256 is invalid")
    if _SHA_RE.fullmatch(value["implementation_authorization_base_sha"]) is None:
        raise ValueError(
            "P14C approval implementation_authorization_base_sha is invalid"
        )
    if _SHA_RE.fullmatch(value["execution_commit_sha"]) is None:
        raise ValueError("P14C approval execution_commit_sha is invalid")
    if _SHA_RE.fullmatch(value["execution_tree_sha"]) is None:
        raise ValueError("P14C approval execution_tree_sha is invalid")
    if _SHA256_RE.fullmatch(value["source_manifest_sha256"]) is None:
        raise ValueError("P14C approval source_manifest_sha256 is invalid")
    if _SHA256_RE.fullmatch(value["replay_ledger_instance_id"]) is None:
        raise ValueError("P14C approval replay_ledger_instance_id is invalid")
    if _HOST_ID_RE.fullmatch(value["execution_host_id"]) is None:
        raise ValueError("P14C approval execution_host_id is invalid")
    if value["clean_worktree"] is not True:
        raise ValueError("P14C approval clean_worktree must be true")
    return P14CLiveExecutionApproval(**value)


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or _UTC_TIMESTAMP_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _load_exact_json(payload: str | bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    return json.loads(payload, object_pairs_hook=reject_duplicate_keys)
