from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from tool_system.development_loop import FrozenDevelopmentContract
from tool_system.local_git import LocalGitIdentity, run_durable_local_git
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
