"""
commands/add.py
---------------
Commande : jpio add
Ajoute une seule entité à un projet JPIO existant.
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
    Ajoute une nouvelle entité à un projet JPIO existant.
    """
    print_banner()

    base_path = Path(".")

    # ── Vérification projet Spring Boot et JPIO ──────────────────────────────
    if not is_spring_boot_project(base_path):
        print_error("Aucun projet Spring Boot détecté dans ce dossier.")
        raise SystemExit(1)

    jpio_file = base_path / ".jpio.json"
    if not jpio_file.exists():
        print_error(
            "Aucun fichier .jpio.json trouvé.\n"
            "   Lancez d'abord [bold]jpio start[/bold] pour initialiser le projet."
        )
        raise SystemExit(1)

    project_name = detect_project_name(base_path)

    # ── Chargement de la configuration existante ─────────────────────────────
    data = json.loads(jpio_file.read_text(encoding="utf-8"))
    config = ProjectConfig.from_dict(data)

    existing_entity_names = [e.name for e in config.entities]

    # ── Wizard pour la nouvelle entité ───────────────────────────────────────
    new_entity = run_add_wizard(existing_entity_names, config.enums)

    if not new_entity:
        print_info("Ajout annulé. Aucune entité créée.")
        raise SystemExit(0)

    # ── Génération ───────────────────────────────────────────────────────────
    print_info(f"Génération des fichiers pour {new_entity.name} en cours…")
    generated = generate_single_entity(config, new_entity)

    # ── Écriture sur le disque ───────────────────────────────────────────────
    file_count = write_all(generated, base_path)

    # ── Mise à jour de .jpio.json ────────────────────────────────────────────
    config.entities.append(new_entity)
    jpio_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print_success(".jpio.json mis à jour.")

    # ── Résumé final ─────────────────────────────────────────────────────────
    print_summary(
        project_name=project_name,
        entity_count=len(config.entities),
        file_count=file_count,
    )
