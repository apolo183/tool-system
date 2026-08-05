from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tool_system.ai_worker.p15c_controls import (
    P15C_AUTHORIZATION_ID,
    OwnerOnlyCredentialResolver,
    P15CControlError,
    P15CUsageLedger,
    build_execution_source_seal,
    load_execution_policy,
    load_target_packet,
    load_target_snapshot,
)


def _owner_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def _owner_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    path.chmod(0o600)
    return path


def _owner_policy_toml(path: Path, record: dict[str, object]) -> Path:
    provider_enabled = record["provider_enabled"]
    provider_budget = record["provider_budget_micro_usd"]
    provider_transfer = record["provider_transfer_enabled"]
    assert isinstance(provider_enabled, dict)
    assert isinstance(provider_budget, dict)
    assert isinstance(provider_transfer, dict)

    def boolean(value: object) -> str:
        assert isinstance(value, bool)
        return "true" if value else "false"

    currency_lines = (
        (f"cny_to_micro_usd_ceiling = {record['cny_to_micro_usd_ceiling']}",)
        if "cny_to_micro_usd_ceiling" in record
        else ()
    )

    path.write_text(
        "\n".join(
            (
                "[p15c]",
                f"schema_version = {record['schema_version']}",
                f'authorization_id = "{record["authorization_id"]}"',
                f"enabled = {boolean(record['enabled'])}",
                f"total_budget_micro_usd = {record['total_budget_micro_usd']}",
                f'expires_at_utc = "{record["expires_at_utc"]}"',
                (
                    "expected_tool_system_commit = "
                    f'"{record["expected_tool_system_commit"]}"'
                ),
                (
                    "expected_tool_system_tree = "
                    f'"{record["expected_tool_system_tree"]}"'
                ),
                (
                    "expected_target_packet_sha256 = "
                    f'"{record["expected_target_packet_sha256"]}"'
                ),
                (
                    "private_repository_transfer_enabled = "
                    f"{boolean(record['private_repository_transfer_enabled'])}"
                ),
                'allowed_case_ids = ["deterministic-corpus", "private-target"]',
                f"max_provider_invocations = {record['max_provider_invocations']}",
                *currency_lines,
                "",
                "[p15c.provider_enabled]",
                *(
                    f"{name} = {boolean(provider_enabled[name])}"
                    for name in ("deepseek", "openai", "qwen")
                ),
                "",
                "[p15c.provider_budget_micro_usd]",
                *(
                    f"{name} = {provider_budget[name]}"
                    for name in ("deepseek", "openai", "qwen")
                ),
                "",
                "[p15c.provider_transfer_enabled]",
                *(
                    f"{name} = {boolean(provider_transfer[name])}"
                    for name in ("deepseek", "openai", "qwen")
                ),
                "",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


def _git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


def _policy_record(
    *, commit: str = "1" * 40, tree: str = "2" * 40
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "authorization_id": P15C_AUTHORIZATION_ID,
        "enabled": True,
        "total_budget_micro_usd": 20_000_000,
        "expires_at_utc": "2099-01-01T00:00:00Z",
        "expected_tool_system_commit": commit,
        "expected_tool_system_tree": tree,
        "expected_target_packet_sha256": hashlib.sha256(b"target-packet").hexdigest(),
        "provider_enabled": {"deepseek": True, "openai": True, "qwen": False},
        "provider_budget_micro_usd": {
            "deepseek": 50_000,
            "openai": 50_000,
            "qwen": 0,
        },
        "private_repository_transfer_enabled": True,
        "provider_transfer_enabled": {
            "deepseek": True,
            "openai": True,
            "qwen": False,
        },
        "allowed_case_ids": ["deterministic-corpus", "private-target"],
        "max_provider_invocations": 4,
        "cny_to_micro_usd_ceiling": 1_000_000,
    }


def _target_packet_record(snapshot: Path, content: bytes) -> dict[str, object]:
    relative = "src/example.py"
    return {
        "schema_version": 1,
        "packet_id": "operator-private-target-v1",
        "repository_identity": "operator/private-target",
        "visibility": "private",
        "branch": "main",
        "exact_commit": "3" * 40,
        "exact_file_allowlist": [relative],
        "content_addressed_inventory": [
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "git_blob_sha": _git_blob_sha(content),
                "size_bytes": len(content),
            }
        ],
        "durable_module_contract": {
            "contract_id": "operator-module-contract-v1",
            "contract_version": "1.0.0",
            "read_only": True,
        },
        "inventory_read_authority": True,
        "benchmark_read_authority": True,
        "provider_transfer_authority_by_provider": {
            "deepseek": True,
            "openai": True,
            "qwen": True,
        },
        "mutation_authority": False,
        "snapshot_root": str(snapshot),
    }


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _source_repository(root: Path) -> tuple[str, str]:
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "P15C Test")
    _git(root, "config", "user.email", "p15c-test@example.invalid")
    _git(root, "remote", "add", "origin", "https://github.com/apolo183/tool-system.git")
    critical = root / "src" / "control.py"
    critical.parent.mkdir(parents=True)
    critical.write_text("BOUND = True\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "test source seal")
    return _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")


def test_policy_is_exact_bounded_and_qwen_capable(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    policy_path = _owner_policy_toml(private / "settings.toml", _policy_record())

    policy = load_execution_policy(policy_path)

    assert policy.total_budget_micro_usd == 20_000_000
    assert policy.provider_enabled == {
        "deepseek": True,
        "openai": True,
        "qwen": False,
    }
    assert policy.provider_budget_micro_usd["qwen"] == 0
    assert policy.cny_to_micro_usd_ceiling == 1_000_000
    assert policy.max_provider_invocations == 4
    assert len(policy.policy_sha256) == 64
    policy.assert_active(now=datetime(2098, 12, 31, tzinfo=timezone.utc))
    with pytest.raises(P15CControlError) as caught:
        policy.assert_active(now=datetime(2099, 1, 1, tzinfo=timezone.utc))
    assert caught.value.code == "POLICY_EXPIRED"

    adjusted_budget = _policy_record()
    adjusted_budget["total_budget_micro_usd"] = 20_000_001
    _owner_policy_toml(policy_path, adjusted_budget)
    with pytest.raises(P15CControlError) as caught:
        load_execution_policy(policy_path)
    assert caught.value.code == "POLICY_BUDGET_ABOVE_AUTHORIZATION"

    qwen_enabled = _policy_record()
    qwen_enabled["provider_enabled"]["qwen"] = True  # type: ignore[index]
    qwen_enabled["provider_budget_micro_usd"]["qwen"] = 500_000  # type: ignore[index]
    qwen_enabled["provider_transfer_enabled"]["qwen"] = True  # type: ignore[index]
    _owner_policy_toml(policy_path, qwen_enabled)
    qwen_policy = load_execution_policy(policy_path)
    assert qwen_policy.provider_enabled["qwen"] is True
    assert qwen_policy.provider_transfer_enabled["qwen"] is True
    assert qwen_policy.provider_budget_micro_usd["qwen"] == 500_000

    unsafe_conversion = _policy_record()
    unsafe_conversion["cny_to_micro_usd_ceiling"] = 999_999
    _owner_policy_toml(policy_path, unsafe_conversion)
    with pytest.raises(P15CControlError) as caught:
        load_execution_policy(policy_path)
    assert caught.value.code == "INTEGER_FIELD"


def test_legacy_policy_remains_readable_only_with_qwen_disabled(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    policy_path = private / "settings.toml"
    legacy = _policy_record()
    legacy["schema_version"] = 1
    legacy.pop("cny_to_micro_usd_ceiling")
    _owner_policy_toml(policy_path, legacy)

    policy = load_execution_policy(policy_path)
    assert policy.cny_to_micro_usd_ceiling == 1_000_000

    legacy["provider_enabled"]["qwen"] = True  # type: ignore[index]
    _owner_policy_toml(policy_path, legacy)
    with pytest.raises(P15CControlError) as caught:
        load_execution_policy(policy_path)
    assert caught.value.code == "LEGACY_QWEN_NOT_DISABLED"


def test_private_controls_reject_permissive_permissions(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    policy_path = _owner_policy_toml(private / "settings.toml", _policy_record())
    policy_path.chmod(0o640)

    with pytest.raises(P15CControlError) as caught:
        load_execution_policy(policy_path)

    assert caught.value.code == "PRIVATE_FILE_PERMISSIONS"


def test_operator_settings_require_an_exact_p15c_table(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    settings = private / "settings.toml"
    settings.write_text("[other]\nenabled = false\n", encoding="utf-8")
    settings.chmod(0o600)

    with pytest.raises(P15CControlError) as caught:
        load_execution_policy(settings)

    assert caught.value.code == "POLICY_SETTINGS_SECTION"


def test_target_packet_loads_only_content_addressed_safe_snapshot(
    tmp_path: Path,
) -> None:
    private = _owner_directory(tmp_path / "private")
    snapshot = _owner_directory(private / "snapshot")
    source = snapshot / "src" / "example.py"
    source.parent.mkdir()
    content = b"def add(left, right):\n    return left + right\n"
    source.write_bytes(content)
    packet_path = _owner_json(
        private / "target.json", _target_packet_record(snapshot, content)
    )

    packet = load_target_packet(packet_path)
    loaded = load_target_snapshot(packet)

    assert packet.exact_commit == "3" * 40
    assert packet.mutation_authority is False
    assert tuple(item.path for item in loaded) == ("src/example.py",)
    assert loaded[0].content == content.decode("utf-8")

    source.write_text("changed\n", encoding="utf-8")
    with pytest.raises(P15CControlError) as caught:
        load_target_snapshot(packet)
    assert caught.value.code == "TARGET_SIZE_DRIFT"


def test_target_snapshot_blocks_secret_like_material(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    snapshot = _owner_directory(private / "snapshot")
    source = snapshot / "src" / "example.py"
    source.parent.mkdir()
    key_field = "api_" + "key"
    content = f'{key_field} = "unit-test-secret-value"\n'.encode()
    source.write_bytes(content)
    packet_path = _owner_json(
        private / "target.json", _target_packet_record(snapshot, content)
    )

    packet = load_target_packet(packet_path)
    with pytest.raises(P15CControlError) as caught:
        load_target_snapshot(packet)

    assert caught.value.code == "TARGET_SECRET_MATERIAL"


def test_credential_resolver_accepts_only_opaque_exact_references(
    tmp_path: Path,
) -> None:
    private = _owner_directory(tmp_path / "private")
    store = private / "credentials.toml"
    key_field = "api_" + "key"
    store.write_text(
        f"[providers.deepseek]\n{key_field} = 'deepseek-unit-value'\n"
        f"[providers.openai]\n{key_field} = 'openai-unit-value'\n"
        f"[providers.qwen]\n{key_field} = 'qwen-unit-value'\n",
        encoding="utf-8",
    )
    store.chmod(0o600)
    resolver = OwnerOnlyCredentialResolver(store)

    value = resolver.resolve(
        "private-control:credentials#providers.openai.api_key", "openai"
    )
    assert value == "openai-unit-value"

    qwen_value = resolver.resolve(
        "private-control:credentials#providers.qwen.api_key", "qwen"
    )
    assert qwen_value == "qwen-unit-value"

    with pytest.raises(P15CControlError) as caught:
        resolver.resolve("env:OPENAI_API_KEY", "openai")
    assert caught.value.code == "CREDENTIAL_REFERENCE_NOT_ALLOWED"
    assert "openai-unit-value" not in str(caught.value)


def test_usage_ledger_reserves_settles_releases_and_blocks_replay(
    tmp_path: Path,
) -> None:
    private = _owner_directory(tmp_path / "private")
    ledger = P15CUsageLedger(private / "usage.sqlite3")
    digest = hashlib.sha256(b"request").hexdigest()

    ledger.reserve(
        attempt_id="attempt-deepseek-deterministic",
        provider_id="deepseek",
        case_id="deterministic-corpus",
        request_sha256=digest,
        reservation_micro_usd=25_000,
        total_budget_micro_usd=100_000,
        provider_budget_micro_usd=50_000,
    )
    ledger.mark_transport_started("attempt-deepseek-deterministic")
    ledger.settle(
        "attempt-deepseek-deterministic",
        charged_micro_usd=123,
        output_sha256=hashlib.sha256(b"output").hexdigest(),
        input_tokens=100,
        output_tokens=10,
        duration_ms=25,
        metrics={"schema_valid": True, "finding_count": 0},
    )
    settled = ledger.attempt("attempt-deepseek-deterministic")
    assert settled is not None
    assert settled.status == "SETTLED"
    assert settled.charged_micro_usd == 123

    with pytest.raises(P15CControlError) as caught:
        ledger.reserve(
            attempt_id="attempt-deepseek-deterministic",
            provider_id="deepseek",
            case_id="deterministic-corpus",
            request_sha256=digest,
            reservation_micro_usd=25_000,
            total_budget_micro_usd=100_000,
            provider_budget_micro_usd=50_000,
        )
    assert caught.value.code == "LEDGER_REPLAY"

    ledger.reserve(
        attempt_id="attempt-openai-private",
        provider_id="openai",
        case_id="private-target",
        request_sha256=digest,
        reservation_micro_usd=25_000,
        total_budget_micro_usd=100_000,
        provider_budget_micro_usd=50_000,
    )
    ledger.release_without_transport("attempt-openai-private")
    assert ledger.attempt("attempt-openai-private").status == "RELEASED"  # type: ignore[union-attr]
    assert (private / "usage.sqlite3").stat().st_mode & 0o077 == 0


def test_usage_ledger_conservatively_charges_transport_failure(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    ledger = P15CUsageLedger(private / "usage.sqlite3")
    digest = hashlib.sha256(b"request").hexdigest()
    ledger.reserve(
        attempt_id="attempt-openai-deterministic",
        provider_id="openai",
        case_id="deterministic-corpus",
        request_sha256=digest,
        reservation_micro_usd=25_000,
        total_budget_micro_usd=25_000,
        provider_budget_micro_usd=25_000,
    )
    ledger.mark_transport_started("attempt-openai-deterministic")
    ledger.record_transport_failure("attempt-openai-deterministic", "TRANSPORT_TIMEOUT")

    failed = ledger.attempt("attempt-openai-deterministic")
    assert failed is not None
    assert failed.status == "UNCERTAIN"
    assert failed.charged_micro_usd == 25_000
    assert failed.failure_code == "TRANSPORT_TIMEOUT"


def test_usage_ledger_rejects_schema_shape_drift(tmp_path: Path) -> None:
    private = _owner_directory(tmp_path / "private")
    path = private / "usage.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE ledger_meta (singleton INTEGER PRIMARY KEY, schema_version INTEGER, instance_id TEXT)"
    )
    connection.execute("CREATE TABLE attempts (attempt_id TEXT PRIMARY KEY)")
    connection.execute("INSERT INTO ledger_meta VALUES (1, 1, 'old-shape')")
    connection.commit()
    connection.close()
    path.chmod(0o600)

    with pytest.raises(P15CControlError) as caught:
        P15CUsageLedger(path)

    assert caught.value.code == "LEDGER_SCHEMA"


def test_source_seal_requires_canonical_clean_exact_tree(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    head, tree = _source_repository(repository)

    seal = build_execution_source_seal(
        repository,
        expected_commit_sha=head,
        expected_tree_sha=tree,
        critical_source_paths=("src/control.py",),
    )
    assert seal.local_tree_sha == tree
    assert seal.clean_worktree is True
    assert len(seal.source_manifest_sha256) == 64

    (repository / "src" / "control.py").write_text("BOUND = False\n", encoding="utf-8")
    with pytest.raises(P15CControlError) as caught:
        build_execution_source_seal(
            repository,
            expected_commit_sha=head,
            expected_tree_sha=tree,
            critical_source_paths=("src/control.py",),
        )
    assert caught.value.code == "SOURCE_DIRTY"


def test_private_control_sources_do_not_reference_environment_credentials() -> None:
    source = Path("src/tool_system/ai_worker/p15c_controls.py").read_text(
        encoding="utf-8"
    )

    assert "os.environ" not in source
    assert "OPENAI_API_KEY" not in source
    assert "DEEPSEEK_API_KEY" not in source
    assert "QWEN_API_KEY" not in source
    assert os.path.basename(__file__) not in source
