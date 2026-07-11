from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tool_system.orchestrator import DurableOrchestratorStore, LeaseConflict, StateConflict


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _active_store(
    tmp_path: Path, clock: Clock | None = None
) -> DurableOrchestratorStore:
    store = DurableOrchestratorStore(
        tmp_path / "state.sqlite3",
        forbidden_roots=(ROOT,),
        clock=clock or Clock(),
    )
    store.create_run("run", blueprint_ref="blueprint", manifest_ref="manifest")
    store.add_task(
        "run",
        "task",
        idempotency_key="task-key",
        expected_precondition_sha=SHA,
    )
    store.claim_task("run", "task", lease_owner="worker", lease_seconds=100)
    return store


def _plan(store: DurableOrchestratorStore, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "effect_id": "effect-1",
        "effect_kind": "fixture_write",
        "action": "write_fixture_receipt",
        "resource_scope": "local_fixture",
        "idempotency_key": "effect-key",
        "expected_precondition_sha": SHA,
        "payload": {"value": 1},
        "lease_owner": "worker",
        "task_attempt": 1,
    }
    values.update(overrides)
    return store.plan_side_effect("run", "task", **values)  # type: ignore[arg-type]


def _complete(store: DurableOrchestratorStore) -> dict[str, object]:
    store.begin_side_effect("effect-1", lease_owner="worker", task_attempt=1)
    return store.complete_side_effect(
        "effect-1",
        lease_owner="worker",
        task_attempt=1,
        expected_precondition_sha=SHA,
        result={"receipt": "ok"},
        event_kind="fixture.completed",
        event_payload={"effect_id": "effect-1"},
    )


def test_plan_is_idempotent_only_for_identical_content(tmp_path: Path) -> None:
    store = _active_store(tmp_path)
    first = _plan(store)
    same = _plan(store)

    assert first["state"] == "PLANNED"
    assert same["effect_id"] == first["effect_id"]
    with pytest.raises(StateConflict, match="different side-effect content"):
        _plan(store, action="different")
    with pytest.raises(StateConflict, match="precondition SHA"):
        _plan(store, expected_precondition_sha="b" * 40)
    with pytest.raises(ValueError, match="local_fixture"):
        _plan(store, resource_scope="remote_repository")


def test_task_precondition_and_active_lease_are_required(tmp_path: Path) -> None:
    store = _active_store(tmp_path)
    with pytest.raises(StateConflict, match="precondition SHA"):
        _plan(store, expected_precondition_sha="b" * 40)
    with pytest.raises(LeaseConflict, match="owner"):
        _plan(store, lease_owner="other")


def test_completion_and_outbox_insert_are_transactional_and_replay_safe(
    tmp_path: Path,
) -> None:
    store = _active_store(tmp_path)
    _plan(store)
    completed = _complete(store)

    assert completed["effect"]["state"] == "COMPLETED"  # type: ignore[index]
    assert completed["outbox"]["state"] == "PENDING"  # type: ignore[index]
    assert completed["already_completed"] is False

    replay = store.complete_side_effect(
        "effect-1",
        lease_owner="worker",
        task_attempt=1,
        expected_precondition_sha=SHA,
        result={"receipt": "ok"},
        event_kind="fixture.completed",
        event_payload={"effect_id": "effect-1"},
    )
    assert replay["already_completed"] is True
    assert store.begin_side_effect(
        "effect-1", lease_owner="worker", task_attempt=1
    )["already_completed"] is True


def test_completed_content_and_precondition_cannot_change(tmp_path: Path) -> None:
    store = _active_store(tmp_path)
    _plan(store)
    _complete(store)

    with pytest.raises(StateConflict, match="precondition SHA mismatch"):
        store.complete_side_effect(
            "effect-1",
            lease_owner="worker",
            task_attempt=1,
            expected_precondition_sha="b" * 40,
            result={"receipt": "ok"},
            event_kind="fixture.completed",
            event_payload={"effect_id": "effect-1"},
        )
    with pytest.raises(StateConflict, match="cannot be rewritten"):
        store.complete_side_effect(
            "effect-1",
            lease_owner="worker",
            task_attempt=1,
            expected_precondition_sha=SHA,
            result={"receipt": "changed"},
            event_kind="fixture.completed",
            event_payload={"effect_id": "effect-1"},
        )


