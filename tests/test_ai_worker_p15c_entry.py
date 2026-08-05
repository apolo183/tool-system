from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tool_system.ai_worker import p15c_entry
from tool_system.ai_worker.p15c_controls import (
    P15C_DEFAULT_CREDENTIALS_PATH,
    P15C_DEFAULT_LEDGER_PATH,
    P15C_DEFAULT_SETTINGS_PATH,
    P15C_DEFAULT_TARGET_PACKET_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET_CONFIG = ROOT / "config" / "p15c_execution_packet_freeze_v1.yaml"


def _output(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_packet_only_is_public_and_performs_zero_private_or_live_operations(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("packet-only mode crossed a private or live boundary")

    monkeypatch.setattr(p15c_entry, "load_target_packet", forbidden)
    monkeypatch.setattr(p15c_entry, "load_target_snapshot", forbidden)
    monkeypatch.setattr(p15c_entry, "OwnerOnlyCredentialResolver", forbidden)
    monkeypatch.setattr(p15c_entry, "P15CUsageLedger", forbidden)
    monkeypatch.setattr(p15c_entry, "P15CDirectTLSTransport", forbidden)

    result = p15c_entry.main(
        [
            "--packet-only",
            "--repository-root",
            str(ROOT),
            "--packet-config",
            str(PACKET_CONFIG),
        ]
    )
    record = _output(capsys)

    assert result == 0
    assert record["status"] == "PASS"
    assert record["mode"] == "packet-only"
    assert [packet["provider_id"] for packet in record["packets"]] == [
        "deepseek",
        "openai",
        "qwen",
    ]
    assert record["catalog_grants_execution_authority"] is False
    assert record["selection_source"] == (
        "repository_external_operator_configuration"
    )
    assert record["packets"][0]["packet_status"] == (
        "BLOCKED_EXACT_VERSION_UNPINNABLE"
    )
    assert record["packets"][1]["exact_model_version"] == "gpt-5.6-luna"
    assert record["packets"][1]["packet_status"] == "FROZEN_NOT_ACTIVATED"
    assert record["packets"][2]["exact_model_version"] == (
        "qwen3.7-plus-2026-05-26"
    )
    assert record["packets"][2]["packet_status"] == "BLOCKED_NOT_FUNDED"
    for field in (
        "provider_invocations",
        "network_operations",
        "credential_resolver_invocations",
        "credential_value_accesses",
        "target_snapshot_reads",
        "benchmark_executions",
        "target_mutations",
        "production_operations",
        "cleanup_operations",
        "rollback_operations",
    ):
        assert record[field] == 0


def test_disabled_api_mode_blocks_before_credentials_targets_or_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("disabled API mode crossed a private or live boundary")

    private = tmp_path / "private"
    private.mkdir()
    private.chmod(0o700)
    settings = private / "settings.toml"
    settings.write_text(
        (ROOT / "examples/operator_config/tool_system_settings.example.toml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    settings.chmod(0o600)

    monkeypatch.setattr(p15c_entry, "load_target_packet", forbidden)
    monkeypatch.setattr(p15c_entry, "load_target_snapshot", forbidden)
    monkeypatch.setattr(p15c_entry, "OwnerOnlyCredentialResolver", forbidden)
    monkeypatch.setattr(p15c_entry, "P15CUsageLedger", forbidden)
    monkeypatch.setattr(p15c_entry, "P15CDirectTLSTransport", forbidden)
    result = p15c_entry.main(
        [
            "--preflight",
            "--repository-root",
            str(ROOT),
            "--packet-config",
            str(PACKET_CONFIG),
            "--settings",
            str(settings),
        ]
    )
    record = _output(capsys)

    assert result == 2
    assert record == {
        "credential_values_recorded": 0,
        "failure_code": "POLICY_DISABLED",
        "private_target_identity_recorded": False,
        "private_target_paths_recorded": False,
        "raw_provider_outputs_recorded": 0,
        "status": "BENCHMARK_BLOCKED",
        "target_mutations": 0,
    }


def test_parser_defaults_to_repository_external_operator_files() -> None:
    arguments = p15c_entry.build_parser().parse_args(["--preflight"])

    assert arguments.settings == str(P15C_DEFAULT_SETTINGS_PATH)
    assert arguments.credentials == str(P15C_DEFAULT_CREDENTIALS_PATH)
    assert arguments.target_packet == str(P15C_DEFAULT_TARGET_PACKET_PATH)
    assert arguments.ledger == str(P15C_DEFAULT_LEDGER_PATH)
    for value in (
        arguments.settings,
        arguments.credentials,
        arguments.target_packet,
        arguments.ledger,
    ):
        assert str(value).startswith("~/")


def test_parser_requires_one_explicit_mode() -> None:
    parser = p15c_entry.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--packet-only", "--execute"])


def test_entry_source_is_generic_and_does_not_embed_target_identity() -> None:
    source = Path("src/tool_system/ai_worker/p15c_entry.py").read_text(encoding="utf-8")

    project_token = "finance" + "-us"
    repository_token = f"apolo183/{project_token}"
    assert project_token not in source
    assert repository_token not in source
    assert "subprocess" not in source
    assert "os.environ" not in source
    assert "qwen" not in source.lower()
    assert "private_target_identity_recorded" in source
    assert "private_target_paths_recorded" in source


def test_source_stage_state_and_exact_scope_remain_non_accepting_and_generic() -> None:
    state = yaml.safe_load(
        (ROOT / "docs/tool_system_project_state_v1.yaml").read_text(encoding="utf-8")
    )
    manifest = yaml.safe_load(
        (
            ROOT
            / "examples/task_manifests/tool_system_p15c_runtime_control_plane_v1.yaml"
        ).read_text(encoding="utf-8")
    )
    plan = yaml.safe_load(
        (
            ROOT
            / "examples/change_plans/tool_system_p15c_runtime_control_plane_v1.yaml"
        ).read_text(encoding="utf-8")
    )
    report = (
        ROOT / "docs/reports/p15c_runtime_control_plane_implementation.md"
    ).read_text(encoding="utf-8")

    current = state["current_phase"]
    runtime = state["p15c_runtime_control_plane"]
    assert current["next_stage_authorized"] is True
    assert current["active_stage"] == "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK"
    assert runtime["module"]["module_version"] == "1.8.1"
    assert runtime["configured_provider_ids"] == ["deepseek", "openai"]
    assert runtime["execution_eligible_provider_ids"] == ["openai"]
    assert runtime["exact_matrix_execution_eligible"] is False
    assert runtime["execution_blocker"] == "PROVIDER_EXACT_VERSION_UNPINNABLE"
    assert runtime["qwen_enabled"] is False
    assert runtime["p15c_stage_accepted"] is False
    assert runtime["p15d_authorized"] is False
    assert set(runtime["source_stage_evidence"].values()) == {0}
    assert len(manifest["allowed_files"]) == 26
    assert set(manifest["allowed_files"]) == set(plan["changed_files"])
    assert "P15C_RUNTIME_CONTROL_PLANE_SOURCE_IMPLEMENTED_FAKE_TRANSPORT_ONLY" in report
    public_source = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in (
            "src/tool_system/ai_worker/p15c_benchmark.py",
            "src/tool_system/ai_worker/p15c_controls.py",
            "src/tool_system/ai_worker/p15c_entry.py",
            "docs/reports/p15c_runtime_control_plane_implementation.md",
        )
    )
    project_token = "finance" + "-us"
    repository_token = f"apolo183/{project_token}"
    assert project_token not in public_source
    assert repository_token not in public_source
