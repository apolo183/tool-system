from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/reports/p16a_sustainable_operations_inventory_v1.yaml"
SPEC = ROOT / "docs/reports/p16a_sustainable_operations_acceptance_specification.md"
STATE = ROOT / "docs/tool_system_project_state_v1.yaml"
MANIFEST = ROOT / "examples/task_manifests/tool_system_p16a_sustainable_operations_acceptance_specification_v1.yaml"
PLAN = ROOT / "examples/change_plans/tool_system_p16a_sustainable_operations_acceptance_specification_v1.yaml"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_every_blueprint_output_is_classified_once() -> None:
    inventory = load(INVENTORY)
    outputs = inventory["outputs"]
    assert len(outputs) == 16
    assert len({item["output"] for item in outputs}) == 16
    assert {item["classification"] for item in outputs} == {
        "complete_inheritable",
        "primitive_not_production_closed",
        "missing_module_or_interface",
        "api_mode_conditional",
        "separate_production_authorization",
    }
    assert all(item["evidence"] for item in outputs)
    state = load(STATE)["p16a_sustainable_operations_acceptance_specification"]
    counts = state["classification_counts"]
    assert counts == dict(__import__("collections").Counter(
        item["classification"] for item in outputs
    ))


def test_p16a_freezes_exact_governance_only_scope() -> None:
    manifest = load(MANIFEST)
    plan = load(PLAN)
    files = set(manifest["allowed_files"])
    assert files == set(manifest["scope"]["in_scope"])
    assert files == set(plan["changed_files"])
    assert len(files) == 7
    assert all(not path.startswith("src/") for path in files)
    assert "blueprint/tool_system_v0.yaml" not in files
    assert all(not path.startswith("config/") for path in files)
    budgets = manifest["bounded_closure"]["frozen_before_execution"]["finite_budgets"]
    assert all(budgets[key] == 0 for key in (
        "provider_invocations", "credential_value_accesses", "real_downstream_accesses",
        "production_operations", "cleanup_operations", "rollback_operations",
        "backup_restore_drills", "disaster_recovery_drills",
    ))


def test_optional_api_work_is_non_gating_and_p16_is_not_accepted() -> None:
    inventory = load(INVENTORY)
    state = load(STATE)
    stop = inventory["stop_boundary"]
    assert stop["optional_api_plugin_is_core_gate"] is False
    assert stop["p16_accepted"] is False
    assert stop["production_deployment_authorized"] is False
    assert stop["first_implementation_package_authorized"] is False
    p16a = state["p16a_sustainable_operations_acceptance_specification"]
    assert p16a["status"] == "inventory_planned_pending_guarded_merge"
    assert p16a["p16_accepted"] is False
    assert p16a["production_deployment_authorized"] is False
    assert p16a["next_implementation_package_authorized"] is False
    assert p16a["optional_api_provider_plugin_v2_is_core_gate"] is False
    text = SPEC.read_text(encoding="utf-8")
    assert "P16 remains active and unaccepted" in text
    assert "separate user authorization for P16B" in text
