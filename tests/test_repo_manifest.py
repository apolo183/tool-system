from __future__ import annotations

from pathlib import Path

import pytest

from tool_system.architecture.repo_manifest import (
    CENTRAL_FORMAL_PARSER_MODE,
    CENTRAL_FORMAL_SECTION,
    CENTRAL_MODULE_REGISTRY_PATH,
    FORMAL_COLUMNS,
    FORMAL_SECTION,
    LEGACY_FORMAL_PARSER_MODE,
    LEGACY_COLUMNS,
    _git_environment,
    _table_rows,
    parse_manifest_formal_rows,
    validate_repo_manifest,
)
from tool_system.manifest.task_manifest import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "REPO_MANIFEST.md"
MODULE_REGISTRY = ROOT / "config" / "module_registry_v1.yaml"
BLUEPRINT = ROOT / "blueprint" / "tool_system_v0.yaml"


def _central_row(path: str, upstream: str = "ROOT") -> str:
    return (
        f"| {path} | formal role | formal purpose | formal owner | ACTIVE | "
        f"{upstream} | formal consumer | formal validation | REGISTERED |"
    )


def _central_manifest_text(
    *,
    columns: tuple[str, ...] = FORMAL_COLUMNS,
    rows: list[str] | None = None,
    section: str = CENTRAL_FORMAL_SECTION,
) -> str:
    formal_rows = rows or [
        _central_row("docs/global_development_principles_v1.md"),
        _central_row(
            CENTRAL_MODULE_REGISTRY_PATH,
            "docs/global_development_principles_v1.md",
        ),
    ]
    return "\n".join(
        [
            "# REPO_MANIFEST.md",
            "",
            section,
            "",
            f"| {' | '.join(columns)} |",
            f"| {' | '.join('---' for _ in columns)} |",
            *formal_rows,
            "",
            "## Non-Claims",
            "",
            "Fixture only.",
        ]
    )


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
    assert result["parser_mode"] == LEGACY_FORMAL_PARSER_MODE
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


def test_both_manifest_formats_have_stable_explicit_parser_modes() -> None:
    legacy_text = _manifest_text()
    central_text = _central_manifest_text()

    legacy_result = parse_manifest_formal_rows(legacy_text)
    central_result = parse_manifest_formal_rows(central_text)

    assert legacy_result == parse_manifest_formal_rows(legacy_text)
    assert central_result == parse_manifest_formal_rows(central_text)
    legacy_mode, legacy_rows, legacy_reasons = legacy_result
    central_mode, central_rows, central_reasons = central_result
    assert legacy_mode == LEGACY_FORMAL_PARSER_MODE
    assert legacy_reasons == []
    assert len(legacy_rows) == 27
    assert central_mode == CENTRAL_FORMAL_PARSER_MODE
    assert central_reasons == []
    assert [row["path"] for row in central_rows] == [
        "docs/global_development_principles_v1.md",
        CENTRAL_MODULE_REGISTRY_PATH,
    ]


@pytest.mark.parametrize(
    "text",
    [
        _manifest_text() + f"\n{FORMAL_SECTION}\n",
        _central_manifest_text() + f"\n{CENTRAL_FORMAL_SECTION}\n",
        _manifest_text() + "\n" + _central_manifest_text(),
    ],
    ids=["duplicate-legacy", "duplicate-central", "mixed-formats"],
)
def test_manifest_parser_blocks_duplicate_or_mixed_formal_sections(text: str) -> None:
    parser_mode, rows, reasons = parse_manifest_formal_rows(text)

    assert parser_mode is None
    assert rows == []
    assert reasons


@pytest.mark.parametrize(
    "section",
    [
        "",
        "## Formal File",
        "## Formal File Set",
        "## Formal Files ",
        "### Formal Files",
    ],
)
def test_manifest_parser_blocks_missing_or_wrong_formal_heading(section: str) -> None:
    text = _central_manifest_text(section=section)

    parser_mode, rows, reasons = parse_manifest_formal_rows(text)

    assert parser_mode is None
    assert rows == []
    assert reasons


