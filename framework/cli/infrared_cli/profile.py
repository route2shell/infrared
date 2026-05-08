"""V1 profile loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in misconfigured envs.
    yaml = None


@dataclass
class ProfileValidationResult:
    path: Path
    valid: bool
    profile: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        value = self.profile.get("name")
        return value if isinstance(value, str) else "-"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "valid": self.valid,
            "name": self.name,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_profile(path: Path) -> ProfileValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if yaml is None:
        return ProfileValidationResult(
            path=path,
            valid=False,
            errors=["PyYAML is required for profile validation"],
        )

    if not path.exists():
        return ProfileValidationResult(
            path=path,
            valid=False,
            errors=[f"profile not found: {path}"],
        )
    if not path.is_file():
        return ProfileValidationResult(
            path=path,
            valid=False,
            errors=[f"profile path is not a file: {path}"],
        )
    if path.suffix.lower() not in {".yaml", ".yml"}:
        warnings.append("profile extension is not .yaml or .yml")

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return ProfileValidationResult(
            path=path,
            valid=False,
            errors=[f"profile YAML is invalid: {exc}"],
            warnings=warnings,
        )

    if not isinstance(loaded, dict):
        return ProfileValidationResult(
            path=path,
            valid=False,
            errors=["profile root must be a mapping"],
            warnings=warnings,
        )

    _validate_string(loaded, "name", errors)
    _validate_string(loaded, "description", errors)
    _validate_mapping(loaded, "operator", errors)
    _validate_mapping(loaded, "transport", errors)
    _validate_mapping(loaded, "redirector", errors)
    _validate_mapping(loaded, "teamserver", errors)
    _validate_mapping(loaded, "telemetry", errors)

    operator = _mapping(loaded, "operator")
    _validate_string(operator, "cli_name", errors, parent="operator")

    transport = _mapping(loaded, "transport")
    _validate_literal(transport, "type", {"http"}, errors, parent="transport")
    _validate_int_range(transport, "beacon_interval_seconds", 1, 86400, errors, parent="transport")
    _validate_int_range(transport, "jitter_percent", 0, 100, errors, parent="transport")

    redirector = _mapping(loaded, "redirector")
    _validate_literal(redirector, "type", {"nginx"}, errors, parent="redirector")
    _validate_string(redirector, "host", errors, parent="redirector")
    _validate_int_range(redirector, "port", 1, 65535, errors, parent="redirector")
    routes = _mapping(redirector, "routes")
    if not routes:
        errors.append("redirector.routes is required")
    else:
        _validate_string(routes, "checkin", errors, parent="redirector.routes")
        _validate_string(routes, "tasks", errors, parent="redirector.routes")
        _validate_string(routes, "results", errors, parent="redirector.routes")
        _validate_v1_routes(routes, warnings)

    teamserver = _mapping(loaded, "teamserver")
    _validate_string(teamserver, "host", errors, parent="teamserver")
    _validate_int_range(teamserver, "port", 1, 65535, errors, parent="teamserver")

    telemetry = _mapping(loaded, "telemetry")
    _validate_bool(telemetry, "sysmon", errors, parent="telemetry")
    _validate_bool(telemetry, "collect_process_creation", errors, parent="telemetry")
    _validate_bool(telemetry, "collect_network_connections", errors, parent="telemetry")
    expected_events = telemetry.get("expected_events")
    if not isinstance(expected_events, list) or not all(isinstance(item, str) for item in expected_events):
        errors.append("telemetry.expected_events must be a list of strings")

    return ProfileValidationResult(
        path=path,
        valid=not errors,
        profile=loaded,
        errors=errors,
        warnings=warnings,
    )


def _mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _field(parent: str | None, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def _validate_mapping(data: dict[str, Any], key: str, errors: list[str]) -> None:
    if key not in data:
        errors.append(f"{key} is required")
    elif not isinstance(data[key], dict):
        errors.append(f"{key} must be a mapping")


def _validate_string(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    parent: str | None = None,
) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{_field(parent, key)} must be a non-empty string")


def _validate_literal(
    data: dict[str, Any],
    key: str,
    allowed: set[str],
    errors: list[str],
    parent: str | None = None,
) -> None:
    value = data.get(key)
    if value not in allowed:
        expected = ", ".join(sorted(allowed))
        errors.append(f"{_field(parent, key)} must be one of: {expected}")


def _validate_int_range(
    data: dict[str, Any],
    key: str,
    minimum: int,
    maximum: int,
    errors: list[str],
    parent: str | None = None,
) -> None:
    value = data.get(key)
    if not isinstance(value, int) or value < minimum or value > maximum:
        errors.append(f"{_field(parent, key)} must be an integer from {minimum} to {maximum}")


def _validate_bool(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    parent: str | None = None,
) -> None:
    if not isinstance(data.get(key), bool):
        errors.append(f"{_field(parent, key)} must be true or false")


def _validate_v1_routes(routes: dict[str, Any], warnings: list[str]) -> None:
    expected = {
        "checkin": "/api/agent/checkin",
        "tasks": "/api/agent/{agent_id}/tasks",
        "results": "/api/agent/{agent_id}/results",
    }
    for key, value in expected.items():
        if routes.get(key) != value:
            warnings.append(f"redirector.routes.{key} does not match current V1 route `{value}`")
