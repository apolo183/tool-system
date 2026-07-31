from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

import tool_system.ai_worker.live_provider as live_provider_module
import tool_system.process_authority.live_provider_approval as approval_module
from tool_system.ai_worker.live_provider import (
    OpenAIResponsesTransport,
    build_p14c_execution_packet,
    build_p14c_github_approval_body,
    build_p14c_live_execution_binding,
    build_p14c_synthetic_request,
    issue_p14c_live_network_capability,
)
from tool_system.process_authority.live_provider_approval import (
    GitHubApprovalReadError,
    P14CLiveExecutionAuthorizationError,
    P14CLiveExecutionBinding,
    P14CLiveExecutionGrant,
)


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
    created_at: datetime,
    expires_at: datetime | None = None,
    nonce_digit: str = "a",
) -> str:
    return build_p14c_github_approval_body(
        expires_at_utc=_utc(expires_at or created_at + timedelta(minutes=10)),
        nonce=nonce_digit * 64,
    )


def _comment_payload(
    *,
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
            "body": body or _approval_body(created_at=created_at),
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


def test_owner_comment_issues_one_exact_capability_without_real_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    comment_id = 91_001
    connections = _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            comment_id=comment_id,
            created_at=now - timedelta(minutes=1),
        ),
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = OpenAIResponsesTransport()

    capability = issue_p14c_live_network_capability(
        comment_id=comment_id,
        packet=packet,
        request=request,
        transport=transport,
    )

    assert capability.authorization_id == "P14C-LIVE-EXEC-v1"
    assert capability.transport_kind == "live_network"
    assert capability.approval_comment_id == comment_id
    assert capability.approval_issue_number == 148
    assert isinstance(capability.expires_at_epoch_seconds, int)
    assert isinstance(capability.approval_record_sha256, str)
    assert len(capability.approval_record_sha256) == 64
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
        match="already used",
    ):
        issue_p14c_live_network_capability(
            comment_id=comment_id,
            packet=packet,
            request=request,
            transport=OpenAIResponsesTransport(),
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
            transport=OpenAIResponsesTransport(),
        )


def test_approval_body_drift_and_duplicate_fields_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    body = json.loads(_approval_body(created_at=now - timedelta(minutes=1)))
    body["model_id"] = "different-model"
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
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
            transport=OpenAIResponsesTransport(),
        )

    duplicate = _approval_body(
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
            transport=OpenAIResponsesTransport(),
        )


def test_http_failure_and_nonexact_transport_fail_closed_before_provider_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_github(monkeypatch, payload=b"{}", status=302)
    with pytest.raises(GitHubApprovalReadError, match="HTTP 302"):
        issue_p14c_live_network_capability(
            comment_id=91_010,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=OpenAIResponsesTransport(),
        )

    class CallerTransport(OpenAIResponsesTransport):
        pass

    with pytest.raises(TypeError, match="exact OpenAI TLS transport"):
        issue_p14c_live_network_capability(
            comment_id=91_011,
            packet=build_p14c_execution_packet(),
            request=build_p14c_synthetic_request(),
            transport=CallerTransport(),
        )


def test_live_capability_expiry_blocks_after_issuance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    comment_id = 91_013
    _install_fake_github(
        monkeypatch,
        payload=_comment_payload(
            comment_id=comment_id,
            created_at=now - timedelta(minutes=1),
        ),
    )
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    transport = OpenAIResponsesTransport()
    capability = issue_p14c_live_network_capability(
        comment_id=comment_id,
        packet=packet,
        request=request,
        transport=transport,
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


def test_grant_is_opaque_and_approval_builder_preserves_all_denials() -> None:
    packet = build_p14c_execution_packet()
    request = build_p14c_synthetic_request(packet)
    binding = build_p14c_live_execution_binding(packet, request)
    record = json.loads(
        build_p14c_github_approval_body(
            expires_at_utc="2026-07-31T12:15:00Z",
            nonce="f" * 64,
            packet=packet,
            request=request,
        )
    )

    assert record["authorization_id"] == "P14C-LIVE-EXEC-v1"
    assert record["repository"] == "apolo183/tool-system"
    assert record["provider_id"] == "openai"
    assert record["model_id"] == "gpt-5.6-luna"
    assert record["credential_reference"] == "env:OPENAI_API_KEY"
    assert record["provider_invocation_ceiling"] == 1
    assert record["max_attempts"] == 2
    assert record["cumulative_cost_microusd"] == 20_000
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
