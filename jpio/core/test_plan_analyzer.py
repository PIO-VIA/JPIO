import re
from typing import List, Optional
from .models import (
    ParseResult, ProjectConfig, TestPlan, TestClass, TestMethod,
    JavaClass, MockField, TestData, JAVA_TEST_VALUES, PomFeatures
)

# ---------------------------------------------------------------------------
# Test Plan Analyzer
# ---------------------------------------------------------------------------

def build_test_plan(parse_result: ParseResult, project_config: ProjectConfig) -> TestPlan:
    """
    Analyzes ParseResult to build a complete TestPlan.
    """
    test_classes = []
    base_package = project_config.base_package
    pom_features = project_config.pom_features or PomFeatures()

    for java_class in parse_result.classes:
        test_type = _classify_class(java_class)
        if not test_type:
            continue

        mock_fields = _extract_mocks(java_class, test_type)
        setup_data = _build_setup_data(java_class, test_type, pom_features)
        test_methods = _build_test_methods(java_class, test_type, mock_fields, setup_data)
        imports_needed = _build_imports(test_type, java_class, base_package)

        # Determine inject mocks field/type
        inject_mocks_field = java_class.name[0].lower() + java_class.name[1:]
        inject_mocks_type = java_class.name

        test_classes.append(TestClass(
            test_class_name=f"{java_class.name}Test",
            class_under_test=java_class.name,
            test_type=test_type,
            package_name=java_class.package_name,
            base_package=base_package,
            imports_needed=imports_needed,
            mock_fields=mock_fields,
            inject_mocks_field=inject_mocks_field,
            inject_mocks_type=inject_mocks_type,
            setup_data=setup_data,
            test_methods=test_methods,
            api_prefix=project_config.api_prefix
        ))

    return TestPlan(test_classes=test_classes, base_package=base_package)


# ── Classification ──────────────────────────────────────────────────────────

def _classify_class(java_class: JavaClass) -> Optional[str]:
    """
    Determines the type of test to generate for a class based on naming and annotations.
    """
    # 1. SERVICE_IMPL
    if (java_class.class_type == "CLASS" and
        "Service" in java_class.annotations and 
        (java_class.implements_list or java_class.name.endswith("ServiceImpl"))):
        return "SERVICE_IMPL"

    # 2. CONTROLLER
    if (java_class.class_type == "CLASS" and
        ("RestController" in java_class.annotations or "Controller" in java_class.annotations)):
        return "CONTROLLER"

    # 3. REPOSITORY
    if (java_class.class_type == "INTERFACE" and
        (java_class.name.endswith("Repository") or any("Repository" in ext for ext in java_class.extends_list))):
        return "REPOSITORY"

    # 4. MAPPER
    if (java_class.class_type == "CLASS" and
        "Component" in java_class.annotations and
        java_class.name.endswith("Mapper")):
        return "MAPPER"

    return None


# ── Extraction ──────────────────────────────────────────────────────────────

def _extract_mocks(java_class: JavaClass, test_type: str) -> List[MockField]:
    """
    Identifies dependencies that should be mocked in the test class.
    """
    mocks = []
    if test_type == "SERVICE_IMPL":
        for field in java_class.fields:
            if field.is_injected:
                mocks.append(MockField(name=field.name, type=field.type_simple, mock_type="Mock"))
    
    elif test_type == "CONTROLLER":
        for field in java_class.fields:
            if field.type_simple.endswith("Service"):
                mocks.append(MockField(name=field.name, type=field.type_simple, mock_type="MockBean"))
                
    return mocks


def _build_setup_data(java_class: JavaClass, test_type: str, pom_features: PomFeatures) -> List[TestData]:
    """
    Generates test data for @BeforeEach based on entity name.
    """
    setup_data = []
    # Extract entity name from class name
    entity_name = java_class.name
    for suffix in ["ServiceImpl", "Service", "Controller", "Repository", "Mapper"]:
        if entity_name.endswith(suffix):
            entity_name = entity_name[:-len(suffix)]
            break
    
    if not entity_name:
        return []

    var_name = entity_name[0].lower() + entity_name[1:]
    
    # Basic fields for builder/constructor
    builder_fields = [("id", JAVA_TEST_VALUES["Long"])]
    
    setup_data.append(TestData(
        variable_name=var_name,
        type=entity_name,
        builder_fields=builder_fields
    ))
    
    return setup_data


