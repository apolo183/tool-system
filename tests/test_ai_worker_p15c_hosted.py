from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import stat
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tool_system.ai_worker.p15c_controls import (
    P15C_AUTHORIZATION_ID,
    P15CControlError,
    load_execution_policy,
    load_target_packet,
    load_target_snapshot,
)
from tool_system.ai_worker.p15c_hosted import (
    P15CHostedBridgeError,
    main,
    materialize_hosted_private_inputs,
)


def _git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def _control(files: dict[str, bytes]) -> dict[str, object]:
    inventory = [
        {
            "path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "git_blob_sha": _git_blob_sha(payload),
            "size_bytes": len(payload),
        }
        for path, payload in sorted(files.items())
    ]
    return {
        "schema_version": 1,
        "authorization_id": P15C_AUTHORIZATION_ID,
        "expires_after_seconds": 600,
        "execution_policy": {
            "schema_version": 1,
            "enabled": True,
            "total_budget_micro_usd": 200_000,
            "provider_enabled": {
                "deepseek": True,
                "openai": True,
                "qwen": False,
            },
            "provider_budget_micro_usd": {
                "deepseek": 100_000,
                "openai": 100_000,
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
        },
        "target_packet": {
            "schema_version": 1,
            "packet_id": "operator-private-target-v1",
            "repository_identity": "example-owner/example-repository",
            "visibility": "private",
            "branch": "main",
            "exact_commit": "1" * 40,
            "exact_file_allowlist": [item["path"] for item in inventory],
            "content_addressed_inventory": inventory,
            "durable_module_contract": {
                "contract_id": "example-module",
                "contract_version": "1.0.0",
                "read_only": True,
            },
            "inventory_read_authority": True,
            "benchmark_read_authority": True,
            "provider_transfer_authority_by_provider": {
                "deepseek": True,
                "openai": True,
                "qwen": False,
            },
            "mutation_authority": False,
        },
    }


def _bundle(
    control: dict[str, object],
    files: dict[str, bytes],
    *,
    extra_members: tuple[tarfile.TarInfo, ...] = (),
) -> str:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        payloads = {
            "control.json": (
                json.dumps(control, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode(),
            **{f"snapshot/{path}": payload for path, payload in files.items()},
        }
        for name, payload in sorted(payloads.items()):
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            member.mode = 0o600
            archive.addfile(member, io.BytesIO(payload))
        for member in extra_members:
            archive.addfile(member)
    return base64.b64encode(gzip.compress(raw.getvalue(), mtime=0)).decode()


def _fixture() -> tuple[dict[str, bytes], dict[str, object], str]:
    files = {
        "README.md": b"# Example\n",
        "src/module.py": b"VALUE = 1\n",
    }
    control = _control(files)
    return files, control, _bundle(control, files)


def test_materialize_hosted_private_inputs_is_owner_only_and_exact(
    tmp_path: Path,
) -> None:
    files, _, bundle = _fixture()
    root = tmp_path / "private"
    materialized = materialize_hosted_private_inputs(
        bundle_base64=bundle,
        deepseek_api_key="deepseek-test-value",
        openai_api_key="openai-test-value",
        private_root=root,
        expected_commit="2" * 40,
        expected_tree="3" * 40,
        now=datetime(2026, 8, 4, 1, 2, 3, tzinfo=timezone.utc),
    )

    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    for path in (
        materialized.policy_path,
        materialized.credential_path,
        materialized.target_packet_path,
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert not materialized.ledger_path.exists()
    packet = load_target_packet(materialized.target_packet_path)
    snapshot = load_target_snapshot(packet)
    policy = load_execution_policy(materialized.policy_path)
    assert tuple(item.path for item in snapshot) == tuple(sorted(files))
    assert policy.expected_tool_system_commit == "2" * 40
    assert policy.expected_tool_system_tree == "3" * 40
    assert policy.expected_target_packet_sha256 == packet.packet_sha256
    assert policy.expires_at_utc == "2026-08-04T01:12:03Z"
    assert materialized.target_file_count == 2
    assert materialized.target_total_bytes == sum(map(len, files.values()))

    public = json.dumps(materialized.public_record(), sort_keys=True)
    assert "deepseek-test-value" not in public
    assert "openai-test-value" not in public
    assert "example-owner" not in public
    assert "src/module.py" not in public
    assert materialized.public_record()["credential_values_recorded"] == 0
    assert materialized.public_record()["network_operations"] == 0


def test_cli_reads_named_secrets_without_printing_values_or_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, _, bundle = _fixture()
    monkeypatch.setenv("BUNDLE_REF", bundle)
    monkeypatch.setenv("DEEPSEEK_REF", "deepseek-test-value")
    monkeypatch.setenv("OPENAI_REF", "openai-test-value")
    root = tmp_path / "private"

    code = main(
        (
            "--private-root",
            str(root),
            "--expected-commit",
            "4" * 40,
            "--expected-tree",
            "5" * 40,
            "--bundle-env",
            "BUNDLE_REF",
            "--deepseek-key-env",
            "DEEPSEEK_REF",
            "--openai-key-env",
            "OPENAI_REF",
        )
    )
    output = capsys.readouterr().out
    receipt = json.loads(output)
    assert code == 0
    assert receipt["status"] == "PASS"
    assert receipt["credential_secret_references_resolved"] == 2
    assert "deepseek-test-value" not in output
    assert "openai-test-value" not in output
    assert "example-owner" not in output
    assert "src/module.py" not in output


def test_missing_secret_fails_before_private_root_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, _, bundle = _fixture()
    monkeypatch.setenv("BUNDLE_REF", bundle)
    monkeypatch.delenv("DEEPSEEK_REF", raising=False)
    monkeypatch.setenv("OPENAI_REF", "openai-test-value")
    root = tmp_path / "private"
    code = main(
        (
            "--private-root",
            str(root),
            "--expected-commit",
            "4" * 40,
            "--expected-tree",
            "5" * 40,
            "--bundle-env",
            "BUNDLE_REF",
            "--deepseek-key-env",
            "DEEPSEEK_REF",
            "--openai-key-env",
            "OPENAI_REF",
        )
    )
    receipt = json.loads(capsys.readouterr().out)
    assert code == 2
    assert receipt["failure_code"] == "HOSTED_SECRET_UNAVAILABLE"
    assert not root.exists()


def test_bundle_rejects_path_traversal_without_writing_outside_root(
    tmp_path: Path,
) -> None:
    files, control, _ = _fixture()
    escaped = tarfile.TarInfo("snapshot/../escaped.txt")
    escaped.size = 1
    root = tmp_path / "private"
    with pytest.raises(P15CHostedBridgeError, match="member path") as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, files, extra_members=(escaped,)),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=root,
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert error.value.code == "HOSTED_BUNDLE_PATH"
    assert not root.exists()
    assert not (tmp_path / "escaped.txt").exists()


def test_bundle_rejects_symlink_member() -> None:
    files, control, _ = _fixture()
    link = tarfile.TarInfo("snapshot/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "README.md"
    with pytest.raises(P15CHostedBridgeError) as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, files, extra_members=(link,)),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=Path("/unused"),
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert error.value.code == "HOSTED_BUNDLE_MEMBER_TYPE"


def test_bundle_rejects_file_set_drift_before_private_root_creation(
    tmp_path: Path,
) -> None:
    files, control, _ = _fixture()
    missing = {"README.md": files["README.md"]}
    root = tmp_path / "private"
    with pytest.raises(P15CHostedBridgeError) as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, missing),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=root,
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert error.value.code == "HOSTED_BUNDLE_FILE_SET"
    assert not root.exists()


def test_bundle_rejects_duplicate_member_before_private_root_creation(
    tmp_path: Path,
) -> None:
    files, control, _ = _fixture()
    duplicate = tarfile.TarInfo("control.json")
    root = tmp_path / "private"
    with pytest.raises(P15CHostedBridgeError) as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, files, extra_members=(duplicate,)),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=root,
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert error.value.code == "HOSTED_BUNDLE_DUPLICATE"
    assert not root.exists()


def test_bundle_rejects_expanded_size_and_member_count_ceilings(
    tmp_path: Path,
) -> None:
    oversized_files = {"large.txt": b"x" * (2 * 1024 * 1024 + 1)}
    oversized_control = _control(oversized_files)
    many_files = {f"src/file-{index:02d}.py": b"x\n" for index in range(65)}
    many_control = _control(many_files)
    for bundle, expected_code in (
        (_bundle(oversized_control, oversized_files), "HOSTED_BUNDLE_TOO_LARGE"),
        (_bundle(many_control, many_files), "HOSTED_BUNDLE_MEMBER_COUNT"),
    ):
        with pytest.raises(P15CHostedBridgeError) as error:
            materialize_hosted_private_inputs(
                bundle_base64=bundle,
                deepseek_api_key="deepseek-test-value",
                openai_api_key="openai-test-value",
                private_root=tmp_path / expected_code,
                expected_commit="2" * 40,
                expected_tree="3" * 40,
            )
        assert error.value.code == expected_code


def test_bundle_rejects_invalid_control_before_private_root_creation(
    tmp_path: Path,
) -> None:
    files, control, _ = _fixture()
    control["schema_version"] = 2
    root = tmp_path / "private"
    with pytest.raises(P15CHostedBridgeError) as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, files),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=root,
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert error.value.code == "HOSTED_CONTROL_SCHEMA"
    assert not root.exists()


