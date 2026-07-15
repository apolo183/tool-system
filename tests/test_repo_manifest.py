from __future__ import annotations

from pathlib import Path

from tool_system.architecture.repo_manifest import (
    FORMAL_COLUMNS,
    LEGACY_COLUMNS,
    _git_environment,
    _table_rows,
    validate_repo_manifest,
)
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "REPO_MANIFEST.md"
MODULE_REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"


def _manifest_text() -> str:
    return MANIFEST.read_text(encoding="utf-8")


def _write_manifest(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "REPO_MANIFEST.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_current_repository_manifest_covers_every_tracked_path_once() -> None:
    result = validate_repo_manifest(MANIFEST, ROOT)

    assert result["status"] == "PASS"
    assert result["reasons"] == []
    assert result["tracked_path_count"] == (
        result["formal_path_count"] + result["legacy_path_count"]
    )
    assert result["formal_set_count"] == 27
    assert result["legacy_set_count"] == 6
    assert result["legacy_path_count"] == 291
    assert result["unclassified_path_count"] == 0
    assert result["group_process_file_compliance_claimed"] is False
    assert result["cleanup_authorized"] is False
    assert result["executes_target_repo_mutation"] is False


def test_manifest_tables_use_registered_columns_and_one_root() -> None:
    text = _manifest_text()
    formal, formal_reasons = _table_rows(
        text,
        "## Formal File Sets",
        FORMAL_COLUMNS,
    )
    legacy, legacy_reasons = _table_rows(
        text,
        "## Retained Non-Authority Sets",
        LEGACY_COLUMNS,
    )

    assert formal_reasons == []
    assert legacy_reasons == []
    assert sum(row["upstream"] == "ROOT" for row in formal) == 1
    assert all(row["lifecycle"] == "ACTIVE" for row in formal)
    assert all(row["status"] == "REGISTERED" for row in formal)
    assert all(row["authority"] == "false" for row in legacy)
    assert all(row["runtime_default"] == "false" for row in legacy)


def test_legacy_sets_are_exactly_the_retained_non_authority_roots() -> None:
    legacy, reasons = _table_rows(
        _manifest_text(),
        "## Retained Non-Authority Sets",
        LEGACY_COLUMNS,
    )

    assert reasons == []
    assert {row["path"] for row in legacy} == {
        "docs/reports/**/*",
        "examples/active_gates.yaml",
        "examples/change_plans/**/*",
        "examples/task_manifests/**/*",
        "examples/target_repo_dry_runs/**/*",
        "examples/target_repo_pr_previews/**/*",
    }
    assert all(
        row["disposition"] == "pending separate cleanup authorization"
        for row in legacy
    )


def test_manifest_blocks_unclassified_tracked_path(tmp_path: Path) -> None:
    text = "\n".join(
        line
        for line in _manifest_text().splitlines()
        if not line.startswith("| .gitignore |")
    )

    result = validate_repo_manifest(_write_manifest(tmp_path, text), ROOT)

    assert result["status"] == "BLOCK"
    assert any("tracked paths are unclassified: .gitignore" in reason for reason in result["reasons"])


def test_manifest_blocks_formal_and_legacy_overlap(tmp_path: Path) -> None:
    text = _manifest_text().replace(
        "| docs/reports/**/* | retained legacy milestone and task evidence |",
        "| README.md | retained legacy milestone and task evidence |",
        1,
    )

    result = validate_repo_manifest(_write_manifest(tmp_path, text), ROOT)

    assert result["status"] == "BLOCK"
    assert any("formal and legacy sets overlap at: README.md" in reason for reason in result["reasons"])


def test_manifest_blocks_legacy_authority_claim(tmp_path: Path) -> None:
    text = _manifest_text().replace(
        "| false | false | pending separate cleanup authorization |",
        "| true | false | pending separate cleanup authorization |",
        1,
    )

    result = validate_repo_manifest(_write_manifest(tmp_path, text), ROOT)

    assert result["status"] == "BLOCK"
    assert any("legacy authority must be false" in reason for reason in result["reasons"])


def test_manifest_blocks_duplicate_formal_section(tmp_path: Path) -> None:
    text = _manifest_text() + "\n## Formal File Sets\n"

    result = validate_repo_manifest(_write_manifest(tmp_path, text), ROOT)

    assert result["status"] == "BLOCK"
    assert any("must appear exactly once" in reason for reason in result["reasons"])


def test_manifest_blocks_self_upstream_and_missing_root(tmp_path: Path) -> None:
    text = _manifest_text().replace(
        "| docs/tool_system_global_development_principles_v1.md | local engineering constitution | Define tool-system-local evidence, authority, modularity, safety, and rollback discipline. | tool-system governance owner | ACTIVE | ROOT |",
        "| docs/tool_system_global_development_principles_v1.md | local engineering constitution | Define tool-system-local evidence, authority, modularity, safety, and rollback discipline. | tool-system governance owner | ACTIVE | docs/tool_system_global_development_principles_v1.md |",
        1,
    )

    result = validate_repo_manifest(_write_manifest(tmp_path, text), ROOT)

    assert result["status"] == "BLOCK"
    assert any("cannot reference itself" in reason for reason in result["reasons"])
    assert any("exactly one ROOT, found 0" in reason for reason in result["reasons"])


def test_manifest_git_reads_use_minimal_deterministic_environment() -> None:
    environment = _git_environment()

    assert set(environment) == {
        "PATH",
        "LC_ALL",
        "GIT_OPTIONAL_LOCKS",
        "GIT_NO_LAZY_FETCH",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_TERMINAL_PROMPT",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_GLOBAL",
    }
    assert environment["LC_ALL"] == "C"
    assert environment["GIT_OPTIONAL_LOCKS"] == "0"
    assert environment["GIT_NO_LAZY_FETCH"] == "1"
    assert environment["GIT_CONFIG_GLOBAL"] == "/dev/null"


def test_blueprint_module_registry_packaging_and_ci_register_manifest() -> None:
    blueprint = load_yaml_file(BLUEPRINT)
    boundary = blueprint["milestone_module_invariant"]["process_migration_boundary"]
    modules = {
        module["module_id"]: module
        for module in load_yaml_file(MODULE_REGISTRY)["modules"]
    }
    architecture = modules["architecture_registry"]
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (
        ROOT / ".github" / "workflows" / "tool-system-ci.yml"
    ).read_text(encoding="utf-8")

    assert boundary["repository_manifest_path"] == "REPO_MANIFEST.md"
    assert boundary["formal_file_set_registration_implemented"] is True
    assert boundary["tracked_path_coverage_validation_implemented"] is True
    assert boundary["legacy_non_authority_sets_registered"] is True
    assert boundary["group_process_file_compliance_claimed"] is False
    assert architecture["module_version"] == "1.1.0"
    assert "REPO_MANIFEST.md" in architecture["natural_owner_paths"]
    assert "src/tool_system/cli/validate_repo_manifest.py" in architecture[
        "natural_owner_paths"
    ]
    assert (
        'tool-system-validate-repo-manifest = "tool_system.cli.validate_repo_manifest:main"'
        in pyproject
    )
    assert (
        "python -m tool_system.cli.validate_repo_manifest REPO_MANIFEST.md"
        in workflow
    )