# ── Method Generation ───────────────────────────────────────────────────────

def _build_test_methods(java_class: JavaClass, test_type: str, 
                        mock_fields: List[MockField], 
                        setup_data: List[TestData]) -> List[TestMethod]:
    """
    Generates specific test scenarios for each public method of the class.
    """
    methods = []
    entity_var = setup_data[0].variable_name if setup_data else "entity"
    entity_type = setup_data[0].type if setup_data else "Entity"
    
    # Try to find a repository mock for Service tests
    repo_mock = next((m.name for m in mock_fields if "Repository" in m.type), "repository")
    # Try to find a service mock for Controller tests
    service_mock = next((m.name for m in mock_fields if "Service" in m.type), "service")

    for jm in java_class.methods:
        if not jm.is_public or jm.is_static:
            continue

        # ── SERVICE_IMPL Scenarios ──────────────────────────────────────────
        if test_type == "SERVICE_IMPL":
            if jm.name in ["findAll", "getAll"]:
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnList_whenCalled",
                    method_under_test=jm.name,
                    scenario="happy_path",
                    given_mocks=[f"when({repo_mock}.findAll()).thenReturn(List.of({entity_var}));"],
                    act_line=f"var result = {java_class.name[0].lower() + java_class.name[1:]}.{jm.name}();",
                    assert_lines=["assertThat(result).hasSize(1);", f"assertThat(result.get(0)).isEqualTo({entity_var});"],
                    verify_lines=[f"verify({repo_mock}).findAll();"]
                ))
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnEmptyList_whenNoData",
                    method_under_test=jm.name,
                    scenario="empty_list",
                    given_mocks=[f"when({repo_mock}.findAll()).thenReturn(List.of());"],
                    act_line=f"var result = {java_class.name[0].lower() + java_class.name[1:]}.{jm.name}();",
                    assert_lines=["assertThat(result).isEmpty();"],
                    verify_lines=[]
                ))

            elif jm.name in ["findById", "getById"]:
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnObject_whenExists",
                    method_under_test=jm.name,
                    scenario="happy_path",
                    given_mocks=[f"when({repo_mock}.findById(1L)).thenReturn(Optional.of({entity_var}));"],
                    act_line=f"var result = {java_class.name[0].lower() + java_class.name[1:]}.{jm.name}(1L);",
                    assert_lines=["assertThat(result).isNotNull();"],
                    verify_lines=[]
                ))
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldThrowException_whenNotExists",
                    method_under_test=jm.name,
                    scenario="not_found",
                    given_mocks=["when({repo_mock}.findById(99L)).thenReturn(Optional.empty());"],
                    act_line=f"assertThatThrownBy(() -> {java_class.name[0].lower() + java_class.name[1:]}.{jm.name}(99L))",
                    assert_lines=[f"    .isInstanceOf({entity_type}NotFoundException.class);"],
                    verify_lines=[]
                ))

            elif jm.name == "delete":
                methods.append(TestMethod(
                    test_name="delete_shouldCallRepo_whenExists",
                    method_under_test="delete",
                    scenario="happy_path",
                    given_mocks=[f"when({repo_mock}.existsById(1L)).thenReturn(true);"],
                    act_line=f"{java_class.name[0].lower() + java_class.name[1:]}.delete(1L);",
                    assert_lines=["assertThatCode(() -> {}).doesNotThrowAnyException();".format(f"{java_class.name[0].lower() + java_class.name[1:]}.delete(1L)")],
                    verify_lines=[f"verify({repo_mock}).deleteById(1L);"]
                ))
                methods.append(TestMethod(
                    test_name="delete_shouldThrowException_whenNotExists",
                    method_under_test="delete",
                    scenario="not_found",
                    given_mocks=[f"when({repo_mock}.existsById(99L)).thenReturn(false);"],
                    act_line=f"assertThatThrownBy(() -> {java_class.name[0].lower() + java_class.name[1:]}.delete(99L))",
                    assert_lines=[f"    .isInstanceOf({entity_type}NotFoundException.class);"],
                    verify_lines=[]
                ))

        # ── CONTROLLER Scenarios ──────────────────────────────────────────
        elif test_type == "CONTROLLER":
            prefix = "" # Could be improved with project_config.api_prefix
            entity_plural = entity_var + "s"
            
            if jm.name in ["findAll", "getAll"]:
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnOk",
                    method_under_test=jm.name,
                    scenario="happy_path",
                    given_mocks=[f"when({service_mock}.{jm.name}()).thenReturn(List.of());"],
                    act_line=f"mockMvc.perform(get(\"{prefix}/{entity_plural}\"))",
                    assert_lines=["    .andExpect(status().isOk())", "    .andExpect(content().contentType(MediaType.APPLICATION_JSON));"],
                    verify_lines=[]
                ))
            
            elif jm.name in ["findById", "getById"]:
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnOk_whenExists",
                    method_under_test=jm.name,
                    scenario="happy_path",
                    given_mocks=[f"when({service_mock}.{jm.name}(1L)).thenReturn(new {entity_type}ResponseDTO());"],
                    act_line=f"mockMvc.perform(get(\"{prefix}/{entity_plural}/1\"))",
                    assert_lines=["    .andExpect(status().isOk());"],
                    verify_lines=[]
                ))
                methods.append(TestMethod(
                    test_name=f"{jm.name}_shouldReturnNotFound_whenNotExists",
                    method_under_test=jm.name,
                    scenario="not_found",
                    given_mocks=[f"when({service_mock}.{jm.name}(99L)).thenThrow(new {entity_type}NotFoundException(99L));"],
                    act_line=f"mockMvc.perform(get(\"{prefix}/{entity_plural}/99\"))",
                    assert_lines=["    .andExpect(status().isNotFound());"],
                    verify_lines=[]
                ))

    return methods


