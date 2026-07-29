from __future__ import annotations

from pathlib import Path

from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"

CENTRAL_REMOTE = "git@github.com:apolo183/finance-governance.git"
CENTRAL_BRANCH = "main"
CENTRAL_FORMAL_PATHS = {
    "docs/global_development_principles_v1.md",
    "config/repo_registry_v1.yaml",
}
OBSOLETE_CENTRAL_MARKERS = {
    "governance_" + "reference_v1",
    "governance_" + "commit_sha",
    "required-" + "governance-ref",
    "module-" + "registry-check",
    "S9_REAL_" + "CENTRAL_MODULE_REGISTRY_CHECK_ACCEPTED",
    "S10_EXPLICIT_" + "CUT" + "OVER",
}
OBSOLETE_CENTRAL_SHAS = {
    "04ca9d558f59dae17603d79" + "76727aa29782253aa",
    "a87fc305932fe52042d98b4" + "abf545afd13f89be2",
    "ad5ad497fad88190b8e3fb0" + "773343d4981ab8fd3",
}


def test_public_entrypoints_consume_current_central_main_by_fixed_paths() -> None:
    for path in (AGENTS, README, PRINCIPLES):
        text = path.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        assert CENTRAL_REMOTE in text
        assert f"`{CENTRAL_BRANCH}`" in text
        assert all(formal_path in text for formal_path in CENTRAL_FORMAL_PATHS)
        assert "Do not pin a central commit SHA" in normalized
        assert "central pull requests or history" in normalized
        assert "Central rules prevail" in normalized
        assert "tool-system-specific constraints" in normalized


def test_obsolete_central_reference_gate_and_sha_state_is_absent() -> None:
    obsolete_reference = ROOT / "config" / ("governance_" + "reference_v1.yaml")
    assert not obsolete_reference.exists()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(ROOT).parts
        if set(relative_parts) & {".git", ".pytest_cache", "__pycache__"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in OBSOLETE_CENTRAL_MARKERS:
            assert marker not in text
        for sha in OBSOLETE_CENTRAL_SHAS:
            assert sha not in text


def test_blueprint_keeps_only_tool_system_owned_module_enforcement() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    invariant = blueprint["milestone_module_invariant"]
    authority = invariant["authority_scope"]
    enforcement = invariant["enforcement"]

    assert authority["repository"] == "tool-system"
    assert authority["governs_other_repositories"] is False
    obsolete_key_fragment = "governance_" + "reference"
    assert not any(obsolete_key_fragment in key for key in authority)
    assert enforcement["module_registry_path"] == "config/module_registry_v1.yaml"
    assert enforcement["module_registry_structural_validation_implemented"] is True
    assert not any(
        "central" in key or ("cut" + "over") in key for key in enforcement
    )


def test_central_principles_and_registry_are_not_copied_locally() -> None:
    assert not (ROOT / "docs" / "global_development_principles_v1.md").exists()
    assert not (ROOT / "config" / "repo_registry_v1.yaml").exists()
