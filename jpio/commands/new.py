"""
commands/new.py
---------------
Commande : jpio start
Orchestre le flow complet :
    détection projet → wizard → génération → écriture → rapport final
"""

import json
from pathlib import Path

import click

from jpio.core.analyzer import run_wizard
from jpio.core.generator import generate_all
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


@click.command("start")
def start_command():
    """
    Lance le wizard JPIO pour scaffolder les couches métier
    d'un projet Spring Boot existant.
    """
    print_banner()

    base_path = Path(".")

    # ── Vérification projet Spring Boot ─────────────────────────────────────
    if not is_spring_boot_project(base_path):
        print_error(
            "Aucun projet Spring Boot détecté dans ce dossier.\n"
            "   Initialisez d'abord votre projet sur [link]https://start.spring.io[/link]\n"
            "   puis relancez [bold]jpio start[/bold] depuis la racine du projet."
        )
        raise SystemExit(1)

    project_name = detect_project_name(base_path)
    print_success(f"Projet Spring Boot détecté : [bold cyan]{project_name}[/bold cyan]")

    # ── Wizard interactif ────────────────────────────────────────────────────
    config = run_wizard()

    if not config.entities:
        print_error("Aucune entité définie. Abandon.")
        raise SystemExit(1)

    # ── Génération ───────────────────────────────────────────────────────────
    print_info("Génération des fichiers en cours…")
    generated = generate_all(config)

    # ── Écriture sur le disque ───────────────────────────────────────────────
    file_count = write_all(generated, base_path)

    # ── Sauvegarde .jpio.json ────────────────────────────────────────────────
    _save_jpio_json(config, base_path)

    # ── Résumé final ─────────────────────────────────────────────────────────
    print_summary(
        project_name=project_name,
        entity_count=len(config.entities),
        file_count=file_count,
    )


def _save_jpio_json(config, base_path: Path) -> None:
    """Sauvegarde le snapshot du projet dans .jpio.json."""
    jpio_file = base_path / ".jpio.json"
    jpio_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print_success(".jpio.json sauvegardé.")