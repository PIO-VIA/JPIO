"""
tests/test_generator.py
------------------------
Tests unitaires pour core/generator.py.
On vérifie que les templates Jinja2 produisent bien le code Java attendu
pour différentes configurations d'entités et de relations.
"""

import pytest
from jpio.core.models import ProjectConfig, Entity, Field, Relation, PomFeatures, FolderMapping
from jpio.core.generator import generate_all
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures — ProjectConfig de test
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_config() -> ProjectConfig:
    """Projet minimal : une entité Product sans relation."""
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
    """Projet avec deux entités et une relation ManyToMany."""
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
                    Relation(kind="ManyToMany", target="Product", mapped_by="categories", owner=False)
                ],
            ),
        ],
    )


@pytest.fixture
def config_with_one_to_many() -> ProjectConfig:
    """Projet avec relation OneToMany : Order → OrderItem."""
    return ProjectConfig(
        base_package="com.pio.orders",
        api_prefix="/api/v1",
        entities=[
            Entity(
                name="Order",
                fields=[Field(name="reference", java_type="String", nullable=False)],
                relations=[
                    Relation(kind="OneToMany", target="OrderItem", mapped_by="order", owner=True)
                ],
            ),
            Entity(
                name="OrderItem",
                fields=[Field(name="quantity", java_type="Integer", nullable=False)],
                relations=[
                    Relation(kind="ManyToOne", target="Order", mapped_by="", owner=False)
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests : structure des clés générées
# ---------------------------------------------------------------------------

class TestGeneratedKeys:

    def test_generates_all_expected_files_for_entity(self, simple_config):
        output = generate_all(simple_config)
        base = "src/main/java/com/pio/ecommerce"

        expected_files = [
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
            f"{base}/config/SwaggerConfig.java",
        ]

        for expected in expected_files:
            assert expected in output, f"Fichier manquant : {expected}"

    def test_generates_append_for_application_properties(self, simple_config):
        output = generate_all(simple_config)
        append_keys = [k for k in output if k.startswith("__append__:")]
        assert len(append_keys) == 1
        assert "application.properties" in append_keys[0]

    def test_generates_files_for_each_entity(self, config_with_many_to_many):
        output = generate_all(config_with_many_to_many)
        base = "src/main/java/com/pio/shop"
        assert f"{base}/models/entity/Product.java" in output
        assert f"{base}/models/entity/Category.java" in output
        assert f"{base}/controller/ProductController.java" in output
        assert f"{base}/controller/CategoryController.java" in output


# ---------------------------------------------------------------------------
# Tests : contenu de l'entité
# ---------------------------------------------------------------------------

class TestEntityContent:

    def test_entity_has_correct_package(self, simple_config):
        output = generate_all(simple_config)
        entity_java = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
        assert "package com.pio.ecommerce.models.entity;" in entity_java

    def test_entity_has_lombok_annotations(self, simple_config):
        output = generate_all(simple_config)
        entity_java = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
        assert "@Data"               in entity_java
        assert "@NoArgsConstructor"  in entity_java
        assert "@AllArgsConstructor" in entity_java
        assert "@Builder"            in entity_java

    def test_entity_has_jpa_annotations(self, simple_config):
        output = generate_all(simple_config)
        entity_java = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
        assert "@Entity"   in entity_java
        assert "@Table"    in entity_java
        assert "@Id"       in entity_java
        assert "@GeneratedValue" in entity_java

    def test_entity_has_all_fields(self, simple_config):
        output = generate_all(simple_config)
        entity_java = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
        assert "private String name;"   in entity_java
        assert "private Double price;"  in entity_java
        assert "private Integer stock;" in entity_java

    def test_non_nullable_field_has_column_annotation(self, simple_config):
        output = generate_all(simple_config)
        entity_java = output["src/main/java/com/pio/ecommerce/models/entity/Product.java"]
        assert "@Column(nullable = false)" in entity_java

    def test_entity_imports_localdate(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[
                Entity(
                    name="Event",
                    fields=[Field(name="date", java_type="LocalDate", nullable=True)],
                    relations=[],
                )
            ],
        )
        output = generate_all(config)
        entity_java = output["src/main/java/com/pio/test/models/entity/Event.java"]
        assert "import java.time.LocalDate;" in entity_java


# ---------------------------------------------------------------------------
# Tests : relations
# ---------------------------------------------------------------------------

class TestRelationsContent:

    def test_many_to_many_owner_has_join_table(self, config_with_many_to_many):
        output = generate_all(config_with_many_to_many)
        product_java = output["src/main/java/com/pio/shop/models/entity/Product.java"]
        assert "@ManyToMany"  in product_java
        assert "@JoinTable"   in product_java
        assert "joinColumns"  in product_java
        assert "inverseJoinColumns" in product_java

    def test_many_to_many_inverse_has_mapped_by(self, config_with_many_to_many):
        output = generate_all(config_with_many_to_many)
        category_java = output["src/main/java/com/pio/shop/models/entity/Category.java"]
        assert "@ManyToMany(mappedBy" in category_java
        assert "@JoinTable" not in category_java

    def test_one_to_many_has_cascade(self, config_with_one_to_many):
        output = generate_all(config_with_one_to_many)
        order_java = output["src/main/java/com/pio/orders/models/entity/Order.java"]
        assert "@OneToMany" in order_java
        assert "cascade"    in order_java
        assert "orphanRemoval" in order_java

    def test_many_to_one_has_join_column(self, config_with_one_to_many):
        output = generate_all(config_with_one_to_many)
        item_java = output["src/main/java/com/pio/orders/models/entity/OrderItem.java"]
        assert "@ManyToOne"   in item_java
        assert "@JoinColumn"  in item_java


# ---------------------------------------------------------------------------
# Tests : DTO
# ---------------------------------------------------------------------------

class TestDTOContent:

    def test_dto_has_correct_package(self, simple_config):
        output = generate_all(simple_config)
        dto = output["src/main/java/com/pio/ecommerce/dto/response/ProductResponseDTO.java"]
        assert "package com.pio.ecommerce.dto.response;" in dto

    def test_dto_has_lombok_annotations(self, simple_config):
        output = generate_all(simple_config)
        dto = output["src/main/java/com/pio/ecommerce/dto/response/ProductResponseDTO.java"]
        assert "@Data"    in dto
        assert "@Builder" in dto

    def test_dto_uses_ids_for_relations(self, config_with_many_to_many):
        output = generate_all(config_with_many_to_many)
        dto = output["src/main/java/com/pio/shop/dto/response/ProductResponseDTO.java"]
        assert "List<Long>" in dto
        assert "Ids"        in dto


# ---------------------------------------------------------------------------
# Tests : Controller
# ---------------------------------------------------------------------------

class TestControllerContent:

    def test_controller_has_correct_mapping(self, simple_config):
        output = generate_all(simple_config)
        ctrl = output["src/main/java/com/pio/ecommerce/controller/ProductController.java"]
        assert '@RequestMapping("/api/v1/products")' in ctrl

    def test_controller_has_all_crud_methods(self, simple_config):
        output = generate_all(simple_config)
        ctrl = output["src/main/java/com/pio/ecommerce/controller/ProductController.java"]
        assert "@GetMapping"    in ctrl
        assert "@PostMapping"   in ctrl
        assert "@PutMapping"    in ctrl
        assert "@DeleteMapping" in ctrl

    def test_controller_uses_required_args_constructor(self, simple_config):
        output = generate_all(simple_config)
        ctrl = output["src/main/java/com/pio/ecommerce/controller/ProductController.java"]
        assert "@RequiredArgsConstructor" in ctrl


# ---------------------------------------------------------------------------
# Tests : Repository
# ---------------------------------------------------------------------------

class TestRepositoryContent:

    def test_repository_extends_jpa_repository(self, simple_config):
        output = generate_all(simple_config)
        repo = output["src/main/java/com/pio/ecommerce/repository/ProductRepository.java"]
        assert "JpaRepository<Product, Long>" in repo

    def test_repository_has_find_by_methods(self, simple_config):
        output = generate_all(simple_config)
        repo = output["src/main/java/com/pio/ecommerce/repository/ProductRepository.java"]
        assert "findByName"  in repo
        assert "findByPrice" in repo
        assert "findByStock" in repo


# ---------------------------------------------------------------------------
# Tests : Exception
# ---------------------------------------------------------------------------

class TestExceptionContent:

    def test_not_found_exception_message(self, simple_config):
        output = generate_all(simple_config)
        exc = output["src/main/java/com/pio/ecommerce/exception/ProductNotFoundException.java"]
        assert "ProductNotFoundException" in exc
        assert "RuntimeException"         in exc

    def test_global_handler_covers_all_entities(self, config_with_many_to_many):
        output = generate_all(config_with_many_to_many)
        handler = output["src/main/java/com/pio/shop/exception/GlobalExceptionHandler.java"]
        assert "ProductNotFoundException"  in handler
        assert "CategoryNotFoundException" in handler
        assert "@RestControllerAdvice"     in handler


# ---------------------------------------------------------------------------
# Tests : PomFeatures adaptations
# ---------------------------------------------------------------------------

class TestPomFeatures:

    def test_no_lombok_generates_getters_setters(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product", fields=[Field("name", "String", nullable=False)])],
            pom_features=PomFeatures(has_lombok=False)
        )
        output = generate_all(config)
        entity_java = output["src/main/java/com/pio/test/models/entity/Product.java"]
        assert "@Data" not in entity_java
        assert "public String getName()" in entity_java
        assert "public void setName(String name)" in entity_java
        assert "public Product()" in entity_java

    def test_no_jpa_uses_crud_repository(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_jpa=False)
        )
        output = generate_all(config)
        repo_java = output["src/main/java/com/pio/test/repository/ProductRepository.java"]
        assert "extends CrudRepository<Product, Long>" in repo_java
        assert "import org.springframework.data.repository.CrudRepository;" in repo_java

    def test_no_swagger_omits_config_and_append(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_swagger=False)
        )
        output = generate_all(config)
        base = "src/main/java/com/pio/test"
        assert f"{base}/config/SwaggerConfig.java" not in output
        assert not any(k.startswith("__append__:") for k in output)

    def test_validation_adds_annotations_to_dto(self):
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product", fields=[
                Field("name", "String", nullable=False),
                Field("price", "Double", nullable=False)
            ])],
            pom_features=PomFeatures(has_validation=True)
        )
        output = generate_all(config)
        dto_java = output["src/main/java/com/pio/test/dto/request/ProductRequestDTO.java"]
        assert "import jakarta.validation.constraints.*;" in dto_java
        assert "@NotBlank" in dto_java
        assert "@NotNull" in dto_java

    def test_yaml_config_detects_correct_append_key(self, tmp_path):
        # On simule un dossier avec application.yaml
        res_dir = tmp_path / "src" / "main" / "resources"
        res_dir.mkdir(parents=True)
        (res_dir / "application.yaml").write_text("existing: true")
        
        config = ProjectConfig(
            base_package="com.pio.test",
            api_prefix="/api/v1",
            entities=[Entity(name="Product")],
            pom_features=PomFeatures(has_swagger=True)
        )
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