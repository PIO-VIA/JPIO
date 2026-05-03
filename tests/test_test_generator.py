import pytest
from pathlib import Path
from jpio.core.models import (
    JavaClass, JavaMethod, JavaField, JavaParameter, ParseResult, 
    ProjectConfig, TestPlan, TestClass, TestMethod, MockField, TestData
)
from jpio.core.test_plan_analyzer import _classify_class, _extract_mocks, build_test_plan
from jpio.core.test_generator import generate_tests

# ---------------------------------------------------------------------------
# Classification Tests
# ---------------------------------------------------------------------------

def test_classify_service():
    jc = JavaClass(
        name="ProductServiceImpl",
        qualified_name="com.pio.service.ProductServiceImpl",
        package_name="com.pio.service",
        class_type="CLASS",
        annotations=["Service"],
        implements_list=["ProductService"],
        extends_list=[],
        imports=[],
        fields=[],
        methods=[],
        is_abstract=False,
        is_public=True,
        file_path="ProductServiceImpl.java"
    )
    assert _classify_class(jc) == "SERVICE_IMPL"

def test_classify_controller():
    jc = JavaClass(
        name="ProductController",
        qualified_name="com.pio.controller.ProductController",
        package_name="com.pio.controller",
        class_type="CLASS",
        annotations=["RestController"],
        implements_list=[],
        extends_list=[],
        imports=[],
        fields=[],
        methods=[],
        is_abstract=False,
        is_public=True,
        file_path="ProductController.java"
    )
    assert _classify_class(jc) == "CONTROLLER"

def test_classify_repository():
    jc = JavaClass(
        name="ProductRepository",
        qualified_name="com.pio.repository.ProductRepository",
        package_name="com.pio.repository",
        class_type="INTERFACE",
        annotations=[],
        implements_list=[],
        extends_list=["JpaRepository<Product, Long>"],
        imports=[],
        fields=[],
        methods=[],
        is_abstract=True,
        is_public=True,
        file_path="ProductRepository.java"
    )
    assert _classify_class(jc) == "REPOSITORY"

def test_classify_mapper():
    jc = JavaClass(
        name="ProductMapper",
        qualified_name="com.pio.mapper.ProductMapper",
        package_name="com.pio.mapper",
        class_type="CLASS",
        annotations=["Component"],
        implements_list=[],
        extends_list=[],
        imports=[],
        fields=[],
        methods=[],
        is_abstract=False,
        is_public=True,
        file_path="ProductMapper.java"
    )
    assert _classify_class(jc) == "MAPPER"

def test_classify_unknown():
    jc = JavaClass(
        name="ProductDTO",
        qualified_name="com.pio.dto.ProductDTO",
        package_name="com.pio.dto",
        class_type="CLASS",
        annotations=["Data"],
        implements_list=[],
        extends_list=[],
        imports=[],
        fields=[],
        methods=[],
        is_abstract=False,
        is_public=True,
        file_path="ProductDTO.java"
    )
    assert _classify_class(jc) is None


# ---------------------------------------------------------------------------
# Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_mocks_service():
    jc = JavaClass(
        name="ProductServiceImpl",
        qualified_name="", package_name="", class_type="CLASS",
        annotations=["Service"], implements_list=[], extends_list=[], imports=[],
        fields=[
            JavaField(name="repo", type="ProductRepository", type_simple="ProductRepository", annotations=[], is_final=True)
        ],
        methods=[], is_abstract=False, is_public=True, file_path=""
    )
    mocks = _extract_mocks(jc, "SERVICE_IMPL")
    assert len(mocks) == 1
    assert mocks[0].name == "repo"
    assert mocks[0].type == "ProductRepository"
    assert mocks[0].mock_type == "Mock"


# ---------------------------------------------------------------------------
# Plan & Generation Tests
# ---------------------------------------------------------------------------

def test_build_test_plan_scenarios():
    # Mock methods
    methods = [
        JavaMethod(name="findAll", return_type="List<Product>", return_type_simple="List", parameters=[], annotations=[], throws_list=[], is_public=True, is_static=False, is_override=True, visibility="public"),
        JavaMethod(name="findById", return_type="Optional<Product>", return_type_simple="Optional", parameters=[JavaParameter(name="id", type="Long")], annotations=[], throws_list=[], is_public=True, is_static=False, is_override=True, visibility="public"),
        JavaMethod(name="delete", return_type="void", return_type_simple="void", parameters=[JavaParameter(name="id", type="Long")], annotations=[], throws_list=[], is_public=True, is_static=False, is_override=True, visibility="public")
    ]
    
    jc = JavaClass(
        name="ProductServiceImpl",
        qualified_name="com.pio.service.ProductServiceImpl",
        package_name="com.pio.service",
        class_type="CLASS",
        annotations=["Service"],
        implements_list=["ProductService"],
        extends_list=[],
        imports=[],
        fields=[JavaField(name="productRepository", type="ProductRepository", type_simple="ProductRepository", annotations=[], is_final=True)],
        methods=methods,
        is_abstract=False,
        is_public=True,
        file_path="ProductServiceImpl.java"
    )
    
    pr = ParseResult(classes=[jc], total_files=1, total_classes=1, errors=[], parser_version="1.0.0", java_version="21")
    pc = ProjectConfig(base_package="com.pio", api_prefix="/api/v1")
    
    plan = build_test_plan(pr, pc)
    assert len(plan.test_classes) == 1
    tc = plan.test_classes[0]
    
    # 2 scenarios for findAll, 2 for findById, 2 for delete
    assert len(tc.test_methods) == 6
    
    scenarios = [m.scenario for m in tc.test_methods]
    assert scenarios.count("happy_path") == 3
    assert scenarios.count("empty_list") == 1
    assert scenarios.count("not_found") == 2

def test_generate_tests_output():
    tc = TestClass(
        test_class_name="ProductServiceImplTest",
        class_under_test="ProductServiceImpl",
        test_type="SERVICE_IMPL",
        package_name="com.pio.service",
        base_package="com.pio",
        imports_needed=["java.util.List"],
        mock_fields=[MockField(name="repo", type="Repo", mock_type="Mock")],
        inject_mocks_field="service",
        inject_mocks_type="ProductServiceImpl",
        setup_data=[TestData(variable_name="p", type="Product", builder_fields=[("id", "1L")])],
        test_methods=[TestMethod(test_name="t1", method_under_test="m1", scenario="s1", given_mocks=[], act_line="a", assert_lines=["as1"], verify_lines=[])]
    )
    
    plan = TestPlan(test_classes=[tc], base_package="com.pio")
    generated = generate_tests(plan)
    
    assert "src/test/java/com/pio/service/ProductServiceImplTest.java" in generated
    content = generated["src/test/java/com/pio/service/ProductServiceImplTest.java"]
    assert "package com.pio.service;" in content
    assert "class ProductServiceImplTest" in content
