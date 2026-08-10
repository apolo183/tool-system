from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from tool_system.development_loop import FrozenDevelopmentContract
from tool_system.local_git import (
    LocalGitIdentity,
    create_isolated_local_workspace,
    run_durable_local_git,
)
from tool_system.orchestrator import DurableOrchestratorStore


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _fixture(tmp_path: Path) -> tuple[Path, DurableOrchestratorStore, LocalGitIdentity]:
    root = tmp_path / "fixture"
    root.mkdir()
    _git(root, "init", "-b", "main")
    (root / "app.txt").write_text("old\n", encoding="utf-8")
    _git(root, "add", "app.txt")
    _git(root, "-c", "user.name=fixture", "-c", "user.email=f@x.invalid", "commit", "-m", "base")
    database_parent = tmp_path / "state"
    database_parent.mkdir(mode=0o700)
    store = DurableOrchestratorStore(
        database_parent / "p14g.sqlite3", forbidden_roots=(root,)
    )
    identity = LocalGitIdentity(
        expected_head_sha=_git(root, "rev-parse", "HEAD"),
        expected_tree_sha=_git(root, "rev-parse", "HEAD^{tree}"),
        branch_name="agent/p14g-fixture-v1",
        commit_message="P14G fixture change",
    )
    return root, store, identity


def _contract() -> FrozenDevelopmentContract:
    return FrozenDevelopmentContract(
        task_digest="a" * 64,
        baseline_tree="b" * 64,
        allowed_scope=("app.txt",),
        acceptance_set=("content",),
        validation_set=("test",),
        terminal_predicate="all_frozen_acceptance_validation_and_reviews_pass",
    )


def _worker(_: object) -> dict[str, object]:
    return {
        "operations": [
            {
                "op": "replace",
                "path": "app.txt",
                "expected_sha256": hashlib.sha256(b"old\n").hexdigest(),
                "content": "new\n",
            }
        ],
        "usage": {"duration_ms": 1, "cost_microunits": 0},
    }


def _validator(files: object) -> dict[str, object]:
    assert files == {"app.txt": "new\n"}
    return {
        "validation_results": {"test": {"status": "PASS", "diagnostic": None}},
        "satisfied_acceptance_items": ["content"],
    }


def _review(_: object) -> dict[str, object]:
    return {"violated_acceptance_items": [], "suggestions": []}


def _run(root: Path, store: DurableOrchestratorStore, identity: LocalGitIdentity) -> dict[str, object]:
    return run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="p14g-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=_worker,
        validator=_validator,
        code_reviewer=_review,
        contract_reviewer=_review,
    )


def test_creates_exact_remote_free_workspace_and_reuses_identity(
    tmp_path: Path,
) -> None:
    source, _, identity = _fixture(tmp_path)
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir(mode=0o700)
    workspace = workspace_parent / "bounded-run"

    created = create_isolated_local_workspace(
        source_repository_root=source,
        workspace_root=workspace,
        expected_head_sha=identity.expected_head_sha,
        expected_tree_sha=identity.expected_tree_sha,
    )

    assert created["status"] == "PASS"
    assert created["workspace_state"] == "CREATED"
    assert created["network_operations"] == 0
    assert _git(workspace, "remote") == ""
    assert _git(workspace, "rev-parse", "HEAD") == identity.expected_head_sha
    assert _git(workspace, "rev-parse", "HEAD^{tree}") == identity.expected_tree_sha

    existing = create_isolated_local_workspace(
        source_repository_root=source,
        workspace_root=workspace,
        expected_head_sha=identity.expected_head_sha,
        expected_tree_sha=identity.expected_tree_sha,
    )
    assert existing["status"] == "PASS"
    assert existing["workspace_state"] == "EXISTING"
    assert existing["workspace_created"] is False


