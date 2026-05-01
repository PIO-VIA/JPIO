"""
Command: jpio scan
Reads .jpio.json and displays a project summary table.
"""

import json
from pathlib import Path

import click

from jpio.utils.console import (
    print_banner,
    print_error,
    print_info,
    print_scan_table,
)


@click.command("scan")
def scan_command():
    """Display the current JPIO project state (entities, fields, relations)."""
    print_banner()

    jpio_file = Path(".jpio.json")

    if not jpio_file.exists():
        print_error(
            "No .jpio.json file found.\n"
            "   Run [bold]jpio start[/bold] first to initialize the project."
        )
        raise SystemExit(1)

    data = json.loads(jpio_file.read_text(encoding="utf-8"))

    print_info(f"Package: [bold cyan]{data.get('base_package', '—')}[/bold cyan]")
    print_info(f"API Prefix: [bold cyan]{data.get('api_prefix', '—')}[/bold cyan]")

    entities = data.get("entities", [])

    if not entities:
        print_error("No entities registered in this project.")
        raise SystemExit(0)

    print_scan_table(entities)