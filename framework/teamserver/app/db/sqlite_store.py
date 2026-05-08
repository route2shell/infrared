"""SQLite-backed V1 teamserver state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from ..store import (
    TASK_COMPLETED,
    TASK_DELIVERED,
    TASK_FAILED,
    TASK_PENDING,
    EventRecord,
    ResultRecord,
    SessionRecord,
    StoreError,
    TaskRecord,
    now_iso,
)


class SQLiteStore:
    """SQLite implementation of the V1 teamserver store contract."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._lock = Lock()
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def check_in(self, payload: Any) -> SessionRecord:
        with self._lock, self._connect() as conn:
            timestamp = now_iso()
            agent_id = payload.agent_id or f"agent-{uuid4()}"
            existing = conn.execute(
                "SELECT * FROM sessions WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()

            metadata_json = _to_json(payload.metadata)
            if existing:
                conn.execute(
                    """
                    UPDATE sessions
                    SET hostname = ?,
                        username = ?,
                        platform = ?,
                        last_seen = ?,
                        checkin_count = checkin_count + 1,
                        metadata_json = ?
                    WHERE agent_id = ?
                    """,
                    (
                        payload.hostname,
                        payload.username,
                        payload.platform,
                        timestamp,
                        metadata_json,
                        agent_id,
                    ),
                )
                session = conn.execute(
                    "SELECT * FROM sessions WHERE agent_id = ?",
                    (agent_id,),
                ).fetchone()
                self._event(
                    conn,
                    "agent.checkin",
                    f"Agent {agent_id} checked in",
                    {"session_id": session["session_id"], "agent_id": agent_id},
                )
                return _session_from_row(session)

            session_id = f"sess-{uuid4()}"
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id,
                    agent_id,
                    hostname,
                    username,
                    platform,
                    first_seen,
                    last_seen,
                    checkin_count,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    agent_id,
                    payload.hostname,
                    payload.username,
                    payload.platform,
                    timestamp,
                    timestamp,
                    1,
                    metadata_json,
                ),
            )
            self._event(
                conn,
                "agent.registered",
                f"Agent {agent_id} registered",
                {"session_id": session_id, "agent_id": agent_id},
            )
            session = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return _session_from_row(session)

    def list_sessions(self) -> list[SessionRecord]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY first_seen ASC"
            ).fetchall()
            return [_session_from_row(row) for row in rows]

    def get_session(self, session_id: str) -> SessionRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise StoreError(f"session not found: {session_id}")
            return _session_from_row(row)

    def create_task(self, payload: Any) -> TaskRecord:
        with self._lock, self._connect() as conn:
            session = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (payload.session_id,),
            ).fetchone()
            if session is None:
                raise StoreError(f"session not found: {payload.session_id}")

            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    session_id,
                    command,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (payload.session_id, payload.command, TASK_PENDING, now_iso()),
            )
            task_id = int(cursor.lastrowid)
            self._event(
                conn,
                "task.created",
                f"Task {task_id} created",
                {"task_id": task_id, "session_id": payload.session_id},
            )
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return _task_from_row(row)

    def list_tasks(self) -> list[TaskRecord]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY task_id ASC").fetchall()
            return [_task_from_row(row) for row in rows]

    def deliver_pending_tasks(self, agent_id: str) -> list[TaskRecord]:
        with self._lock, self._connect() as conn:
            session_id = self._session_id_for_agent(conn, agent_id)
            rows = conn.execute(
                """
                SELECT *
                FROM tasks
                WHERE session_id = ? AND status = ?
                ORDER BY task_id ASC
                """,
                (session_id, TASK_PENDING),
            ).fetchall()
            timestamp = now_iso()
            delivered: list[TaskRecord] = []

            for row in rows:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = ?, delivered_at = ?
                    WHERE task_id = ?
                    """,
                    (TASK_DELIVERED, timestamp, row["task_id"]),
                )
                self._event(
                    conn,
                    "task.delivered",
                    f"Task {row['task_id']} delivered",
                    {"task_id": row["task_id"], "session_id": session_id},
                )
                delivered.append(
                    TaskRecord(
                        task_id=row["task_id"],
                        session_id=row["session_id"],
                        command=row["command"],
                        status=TASK_DELIVERED,
                        created_at=row["created_at"],
                        delivered_at=timestamp,
                        completed_at=row["completed_at"],
                    )
                )

            return delivered

    def record_result(self, agent_id: str, payload: Any) -> ResultRecord:
        with self._lock, self._connect() as conn:
            session_id = self._session_id_for_agent(conn, agent_id)
            task = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (payload.task_id,),
            ).fetchone()
            if task is None:
                raise StoreError(f"task not found: {payload.task_id}")
            if task["session_id"] != session_id:
                raise StoreError("task does not belong to agent session")

            timestamp = now_iso()
            result_status = payload.status or TASK_COMPLETED
            task_status = TASK_FAILED if result_status == TASK_FAILED else TASK_COMPLETED
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, completed_at = ?
                WHERE task_id = ?
                """,
                (task_status, timestamp, payload.task_id),
            )
            conn.execute(
                """
                INSERT INTO results (
                    task_id,
                    session_id,
                    stdout,
                    stderr,
                    exit_code,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    stdout = excluded.stdout,
                    stderr = excluded.stderr,
                    exit_code = excluded.exit_code,
                    status = excluded.status,
                    created_at = excluded.created_at
                """,
                (
                    payload.task_id,
                    session_id,
                    payload.stdout,
                    payload.stderr,
                    payload.exit_code,
                    result_status,
                    timestamp,
                ),
            )
            self._event(
                conn,
                "result.received",
                f"Result received for task {payload.task_id}",
                {
                    "task_id": payload.task_id,
                    "session_id": session_id,
                    "exit_code": payload.exit_code,
                },
            )
            row = conn.execute(
                "SELECT * FROM results WHERE task_id = ?",
                (payload.task_id,),
            ).fetchone()
            return _result_from_row(row)

    def get_result(self, task_id: int) -> ResultRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM results WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise StoreError(f"result not found for task: {task_id}")
            return _result_from_row(row)

    def list_results(self) -> list[ResultRecord]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM results ORDER BY task_id ASC").fetchall()
            return [_result_from_row(row) for row in rows]

    def list_events(self) -> list[EventRecord]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY event_id ASC").fetchall()
            return [_event_from_row(row) for row in rows]

    def _initialize(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL UNIQUE,
                    hostname TEXT,
                    username TEXT,
                    platform TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    checkin_count INTEGER NOT NULL DEFAULT 1,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS results (
                    task_id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    stdout TEXT NOT NULL DEFAULT '',
                    stderr TEXT NOT NULL DEFAULT '',
                    exit_code INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id),
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _session_id_for_agent(self, conn: sqlite3.Connection, agent_id: str) -> str:
        row = conn.execute(
            "SELECT session_id FROM sessions WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        if row is None:
            raise StoreError(f"agent not found: {agent_id}")
        return str(row["session_id"])

    def _event(
        self,
        conn: sqlite3.Connection,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO events (event_type, message, created_at, metadata_json)
            VALUES (?, ?, ?, ?)
            """,
            (event_type, message, now_iso(), _to_json(metadata or {})),
        )


def _to_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True)


def _from_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    loaded = json.loads(value)
    if isinstance(loaded, dict):
        return loaded
    return {}


def _session_from_row(row: sqlite3.Row) -> SessionRecord:
    return SessionRecord(
        session_id=row["session_id"],
        agent_id=row["agent_id"],
        hostname=row["hostname"],
        username=row["username"],
        platform=row["platform"],
        first_seen=row["first_seen"],
        last_seen=row["last_seen"],
        checkin_count=row["checkin_count"],
        metadata=_from_json(row["metadata_json"]),
    )


def _task_from_row(row: sqlite3.Row) -> TaskRecord:
    return TaskRecord(
        task_id=row["task_id"],
        session_id=row["session_id"],
        command=row["command"],
        status=row["status"],
        created_at=row["created_at"],
        delivered_at=row["delivered_at"],
        completed_at=row["completed_at"],
    )


def _result_from_row(row: sqlite3.Row) -> ResultRecord:
    return ResultRecord(
        task_id=row["task_id"],
        session_id=row["session_id"],
        stdout=row["stdout"],
        stderr=row["stderr"],
        exit_code=row["exit_code"],
        status=row["status"],
        created_at=row["created_at"],
    )


def _event_from_row(row: sqlite3.Row) -> EventRecord:
    return EventRecord(
        event_id=row["event_id"],
        event_type=row["event_type"],
        message=row["message"],
        created_at=row["created_at"],
        metadata=_from_json(row["metadata_json"]),
    )
