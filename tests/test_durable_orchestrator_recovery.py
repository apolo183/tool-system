from __future__ import annotations

import json
from pathlib import Path

import pytest

from tool_system.orchestrator import DurableOrchestratorStore, StateConflict


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class LocalIdempotentSink:
    """A persistent fixture sink that applies each durable key once."""

    def __init__(self, receipt_path: Path) -> None:
        self.receipt_path = receipt_path
        self.calls = 0

    def __call__(self, event: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        key = str(event["idempotency_key"])
        applied = (
            json.loads(self.receipt_path.read_text(encoding="utf-8"))
            if self.receipt_path.exists()
            else []
        )
        already_applied = key in applied
        if not already_applied:
            applied.append(key)
            self.receipt_path.write_text(
                json.dumps(applied, sort_keys=True), encoding="utf-8"
            )
        return {
            "idempotency_key": key,
            "already_applied": already_applied,
            "applied_count": len(applied),
        }

    def applied(self) -> list[str]:
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))


def _store(database: Path, clock: Clock) -> DurableOrchestratorStore:
    return DurableOrchestratorStore(
        database,
        forbidden_roots=(ROOT,),
        clock=clock,
    )


def _active_task(
    database: Path, clock: Clock, *, max_attempts: int = 3
) -> DurableOrchestratorStore:
    store = _store(database, clock)
    store.create_run("run", blueprint_ref="blueprint", manifest_ref="manifest")
    store.add_task(
        "run",
        "task",
        idempotency_key="task-key",
        expected_precondition_sha=SHA,
        max_attempts=max_attempts,
        checkpoint={"step": 0},
    )
    store.claim_task("run", "task", lease_owner="worker-1", lease_seconds=10)
    return store


def _completed_effect(store: DurableOrchestratorStore) -> None:
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    store.begin_side_effect("effect-1", lease_owner="worker-1", task_attempt=1)
    store.complete_side_effect(
        "effect-1",
        lease_owner="worker-1",
        task_attempt=1,
        expected_precondition_sha=SHA,
        result={"receipt": "complete"},
        event_kind="fixture.completed",
        event_payload={"effect_id": "effect-1"},
    )


