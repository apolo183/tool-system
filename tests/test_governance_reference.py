from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "config" / "governance_reference_v1.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
RECORDED_AUDIT_SHA = "a87fc305932fe52042d98b4abf545afd13f89be2"
PRE_ACTIVATION_SHA = "f039a5355e1e5ea3fa865b827947b0c1153a2745"


def test_governance_reference_has_exact_v1_shape_and_values() -> None:
    reference = load_yaml_file(REFERENCE)

    assert reference == {
        "reference_contract_version": "governance_reference_v1",
        "downstream_canonical_repo_id": "tool-system",
        "governance_canonical_repo_id": "finance-governance",
        "governance_canonical_remote": (
            "git@github.com:apolo183/finance-governance.git"
        ),
        "governance_commit_sha": RECORDED_AUDIT_SHA,
    }


def test_reference_records_audit_sha_without_selecting_current_rules() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    authority = blueprint["milestone_module_invariant"]["authority_scope"]
    enforcement = blueprint["milestone_module_invariant"]["enforcement"]
    evidence = enforcement["real_central_module_registry_check_evidence"]

    assert authority["governance_reference_effect"] == (
        "compatibility_and_audit_record_not_current_policy_selector_or_cutover_evidence"
    )
    assert authority["governance_reference_record_present"] is True
    assert authority["group_cutover_completed_by_reference"] is False
    assert blueprint["active_phase_execution"]["authority_effect"] == (
        "tool_system_local_only"
    )
    assert enforcement["real_central_module_registry_check_passed"] is True
    assert evidence["governance_current_observed_effect"] == (
        "audit_evidence_only_not_policy_pin"
    )
    assert evidence["recorded_governance_ref"] == RECORDED_AUDIT_SHA
    assert evidence["recorded_governance_ref_effect"] == (
        "compatibility_and_audit_record_only"
    )
    assert evidence["central_cutover_completed"] is False
    assert evidence["next_stage"] == "S10_EXPLICIT_CUTOVER"
    assert evidence["next_stage_authorized"] is False


def test_public_contracts_state_current_head_consumption_and_staged_cutover() -> None:
    for path in (AGENTS, README, PRINCIPLES):
        text = path.read_text(encoding="utf-8")
        assert "config/governance_reference_v1.yaml" in text
        assert RECORDED_AUDIT_SHA not in text
        assert PRE_ACTIVATION_SHA not in text
        assert "`finance-governance` is the active group authority" in text
        assert (
            "current verified committed finance-governance `HEAD`" in text
        )
        assert (
            "`governance_commit_sha` does not select or pin current rules"
            in text
        )
        assert (
            "a central SHA change alone does not require a tool-system update or PR"
            in text
        )
        assert "central repository registry supplies identity only" in text
        assert "caller supplies the target root" in text
        assert (
            "neither controls central `authority_status` nor proves tool-system cutover"
            in text
        )
        assert "S8 completed only the compatibility/audit reference record" in text
        assert (
            "S9's real central `module-registry-check` has passed and is accepted"
            in text
        )
        assert "S9 does not perform cutover" in text
        assert "until S10 is separately authorized and accepted" in text
        assert "immutable downstream pointer" not in text
        assert "accepted active-authority commit" not in text
        assert "does not activate group governance" not in text
        assert "pre-activation" not in text
        for stage in ("S9", "S10"):
            assert stage in text


def test_group_constitution_is_not_copied_into_tool_system() -> None:
    assert not (ROOT / "docs" / "global_development_principles_v1.md").exists()
    assert not (ROOT / "config" / "governance_reference_schema_v1.json").exists()
