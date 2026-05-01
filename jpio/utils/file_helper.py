"""

File system operations.
All path and file manipulations go through here.
"""

import os
import re
from pathlib import Path
import logging

from jpio.core.models import PomFeatures, FolderMapping

logger = logging.getLogger(__name__)


EXPECTED_FOLDERS = {
    "controller": ["controller", "controllers", "ctrl", "web", "rest", "api"],
    "service":    ["service", "services", "svc", "business"],
    "repository": ["repository", "repositories", "repo", "dao"],
    "entity":     ["entity", "entities", "model", "models", "domain"],
    "dto":        ["dto", "dtos", "transfer", "payload"],
    "mapper":     ["mapper", "mappers", "converter"],
    "exception":  ["exception", "exceptions", "error", "errors"],
    "config":     ["config", "configuration", "cfg"],
}


# ---------------------------------------------------------------------------
# Spring Boot Project Detection
# ---------------------------------------------------------------------------

def is_spring_boot_project(path: Path = Path(".")) -> bool:
    """
    Verifies that the current folder is indeed a Spring Boot project.
    Criteria: presence of pom.xml AND src/main/java/
    """
    return (path / "pom.xml").exists() and (path / "src" / "main" / "java").exists()


def detect_base_package(path: Path = Path(".")) -> str | None:
    """
    Scans src/main/java/ to find the *Application.java file
    and automatically infer the base package.

    Returns the package (e.g., "com.pio.ecommerce") or None if not found.
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
    Reads pom.xml to extract artifactId as the project name.
    Returns the current folder name if not found.
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
    Detects the Spring Boot configuration format used in the project.

    Priority rules:
    1. If application.properties exists → returns ("properties", path)
    2. If application.yaml exists       → returns ("yaml", path)
    3. If application.yml exists        → returns ("yaml", path)
    4. If multiple exist                → takes properties by default, logs a warning
    5. If none exist                    → returns ("properties", path) by default
                                          and logs a warning

    Returns a tuple (format: str, filepath: Path)
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
        logger.warning("Multiple configuration files detected. 'application.properties' will be used by default.")
        # Specifically look for properties in the list
        for fmt, p in found:
            if fmt == "properties":
                return fmt, p
        return found[0]

    if not found:
        logger.warning("No configuration file detected. Using 'application.properties' by default.")
        return "properties", prop_path

    return found[0]


def detect_existing_folders(package_path: Path) -> FolderMapping:
    """
    Scans the Java package folder to detect existing directories.
    Returns a FolderMapping with the actual names found.
    """
    mapping_dict = {}
    if package_path.exists():
        for layer, synonyms in EXPECTED_FOLDERS.items():
            for syn in synonyms:
                path = package_path / syn
                if path.is_dir():
                    # Special case for 'models/entity'
                    if syn == "models" and layer == "entity":
                        if (path / "entity").is_dir():
                            mapping_dict[layer] = "models/entity"
                            break
                        if (path / "model").is_dir():
                            mapping_dict[layer] = "models/model"
                            break
                    
                    mapping_dict[layer] = syn
                    break
                    
    return FolderMapping(**mapping_dict)


def analyze_pom(path: Path = Path(".")) -> PomFeatures:
    """
    Reads pom.xml and detects present dependencies.

    Dependencies to detect (searching for artifactId in XML content):
    - has_jpa        : "spring-boot-starter-data-jpa"
    - has_lombok     : "lombok"
    - has_swagger    : "springdoc-openapi-starter-webmvc-ui" OR "springdoc-openapi-ui"
    - has_validation : "spring-boot-starter-validation"

    If pom.xml is missing or unreadable, returns PomFeatures() with default values.
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
        logger.warning(f"Error reading pom.xml: {e}. Using default values.")
        return PomFeatures()


# ---------------------------------------------------------------------------
# Generated Files Operations
# ---------------------------------------------------------------------------

def ensure_dir(directory: Path) -> None:
    """Creates a directory and all its parents if necessary."""
    directory.mkdir(parents=True, exist_ok=True)


def write_file(filepath: Path, content: str, overwrite: bool = False) -> bool:
    """
    Writes content to a file.

    - If file exists and overwrite=False, does nothing and returns False.
    - Creates parent directories if necessary.
    - Returns True if the file was written.
    """
    if filepath.exists() and not overwrite:
        return False

    ensure_dir(filepath.parent)
    filepath.write_text(content, encoding="utf-8")
    return True


def append_to_file(filepath: Path, content: str) -> None:
    """
    Appends content to the end of an existing file.
    Used for application.properties (adding Swagger config).
    """
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Java Paths
# ---------------------------------------------------------------------------

def java_source_root(base_path: Path, base_package: str) -> Path:
    """
    Returns the root path for Java sources for a given package.

    e.g.: base_package = "com.pio.ecommerce"
    →   ./src/main/java/com/pio/ecommerce/
    """
    package_path = base_package.replace(".", os.sep)
    return base_path / "src" / "main" / "java" / package_path


def resources_root(base_path: Path = Path(".")) -> Path:
    """Returns the path to the resources folder."""
    return base_path / "src" / "main" / "resources"