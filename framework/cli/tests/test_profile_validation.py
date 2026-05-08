"""Tests for V1 profile validation."""

from pathlib import Path

from infrared_cli.profile import validate_profile


ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "profiles" / "local-http-basic.yaml"


def test_local_http_basic_profile_is_valid() -> None:
    result = validate_profile(PROFILE)

    assert result.valid
    assert result.errors == []
    assert result.name == "local-http-basic"
    assert result.profile["redirector"]["host"] == "127.0.0.1"
    assert result.profile["redirector"]["port"] == 8080
    assert result.profile["teamserver"]["port"] == 8000


def test_profile_requires_core_sections(tmp_path) -> None:
    profile = tmp_path / "bad.yaml"
    profile.write_text("name: bad\n", encoding="utf-8")

    result = validate_profile(profile)

    assert not result.valid
    assert "operator is required" in result.errors
    assert "transport is required" in result.errors
    assert "redirector is required" in result.errors
    assert "teamserver is required" in result.errors
    assert "telemetry is required" in result.errors


def test_profile_warns_when_routes_drift_from_v1(tmp_path) -> None:
    profile = tmp_path / "drift.yaml"
    profile.write_text(
        """
name: drift
description: Drift test profile.
operator:
  cli_name: ir
transport:
  type: http
  beacon_interval_seconds: 5
  jitter_percent: 0
redirector:
  type: nginx
  host: 127.0.0.1
  port: 8080
  routes:
    checkin: /submit
    tasks: /tasks
    results: /results
teamserver:
  host: 127.0.0.1
  port: 8000
telemetry:
  sysmon: true
  collect_process_creation: true
  collect_network_connections: true
  expected_events:
    - redirector_access
""".strip(),
        encoding="utf-8",
    )

    result = validate_profile(profile)

    assert result.valid
    assert len(result.warnings) == 3