# ── Imports ─────────────────────────────────────────────────────────────────

def _build_imports(test_type: str, java_class: JavaClass, base_package: str) -> List[str]:
    """
    Compiles list of required imports for the test file.
    """
    imports = {
        "org.junit.jupiter.api.Test",
        "org.junit.jupiter.api.BeforeEach",
        "static org.assertj.core.api.Assertions.*"
    }

    if test_type == "SERVICE_IMPL":
        imports.update([
            "org.junit.jupiter.api.extension.ExtendWith",
            "org.mockito.junit.jupiter.MockitoExtension",
            "org.mockito.Mock",
            "org.mockito.InjectMocks",
            "static org.mockito.Mockito.*",
            "java.util.Optional",
            "java.util.List"
        ])
    
    elif test_type == "CONTROLLER":
        imports.update([
            "org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest",
            "org.springframework.boot.test.mock.mockito.MockBean",
            "org.springframework.beans.factory.annotation.Autowired",
            "org.springframework.test.web.servlet.MockMvc",
            "com.fasterxml.jackson.databind.ObjectMapper",
            "static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*",
            "static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*",
            "org.springframework.http.MediaType",
            "static org.mockito.Mockito.*",
            "java.util.List"
        ])

    elif test_type == "REPOSITORY":
        imports.update([
            "org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest",
            "org.springframework.beans.factory.annotation.Autowired",
            "java.util.Optional",
            "java.util.List"
        ])

    # Entity-related imports
    entity_name = java_class.name
    for suffix in ["ServiceImpl", "Service", "Controller", "Repository", "Mapper"]:
        if entity_name.endswith(suffix):
            entity_name = entity_name[:-len(suffix)]
            break
            
    if entity_name:
        imports.add(f"{base_package}.models.entity.{entity_name}")
        imports.add(f"{base_package}.exception.{entity_name}NotFoundException")
        
        if test_type == "CONTROLLER":
            imports.add(f"{base_package}.dto.response.{entity_name}ResponseDTO")
            imports.add(f"{base_package}.dto.request.{entity_name}RequestDTO")
            
        for imp in java_class.imports:
            if base_package in imp:
                imports.add(imp)

    return sorted(list(imports))
