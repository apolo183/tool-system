from __future__ import annotations

import hashlib
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Mapping

import pytest

from tool_system.blueprint_compiler import BlueprintCompilerError, compile_blueprint
from tool_system.development_loop import (
    DevelopmentLoopLimits,
    FrozenDevelopmentContract,
    evaluate_sealed_candidate_reopen,
    run_development_loop,
)
from tool_system.local_git import LocalGitIdentity, run_durable_local_git
from tool_system.manifest.task_manifest import load_yaml_file
from tool_system.orchestrator import DurableOrchestratorStore
from tool_system.repository_context import build_repository_context


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "p14h"


def _git(root: Path, *arguments: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _base_files(
    root: Path,
    head: str,
    scope: tuple[str, ...],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in scope:
        completed = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if completed.returncode == 0:
            result[path] = completed.stdout.decode("utf-8")
    return result


def _fixture(tmp_path: Path, name: str) -> tuple[Path, str]:
    root = tmp_path / name
    shutil.copytree(FIXTURES / name, root)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "P14H Fixture")
    _git(root, "config", "user.email", "fixture@tool-system.invalid")
    _git(root, "add", "--all")
    _git(root, "commit", "-q", "-m", "fixture base")
    return root, _git(root, "rev-parse", "HEAD")


def _authorization() -> dict[str, bool]:
    return {
        "blueprint_approved": True,
        "isolated_fixture_repositories_only": True,
        "target_repo_mutation_authorized": False,
        "provider_execution_authorized": False,
        "credential_value_access_authorized": False,
        "production_operation_authorized": False,
        "cleanup_execution_authorized": False,
    }


def _context_and_compilation(
    root: Path,
    head: str,
    milestone_id: str,
    terms: tuple[str, ...],
) -> tuple[dict[str, object], dict[str, object]]:
    context = build_repository_context(
        root,
        expected_head=head,
        blueprint_path="blueprint.yaml",
        governance_paths=("GOVERNANCE.md",),
        query_terms=terms,
    )
    blueprint = load_yaml_file(root / "blueprint.yaml")
    compilation = compile_blueprint(
        blueprint,
        context,
        {"modules": []},
        _authorization(),
        milestone_ids=(milestone_id,),
        acceptance_requirements=("all frozen fixture acceptance passes",),
    )
    assert context == build_repository_context(
        root,
        expected_head=head,
        blueprint_path="blueprint.yaml",
        governance_paths=("GOVERNANCE.md",),
        query_terms=terms,
    )
    assert compilation == compile_blueprint(
        blueprint,
        context,
        {"modules": []},
        _authorization(),
        milestone_ids=(milestone_id,),
        acceptance_requirements=("all frozen fixture acceptance passes",),
    )
    return context, compilation


def _store(tmp_path: Path, root: Path, name: str) -> DurableOrchestratorStore:
    parent = tmp_path / f"{name}-state"
    parent.mkdir(mode=0o700)
    return DurableOrchestratorStore(parent / "state.sqlite3", forbidden_roots=(root,))


def _review(_: Mapping[str, object]) -> dict[str, object]:
    return {
        "violated_acceptance_items": [],
        "suggestions": ["optional wording outside frozen acceptance"],
    }


def _run_compiled_stack(
    *,
    tmp_path: Path,
    name: str,
    milestone_id: str,
    terms: tuple[str, ...],
    worker: Callable[[Mapping[str, object]], Mapping[str, object]],
    validator: Callable[[Mapping[str, str]], Mapping[str, object]],
    run_id: str,
    after_effect: Callable[[str], None] | None = None,
    lease_seconds: float = 60.0,
) -> tuple[Path, str, dict[str, object], DurableOrchestratorStore]:
    root, head = _fixture(tmp_path, name)
    _, compilation = _context_and_compilation(root, head, milestone_id, terms)
    binding = compilation["milestone_module_bindings"][0]
    scope = tuple(binding["allowed_files"])
    baseline = {
        path: (root / path).read_text(encoding="utf-8")
        for path in scope
        if (root / path).is_file()
    }
    contract = FrozenDevelopmentContract(
        task_digest=compilation["compilation_sha256"],
        baseline_tree=_git(root, "rev-parse", "HEAD^{tree}"),
        allowed_scope=scope,
        acceptance_set=tuple(binding["acceptance"]),
        validation_set=("fixture-stack",),
    )
    store = _store(tmp_path, root, run_id)
    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id=run_id,
        task_id="compiled-change",
        lease_owner="p14h-fixture",
        identity=LocalGitIdentity(
            expected_head_sha=head,
            expected_tree_sha=_git(root, "rev-parse", "HEAD^{tree}"),
            branch_name=f"agent/{run_id}",
            commit_message=f"P14H {name} fixture",
        ),
        contract=contract,
        baseline_files=baseline,
        worker=worker,
        validator=validator,
        code_reviewer=_review,
        contract_reviewer=_review,
        after_effect=after_effect,
        lease_seconds=lease_seconds,
    )
    return root, head, result, store


