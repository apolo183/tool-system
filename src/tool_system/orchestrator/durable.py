from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import stat
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RUN_STATUSES = {"ACTIVE", "COMPLETED", "FAILED"}
_TASK_STATUSES = {"READY", "RUNNING", "COMPLETED", "FAILED"}


class StateConflict(RuntimeError):
    """The requested durable transition conflicts with stored state."""


class LeaseConflict(StateConflict):
    """A task lease is missing, stale, or owned by another worker."""


class RetryExhausted(StateConflict):
    """A task cannot be claimed because its attempt budget is exhausted."""


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _canonical_json(
    value: Mapping[str, object] | None,
    label: str,
    *,
    max_bytes: int,
) -> str:
    if value is not None and not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON mapping")
    try:
        result = json.dumps(
            dict(value or {}),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError(f"{label} must be a finite JSON mapping") from exc
    if len(result.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds max_record_bytes")
    return result


def _require_text(value: str, label: str, *, max_bytes: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    result = value.strip()
    if not result:
        raise ValueError(f"{label} is required")
    if len(result.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds max_text_bytes")
    return result


def _require_sha(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("expected_precondition_sha must be a string")
    result = value.strip()
    if not _SHA_RE.fullmatch(result):
        raise ValueError("expected_precondition_sha must be a lowercase 40-character SHA")
    return result


class DurableOrchestratorStore:
    """SQLite-backed single-host orchestration state for local fixture use."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        forbidden_roots: tuple[str | Path, ...],
        clock: Callable[[], float] = time.time,
        busy_timeout_ms: int = 5_000,
        max_text_bytes: int = 4_096,
        max_record_bytes: int = 1024 * 1024,
    ) -> None:
        if not forbidden_roots:
            raise ValueError("forbidden_roots must be non-empty")
        raw_path = Path(database_path)
        if raw_path.exists() and raw_path.is_symlink():
            raise ValueError("database_path must not be a symlink")
        parent = raw_path.parent.resolve(strict=True)
        if raw_path.parent.is_symlink():
            raise ValueError("database parent must not be a symlink")
        parent_stat = parent.lstat()
        if not stat.S_ISDIR(parent_stat.st_mode):
            raise ValueError("database parent must be a directory")
        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ValueError("database parent must not be group/world-writable")
        resolved = parent / raw_path.name
        resolved_forbidden_roots: list[Path] = []
        for raw_root in forbidden_roots:
            root = Path(raw_root).resolve(strict=True)
            resolved_forbidden_roots.append(root)
            if _is_relative_to(resolved, root):
                raise ValueError("database_path must be outside every forbidden_root")
        if resolved.suffix not in {".sqlite", ".sqlite3", ".db"}:
            raise ValueError("database_path must use .sqlite, .sqlite3, or .db")
        if (
            not isinstance(busy_timeout_ms, int)
            or isinstance(busy_timeout_ms, bool)
            or busy_timeout_ms <= 0
        ):
            raise ValueError("busy_timeout_ms must be a positive integer")
        if (
            not isinstance(max_text_bytes, int)
            or isinstance(max_text_bytes, bool)
            or max_text_bytes <= 0
        ):
            raise ValueError("max_text_bytes must be a positive integer")
        if (
            not isinstance(max_record_bytes, int)
            or isinstance(max_record_bytes, bool)
            or max_record_bytes <= 0
        ):
            raise ValueError("max_record_bytes must be a positive integer")
        self.database_path = resolved
        self._clock = clock
        self._busy_timeout_ms = busy_timeout_ms
        self._max_text_bytes = max_text_bytes
        self._max_record_bytes = max_record_bytes
        self._database_parent = parent
        self._database_parent_identity = (parent_stat.st_dev, parent_stat.st_ino)
        self._forbidden_roots = tuple(resolved_forbidden_roots)
        self._database_identity: tuple[int, int] | None = None
        self._validate_database_path()
        self._initialize()

    def _text(self, value: str, label: str) -> str:
        return _require_text(value, label, max_bytes=self._max_text_bytes)

    def _json(self, value: Mapping[str, object] | None, label: str) -> str:
        return _canonical_json(value, label, max_bytes=self._max_record_bytes)

    def _now(self) -> float:
        value = self._clock()
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
        ):
            raise StateConflict("clock must return a finite number")
        return float(value)

    @staticmethod
    def _positive_integer(value: int, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive integer")
        return value

    @staticmethod
    def _positive_seconds(value: float, label: str) -> float:
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"{label} must be a finite positive number")
        return float(value)

    @staticmethod
    def _require_regular_single_link(path: Path, label: str) -> os.stat_result:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise StateConflict(f"{label} must not be a symlink")
        if not stat.S_ISREG(metadata.st_mode):
            raise StateConflict(f"{label} must be a regular file")
        if metadata.st_nlink != 1:
            raise StateConflict(f"{label} must have exactly one hard link")
        return metadata

    def _validate_database_path(self) -> None:
        try:
            parent_metadata = self._database_parent.lstat()
            resolved_parent = self._database_parent.resolve(strict=True)
        except OSError as exc:
            raise StateConflict("database parent identity is unavailable") from exc
        if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(
            parent_metadata.st_mode
        ):
            raise StateConflict("database parent must remain a non-symlink directory")
        if (parent_metadata.st_dev, parent_metadata.st_ino) != (
            self._database_parent_identity
        ):
            raise StateConflict("database parent identity changed")
        if resolved_parent != self._database_parent:
            raise StateConflict("database parent resolved path changed")
        if parent_metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise StateConflict("database parent became group/world-writable")
        for root in self._forbidden_roots:
            if _is_relative_to(self.database_path, root):
                raise StateConflict("database_path entered a forbidden_root")

        if self.database_path.exists() or self.database_path.is_symlink():
            metadata = self._require_regular_single_link(
                self.database_path, "database file"
            )
            identity = (metadata.st_dev, metadata.st_ino)
            if (
                self._database_identity is not None
                and identity != self._database_identity
            ):
                raise StateConflict("database file identity changed")

        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = Path(f"{self.database_path}{suffix}")
            if sidecar.exists() or sidecar.is_symlink():
                self._require_regular_single_link(
                    sidecar, f"database sidecar {suffix}"
                )

    def _connect(self) -> sqlite3.Connection:
        self._validate_database_path()
        connection = sqlite3.connect(
            self.database_path,
            timeout=self._busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        try:
            self._validate_database_path()
            metadata = self._require_regular_single_link(
                self.database_path, "database file"
            )
            identity = (metadata.st_dev, metadata.st_ino)
            if self._database_identity is None:
                self._database_identity = identity
            elif identity != self._database_identity:
                raise StateConflict("database file identity changed")
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            self._validate_database_path()
            return connection
        except Exception:
            connection.close()
            raise

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK (status IN ('ACTIVE','COMPLETED','FAILED')),
                    blueprint_ref TEXT NOT NULL,
                    manifest_ref TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('READY','RUNNING','COMPLETED','FAILED')),
                    attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
                    max_attempts INTEGER NOT NULL CHECK (max_attempts > 0),
                    idempotency_key TEXT NOT NULL UNIQUE,
                    checkpoint_json TEXT NOT NULL,
                    expected_precondition_sha TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_expires_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (run_id, task_id),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_resume
                    ON tasks(status, lease_expires_at, run_id, task_id);
                CREATE TABLE IF NOT EXISTS side_effects (
                    effect_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    effect_kind TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_scope TEXT NOT NULL CHECK (resource_scope = 'local_fixture'),
                    idempotency_key TEXT NOT NULL UNIQUE,
                    expected_precondition_sha TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('PLANNED','IN_PROGRESS','COMPLETED','FAILED')),
                    attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
                    result_json TEXT,
                    completed_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (run_id, task_id) REFERENCES tasks(run_id, task_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_side_effect_state
                    ON side_effects(state, run_id, task_id, effect_id);
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id TEXT PRIMARY KEY,
                    effect_id TEXT NOT NULL UNIQUE,
                    event_kind TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('PENDING','DELIVERING','PUBLISHED')),
                    attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
                    lease_owner TEXT,
                    lease_expires_at REAL,
                    receipt_json TEXT,
                    published_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (effect_id) REFERENCES side_effects(effect_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_outbox_delivery
                    ON outbox(state, lease_expires_at, event_id);
                """
            )
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row["value"]) == 1:
                connection.execute(
                    "UPDATE metadata SET value=? WHERE key='schema_version'",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row["value"]) != SCHEMA_VERSION:
                raise StateConflict(
                    f"unsupported schema version {row['value']}; expected {SCHEMA_VERSION}"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def pragmas(self) -> dict[str, object]:
        connection = self._connect()
        try:
            return {
                "foreign_keys": connection.execute("PRAGMA foreign_keys").fetchone()[0],
                "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0],
                "synchronous": connection.execute("PRAGMA synchronous").fetchone()[0],
                "busy_timeout": connection.execute("PRAGMA busy_timeout").fetchone()[0],
                "schema_version": int(
                    connection.execute(
                        "SELECT value FROM metadata WHERE key = 'schema_version'"
                    ).fetchone()[0]
                ),
            }
        finally:
            connection.close()

    def integrity_check(self) -> dict[str, object]:
        connection = self._connect()
        try:
            results = tuple(
                str(row[0])
                for row in connection.execute("PRAGMA integrity_check").fetchall()
            )
            foreign_key_violations = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            if results != ("ok",) or foreign_key_violations:
                raise StateConflict("database integrity check failed")
            return {
                "integrity_check": results,
                "foreign_key_violations": 0,
            }
        finally:
            connection.close()

    def create_run(
        self, run_id: str, *, blueprint_ref: str, manifest_ref: str
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        blueprint_ref = self._text(blueprint_ref, "blueprint_ref")
        manifest_ref = self._text(manifest_ref, "manifest_ref")
        now = self._now()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if existing is not None:
                if (
                    existing["blueprint_ref"] != blueprint_ref
                    or existing["manifest_ref"] != manifest_ref
                ):
                    raise StateConflict("run_id already exists with different references")
                return dict(existing)
            connection.execute(
                """
                INSERT INTO runs(
                    run_id, status, blueprint_ref, manifest_ref, created_at, updated_at
                ) VALUES(?, 'ACTIVE', ?, ?, ?, ?)
                """,
                (run_id, blueprint_ref, manifest_ref, now, now),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM runs WHERE run_id = ?", (run_id,)
                ).fetchone()
            )

    def add_task(
        self,
        run_id: str,
        task_id: str,
        *,
        idempotency_key: str,
        expected_precondition_sha: str,
        max_attempts: int = 3,
        checkpoint: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        idempotency_key = self._text(idempotency_key, "idempotency_key")
        expected_precondition_sha = _require_sha(expected_precondition_sha)
        max_attempts = self._positive_integer(max_attempts, "max_attempts")
        checkpoint_json = self._json(checkpoint, "checkpoint")
        now = self._now()
        with self._transaction() as connection:
            run = connection.execute(
                "SELECT status FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if run is None:
                raise StateConflict("run does not exist")
            if run["status"] != "ACTIVE":
                raise StateConflict("tasks can be added only to an ACTIVE run")
            existing = connection.execute(
                "SELECT * FROM tasks WHERE run_id = ? AND task_id = ?",
                (run_id, task_id),
            ).fetchone()
            if existing is not None:
                expected = (
                    idempotency_key,
                    expected_precondition_sha,
                    max_attempts,
                    checkpoint_json,
                )
                actual = (
                    existing["idempotency_key"],
                    existing["expected_precondition_sha"],
                    existing["max_attempts"],
                    existing["checkpoint_json"],
                )
                if actual != expected:
                    raise StateConflict("task already exists with different durable content")
                return self._task_record(existing)
            try:
                connection.execute(
                    """
                    INSERT INTO tasks(
                        run_id, task_id, status, attempt, max_attempts,
                        idempotency_key, checkpoint_json, expected_precondition_sha,
                        lease_owner, lease_expires_at, created_at, updated_at
                    ) VALUES(?, ?, 'READY', 0, ?, ?, ?, ?, NULL, NULL, ?, ?)
                    """,
                    (
                        run_id,
                        task_id,
                        max_attempts,
                        idempotency_key,
                        checkpoint_json,
                        expected_precondition_sha,
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict("idempotency_key already belongs to another task") from exc
            return self._task_record(
                connection.execute(
                    "SELECT * FROM tasks WHERE run_id = ? AND task_id = ?",
                    (run_id, task_id),
                ).fetchone()
            )

    def get_run(self, run_id: str) -> dict[str, object] | None:
        run_id = self._text(run_id, "run_id")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            connection.close()

    def get_task(self, run_id: str, task_id: str) -> dict[str, object] | None:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM tasks WHERE run_id = ? AND task_id = ?",
                (run_id, task_id),
            ).fetchone()
            return self._task_record(row) if row is not None else None
        finally:
            connection.close()

    def claim_task(
        self,
        run_id: str,
        task_id: str,
        *,
        lease_owner: str,
        lease_seconds: float,
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        lease_seconds = self._positive_seconds(lease_seconds, "lease_seconds")
        now = self._now()
        with self._transaction() as connection:
            row = self._task_row(connection, run_id, task_id)
            if row["status"] in {"COMPLETED", "FAILED"}:
                raise StateConflict(f"terminal task cannot be claimed: {row['status']}")
            if (
                row["status"] == "RUNNING"
                and row["lease_expires_at"] is not None
                and row["lease_expires_at"] > now
            ):
                raise LeaseConflict("task has an unexpired lease")
            if row["attempt"] >= row["max_attempts"]:
                connection.execute(
                    """
                    UPDATE tasks SET status='FAILED', lease_owner=NULL,
                        lease_expires_at=NULL, updated_at=?
                    WHERE run_id=? AND task_id=?
                    """,
                    (now, run_id, task_id),
                )
                raise RetryExhausted("task attempt budget is exhausted")
            connection.execute(
                """
                UPDATE tasks SET status='RUNNING', attempt=attempt+1,
                    lease_owner=?, lease_expires_at=?, updated_at=?
                WHERE run_id=? AND task_id=?
                """,
                (lease_owner, now + lease_seconds, now, run_id, task_id),
            )
            return self._task_record(self._task_row(connection, run_id, task_id))

    def checkpoint_task(
        self,
        run_id: str,
        task_id: str,
        *,
        lease_owner: str,
        attempt: int,
        checkpoint: Mapping[str, object],
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        attempt = self._positive_integer(attempt, "attempt")
        checkpoint_json = self._json(checkpoint, "checkpoint")
        now = self._now()
        with self._transaction() as connection:
            row = self._require_active_lease(
                connection, run_id, task_id, lease_owner, attempt, now
            )
            connection.execute(
                """
                UPDATE tasks SET checkpoint_json=?, updated_at=?
                WHERE run_id=? AND task_id=?
                """,
                (checkpoint_json, now, run_id, task_id),
            )
            return self._task_record(self._task_row(connection, run_id, task_id))

    def complete_task(
        self, run_id: str, task_id: str, *, lease_owner: str, attempt: int
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        attempt = self._positive_integer(attempt, "attempt")
        now = self._now()
        with self._transaction() as connection:
            self._require_active_lease(
                connection, run_id, task_id, lease_owner, attempt, now
            )
            connection.execute(
                """
                UPDATE tasks SET status='COMPLETED', lease_owner=NULL,
                    lease_expires_at=NULL, updated_at=?
                WHERE run_id=? AND task_id=?
                """,
                (now, run_id, task_id),
            )
            return self._task_record(self._task_row(connection, run_id, task_id))

    def fail_task(
        self,
        run_id: str,
        task_id: str,
        *,
        lease_owner: str,
        attempt: int,
        retryable: bool,
        checkpoint: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        attempt = self._positive_integer(attempt, "attempt")
        if not isinstance(retryable, bool):
            raise ValueError("retryable must be a boolean")
        checkpoint_json = (
            self._json(checkpoint, "checkpoint") if checkpoint is not None else None
        )
        now = self._now()
        with self._transaction() as connection:
            row = self._require_active_lease(
                connection, run_id, task_id, lease_owner, attempt, now
            )
            next_status = (
                "READY" if retryable and row["attempt"] < row["max_attempts"] else "FAILED"
            )
            checkpoint_json = checkpoint_json or row["checkpoint_json"]
            connection.execute(
                """
                UPDATE tasks SET status=?, checkpoint_json=?, lease_owner=NULL,
                    lease_expires_at=NULL, updated_at=?
                WHERE run_id=? AND task_id=?
                """,
                (next_status, checkpoint_json, now, run_id, task_id),
            )
            return self._task_record(self._task_row(connection, run_id, task_id))

    def recover_expired_leases(self) -> list[dict[str, object]]:
        now = self._now()
        recovered: list[dict[str, object]] = []
        with self._transaction() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                WHERE status='RUNNING' AND lease_expires_at IS NOT NULL
                    AND lease_expires_at <= ?
                ORDER BY run_id, task_id
                """,
                (now,),
            ).fetchall()
            for row in rows:
                next_status = (
                    "READY" if row["attempt"] < row["max_attempts"] else "FAILED"
                )
                connection.execute(
                    """
                    UPDATE tasks SET status=?, lease_owner=NULL,
                        lease_expires_at=NULL, updated_at=?
                    WHERE run_id=? AND task_id=?
                    """,
                    (next_status, now, row["run_id"], row["task_id"]),
                )
                recovered.append(
                    self._task_record(
                        self._task_row(connection, row["run_id"], row["task_id"])
                    )
                )
        return recovered

    def complete_run(self, run_id: str) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        now = self._now()
        with self._transaction() as connection:
            run = connection.execute(
                "SELECT * FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if run is None:
                raise StateConflict("run does not exist")
            counts = connection.execute(
                """
                SELECT COUNT(*) AS total,
                    SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS completed
                FROM tasks WHERE run_id=?
                """,
                (run_id,),
            ).fetchone()
            if counts["total"] == 0 or counts["total"] != counts["completed"]:
                raise StateConflict("run can complete only when every task is COMPLETED")
            connection.execute(
                "UPDATE runs SET status='COMPLETED', updated_at=? WHERE run_id=?",
                (now, run_id),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
            )

    def plan_side_effect(
        self,
        run_id: str,
        task_id: str,
        *,
        effect_id: str,
        effect_kind: str,
        action: str,
        resource_scope: str,
        idempotency_key: str,
        expected_precondition_sha: str,
        payload: Mapping[str, object],
        lease_owner: str,
        task_attempt: int,
    ) -> dict[str, object]:
        run_id = self._text(run_id, "run_id")
        task_id = self._text(task_id, "task_id")
        effect_id = self._text(effect_id, "effect_id")
        effect_kind = self._text(effect_kind, "effect_kind")
        action = self._text(action, "action")
        idempotency_key = self._text(idempotency_key, "idempotency_key")
        expected_precondition_sha = _require_sha(expected_precondition_sha)
        lease_owner = self._text(lease_owner, "lease_owner")
        task_attempt = self._positive_integer(task_attempt, "task_attempt")
        if resource_scope != "local_fixture":
            raise ValueError("resource_scope must be local_fixture")
        payload_json = self._json(payload, "payload")
        now = self._now()
        with self._transaction() as connection:
            task = self._require_active_lease(
                connection, run_id, task_id, lease_owner, task_attempt, now
            )
            if task["expected_precondition_sha"] != expected_precondition_sha:
                raise StateConflict("side effect precondition SHA does not match task")
            existing = connection.execute(
                "SELECT * FROM side_effects WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            expected = (
                effect_id,
                run_id,
                task_id,
                effect_kind,
                action,
                resource_scope,
                expected_precondition_sha,
                payload_json,
            )
            if existing is not None:
                actual = tuple(
                    existing[name]
                    for name in (
                        "effect_id",
                        "run_id",
                        "task_id",
                        "effect_kind",
                        "action",
                        "resource_scope",
                        "expected_precondition_sha",
                        "payload_json",
                    )
                )
                if actual != expected:
                    raise StateConflict(
                        "idempotency_key already exists with different side-effect content"
                    )
                return self._effect_record(existing)
            if connection.execute(
                "SELECT 1 FROM side_effects WHERE effect_id=?", (effect_id,)
            ).fetchone():
                raise StateConflict("effect_id already exists")
            connection.execute(
                """
                INSERT INTO side_effects(
                    effect_id, run_id, task_id, effect_kind, action, resource_scope,
                    idempotency_key, expected_precondition_sha, payload_json,
                    state, attempt, result_json, completed_at, created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, 'local_fixture', ?, ?, ?, 'PLANNED', 0,
                    NULL, NULL, ?, ?)
                """,
                (
                    effect_id,
                    run_id,
                    task_id,
                    effect_kind,
                    action,
                    idempotency_key,
                    expected_precondition_sha,
                    payload_json,
                    now,
                    now,
                ),
            )
            return self._effect_record(self._effect_row(connection, effect_id))

    def begin_side_effect(
        self,
        effect_id: str,
        *,
        lease_owner: str,
        task_attempt: int,
    ) -> dict[str, object]:
        effect_id = self._text(effect_id, "effect_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        task_attempt = self._positive_integer(task_attempt, "task_attempt")
        now = self._now()
        with self._transaction() as connection:
            effect = self._effect_row(connection, effect_id)
            self._require_active_lease(
                connection,
                effect["run_id"],
                effect["task_id"],
                lease_owner,
                task_attempt,
                now,
            )
            if effect["state"] == "COMPLETED":
                record = self._effect_record(effect)
                record["already_completed"] = True
                return record
            if effect["state"] == "IN_PROGRESS":
                raise StateConflict(
                    "side effect is already IN_PROGRESS; reconcile by idempotency key"
                )
            connection.execute(
                """
                UPDATE side_effects SET state='IN_PROGRESS', attempt=attempt+1,
                    updated_at=? WHERE effect_id=?
                """,
                (now, effect_id),
            )
            record = self._effect_record(self._effect_row(connection, effect_id))
            record["already_completed"] = False
            return record

    def complete_side_effect(
        self,
        effect_id: str,
        *,
        lease_owner: str,
        task_attempt: int,
        expected_precondition_sha: str,
        result: Mapping[str, object],
        event_kind: str,
        event_payload: Mapping[str, object],
    ) -> dict[str, object]:
        effect_id = self._text(effect_id, "effect_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        task_attempt = self._positive_integer(task_attempt, "task_attempt")
        expected_precondition_sha = _require_sha(expected_precondition_sha)
        event_kind = self._text(event_kind, "event_kind")
        result_json = self._json(result, "result")
        event_payload_json = self._json(event_payload, "event_payload")
        now = self._now()
        with self._transaction() as connection:
            effect = self._effect_row(connection, effect_id)
            if effect["expected_precondition_sha"] != expected_precondition_sha:
                raise StateConflict("side effect completion precondition SHA mismatch")
            self._require_active_lease(
                connection,
                effect["run_id"],
                effect["task_id"],
                lease_owner,
                task_attempt,
                now,
            )
            event_id = self._text(f"{effect_id}:completed", "event_id")
            event_key = self._text(
                f"{effect['idempotency_key']}:completed", "event idempotency_key"
            )
            if effect["state"] == "COMPLETED":
                outbox = self._outbox_row(connection, event_id)
                if (
                    effect["result_json"] != result_json
                    or outbox["event_kind"] != event_kind
                    or outbox["payload_json"] != event_payload_json
                ):
                    raise StateConflict(
                        "completed side effect cannot be rewritten with different content"
                    )
                return {
                    "effect": self._effect_record(effect),
                    "outbox": self._outbox_record(outbox),
                    "already_completed": True,
                }
            if effect["state"] != "IN_PROGRESS":
                raise StateConflict("side effect must be IN_PROGRESS before completion")
            connection.execute(
                """
                UPDATE side_effects SET state='COMPLETED', result_json=?,
                    completed_at=?, updated_at=? WHERE effect_id=?
                """,
                (result_json, now, now, effect_id),
            )
            connection.execute(
                """
                INSERT INTO outbox(
                    event_id, effect_id, event_kind, idempotency_key, payload_json,
                    state, attempt, lease_owner, lease_expires_at, receipt_json,
                    published_at, created_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, 'PENDING', 0, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (
                    event_id,
                    effect_id,
                    event_kind,
                    event_key,
                    event_payload_json,
                    now,
                    now,
                ),
            )
            return {
                "effect": self._effect_record(self._effect_row(connection, effect_id)),
                "outbox": self._outbox_record(self._outbox_row(connection, event_id)),
                "already_completed": False,
            }

    def fail_side_effect(
        self,
        effect_id: str,
        *,
        lease_owner: str,
        task_attempt: int,
        result: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        effect_id = self._text(effect_id, "effect_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        task_attempt = self._positive_integer(task_attempt, "task_attempt")
        result_json = self._json(result, "result")
        now = self._now()
        with self._transaction() as connection:
            effect = self._effect_row(connection, effect_id)
            self._require_active_lease(
                connection,
                effect["run_id"],
                effect["task_id"],
                lease_owner,
                task_attempt,
                now,
            )
            if effect["state"] != "IN_PROGRESS":
                raise StateConflict("only an IN_PROGRESS side effect can fail")
            connection.execute(
                """
                UPDATE side_effects SET state='FAILED', result_json=?, updated_at=?
                WHERE effect_id=?
                """,
                (result_json, now, effect_id),
            )
            return self._effect_record(self._effect_row(connection, effect_id))

    def get_side_effect(self, effect_id: str) -> dict[str, object] | None:
        effect_id = self._text(effect_id, "effect_id")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM side_effects WHERE effect_id=?", (effect_id,)
            ).fetchone()
            return self._effect_record(row) if row is not None else None
        finally:
            connection.close()

    def get_outbox_event(self, event_id: str) -> dict[str, object] | None:
        event_id = self._text(event_id, "event_id")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM outbox WHERE event_id=?", (event_id,)
            ).fetchone()
            return self._outbox_record(row) if row is not None else None
        finally:
            connection.close()

    def pending_outbox(self, *, limit: int = 100) -> list[dict[str, object]]:
        limit = self._positive_integer(limit, "limit")
        now = self._now()
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT * FROM outbox
                WHERE state='PENDING'
                   OR (state='DELIVERING' AND lease_expires_at <= ?)
                ORDER BY created_at, event_id LIMIT ?
                """,
                (now, limit),
            ).fetchall()
            return [self._outbox_record(row) for row in rows]
        finally:
            connection.close()

    def claim_outbox_event(
        self, event_id: str, *, lease_owner: str, lease_seconds: float
    ) -> dict[str, object]:
        event_id = self._text(event_id, "event_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        lease_seconds = self._positive_seconds(lease_seconds, "lease_seconds")
        now = self._now()
        with self._transaction() as connection:
            row = self._outbox_row(connection, event_id)
            if row["state"] == "PUBLISHED":
                record = self._outbox_record(row)
                record["already_published"] = True
                return record
            if (
                row["state"] == "DELIVERING"
                and row["lease_expires_at"] is not None
                and row["lease_expires_at"] > now
            ):
                raise LeaseConflict("outbox event has an unexpired lease")
            connection.execute(
                """
                UPDATE outbox SET state='DELIVERING', attempt=attempt+1,
                    lease_owner=?, lease_expires_at=?, updated_at=?
                WHERE event_id=?
                """,
                (lease_owner, now + lease_seconds, now, event_id),
            )
            record = self._outbox_record(self._outbox_row(connection, event_id))
            record["already_published"] = False
            return record

    def mark_outbox_published(
        self,
        event_id: str,
        *,
        lease_owner: str,
        receipt: Mapping[str, object],
    ) -> dict[str, object]:
        event_id = self._text(event_id, "event_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        receipt_json = self._json(receipt, "receipt")
        now = self._now()
        with self._transaction() as connection:
            row = self._outbox_row(connection, event_id)
            if row["state"] == "PUBLISHED":
                if row["receipt_json"] != receipt_json:
                    raise StateConflict("published outbox receipt cannot change")
                return self._outbox_record(row)
            if row["state"] != "DELIVERING" or row["lease_owner"] != lease_owner:
                raise LeaseConflict("outbox delivery lease owner does not match")
            if row["lease_expires_at"] is None or row["lease_expires_at"] <= now:
                raise LeaseConflict("outbox delivery lease is expired")
            connection.execute(
                """
                UPDATE outbox SET state='PUBLISHED', receipt_json=?, published_at=?,
                    lease_owner=NULL, lease_expires_at=NULL, updated_at=?
                WHERE event_id=?
                """,
                (receipt_json, now, now, event_id),
            )
            return self._outbox_record(self._outbox_row(connection, event_id))

    def release_outbox_event(self, event_id: str, *, lease_owner: str) -> dict[str, object]:
        event_id = self._text(event_id, "event_id")
        lease_owner = self._text(lease_owner, "lease_owner")
        now = self._now()
        with self._transaction() as connection:
            row = self._outbox_row(connection, event_id)
            if row["state"] != "DELIVERING" or row["lease_owner"] != lease_owner:
                raise LeaseConflict("outbox delivery lease owner does not match")
            connection.execute(
                """
                UPDATE outbox SET state='PENDING', lease_owner=NULL,
                    lease_expires_at=NULL, updated_at=? WHERE event_id=?
                """,
                (now, event_id),
            )
            return self._outbox_record(self._outbox_row(connection, event_id))

    def recover_expired_outbox_leases(self) -> list[dict[str, object]]:
        now = self._now()
        with self._transaction() as connection:
            rows = connection.execute(
                """
                SELECT event_id FROM outbox
                WHERE state='DELIVERING' AND lease_expires_at <= ?
                ORDER BY event_id
                """,
                (now,),
            ).fetchall()
            recovered: list[dict[str, object]] = []
            for row in rows:
                connection.execute(
                    """
                    UPDATE outbox SET state='PENDING', lease_owner=NULL,
                        lease_expires_at=NULL, updated_at=? WHERE event_id=?
                    """,
                    (now, row["event_id"]),
                )
                recovered.append(
                    self._outbox_record(self._outbox_row(connection, row["event_id"]))
                )
            return recovered

    def reconcile_outbox(
        self,
        deliver: Callable[[dict[str, object]], Mapping[str, object]],
        *,
        lease_owner: str,
        lease_seconds: float = 30.0,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        lease_owner = self._text(lease_owner, "lease_owner")
        self._positive_seconds(lease_seconds, "lease_seconds")
        self._positive_integer(limit, "limit")
        results: list[dict[str, object]] = []
        for pending in self.pending_outbox(limit=limit):
            event_id = str(pending["event_id"])
            claimed = self.claim_outbox_event(
                event_id, lease_owner=lease_owner, lease_seconds=lease_seconds
            )
            if claimed.get("already_published") is True:
                results.append(claimed)
                continue
            try:
                receipt = deliver(claimed)
            except Exception as exc:
                self.release_outbox_event(event_id, lease_owner=lease_owner)
                results.append(
                    {
                        "event_id": event_id,
                        "status": "DELIVERY_FAILED",
                        "error_type": type(exc).__name__,
                    }
                )
            else:
                published = self.mark_outbox_published(
                    event_id, lease_owner=lease_owner, receipt=receipt
                )
                published["status"] = "PUBLISHED"
                results.append(published)
        return results

    @staticmethod
    def _task_record(row: sqlite3.Row) -> dict[str, object]:
        record = dict(row)
        record["checkpoint"] = json.loads(record.pop("checkpoint_json"))
        return record

    @staticmethod
    def _effect_record(row: sqlite3.Row) -> dict[str, object]:
        record = dict(row)
        record["payload"] = json.loads(record.pop("payload_json"))
        result_json = record.pop("result_json")
        record["result"] = json.loads(result_json) if result_json is not None else None
        return record

    @staticmethod
    def _outbox_record(row: sqlite3.Row) -> dict[str, object]:
        record = dict(row)
        record["payload"] = json.loads(record.pop("payload_json"))
        receipt_json = record.pop("receipt_json")
        record["receipt"] = json.loads(receipt_json) if receipt_json is not None else None
        return record

    @staticmethod
    def _task_row(
        connection: sqlite3.Connection, run_id: str, task_id: str
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM tasks WHERE run_id=? AND task_id=?", (run_id, task_id)
        ).fetchone()
        if row is None:
            raise StateConflict("task does not exist")
        return row

    def _require_active_lease(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        task_id: str,
        lease_owner: str,
        attempt: int,
        now: float,
    ) -> sqlite3.Row:
        row = self._task_row(connection, run_id, task_id)
        if row["status"] != "RUNNING":
            raise LeaseConflict("task is not RUNNING")
        if row["lease_owner"] != lease_owner:
            raise LeaseConflict("lease owner does not match")
        if row["attempt"] != attempt:
            raise LeaseConflict("attempt does not match active lease")
        if row["lease_expires_at"] is None or row["lease_expires_at"] <= now:
            raise LeaseConflict("lease is expired")
        return row

    @staticmethod
    def _effect_row(connection: sqlite3.Connection, effect_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM side_effects WHERE effect_id=?", (effect_id,)
        ).fetchone()
        if row is None:
            raise StateConflict("side effect does not exist")
        return row

    @staticmethod
    def _outbox_row(connection: sqlite3.Connection, event_id: str) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM outbox WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is None:
            raise StateConflict("outbox event does not exist")
        return row