def test_invalid_source_sha_and_credential_fail_closed(tmp_path: Path) -> None:
    _, _, bundle = _fixture()
    for key, commit, expected_code in (
        ("contains whitespace", "2" * 40, "HOSTED_CREDENTIAL_INVALID"),
        ("deepseek-test-value", "not-a-sha", "HOSTED_SOURCE_SHA"),
    ):
        with pytest.raises(P15CHostedBridgeError) as error:
            materialize_hosted_private_inputs(
                bundle_base64=bundle,
                deepseek_api_key=key,
                openai_api_key="openai-test-value",
                private_root=tmp_path / expected_code,
                expected_commit=commit,
                expected_tree="3" * 40,
            )
        assert error.value.code == expected_code


def test_policy_above_public_ceiling_is_rejected(tmp_path: Path) -> None:
    files, control, _ = _fixture()
    policy = control["execution_policy"]
    assert isinstance(policy, dict)
    policy["total_budget_micro_usd"] = 20_000_001
    policy["provider_budget_micro_usd"] = {
        "deepseek": 10_000_000,
        "openai": 10_000_000,
        "qwen": 0,
    }
    root = tmp_path / "private"
    with pytest.raises(P15CControlError) as error:
        materialize_hosted_private_inputs(
            bundle_base64=_bundle(control, files),
            deepseek_api_key="deepseek-test-value",
            openai_api_key="openai-test-value",
            private_root=root,
            expected_commit="2" * 40,
            expected_tree="3" * 40,
        )
    assert getattr(error.value, "code", None) == "POLICY_BUDGET_ABOVE_PUBLIC_CEILING"
    assert root.exists()
    assert not (root / "credentials.toml").exists()