def test_reopen_preserves_run_task_attempt_checkpoint_and_live_lease(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    first = _active_task(database, clock)
    first.checkpoint_task(
        "run",
        "task",
        lease_owner="worker-1",
        attempt=1,
        checkpoint={"step": 4, "cursor": "fixture-17"},
    )

    reopened = _store(database, clock)

    assert reopened.get_run("run")["status"] == "ACTIVE"  # type: ignore[index]
    task = reopened.get_task("run", "task")
    assert task is not None
    assert task["status"] == "RUNNING"
    assert task["attempt"] == 1
    assert task["checkpoint"] == {"step": 4, "cursor": "fixture-17"}
    assert task["lease_owner"] == "worker-1"
    assert task["lease_expires_at"] == 1_010.0


def test_expired_lease_recovers_and_reclaims_with_next_attempt(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    _active_task(database, clock)
    clock.advance(11)

    reopened = _store(database, clock)
    recovered = reopened.recover_expired_leases()
    reclaimed = reopened.claim_task(
        "run", "task", lease_owner="worker-2", lease_seconds=10
    )

    assert recovered[0]["status"] == "READY"
    assert recovered[0]["attempt"] == 1
    assert reclaimed["status"] == "RUNNING"
    assert reclaimed["attempt"] == 2
    assert reclaimed["lease_owner"] == "worker-2"


def test_retry_exhaustion_is_terminal_across_reopen(tmp_path: Path) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock, max_attempts=2)
    first_failure = store.fail_task(
        "run", "task", lease_owner="worker-1", attempt=1, retryable=True
    )
    assert first_failure["status"] == "READY"
    store.claim_task("run", "task", lease_owner="worker-2", lease_seconds=10)
    second_failure = store.fail_task(
        "run", "task", lease_owner="worker-2", attempt=2, retryable=True
    )

    reopened = _store(database, clock)

    assert second_failure["status"] == "FAILED"
    assert reopened.get_task("run", "task")["status"] == "FAILED"  # type: ignore[index]
    with pytest.raises(StateConflict, match="terminal task"):
        reopened.claim_task(
            "run", "task", lease_owner="worker-3", lease_seconds=10
        )


def test_duplicate_effect_registration_is_stable_and_mismatch_blocks_after_reopen(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    first = store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    reopened = _store(database, clock)
    same = reopened.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )

    assert same == first
    with pytest.raises(StateConflict, match="different side-effect content"):
        reopened.plan_side_effect(
            "run",
            "task",
            effect_id="effect-1",
            effect_kind="fixture_write",
            action="different_action",
            resource_scope="local_fixture",
            idempotency_key="effect-key",
            expected_precondition_sha=SHA,
            payload={"value": 1},
            lease_owner="worker-1",
            task_attempt=1,
        )
    with pytest.raises(StateConflict, match="precondition SHA"):
        reopened.plan_side_effect(
            "run",
            "task",
            effect_id="effect-1",
            effect_kind="fixture_write",
            action="write_fixture_receipt",
            resource_scope="local_fixture",
            idempotency_key="effect-key",
            expected_precondition_sha="b" * 40,
            payload={"value": 1},
            lease_owner="worker-1",
            task_attempt=1,
        )


def test_completion_and_pending_outbox_survive_reopen_without_effect_reexecution(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    _completed_effect(store)

    reopened = _store(database, clock)

    assert reopened.get_side_effect("effect-1")["state"] == "COMPLETED"  # type: ignore[index]
    assert reopened.get_outbox_event("effect-1:completed")["state"] == "PENDING"  # type: ignore[index]
    replay = reopened.begin_side_effect(
        "effect-1", lease_owner="worker-1", task_attempt=1
    )
    assert replay["already_completed"] is True
    assert replay["attempt"] == 1


def test_publisher_crash_reconciles_through_idempotent_local_sink_once(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    _completed_effect(store)
    sink = LocalIdempotentSink(tmp_path / "sink_receipts.json")

    claimed = store.claim_outbox_event(
        "effect-1:completed", lease_owner="publisher-1", lease_seconds=5
    )
    first_receipt = sink(claimed)
    assert first_receipt["already_applied"] is False
    # Simulated crash: deliberately omit mark_outbox_published.
    clock.advance(6)

    reopened = _store(database, clock)
    assert reopened.get_outbox_event("effect-1:completed")["state"] == "DELIVERING"  # type: ignore[index]
    recovered = reopened.recover_expired_outbox_leases()
    replay = reopened.reconcile_outbox(sink, lease_owner="publisher-2")
    no_repeat = reopened.reconcile_outbox(sink, lease_owner="publisher-2")

    assert recovered[0]["state"] == "PENDING"
    assert replay[0]["status"] == "PUBLISHED"
    assert replay[0]["receipt"]["already_applied"] is True  # type: ignore[index]
    assert reopened.get_outbox_event("effect-1:completed")["attempt"] == 2  # type: ignore[index]
    assert sink.calls == 2
    assert sink.applied() == ["effect-key:completed"]
    assert no_repeat == []


def test_ambiguous_in_progress_effect_remains_fail_closed_after_reopen(
    tmp_path: Path,
) -> None:
    clock = Clock()
    database = tmp_path / "state.sqlite3"
    store = _active_task(database, clock)
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect-1",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker-1",
        task_attempt=1,
    )
    store.begin_side_effect("effect-1", lease_owner="worker-1", task_attempt=1)

    reopened = _store(database, clock)

    with pytest.raises(StateConflict, match="reconcile by idempotency key"):
        reopened.begin_side_effect(
            "effect-1", lease_owner="worker-1", task_attempt=1
        )
