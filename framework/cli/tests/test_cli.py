"""Tests for the Infrared V1 operator CLI."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

import pytest

from infrared_cli.client import ClientError, TeamserverClient
from infrared_cli.main import main


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_bare_cli_prints_banner_and_help(capsys) -> None:
    code = main([])

    output = capsys.readouterr().out
    assert code == 0
    assert "infra + red" in output
    assert "Quick start" in output
    assert "sessions" in output


def test_task_create_requires_command(capsys) -> None:
    code = main(["task", "create", "sess-1"])

    captured = capsys.readouterr()
    assert code == 2
    assert "task command is required" in captured.err


def test_profile_validate_missing_file_returns_error(capsys, tmp_path) -> None:
    missing = tmp_path / "missing.yaml"

    code = main(["profile", "validate", str(missing)])

    captured = capsys.readouterr()
    assert code == 1
    assert "Valid" in captured.out
    assert "no" in captured.out
    assert "profile not found" in captured.err


def test_profile_validate_valid_profile(capsys) -> None:
    code = main(["profile", "validate", "../../profiles/local-http-basic.yaml"])

    captured = capsys.readouterr()
    assert code == 0
    assert "local-http-basic" in captured.out
    assert "127.0.0.1:8080" in captured.out
    assert "127.0.0.1:8000" in captured.out


def test_client_sends_json_payload(monkeypatch) -> None:
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(
            {
                "task_id": 1,
                "session_id": "sess-1",
                "command": "whoami",
                "status": "pending",
                "created_at": "2026-05-08T10:00:00Z",
            }
        )

    monkeypatch.setattr("infrared_cli.client.urlopen", fake_urlopen)
    client = TeamserverClient("http://127.0.0.1:8000")

    response = client.create_task("sess-1", "whoami")

    assert response["task_id"] == 1
    request, timeout = calls[0]
    assert timeout == 10.0
    assert request.full_url == "http://127.0.0.1:8000/api/operator/tasks"
    assert json.loads(request.data.decode("utf-8")) == {
        "session_id": "sess-1",
        "command": "whoami",
    }


def test_client_reports_connection_errors(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise URLError("refused")

    monkeypatch.setattr("infrared_cli.client.urlopen", fake_urlopen)
    client = TeamserverClient("http://127.0.0.1:8000")

    with pytest.raises(ClientError, match="could not reach teamserver"):
        client.health()
