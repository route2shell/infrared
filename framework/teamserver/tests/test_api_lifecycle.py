"""API lifecycle tests for the Infrared V1 teamserver."""

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import create_app
from app.db import SQLiteStore


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "teamserver-test.sqlite3"
    return TestClient(create_app(store=SQLiteStore(db_path)))


def test_health_route_reports_service_status(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "infrared-teamserver"


def test_checkin_task_delivery_and_result_lifecycle(client) -> None:
    checkin = client.post(
        "/api/agent/checkin",
        json={
            "agent_id": "agent-local-1",
            "hostname": "win-lab-01",
            "username": "lab-user",
            "platform": "windows",
        },
    )
    assert checkin.status_code == 200
    session = checkin.json()["session"]
    session_id = session["session_id"]

    sessions = client.get("/api/operator/sessions")
    assert sessions.status_code == 200
    assert sessions.json()["sessions"][0]["agent_id"] == "agent-local-1"

    task = client.post(
        "/api/operator/tasks",
        json={"session_id": session_id, "command": "whoami"},
    )
    assert task.status_code == 201
    task_id = task.json()["task_id"]
    assert task.json()["status"] == "pending"

    delivered = client.get("/api/agent/agent-local-1/tasks")
    assert delivered.status_code == 200
    delivered_tasks = delivered.json()["tasks"]
    assert len(delivered_tasks) == 1
    assert delivered_tasks[0]["task_id"] == task_id
    assert delivered_tasks[0]["status"] == "delivered"

    result = client.post(
        "/api/agent/agent-local-1/results",
        json={
            "task_id": task_id,
            "stdout": "LAB\\\\lab-user",
            "stderr": "",
            "exit_code": 0,
            "status": "completed",
        },
    )
    assert result.status_code == 200
    assert result.json()["stdout"] == "LAB\\\\lab-user"

    fetched = client.get(f"/api/operator/results/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["task_id"] == task_id
    assert fetched.json()["status"] == "completed"


def test_unknown_agent_task_poll_returns_404(client) -> None:
    response = client.get("/api/agent/missing-agent/tasks")

    assert response.status_code == 404


def test_sqlite_state_persists_across_app_instances(tmp_path) -> None:
    db_path = tmp_path / "persistent-teamserver.sqlite3"
    first_client = TestClient(create_app(store=SQLiteStore(db_path)))

    checkin = first_client.post(
        "/api/agent/checkin",
        json={"agent_id": "agent-persistent-1", "hostname": "win-lab-02"},
    )
    assert checkin.status_code == 200
    session_id = checkin.json()["session"]["session_id"]

    task = first_client.post(
        "/api/operator/tasks",
        json={"session_id": session_id, "command": "whoami"},
    )
    assert task.status_code == 201
    task_id = task.json()["task_id"]

    second_client = TestClient(create_app(store=SQLiteStore(db_path)))

    sessions = second_client.get("/api/operator/sessions")
    assert sessions.status_code == 200
    assert sessions.json()["sessions"][0]["session_id"] == session_id

    tasks = second_client.get("/api/operator/tasks")
    assert tasks.status_code == 200
    assert tasks.json()["tasks"][0]["task_id"] == task_id