@pytest.mark.parametrize("missing_index", range(len(FORMAL_COLUMNS)))
def test_central_manifest_blocks_each_missing_header_column(
    missing_index: int,
) -> None:
    columns = tuple(
        column for index, column in enumerate(FORMAL_COLUMNS) if index != missing_index
    )

    parser_mode, _, reasons = parse_manifest_formal_rows(
        _central_manifest_text(columns=columns)
    )

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert any("columns must be exactly" in reason for reason in reasons)


@pytest.mark.parametrize(
    "columns",
    [
        (*FORMAL_COLUMNS, "extra"),
        (FORMAL_COLUMNS[1], FORMAL_COLUMNS[0], *FORMAL_COLUMNS[2:]),
    ],
    ids=["additional-column", "reordered-columns"],
)
def test_central_manifest_blocks_additional_or_reordered_header_columns(
    columns: tuple[str, ...],
) -> None:
    parser_mode, _, reasons = parse_manifest_formal_rows(
        _central_manifest_text(columns=columns)
    )

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert any("columns must be exactly" in reason for reason in reasons)


@pytest.mark.parametrize(
    "registry_row",
    [
        "| config/module_registry_v1.yaml | too | few | columns |",
        "config/module_registry_v1.yaml is formal",
    ],
    ids=["wrong-column-count", "non-table-text"],
)
def test_central_manifest_blocks_malformed_rows(registry_row: str) -> None:
    text = _central_manifest_text(
        rows=[
            _central_row("docs/global_development_principles_v1.md"),
            registry_row,
        ]
    )

    parser_mode, _, reasons = parse_manifest_formal_rows(text)

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert reasons


def test_central_manifest_blocks_duplicate_exact_path() -> None:
    registry_row = _central_row(
        CENTRAL_MODULE_REGISTRY_PATH,
        "docs/global_development_principles_v1.md",
    )
    text = _central_manifest_text(
        rows=[
            _central_row("docs/global_development_principles_v1.md"),
            registry_row,
            registry_row,
        ]
    )

    parser_mode, _, reasons = parse_manifest_formal_rows(text)

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert any("duplicate central formal path" in reason for reason in reasons)


@pytest.mark.parametrize(
    "registry_path",
    [
        "config/module_registry*.yaml",
        "./config/module_registry_v1.yaml",
        "config/module_registry_v1.yaml/",
        "config/module_registry_v1.yml",
    ],
)
def test_central_manifest_requires_literal_module_registry_row(
    registry_path: str,
) -> None:
    text = _central_manifest_text(
        rows=[
            _central_row("docs/global_development_principles_v1.md"),
            _central_row(
                registry_path,
                "docs/global_development_principles_v1.md",
            ),
        ]
    )

    parser_mode, rows, reasons = parse_manifest_formal_rows(text)

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert CENTRAL_MODULE_REGISTRY_PATH not in {row["path"] for row in rows}
    assert any("exact module registry path" in reason for reason in reasons)


def test_central_manifest_blocks_missing_module_registry_row() -> None:
    text = _central_manifest_text(
        rows=[_central_row("docs/global_development_principles_v1.md")]
    )

    parser_mode, rows, reasons = parse_manifest_formal_rows(text)

    assert parser_mode == CENTRAL_FORMAL_PARSER_MODE
    assert [row["path"] for row in rows] == ["docs/global_development_principles_v1.md"]
    assert any("exact module registry path" in reason for reason in reasons)


def test_central_parser_does_not_activate_local_validator_adapter(
    tmp_path: Path,
) -> None:
    result = validate_repo_manifest(
        _write_manifest(tmp_path, _central_manifest_text()),
        ROOT,
    )

    assert result["status"] == "BLOCK"
    assert result["parser_mode"] == CENTRAL_FORMAL_PARSER_MODE
    assert any("parse-only" in reason for reason in result["reasons"])


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
