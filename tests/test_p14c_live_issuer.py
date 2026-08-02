from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import tool_system.ai_worker.live_evidence as live_evidence_module
import tool_system.ai_worker.live_provider as live_provider_module
import tool_system.orchestrator as orchestrator_package
import tool_system.orchestrator.durable as durable_module
import tool_system.process_authority as process_authority_package
import tool_system.process_authority.live_provider_approval as approval_module
from tool_system.ai_worker.contract import (
    AIWorkerErrorCode,
    AIWorkerUsage,
    ProviderResponse,
    canonical_sha256,
)
from tool_system.ai_worker.live_evidence import (
    build_prepare_approval_evidence,
    execute_p14c_live_entry,
)
from tool_system.ai_worker.live_provider import (
    DeepSeekChatCompletionsProvider,
    DeepSeekChatCompletionsTransport,
    build_p14c_execution_packet,
    build_p14c_github_approval_body,
    build_p14c_live_execution_binding,
    build_p14c_synthetic_request,
    issue_p14c_live_network_capability,
)
from tool_system.process_authority.live_provider_approval import (
    GitHubApprovalReadError,
    P14C_APPROVAL_VERSION,
    P14C_CRITICAL_SOURCE_PATHS,
    P14CExecutionSourceSeal,
    P14CLiveExecutionAuthorizationError,
    P14CLiveExecutionBinding,
    P14CLiveExecutionGrant,
    build_p14c_execution_source_seal,
    validate_p14c_execution_source_seal,
)
from tool_system.orchestrator import DurableOrchestratorStore


ROOT = Path(__file__).resolve().parents[1]
ExecutionContext = tuple[Path, DurableOrchestratorStore]


class _FakeGitHubResponse:
    def __init__(self, *, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self, limit: int) -> bytes:
        return self._body


class _FakeGitHubConnection:
    def __init__(self, *, status: int, body: bytes) -> None:
        self.response = _FakeGitHubResponse(status=status, body=body)
        self.requests: list[dict[str, object]] = []
        self.closed = False

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
    ) -> None:
        self.requests.append(
            {
                "method": method,
                "path": path,
                "headers": dict(headers),
            }
        )

    def getresponse(self) -> _FakeGitHubResponse:
        return self.response

    def close(self) -> None:
        self.closed = True


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _approval_body(
    *,
    execution_context: ExecutionContext,
    created_at: datetime,
    expires_at: datetime | None = None,
    nonce_digit: str = "a",
) -> str:
    repository_root, replay_ledger = execution_context
    return build_p14c_github_approval_body(
        expires_at_utc=_utc(expires_at or created_at + timedelta(minutes=10)),
        nonce=nonce_digit * 64,
        repository_root=repository_root,
        replay_ledger=replay_ledger,
    )


def _comment_payload(
    *,
    execution_context: ExecutionContext,
    comment_id: int,
    created_at: datetime,
    body: str | None = None,
    author_login: str = "apolo183",
    author_association: str = "OWNER",
    updated_at: datetime | None = None,
    issue_url: str = (
        "https://api.github.com/repos/apolo183/tool-system/issues/148"
    ),
) -> bytes:
    return json.dumps(
        {
            "id": comment_id,
            "issue_url": issue_url,
            "user": {"login": author_login},
            "author_association": author_association,
            "created_at": _utc(created_at),
            "updated_at": _utc(updated_at or created_at),
            "body": body
            or _approval_body(
                execution_context=execution_context,
                created_at=created_at,
            ),
        }
    ).encode("utf-8")


def _install_fake_github(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: bytes,
    status: int = 200,
) -> list[_FakeGitHubConnection]:
    connections: list[_FakeGitHubConnection] = []

    def build_connection(
        host: str,
        port: int,
        *,
        timeout: float,
        context: object,
    ) -> _FakeGitHubConnection:
        assert (host, port, timeout) == ("api.github.com", 443, 10.0)
        assert context is not None
        connection = _FakeGitHubConnection(status=status, body=payload)
        connections.append(connection)
        return connection

    monkeypatch.setattr(
        approval_module.http.client,
        "HTTPSConnection",
        build_connection,
    )
    return connections


