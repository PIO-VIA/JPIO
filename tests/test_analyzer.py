"""
Unit tests for the detection utility functions used by the analyzer (file_helper.py).
Interactive wizard (questionary) is not tested as it requires a real terminal — only pure functions are tested.
"""

import pytest
from pathlib import Path
import tempfile
import os

from jpio.utils.file_helper import (
    is_spring_boot_project,
    detect_base_package,
    detect_project_name,
)


# ---------------------------------------------------------------------------
# Fixtures — creation of fake temporary Spring Boot projects
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_spring_project(tmp_path: Path) -> Path:
    """
    Creates a minimal fake Spring Boot project in a temporary folder.
    Structure:
        tmp_path/
        ├── pom.xml
        └── src/main/java/com/pio/ecommerce/
            └── EcommerceApplication.java
    """
    # pom.xml
    pom = tmp_path / "pom.xml"
    pom.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project>
    <groupId>com.pio</groupId>
    <artifactId>ecommerce-api</artifactId>
    <version>0.0.1-SNAPSHOT</version>
</project>
""")

    # Application.java
    java_dir = tmp_path / "src" / "main" / "java" / "com" / "pio" / "ecommerce"
    java_dir.mkdir(parents=True)
    app_file = java_dir / "EcommerceApplication.java"
    app_file.write_text("""package com.pio.ecommerce;
    
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class EcommerceApplication {
    public static void main(String[] args) {
        SpringApplication.run(EcommerceApplication.class, args);
    }
}
""")
    return tmp_path


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    """Empty folder — does not look like a Spring Boot project."""
    return tmp_path


@pytest.fixture
def project_without_app_file(tmp_path: Path) -> Path:
    """Project with pom.xml and src/ but without *Application.java file."""
    pom = tmp_path / "pom.xml"
    pom.write_text("<project><artifactId>no-app</artifactId></project>")
    java_dir = tmp_path / "src" / "main" / "java" / "com" / "pio"
    java_dir.mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: is_spring_boot_project
# ---------------------------------------------------------------------------

class TestIsSpringBootProject:

    def test_valid_project_returns_true(self, fake_spring_project):
        assert is_spring_boot_project(fake_spring_project) is True

    def test_empty_folder_returns_false(self, empty_project):
        assert is_spring_boot_project(empty_project) is False

    def test_missing_pom_returns_false(self, tmp_path):
        # src/ exists but not pom.xml
        (tmp_path / "src" / "main" / "java").mkdir(parents=True)
        assert is_spring_boot_project(tmp_path) is False

    def test_missing_src_returns_false(self, tmp_path):
        # pom.xml exists but not src/
        (tmp_path / "pom.xml").write_text("<project/>")
        assert is_spring_boot_project(tmp_path) is False


# ---------------------------------------------------------------------------
# Tests: detect_base_package
# ---------------------------------------------------------------------------

class TestDetectBasePackage:

    def test_detects_package_correctly(self, fake_spring_project):
        package = detect_base_package(fake_spring_project)
        assert package == "com.pio.ecommerce"

    def test_returns_none_if_no_application_file(self, project_without_app_file):
        package = detect_base_package(project_without_app_file)
        assert package is None

    def test_returns_none_if_no_src(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project/>")
        package = detect_base_package(tmp_path)
        assert package is None

    def test_detects_deep_package(self, tmp_path):
        """Verifies that detection works with a deep package."""
        java_dir = tmp_path / "src" / "main" / "java" / "com" / "company" / "team" / "project"
        java_dir.mkdir(parents=True)
        app = java_dir / "ProjectApplication.java"
        app.write_text("package com.company.team.project;\n\npublic class ProjectApplication {}\n")
        assert detect_base_package(tmp_path) == "com.company.team.project"


# ---------------------------------------------------------------------------
# Tests: detect_project_name
# ---------------------------------------------------------------------------

class TestDetectProjectName:

    def test_reads_artifact_id_from_pom(self, fake_spring_project):
        name = detect_project_name(fake_spring_project)
        assert name == "ecommerce-api"

    def test_falls_back_to_folder_name_if_no_pom(self, tmp_path):
        # No pom.xml → returns the folder name
        name = detect_project_name(tmp_path)
        assert name == tmp_path.name

    def test_falls_back_if_no_artifact_id(self, tmp_path):
        """pom.xml without <artifactId> → returns the folder name."""
        pom = tmp_path / "pom.xml"
        pom.write_text("<project><groupId>com.pio</groupId></project>")
        name = detect_project_name(tmp_path)
        assert name == tmp_path.name