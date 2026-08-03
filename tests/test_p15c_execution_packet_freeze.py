from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "config" / "p15c_execution_packet_freeze_v1.yaml"
REPORT = ROOT / "docs" / "reports" / "p15c_execution_packet_freeze.md"
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_execution_packet_freeze_v1.yaml"
)
PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_execution_packet_freeze_v1.yaml"
)
REPO_WRITE_POLICY = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy" / "autonomy_policy.yaml"

EXACT_FILES = {
    "REPO_MANIFEST.md",
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/reports/p15c_execution_packet_freeze.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_execution_packet_freeze_v1.yaml",
    "examples/task_manifests/tool_system_p15c_execution_packet_freeze_v1.yaml",
    "tests/test_p15c_execution_packet_freeze.py",
    "tests/test_repo_manifest.py",
}


def _aggregate_sha256(files: list[dict[str, str]]) -> str:
    payload = "".join(
        f"{item['git_blob_sha']} {item['path']}\n" for item in files
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def test_exact_task_pair_and_pre_entry_state_validate() -> None:
    manifest_result = validate_task_manifest(
        MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(PLAN)
    manifest = load_yaml_file(MANIFEST)
    plan = load_yaml_file(PLAN)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == EXACT_FILES
    assert set(plan["changed_files"]) == EXACT_FILES
    assert len(EXACT_FILES) == 8

    current = state["current_phase"]
    assert current["last_accepted_stage"] == (
        "P15B_ADAPTER_ROUTER_AND_PROFILER_FIXTURES"
    )
    assert current["next_stage"] == "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK"
    assert current["next_stage_authorized"] is False
    freeze = state["p15c_packet_freeze"]
    assert freeze["status"] == "accepted_pre_entry_freeze_no_execution_authority"
    assert freeze["provider_packets_enabled_for_live_execution"] == 0
    assert freeze["p15c_authorized"] is False
    assert freeze["p15c_stage_accepted"] is False
    assert state["authority_effect"] == "none"


def test_private_secret_policy_and_usage_state_are_separated() -> None:
    packets = load_yaml_file(PACKETS)
    control = packets["private_control_plane"]
    credentials = control["credential_store"]
    policy = control["execution_policy"]
    target = control["target_packet_store"]
    ledger = control["usage_ledger"]

    assert credentials["reference_id"] == "private-control:credentials"
    assert credentials["tracked_in_repository"] is False
    assert credentials["may_contain_execution_switch_or_budget"] is False
    assert policy["reference_id"] == "private-control:p15c-execution-policy"
    assert policy["tracked_in_repository"] is False
    assert policy["may_contain_credential_values"] is False
    assert policy["required_shape"]["enabled"] is False
    assert policy["required_shape"]["total_budget_usd"] == 20
    assert all(
        enabled is False
        for enabled in policy["required_shape"]["provider_enabled"].values()
    )
    assert target["reference_id"] == "private-control:p15c-target-packet"
    assert target["tracked_in_repository"] is False
    assert target["may_contain_credential_values"] is False
    assert target["public_serialization_allowed"] is False
    assert ledger["reference_id"] == "private-state:p15c-usage-ledger"
    assert ledger["human_policy_input"] is False

    budget = packets["budget_envelope"]
    assert budget["public_authorization_ceiling_micro_usd"] == 20_000_000
    assert budget["private_policy_default_micro_usd"] == 20_000_000
    assert budget["shared_across_provider_packets"] is True
    assert budget["qwen_current_allocation_micro_usd"] == 0
    assert budget["execution_spend_in_this_freeze_micro_usd"] == 0

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PACKETS, REPORT, PROJECT_STATE, MANIFEST, PLAN)
    )
    for forbidden in (
        r"OPENAI_API_KEY\s*=",
        r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{8,}",
        r"(?<![A-Za-z0-9_-])gho_[A-Za-z0-9]{8,}",
        r"api_key\s*=\s*[\"']",
    ):
        assert re.search(forbidden, combined) is None


