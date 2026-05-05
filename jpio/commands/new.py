import json
import questionary
from pathlib import Path

import click

from jpio.core.analyzer import run_wizard, QSTYLE, _ask
from jpio.core.models import FolderMapping
from jpio.core.generator import generate_all
from jpio.core.writer import write_all
from jpio.utils.console import (
    print_banner,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_summary,
    print_folder_mapping_report,
    console,
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
    Launch the JPIO wizard to scaffold business layers
    for an existing Spring Boot project.
    """
    try:
        _run_start()
    except (KeyboardInterrupt, EOFError):
        console.print(
            "\n\n  [bold yellow]⚠[/bold yellow]  "
            "Opération annulée par l'utilisateur.\n"
        )
        raise SystemExit(0)
    except click.exceptions.Abort:
        console.print(
            "\n\n  [bold yellow]⚠[/bold yellow]  "
            "Opération annulée.\n"
        )
        raise SystemExit(0)

def _run_start():
    print_banner()

    base_path = Path(".")

    # ── Spring Boot Project Verification ─────────────────────────────────────
    if not is_spring_boot_project(base_path):
        print_error(
            "No Spring Boot project detected in this folder.\n"
            "   Initialize your project first at [link]https://start.spring.io[/link]\n"
            "   then run [bold]jpio start[/bold] from the project root."
        )
        raise SystemExit(1)

    project_name = detect_project_name(base_path)
    print_success(f"Spring Boot project detected: [bold cyan]{project_name}[/bold cyan]")

    # ── Vérification projet déjà initialisé ─────────────────────────
    jpio_file = base_path / ".jpio.json"

    if jpio_file.exists():
        # Lire la version et les entités existantes
        try:
            existing_data = json.loads(jpio_file.read_text(encoding="utf-8"))
            existing_entities = existing_data.get("entities", [])
            entity_names = [e["name"] for e in existing_entities]
        except Exception:
            existing_entities = []
            entity_names = []

        print_warning(
            f"Ce projet a déjà été initialisé avec JPIO.\n"
            f"   Entités existantes : "
            f"{', '.join(entity_names) if entity_names else 'aucune'}"
        )

        action = _ask(questionary.select(
            "Que voulez-vous faire ?",
            choices=[
                "Ajouter de nouvelles entités  (recommandé → jpio add)",
                "Régénérer le projet            (écrase les fichiers existants)",
                "Annuler",
            ],
            style=QSTYLE,
        ))

        if "Annuler" in action:
            print_info("Opération annulée.")
            raise SystemExit(0)

        if "Ajouter" in action:
            print_info(
                "Utilisez la commande [bold]jpio add[/bold] "
                "pour ajouter une entité à ce projet."
            )
            raise SystemExit(0)

        # Si "Régénérer" → continuer normalement avec le wizard
        print_warning("Régénération en cours — les fichiers existants seront ignorés.")

    # ── pom.xml Analysis ───────────────────────────────────────────────────
    pom_features = analyze_pom(base_path)
    
    if pom_features.has_jpa:
        print_info("JPA detected ✔")
    else:
        from jpio.utils.file_helper import inject_jpa_dependency

        print_info("JPA not detected.")
        add_jpa = _ask(questionary.confirm(
            "Would you like to add JPA dependency to optimize repository writing?",
            default=True,
            style=QSTYLE,
        ))

        if add_jpa:
            if inject_jpa_dependency(base_path):
                print_success("JPA dependency injected into pom.xml ✔")
                pom_features.has_jpa = True
            else:
                print_error("Failed to inject JPA dependency. Using CrudRepository.")
        else:
            print_info("Proceeding without JPA — repositories will use CrudRepository.")
        
    if pom_features.has_lombok:
        print_info("Lombok detected ✔")
    else:
        print_info("Lombok not detected — getters/setters generated manually")
        
    if pom_features.has_swagger:
        print_info("Swagger detected ✔")
    else:
        print_info("Swagger not detected — SwaggerConfig ignored")
        
    if pom_features.has_validation:
        print_info("Validation detected ✔")
    else:
        print_info("Validation not detected — @Valid annotations ignored")

    # ── Folder Detection ───────────────────────────────────────────────
    base_package = detect_base_package(base_path)
    if base_package:
        package_dir = java_source_root(base_path, base_package)
        folder_mapping = detect_existing_folders(package_dir)
    else:
        folder_mapping = FolderMapping()
        
    print_folder_mapping_report(folder_mapping)

    # ── Interactive Wizard ────────────────────────────────────────────────────
    config = run_wizard(pom_features, folder_mapping)

    if not config.entities:
        print_warning("No entities defined. Only global configurations will be generated.")

    # ── Generation ───────────────────────────────────────────────────────────
    print_info("Generating files...")
    generated = generate_all(config, base_path)

    # ── Disk Writing ───────────────────────────────────────────────
    file_count = write_all(generated, base_path)

    # ── Save .jpio.json ────────────────────────────────────────────────
    _save_jpio_json(config, base_path)

    # ── Final Summary ─────────────────────────────────────────────────────────
    print_summary(
        project_name=project_name,
        entity_count=len(config.entities),
        file_count=file_count,
    )


def _save_jpio_json(config, base_path: Path) -> None:
    """Saves a snapshot of the project in .jpio.json."""
    jpio_file = base_path / ".jpio.json"
    jpio_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print_success(".jpio.json saved.")