def test_greenfield_python_cli_repairs_source_and_stale_status(
    tmp_path: Path,
) -> None:
    calls = 0

    def worker(_: Mapping[str, object]) -> dict[str, object]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {
                "operations": [
                    {
                        "op": "replace",
                        "path": "src/calculator.py",
                        "expected_sha256": _sha(
                            "def increment(value: int) -> int:\n    return value\n"
                        ),
                        "content": "def increment(value: int) -> int:\n    return value + 1\n",
                    },
                    {
                        "op": "add",
                        "path": "src/cli.py",
                        "expected_sha256": None,
                        "content": "from src.calculator import increment\n\ndef main(value: int) -> int:\n    return increment(value)\n",
                    },
                ]
            }
        return {
            "operations": [
                {
                    "op": "replace",
                    "path": "STATUS.md",
                    "expected_sha256": _sha("implementation: pending\n"),
                    "content": "implementation: accepted\n",
                }
            ]
        }

    acceptance = (
        "library increments correctly",
        "CLI delegates to library",
        "status converges",
    )

    def validator(files: Mapping[str, str]) -> dict[str, object]:
        namespace: dict[str, object] = {}
        exec(compile(files["src/calculator.py"], "calculator.py", "exec"), namespace)
        source_pass = namespace["increment"](1) == 2  # type: ignore[operator]
        cli_pass = "increment(value)" in files.get("src/cli.py", "")
        status_pass = files["STATUS.md"] == "implementation: accepted\n"
        satisfied = [
            item
            for item, passed in zip(
                acceptance,
                (source_pass, cli_pass, status_pass),
                strict=True,
            )
            if passed
        ]
        return {
            "validation_results": {
                "fixture-stack": {
                    "status": "PASS" if len(satisfied) == 3 else "BLOCK",
                    "diagnostic": None if len(satisfied) == 3 else "bounded repair required",
                }
            },
            "satisfied_acceptance_items": satisfied,
        }

    root, head, result, _ = _run_compiled_stack(
        tmp_path=tmp_path,
        name="python_cli",
        milestone_id="PYTHON_CLI",
        terms=("increment", "cli"),
        worker=worker,
        validator=validator,
        run_id="p14h-python",
    )

    assert result["status"] == "PASS", result
    assert calls == 2
    assert _git(root, "diff", "--name-status", head, "HEAD").splitlines() == [
        "M\tSTATUS.md",
        "M\tsrc/calculator.py",
        "A\tsrc/cli.py",
    ]
    assert _git(root, "rev-list", "--count", f"{head}..HEAD") == "1"
    assert result["remote_operations"] == result["provider_calls"] == 0


