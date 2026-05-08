"""Static checks for the Infrared V1 Nginx redirector config."""

from pathlib import Path


CONFIG = Path(__file__).resolve().parents[1] / "nginx.conf"


def test_nginx_config_exists() -> None:
    assert CONFIG.exists()


def test_redirector_listens_on_local_v1_port() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "listen 8080;" in text
    assert "server 127.0.0.1:8000;" in text


def test_agent_routes_are_forwarded() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "location = /api/agent/checkin" in text
    assert r"^/api/agent/[^/]+/(tasks|results)$" in text
    assert text.count("proxy_pass http://infrared_teamserver;") == 2


def test_operator_routes_are_not_forwarded_by_default() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "/api/operator" not in text
    assert "return 404;" in text


def test_redirector_access_log_is_configured() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "log_format infrared_agent" in text
    assert "access_log logs/access.log infrared_agent;" in text
    assert "X-Infrared-Redirector local-nginx-v1" in text