def _run_git(repository_root: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", *arguments),
        cwd=repository_root,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


@pytest.fixture
def execution_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> ExecutionContext:
    repository_root = tmp_path / "source"
    repository_root.mkdir(mode=0o700)
    for relative_path in P14C_CRITICAL_SOURCE_PATHS:
        target = repository_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, target)
    _run_git(repository_root, "init", "-q")
    _run_git(repository_root, "config", "user.name", "tool-system test")
    _run_git(repository_root, "config", "user.email", "tool-system@example.invalid")
    _run_git(
        repository_root,
        "remote",
        "add",
        "origin",
        "https://github.com/apolo183/tool-system.git",
    )
    _run_git(repository_root, "add", "--all")
    _run_git(repository_root, "commit", "-q", "-m", "fixture source")
    ledger_root = tmp_path / "ledger"
    ledger_root.mkdir(mode=0o700)
    replay_ledger = DurableOrchestratorStore(
        ledger_root / "approval.sqlite3",
        forbidden_roots=(ROOT, repository_root),
    )
    monkeypatch.setattr(
        live_provider_module,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[0]),
    )
    monkeypatch.setattr(
        orchestrator_package,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[1]),
    )
    monkeypatch.setattr(
        durable_module,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[2]),
    )
    monkeypatch.setattr(
        process_authority_package,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[3]),
    )
    monkeypatch.setattr(
        approval_module,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[4]),
    )
    monkeypatch.setattr(
        live_evidence_module,
        "__file__",
        str(repository_root / P14C_CRITICAL_SOURCE_PATHS[5]),
    )
    return repository_root, replay_ledger


def _live_capability_arguments(
    execution_context: ExecutionContext,
) -> dict[str, object]:
    repository_root, replay_ledger = execution_context
    return {
        "repository_root": repository_root,
        "replay_ledger": replay_ledger,
    }


