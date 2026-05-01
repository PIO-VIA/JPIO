"""
core/writer.py
--------------
Prend le dict { filepath: java_code } produit par generator.py
et écrit les fichiers sur le disque.

Convention spéciale :
    Les clés préfixées par "__append__:" ne créent pas un nouveau fichier
    mais ajoutent le contenu à la fin d'un fichier existant
    (ex: application.properties).
"""

from pathlib import Path

from jpio.utils.file_helper import write_file, append_to_file
from jpio.utils.console import print_file_created, print_warning

APPEND_PREFIX = "__append__:"


def write_all(
    generated: dict[str, str],
    base_path: Path = Path("."),
) -> int:
    """
    Écrit tous les fichiers générés sur le disque.

    Paramètres :
        generated : dict { chemin_relatif: contenu }
        base_path : racine du projet Spring Boot (par défaut dossier courant)

    Retourne :
        Le nombre de fichiers effectivement écrits.
    """
    written_count = 0

    for rel_path, content in generated.items():

        # ── Mode append (application.properties) ────────────────────────────
        if rel_path.startswith(APPEND_PREFIX):
            actual_path = base_path / rel_path[len(APPEND_PREFIX):]

            if actual_path.exists():
                append_to_file(actual_path, "\n" + content)
                print_file_created(str(actual_path.relative_to(base_path)))
                written_count += 1
            else:
                print_warning(
                    f"Fichier introuvable pour append : {actual_path} — ignoré."
                )
            continue

        # ── Mode création normale ────────────────────────────────────────────
        filepath = base_path / rel_path
        was_written = write_file(filepath, content, overwrite=False)

        if was_written:
            print_file_created(rel_path)
            written_count += 1
        else:
            print_warning(f"Fichier déjà existant — ignoré : {rel_path}")

    return written_count