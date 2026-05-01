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
from jpio.core.models import FolderMapping
from jpio.core.generator import generate_all
from jpio.core.writer import write_all
from jpio.utils.console import (
    print_banner,
    print_success,
    print_error,
    print_info,
    print_summary,
    print_folder_mapping_report,
)
from jpio.utils.file_helper import (
    is_spring_boot_project,
    detect_project_name,
    analyze_pom,
    detect_existing_folders,
    detect_base_package,
    java_source_root,
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

    # ── Analyse du pom.xml ───────────────────────────────────────────────────
    pom_features = analyze_pom(base_path)
    
    if pom_features.has_jpa:
        print_info("JPA détecté ✔")
    else:
        print_info("JPA non détecté — repository généré sans JpaRepository")
        
    if pom_features.has_lombok:
        print_info("Lombok détecté ✔")
    else:
        print_info("Lombok non détecté — getters/setters générés manuellement")
        
    if pom_features.has_swagger:
        print_info("Swagger détecté ✔")
    else:
        print_info("Swagger non détecté — SwaggerConfig ignoré")
        
    if pom_features.has_validation:
        print_info("Validation détectée ✔")
    else:
        print_info("Validation non détectée — annotations @Valid ignorées")

    # ── Détection des dossiers ───────────────────────────────────────────────
    base_package = detect_base_package(base_path)
    if base_package:
        package_dir = java_source_root(base_path, base_package)
        folder_mapping = detect_existing_folders(package_dir)
    else:
        folder_mapping = FolderMapping()
        
    print_folder_mapping_report(folder_mapping)

    # ── Wizard interactif ────────────────────────────────────────────────────
    config = run_wizard(pom_features, folder_mapping)

    if not config.entities:
        print_error("Aucune entité définie. Abandon.")
        raise SystemExit(1)

    # ── Génération ───────────────────────────────────────────────────────────
    print_info("Génération des fichiers en cours…")
    generated = generate_all(config, base_path)

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