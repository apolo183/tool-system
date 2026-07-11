from __future__ import annotations

from pathlib import Path

import pytest

from tool_system.orchestrator import (
    DurableOrchestratorStore,
    LeaseConflict,
    StateConflict,
)


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _store(tmp_path: Path, clock: Clock | None = None) -> DurableOrchestratorStore:
    return DurableOrchestratorStore(
        tmp_path / "state.sqlite3",
        forbidden_roots=(ROOT,),
        clock=clock or Clock(),
    )


def _task(store: DurableOrchestratorStore, *, max_attempts: int = 3) -> None:
    store.create_run("run-1", blueprint_ref="blueprint@sha", manifest_ref="manifest@sha")
    store.add_task(
        "run-1",
        "task-1",
        idempotency_key="run-1/task-1",
        expected_precondition_sha=SHA,
        max_attempts=max_attempts,
        checkpoint={"step": 0},
    )


def test_store_enables_required_sqlite_controls(tmp_path: Path) -> None:
    pragmas = _store(tmp_path).pragmas()

    assert pragmas["foreign_keys"] == 1
    assert str(pragmas["journal_mode"]).lower() == "wal"
    assert pragmas["synchronous"] == 2
    assert pragmas["busy_timeout"] == 5_000
    assert pragmas["schema_version"] == 2


def test_run_and_task_survive_store_reopen(tmp_path: Path) -> None:
    first = _store(tmp_path)
    _task(first)

    reopened = _store(tmp_path)

    assert reopened.get_run("run-1")["status"] == "ACTIVE"  # type: ignore[index]
    task = reopened.get_task("run-1", "task-1")
    assert task is not None
    assert task["status"] == "READY"
    assert task["attempt"] == 0
    assert task["checkpoint"] == {"step": 0}
    assert task["expected_precondition_sha"] == SHA


def test_claim_checkpoint_complete_and_run_completion(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _task(store)

    claimed = store.claim_task(
        "run-1", "task-1", lease_owner="worker-a", lease_seconds=30
    )
    assert claimed["status"] == "RUNNING"
    assert claimed["attempt"] == 1
    assert claimed["lease_owner"] == "worker-a"

    checkpointed = store.checkpoint_task(
        "run-1",
        "task-1",
        lease_owner="worker-a",
        attempt=1,
        checkpoint={"step": 1},
    )
    assert checkpointed["checkpoint"] == {"step": 1}

    completed = store.complete_task(
        "run-1", "task-1", lease_owner="worker-a", attempt=1
    )
    assert completed["status"] == "COMPLETED"
    assert completed["lease_owner"] is None
    assert store.complete_run("run-1")["status"] == "COMPLETED"


def test_unexpired_or_wrong_lease_blocks(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _task(store)
    store.claim_task("run-1", "task-1", lease_owner="worker-a", lease_seconds=30)

    with pytest.raises(LeaseConflict, match="unexpired"):
        store.claim_task("run-1", "task-1", lease_owner="worker-b", lease_seconds=30)
    with pytest.raises(LeaseConflict, match="owner"):
        store.checkpoint_task(
            "run-1",
            "task-1",
            lease_owner="worker-b",
            attempt=1,
            checkpoint={"bad": True},
        )
    with pytest.raises(LeaseConflict, match="attempt"):
        store.complete_task("run-1", "task-1", lease_owner="worker-a", attempt=2)


def test_expired_lease_recovers_and_next_claim_increments_attempt(
    tmp_path: Path,
) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    _task(store)
    store.claim_task("run-1", "task-1", lease_owner="worker-a", lease_seconds=10)
    clock.advance(11)

    recovered = store.recover_expired_leases()
    claimed = store.claim_task(
        "run-1", "task-1", lease_owner="worker-b", lease_seconds=10
    )

    assert recovered[0]["status"] == "READY"
    assert recovered[0]["attempt"] == 1
    assert claimed["attempt"] == 2
    assert claimed["lease_owner"] == "worker-b"


def test_expired_last_attempt_becomes_terminal_failed(tmp_path: Path) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    _task(store, max_attempts=1)
    store.claim_task("run-1", "task-1", lease_owner="worker-a", lease_seconds=1)
    clock.advance(2)

    recovered = store.recover_expired_leases()

    assert recovered[0]["status"] == "FAILED"
    with pytest.raises(StateConflict, match="terminal"):
        store.claim_task("run-1", "task-1", lease_owner="worker-b", lease_seconds=1)


def test_retryable_failure_requeues_until_attempt_budget_is_used(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    _task(store, max_attempts=2)
    store.claim_task("run-1", "task-1", lease_owner="worker", lease_seconds=10)
    first = store.fail_task(
        "run-1",
        "task-1",
        lease_owner="worker",
        attempt=1,
        retryable=True,
        checkpoint={"failed_at": 1},
    )
    store.claim_task("run-1", "task-1", lease_owner="worker", lease_seconds=10)
    second = store.fail_task(
        "run-1",
        "task-1",
        lease_owner="worker",
        attempt=2,
        retryable=True,
    )

    assert first["status"] == "READY"
    assert first["checkpoint"] == {"failed_at": 1}
    assert second["status"] == "FAILED"


def test_idempotent_registration_requires_identical_content(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _task(store)

    same = store.add_task(
        "run-1",
        "task-1",
        idempotency_key="run-1/task-1",
        expected_precondition_sha=SHA,
        max_attempts=3,
        checkpoint={"step": 0},
    )
    assert same["task_id"] == "task-1"

    with pytest.raises(StateConflict, match="different durable content"):
        store.add_task(
            "run-1",
            "task-1",
            idempotency_key="run-1/task-1",
            expected_precondition_sha="b" * 40,
            checkpoint={"step": 0},
        )
    with pytest.raises(StateConflict, match="another task"):
        store.add_task(
            "run-1",
            "task-2",
            idempotency_key="run-1/task-1",
            expected_precondition_sha=SHA,
        )


def test_database_path_inside_forbidden_root_or_symlink_blocks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside every forbidden_root"):
        DurableOrchestratorStore(
            tmp_path / "inside.sqlite3", forbidden_roots=(tmp_path,)
        )

    real = tmp_path / "real.sqlite3"
    real.touch()
    link = tmp_path / "link.sqlite3"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="must not be a symlink"):
        DurableOrchestratorStore(link, forbidden_roots=(ROOT,))


def test_run_cannot_complete_with_incomplete_or_empty_tasks(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.create_run("run-1", blueprint_ref="blueprint", manifest_ref="manifest")
    with pytest.raises(StateConflict, match="every task"):
        store.complete_run("run-1")
    store.add_task(
        "run-1",
        "task-1",
        idempotency_key="key",
        expected_precondition_sha=SHA,
    )
    with pytest.raises(StateConflict, match="every task"):
        store.complete_run("run-1")
