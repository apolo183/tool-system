from __future__ import annotations

import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from tool_system.orchestrator import (
    DurableOrchestratorStore,
    LeaseConflict,
    StateConflict,
)


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def _store(
    tmp_path: Path, **overrides: object
) -> DurableOrchestratorStore:
    values: dict[str, object] = {
        "forbidden_roots": (ROOT,),
    }
    values.update(overrides)
    return DurableOrchestratorStore(
        tmp_path / "state.sqlite3", **values  # type: ignore[arg-type]
    )


def _task(store: DurableOrchestratorStore) -> None:
    store.create_run("run", blueprint_ref="blueprint", manifest_ref="manifest")
    store.add_task(
        "run",
        "task",
        idempotency_key="task-key",
        expected_precondition_sha=SHA,
    )


def _active_effect(store: DurableOrchestratorStore) -> None:
    _task(store)
    store.claim_task("run", "task", lease_owner="worker", lease_seconds=100)
    store.plan_side_effect(
        "run",
        "task",
        effect_id="effect",
        effect_kind="fixture_write",
        action="write_fixture_receipt",
        resource_scope="local_fixture",
        idempotency_key="effect-key",
        expected_precondition_sha=SHA,
        payload={"value": 1},
        lease_owner="worker",
        task_attempt=1,
    )
    store.begin_side_effect("effect", lease_owner="worker", task_attempt=1)


def test_integrity_check_passes_for_healthy_store(tmp_path: Path) -> None:
    store = _store(tmp_path)

    assert store.integrity_check() == {
        "integrity_check": ("ok",),
        "foreign_key_violations": 0,
    }


def test_constructor_rejects_unsafe_parent_permissions(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    unsafe.chmod(0o777)
    try:
        with pytest.raises(ValueError, match="group/world-writable"):
            DurableOrchestratorStore(
                unsafe / "state.sqlite3", forbidden_roots=(ROOT,)
            )
    finally:
        unsafe.chmod(0o700)


@pytest.mark.parametrize("limit", [0, True])
def test_constructor_rejects_invalid_resource_limits(
    tmp_path: Path, limit: object
) -> None:
    with pytest.raises(ValueError, match="max_text_bytes"):
        _store(tmp_path, max_text_bytes=limit)


def test_text_and_json_resource_bounds_fail_before_mutation(tmp_path: Path) -> None:
    text_store = _store(tmp_path, max_text_bytes=8)
    with pytest.raises(ValueError, match="max_text_bytes"):
        text_store.create_run(
            "run-too-long", blueprint_ref="bp", manifest_ref="manifest"
        )
    assert text_store.get_run("missing") is None

    record_path = tmp_path / "record"
    record_path.mkdir()
    record_store = _store(record_path, max_record_bytes=16)
    record_store.create_run("run", blueprint_ref="bp", manifest_ref="manifest")
    with pytest.raises(ValueError, match="max_record_bytes"):
        record_store.add_task(
            "run",
            "task",
            idempotency_key="task-key",
            expected_precondition_sha=SHA,
            checkpoint={"payload": "x" * 32},
        )
    assert record_store.get_task("run", "task") is None


def test_invalid_types_and_nonfinite_json_fail_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(ValueError, match="run_id must be a string"):
        store.create_run(1, blueprint_ref="bp", manifest_ref="manifest")  # type: ignore[arg-type]
    store.create_run("run", blueprint_ref="bp", manifest_ref="manifest")
    with pytest.raises(ValueError, match="JSON mapping"):
        store.add_task(
            "run",
            "task",
            idempotency_key="key",
            expected_precondition_sha=SHA,
            checkpoint=[],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="finite JSON mapping"):
        store.add_task(
            "run",
            "task",
            idempotency_key="key",
            expected_precondition_sha=SHA,
            checkpoint={"value": float("nan")},
        )


def test_database_symlink_and_regular_file_substitution_are_detected(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.sqlite3"
    store = _store(tmp_path)
    backing = tmp_path / "backing.sqlite3"
    database.rename(backing)
    database.symlink_to(backing)
    with pytest.raises(StateConflict, match="symlink"):
        store.get_run("run")

    database.unlink()
    database.touch()
    with pytest.raises(StateConflict, match="identity changed"):
        store.get_run("run")


def test_database_hardlink_and_sidecar_symlink_are_detected(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    store = _store(tmp_path)
    hardlink = tmp_path / "state-copy.sqlite3"
    os.link(database, hardlink)
    with pytest.raises(StateConflict, match="exactly one hard link"):
        store.get_run("run")
    hardlink.unlink()

    sidecar = Path(f"{database}-wal")
    target = tmp_path / "sidecar-target"
    target.touch()
    sidecar.symlink_to(target)
    with pytest.raises(StateConflict, match="sidecar.*symlink"):
        store.get_run("run")


def test_database_parent_identity_substitution_is_detected(tmp_path: Path) -> None:
    parent = tmp_path / "state"
    parent.mkdir()
    store = _store(parent)
    moved = tmp_path / "moved"
    parent.rename(moved)
    parent.mkdir()

    with pytest.raises(StateConflict, match="parent identity changed"):
        store.get_run("run")


def test_side_effect_completion_rolls_back_when_outbox_insert_fails(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    _active_effect(store)
    connection = sqlite3.connect(tmp_path / "state.sqlite3")
    try:
        connection.execute(
            """
            CREATE TRIGGER reject_outbox BEFORE INSERT ON outbox
            BEGIN SELECT RAISE(ABORT, 'fault injection'); END
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="fault injection"):
        store.complete_side_effect(
            "effect",
            lease_owner="worker",
            task_attempt=1,
            expected_precondition_sha=SHA,
            result={"receipt": "ok"},
            event_kind="fixture.completed",
            event_payload={"effect_id": "effect"},
        )

    assert store.get_side_effect("effect")["state"] == "IN_PROGRESS"  # type: ignore[index]
    assert store.get_outbox_event("effect:completed") is None


def test_concurrent_claim_has_exactly_one_winner(tmp_path: Path) -> None:
    first = _store(tmp_path)
    _task(first)
    second = _store(tmp_path)
    barrier = Barrier(2)

    def claim(store: DurableOrchestratorStore, owner: str) -> str:
        barrier.wait()
        try:
            store.claim_task(
                "run", "task", lease_owner=owner, lease_seconds=30
            )
        except LeaseConflict:
            return "conflict"
        return owner

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = (
            executor.submit(claim, first, "worker-a"),
            executor.submit(claim, second, "worker-b"),
        )
        outcomes = {future.result() for future in futures}

    assert "conflict" in outcomes
    assert len(outcomes) == 2


def test_foreign_key_corruption_fails_integrity_check(tmp_path: Path) -> None:
    store = _store(tmp_path)
    connection = sqlite3.connect(tmp_path / "state.sqlite3")
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO tasks(
                run_id, task_id, status, attempt, max_attempts,
                idempotency_key, checkpoint_json, expected_precondition_sha,
                lease_owner, lease_expires_at, created_at, updated_at
            ) VALUES('missing', 'task', 'READY', 0, 1, 'key', '{}', ?,
                NULL, NULL, 1, 1)
            """,
            (SHA,),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(StateConflict, match="integrity check failed"):
        store.integrity_check()


def test_database_corruption_is_not_silently_recovered(tmp_path: Path) -> None:
    store = _store(tmp_path)
    database = tmp_path / "state.sqlite3"
    with database.open("r+b") as stream:
        stream.write(b"not-a-sqlite-database")

    with pytest.raises(sqlite3.DatabaseError):
        store.integrity_check()