def test_in_progress_effect_fails_closed_for_ambiguous_replay(tmp_path: Path) -> None:
    store = _active_store(tmp_path)
    _plan(store)
    store.begin_side_effect("effect-1", lease_owner="worker", task_attempt=1)

    with pytest.raises(StateConflict, match="reconcile by idempotency key"):
        store.begin_side_effect("effect-1", lease_owner="worker", task_attempt=1)


def test_outbox_lease_publish_and_receipt_are_idempotent(tmp_path: Path) -> None:
    store = _active_store(tmp_path)
    _plan(store)
    _complete(store)
    event_id = "effect-1:completed"
    claimed = store.claim_outbox_event(
        event_id, lease_owner="publisher", lease_seconds=20
    )
    assert claimed["attempt"] == 1
    with pytest.raises(LeaseConflict, match="unexpired"):
        store.claim_outbox_event(event_id, lease_owner="other", lease_seconds=20)

    published = store.mark_outbox_published(
        event_id, lease_owner="publisher", receipt={"sink": "ok"}
    )
    assert published["state"] == "PUBLISHED"
    assert store.mark_outbox_published(
        event_id, lease_owner="publisher", receipt={"sink": "ok"}
    )["state"] == "PUBLISHED"
    with pytest.raises(StateConflict, match="receipt cannot change"):
        store.mark_outbox_published(
            event_id, lease_owner="publisher", receipt={"sink": "changed"}
        )


def test_expired_outbox_lease_recovers_for_reconciliation(tmp_path: Path) -> None:
    clock = Clock()
    store = _active_store(tmp_path, clock)
    _plan(store)
    _complete(store)
    store.claim_outbox_event(
        "effect-1:completed", lease_owner="publisher", lease_seconds=5
    )
    clock.advance(6)

    recovered = store.recover_expired_outbox_leases()

    assert recovered[0]["state"] == "PENDING"
    assert recovered[0]["lease_owner"] is None


def test_reconciliation_publishes_once_and_failed_delivery_requeues(
    tmp_path: Path,
) -> None:
    store = _active_store(tmp_path)
    _plan(store)
    _complete(store)
    failures = 0

    def failing(event: dict[str, object]) -> dict[str, object]:
        nonlocal failures
        failures += 1
        raise RuntimeError("fixture unavailable")

    failed = store.reconcile_outbox(failing, lease_owner="publisher")
    assert failed == [
        {
            "event_id": "effect-1:completed",
            "status": "DELIVERY_FAILED",
            "error_type": "RuntimeError",
        }
    ]
    assert store.get_outbox_event("effect-1:completed")["state"] == "PENDING"  # type: ignore[index]

    applied: set[str] = set()

    def sink(event: dict[str, object]) -> dict[str, object]:
        applied.add(str(event["idempotency_key"]))
        return {"applied_key": event["idempotency_key"]}

    published = store.reconcile_outbox(sink, lease_owner="publisher")
    replay = store.reconcile_outbox(sink, lease_owner="publisher")

    assert published[0]["status"] == "PUBLISHED"
    assert replay == []
    assert applied == {"effect-key:completed"}
    assert failures == 1


def test_schema_version_one_is_migrated_to_two(tmp_path: Path) -> None:
    database = tmp_path / "migration.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("INSERT INTO metadata VALUES('schema_version', '1')")
    connection.commit()
    connection.close()

    store = DurableOrchestratorStore(database, forbidden_roots=(ROOT,))

    assert store.pragmas()["schema_version"] == 2