def test_local_git_honors_cancellation_before_worker_and_commit(
    tmp_path: Path,
) -> None:
    root, store, identity = _fixture(tmp_path)

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="cancelled-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=_worker,
        validator=_validator,
        code_reviewer=_review,
        contract_reviewer=_review,
        cancellation_requested=lambda: True,
    )

    assert result["status"] == "BLOCK"
    assert result["terminal_code"] == "CANCELLED_BY_CALLER"
    assert _git(root, "branch", "--show-current") == "main"
    assert _git(root, "rev-parse", "HEAD") == identity.expected_head_sha
    assert store.get_side_effect("cancelled-run:branch") is None


def test_records_one_isolated_local_branch_and_commit(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)

    result = _run(root, store, identity)

    assert result["status"] == "PASS"
    assert _git(root, "branch", "--show-current") == identity.branch_name
    assert _git(root, "show", "HEAD:app.txt") == "new"
    assert _git(root, "rev-list", "--count", f"{identity.expected_head_sha}..HEAD") == "1"
    assert store.get_task("p14g-run", "local-change")["status"] == "COMPLETED"
    assert store.get_side_effect("p14g-run:branch")["state"] == "COMPLETED"
    assert store.get_side_effect("p14g-run:commit")["state"] == "COMPLETED"
    assert result["rollback_plan"]["authorized"] is False
    assert result["cleanup_plan"]["authorized"] is False
    assert result["remote_operations"] == result["provider_calls"] == 0


def test_remote_or_dirty_fixture_blocks_before_durable_or_git_write(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)
    _git(root, "remote", "add", "origin", "https://example.invalid/repo.git")

    result = _run(root, store, identity)

    assert result["terminal_code"] == "REMOTE_REPOSITORY_FORBIDDEN"
    assert store.get_run("p14g-run") is None
    assert _git(root, "branch", "--show-current") == "main"


def test_head_tree_and_scope_drift_fail_closed(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)
    drift = LocalGitIdentity(
        expected_head_sha=identity.expected_head_sha,
        expected_tree_sha="0" * 40,
        branch_name=identity.branch_name,
        commit_message=identity.commit_message,
    )
    result = _run(root, store, drift)
    assert result["terminal_code"] == "TREE_PRECONDITION_DRIFT"
    assert _git(root, "branch", "--show-current") == "main"


def test_failed_frozen_validation_creates_no_branch_or_commit(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="blocked",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=_worker,
        validator=lambda _: {
            "validation_results": {"test": {"status": "FAIL", "diagnostic": "no"}},
            "satisfied_acceptance_items": [],
        },
        code_reviewer=_review,
        contract_reviewer=_review,
    )

    assert result["status"] == "BLOCK"
    assert _git(root, "branch", "--show-current") == "main"
    assert _git(root, "rev-parse", "HEAD") == identity.expected_head_sha
    assert store.get_side_effect("blocked:branch") is None


def test_crash_after_durable_commit_resumes_without_duplicate_commit(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)

    class Crash(BaseException):
        pass

    try:
        run_durable_local_git(
            repository_root=root,
            store=store,
            run_id="resume-run",
            task_id="local-change",
            lease_owner="fixture-worker",
            identity=identity,
            contract=_contract(),
            baseline_files={"app.txt": "old\n"},
            worker=_worker,
            validator=_validator,
            code_reviewer=_review,
            contract_reviewer=_review,
            lease_seconds=0.2,
            after_effect=lambda name: (_ for _ in ()).throw(Crash()) if name == "commit" else None,
        )
    except Crash:
        pass
    else:
        raise AssertionError("simulated crash did not occur")

    commit = _git(root, "rev-parse", "HEAD")
    import time

    time.sleep(0.25)
    resumed = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="resume-run",
        task_id="local-change",
        lease_owner="resume-worker",
        identity=identity,
        contract=_contract(),
        baseline_files={"app.txt": "old\n"},
        worker=_worker,
        validator=_validator,
        code_reviewer=_review,
        contract_reviewer=_review,
    )

    assert resumed["terminal_code"] == "RESUMED_COMPLETED_LOCAL_COMMIT"
    assert resumed["commit"] == commit
    assert _git(root, "rev-list", "--count", f"{identity.expected_head_sha}..HEAD") == "1"


