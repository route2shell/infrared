"""FastAPI application for the Infrared V1 teamserver."""

import os
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException, Request

from .db import SQLiteStore
from .schemas import (
    CheckinRequest,
    CheckinResponse,
    HealthResponse,
    ResultListResponse,
    ResultPostRequest,
    ResultResponse,
    SessionListResponse,
    SessionResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
)
from .store import ResultRecord, SessionRecord, StoreError, TaskRecord

SERVICE_NAME = "infrared-teamserver"
SERVICE_VERSION = "0.1.0-v1"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "teamserver.sqlite3"


class TeamserverStore(Protocol):
    def check_in(self, payload: object) -> SessionRecord: ...
    def deliver_pending_tasks(self, agent_id: str) -> list[TaskRecord]: ...
    def record_result(self, agent_id: str, payload: object) -> ResultRecord: ...
    def list_sessions(self) -> list[SessionRecord]: ...
    def get_session(self, session_id: str) -> SessionRecord: ...
    def create_task(self, payload: object) -> TaskRecord: ...
    def list_tasks(self) -> list[TaskRecord]: ...
    def get_result(self, task_id: int) -> ResultRecord: ...
    def list_results(self) -> list[ResultRecord]: ...


def default_store() -> SQLiteStore:
    db_path = os.environ.get("INFRARED_TEAMSERVER_DB", str(DEFAULT_DB_PATH))
    return SQLiteStore(db_path)


def _store(request: Request) -> TeamserverStore:
    return request.app.state.store


def create_app(store: TeamserverStore | None = None) -> FastAPI:
    """Create a configured FastAPI app.

    Phase 3 uses SQLite by default while preserving the Phase 2 API contract.
    Tests can inject any store that implements the same small method surface.
    """

    app = FastAPI(
        title="Infrared Teamserver",
        description="V1 local-first control plane for sessions, tasks, and results.",
        version=SERVICE_VERSION,
    )
    app.state.store = store or default_store()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=SERVICE_NAME,
            version=SERVICE_VERSION,
        )

    @app.post("/api/agent/checkin", response_model=CheckinResponse)
    def agent_checkin(payload: CheckinRequest, request: Request) -> CheckinResponse:
        session = _store(request).check_in(payload)
        return CheckinResponse(session=SessionResponse.from_record(session))

    @app.get("/api/agent/{agent_id}/tasks", response_model=TaskListResponse)
    def agent_tasks(agent_id: str, request: Request) -> TaskListResponse:
        try:
            tasks = _store(request).deliver_pending_tasks(agent_id)
        except StoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return TaskListResponse(tasks=[TaskResponse.from_record(task) for task in tasks])

    @app.post("/api/agent/{agent_id}/results", response_model=ResultResponse)
    def agent_results(
        agent_id: str,
        payload: ResultPostRequest,
        request: Request,
    ) -> ResultResponse:
        try:
            result = _store(request).record_result(agent_id, payload)
        except StoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ResultResponse.from_record(result)

    @app.get("/api/operator/sessions", response_model=SessionListResponse)
    def operator_sessions(request: Request) -> SessionListResponse:
        sessions = _store(request).list_sessions()
        return SessionListResponse(
            sessions=[SessionResponse.from_record(session) for session in sessions]
        )

    @app.get("/api/operator/sessions/{session_id}", response_model=SessionResponse)
    def operator_session(session_id: str, request: Request) -> SessionResponse:
        try:
            session = _store(request).get_session(session_id)
        except StoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return SessionResponse.from_record(session)

    @app.post("/api/operator/tasks", response_model=TaskResponse, status_code=201)
    def operator_create_task(
        payload: TaskCreateRequest,
        request: Request,
    ) -> TaskResponse:
        try:
            task = _store(request).create_task(payload)
        except StoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return TaskResponse.from_record(task)

    @app.get("/api/operator/tasks", response_model=TaskListResponse)
    def operator_tasks(request: Request) -> TaskListResponse:
        tasks = _store(request).list_tasks()
        return TaskListResponse(tasks=[TaskResponse.from_record(task) for task in tasks])

    @app.get("/api/operator/results/{task_id}", response_model=ResultResponse)
    def operator_result(task_id: int, request: Request) -> ResultResponse:
        try:
            result = _store(request).get_result(task_id)
        except StoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ResultResponse.from_record(result)

    @app.get("/api/operator/results", response_model=ResultListResponse)
    def operator_results(request: Request) -> ResultListResponse:
        results = _store(request).list_results()
        return ResultListResponse(
            results=[ResultResponse.from_record(result) for result in results]
        )

    return app


app = create_app()
