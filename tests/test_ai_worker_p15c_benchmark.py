from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from tool_system.ai_worker.p15c_benchmark import (
    P15CBenchmarkCase,
    P15CBenchmarkError,
    P15CBenchmarkExecutor,
    P15CDirectTLSTransport,
    P15CHTTPResponse,
    P15CTransportFailure,
    assert_p15c_provider_packets_execution_eligible,
    build_p15c_metrics,
    build_p15c_private_case,
    build_p15c_request,
    calculate_p15c_cost_micro_usd,
    load_p15c_deterministic_case,
    load_p15c_provider_packets,
    parse_p15c_provider_response,
)
from tool_system.ai_worker.p15c_controls import (
    P15C_AUTHORIZATION_ID,
    P15CSnapshotFile,
    P15CTargetInventoryItem,
    P15CTargetPacket,
    P15CUsageLedger,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_CONFIG = ROOT / "config" / "p15c_execution_packet_freeze_v1.yaml"


def _git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


def _snapshot(path: str, content: str) -> P15CSnapshotFile:
    raw = content.encode("utf-8")
    return P15CSnapshotFile(
        path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
        git_blob_sha=_git_blob_sha(raw),
        content=content,
    )


def _cases() -> tuple[P15CBenchmarkCase, P15CBenchmarkCase]:
    deterministic_file = _snapshot("src/deterministic.py", "result = 1 / 0\n")
    private_file = _snapshot(
        "src/private.py", "def identity(value):\n    return value\n"
    )
    return (
        P15CBenchmarkCase(
            case_id="deterministic-corpus",
            files=(deterministic_file,),
            case_sha256=hashlib.sha256(b"deterministic-case").hexdigest(),
            expected_finding_paths=frozenset({deterministic_file.path}),
            private_target=False,
        ),
        P15CBenchmarkCase(
            case_id="private-target",
            files=(private_file,),
            case_sha256=hashlib.sha256(b"private-case").hexdigest(),
            expected_finding_paths=frozenset(),
            private_target=True,
        ),
    )


def _target_packet(private_case: P15CBenchmarkCase, root: Path) -> P15CTargetPacket:
    item = private_case.files[0]
    inventory = P15CTargetInventoryItem(
        path=item.path,
        sha256=item.sha256,
        git_blob_sha=item.git_blob_sha,
        size_bytes=len(item.content.encode("utf-8")),
    )
    return P15CTargetPacket(
        packet_id="operator-private-target-v1",
        repository_identity="operator/private-target",
        visibility="private",
        branch="main",
        exact_commit="3" * 40,
        exact_file_allowlist=(item.path,),
        content_addressed_inventory=(inventory,),
        durable_module_contract={
            "contract_id": "operator-contract-v1",
            "contract_version": "1.0.0",
            "read_only": True,
        },
        inventory_read_authority=True,
        benchmark_read_authority=True,
        provider_transfer_authority_by_provider={
            "deepseek": True,
            "openai": True,
            "qwen": True,
        },
        mutation_authority=False,
        snapshot_root=root,
        packet_sha256=hashlib.sha256(b"private-packet").hexdigest(),
    )


def _model_output(path: str) -> dict[str, object]:
    return {
        "assessment": "issues_found",
        "confidence_micros": 900_000,
        "findings": [
            {
                "path": path,
                "category": "correctness",
                "severity": "high",
                "summary": "A concrete issue is present in the supplied snapshot.",
            }
        ],
    }


def _provider_response(provider_id: str, path: str) -> P15CHTTPResponse:
    output_text = json.dumps(_model_output(path), sort_keys=True)
    if provider_id == "openai":
        body = {
            "model": "gpt-5.6-luna",
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": output_text}],
                }
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 10,
                "input_tokens_details": {"cached_tokens": 20},
            },
        }
    elif provider_id == "deepseek":
        body = {
            "model": "deepseek-v4-flash",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": output_text},
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10},
        }
    else:
        assert provider_id == "qwen"
        body = {
            "model": "qwen3.7-plus-2026-05-26",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": output_text},
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 10,
                "prompt_tokens_details": {"cached_tokens": 20},
            },
        }
    return P15CHTTPResponse(
        200, {"content-type": "application/json"}, json.dumps(body).encode()
    )


