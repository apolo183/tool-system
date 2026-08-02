from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tool_system.cli.validate_change_plan import validate as validate_change_plan
from tool_system.cli.validate_task_manifest import validate as validate_task_manifest
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.repository_context import (
    RepositoryContextError,
    RepositoryContextLimits,
    build_repository_context,
    validate_repository_context_freshness,
)


ROOT = Path(__file__).resolve().parents[1]
P14D_MANIFEST = (
    ROOT
    / "examples"
    / "task_manifests"
    / "tool_system_p14d_repository_context_v1.yaml"
)
P14D_PLAN = (
    ROOT
    / "examples"
    / "change_plans"
    / "tool_system_p14d_repository_context_v1.yaml"
)
PROJECT_STATE = ROOT / "docs" / "tool_system_project_state_v1.yaml"
REPO_WRITE_POLICY = ROOT / "policy" / "repo_write_policy.yaml"
AUTONOMY_POLICY = ROOT / "policy" / "autonomy_policy.yaml"
P14D_REPORT = (
    ROOT
    / "docs"
    / "reports"
    / "p14d_repository_context_natural_owner_acceptance.md"
)
P14D_FILES = {
    "REPO_MANIFEST.md",
    "config/module_registry_v1.yaml",
    "docs/modules/repository-context-contract-v1.md",
    "docs/tool_system_module_registry_contract_v1.md",
    "docs/tool_system_project_state_v1.yaml",
    "docs/reports/p14d_repository_context_natural_owner_acceptance.md",
    "src/tool_system/repository_context/__init__.py",
    "src/tool_system/repository_context/builder.py",
    "tests/test_repository_context_builder.py",
    "tests/test_module_registry.py",
    "tests/test_module_contracts.py",
    "tests/test_repo_manifest.py",
    "tests/test_phase_alignment.py",
    "tests/test_milestone_module_invariant.py",
    "tests/test_model_provider_portfolio_contract.py",
    "tests/test_p14_phase_entry_contract.py",
    "tests/test_p14c_execution_contract.py",
    "examples/task_manifests/tool_system_p14d_repository_context_v1.yaml",
    "examples/change_plans/tool_system_p14d_repository_context_v1.yaml",
}


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repository: Path, message: str = "fixture") -> str:
    _git(repository, "add", "--all")
    _git(repository, "commit", "-q", "-m", message)
    return _git(repository, "rev-parse", "HEAD")


def _repository(tmp_path: Path, files: dict[str, str | bytes]) -> tuple[Path, str]:
    repository = tmp_path / "fixture-repository"
    repository.mkdir(parents=True)
    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "config", "user.email", "fixture@example.invalid")
    _git(repository, "config", "user.name", "Fixture")
    for relative, content in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return repository, _commit(repository)


def _build(repository: Path, head: str, **overrides: object) -> dict[str, object]:
    arguments: dict[str, object] = {
        "expected_head": head,
        "blueprint_path": "blueprint.yaml",
        "governance_paths": ("GOVERNANCE.md",),
        "query_terms": ("billing",),
    }
    arguments.update(overrides)
    return build_repository_context(repository, **arguments)  # type: ignore[arg-type]


