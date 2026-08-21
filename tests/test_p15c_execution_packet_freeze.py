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
EXACT_VERSION_BLOCK_REPORT = (
    ROOT / "docs" / "reports" / "p15c_deepseek_exact_version_block.md"
)
EXACT_VERSION_BLOCK_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_deepseek_exact_version_block_v1.yaml"
)
EXACT_VERSION_BLOCK_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_deepseek_exact_version_block_v1.yaml"
)
OPENAI_QWEN_MATRIX_REPORT = (
    ROOT / "docs" / "reports" / "p15c_openai_qwen_matrix_refreeze.md"
)
OPENAI_QWEN_MATRIX_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml"
)
OPENAI_QWEN_MATRIX_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml"
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
EXACT_VERSION_BLOCK_FILES = {
    "config/module_registry_v1.yaml",
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/modules/ai-worker-runtime-contract-v1.md",
    "docs/reports/p15c_deepseek_exact_version_block.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_deepseek_exact_version_block_v1.yaml",
    "examples/task_manifests/tool_system_p15c_deepseek_exact_version_block_v1.yaml",
    "src/tool_system/ai_worker/p15c_benchmark.py",
    "src/tool_system/ai_worker/p15c_entry.py",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_entry.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_execution_packet_freeze.py",
}
OPENAI_QWEN_MATRIX_FILES = {
    "config/module_registry_v1.yaml",
    "config/p15c_execution_packet_freeze_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15c_openai_qwen_matrix_refreeze.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml",
    "examples/task_manifests/tool_system_p15c_openai_qwen_matrix_refreeze_v1.yaml",
    "tests/test_ai_worker_p15c_benchmark.py",
    "tests/test_ai_worker_p15c_entry.py",
    "tests/test_module_registry.py",
    "tests/test_p15c_execution_packet_freeze.py",
}
REFREEZE_PACKET_SEMANTICS_SHA256 = (
    "03f99a7e43ce7f3a381d59231c8a9d31ec1a9324922639126fa2268ff6d42626"
)
CORRECTED_PACKET_SEMANTICS_SHA256 = (
    "27dc75dc1644518aee2717a1a0150a86c55be38d09a2d8c753c0a8bdf1bfc483"
)
BLOCKED_PACKET_SEMANTICS_SHA256 = (
    "9d856fe6821f340b4ae372572f42bf4da4c45c318f7cbd0ba1c6a42b8aaa3d4b"
)
OPENAI_QWEN_MATRIX_PACKET_SEMANTICS_SHA256 = (
    "9c0170c83143ed99d759f9932d42b8d407417f50af19f1a52d61e5417c9cbf95"
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

    assert manifest_result["status"] == "BLOCK"
    assert manifest_result["reasons"]
    assert all(
        reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION")
        for reason in manifest_result["reasons"]
    )
    assert plan_result["status"] == "BLOCK"
    assert plan_result["reasons"]
    assert set(manifest["allowed_files"]) == EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == EXACT_FILES
    assert set(plan["changed_files"]) == EXACT_FILES
    assert len(EXACT_FILES) == 8

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
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "BLOCK"
    assert manifest_result["reasons"]
    assert all(
        reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION")
        for reason in manifest_result["reasons"]
    )
    assert plan_result["status"] == "BLOCK"
    assert plan_result["reasons"]
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


def test_deepseek_packet_correction_pair_and_historical_baseline_validate() -> None:
    manifest_result = validate_task_manifest(
        CORRECTION_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(CORRECTION_PLAN)
    manifest = load_yaml_file(CORRECTION_MANIFEST)
    plan = load_yaml_file(CORRECTION_PLAN)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "BLOCK"
    assert manifest_result["reasons"]
    assert all(
        reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION")
        for reason in manifest_result["reasons"]
    )
    assert plan_result["status"] == "BLOCK"
    assert plan_result["reasons"]
    assert set(manifest["allowed_files"]) == CORRECTION_EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == CORRECTION_EXACT_FILES
    assert set(plan["changed_files"]) == CORRECTION_EXACT_FILES
    assert len(CORRECTION_EXACT_FILES) == 7

    correction = state["p15c_packet_freeze"]["deepseek_packet_evidence_correction"]
    assert correction["status"] == "accepted_on_guarded_squash_merge"
    assert correction["baseline_commit"] == ("f30f43512acfa497afd9f27dcce7cf4a0ebeb101")
    assert correction["baseline_tree"] == ("1c6b29bdcb9b823e7e063d5050587df45cd2f126")
    assert correction["packet_semantics_excluding_tool_system_baseline_sha256"] == (
        CORRECTED_PACKET_SEMANTICS_SHA256
    )
    assert correction["provider_model_id_changed"] is False
    assert correction["execution_authority_added"] is False
    assert correction["provider_invocations"] == 0
    assert correction["credential_value_accesses"] == 0
    assert correction["target_repository_accesses"] == 0
    assert correction["benchmark_executions"] == 0


def test_exact_version_block_pair_and_fail_closed_state_validate() -> None:
    manifest_result = validate_task_manifest(
        EXACT_VERSION_BLOCK_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(EXACT_VERSION_BLOCK_PLAN)
    manifest = load_yaml_file(EXACT_VERSION_BLOCK_MANIFEST)
    plan = load_yaml_file(EXACT_VERSION_BLOCK_PLAN)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "BLOCK"
    assert manifest_result["reasons"]
    assert all(
        reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION")
        for reason in manifest_result["reasons"]
    )
    assert plan_result["status"] == "BLOCK"
    assert plan_result["reasons"]
    assert set(manifest["allowed_files"]) == EXACT_VERSION_BLOCK_FILES
    assert set(manifest["scope"]["in_scope"]) == EXACT_VERSION_BLOCK_FILES
    assert set(plan["changed_files"]) == EXACT_VERSION_BLOCK_FILES
    assert len(EXACT_VERSION_BLOCK_FILES) == 14

    block = state["p15c_packet_freeze"]["deepseek_exact_version_block"]
    assert block["status"] == "accepted_only_on_guarded_squash_merge_no_execution"
    assert block["official_catalog_model_version"] == "DeepSeek-V4-Flash-0731"
    assert block["request_api_model_id"] == "deepseek-v4-flash"
    assert block["exact_version_request_binding_evidenced"] is False
    assert block["execution_blocker"] == "PROVIDER_EXACT_VERSION_UNPINNABLE"
    assert block["packet_semantics_excluding_tool_system_baseline_sha256"] == (
        BLOCKED_PACKET_SEMANTICS_SHA256
    )
    assert block["provider_invocations"] == 0
    assert block["credential_value_accesses"] == 0
    assert block["target_repository_accesses"] == 0
    assert block["benchmark_executions"] == 0
    assert block["p15c_stage_accepted"] is False
    assert block["p15d_authorized"] is False


def test_openai_qwen_matrix_pair_current_baseline_and_state_validate() -> None:
    manifest_result = validate_task_manifest(
        OPENAI_QWEN_MATRIX_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(OPENAI_QWEN_MATRIX_PLAN)
    manifest = load_yaml_file(OPENAI_QWEN_MATRIX_MANIFEST)
    plan = load_yaml_file(OPENAI_QWEN_MATRIX_PLAN)
    packets = load_yaml_file(PACKETS)
    state = load_yaml_file(PROJECT_STATE)["p15c_openai_qwen_matrix_refreeze"]

    assert manifest_result["status"] == "BLOCK"
    assert manifest_result["reasons"]
    assert all(
        reason.startswith("TASK_MANIFEST_SCHEMA_VIOLATION")
        for reason in manifest_result["reasons"]
    )
    assert plan_result["status"] == "BLOCK"
    assert plan_result["reasons"]
    assert set(manifest["allowed_files"]) == OPENAI_QWEN_MATRIX_FILES
    assert set(manifest["scope"]["in_scope"]) == OPENAI_QWEN_MATRIX_FILES
    assert set(plan["changed_files"]) == OPENAI_QWEN_MATRIX_FILES
    assert len(OPENAI_QWEN_MATRIX_FILES) == 12

    baseline = packets["tool_system_baseline"]
    assert baseline["commit"] == "0908a1d2ed8e88554fa4bd1e73bb7c4c4a88807b"
    assert baseline["tree"] == "c053dd93999c5ef2f9112a7638b5fd2c00acb676"
    assert baseline["previous_commit"] == ("20686afbef73d5985f4aac0d542eabe7f3fdadff")
    assert baseline["execution_matrix_changed"] is True
    assert baseline["runtime_source_changed"] is False
    assert baseline["p15c_execution_authority_added"] is False
    assert state["module"]["previous_module_version"] == "1.0.0"
    assert state["module"]["module_version"] == "1.1.0"
    assert state["execution_matrix"]["provider_ids"] == ["openai", "qwen"]
    assert state["execution_matrix"]["max_provider_invocations"] == 4
    assert state["qwen_funding_attested"] is False
    assert set(state["source_stage_evidence"].values()) == {0}
    assert state["p15c_stage_accepted"] is False
    assert state["p15d_authorized"] is False


def test_current_openai_qwen_matrix_semantics_are_content_addressed() -> None:
    packets = load_yaml_file(PACKETS)
    packets.pop("tool_system_baseline")
    normalized = yaml.safe_dump(packets, sort_keys=True).encode("utf-8")

    assert (
        hashlib.sha256(normalized).hexdigest()
        == OPENAI_QWEN_MATRIX_PACKET_SEMANTICS_SHA256
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
        for path in (
            PACKETS,
            REPORT,
            PROJECT_STATE,
            MANIFEST,
            PLAN,
            OPENAI_QWEN_MATRIX_REPORT,
            OPENAI_QWEN_MATRIX_MANIFEST,
            OPENAI_QWEN_MATRIX_PLAN,
        )
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
    assert providers["deepseek"]["packet_id"] == ("P15C-DEEPSEEK-V4-FLASH-READONLY-v1")
    assert providers["deepseek"]["model_id"] == "deepseek-v4-flash"
    assert providers["deepseek"]["exact_model_version"] == ("DeepSeek-V4-Flash-0731")
    assert providers["deepseek"]["execution_surface_id"] == (
        "deepseek-openai-compatible-chat"
    )
    assert providers["deepseek"]["operation"] == "chat.completions.create"
    assert (
        providers["deepseek"]["official_evidence"]["chat_completions_surface"]
        == "https://api-docs.deepseek.com/api/create-chat-completion"
    )
    assert "responses_surface" not in providers["deepseek"]["official_evidence"]
    assert providers["deepseek"]["packet_status"] == (
        "BLOCKED_EXACT_VERSION_UNPINNABLE"
    )
    assert providers["deepseek"]["execution_blocker"] == (
        "EXACT_MODEL_VERSION_UNPINNABLE"
    )
    assert providers["deepseek"]["private_repository_policy_fit"] == (
        "excluded_from_selected_execution_matrix"
    )
    assert (
        providers["deepseek"]["data_policy"]["repository_content_transfer_allowed"]
        is False
    )
    assert providers["openai"]["packet_id"] == ("P15C-OPENAI-GPT-5.6-LUNA-READONLY-v1")
    assert providers["openai"]["model_id"] == "gpt-5.6-luna"
    assert providers["openai"]["packet_status"] == "FROZEN_NOT_ACTIVATED"
    assert providers["openai"]["private_repository_policy_fit"] == (
        "transfer_authorized_but_private_runtime_gates_required"
    )
    assert (
        providers["openai"]["data_policy"]["repository_content_transfer_allowed"]
        is True
    )
    assert providers["qwen"]["packet_id"] == ("P15C-QWEN-3.7-PLUS-READONLY-v1")
    assert providers["qwen"]["model_id"] == "qwen3.7-plus-2026-05-26"
    assert providers["qwen"]["exact_model_version"] == ("qwen3.7-plus-2026-05-26")
    assert providers["qwen"]["packet_status"] == "BLOCKED_NOT_FUNDED"
    assert providers["qwen"]["operator_availability_attestation"] == "not_funded"
    assert providers["qwen"]["official_limits"]["max_output_tokens"] == 131_072
    assert (
        providers["qwen"]["pricing_snapshot"]["calculated_worst_case_micro_cny"]
        == 196_608
    )
    assert (
        providers["qwen"]["pricing_snapshot"]["per_attempt_hard_cap_micro_cny"]
        == 250_000
    )
    assert (
        providers["qwen"]["pricing_snapshot"]["shared_usd_budget_allocation_micro_usd"]
        == 0
    )
    assert providers["qwen"]["private_repository_policy_fit"] == (
        "transfer_authorized_but_blocked_not_funded_and_private_runtime_gates_required"
    )
    assert (
        providers["qwen"]["data_policy"]["repository_content_transfer_allowed"] is True
    )

    assert "execution_blocker" not in providers["openai"]

    for provider_id in ("deepseek", "openai", "qwen"):
        packet = providers[provider_id]
        assert packet["qualification_state"] == "QUARANTINED"
        assert packet["credential_value_inspected"] is False
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
        if provider_id != "qwen":
            assert (
                packet["pricing_snapshot"]["calculated_worst_case_micro_usd"] == 22_400
            )
            assert (
                packet["pricing_snapshot"]["per_attempt_hard_cap_micro_usd"] == 25_000
            )

    assert packets["execution_matrix"] == {
        "provider_ids": ["openai", "qwen"],
        "case_ids": ["deterministic-corpus", "private-target"],
        "max_provider_invocations": 4,
    }

    assert packets["authority"]["execution_authorized"] is False
    assert packets["authority"]["provider_invocations_authorized"] == 0
    assert packets["authority"]["benchmark_executions_authorized"] == 0
    assert (
        packets["authority"]["private_repository_provider_transfer_authorized"] is False
    )
    assert packets["authority"][
        "private_repository_provider_transfer_authorized_by_provider"
    ] == {"deepseek": False, "openai": True, "qwen": True}
    assert packets["authority"]["catalog_record_grants_runtime_transfer"] is False


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
    assert target["prepared_target_attestation"] == ("present_outside_repository")
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
    assert target["provider_transfer_authorization_recorded_by_provider"] == {
        "deepseek": False,
        "openai": True,
        "qwen": True,
    }
    assert target["provider_transfer_still_requires_private_runtime_gates"] is True
    assert target["mutation_authorized"] is False


def test_report_records_zero_operation_stop_boundary() -> None:
    report = REPORT.read_text(encoding="utf-8")
    normalized_report = " ".join(report.split())

    assert "P15C_PACKET_FREEZE_ACCEPTED_PRE_ENTRY_NO_EXECUTION" in report
    assert "budget and manual switches belong together" in normalized_report
    assert "they do not belong in the credential file" in normalized_report
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

    exact_version_block_report = EXACT_VERSION_BLOCK_REPORT.read_text(encoding="utf-8")
    assert (
        "ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_NO_EXECUTION"
        in exact_version_block_report
    )
    assert "DeepSeek-V4-Flash-0731" in exact_version_block_report
    assert "deepseek-v4-flash" in exact_version_block_report
    assert "PROVIDER_EXACT_VERSION_UNPINNABLE" in exact_version_block_report
    assert "credential_value_accesses: 0" in exact_version_block_report
    assert "provider_invocations: 0" in exact_version_block_report
    assert "benchmark_executions: 0" in exact_version_block_report

    matrix_report = OPENAI_QWEN_MATRIX_REPORT.read_text(encoding="utf-8")
    assert (
        "ACCEPTED_ONLY_ON_GUARDED_SQUASH_MERGE_BLOCKED_NOT_FUNDED_NO_EXECUTION"
        in matrix_report
    )
    assert "gpt-5.6-luna" in matrix_report
    assert "qwen3.7-plus-2026-05-26" in matrix_report
    assert "196,608 microCNY" in matrix_report
    assert "PROVIDER_PACKET_BLOCKED" in matrix_report
    assert "provider_invocations: 0" in matrix_report
    assert "benchmark_executions: 0" in matrix_report
    assert "p15d_authorized: false" in matrix_report
