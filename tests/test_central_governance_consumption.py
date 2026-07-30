from __future__ import annotations

import re
from pathlib import Path

from tool_system.architecture.repo_manifest import parse_manifest_formal_rows
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PRINCIPLES = ROOT / "docs" / "tool_system_global_development_principles_v1.md"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"
REPO_MANIFEST = ROOT / "REPO_MANIFEST.md"

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
CENTRAL_PIN_KEY = re.compile(
    r"\b(?:central|finance_governance)[a-z0-9_]*"
    r"(?:sha|commit|revision|base)\b\s*[:=]",
    re.IGNORECASE,
)
FULL_COMMIT_SHA = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)


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


def test_obsolete_central_reference_gate_state_is_absent() -> None:
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


def test_formal_files_cannot_pin_a_central_governance_revision() -> None:
    parser_mode, formal_rows, reasons = parse_manifest_formal_rows(
        REPO_MANIFEST.read_text(encoding="utf-8")
    )

    assert parser_mode is not None
    assert reasons == []
    for row in formal_rows:
        relative = row["path"]
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert CENTRAL_PIN_KEY.search(text) is None, relative
        for line_number, line in enumerate(text.splitlines(), start=1):
            normalized = line.lower()
            has_central_context = (
                "central" in normalized or "finance-governance" in normalized
            )
            has_revision_context = any(
                token in normalized for token in ("sha", "commit", "revision")
            )
            assert not (
                has_central_context
                and has_revision_context
                and FULL_COMMIT_SHA.search(line)
            ), f"{relative}:{line_number}"


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
