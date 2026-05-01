"""
commands/scan.py
----------------
Commande : jpio scan
Lit .jpio.json et affiche un tableau récapitulatif du projet.
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
    """Affiche l'état actuel du projet JPIO (entités, champs, relations)."""
    print_banner()

    jpio_file = Path(".jpio.json")

    if not jpio_file.exists():
        print_error(
            "Aucun fichier .jpio.json trouvé.\n"
            "   Lancez d'abord [bold]jpio start[/bold] pour initialiser le projet."
        )
        raise SystemExit(1)

    data = json.loads(jpio_file.read_text(encoding="utf-8"))

    print_info(f"Package : [bold cyan]{data.get('base_package', '—')}[/bold cyan]")
    print_info(f"Préfixe API : [bold cyan]{data.get('api_prefix', '—')}[/bold cyan]")

    entities = data.get("entities", [])

    if not entities:
        print_error("Aucune entité enregistrée dans ce projet.")
        raise SystemExit(0)

    print_scan_table(entities)