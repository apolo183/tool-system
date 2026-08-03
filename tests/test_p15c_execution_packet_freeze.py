from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

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
REFREEZE_REPORT = (
    ROOT / "docs" / "reports" / "p15c_packet_canonical_refreeze_acceptance.md"
)
REFREEZE_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_packet_canonical_refreeze_v1.yaml"
)
REFREEZE_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_packet_canonical_refreeze_v1.yaml"
)
CORRECTION_REPORT = (
    ROOT / "docs" / "reports" / "p15c_deepseek_packet_evidence_correction.md"
)
CORRECTION_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_deepseek_packet_evidence_correction_v1.yaml"
)
CORRECTION_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_deepseek_packet_evidence_correction_v1.yaml"
)

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

REFREEZE_EXACT_FILES = {
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/reports/p15c_execution_packet_freeze.md",
    "docs/reports/p15c_packet_canonical_refreeze_acceptance.md",
    "docs/reports/target_identity_decoupling_acceptance.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_packet_canonical_refreeze_v1.yaml",
    "examples/task_manifests/tool_system_p15c_packet_canonical_refreeze_v1.yaml",
    "tests/test_p15c_execution_packet_freeze.py",
    "tests/test_target_identity_decoupling.py",
}
CORRECTION_EXACT_FILES = {
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/reports/p15c_deepseek_packet_evidence_correction.md",
    "docs/reports/p15c_execution_packet_freeze.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_deepseek_packet_evidence_correction_v1.yaml",
    "examples/task_manifests/tool_system_p15c_deepseek_packet_evidence_correction_v1.yaml",
    "tests/test_p15c_execution_packet_freeze.py",
}
REFREEZE_PACKET_SEMANTICS_SHA256 = (
    "03f99a7e43ce7f3a381d59231c8a9d31ec1a9324922639126fa2268ff6d42626"
)
CORRECTED_PACKET_SEMANTICS_SHA256 = (
    "27dc75dc1644518aee2717a1a0150a86c55be38d09a2d8c753c0a8bdf1bfc483"
)


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
    assert current["next_stage_authorized"] is True
    freeze = state["p15c_packet_freeze"]
    assert freeze["status"] == "accepted_pre_entry_freeze_no_execution_authority"
    assert freeze["provider_packets_enabled_for_live_execution"] == 0
    assert freeze["p15c_authorized"] is False
    assert freeze["p15c_stage_accepted"] is False
    assert state["authority_effect"] == "none"


def test_canonical_refreeze_task_pair_baseline_and_state_validate() -> None:
    manifest_result = validate_task_manifest(
        REFREEZE_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(REFREEZE_PLAN)
    manifest = load_yaml_file(REFREEZE_MANIFEST)
    plan = load_yaml_file(REFREEZE_PLAN)
    packets = load_yaml_file(PACKETS)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == REFREEZE_EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == REFREEZE_EXACT_FILES
    assert set(plan["changed_files"]) == REFREEZE_EXACT_FILES
    assert len(REFREEZE_EXACT_FILES) == 9

    refreeze = state["p15c_packet_freeze"]["canonical_refreeze"]
    assert refreeze["status"] == "accepted_on_guarded_squash_merge"
    assert refreeze["packet_semantics_excluding_tool_system_baseline_sha256"] == (
        REFREEZE_PACKET_SEMANTICS_SHA256
    )
    assert refreeze["provider_invocations"] == 0
    assert refreeze["credential_value_accesses"] == 0
    assert refreeze["target_repository_accesses"] == 0
    assert refreeze["benchmark_executions"] == 0
    assert refreeze["p15c_authorized"] is False
    assert refreeze["p15c_stage_accepted"] is False


def test_deepseek_packet_correction_pair_and_current_baseline_validate() -> None:
    manifest_result = validate_task_manifest(
        CORRECTION_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(CORRECTION_PLAN)
    manifest = load_yaml_file(CORRECTION_MANIFEST)
    plan = load_yaml_file(CORRECTION_PLAN)
    packets = load_yaml_file(PACKETS)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == CORRECTION_EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == CORRECTION_EXACT_FILES
    assert set(plan["changed_files"]) == CORRECTION_EXACT_FILES
    assert len(CORRECTION_EXACT_FILES) == 7

    baseline = packets["tool_system_baseline"]
    assert baseline["commit"] == "f30f43512acfa497afd9f27dcce7cf4a0ebeb101"
    assert baseline["tree"] == "1c6b29bdcb9b823e7e063d5050587df45cd2f126"
    assert baseline["previous_commit"] == (
        "1ede788b8b1c36bcc224cde15a5f6462c9b51938"
    )
    assert baseline["provider_model_economics_corpus_and_limit_semantics_changed"] is True
    assert baseline["execution_surface_corrected"] is True
    assert baseline["p15c_execution_authority_added"] is False

    correction = state["p15c_packet_freeze"][
        "deepseek_packet_evidence_correction"
    ]
    assert correction["status"] == "accepted_on_guarded_squash_merge"
    assert correction["packet_semantics_excluding_tool_system_baseline_sha256"] == (
        CORRECTED_PACKET_SEMANTICS_SHA256
    )
    assert correction["provider_model_id_changed"] is False
    assert correction["execution_authority_added"] is False
    assert correction["provider_invocations"] == 0
    assert correction["credential_value_accesses"] == 0
    assert correction["target_repository_accesses"] == 0
    assert correction["benchmark_executions"] == 0


def test_corrected_packet_semantics_are_content_addressed() -> None:
    packets = load_yaml_file(PACKETS)
    packets.pop("tool_system_baseline")
    normalized = yaml.safe_dump(packets, sort_keys=True).encode("utf-8")

    assert (
        hashlib.sha256(normalized).hexdigest()
        == CORRECTED_PACKET_SEMANTICS_SHA256
    )


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
        "DeepSeek-V4-Flash"
    )
    assert providers["deepseek"]["execution_surface_id"] == (
        "deepseek-openai-compatible-chat"
    )
    assert providers["deepseek"]["operation"] == "chat.completions.create"
    assert providers["deepseek"]["official_evidence"][
        "chat_completions_surface"
    ] == "https://api-docs.deepseek.com/api/create-chat-completion"
    assert "responses_surface" not in providers["deepseek"]["official_evidence"]
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

    refreeze_report = REFREEZE_REPORT.read_text(encoding="utf-8")
    assert "ACCEPTED_ON_GUARDED_SQUASH_MERGE_NO_P15C_AUTHORITY" in refreeze_report
    assert "P15C_authorized: false" in refreeze_report
    assert "provider_invocations: 0" in refreeze_report
    assert "target_repository_accesses: 0" in refreeze_report
    assert "benchmark_executions: 0" in refreeze_report

    correction_report = CORRECTION_REPORT.read_text(encoding="utf-8")
    assert "ACCEPTED_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION" in correction_report
    assert "DeepSeek-V4-Flash-0731" in correction_report
    assert "DeepSeek-V4-Flash" in correction_report
    assert "POST /chat/completions" in correction_report
    assert "credential_value_accesses: 0" in correction_report
    assert "provider_invocations: 0" in correction_report
    assert "benchmark_executions: 0" in correction_report
