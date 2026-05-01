"""
utils/file_helper.py
--------------------
Opérations sur le système de fichiers.
Toute manipulation de chemins et de fichiers passe par ici.
"""

import os
import re
from pathlib import Path
import logging

from jpio.core.models import PomFeatures

logger = logging.getLogger(__name__)


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


def detect_config_format(path: Path = Path(".")) -> tuple[str, Path]:
    """
    Détecte le format de configuration Spring Boot utilisé dans le projet.

    Règles de priorité :
    1. Si application.properties existe → retourne ("properties", chemin)
    2. Si application.yaml existe       → retourne ("yaml", chemin)
    3. Si application.yml existe        → retourne ("yaml", chemin)
    4. Si plusieurs existent            → prend properties en priorité, log un warning
    5. Si aucun n'existe                → retourne ("properties", chemin) par défaut
                                          et log un warning

    Retourne un tuple (format: str, filepath: Path)
    """
    res_dir = resources_root(path)
    prop_path = res_dir / "application.properties"
    yaml_path = res_dir / "application.yaml"
    yml_path  = res_dir / "application.yml"

    found = []
    if prop_path.exists(): found.append(("properties", prop_path))
    if yaml_path.exists(): found.append(("yaml", yaml_path))
    if yml_path.exists():  found.append(("yaml", yml_path))

    if len(found) > 1:
        logger.warning("Plusieurs fichiers de configuration détectés. 'application.properties' sera utilisé par défaut.")
        # On cherche spécifiquement properties dans la liste
        for fmt, p in found:
            if fmt == "properties":
                return fmt, p
        return found[0]

    if not found:
        logger.warning("Aucun fichier de configuration détecté. Utilisation de 'application.properties' par défaut.")
        return "properties", prop_path

    return found[0]


def analyze_pom(path: Path = Path(".")) -> PomFeatures:
    """
    Lit le pom.xml et détecte les dépendances présentes.

    Dépendances à détecter (chercher les artifactId dans le contenu XML) :
    - has_jpa        : "spring-boot-starter-data-jpa"
    - has_lombok     : "lombok"
    - has_swagger    : "springdoc-openapi-starter-webmvc-ui" OU "springdoc-openapi-ui"
    - has_validation : "spring-boot-starter-validation"

    Si pom.xml est absent ou illisible, retourne PomFeatures() avec les valeurs par défaut.
    """
    pom_path = path / "pom.xml"
    if not pom_path.exists():
        return PomFeatures()

    try:
        content = pom_path.read_text(encoding="utf-8")
        return PomFeatures(
            has_jpa="spring-boot-starter-data-jpa" in content,
            has_lombok="lombok" in content,
            has_swagger="springdoc-openapi-starter-webmvc-ui" in content or "springdoc-openapi-ui" in content,
            has_validation="spring-boot-starter-validation" in content
        )
    except Exception as e:
        logger.warning(f"Erreur lors de la lecture du pom.xml : {e}. Utilisation des valeurs par défaut.")
        return PomFeatures()


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