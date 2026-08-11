from __future__ import annotations

from pathlib import Path

import pytest

from tool_system.orchestrator import (
    AuthorizationReplay,
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
    assert pragmas["schema_version"] == 4
    assert len(str(pragmas["authorization_ledger_instance_id"])) == 64


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


def test_authorization_consumption_survives_reopen_and_burns_on_claim(
    tmp_path: Path,
) -> None:
    clock = Clock()
    first = _store(tmp_path, clock)
    ledger_id = first.authorization_ledger_instance_id

    consumed = first.consume_authorization_once(
        approval_source="github_issue_comment",
        repository="apolo183/tool-system",
        approval_record_id="91001",
        authorization_id="P14C-LIVE-EXEC-v2",
        approval_record_sha256="b" * 64,
        binding_sha256="c" * 64,
        executor_host_id="test-host",
        ledger_instance_id=ledger_id,
        expires_at_epoch_seconds=clock.value + 60,
    )
    reopened = _store(tmp_path, clock)

    assert reopened.authorization_ledger_instance_id == ledger_id
    assert consumed["approval_record_id"] == "91001"
    assert reopened.get_authorization_consumption(
        approval_source="github_issue_comment",
        repository="apolo183/tool-system",
        approval_record_id="91001",
    ) == consumed
    with pytest.raises(AuthorizationReplay, match="already consumed"):
        reopened.consume_authorization_once(
            approval_source="github_issue_comment",
            repository="apolo183/tool-system",
            approval_record_id="91001",
            authorization_id="P14C-LIVE-EXEC-v2",
            approval_record_sha256="b" * 64,
            binding_sha256="c" * 64,
            executor_host_id="test-host",
            ledger_instance_id=ledger_id,
            expires_at_epoch_seconds=clock.value + 60,
        )


def test_authorization_wrong_ledger_or_expiry_blocks_before_insert(
    tmp_path: Path,
) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    values: dict[str, object] = {
        "approval_source": "github_issue_comment",
        "repository": "apolo183/tool-system",
        "approval_record_id": "91002",
        "authorization_id": "P14C-LIVE-EXEC-v2",
        "approval_record_sha256": "b" * 64,
        "binding_sha256": "c" * 64,
        "executor_host_id": "test-host",
        "ledger_instance_id": "d" * 64,
        "expires_at_epoch_seconds": clock.value + 60,
    }
    with pytest.raises(StateConflict, match="ledger instance identity"):
        store.consume_authorization_once(**values)  # type: ignore[arg-type]
    values["ledger_instance_id"] = store.authorization_ledger_instance_id
    values["expires_at_epoch_seconds"] = clock.value - 1
    with pytest.raises(StateConflict, match="expired"):
        store.consume_authorization_once(**values)  # type: ignore[arg-type]
    assert store.get_authorization_consumption(
        approval_source="github_issue_comment",
        repository="apolo183/tool-system",
        approval_record_id="91002",
    ) is None


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


def test_active_lease_renews_at_controlled_fake_clock_boundary(
    tmp_path: Path,
) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    _task(store)
    claimed = store.claim_task(
        "run-1", "task-1", lease_owner="worker-a", lease_seconds=10
    )
    clock.advance(6)

    renewed = store.renew_task_lease(
        "run-1",
        "task-1",
        lease_owner="worker-a",
        attempt=1,
        lease_seconds=10,
    )
    clock.advance(5)
    checkpoint = store.checkpoint_task(
        "run-1",
        "task-1",
        lease_owner="worker-a",
        attempt=1,
        checkpoint={"renewed": True},
    )

    assert claimed["lease_expires_at"] == 1_010.0
    assert renewed["lease_expires_at"] == 1_016.0
    assert checkpoint["checkpoint"] == {"renewed": True}


def test_worker_call_consumption_survives_expiry_reopen_and_total_budget(
    tmp_path: Path,
) -> None:
    clock = Clock()
    store = _store(tmp_path, clock)
    _task(store, max_attempts=2)
    store.claim_task(
        "run-1", "task-1", lease_owner="worker-a", lease_seconds=10
    )

    first = store.begin_worker_call(
        "run-1",
        "task-1",
        request_sha256="b" * 64,
        max_calls=2,
        lease_owner="worker-a",
        task_attempt=1,
    )
    clock.advance(11)
    reopened = _store(tmp_path, clock)
    reopened.recover_expired_leases()
    reopened.claim_task(
        "run-1", "task-1", lease_owner="worker-b", lease_seconds=10
    )
    second = reopened.begin_worker_call(
        "run-1",
        "task-1",
        request_sha256="c" * 64,
        max_calls=2,
        lease_owner="worker-b",
        task_attempt=2,
    )

    assert first["state"] == "STARTED"
    assert first["ordinal"] == 1
    assert second["ordinal"] == 2
    assert reopened.worker_call_count("run-1", "task-1") == 2
    with pytest.raises(ValueError, match="stable safe code"):
        reopened.complete_worker_call(
            str(second["call_id"]),
            lease_owner="worker-b",
            task_attempt=2,
            status="BLOCK",
            terminal_code="raw timeout detail",
        )
    with pytest.raises(StateConflict, match="budget"):
        reopened.begin_worker_call(
            "run-1",
            "task-1",
            request_sha256="d" * 64,
            max_calls=2,
            lease_owner="worker-b",
            task_attempt=2,
        )


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
