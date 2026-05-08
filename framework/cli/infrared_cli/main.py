"""Command implementation for the Infrared V1 operator CLI."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .client import ClientError, TeamserverClient
from .formatting import print_banner, print_json, print_key_values, print_table
from .profile import validate_profile

DEFAULT_SERVER_URL = "http://127.0.0.1:8000"
ENV_SERVER_URL = "INFRARED_TEAMSERVER_URL"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command_group", None):
        print_banner()
        parser.print_help()
        print("\nQuick start:")
        print("  ir server status")
        print("  ir sessions")
        print('  ir task create <session-id> "whoami"')
        return 0

    client = TeamserverClient(args.server_url, timeout=args.timeout)

    try:
        return args.handler(args, client)
    except ClientError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(f"hint: check teamserver status with `ir --server-url {args.server_url} server status`", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ir",
        description="Infrared V1 operator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get(ENV_SERVER_URL, DEFAULT_SERVER_URL),
        help=f"teamserver base URL (default: {DEFAULT_SERVER_URL}; env: {ENV_SERVER_URL})",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="teamserver request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON when supported")
    parser.add_argument("--version", action="version", version=f"ir {__version__}")

    subparsers = parser.add_subparsers(dest="command_group")

    _add_server_commands(subparsers)
    _add_lab_commands(subparsers)
    _add_profile_commands(subparsers)
    _add_session_commands(subparsers)
    _add_task_commands(subparsers)
    _add_results_commands(subparsers)

    return parser


def _add_server_commands(subparsers: argparse._SubParsersAction) -> None:
    server = subparsers.add_parser("server", help="teamserver status helpers")
    server_sub = server.add_subparsers(dest="server_command", required=True)

    status = server_sub.add_parser("status", help="check teamserver health")
    status.set_defaults(handler=handle_server_status)


def _add_lab_commands(subparsers: argparse._SubParsersAction) -> None:
    lab = subparsers.add_parser("lab", help="local lab lifecycle helpers")
    lab_sub = lab.add_subparsers(dest="lab_command", required=True)

    up = lab_sub.add_parser("up", help="start local lab services when Compose exists")
    up.set_defaults(handler=handle_lab_up)

    down = lab_sub.add_parser("down", help="stop local lab services when Compose exists")
    down.set_defaults(handler=handle_lab_down)

    status = lab_sub.add_parser("status", help="show local lab readiness")
    status.set_defaults(handler=handle_lab_status)


def _add_profile_commands(subparsers: argparse._SubParsersAction) -> None:
    profile = subparsers.add_parser("profile", help="profile inspection and validation")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)

    validate = profile_sub.add_parser("validate", help="validate a local profile file")
    validate.add_argument("path", help="profile YAML path")
    validate.set_defaults(handler=handle_profile_validate)


def _add_session_commands(subparsers: argparse._SubParsersAction) -> None:
    sessions = subparsers.add_parser("sessions", help="list and inspect sessions")
    sessions_sub = sessions.add_subparsers(dest="sessions_command")
    sessions.set_defaults(handler=handle_sessions_list)

    show = sessions_sub.add_parser("show", help="show one session")
    show.add_argument("session_id")
    show.set_defaults(handler=handle_sessions_show)


def _add_task_commands(subparsers: argparse._SubParsersAction) -> None:
    task = subparsers.add_parser("task", help="create and list tasks")
    task_sub = task.add_subparsers(dest="task_command", required=True)

    create = task_sub.add_parser("create", help="create a task for a session")
    create.add_argument("session_id")
    create.add_argument("command", nargs=argparse.REMAINDER, help="command to run, for example: whoami")
    create.set_defaults(handler=handle_task_create)

    list_cmd = task_sub.add_parser("list", help="list tasks")
    list_cmd.set_defaults(handler=handle_task_list)


def _add_results_commands(subparsers: argparse._SubParsersAction) -> None:
    results = subparsers.add_parser("results", help="show task results")
    results.add_argument("task_id", nargs="?", type=int, help="task ID to show")
    results.set_defaults(handler=handle_results)


def handle_server_status(args: argparse.Namespace, client: TeamserverClient) -> int:
    data = client.health()
    if args.json:
        print_json(data)
    else:
        print_key_values(
            [
                ("Status", data.get("status")),
                ("Service", data.get("service")),
                ("Version", data.get("version")),
                ("URL", args.server_url),
            ]
        )
    return 0


def handle_sessions_list(args: argparse.Namespace, client: TeamserverClient) -> int:
    data = client.list_sessions()
    sessions = data.get("sessions", [])
    if args.json:
        print_json(data)
    else:
        print_table(
            sessions,
            [
                ("session_id", "Session ID"),
                ("agent_id", "Agent ID"),
                ("hostname", "Host"),
                ("username", "User"),
                ("platform", "Platform"),
                ("last_seen", "Last Seen"),
            ],
        )
    return 0


def handle_sessions_show(args: argparse.Namespace, client: TeamserverClient) -> int:
    session = client.get_session(args.session_id)
    if args.json:
        print_json(session)
    else:
        print_key_values(
            [
                ("Session ID", session.get("session_id")),
                ("Agent ID", session.get("agent_id")),
                ("Host", session.get("hostname")),
                ("User", session.get("username")),
                ("Platform", session.get("platform")),
                ("First Seen", session.get("first_seen")),
                ("Last Seen", session.get("last_seen")),
                ("Check-ins", session.get("checkin_count")),
            ]
        )
    return 0


def handle_task_create(args: argparse.Namespace, client: TeamserverClient) -> int:
    command = " ".join(args.command).strip()
    if not command:
        print("error: task command is required", file=sys.stderr)
        print('hint: ir task create <session-id> "whoami"', file=sys.stderr)
        return 2

    task = client.create_task(args.session_id, command)
    if args.json:
        print_json(task)
    else:
        print("Task created.")
        print_key_values(
            [
                ("Task ID", task.get("task_id")),
                ("Session ID", task.get("session_id")),
                ("Command", task.get("command")),
                ("Status", task.get("status")),
            ]
        )
    return 0


def handle_task_list(args: argparse.Namespace, client: TeamserverClient) -> int:
    data = client.list_tasks()
    tasks = data.get("tasks", [])
    if args.json:
        print_json(data)
    else:
        print_table(
            tasks,
            [
                ("task_id", "Task ID"),
                ("session_id", "Session ID"),
                ("command", "Command"),
                ("status", "Status"),
                ("created_at", "Created"),
            ],
        )
    return 0


def handle_results(args: argparse.Namespace, client: TeamserverClient) -> int:
    if args.task_id is None:
        data = client.list_results()
        if args.json:
            print_json(data)
        else:
            print_table(
                data.get("results", []),
                [
                    ("task_id", "Task ID"),
                    ("session_id", "Session ID"),
                    ("status", "Status"),
                    ("exit_code", "Exit"),
                    ("created_at", "Created"),
                ],
            )
        return 0

    result = client.get_result(args.task_id)
    if args.json:
        print_json(result)
    else:
        print_key_values(
            [
                ("Task ID", result.get("task_id")),
                ("Session ID", result.get("session_id")),
                ("Status", result.get("status")),
                ("Exit Code", result.get("exit_code")),
                ("Created", result.get("created_at")),
            ]
        )
        print("\nSTDOUT:")
        print(result.get("stdout") or "")
        if result.get("stderr"):
            print("\nSTDERR:")
            print(result.get("stderr"))
    return 0


def handle_profile_validate(args: argparse.Namespace, client: TeamserverClient) -> int:
    path = Path(args.path)
    result = validate_profile(path)

    if args.json:
        print_json(result.to_dict())
    else:
        profile = result.profile
        redirector = profile.get("redirector", {}) if isinstance(profile.get("redirector"), dict) else {}
        teamserver = profile.get("teamserver", {}) if isinstance(profile.get("teamserver"), dict) else {}
        transport = profile.get("transport", {}) if isinstance(profile.get("transport"), dict) else {}
        print_key_values(
            [
                ("Profile", path),
                ("Name", result.name),
                ("Valid", "yes" if result.valid else "no"),
                ("Transport", transport.get("type", "-")),
                ("Redirector", _host_port(redirector)),
                ("Teamserver", _host_port(teamserver)),
            ]
        )
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)

    return 0 if result.valid else 1


def handle_lab_status(args: argparse.Namespace, client: TeamserverClient) -> int:
    compose = _compose_file()
    print_key_values(
        [
            ("Compose file", compose),
            ("Compose ready", "yes" if compose.exists() else "no"),
            ("Teamserver URL", args.server_url),
        ]
    )
    if not compose.exists():
        print("note: Docker Compose local lab arrives in Phase 7.")
        return 0

    result = subprocess.run(
        ["docker", "compose", "-f", str(compose), "ps"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print("\nServices:")
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    return 0


def handle_lab_up(args: argparse.Namespace, client: TeamserverClient) -> int:
    return _run_compose(["up", "-d"])


def handle_lab_down(args: argparse.Namespace, client: TeamserverClient) -> int:
    return _run_compose(["down"])


def _compose_file() -> Path:
    return Path(__file__).resolve().parents[3] / "infrastructure" / "local" / "docker-compose.yml"


def _host_port(value: dict[str, Any]) -> str:
    host = value.get("host")
    port = value.get("port")
    if host is None or port is None:
        return "-"
    return f"{host}:{port}"


def _run_compose(action: list[str]) -> int:
    compose = _compose_file()
    if not compose.exists():
        print(f"error: Docker Compose file not found: {compose}", file=sys.stderr)
        print("hint: local lab orchestration is scheduled for Phase 7.", file=sys.stderr)
        return 2
    command = ["docker", "compose", "-f", str(compose), *action]
    return subprocess.run(command, check=False).returncode
