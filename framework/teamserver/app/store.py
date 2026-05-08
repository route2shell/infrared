"""In-memory V1 teamserver state.

Phase 2 uses this store to prove the API lifecycle. Phase 3 replaces the
storage backend with SQLite while preserving the route behavior.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


TASK_PENDING = "pending"
TASK_DELIVERED = "delivered"
TASK_COMPLETED = "completed"
TASK_FAILED = "failed"


class StoreError(Exception):
    """Raised when a requested V1 state transition is invalid."""


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class SessionRecord:
    session_id: str
    agent_id: str
    hostname: str | None
    username: str | None
    platform: str | None
    first_seen: str
    last_seen: str
    checkin_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRecord:
    task_id: int
    session_id: str
    command: str
    status: str
    created_at: str
    delivered_at: str | None = None
    completed_at: str | None = None


@dataclass
class ResultRecord:
    task_id: int
    session_id: str
    stdout: str
    stderr: str
    exit_code: int
    status: str
    created_at: str


@dataclass
class EventRecord:
    event_id: int
    event_type: str
    message: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryStore:
    """Small thread-safe store for the V1 API lifecycle."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, SessionRecord] = {}
        self._agent_to_session: dict[str, str] = {}
        self._tasks: dict[int, TaskRecord] = {}
        self._results: dict[int, ResultRecord] = {}
        self._events: list[EventRecord] = []
        self._next_task_id = 1
        self._next_event_id = 1

    def check_in(self, payload: Any) -> SessionRecord:
        with self._lock:
            timestamp = now_iso()
            agent_id = payload.agent_id or f"agent-{uuid4()}"

            if agent_id in self._agent_to_session:
                session_id = self._agent_to_session[agent_id]
                session = self._sessions[session_id]
                session.hostname = payload.hostname
                session.username = payload.username
                session.platform = payload.platform
                session.metadata = payload.metadata
                session.last_seen = timestamp
                session.checkin_count += 1
                self._event(
                    "agent.checkin",
                    f"Agent {agent_id} checked in",
                    {"session_id": session_id, "agent_id": agent_id},
                )
                return session

            session_id = f"sess-{uuid4()}"
            session = SessionRecord(
                session_id=session_id,
                agent_id=agent_id,
                hostname=payload.hostname,
                username=payload.username,
                platform=payload.platform,
                first_seen=timestamp,
                last_seen=timestamp,
                metadata=payload.metadata,
            )
            self._sessions[session_id] = session
            self._agent_to_session[agent_id] = session_id
            self._event(
                "agent.registered",
                f"Agent {agent_id} registered",
                {"session_id": session_id, "agent_id": agent_id},
            )
            return session

    def list_sessions(self) -> list[SessionRecord]:
        with self._lock:
            return list(self._sessions.values())

    def get_session(self, session_id: str) -> SessionRecord:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise StoreError(f"session not found: {session_id}") from exc

    def create_task(self, payload: Any) -> TaskRecord:
        with self._lock:
            if payload.session_id not in self._sessions:
                raise StoreError(f"session not found: {payload.session_id}")

            task = TaskRecord(
                task_id=self._next_task_id,
                session_id=payload.session_id,
                command=payload.command,
                status=TASK_PENDING,
                created_at=now_iso(),
            )
            self._tasks[task.task_id] = task
            self._next_task_id += 1
            self._event(
                "task.created",
                f"Task {task.task_id} created",
                {"task_id": task.task_id, "session_id": task.session_id},
            )
            return task

    def list_tasks(self) -> list[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())

    def deliver_pending_tasks(self, agent_id: str) -> list[TaskRecord]:
        with self._lock:
            session_id = self._session_id_for_agent(agent_id)
            delivered: list[TaskRecord] = []
            timestamp = now_iso()

            for task in self._tasks.values():
                if task.session_id != session_id or task.status != TASK_PENDING:
                    continue
                task.status = TASK_DELIVERED
                task.delivered_at = timestamp
                delivered.append(task)
                self._event(
                    "task.delivered",
                    f"Task {task.task_id} delivered",
                    {"task_id": task.task_id, "session_id": session_id},
                )

            return delivered

    def record_result(self, agent_id: str, payload: Any) -> ResultRecord:
        with self._lock:
            session_id = self._session_id_for_agent(agent_id)
            task = self._tasks.get(payload.task_id)
            if task is None:
                raise StoreError(f"task not found: {payload.task_id}")
            if task.session_id != session_id:
                raise StoreError("task does not belong to agent session")

            timestamp = now_iso()
            result_status = payload.status or TASK_COMPLETED
            task.status = TASK_FAILED if result_status == TASK_FAILED else TASK_COMPLETED
            task.completed_at = timestamp

            result = ResultRecord(
                task_id=task.task_id,
                session_id=session_id,
                stdout=payload.stdout,
                stderr=payload.stderr,
                exit_code=payload.exit_code,
                status=result_status,
                created_at=timestamp,
            )
            self._results[result.task_id] = result
            self._event(
                "result.received",
                f"Result received for task {task.task_id}",
                {
                    "task_id": task.task_id,
                    "session_id": session_id,
                    "exit_code": payload.exit_code,
                },
            )
            return result

    def get_result(self, task_id: int) -> ResultRecord:
        with self._lock:
            try:
                return self._results[task_id]
            except KeyError as exc:
                raise StoreError(f"result not found for task: {task_id}") from exc

    def list_results(self) -> list[ResultRecord]:
        with self._lock:
            return list(self._results.values())

    def _session_id_for_agent(self, agent_id: str) -> str:
        try:
            return self._agent_to_session[agent_id]
        except KeyError as exc:
            raise StoreError(f"agent not found: {agent_id}") from exc

    def _event(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._events.append(
            EventRecord(
                event_id=self._next_event_id,
                event_type=event_type,
                message=message,
                created_at=now_iso(),
                metadata=metadata or {},
            )
        )
        self._next_event_id += 1
