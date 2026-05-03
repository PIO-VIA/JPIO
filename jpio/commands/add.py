"""
Command: jpio add
Adds a single entity to an existing JPIO project.
"""

import json
from pathlib import Path

import click

from jpio.core.models import ProjectConfig
from jpio.core.analyzer import run_add_wizard
from jpio.core.generator import generate_single_entity
from jpio.core.writer import write_all
from jpio.utils.console import (
    print_banner,
    print_success,
    print_error,
    print_info,
    print_summary,
)
from jpio.utils.file_helper import (
    is_spring_boot_project,
    detect_project_name,
)


@click.command("add")
def add_command():
    """
    Add a new entity to an existing JPIO project.
    """
    print_banner()

    base_path = Path(".")

    # ── Spring Boot and JPIO Project Verification ──────────────────────────────
    if not is_spring_boot_project(base_path):
        print_error("No Spring Boot project detected in this folder.")
        raise SystemExit(1)

    jpio_file = base_path / ".jpio.json"
    if not jpio_file.exists():
        print_error(
            "No .jpio.json file found.\n"
            "   Run [bold]jpio start[/bold] first to initialize the project."
        )
        raise SystemExit(1)

    project_name = detect_project_name(base_path)

    # ── Load existing configuration ─────────────────────────────
    data = json.loads(jpio_file.read_text(encoding="utf-8"))
    config = ProjectConfig.from_dict(data)

    existing_entity_names = [e.name for e in config.entities]

    # ── Wizard for the new entities ───────────────────────────────────────
    new_entities = run_add_wizard(existing_entity_names, config.enums)

    if not new_entities:
        print_info("Addition cancelled. No entities created.")
        raise SystemExit(0)

    # ── Generation and Writing ────────────────────────────────────────────────
    file_count = 0
    for entity in new_entities:
        print_info(f"Generating files for {entity.name}...")
        generated = generate_single_entity(config, entity)
        file_count += write_all(generated, base_path)
        config.entities.append(entity)

    # ── Update .jpio.json ────────────────────────────────────────────
    jpio_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print_success(".jpio.json updated.")

    # ── Final Summary ─────────────────────────────────────────────────────────
    print_summary(
        project_name=project_name,
        entity_count=len(config.entities),
        file_count=file_count,
    )
