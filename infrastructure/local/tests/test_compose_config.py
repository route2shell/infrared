"""Static checks for the Infrared V1 Docker Compose local lab."""

from pathlib import Path


COMPOSE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


def test_compose_file_exists() -> None:
    assert COMPOSE.exists()


def test_compose_defines_required_services() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    assert "teamserver:" in text
    assert "redirector:" in text
    assert "infrared-teamserver:v1" in text
    assert "nginx:1.24" in text


def test_compose_exposes_v1_ports() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    assert '"8000:8000"' in text
    assert '"8080:8080"' in text


def test_compose_persists_teamserver_state() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    assert "teamserver-data:/data" in text
    assert "INFRARED_TEAMSERVER_DB: /data/teamserver.sqlite3" in text
    assert "teamserver-data:" in text


def test_redirector_uses_compose_nginx_config() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    assert "../nginx/nginx.compose.conf:/etc/nginx/nginx.conf:ro" in text
    assert "../nginx/logs:/var/log/nginx/infrared" in text
