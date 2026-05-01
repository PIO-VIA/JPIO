"""
tests/test_writer.py
---------------------
Tests unitaires pour core/writer.py.
On vérifie que les fichiers sont bien créés sur le disque,
que le mode append fonctionne, et que les fichiers existants
ne sont pas écrasés par défaut.
"""

import pytest
from pathlib import Path

from jpio.core.writer import write_all, APPEND_PREFIX


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generated_simple() -> dict[str, str]:
    """Simule un dict de sortie minimal de generator.py."""
    return {
        "src/main/java/com/pio/test/entity/Product.java":     "// Product.java content",
        "src/main/java/com/pio/test/dto/ProductDTO.java":     "// ProductDTO.java content",
        "src/main/java/com/pio/test/service/ProductService.java": "// ProductService content",
    }


@pytest.fixture
def generated_with_append(tmp_path: Path) -> tuple[dict, Path]:
    """
    Simule un dict avec une clé __append__: et crée le fichier cible.
    Retourne le dict et le chemin du fichier application.properties.
    """
    props_file = tmp_path / "src" / "main" / "resources" / "application.properties"
    props_file.parent.mkdir(parents=True)
    props_file.write_text("# existing config\nserver.port=8080\n")

    generated = {
        f"{APPEND_PREFIX}src/main/resources/application.properties":
            "\n# Swagger\nspringdoc.api-docs.path=/api-docs\n"
    }
    return generated, props_file


# ---------------------------------------------------------------------------
# Tests : création de fichiers normaux
# ---------------------------------------------------------------------------

class TestWriteNormalFiles:

    def test_creates_files_on_disk(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        assert (tmp_path / "src/main/java/com/pio/test/entity/Product.java").exists()
        assert (tmp_path / "src/main/java/com/pio/test/dto/ProductDTO.java").exists()
        assert (tmp_path / "src/main/java/com/pio/test/service/ProductService.java").exists()

    def test_file_content_is_correct(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        content = (tmp_path / "src/main/java/com/pio/test/entity/Product.java").read_text()
        assert content == "// Product.java content"

    def test_creates_parent_directories(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        assert (tmp_path / "src" / "main" / "java" / "com" / "pio" / "test" / "entity").is_dir()
        assert (tmp_path / "src" / "main" / "java" / "com" / "pio" / "test" / "dto").is_dir()

    def test_returns_correct_file_count(self, tmp_path, generated_simple):
        count = write_all(generated_simple, base_path=tmp_path)
        assert count == 3

    def test_does_not_overwrite_existing_file(self, tmp_path):
        """Un fichier déjà présent ne doit pas être écrasé (overwrite=False par défaut)."""
        target = tmp_path / "src/main/java/com/pio/test/entity/Product.java"
        target.parent.mkdir(parents=True)
        target.write_text("// ORIGINAL")

        generated = {"src/main/java/com/pio/test/entity/Product.java": "// NEW CONTENT"}
        count = write_all(generated, base_path=tmp_path)

        assert target.read_text() == "// ORIGINAL"
        assert count == 0   # aucun fichier écrit car déjà existant

    def test_skips_existing_and_writes_new(self, tmp_path):
        """Écrit les nouveaux fichiers et ignore les existants."""
        existing = tmp_path / "src/main/java/com/pio/test/entity/Product.java"
        existing.parent.mkdir(parents=True)
        existing.write_text("// ORIGINAL")

        generated = {
            "src/main/java/com/pio/test/entity/Product.java": "// NEW",  # existant → ignoré
            "src/main/java/com/pio/test/dto/ProductDTO.java": "// DTO",  # nouveau → écrit
        }
        count = write_all(generated, base_path=tmp_path)

        assert existing.read_text() == "// ORIGINAL"
        assert (tmp_path / "src/main/java/com/pio/test/dto/ProductDTO.java").read_text() == "// DTO"
        assert count == 1


# ---------------------------------------------------------------------------
# Tests : mode append (application.properties)
# ---------------------------------------------------------------------------

class TestAppendMode:

    def test_appends_to_existing_file(self, tmp_path, generated_with_append):
        generated, props_file = generated_with_append
        write_all(generated, base_path=tmp_path)

        content = props_file.read_text()
        assert "server.port=8080"          in content   # contenu original
        assert "springdoc.api-docs.path"   in content   # contenu ajouté

    def test_original_content_preserved(self, tmp_path, generated_with_append):
        generated, props_file = generated_with_append
        write_all(generated, base_path=tmp_path)

        content = props_file.read_text()
        assert content.startswith("# existing config")

    def test_append_counts_as_written(self, tmp_path, generated_with_append):
        generated, _ = generated_with_append
        count = write_all(generated, base_path=tmp_path)
        assert count == 1

    def test_append_ignored_if_file_missing(self, tmp_path):
        """Si le fichier cible n'existe pas, l'append est ignoré sans planter."""
        generated = {
            f"{APPEND_PREFIX}src/main/resources/application.properties":
                "# some config"
        }
        count = write_all(generated, base_path=tmp_path)
        assert count == 0
        assert not (tmp_path / "src/main/resources/application.properties").exists()


# ---------------------------------------------------------------------------
# Tests : cas limites
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_generated_dict(self, tmp_path):
        count = write_all({}, base_path=tmp_path)
        assert count == 0

    def test_empty_content_creates_empty_file(self, tmp_path):
        generated = {"src/main/java/com/pio/test/Empty.java": ""}
        write_all(generated, base_path=tmp_path)
        target = tmp_path / "src/main/java/com/pio/test/Empty.java"
        assert target.exists()
        assert target.read_text() == ""

    def test_unicode_content_written_correctly(self, tmp_path):
        """Vérifie que les caractères spéciaux (accents) sont bien encodés."""
        content = "// commentaire avec accents : é, è, ê, ç, à"
        generated = {"src/main/java/com/pio/test/Unicode.java": content}
        write_all(generated, base_path=tmp_path)
        result = (tmp_path / "src/main/java/com/pio/test/Unicode.java").read_text(encoding="utf-8")
        assert result == content