def test_typescript_language_neutral_flow_records_add_modify_delete(
    tmp_path: Path,
) -> None:
    def worker(_: Mapping[str, object]) -> dict[str, object]:
        return {
            "operations": [
                {
                    "op": "add",
                    "path": "src/format.ts",
                    "expected_sha256": None,
                    "content": "export const format = (value) => `value:${value}`;\n",
                },
                {
                    "op": "replace",
                    "path": "src/index.ts",
                    "expected_sha256": _sha(
                        (FIXTURES / "typescript_package" / "src/index.ts").read_text(
                            encoding="utf-8"
                        )
                    ),
                    "content": 'import { format } from "./format.js";\n\nexport const display = (value) => format(value);\n',
                },
                {
                    "op": "delete",
                    "path": "src/legacy.ts",
                    "expected_sha256": _sha(
                        (FIXTURES / "typescript_package" / "src/legacy.ts").read_text(
                            encoding="utf-8"
                        )
                    ),
                },
                {
                    "op": "replace",
                    "path": "STATUS.md",
                    "expected_sha256": _sha(
                        (FIXTURES / "typescript_package" / "STATUS.md").read_text(
                            encoding="utf-8"
                        )
                    ),
                    "content": "implementation: accepted\n",
                },
            ]
        }

    acceptance = (
        "formatter is exported",
        "legacy source is removed",
        "status converges",
    )

    def validator(files: Mapping[str, str]) -> dict[str, object]:
        syntax = all(
            subprocess.run(
                ["node", "--input-type=module", "--check", "-"],
                input=files[path],
                text=True,
                capture_output=True,
                check=False,
            ).returncode
            == 0
            for path in ("src/format.ts", "src/index.ts", "tests/index.test.ts")
        )
        passed = (
            syntax and "format(value)" in files["src/index.ts"],
            "src/legacy.ts" not in files,
            files["STATUS.md"] == "implementation: accepted\n",
        )
        satisfied = [
            item
            for item, ok in zip(acceptance, passed, strict=True)
            if ok
        ]
        return {
            "validation_results": {
                "fixture-stack": {
                    "status": "PASS" if len(satisfied) == 3 else "BLOCK",
                    "diagnostic": None,
                }
            },
            "satisfied_acceptance_items": satisfied,
        }

    root, head, result, _ = _run_compiled_stack(
        tmp_path=tmp_path,
        name="typescript_package",
        milestone_id="TYPESCRIPT_PACKAGE",
        terms=("display", "legacy", "formatter"),
        worker=worker,
        validator=validator,
        run_id="p14h-typescript",
    )

    assert result["status"] == "PASS", result
    assert _git(root, "diff", "--name-status", head, "HEAD").splitlines() == [
        "M\tSTATUS.md",
        "A\tsrc/format.ts",
        "M\tsrc/index.ts",
        "D\tsrc/legacy.ts",
    ]
    assert result["remote_operations"] == result["credential_reads"] == 0


def test_ambiguous_blueprint_out_of_scope_patch_and_invented_milestone_block(
    tmp_path: Path,
) -> None:
    root, head = _fixture(tmp_path, "python_cli")
    context, _ = _context_and_compilation(root, head, "PYTHON_CLI", ("increment",))
    blueprint = load_yaml_file(root / "blueprint.yaml")
    del blueprint["milestones"]["PYTHON_CLI"]["module_change"]
    with pytest.raises(BlueprintCompilerError, match="MISSING_MODULE_CHANGE_BINDING"):
        compile_blueprint(
            blueprint,
            context,
            {"modules": []},
            _authorization(),
            milestone_ids=("PYTHON_CLI",),
            acceptance_requirements=("frozen",),
        )
    with pytest.raises(BlueprintCompilerError, match="UNKNOWN_MILESTONE"):
        compile_blueprint(
            load_yaml_file(root / "blueprint.yaml"),
            context,
            {"modules": []},
            _authorization(),
            milestone_ids=("INVENTED",),
            acceptance_requirements=("frozen",),
        )

    store = _store(tmp_path, root, "out-of-scope")
    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="out-of-scope",
        task_id="compiled-change",
        lease_owner="p14h-fixture",
        identity=LocalGitIdentity(
            expected_head_sha=head,
            expected_tree_sha=_git(root, "rev-parse", "HEAD^{tree}"),
            branch_name="agent/out-of-scope",
            commit_message="blocked fixture",
        ),
        contract=FrozenDevelopmentContract(
            task_digest="a" * 64,
            baseline_tree=_git(root, "rev-parse", "HEAD^{tree}"),
            allowed_scope=("STATUS.md",),
            acceptance_set=("frozen",),
            validation_set=("fixture-stack",),
        ),
        baseline_files={"STATUS.md": "implementation: pending\n"},
        worker=lambda _: {
            "operations": [
                {
                    "op": "add",
                    "path": "UNAUTHORIZED.md",
                    "expected_sha256": None,
                    "content": "blocked\n",
                }
            ]
        },
        validator=lambda _: {},
        code_reviewer=_review,
        contract_reviewer=_review,
    )
    assert result["terminal_code"] == "PATCH_OUTSIDE_FROZEN_SCOPE"
    assert _git(root, "branch", "--show-current") == "main"
    assert _git(root, "status", "--porcelain=v1", "--untracked-files=all") == ""
    assert store.get_side_effect("out-of-scope:branch") is None


