"""Output helpers for the Infrared operator CLI."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from typing import Any

BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        ██╗███╗   ██╗███████╗██████╗  █████╗ ██████╗ ███████╗██████╗          ║
║        ██║████╗  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗         ║
║        ██║██╔██╗ ██║█████╗  ██████╔╝███████║██████╔╝█████╗  ██║  ██║         ║
║        ██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██╔══██╗██╔══╝  ██║  ██║         ║
║        ██║██║ ╚████║██║     ██║  ██║██║  ██║██║  ██║███████╗██████╔╝         ║
║        ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝          ║
║                                                                              ║
║         ┌─────────────── RED TEAM INFRASTRUCTURE LAB ─────────────┐          ║
║         │                                                         │          ║
║         │    operator ──► redirector ──► C2 lab ──► telemetry     │          ║
║         │                                                         │          ║
║         │    [ learn ]--→[ build ]--→[ route ]--→[ observe ]      │          ║
║         │                                                         │          ║
║         └─────────────────────────────────────────────────────────┘          ║
║                                                                              ║
║                                                                  @route2shell║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def print_banner() -> None:
    print(BANNER.strip("\n"))


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def print_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    if not rows:
        print("No records found.")
        return

    terminal_width = shutil.get_terminal_size((100, 24)).columns
    rendered_rows = [
        {key: _shorten(_stringify(row.get(key, "")), terminal_width) for key, _ in columns}
        for row in rows
    ]
    widths = {
        key: max(len(label), *(len(row[key]) for row in rendered_rows))
        for key, label in columns
    }
    header = "  ".join(label.ljust(widths[key]) for key, label in columns)
    divider = "  ".join("-" * widths[key] for key, _ in columns)
    print(header)
    print(divider)
    for row in rendered_rows:
        print("  ".join(row[key].ljust(widths[key]) for key, _ in columns))


def print_key_values(items: Iterable[tuple[str, Any]]) -> None:
    pairs = [(key, _stringify(value)) for key, value in items]
    if not pairs:
        return
    width = max(len(key) for key, _ in pairs)
    for key, value in pairs:
        print(f"{key.ljust(width)}  {value}")


def _stringify(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _shorten(value: str, terminal_width: int) -> str:
    max_cell = max(18, min(48, terminal_width // 3))
    if len(value) <= max_cell:
        return value
    return f"{value[: max_cell - 1]}..."