class _FakeResolver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def resolve(self, reference: str, provider_id: str) -> str:
        self.calls.append((reference, provider_id))
        return "unit-test-credential-value"


class _FakeTransport:
    transport_kind = "injected_fake"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def send(
        self,
        *,
        host: str,
        path: str,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> P15CHTTPResponse:
        request = json.loads(body)
        provider_id = {
            "api.openai.com": "openai",
            "api.deepseek.com": "deepseek",
            "dashscope.aliyuncs.com": "qwen",
        }[host]
        messages = request.get("input", request.get("messages"))
        snapshot = json.loads(messages[1]["content"].split("SNAPSHOT_JSON:\n", 1)[1])
        self.calls.append(
            {
                "host": host,
                "path": path,
                "authorization_present": "authorization" in headers,
                "timeout_seconds": timeout_seconds,
            }
        )
        return _provider_response(provider_id, snapshot["allowed_paths"][0])


class _FailingTransport:
    transport_kind = "injected_fake_failure"

    def __init__(self) -> None:
        self.calls = 0

    def send(self, **_: object) -> P15CHTTPResponse:
        self.calls += 1
        raise P15CTransportFailure("TRANSPORT_TIMEOUT")


class _Clock:
    def __init__(self) -> None:
        self.value = 10.0

    def __call__(self) -> float:
        self.value += 0.01
        return self.value


class _Cancelled:
    def is_cancelled(self) -> bool:
        return True


class _ForbiddenPrivateBoundary:
    def __getattr__(self, _: str) -> object:
        raise AssertionError("provider-packet blocker crossed a private boundary")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _sealed_repository(
    root: Path,
    provider_ids: tuple[str, str] = ("deepseek", "openai"),
) -> tuple[Path, str, str]:
    root.mkdir()
    for relative in (
        "config/p15c_execution_packet_freeze_v1.yaml",
        "src/tool_system/ai_worker/p15c_benchmark.py",
        "src/tool_system/ai_worker/p15c_controls.py",
        "src/tool_system/ai_worker/p15c_entry.py",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    packet_config = root / "config/p15c_execution_packet_freeze_v1.yaml"
    packet_source = yaml.safe_load(packet_config.read_text(encoding="utf-8"))
    if provider_ids == ("deepseek", "openai"):
        packet_source.pop("execution_matrix", None)
        deepseek = next(
            packet
            for packet in packet_source["provider_packets"]
            if packet["provider_id"] == "deepseek"
        )
        deepseek["packet_status"] = "FROZEN_NOT_ACTIVATED"
        deepseek.pop("execution_blocker")
    else:
        assert provider_ids == ("openai", "qwen")
        packet_source["execution_matrix"] = {
            "provider_ids": list(provider_ids),
            "case_ids": ["deterministic-corpus", "private-target"],
            "max_provider_invocations": 4,
        }
        qwen = next(
            packet
            for packet in packet_source["provider_packets"]
            if packet["provider_id"] == "qwen"
        )
        qwen["packet_status"] = "FROZEN_NOT_ACTIVATED"
        qwen["pricing_snapshot"]["calculated_worst_case_micro_cny"] = 196_608
    packet_config.write_text(
        yaml.safe_dump(packet_source, sort_keys=False),
        encoding="utf-8",
    )
    shutil.copytree(
        ROOT / "tests" / "fixtures" / "p14h",
        root / "tests" / "fixtures" / "p14h",
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "P15C Test")
    _git(root, "config", "user.email", "p15c-test@example.invalid")
    _git(root, "remote", "add", "origin", "https://github.com/apolo183/tool-system.git")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "sealed source")
    return root, _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")


def _owner_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    path.chmod(0o600)
    return path


def _policy(
    path: Path,
    commit: str,
    tree: str,
    target_packet_sha256: str,
    provider_ids: tuple[str, str] = ("deepseek", "openai"),
) -> Path:
    provider_enabled = {
        provider_id: False for provider_id in ("deepseek", "openai", "qwen")
    }
    provider_transfer = dict(provider_enabled)
    provider_budget = {provider_id: 0 for provider_id in provider_enabled}
    for provider_id in provider_ids:
        provider_enabled[provider_id] = True
        provider_transfer[provider_id] = True
    provider_budget["openai"] = 50_000
    if "deepseek" in provider_ids:
        provider_budget["deepseek"] = 50_000
        total_budget_micro_usd = 100_000
    else:
        provider_budget["qwen"] = 500_000
        total_budget_micro_usd = 550_000
    return _owner_json(
        path,
        {
            "schema_version": 2,
            "authorization_id": P15C_AUTHORIZATION_ID,
            "enabled": True,
            "total_budget_micro_usd": total_budget_micro_usd,
            "expires_at_utc": "2099-01-01T00:00:00Z",
            "expected_tool_system_commit": commit,
            "expected_tool_system_tree": tree,
            "expected_target_packet_sha256": target_packet_sha256,
            "provider_enabled": provider_enabled,
            "provider_budget_micro_usd": provider_budget,
            "private_repository_transfer_enabled": True,
            "provider_transfer_enabled": provider_transfer,
            "allowed_case_ids": ["deterministic-corpus", "private-target"],
            "max_provider_invocations": 4,
            "cny_to_micro_usd_ceiling": 1_000_000,
        },
    )


def _executor_fixture(
    tmp_path: Path,
    transport: object,
    provider_ids: tuple[str, str] = ("deepseek", "openai"),
):
    repository, commit, tree = _sealed_repository(tmp_path / "sealed", provider_ids)
    private_fixture = _cases()[1]
    target = _target_packet(private_fixture, tmp_path)
    cases = (
        load_p15c_deterministic_case(
            repository,
            repository / "config/p15c_execution_packet_freeze_v1.yaml",
        ),
        build_p15c_private_case(target, private_fixture.files),
    )
    private = tmp_path / "private"
    private.mkdir()
    private.chmod(0o700)
    policy = _policy(
        private / "policy.json",
        commit,
        tree,
        target.packet_sha256,
        provider_ids,
    )
    ledger = P15CUsageLedger(private / "usage.sqlite3")
    resolver = _FakeResolver()
    executor = P15CBenchmarkExecutor(
        repository_root=repository,
        packet_config_path=repository / "config/p15c_execution_packet_freeze_v1.yaml",
        policy_path=policy,
        credential_resolver=resolver,  # type: ignore[arg-type]
        ledger=ledger,
        transport=transport,  # type: ignore[arg-type]
        target_packet=target,
        monotonic=_Clock(),
    )
    packets = load_p15c_provider_packets(
        repository / "config/p15c_execution_packet_freeze_v1.yaml"
    )
    return executor, packets, cases, resolver, ledger


def test_frozen_packets_expose_exact_openai_qwen_routes_and_funding_block() -> None:
    packets = load_p15c_provider_packets(PACKET_CONFIG)

    assert tuple(packet.provider_id for packet in packets) == ("openai", "qwen")
    assert [(packet.host, packet.path) for packet in packets] == [
        ("api.openai.com", "/v1/responses"),
        ("dashscope.aliyuncs.com", "/compatible-mode/v1/chat/completions"),
    ]
    assert packets[0].billing_currency == "USD"
    assert packets[0].per_attempt_hard_cap_native_microunits == 25_000
    assert packets[1].billing_currency == "CNY"
    assert packets[1].per_attempt_hard_cap_native_microunits == 250_000
    assert all(packet.public_record()["max_retries"] == 0 for packet in packets)
    assert packets[0].exact_model_version == "gpt-5.6-luna"
    assert packets[0].packet_status == "FROZEN_NOT_ACTIVATED"
    assert packets[0].execution_blocker is None
    assert packets[1].exact_model_version == "qwen3.7-plus-2026-05-26"
    assert packets[1].packet_status == "BLOCKED_NOT_FUNDED"
    assert packets[1].execution_blocker is None
    assert "deepseek" not in json.dumps([packet.public_record() for packet in packets])


def test_canonical_packet_set_blocks_execution_on_unfunded_qwen() -> None:
    with pytest.raises(P15CBenchmarkError) as caught:
        assert_p15c_provider_packets_execution_eligible(
            load_p15c_provider_packets(PACKET_CONFIG)
        )

    assert caught.value.code == "PROVIDER_PACKET_BLOCKED"


def test_direct_executor_blocks_before_policy_ledger_credentials_or_transport(
    tmp_path: Path,
) -> None:
    packets = load_p15c_provider_packets(PACKET_CONFIG)
    cases = _cases()
    target = _target_packet(cases[1], tmp_path)
    forbidden = _ForbiddenPrivateBoundary()
    executor = P15CBenchmarkExecutor(
        repository_root=ROOT,
        packet_config_path=PACKET_CONFIG,
        policy_path=tmp_path / "must-not-be-read.json",
        credential_resolver=forbidden,  # type: ignore[arg-type]
        ledger=forbidden,  # type: ignore[arg-type]
        transport=forbidden,  # type: ignore[arg-type]
        target_packet=target,
    )

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.preflight(packets, cases)
    assert caught.value.code == "PROVIDER_PACKET_BLOCKED"

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.execute(packets[1], cases[0])
    assert caught.value.code == "PROVIDER_PACKET_BLOCKED"


def test_deterministic_corpus_is_exact_content_addressed_twelve_file_set() -> None:
    case = load_p15c_deterministic_case(ROOT, PACKET_CONFIG)

    assert case.case_id == "deterministic-corpus"
    assert len(case.files) == 12
    assert tuple(item.path for item in case.files) == tuple(
        sorted(item.path for item in case.files)
    )
    assert case.expected_finding_paths <= case.allowed_paths
    assert case.private_target is False


def test_private_case_defers_provider_transfer_to_exact_route(tmp_path: Path) -> None:
    private_case = _cases()[1]
    packet = _target_packet(private_case, tmp_path)

    built = build_p15c_private_case(packet, private_case.files)
    assert built.private_target is True
    assert built.allowed_paths == {"src/private.py"}

    blocked = P15CTargetPacket(
        **{
            **packet.__dict__,
            "provider_transfer_authority_by_provider": {
                "deepseek": True,
                "openai": False,
                "qwen": False,
            },
        }
    )
    built_without_openai_transfer = build_p15c_private_case(blocked, private_case.files)
    assert built_without_openai_transfer.case_sha256 == built.case_sha256


def test_requests_use_provider_specific_structured_json_and_no_tools() -> None:
    packets = load_p15c_provider_packets(PACKET_CONFIG)
    case = _cases()[0]

    openai = json.loads(build_p15c_request(packets[0], case)[0])
    qwen = json.loads(build_p15c_request(packets[1], case)[0])

    assert openai["model"] == "gpt-5.6-luna"
    assert openai["store"] is False
    assert openai["tools"] == []
    assert openai["text"]["format"]["type"] == "json_schema"
    assert openai["text"]["format"]["strict"] is True
    assert qwen["model"] == "qwen3.7-plus-2026-05-26"
    assert qwen["response_format"] == {"type": "json_object"}
    assert qwen["enable_thinking"] is False
    assert qwen["stream"] is False
    assert qwen["tools"] == []
    assert "operator/private-target" not in json.dumps(openai)
    assert "operator/private-target" not in json.dumps(qwen)


def test_qwen_exact_snapshot_request_response_and_cny_cost_are_bounded(
    tmp_path: Path,
) -> None:
    repository, _, _ = _sealed_repository(tmp_path / "qwen-sealed", ("openai", "qwen"))
    packets = load_p15c_provider_packets(
        repository / "config/p15c_execution_packet_freeze_v1.yaml"
    )
    assert tuple(packet.provider_id for packet in packets) == ("openai", "qwen")
    qwen = packets[1]
    assert qwen.exact_model_version == "qwen3.7-plus-2026-05-26"
    assert (qwen.host, qwen.path) == (
        "dashscope.aliyuncs.com",
        "/compatible-mode/v1/chat/completions",
    )
    assert qwen.billing_currency == "CNY"
    assert qwen.per_attempt_hard_cap_native_microunits == 250_000

    case = _cases()[0]
    request = json.loads(build_p15c_request(qwen, case)[0])
    assert request["model"] == "qwen3.7-plus-2026-05-26"
    assert request["max_completion_tokens"] == 2_048
    assert request["response_format"] == {"type": "json_object"}
    assert request["enable_thinking"] is False
    assert request["stream"] is False
    assert request["tools"] == []

    parsed = parse_p15c_provider_response(
        qwen, _provider_response("qwen", next(iter(case.allowed_paths)))
    )
    assert (
        calculate_p15c_cost_micro_usd(qwen, parsed, cny_to_micro_usd_ceiling=1_000_000)
        == 280
    )
    with pytest.raises(P15CBenchmarkError) as caught:
        calculate_p15c_cost_micro_usd(qwen, parsed, cny_to_micro_usd_ceiling=999_999)
    assert caught.value.code == "CURRENCY_CEILING_INVALID"

    with pytest.raises(P15CBenchmarkError) as caught:
        calculate_p15c_cost_micro_usd(
            qwen,
            parsed,
            cny_to_micro_usd_ceiling=20_000_001,
        )
    assert caught.value.code == "CURRENCY_CEILING_INVALID"


def test_selected_qwen_rejects_stale_worst_case_native_ceiling(
    tmp_path: Path,
) -> None:
    source = yaml.safe_load(PACKET_CONFIG.read_text(encoding="utf-8"))
    source["execution_matrix"] = {
        "provider_ids": ["openai", "qwen"],
        "case_ids": ["deterministic-corpus", "private-target"],
        "max_provider_invocations": 4,
    }
    qwen = next(
        packet
        for packet in source["provider_packets"]
        if packet["provider_id"] == "qwen"
    )
    qwen["pricing_snapshot"]["calculated_worst_case_micro_cny"] = 192_000
    candidate = tmp_path / "stale-qwen-price.yaml"
    candidate.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")

    with pytest.raises(P15CBenchmarkError) as caught:
        load_p15c_provider_packets(candidate)

    assert caught.value.code == "PACKET_PRICE_DRIFT"


def test_execution_matrix_rejects_non_string_provider_ids(tmp_path: Path) -> None:
    source = yaml.safe_load(PACKET_CONFIG.read_text(encoding="utf-8"))
    source["execution_matrix"] = {
        "provider_ids": [{"provider": "openai"}, "qwen"],
        "case_ids": ["deterministic-corpus", "private-target"],
        "max_provider_invocations": 4,
    }
    candidate = tmp_path / "invalid-matrix.yaml"
    candidate.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")

    with pytest.raises(P15CBenchmarkError) as caught:
        load_p15c_provider_packets(candidate)

    assert caught.value.code == "PACKET_MATRIX_INVALID"


def test_request_budget_uses_conservative_byte_ceiling() -> None:
    packet = load_p15c_provider_packets(PACKET_CONFIG)[0]
    oversized = _snapshot("src/oversized.py", "x" * 66_000)
    case = P15CBenchmarkCase(
        case_id="deterministic-corpus",
        files=(oversized,),
        case_sha256=hashlib.sha256(b"oversized").hexdigest(),
        expected_finding_paths=frozenset(),
        private_target=False,
    )

    with pytest.raises(P15CBenchmarkError) as caught:
        build_p15c_request(packet, case)

    assert caught.value.code == "REQUEST_INPUT_BUDGET"


@pytest.mark.parametrize("provider_index", [0, 1])
def test_provider_response_parsing_metrics_and_cost_are_redacted_and_bounded(
    provider_index: int,
) -> None:
    packet = load_p15c_provider_packets(PACKET_CONFIG)[provider_index]
    case = _cases()[0]
    parsed = parse_p15c_provider_response(
        packet, _provider_response(packet.provider_id, next(iter(case.allowed_paths)))
    )
    metrics = build_p15c_metrics(parsed.output, case)
    cost = calculate_p15c_cost_micro_usd(
        packet,
        parsed,
        cny_to_micro_usd_ceiling=(1_000_000 if packet.provider_id == "qwen" else None),
    )

    assert parsed.input_tokens == 100
    assert parsed.output_tokens == 10
    assert metrics["schema_valid"] is True
    assert metrics["grounded_path_ratio_micros"] == 1_000_000
    assert metrics["expected_path_recall_micros"] == 1_000_000
    assert cost == (29 if packet.provider_id == "openai" else 280)

    drifted = json.loads(
        _provider_response(packet.provider_id, next(iter(case.allowed_paths))).body
    )
    drifted["model"] = "unexpected-model"
    with pytest.raises(P15CBenchmarkError) as caught:
        parse_p15c_provider_response(
            packet,
            P15CHTTPResponse(200, {}, json.dumps(drifted).encode("utf-8")),
        )
    assert caught.value.code == "PROVIDER_MODEL_DRIFT"


def test_preflight_resolves_references_but_performs_no_transport(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, resolver, ledger = _executor_fixture(tmp_path, transport)

    record = executor.preflight(packets, cases)

    assert record["status"] == "PASS"
    assert record["total_budget_micro_usd"] == 100_000
    assert record["planned_provider_invocations"] == 4
    assert record["provider_invocations"] == 0
    assert record["network_operations"] == 0
    assert record["credential_references_resolved"] == 2
    assert record["credential_values_recorded"] == 0
    assert record["target_identity_recorded"] is False
    assert len(resolver.calls) == 2
    assert transport.calls == []
    assert ledger.attempts() == ()


def test_nonempty_ledger_blocks_preflight_before_credential_resolution(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, resolver, ledger = _executor_fixture(tmp_path, transport)
    ledger.reserve(
        attempt_id="prior-attempt",
        provider_id="deepseek",
        case_id="deterministic-corpus",
        request_sha256=hashlib.sha256(b"prior").hexdigest(),
        reservation_micro_usd=25_000,
        total_budget_micro_usd=100_000,
        provider_budget_micro_usd=50_000,
    )
    ledger.release_without_transport("prior-attempt")

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.preflight(packets, cases)

    assert caught.value.code == "LEDGER_NOT_EMPTY"
    assert resolver.calls == []
    assert transport.calls == []


def test_total_private_budget_must_cover_all_four_conservative_reservations(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, resolver, _ = _executor_fixture(tmp_path, transport)
    policy_path = tmp_path / "private" / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["total_budget_micro_usd"] = 99_999
    _owner_json(policy_path, policy)

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.preflight(packets, cases)

    assert caught.value.code == "TOTAL_POLICY_BUDGET"
    assert resolver.calls == []
    assert transport.calls == []


def test_executor_rebinds_packet_case_and_target_digest_before_transport(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, resolver, _ = _executor_fixture(tmp_path, transport)

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.execute(replace(packets[0], model_id="drifted-model"), cases[0])
    assert caught.value.code == "PROVIDER_PACKET_DRIFT"

    with pytest.raises(P15CBenchmarkError) as caught:
        executor.execute(
            packets[0],
            replace(cases[0], case_sha256=hashlib.sha256(b"drift").hexdigest()),
        )
    assert caught.value.code == "BENCHMARK_CASE_DRIFT"

    policy_path = tmp_path / "private" / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["expected_target_packet_sha256"] = hashlib.sha256(b"other").hexdigest()
    _owner_json(policy_path, policy)
    with pytest.raises(P15CBenchmarkError) as caught:
        executor.execute(packets[0], cases[0])
    assert caught.value.code == "TARGET_PACKET_POLICY_DRIFT"
    assert resolver.calls == []
    assert transport.calls == []


def test_executor_runs_exact_fake_matrix_and_blocks_replay(tmp_path: Path) -> None:
    transport = _FakeTransport()
    executor, packets, cases, _, ledger = _executor_fixture(tmp_path, transport)
    executor.preflight(packets, cases)

    outcomes = [executor.execute(packet, case) for packet in packets for case in cases]

    assert len(outcomes) == 4
    assert all(outcome.status == "PASS" for outcome in outcomes)
    assert len(transport.calls) == 4
    assert all(call["authorization_present"] for call in transport.calls)
    assert sum(outcome.charged_micro_usd for outcome in outcomes) == 126
    public = json.dumps(
        [outcome.public_record() for outcome in outcomes], sort_keys=True
    )
    assert "unit-test-credential-value" not in public
    assert "operator/private-target" not in public
    assert "src/private.py" not in public
    assert all(item.status == "SETTLED" for item in ledger.attempts())

    replay = executor.execute(packets[0], cases[0])
    assert replay.status == "SETTLED"
    assert replay.failure_code == "LEDGER_REPLAY_BLOCKED"
    assert len(transport.calls) == 4


def test_executor_runs_openai_qwen_matrix_with_fake_transport_only(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, resolver, ledger = _executor_fixture(
        tmp_path, transport, ("openai", "qwen")
    )

    preflight = executor.preflight(packets, cases)
    outcomes = [executor.execute(packet, case) for packet in packets for case in cases]

    assert preflight["planned_provider_invocations"] == 4
    assert tuple(packet.provider_id for packet in packets) == ("openai", "qwen")
    assert len(resolver.calls) == 6
    assert len(transport.calls) == 4
    assert all(outcome.status == "PASS" for outcome in outcomes)
    assert sum(outcome.charged_micro_usd for outcome in outcomes) == 618
    assert all(item.status == "SETTLED" for item in ledger.attempts())
    public = json.dumps([outcome.public_record() for outcome in outcomes])
    assert "unit-test-credential-value" not in public
    assert "operator/private-target" not in public
    assert "src/private.py" not in public
    assert all(call["authorization_present"] for call in transport.calls)


def test_cancellation_blocks_before_fake_transport_and_releases_budget(
    tmp_path: Path,
) -> None:
    transport = _FakeTransport()
    executor, packets, cases, _, ledger = _executor_fixture(tmp_path, transport)

    outcome = executor.execute(packets[0], cases[0], cancellation=_Cancelled())

    assert outcome.status == "CANCELLED"
    assert outcome.charged_micro_usd == 0
    assert transport.calls == []
    assert ledger.attempts()[0].status == "RELEASED"


def test_transport_failure_is_not_retried_and_charges_full_reservation(
    tmp_path: Path,
) -> None:
    transport = _FailingTransport()
    executor, packets, cases, _, ledger = _executor_fixture(tmp_path, transport)

    outcome = executor.execute(packets[1], cases[0])

    assert outcome.status == "ERROR"
    assert outcome.failure_code == "TRANSPORT_TIMEOUT"
    assert outcome.charged_micro_usd == 25_000
    assert transport.calls == 1
    assert ledger.attempts()[0].status == "UNCERTAIN"


def test_direct_transport_routes_are_fixed_and_source_has_no_proxy_or_retry() -> None:
    assert P15CDirectTLSTransport._allowed_routes == {
        ("api.deepseek.com", "/chat/completions"),
        ("api.openai.com", "/v1/responses"),
        (
            "dashscope.aliyuncs.com",
            "/compatible-mode/v1/chat/completions",
        ),
    }
    source = Path("src/tool_system/ai_worker/p15c_benchmark.py").read_text(
        encoding="utf-8"
    )
    assert "Proxy" not in source
    assert "HTTP_PROXY" not in source
    assert "HTTPS_PROXY" not in source
    assert "requests." not in source
    assert "urllib.request" not in source