def test_python_repository_context_is_deterministic_bounded_and_evidenced(
    tmp_path: Path,
) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: maintain billing totals\n",
            "GOVERNANCE.md": "Natural owners remain proposals until accepted.\n",
            "src/billing/__init__.py": "from .service import total\n",
            "src/billing/service.py": (
                "from src.billing.money import cents\n\n"
                "def total(value: int) -> int:\n    return cents(value)\n"
            ),
            "src/billing/money.py": (
                "def cents(value: int) -> int:\n    return value * 100\n"
            ),
            "tests/test_service.py": (
                "from src.billing.service import total\n\n"
                "def test_total():\n    assert total(2) == 200\n"
            ),
            "assets/logo.bin": b"\x00\x01\x02",
        },
    )

    first = _build(repository, head)
    second = _build(repository, head)

    assert first == second
    assert first["status"] == "PASS"
    snapshot = first["snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["head"] == head
    assert snapshot["tree"] == _git(repository, "rev-parse", "HEAD^{tree}")
    assert snapshot["clean_worktree"] is True
    assert len(str(snapshot["tracked_set_sha256"])) == 64
    assert len(str(snapshot["context_sha256"])) == 64
    selected = {
        record["path"]: record
        for record in first["selected_context"]  # type: ignore[union-attr]
    }
    assert {"blueprint.yaml", "GOVERNANCE.md"} <= set(selected)
    assert "src/billing/service.py" in selected
    assert "tests/test_service.py" in selected
    assert first["dependency_map"]["src/billing/service.py"] == [  # type: ignore[index]
        "src/billing/money.py"
    ]
    assert first["test_map"]["src/billing/service.py"] == [  # type: ignore[index]
        "tests/test_service.py"
    ]
    proposal = first["natural_owner_proposal"]
    assert proposal["authority_effect"] == "none"  # type: ignore[index]
    assert proposal["owner_path"] == "src/billing"  # type: ignore[index]
    assert proposal["proposal_status"] == "EVIDENCE_SUPPORTED"  # type: ignore[index]
    assert first["selected_file_count"] <= 32
    assert first["selected_bytes"] <= 1_048_576
    assert first["side_effects"] == {
        "repository_writes": 0,
        "network_operations": 0,
        "provider_invocations": 0,
        "credential_accesses": 0,
    }
    assert _git(repository, "status", "--porcelain=v1", "--untracked-files=all") == ""


def test_typescript_relative_dependencies_and_tests_are_mapped(tmp_path: Path) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: order pricing\n",
            "GOVERNANCE.md": "Use the nearest evidenced owner.\n",
            "src/order.ts": (
                "import { cents } from './money';\n"
                "export const orderTotal = (n: number) => cents(n);\n"
            ),
            "src/money.ts": "export const cents = (n: number) => n * 100;\n",
            "tests/order.test.ts": (
                "import { orderTotal } from '../src/order';\n"
                "if (orderTotal(2) !== 200) throw new Error('bad');\n"
            ),
        },
    )

    result = _build(repository, head, query_terms=("order",))

    assert result["dependency_map"]["src/order.ts"] == ["src/money.ts"]
    assert result["test_map"]["src/order.ts"] == ["tests/order.test.ts"]
    selected_paths = {
        record["path"] for record in result["selected_context"]
    }
    assert {"src/order.ts", "src/money.ts", "tests/order.test.ts"} <= selected_paths


def test_seed_path_can_supply_owner_evidence_with_an_unmatched_query(
    tmp_path: Path,
) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: bounded change\n",
            "GOVERNANCE.md": "Owner evidence is required.\n",
            "lib/engine.py": "def run():\n    return True\n",
        },
    )

    result = _build(
        repository,
        head,
        query_terms=("unmatched",),
        seed_paths=("lib/engine.py",),
    )

    assert result["natural_owner_proposal"]["owner_path"] == "lib/engine.py"
    engine = next(
        record
        for record in result["selected_context"]
        if record["path"] == "lib/engine.py"
    )
    assert "caller-seed" in engine["relevance_reasons"]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"expected_head": "0" * 40}, "STALE_EXPECTED_HEAD"),
        ({"blueprint_path": "missing.yaml"}, "REQUIRED_EVIDENCE_MISSING"),
        ({"governance_paths": ()}, "INVALID_GOVERNANCE_PATHS"),
        ({"query_terms": ()}, "INVALID_QUERY_TERMS"),
        ({"blueprint_path": "../blueprint.yaml"}, "INVALID_REPOSITORY_PATH"),
    ],
)
def test_invalid_or_stale_inputs_fail_closed(
    tmp_path: Path,
    overrides: dict[str, object],
    code: str,
) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: billing\n",
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )

    with pytest.raises(RepositoryContextError, match=code):
        _build(repository, head, **overrides)


def test_dirty_worktree_and_post_build_staleness_fail_closed(tmp_path: Path) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: billing\n",
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )
    result = _build(repository, head)
    snapshot = result["snapshot"]
    assert validate_repository_context_freshness(repository, snapshot)["status"] == "PASS"

    (repository / "src/billing.py").write_text(
        "def total():\n    return 2\n", encoding="utf-8"
    )
    with pytest.raises(RepositoryContextError, match="DIRTY_WORKTREE"):
        _build(repository, head)
    with pytest.raises(RepositoryContextError, match="DIRTY_WORKTREE"):
        validate_repository_context_freshness(repository, snapshot)

    _commit(repository, "changed")
    with pytest.raises(RepositoryContextError, match="STALE_EXPECTED_HEAD"):
        validate_repository_context_freshness(repository, snapshot)


