"""
Unit tests for core/security_generator.py.
"""

import pytest
from pathlib import Path
from jpio.core.models import ProjectConfig, SecurityConfig, Field, PomFeatures
from jpio.core.security_generator import generate_security
from jpio.utils.file_helper import inject_security_dependencies

@pytest.fixture
def base_config():
    return ProjectConfig(
        base_package="com.example.test",
        api_prefix="/api/v1",
        pom_features=PomFeatures(has_lombok=True, has_jpa=True)
    )

@pytest.fixture
def security_config_new_user():
    return SecurityConfig(
        username_field="email",
        jwt_secret="super-secret-key-at-least-32-chars-long",
        jwt_expiration_hours=24,
        public_routes=["/api/v1/public/**"],
        existing_user_entity="",
        extra_user_fields=[Field(name="fullName", java_type="String")]
    )

@pytest.fixture
def security_config_existing_user():
    return SecurityConfig(
        username_field="username",
        jwt_secret="super-secret-key-at-least-32-chars-long",
        jwt_expiration_hours=12,
        existing_user_entity="Account"
    )

def test_generate_security_new_user(base_config, security_config_new_user):
    """Verifies that all files are generated for a new User entity."""
    output = generate_security(base_config, security_config_new_user)
    
    java_base = "src/main/java/com/example/test"
    
    expected_files = [
        f"{java_base}/config/SecurityConfig.java",
        f"{java_base}/security/JwtUtil.java",
        f"{java_base}/security/JwtAuthenticationFilter.java",
        f"{java_base}/security/UserDetailsServiceImpl.java",
        f"{java_base}/controller/AuthController.java",
        f"{java_base}/dto/request/LoginRequestDTO.java",
        f"{java_base}/dto/request/RegisterRequestDTO.java",
        f"{java_base}/dto/response/AuthResponseDTO.java",
        f"{java_base}/models/entity/User.java",
        f"{java_base}/models/enum/Role.java",
        f"{java_base}/repository/UserRepository.java",
        "__append__:src/main/resources/application.properties"
    ]
    
    for f in expected_files:
        assert f in output
        assert len(output[f]) > 0

def test_generate_security_existing_user(base_config, security_config_existing_user):
    """Verifies that User-related files are NOT generated if existing_user_entity is set."""
    output = generate_security(base_config, security_config_existing_user)
    
    java_base = "src/main/java/com/example/test"
    
    # These should NOT be there
    assert f"{java_base}/models/entity/User.java" not in output
    assert f"{java_base}/repository/UserRepository.java" not in output
    
    # These should still be there
    assert f"{java_base}/config/SecurityConfig.java" in output
    assert f"{java_base}/security/JwtUtil.java" in output

def test_security_config_contains_routes(base_config, security_config_new_user):
    """Verifies that SecurityConfig.java contains public routes."""
    output = generate_security(base_config, security_config_new_user)
    content = output["src/main/java/com/example/test/config/SecurityConfig.java"]
    
    assert "/auth/**" in content
    assert "/swagger-ui/**" in content
    assert "/api/v1/public/**" in content

def test_jwt_util_contains_value_annotations(base_config, security_config_new_user):
    """Verifies that JwtUtil.java contains @Value annotations."""
    output = generate_security(base_config, security_config_new_user)
    content = output["src/main/java/com/example/test/security/JwtUtil.java"]
    
    assert "@Value(\"${jwt.secret}\")" in content
    assert "@Value(\"${jwt.expiration}\")" in content

def test_user_entity_implements_userdetails(base_config, security_config_new_user):
    """Verifies that User.java implements UserDetails."""
    output = generate_security(base_config, security_config_new_user)
    content = output["src/main/java/com/example/test/models/entity/User.java"]
    
    assert "public class User implements UserDetails" in content
    assert "public String getUsername()" in content
    assert "return email;" in content  # because username_field is "email"

def test_inject_security_dependencies(tmp_path):
    """Verifies that pom.xml is updated correctly."""
    pom = tmp_path / "pom.xml"
    pom.write_text("<project>\n  <dependencies>\n    <dependency>\n      <artifactId>something</artifactId>\n    </dependency>\n  </dependencies>\n</project>")
    
    success = inject_security_dependencies(tmp_path)
    assert success
    
    content = pom.read_text()
    assert "spring-boot-starter-security" in content
    assert "jjwt-api" in content
    assert "jjwt-impl" in content
    assert "jjwt-jackson" in content
    assert content.count("<dependency>") == 5

def test_inject_security_dependencies_idempotent(tmp_path):
    """Verifies that dependencies are not duplicated."""
    pom = tmp_path / "pom.xml"
    pom.write_text("<project>\n  <dependencies>\n    <dependency>\n      <artifactId>spring-boot-starter-security</artifactId>\n    </dependency>\n  </dependencies>\n</project>")
    
    success = inject_security_dependencies(tmp_path)
    assert not success # Already present
    
    content = pom.read_text()
    assert content.count("spring-boot-starter-security") == 1
