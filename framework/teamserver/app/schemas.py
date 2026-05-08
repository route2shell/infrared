"""Request and response models for the Infrared V1 teamserver API."""

from typing import Any

from pydantic import BaseModel, Field

from .store import ResultRecord, SessionRecord, TaskRecord


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class CheckinRequest(BaseModel):
    agent_id: str | None = None
    hostname: str | None = None
    username: str | None = None
    platform: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    session_id: str
    agent_id: str
    hostname: str | None = None
    username: str | None = None
    platform: str | None = None
    first_seen: str
    last_seen: str
    checkin_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_record(cls, record: SessionRecord) -> "SessionResponse":
        return cls(
            session_id=record.session_id,
            agent_id=record.agent_id,
            hostname=record.hostname,
            username=record.username,
            platform=record.platform,
            first_seen=record.first_seen,
            last_seen=record.last_seen,
            checkin_count=record.checkin_count,
            metadata=record.metadata,
        )


class CheckinResponse(BaseModel):
    session: SessionResponse


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class TaskCreateRequest(BaseModel):
    session_id: str
    command: str = Field(min_length=1)


class TaskResponse(BaseModel):
    task_id: int
    session_id: str
    command: str
    status: str
    created_at: str
    delivered_at: str | None = None
    completed_at: str | None = None

    @classmethod
    def from_record(cls, record: TaskRecord) -> "TaskResponse":
        return cls(
            task_id=record.task_id,
            session_id=record.session_id,
            command=record.command,
            status=record.status,
            created_at=record.created_at,
            delivered_at=record.delivered_at,
            completed_at=record.completed_at,
        )


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class ResultPostRequest(BaseModel):
    task_id: int
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    status: str = "completed"


class ResultResponse(BaseModel):
    task_id: int
    session_id: str
    stdout: str
    stderr: str
    exit_code: int
    status: str
    created_at: str

    @classmethod
    def from_record(cls, record: ResultRecord) -> "ResultResponse":
        return cls(
            task_id=record.task_id,
            session_id=record.session_id,
            stdout=record.stdout,
            stderr=record.stderr,
            exit_code=record.exit_code,
            status=record.status,
            created_at=record.created_at,
        )


class ResultListResponse(BaseModel):
    results: list[ResultResponse]
