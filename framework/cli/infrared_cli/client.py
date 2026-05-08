"""HTTP client for the Infrared teamserver API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ClientError(Exception):
    """Raised when a teamserver request fails."""


@dataclass(frozen=True)
class TeamserverClient:
    base_url: str
    timeout: float = 10.0

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def list_sessions(self) -> dict[str, Any]:
        return self._request("GET", "/api/operator/sessions")

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/operator/sessions/{session_id}")

    def create_task(self, session_id: str, command: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/operator/tasks",
            {"session_id": session_id, "command": command},
        )

    def list_tasks(self) -> dict[str, Any]:
        return self._request("GET", "/api/operator/tasks")

    def get_result(self, task_id: int) -> dict[str, Any]:
        return self._request("GET", f"/api/operator/results/{task_id}")

    def list_results(self) -> dict[str, Any]:
        return self._request("GET", "/api/operator/results")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = self._url(path, query)
        body = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = _read_error_detail(exc)
            raise ClientError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ClientError(f"could not reach teamserver at {self.base_url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ClientError(f"request timed out reaching teamserver at {self.base_url}") from exc

        if not raw:
            return {}

        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ClientError(f"teamserver returned non-JSON response from {path}") from exc

        if isinstance(loaded, dict):
            return loaded
        raise ClientError(f"teamserver returned unexpected response shape from {path}")

    def _url(self, path: str, query: dict[str, str] | None = None) -> str:
        base = self.base_url.rstrip("/")
        url = f"{base}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        return url


def _read_error_detail(exc: HTTPError) -> str:
    raw = exc.read().decode("utf-8", errors="replace")
    if not raw:
        return exc.reason
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(loaded, dict) and "detail" in loaded:
        return str(loaded["detail"])
    return raw
