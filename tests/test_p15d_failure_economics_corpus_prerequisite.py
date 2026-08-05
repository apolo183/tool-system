from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "config/p15d_failure_economics_corpus_prerequisite_v1.yaml"
BLUEPRINT = ROOT / "blueprint/tool_system_v0.yaml"
PROJECT_STATE = ROOT / "docs/tool_system_project_state_v1.yaml"
REPORT = ROOT / "docs/reports/p15d_failure_economics_corpus_prerequisite_freeze.md"
MANIFEST = (
    ROOT / "examples/task_manifests/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml"
)
PLAN = (
    ROOT / "examples/change_plans/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml"
)
REPO_WRITE_POLICY = ROOT / "policy/repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy/autonomy_policy.yaml"
EXACT_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "config/p15d_failure_economics_corpus_prerequisite_v1.yaml",
    "docs/modules/adaptive-model-portfolio-and-economics-contract-v1.md",
    "docs/reports/p15d_failure_economics_corpus_prerequisite_freeze.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "examples/change_plans/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml",
    "examples/task_manifests/tool_system_p15d_prerequisite_corpus_freeze_v1.yaml",
    "tests/test_module_registry.py",
    "tests/test_p15d_failure_economics_corpus_prerequisite.py",
    "tests/test_repo_manifest.py",
}
EXPECTED_CORPUS_SHA256 = (
    "583855b9336fdac767823b942b810ccc455c7aff995c847518e4021350616f4d"
)


def _load(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_task_pair_exact_scope_and_non_authorizing_boundary_validate() -> None:
    manifest_result = validate_task_manifest(
        MANIFEST, REPO_WRITE_POLICY, AUTONOMY_POLICY
    )
    plan_result = validate_change_plan(PLAN)
    manifest = _load(MANIFEST)
    plan = _load(PLAN)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == EXACT_FILES
    assert set(manifest["scope"]["in_scope"]) == EXACT_FILES
    assert set(plan["changed_files"]) == EXACT_FILES
    assert len(EXACT_FILES) == 12
    assert manifest["authority_effect"] == "none"
    assert manifest["publication"]["retain_feature_branch"] is True
    assert manifest["rollback"]["execution_authorized"] is False


def test_corpus_sources_cases_and_synthetic_economics_are_content_addressed() -> None:
    packet = _load(CORPUS)

    assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == EXPECTED_CORPUS_SHA256
    assert packet["authority_effect"] == "none"
    assert packet["blueprint_binding"]["entry_condition_satisfied"] is False
    assert packet["blueprint_binding"]["p15d_stage_entry_authorized"] is False

    for source in packet["evidence_inputs"]["accepted_fixture_sources"]:
        path = ROOT / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    for source in packet["evidence_inputs"]["current_non_accepting_p15c_sources"]:
        path = ROOT / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    for source in packet["source_test_catalog"]:
        path = ROOT / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]

    cases = packet["case_catalog"]
    assert [case["case_id"] for case in cases] == [
        "availability-failover",
        "quality-repair-then-escalation",
        "policy-block-no-provider-bypass",
        "cancellation-before-dispatch-and-before-application",
        "repeated-or-two-cycle-no-progress-stop",
        "affected-module-isolation",
        "rollback-plan-remains-non-executing",
        "hard-floors-before-total-economics",
    ]
    assert cases[0]["expected_disposition"] == "AVAILABILITY_FAILOVER"
    assert cases[1]["expected_disposition"] == "SAME_ROUTE_REPAIR_THEN_ESCALATE"
    assert cases[2]["expected_disposition"] == "BLOCK_NO_PROVIDER_BYPASS"
    assert cases[2]["provider_switch_allowed"] is False
    assert cases[6]["expected_rollback_plan_authorized"] is False
    assert cases[7]["cheaper_unqualified_route_selectable"] is False

    economics = packet["economic_record_schema"]
    values = economics["synthetic_fixture"]
    expected = values.pop("expected_total")
    assert sum(values.values()) == expected == 17_000
    assert economics["private_economic_values_recorded"] is False


def test_blueprint_state_report_and_zero_operation_stop_remain_consistent() -> None:
    packet = _load(CORPUS)
    blueprint = _load(BLUEPRINT)
    state = _load(PROJECT_STATE)
    report = REPORT.read_text(encoding="utf-8")

    stages = {
        item["stage"]: item
        for item in blueprint["milestones"]["P15_MULTI_PROJECT_BENCHMARK"]["stage_plan"]
    }
    p15d = stages["P15D_FAILURE_ROLLBACK_ISOLATION_AND_ECONOMICS_CORPUS"]
    assert p15d["entry_requires"] == [
        "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK accepted"
    ]
    assert state["current_phase"]["active_stage"] == (
        "P15C_CROSS_PROVIDER_READ_ONLY_BENCHMARK"
    )
    prerequisite = state["p15d_prerequisite_corpus_freeze"]
    assert prerequisite["p15c_stage_accepted"] is False
    assert prerequisite["p15d_stage_entered"] is False
    assert prerequisite["p15d_stage_accepted"] is False
    assert prerequisite["p15e_authorized"] is False
    assert set(packet["zero_operation_boundary"].values()) == {0}
    assert (
        packet["terminal_boundary"][
            "funding_or_live_execution_required_for_this_freeze"
        ]
        is False
    )
    assert "does not enter or accept P15D" in report
    assert "p15d_stage_entered: false" in report