def test_prepare_entry_builds_exact_source_bound_body_with_zero_external_io(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    repository_root, replay_ledger = execution_context
    github_reads = 0

    def forbidden_github(*args: object, **kwargs: object) -> object:
        nonlocal github_reads
        github_reads += 1
        raise AssertionError("prepare must not read GitHub")

    monkeypatch.setattr(
        approval_module.http.client,
        "HTTPSConnection",
        forbidden_github,
    )
    now = datetime(2026, 8, 1, 1, 2, 3, tzinfo=timezone.utc)
    evidence = build_prepare_approval_evidence(
        repository_root=repository_root,
        ledger_path=replay_ledger.database_path,
        ttl_seconds=600,
        _now=now,
        _nonce="b" * 64,
    )
    approval = json.loads(str(evidence["approval_body"]))

    assert evidence["status"] == "PASS"
    assert evidence["mode"] == "prepare-approval"
    assert evidence["approval_expires_at_utc"] == "2026-08-01T01:12:03Z"
    assert approval["approval_version"] == "p14c-live-execution-approval-v2"
    assert approval["execution_commit_sha"] == evidence["source_seal"][
        "execution_commit_sha"
    ]
    assert approval["source_manifest_sha256"] == evidence["source_seal"][
        "source_manifest_sha256"
    ]
    assert approval["replay_ledger_instance_id"] == (
        replay_ledger.authorization_ledger_instance_id
    )
    assert approval["nonce"] == "b" * 64
    assert evidence["github_approval_read_count"] == 0
    assert evidence["github_approval_write_count"] == 0
    assert evidence["credential_value_access_count"] == 0
    assert evidence["provider_invocation_count"] == 0
    assert evidence["transport_attempt_count"] == 0
    assert github_reads == 0


def test_execute_entry_emits_only_redacted_receipt_with_injected_io(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    repository_root, replay_ledger = execution_context
    source_seal = build_p14c_execution_source_seal(
        repository_root, replay_ledger
    )
    output = {
        "summary": "sensitive-model-output-must-not-appear",
        "control_status": "PASS",
    }

    class FakeCapability:
        def __init__(self) -> None:
            self.authorization_id = "P14C-LIVE-EXEC-v2"
            self.approval_record_sha256 = "a" * 64
            self.approval_issue_number = 148
            self.source_seal = source_seal

    class FakeCredentialResolver:
        def resolve(self, reference: str) -> str:
            assert reference == (
                "file:~/.config/tool-system/credentials.toml"
                "#providers.deepseek.api_key"
            )
            return "sensitive-credential-must-not-appear"

    class FakeGuard:
        def __init__(self, **kwargs: object) -> None:
            self.values = kwargs

        def validate(self, request: object, provider: object) -> tuple[str, ...]:
            return ()

    class FakeProvider:
        def __init__(
            self,
            *,
            packet: object,
            transport: object,
            credential_resolver: object,
            execution_capability: object,
        ) -> None:
            self.packet = packet
            self.transport = transport
            self.credential_resolver = credential_resolver
            self.execution_capability = execution_capability

        def invoke(self, request: object) -> ProviderResponse:
            self.credential_resolver.resolve(
                "file:~/.config/tool-system/credentials.toml"
                "#providers.deepseek.api_key"
            )
            return ProviderResponse(
                output=output,
                usage=AIWorkerUsage(
                    input_tokens=12,
                    output_tokens=7,
                    duration_ms=25,
                    cost_microunits=54,
                ),
            )

    transport = object()
    monkeypatch.setattr(
        live_evidence_module,
        "open_p14c_live_execution_ledger",
        lambda *args, **kwargs: replay_ledger,
    )
    monkeypatch.setattr(
        live_evidence_module,
        "DeepSeekChatCompletionsTransport",
        lambda: transport,
    )
    monkeypatch.setattr(
        live_evidence_module,
        "issue_p14c_live_network_capability",
        lambda **kwargs: FakeCapability(),
    )
    monkeypatch.setattr(
        live_evidence_module,
        "LocalCredentialFileResolver",
        FakeCredentialResolver,
    )
    monkeypatch.setattr(
        live_evidence_module,
        "P14CLiveExecutionGuard",
        FakeGuard,
    )
    monkeypatch.setattr(
        live_evidence_module,
        "DeepSeekChatCompletionsProvider",
        FakeProvider,
    )

    evidence = execute_p14c_live_entry(
        repository_root=repository_root,
        ledger_path=replay_ledger.database_path,
        comment_id=91_999,
    )
    rendered = json.dumps(evidence, sort_keys=True)

    assert evidence["status"] == "PASS"
    assert evidence["mode"] == "execute"
    assert evidence["approval_durably_consumed"] is True
    assert evidence["credential_resolution_attempt_count"] == 1
    assert evidence["provider_invocation_count"] == 1
    assert evidence["output_sha256"] == canonical_sha256(output)
    assert evidence["raw_provider_output_included"] is False
    assert "sensitive-model-output-must-not-appear" not in rendered
    assert "sensitive-credential-must-not-appear" not in rendered


def test_owner_comment_issues_one_exact_capability_without_real_io(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    comment_id = 91_001
    connections = _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=comment_id,
            created_at=now - timedelta(minutes=1),
        ),
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = DeepSeekChatCompletionsTransport()

    capability = issue_p14c_live_network_capability(
        comment_id=comment_id,
        packet=packet,
        request=request,
        transport=transport,
        **_live_capability_arguments(execution_context),
    )

    assert capability.authorization_id == "P14C-LIVE-EXEC-v2"
    assert capability.transport_kind == "live_network"
    assert capability.approval_comment_id == comment_id
    assert capability.approval_issue_number == 148
    assert isinstance(capability.expires_at_epoch_seconds, int)
    assert isinstance(capability.approval_record_sha256, str)
    assert len(capability.approval_record_sha256) == 64
    assert capability.source_seal is not None
    assert capability.source_seal.clean_worktree is True
    assert len(connections) == 1
    assert connections[0].requests == [
        {
            "method": "GET",
            "path": (
                "/repos/apolo183/tool-system/issues/comments/91001"
            ),
            "headers": {
                "Accept": "application/vnd.github+json",
                "User-Agent": "tool-system-p14c-live-issuer/1.0",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        }
    ]
    assert "Authorization" not in connections[0].requests[0]["headers"]
    assert connections[0].closed is True
    assert capability.consume(
        packet=packet,
        request=request,
        transport=transport,
    ) == ()
    assert capability.consume(
        packet=packet,
        request=request,
        transport=transport,
    ) == ("live execution capability was already consumed",)

    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="already consumed",
    ):
        issue_p14c_live_network_capability(
            comment_id=comment_id,
            packet=packet,
            request=request,
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )


@pytest.mark.parametrize(
    ("comment_id", "changes", "reason"),
    [
        (91_002, {"author_login": "other-user"}, "pinned repository owner"),
        (91_003, {"author_association": "MEMBER"}, "must be OWNER"),
        (
            91_004,
            {"updated_offset": timedelta(seconds=1)},
            "must never have been edited",
        ),
        (
            91_005,
            {"expires_offset": timedelta(minutes=-1)},
            "has expired",
        ),
        (
            91_006,
            {"expires_offset": timedelta(minutes=16)},
            "exceeds 15 minutes",
        ),
        (
            91_007,
            {"issue_url": "https://api.github.com/repos/other/repo/issues/1"},
            "not from apolo183/tool-system",
        ),
    ],
)
def test_untrusted_edited_expired_or_wrong_repo_comment_blocks(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
    comment_id: int,
    changes: dict[str, Any],
    reason: str,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    created_at = now - timedelta(minutes=2)
    expires_at = created_at + changes.get(
        "expires_offset",
        timedelta(minutes=10),
    )
    payload = _comment_payload(
        execution_context=execution_context,
        comment_id=comment_id,
        created_at=created_at,
        updated_at=created_at + changes.get("updated_offset", timedelta()),
        author_login=changes.get("author_login", "apolo183"),
        author_association=changes.get("author_association", "OWNER"),
        issue_url=changes.get(
            "issue_url",
            "https://api.github.com/repos/apolo183/tool-system/issues/148",
        ),
        body=_approval_body(
            execution_context=execution_context,
            created_at=created_at,
            expires_at=expires_at,
            nonce_digit=str(comment_id)[-1],
        ),
    )
    _install_fake_github(monkeypatch, payload=payload)

    with pytest.raises(
        (GitHubApprovalReadError, P14CLiveExecutionAuthorizationError),
        match=reason,
    ):
        issue_p14c_live_network_capability(
            comment_id=comment_id,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )


def test_approval_body_drift_and_duplicate_fields_block(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    body = json.loads(
        _approval_body(
            execution_context=execution_context,
            created_at=now - timedelta(minutes=1),
        )
    )
    body["model_id"] = "different-model"
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=91_008,
            created_at=now - timedelta(minutes=1),
            body=json.dumps(body),
        ),
    )
    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="binding does not match",
    ):
        issue_p14c_live_network_capability(
            comment_id=91_008,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )

    duplicate = _approval_body(
        execution_context=execution_context,
        created_at=now - timedelta(minutes=1),
        nonce_digit="9",
    ).replace(
        '{"action":',
        '{"action":"duplicate","action":',
        1,
    )
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=91_009,
            created_at=now - timedelta(minutes=1),
            body=duplicate,
        ),
    )
    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="duplicate JSON key",
    ):
        issue_p14c_live_network_capability(
            comment_id=91_009,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )


