"""
utils/file_helper.py
--------------------
Opérations sur le système de fichiers.
Toute manipulation de chemins et de fichiers passe par ici.
"""

import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Détection du projet Spring Boot
# ---------------------------------------------------------------------------

def is_spring_boot_project(path: Path = Path(".")) -> bool:
    """
    Vérifie que le dossier courant est bien un projet Spring Boot.
    Critères : présence de pom.xml ET de src/main/java/
    """
    return (path / "pom.xml").exists() and (path / "src" / "main" / "java").exists()


def detect_base_package(path: Path = Path(".")) -> str | None:
    """
    Scanne src/main/java/ pour trouver le fichier *Application.java
    et en déduire le package de base automatiquement.

    Retourne le package (ex: "com.pio.ecommerce") ou None si non trouvé.
    """
    java_root = path / "src" / "main" / "java"
    if not java_root.exists():
        return None

    for java_file in java_root.rglob("*Application.java"):
        content = java_file.read_text(encoding="utf-8")
        match = re.search(r"^package\s+([\w.]+);", content, re.MULTILINE)
        if match:
            return match.group(1)

    return None


def detect_project_name(path: Path = Path(".")) -> str:
    """
    Lit le pom.xml pour extraire l'artifactId comme nom du projet.
    Retourne le nom du dossier courant si non trouvé.
    """
    pom = path / "pom.xml"
    if pom.exists():
        content = pom.read_text(encoding="utf-8")
        match = re.search(r"<artifactId>(.*?)</artifactId>", content)
        if match:
            return match.group(1).strip()
    return path.resolve().name


# ---------------------------------------------------------------------------
# Opérations sur les fichiers générés
# ---------------------------------------------------------------------------

def ensure_dir(directory: Path) -> None:
    """Crée un dossier et tous ses parents si nécessaire."""
    directory.mkdir(parents=True, exist_ok=True)


def write_file(filepath: Path, content: str, overwrite: bool = False) -> bool:
    """
    Écrit le contenu dans un fichier.

    - Si le fichier existe et overwrite=False, ne fait rien et retourne False.
    - Crée les dossiers parents si nécessaire.
    - Retourne True si le fichier a été écrit.
    """
    if filepath.exists() and not overwrite:
        return False

    ensure_dir(filepath.parent)
    filepath.write_text(content, encoding="utf-8")
    return True


def append_to_file(filepath: Path, content: str) -> None:
    """
    Ajoute du contenu à la fin d'un fichier existant.
    Utilisé pour application.properties (ajout config Swagger).
    """
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Chemins Java
# ---------------------------------------------------------------------------

def java_source_root(base_path: Path, base_package: str) -> Path:
    """
    Retourne le chemin racine des sources Java pour un package donné.

    ex: base_package = "com.pio.ecommerce"
    →   ./src/main/java/com/pio/ecommerce/
    """
    package_path = base_package.replace(".", os.sep)
    return base_path / "src" / "main" / "java" / package_path


def resources_root(base_path: Path = Path(".")) -> Path:
    """Retourne le chemin du dossier resources."""
    return base_path / "src" / "main" / "resources"