def test_provider_packets_are_exact_bounded_and_not_activated() -> None:
    packets = load_yaml_file(PACKETS)
    providers = {
        packet["provider_id"]: packet for packet in packets["provider_packets"]
    }

    assert set(providers) == {"deepseek", "openai", "qwen"}
    assert providers["deepseek"]["packet_id"] == (
        "P15C-DEEPSEEK-V4-FLASH-READONLY-v1"
    )
    assert providers["deepseek"]["model_id"] == "deepseek-v4-flash"
    assert providers["deepseek"]["exact_model_version"] == (
        "DeepSeek-V4-Flash-0731"
    )
    assert providers["openai"]["packet_id"] == (
        "P15C-OPENAI-GPT-5.6-LUNA-READONLY-v1"
    )
    assert providers["openai"]["model_id"] == "gpt-5.6-luna"
    assert providers["qwen"]["packet_id"] == (
        "P15C-QWEN-3.7-PLUS-READONLY-v1"
    )
    assert providers["qwen"]["model_id"] == "qwen3.7-plus-2026-05-26"
    assert providers["qwen"]["packet_status"] == "BLOCKED_NOT_FUNDED"
    assert (
        providers["qwen"]["pricing_snapshot"][
            "shared_usd_budget_allocation_micro_usd"
        ]
        == 0
    )

    for provider_id in ("deepseek", "openai"):
        packet = providers[provider_id]
        assert packet["qualification_state"] == "QUARANTINED"
        assert packet["packet_status"] == "FROZEN_NOT_ACTIVATED"
        assert packet["credential_value_inspected"] is False
        assert packet["private_repository_policy_fit"] == (
            "blocked_pending_explicit_provider_transfer_authorization"
        )
        limits = packet["attempt_limits"]
        assert limits == {
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
        assert packet["pricing_snapshot"]["calculated_worst_case_micro_usd"] == (
            22_400
        )
        assert packet["pricing_snapshot"]["per_attempt_hard_cap_micro_usd"] == (
            25_000
        )

    assert packets["authority"]["execution_authorized"] is False
    assert packets["authority"]["provider_invocations_authorized"] == 0
    assert packets["authority"]["benchmark_executions_authorized"] == 0
    assert (
        packets["authority"]["private_repository_provider_transfer_authorized"]
        is False
    )


def test_corpus_and_private_target_contract_are_project_neutral() -> None:
    packets = load_yaml_file(PACKETS)
    corpus = packets["deterministic_corpus"]
    target = packets["private_target_packet_contract"]

    assert len(corpus["files"]) == 12
    assert _aggregate_sha256(corpus["files"]) == corpus["aggregate_sha256"]
    for item in corpus["files"]:
        assert _git_blob_sha(ROOT / item["path"]) == item["git_blob_sha"]

    assert target["binding_mode"] == "operator_private_runtime_input"
    assert target["public_identity_serialized"] is False
    assert target["public_commit_serialized"] is False
    assert target["public_path_allowlist_serialized"] is False
    assert target["public_content_digest_serialized"] is False
    assert target["prepared_target_attestation"] == (
        "present_outside_repository"
    )
    assert target["exact_snapshot_required_before_execution"] is True
    assert set(target["required_private_fields"]) == {
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
    }
    assert not ({"repository", "commit", "files", "aggregate_sha256"} & set(target))
    assert target["benchmark_read_authorized"] is False
    assert target["provider_transfer_authorized"] is False
    assert target["mutation_authorized"] is False


def test_report_records_zero_operation_stop_boundary() -> None:
    report = REPORT.read_text(encoding="utf-8")
    normalized_report = " ".join(report.split())

    assert "P15C_PACKET_FREEZE_ACCEPTED_PRE_ENTRY_NO_EXECUTION" in report
    assert "budget and manual switches belong together" in normalized_report
    assert (
        "they do not belong in the credential file" in normalized_report
    )
    assert "P15C_authorized: false" in report
    assert "provider_invocations: 0" in report
    assert "benchmark_executions: 0" in report
    assert "private_repository_provider_transfers: 0" in report
    assert "runtime_source_changes: 0" in report