def test_records_add_modify_delete_topology_in_one_commit(tmp_path: Path) -> None:
    root, store, identity = _fixture(tmp_path)
    (root / "delete.txt").write_text("remove\n", encoding="utf-8")
    _git(root, "add", "delete.txt")
    _git(
        root,
        "-c",
        "user.name=fixture",
        "-c",
        "user.email=f@x.invalid",
        "commit",
        "--amend",
        "--no-edit",
    )
    identity = LocalGitIdentity(
        expected_head_sha=_git(root, "rev-parse", "HEAD"),
        expected_tree_sha=_git(root, "rev-parse", "HEAD^{tree}"),
        branch_name=identity.branch_name,
        commit_message=identity.commit_message,
    )
    contract = FrozenDevelopmentContract(
        task_digest="c" * 64,
        baseline_tree="d" * 64,
        allowed_scope=("add.txt", "app.txt", "delete.txt"),
        acceptance_set=("topology",),
        validation_set=("test",),
    )

    result = run_durable_local_git(
        repository_root=root,
        store=store,
        run_id="topology-run",
        task_id="local-change",
        lease_owner="fixture-worker",
        identity=identity,
        contract=contract,
        baseline_files={"app.txt": "old\n", "delete.txt": "remove\n"},
        worker=lambda _: {
            "operations": [
                {
                    "op": "add",
                    "path": "add.txt",
                    "expected_sha256": None,
                    "content": "added\n",
                },
                {
                    "op": "replace",
                    "path": "app.txt",
                    "expected_sha256": hashlib.sha256(b"old\n").hexdigest(),
                    "content": "new\n",
                },
                {
                    "op": "delete",
                    "path": "delete.txt",
                    "expected_sha256": hashlib.sha256(b"remove\n").hexdigest(),
                },
            ]
        },
        validator=lambda files: {
            "validation_results": {
                "test": {
                    "status": "PASS"
                    if files == {"add.txt": "added\n", "app.txt": "new\n"}
                    else "BLOCK",
                    "diagnostic": None,
                }
            },
            "satisfied_acceptance_items": ["topology"],
        },
        code_reviewer=_review,
        contract_reviewer=_review,
    )

    assert result["status"] == "PASS"
    assert _git(root, "diff", "--name-status", identity.expected_head_sha, "HEAD").splitlines() == [
        "A\tadd.txt",
        "M\tapp.txt",
        "D\tdelete.txt",
    ]
    assert _git(root, "show", "HEAD:add.txt") == "added"
    assert _git(root, "show", "HEAD:app.txt") == "new"


def test_baseline_topology_and_content_drift_block_before_durable_write(
    tmp_path: Path,
) -> None:
    for index, (baseline, expected) in enumerate((
        ({}, "BASELINE_SCOPE_MISMATCH"),
        ({"app.txt": "wrong\n"}, "BASELINE_CONTENT_MISMATCH"),
        (
            {"app.txt": "old\n", "absent.txt": "invented\n"},
            "BASELINE_SCOPE_MISMATCH",
        ),
    )):
        case_root = tmp_path / f"{index}-{expected}"
        case_root.mkdir()
        root, store, identity = _fixture(case_root)
        contract = FrozenDevelopmentContract(
            task_digest="e" * 64,
            baseline_tree="f" * 64,
            allowed_scope=("absent.txt", "app.txt"),
            acceptance_set=("content",),
            validation_set=("test",),
        )

        result = run_durable_local_git(
            repository_root=root,
            store=store,
            run_id="drift-run",
            task_id="local-change",
            lease_owner="fixture-worker",
            identity=identity,
            contract=contract,
            baseline_files=baseline,
            worker=_worker,
            validator=_validator,
            code_reviewer=_review,
            contract_reviewer=_review,
        )

        assert result["terminal_code"] == expected
        assert store.get_run("drift-run") is None
        assert _git(root, "branch", "--show-current") == "main"