def test_http_failure_and_nonexact_transport_fail_closed_before_provider_access(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    _install_fake_github(monkeypatch, payload=b"{}", status=302)
    with pytest.raises(GitHubApprovalReadError, match="HTTP 302"):
        issue_p14c_live_network_capability(
            comment_id=91_010,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )

    class CallerTransport(DeepSeekChatCompletionsTransport):
        pass

    with pytest.raises(TypeError, match="exact DeepSeek TLS transport"):
        issue_p14c_live_network_capability(
            comment_id=91_011,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=CallerTransport(),
            **_live_capability_arguments(execution_context),
        )


def test_live_capability_expiry_blocks_after_issuance(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    comment_id = 91_013
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=comment_id,
            created_at=now - timedelta(minutes=1),
        ),
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = DeepSeekChatCompletionsTransport()
    capability = issue_p14c_live_network_capability(
        comment_id=comment_id,
        packet=packet,
        request=request,
        transport=transport,
        **_live_capability_arguments(execution_context),
    )
    assert capability.expires_at_epoch_seconds is not None
    monkeypatch.setattr(
        live_provider_module.time,
        "time",
        lambda: capability.expires_at_epoch_seconds + 1,
    )

    assert capability.consume(
        packet=packet,
        request=request,
        transport=transport,
    ) == ("live execution capability has expired",)


def test_source_seal_is_exact_and_wrong_host_or_ledger_fails(
    execution_context: ExecutionContext,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root, replay_ledger = execution_context
    seal = build_p14c_execution_source_seal(repository_root, replay_ledger)

    assert seal.clean_worktree is True
    assert len(seal.execution_commit_sha) == 40
    assert len(seal.execution_tree_sha) == 40
    assert len(seal.source_manifest_sha256) == 64
    assert validate_p14c_execution_source_seal(
        seal,
        repository_root=repository_root,
        replay_ledger=replay_ledger,
    ) == ()
    assert validate_p14c_execution_source_seal(
        replace(seal, execution_host_id="different-host"),
        repository_root=repository_root,
        replay_ledger=replay_ledger,
    ) == ("P14C execution source seal execution_host_id does not match",)

    second_root = tmp_path / "second-ledger"
    second_root.mkdir(mode=0o700)
    second_ledger = DurableOrchestratorStore(
        second_root / "approval.sqlite3",
        forbidden_roots=(ROOT, repository_root),
    )
    assert validate_p14c_execution_source_seal(
        seal,
        repository_root=repository_root,
        replay_ledger=second_ledger,
    ) == (
        "P14C execution source seal replay_ledger_instance_id does not match",
    )
    monkeypatch.setattr(
        live_provider_module,
        "__file__",
        str(ROOT / P14C_CRITICAL_SOURCE_PATHS[0]),
    )
    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="module source does not match execution checkout",
    ):
        build_p14c_execution_source_seal(repository_root, replay_ledger)


def test_dirty_source_blocks_before_github_read(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = _comment_payload(
        execution_context=execution_context,
        comment_id=91_014,
        created_at=now - timedelta(minutes=1),
    )
    connections = _install_fake_github(monkeypatch, payload=payload)
    repository_root, _ = execution_context
    source = repository_root / P14C_CRITICAL_SOURCE_PATHS[0]
    source.write_text(source.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")

    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="worktree must be exactly clean",
    ):
        issue_p14c_live_network_capability(
            comment_id=91_014,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )
    assert connections == []


@pytest.mark.parametrize("source_state", ["missing", "symlink"])
def test_missing_or_symlinked_critical_source_fails_closed(
    execution_context: ExecutionContext,
    source_state: str,
) -> None:
    repository_root, replay_ledger = execution_context
    source = repository_root / P14C_CRITICAL_SOURCE_PATHS[0]
    source.unlink()
    if source_state == "symlink":
        target = repository_root / P14C_CRITICAL_SOURCE_PATHS[1]
        source.symlink_to(target)
    _run_git(repository_root, "add", "--all")
    _run_git(repository_root, "commit", "-q", "-m", f"{source_state} source")

    expected = "unavailable" if source_state == "missing" else "non-symlink"
    with pytest.raises(P14CLiveExecutionAuthorizationError, match=expected):
        build_p14c_execution_source_seal(repository_root, replay_ledger)


def test_approval_v1_is_rejected_and_not_consumed(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    record = json.loads(
        _approval_body(
            execution_context=execution_context,
            created_at=now - timedelta(minutes=1),
        )
    )
    record["approval_version"] = "p14c-live-execution-approval-v1"
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=91_015,
            created_at=now - timedelta(minutes=1),
            body=json.dumps(record),
        ),
    )

    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="approval version does not match",
    ):
        issue_p14c_live_network_capability(
            comment_id=91_015,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=DeepSeekChatCompletionsTransport(),
            **_live_capability_arguments(execution_context),
        )
    _, replay_ledger = execution_context
    assert replay_ledger.get_authorization_consumption(
        approval_source="github_issue_comment",
        repository="apolo183/tool-system",
        approval_record_id="91015",
    ) is None