def test_binary_oversized_symlink_and_scan_limits_block(tmp_path: Path) -> None:
    binary_repository, binary_head = _repository(
        tmp_path / "binary",
        {
            "blueprint.yaml": b"\x00binary",
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )
    with pytest.raises(RepositoryContextError, match="BINARY_INPUT_BLOCKED"):
        _build(binary_repository, binary_head)

    large_repository, large_head = _repository(
        tmp_path / "large",
        {
            "blueprint.yaml": "x" * 128,
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )
    with pytest.raises(RepositoryContextError, match="REQUIRED_FILE_LIMIT_EXCEEDED"):
        _build(
            large_repository,
            large_head,
            limits=RepositoryContextLimits(max_file_bytes=64),
        )

    symlink_root = tmp_path / "symlink-root"
    symlink_root.symlink_to(large_repository, target_is_directory=True)
    with pytest.raises(RepositoryContextError, match="SYMLINK_REPOSITORY_ROOT"):
        _build(symlink_root, large_head)


def test_missing_relevant_implementation_evidence_blocks(tmp_path: Path) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: billing\n",
            "GOVERNANCE.md": "owner: local\n",
            "notes/billing.md": "Only prose is present.\n",
        },
    )

    with pytest.raises(RepositoryContextError, match="INSUFFICIENT_OWNER_EVIDENCE"):
        _build(repository, head)


def test_local_git_reads_use_hardened_no_prompt_no_write_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: billing\n",
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )
    observed: list[tuple[list[str], dict[str, str]]] = []
    real_run = subprocess.run

    def recording_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        command = list(args[0])  # type: ignore[arg-type]
        environment = dict(kwargs.get("env", {}))  # type: ignore[arg-type]
        if command[0] == "git" and environment:
            observed.append((command, environment))
        return real_run(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(subprocess, "run", recording_run)

    assert _build(repository, head)["status"] == "PASS"
    assert observed
    forbidden = {"add", "apply", "checkout", "commit", "fetch", "merge", "push", "reset"}
    for command, environment in observed:
        assert forbidden.isdisjoint(command)
        assert environment["GIT_OPTIONAL_LOCKS"] == "0"
        assert environment["GIT_NO_LAZY_FETCH"] == "1"
        assert environment["GIT_TERMINAL_PROMPT"] == "0"
        assert environment["GIT_NO_REPLACE_OBJECTS"] == "1"


def test_repository_root_must_be_exact_top_level(tmp_path: Path) -> None:
    repository, head = _repository(
        tmp_path,
        {
            "blueprint.yaml": "objective: billing\n",
            "GOVERNANCE.md": "owner: local\n",
            "src/billing.py": "def total():\n    return 1\n",
        },
    )

    with pytest.raises(RepositoryContextError, match="REPOSITORY_ROOT_NOT_TOP_LEVEL"):
        _build(repository / "src", head)

    assert os.path.samefile(repository, Path(repository).resolve())


def test_p14d_exact_task_pair_and_descriptive_acceptance_state_validate() -> None:
    manifest_result = validate_task_manifest(
        P14D_MANIFEST,
        REPO_WRITE_POLICY,
        AUTONOMY_POLICY,
    )
    plan_result = validate_change_plan(P14D_PLAN)
    manifest = load_yaml_file(P14D_MANIFEST)
    plan = load_yaml_file(P14D_PLAN)
    state = load_yaml_file(PROJECT_STATE)

    assert manifest_result["status"] == "PASS"
    assert manifest_result["reasons"] == []
    assert plan_result["status"] == "PASS"
    assert plan_result["reasons"] == []
    assert set(manifest["allowed_files"]) == P14D_FILES
    assert set(manifest["scope"]["in_scope"]) == P14D_FILES
    assert set(plan["changed_files"]) == P14D_FILES
    assert len(P14D_FILES) == 19
    current = state["current_phase"]
    assert current["last_accepted_stage"] == "P14E_BLUEPRINT_COMPILER"
    assert current["last_accepted_stage_record"] == (
        "docs/reports/p14e_blueprint_compiler_acceptance.md"
    )
    assert current["next_stage"] == "P14F_AUTONOMOUS_PATCH_TEST_REPAIR_REVIEW"
    assert current["next_stage_authorized"] is False
    assert state["authority_effect"] == "none"
    assert state["p14d"]["stage_accepted"] is True
    assert state["p14d"]["natural_owner_proposal_grants_authority"] is False
    assert state["p14e"]["stage_accepted"] is True
    assert state["authorization_boundaries"] == {
        "state_file_grants_authority": False,
        "live_model_provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "downstream_repository_access_authorized": False,
        "remote_target_mutation_authorized": False,
        "production_deployment_authorized": False,
        "cleanup_execution_authorized": False,
        "rollback_execution_authorized": False,
    }
    assert "P14D_ACCEPTED_ISOLATED_FIXTURE_ONLY" in P14D_REPORT.read_text(
        encoding="utf-8"
    )
