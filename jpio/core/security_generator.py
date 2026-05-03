"""
Generates Java security files and configuration appends.
"""

from pathlib import Path
from jpio.core.models import ProjectConfig, SecurityConfig
from jpio.core.generator import _make_env
from jpio.utils.file_helper import detect_config_format

def generate_security(config: ProjectConfig, security_config: SecurityConfig) -> dict[str, str]:
    """
    Generates all security-related files.
    """
    env = _make_env()
    output = {}
    
    java_base = f"src/main/java/{config.package_path}"
    
    user_entity = security_config.existing_user_entity or "User"
    user_repository = f"{user_entity}Repository"
    user_repo_var = user_repository[0].lower() + user_repository[1:]

    generate_user = not security_config.existing_user_entity

    ctx = {
        "base_package": config.base_package,
        "api_prefix": config.api_prefix,
        "security_config": security_config,
        "pom_features": config.pom_features,
        "username_field_capitalized": security_config.username_field[0].upper() + security_config.username_field[1:],
        "user_entity": user_entity,
        "user_repository": user_repository,
        "user_repo_var": user_repo_var,
        "generate_user": generate_user
    }
    
    security_templates = [
        ("security/security_config.java.j2",           f"{java_base}/config/SecurityConfig.java"),
        ("security/jwt_util.java.j2",                   f"{java_base}/security/JwtUtil.java"),
        ("security/jwt_authentication_filter.java.j2",  f"{java_base}/security/JwtAuthenticationFilter.java"),
        ("security/user_details_service_impl.java.j2", f"{java_base}/security/UserDetailsServiceImpl.java"),
        ("security/auth_controller.java.j2",           f"{java_base}/controller/AuthController.java"),
        ("security/login_request_dto.java.j2",         f"{java_base}/dto/request/LoginRequestDTO.java"),
        ("security/register_request_dto.java.j2",      f"{java_base}/dto/request/RegisterRequestDTO.java"),
        ("security/auth_response_dto.java.j2",         f"{java_base}/dto/response/AuthResponseDTO.java"),
    ]
    
    # If no existing user entity, generate User.java, Role.java, and UserRepository.java
    if not security_config.existing_user_entity:
        security_templates.extend([
            ("security/user_entity.java.j2",     f"{java_base}/models/entity/User.java"),
            ("security/role_enum.java.j2",       f"{java_base}/models/enum/Role.java"),
            ("security/user_repository.java.j2", f"{java_base}/repository/UserRepository.java"),
        ])
        
    for template_name, dest_path in security_templates:
        template = env.get_template(template_name)
        output[dest_path] = template.render(**ctx)
        
    # Appends for application config
    config_format, _ = detect_config_format(Path("."))
    if config_format == "properties":
        template = env.get_template("security/jwt.properties.j2")
        output[f"__append__:src/main/resources/application.properties"] = template.render(**ctx)
    else:
        template = env.get_template("security/jwt.yaml.j2")
        output[f"__append__:src/main/resources/application.yaml"] = template.render(**ctx)
        
    return output