def test_cancellation_resume_no_progress_and_evidence_non_reopening() -> None:
    contract = FrozenDevelopmentContract(
        task_digest="b" * 64,
        baseline_tree="c" * 40,
        allowed_scope=("file.txt",),
        acceptance_set=("content",),
        validation_set=("fixture-stack",),
    )
    baseline = {"file.txt": "old\n"}
    patch = {
        "operations": [
            {
                "op": "replace",
                "path": "file.txt",
                "expected_sha256": _sha("old\n"),
                "content": "new\n",
            }
        ]
    }
    checks = iter((False, True))
    cancelled = run_development_loop(
        contract=contract,
        baseline_files=baseline,
        worker=lambda _: patch,
        validator=lambda _: {},
        code_reviewer=_review,
        contract_reviewer=_review,
        cancellation_requested=lambda: next(checks),
    )
    assert cancelled["terminal_code"] == "CANCELLED_BY_CALLER"
    assert cancelled["candidate_files"] == baseline
    assert cancelled["cycles"] == []
    resumed = run_development_loop(
        contract=contract,
        baseline_files=baseline,
        worker=lambda _: patch,
        validator=lambda files: {
            "validation_results": {
                "fixture-stack": {"status": "PASS", "diagnostic": None}
            },
            "satisfied_acceptance_items": ["content"]
            if files["file.txt"] == "new\n"
            else [],
        },
        code_reviewer=_review,
        contract_reviewer=_review,
        resume_state=cancelled,
    )
    assert resumed["status"] == "PASS"
    assert resumed["worker_call_count"] == 2
    stale = evaluate_sealed_candidate_reopen(
        resumed,
        {"pull_request_status": "stale", "material_evidence": False},
    )
    assert stale == {
        "status": "PASS",
        "reopen": False,
        "reason": "EVIDENCE_CANNOT_REOPEN",
    }

    repeated = run_development_loop(
        contract=contract,
        baseline_files=baseline,
        worker=lambda _: {
            "operations": [
                {
                    "op": "replace",
                    "path": "file.txt",
                    "expected_sha256": _sha("old\n"),
                    "content": "old\n",
                }
            ]
        },
        validator=lambda _: {
            "validation_results": {
                "fixture-stack": {"status": "BLOCK", "diagnostic": "same"}
            },
            "satisfied_acceptance_items": [],
        },
        code_reviewer=_review,
        contract_reviewer=_review,
    )
    assert repeated["terminal_code"] == "STOPPED_NO_PROGRESS_REPEATED_FINGERPRINT"
    assert repeated["cycles"][0]["recurrence_fingerprint"] == repeated["cycles"][1]["recurrence_fingerprint"]


