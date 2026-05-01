"""
Unit tests for core/writer.py.
Verifies that files are correctly created on disk,
that append mode works, and that existing files
are not overwritten by default.
"""

import pytest
from pathlib import Path

from jpio.core.writer import write_all, APPEND_PREFIX


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generated_simple() -> dict[str, str]:
    """Simulates a minimal output dict from generator.py."""
    return {
        "src/main/java/com/pio/test/models/entity/Product.java":     "// Product.java content",
        "src/main/java/com/pio/test/dto/response/ProductResponseDTO.java":     "// ProductDTO.java content",
        "src/main/java/com/pio/test/service/ProductService.java": "// ProductService content",
    }


@pytest.fixture
def generated_with_append(tmp_path: Path) -> tuple[dict, Path]:
    """
    Simulates a dict with an __append__: key and creates the target file.
    Returns the dict and the path to the application.properties file.
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
# Tests: Normal File Creation
# ---------------------------------------------------------------------------

class TestWriteNormalFiles:

    def test_creates_files_on_disk(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        assert (tmp_path / "src/main/java/com/pio/test/models/entity/Product.java").exists()
        assert (tmp_path / "src/main/java/com/pio/test/dto/response/ProductResponseDTO.java").exists()
        assert (tmp_path / "src/main/java/com/pio/test/service/ProductService.java").exists()

    def test_file_content_is_correct(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        content = (tmp_path / "src/main/java/com/pio/test/models/entity/Product.java").read_text()
        assert content == "// Product.java content"

    def test_creates_parent_directories(self, tmp_path, generated_simple):
        write_all(generated_simple, base_path=tmp_path)

        assert (tmp_path / "src" / "main" / "java" / "com" / "pio" / "test" / "models" / "entity").is_dir()
        assert (tmp_path / "src" / "main" / "java" / "com" / "pio" / "test" / "dto" / "response").is_dir()

    def test_returns_correct_file_count(self, tmp_path, generated_simple):
        count = write_all(generated_simple, base_path=tmp_path)
        assert count == 3

    def test_does_not_overwrite_existing_file(self, tmp_path):
        """An already present file should not be overwritten (overwrite=False by default)."""
        target = tmp_path / "src/main/java/com/pio/test/models/entity/Product.java"
        target.parent.mkdir(parents=True)
        target.write_text("// ORIGINAL")
        generated = {"src/main/java/com/pio/test/models/entity/Product.java": "// NEW CONTENT"}
        count = write_all(generated, base_path=tmp_path)

        assert target.read_text() == "// ORIGINAL"
        assert count == 0   # no file written because it already exists

    def test_skips_existing_and_writes_new(self, tmp_path):
        """Writes new files and ignores existing ones."""
        existing = tmp_path / "src/main/java/com/pio/test/models/entity/Product.java"
        existing.parent.mkdir(parents=True)
        existing.write_text("// ORIGINAL")
        generated = {
            "src/main/java/com/pio/test/models/entity/Product.java": "// NEW",  # existing → ignored
            "src/main/java/com/pio/test/dto/response/ProductResponseDTO.java": "// DTO",  # new → written
        }
        count = write_all(generated, base_path=tmp_path)

        assert existing.read_text() == "// ORIGINAL"
        assert (tmp_path / "src/main/java/com/pio/test/dto/response/ProductResponseDTO.java").read_text() == "// DTO"
        assert count == 1


# ---------------------------------------------------------------------------
# Tests: Append Mode (application.properties)
# ---------------------------------------------------------------------------

class TestAppendMode:

    def test_appends_to_existing_file(self, tmp_path, generated_with_append):
        generated, props_file = generated_with_append
        write_all(generated, base_path=tmp_path)

        content = props_file.read_text()
        assert "server.port=8080"          in content   # original content
        assert "springdoc.api-docs.path"   in content   # appended content

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
        """If the target file does not exist, append is ignored without crashing."""
        generated = {
            f"{APPEND_PREFIX}src/main/resources/application.properties":
                "# some config"
        }
        count = write_all(generated, base_path=tmp_path)
        assert count == 0
        assert not (tmp_path / "src/main/resources/application.properties").exists()


# ---------------------------------------------------------------------------
# Tests: Edge Cases
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
        """Verifies that special characters (accents) are correctly encoded."""
        content = "// comment with accents: é, è, ê, ç, à"
        generated = {"src/main/java/com/pio/test/Unicode.java": content}
        write_all(generated, base_path=tmp_path)
        result = (tmp_path / "src/main/java/com/pio/test/Unicode.java").read_text(encoding="utf-8")
        assert result == content