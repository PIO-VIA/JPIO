"""
Unit tests for core/generator.py.
Verifies that Jinja2 templates produce the expected Java code
for different entity and relation configurations.
"""

import pytest
from jpio.core.models import ProjectConfig, Entity, Field, Relation, PomFeatures, FolderMapping
from jpio.core.generator import generate_all
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures — Test ProjectConfig
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_config() -> ProjectConfig:
    """Minimal project: one Product entity without relations."""
    return ProjectConfig(
        base_package="com.pio.ecommerce",
        api_prefix="/api/v1",
        entities=[
            Entity(
                name="Product",
                fields=[
                    Field(name="name",  java_type="String",  nullable=False),
                    Field(name="price", java_type="Double",  nullable=True),
                    Field(name="stock", java_type="Integer", nullable=True),
                ],
                relations=[],
            )
        ],
    )


@pytest.fixture
def config_with_many_to_many() -> ProjectConfig:
    """Project with two entities and a ManyToMany relation."""
    return ProjectConfig(
        base_package="com.pio.shop",
        api_prefix="/api/v1",
        entities=[
            Entity(
                name="Product",
                fields=[Field(name="name", java_type="String", nullable=False)],
                relations=[
                    Relation(kind="ManyToMany", target="Category", mapped_by="products", owner=True)
                ],
            ),
            Entity(
                name="Category",
                fields=[Field(name="name", java_type="String", nullable=False)],
                relations=[
                    Relation(kind="ManyToMany", target="Product", mapped_by="categorys", owner=False)
                ],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests: General Generation
# ---------------------------------------------------------------------------

def test_generate_all_keys(simple_config):
    """Verifies that all expected files are present in the output dict."""
    output = generate_all(simple_config)
    
    # ── Path check ──────────────────────────────────────────────────────────
    base = "src/main/java/com/pio/ecommerce"
    
    expected_paths = [
        f"{base}/models/entity/Product.java",
        f"{base}/dto/request/ProductRequestDTO.java",
        f"{base}/dto/response/ProductResponseDTO.java",
        f"{base}/mapper/ProductMapper.java",
        f"{base}/repository/ProductRepository.java",
        f"{base}/service/ProductService.java",
        f"{base}/service/ProductServiceImpl.java",
        f"{base}/controller/ProductController.java",
        f"{base}/exception/ProductNotFoundException.java",
        f"{base}/exception/GlobalExceptionHandler.java",
    ]
    
    for path in expected_paths:
        assert path in output


# ---------------------------------------------------------------------------
# Tests: Template Content (Entity)
# ---------------------------------------------------------------------------

def test_entity_content(simple_config):
    output = generate_all(simple_config)
    java_code = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
    
    assert "public class Product" in java_code
    assert "private String name;" in java_code
    assert "private Double price;" in java_code
    assert "@Id" in java_code
    assert "@GeneratedValue" in java_code


def test_repository_content(simple_config):
    output = generate_all(simple_config)
    java_code = output["src/main/java/com/pio/ecommerce/repository/ProductRepository.java"]
    
    assert "public interface ProductRepository extends JpaRepository<Product, Long>" in java_code


def test_controller_content(simple_config):
    output = generate_all(simple_config)
    java_code = output["src/main/java/com/pio/ecommerce/controller/ProductController.java"]
    
    assert "@RestController" in java_code
    assert "@RequestMapping(\"/api/v1/products\")" in java_code
    assert "public ResponseEntity<ProductResponseDTO> create(" in java_code


# ---------------------------------------------------------------------------
# Tests: Relations
# ---------------------------------------------------------------------------

def test_many_to_many_owner_side(config_with_many_to_many):
    output = generate_all(config_with_many_to_many)
    java_code = output["src/main/java/com/pio/shop/models/entity/Product.java"]
    
    assert "@ManyToMany" in java_code
    assert "@JoinTable" in java_code
    assert "private List<Category> categorys;" in java_code


def test_many_to_many_inverse_side(config_with_many_to_many):
    output = generate_all(config_with_many_to_many)
    java_code = output["src/main/java/com/pio/shop/models/entity/Category.java"]
    
    assert "@ManyToMany(mappedBy = \"categorys\")" in java_code
    assert "private List<Product> products;" in java_code
    assert "@JoinTable" not in java_code


# ---------------------------------------------------------------------------
# Tests: PomFeatures
# ---------------------------------------------------------------------------

class TestPomFeatures:

    def test_no_lombok_generates_getters_setters(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[Entity(name="Product", fields=[Field("name", "String")])],
            pom_features=PomFeatures(has_lombok=False)
        )
        output = generate_all(config)
        java_code = output["src/main/java/com/pio/test/models/entity/Product.java"]
        
        assert "@Data" not in java_code
        assert "public String getName()" in java_code
        assert "public void setName(String name)" in java_code

    def test_no_jpa_generates_crud_repository(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_jpa=False)
        )
        output = generate_all(config)
        java_code = output["src/main/java/com/pio/test/repository/ProductRepository.java"]
        
        assert "extends JpaRepository" not in java_code
        assert "extends CrudRepository<Product, Long>" in java_code

    def test_validation_adds_annotations(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[
                Entity(
                    name="Product",
                    fields=[
                        Field("name", "String", nullable=False),
                        Field("price", "Double", nullable=False)
                    ]
                )
            ],
            pom_features=PomFeatures(has_validation=True)
        )
        output = generate_all(config)
        request_dto = output["src/main/java/com/pio/test/dto/request/ProductRequestDTO.java"]
        
        assert "@NotBlank" in request_dto
        assert "@NotNull" in request_dto
        assert "import jakarta.validation.constraints" in request_dto

    def test_no_swagger_skips_config_and_annotations(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_swagger=False)
        )
        output = generate_all(config)
        
        # Check global config absence
        swagger_path = "src/main/java/com/pio/test/config/SwaggerConfig.java"
        assert swagger_path not in output
        
        # Check controller annotations absence
        controller_code = output["src/main/java/com/pio/test/controller/ProductController.java"]
        assert "@Tag" not in controller_code
        assert "@Operation" not in controller_code

    def test_swagger_properties_append(self, tmp_path):
        """Verifies that Swagger properties are correctly generated for .properties."""
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_swagger=True)
        )
        # Setup fake resources for detection
        res_dir = tmp_path / "src" / "main" / "resources"
        res_dir.mkdir(parents=True)
        (res_dir / "application.properties").write_text("existing=value")
        
        output = generate_all(config, base_path=tmp_path)
        
        expected_key = "__append__:src/main/resources/application.properties"
        assert expected_key in output
        assert "springdoc.api-docs.path=/api-docs" in output[expected_key]

    def test_swagger_yaml_append(self, tmp_path):
        """Verifies that Swagger properties are correctly generated for .yaml."""
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_swagger=True)
        )
        # Setup fake resources for detection
        res_dir = tmp_path / "src" / "main" / "resources"
        res_dir.mkdir(parents=True)
        (res_dir / "application.yaml").write_text("existing: value")
        
        output = generate_all(config, base_path=tmp_path)
        
        expected_key = "__append__:src/main/resources/application.yaml"
        assert expected_key in output
        assert "springdoc:" in output[expected_key]

    def test_custom_folder_mapping_paths(self):
        mapping = FolderMapping(
            entity="domain/models",
            controller="web/api",
            service="logic/services"
        )
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product")],
            folder_mapping=mapping
        )
        output = generate_all(config)
        base = "src/main/java/com/pio/test"
        
        assert f"{base}/domain/models/Product.java" in output
        assert f"{base}/web/api/ProductController.java" in output
        assert f"{base}/logic/services/ProductService.java" in output