def test_completed_commit_crash_resumes_once_and_conflicting_branch_blocks(
    tmp_path: Path,
) -> None:
    class Crash(BaseException):
        pass

    def worker(_: Mapping[str, object]) -> dict[str, object]:
        return {
            "operations": [
                {
                    "op": "replace",
                    "path": "STATUS.md",
                    "expected_sha256": _sha("implementation: pending\n"),
                    "content": "implementation: accepted\n",
                },
                {
                    "op": "replace",
                    "path": "src/calculator.py",
                    "expected_sha256": _sha(
                        "def increment(value: int) -> int:\n    return value\n"
                    ),
                    "content": "def increment(value: int) -> int:\n    return value + 1\n",
                },
                {
                    "op": "add",
                    "path": "src/cli.py",
                    "expected_sha256": None,
                    "content": "from src.calculator import increment\n",
                },
            ]
        }

    validator = lambda files: {
        "validation_results": {
            "fixture-stack": {"status": "PASS", "diagnostic": None}
        },
        "satisfied_acceptance_items": [
            "library increments correctly",
            "CLI delegates to library",
            "status converges",
        ],
    }
    try:
        root, head, _, store = _run_compiled_stack(
            tmp_path=tmp_path,
            name="python_cli",
            milestone_id="PYTHON_CLI",
            terms=("increment", "cli"),
            worker=worker,
            validator=validator,
            run_id="p14h-crash",
            lease_seconds=0.1,
            after_effect=lambda effect: (_ for _ in ()).throw(Crash())
            if effect == "commit"
            else None,
        )
    except Crash:
        root = tmp_path / "python_cli"
        head = _git(root, "rev-parse", "HEAD^")
        store = DurableOrchestratorStore(
            tmp_path / "p14h-crash-state" / "state.sqlite3",
            forbidden_roots=(root,),
        )
    else:
        raise AssertionError("fixture crash did not occur")

    commit = _git(root, "rev-parse", "HEAD")
    time.sleep(0.12)
    _, compilation = _context_and_compilation_at_base(root, head, "PYTHON_CLI", ("increment", "cli"))
    binding = compilation["milestone_module_bindings"][0]
    scope = tuple(binding["allowed_files"])
    baseline = _base_files(root, head, scope)
    resumed = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="p14h-crash",
        task_id="compiled-change",
        lease_owner="p14h-resume",
        identity=LocalGitIdentity(
            expected_head_sha=head,
            expected_tree_sha=_git(root, "rev-parse", f"{head}^{{tree}}"),
            branch_name="agent/p14h-crash",
            commit_message="P14H python_cli fixture",
        ),
        contract=FrozenDevelopmentContract(
            task_digest=compilation["compilation_sha256"],
            baseline_tree=_git(root, "rev-parse", f"{head}^{{tree}}"),
            allowed_scope=scope,
            acceptance_set=tuple(binding["acceptance"]),
            validation_set=("fixture-stack",),
        ),
        baseline_files=baseline,
        worker=worker,
        validator=validator,
        code_reviewer=_review,
        contract_reviewer=_review,
    )
    assert resumed["terminal_code"] == "RESUMED_COMPLETED_LOCAL_COMMIT"
    assert resumed["commit"] == commit
    assert _git(root, "rev-list", "--count", f"{head}..HEAD") == "1"
    assert resumed["draft_pr_plan"] == {"authorized": False, "remote_operations": 0}

    conflict_root, conflict_head = _fixture(tmp_path / "conflict", "python_cli")
    _git(conflict_root, "branch", "agent/conflict", conflict_head)
    conflict_store = _store(tmp_path / "conflict", conflict_root, "conflict")
    blocked = run_durable_local_git(
        repository_root=conflict_root,
        store=conflict_store,
        run_id="conflict",
        task_id="compiled-change",
        lease_owner="p14h-fixture",
        identity=LocalGitIdentity(
            expected_head_sha=conflict_head,
            expected_tree_sha=_git(conflict_root, "rev-parse", "HEAD^{tree}"),
            branch_name="agent/conflict",
            commit_message="blocked fixture",
        ),
        contract=FrozenDevelopmentContract(
            task_digest="d" * 64,
            baseline_tree=_git(conflict_root, "rev-parse", "HEAD^{tree}"),
            allowed_scope=("STATUS.md",),
            acceptance_set=("status",),
            validation_set=("fixture-stack",),
        ),
        baseline_files={"STATUS.md": "implementation: pending\n"},
        worker=lambda _: {},
        validator=lambda _: {},
        code_reviewer=_review,
        contract_reviewer=_review,
    )
    assert blocked["terminal_code"] == "BRANCH_ALREADY_EXISTS_WITHOUT_RECEIPT"
    assert conflict_store.get_run("conflict") is None


def _context_and_compilation_at_base(
    root: Path,
    head: str,
    milestone_id: str,
    terms: tuple[str, ...],
) -> tuple[dict[str, object], dict[str, object]]:
    current_branch = _git(root, "branch", "--show-current")
    _git(root, "switch", "--detach", head)
    try:
        return _context_and_compilation(root, head, milestone_id, terms)
    finally:
        _git(root, "switch", current_branch)