def test_failure_after_durable_claim_leaves_approval_burned(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=91_017,
            created_at=now - timedelta(minutes=1),
        ),
    )
    original_grant_type = approval_module.P14CLiveExecutionGrant

    def crash_after_claim(**values: object) -> object:
        raise RuntimeError("simulated crash after durable claim")

    monkeypatch.setattr(
        approval_module,
        "P14CLiveExecutionGrant",
        crash_after_claim,
    )
    values = {
        "comment_id": 91_017,
        "packet": build_p14c_execution_packet(),
        "request": build_p14c_synthetic_request(),
        "transport": DeepSeekChatCompletionsTransport(),
        **_live_capability_arguments(execution_context),
    }
    with pytest.raises(RuntimeError, match="simulated crash"):
        issue_p14c_live_network_capability(**values)  # type: ignore[arg-type]

    monkeypatch.setattr(
        approval_module,
        "P14CLiveExecutionGrant",
        original_grant_type,
    )
    with pytest.raises(
        P14CLiveExecutionAuthorizationError,
        match="already consumed",
    ):
        issue_p14c_live_network_capability(**values)  # type: ignore[arg-type]


def test_source_drift_after_issuance_blocks_before_credential_and_transport(
    monkeypatch: pytest.MonkeyPatch,
    execution_context: ExecutionContext,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            execution_context=execution_context,
            comment_id=91_016,
            created_at=now - timedelta(minutes=1),
        ),
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = DeepSeekChatCompletionsTransport()
    capability = issue_p14c_live_network_capability(
        comment_id=91_016,
        packet=packet,
        request=request,
        transport=transport,
        **_live_capability_arguments(execution_context),
    )
    credential_calls = 0
    transport_calls = 0

    class Resolver:
        def resolve(self, reference: str) -> str:
            nonlocal credential_calls
            credential_calls += 1
            return "not-a-real-secret"

    def blocked_transport(*args: object, **kwargs: object) -> object:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    monkeypatch.setattr(
        DeepSeekChatCompletionsTransport,
        "send",
        blocked_transport,
    )
    repository_root, _ = execution_context
    source = repository_root / P14C_CRITICAL_SOURCE_PATHS[0]
    source.write_text(source.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    response = DeepSeekChatCompletionsProvider(
        packet=packet,
        transport=transport,
        credential_resolver=Resolver(),
        execution_capability=capability,
    ).invoke(request)

    assert response.error is not None
    assert response.error.code is AIWorkerErrorCode.PROVIDER_MISMATCH
    assert credential_calls == 0
    assert transport_calls == 0


def test_grant_is_opaque_and_approval_builder_preserves_all_denials(
    execution_context: ExecutionContext,
) -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    repository_root, replay_ledger = execution_context
    source_seal = build_p14c_execution_source_seal(
        repository_root, replay_ledger
    )
    binding = build_p14c_live_execution_binding(
        packet, request, source_seal
    )
    record = json.loads(
        build_p14c_github_approval_body(
            expires_at_utc="2026-07-31T12:15:00Z",
            nonce="f" * 64,
            packet=packet,
            request=request,
            repository_root=repository_root,
            replay_ledger=replay_ledger,
        )
    )

    assert record["approval_version"] == P14C_APPROVAL_VERSION
    assert record["authorization_id"] == "P14C-LIVE-EXEC-v2"
    assert record["repository"] == "apolo183/tool-system"
    assert record["provider_id"] == "deepseek"
    assert record["model_id"] == "deepseek-v4-flash"
    assert record["credential_reference"] == (
        "file:~/.config/tool-system/credentials.toml#providers.deepseek.api_key"
    )
    assert record["provider_invocation_ceiling"] == 1
    assert record["max_attempts"] == 1
    assert record["cumulative_cost_microusd"] == 2_000
    assert record["execution_commit_sha"] == source_seal.execution_commit_sha
    assert record["execution_tree_sha"] == source_seal.execution_tree_sha
    assert record["source_manifest_sha256"] == source_seal.source_manifest_sha256
    assert record["clean_worktree"] is True
    assert record["execution_host_id"] == source_seal.execution_host_id
    assert record["replay_ledger_instance_id"] == (
        source_seal.replay_ledger_instance_id
    )
    assert record["target_repo_mutation_authorized"] is False
    assert record["production_deployment_authorized"] is False
    assert record["cleanup_execution_authorized"] is False
    assert record["p14d_authorized"] is False

    with pytest.raises(TypeError, match="GitHub issuer"):
        P14CLiveExecutionGrant(
            binding=replace(
                binding,
                authorization_id="caller-created",
            ),
            approval_record_sha256="0" * 64,
            comment_id=91_012,
            issue_number=148,
            expires_at_epoch_seconds=1,
            _issuer=object(),
        )
