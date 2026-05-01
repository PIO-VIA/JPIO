"""
Takes a ProjectConfig and returns a dictionary:
    { relative_file_path: java_content_string }

Uses Jinja2 to render .j2 templates into Java code.
Does not touch the disk — that is the role of writer.py.
"""

from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape

from jpio.core.models import ProjectConfig, Entity, PomFeatures


# ---------------------------------------------------------------------------
# Jinja2 Environment
# ---------------------------------------------------------------------------

def _make_env() -> Environment:
    """
    Creates the Jinja2 environment pointing to jpio/templates/.
    PackageLoader looks for templates in the installed package,
    which works both in development and after pip install.
    """
    return Environment(
        autoescape=select_autoescape(
            enabled_extensions=("j2",),
            default_for_string=True,
        ),
        # We use FileSystemLoader pointing to the templates folder
        # relative to this file for portability.
        **_loader_kwargs(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _loader_kwargs() -> dict:
    from jinja2 import FileSystemLoader
    templates_dir = Path(__file__).parent.parent / "templates"
    return {"loader": FileSystemLoader(str(templates_dir))}


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def generate_all(config: ProjectConfig, base_path: Path = Path(".")) -> dict[str, str]:
    """
    Generates all Java files for the project.

    Returns:
        dict where keys are relative paths from project root
        and values are the generated Java content.

    Key example:
        "src/main/java/com/pio/ecommerce/models/entity/Product.java"
    """
    from jpio.utils.file_helper import detect_config_format

    env    = _make_env()
    output = {}

    java_base = f"src/main/java/{config.package_path}"

    # Detect config format for Swagger
    config_format, config_path = detect_config_format(base_path)
    rel_config_path = str(config_path.relative_to(base_path)) if base_path != Path(".") else str(config_path)

    # ── Entity Files ──────────────────────────────────────────────────
    for entity in config.entities:
        output.update(_generate_entity_files(env, config, entity, java_base))

    # ── Enums ─────────────────────────────────────────────────────────
    for enum_obj in config.enums:
        output.update(_generate_enum_file(env, config, enum_obj, java_base))

    # ── Global Files (once per project) ─────────────────────────
    global_ctx = _global_context(config)

    global_templates = [
        ("exception/global_exception_handler.java.j2",
         f"{java_base}/{config.folder_mapping.exception}/GlobalExceptionHandler.java")
    ]
    
    if config.pom_features.has_swagger:
        global_templates.append(
            ("config/swagger_config.java.j2",
             f"{java_base}/{config.folder_mapping.config}/SwaggerConfig.java")
        )

    for template_name, dest_path in global_templates:
        template = env.get_template(template_name)
        output[dest_path] = template.render(**global_ctx)

    # ── application.properties / yaml (append) ──────────────────────────────
    if config.pom_features.has_swagger:
        if config_format == "properties":
            template = env.get_template("project/application.properties.j2")
        else:
            template = env.get_template("project/application.yaml.j2")
            
        output[f"__append__:{rel_config_path}"] = template.render(**global_ctx)

    return output


def _generate_enum_file(env: Environment, config: ProjectConfig, enum_obj, java_base: str) -> dict[str, str]:
    template = env.get_template("entity/enum.java.j2")
    # Infer enum folder from entity folder (e.g., models/entity -> models/enum)
    enum_folder = config.folder_mapping.entity.replace("entity", "enum").replace("entities", "enums")
    if enum_folder == config.folder_mapping.entity:
        enum_folder = "enum"
        
    dest_path = f"{java_base}/{enum_folder}/{enum_obj.name}.java"
    ctx = {
        "base_package": config.base_package,
        "enum": enum_obj
    }
    return {dest_path: template.render(**ctx)}


def _generate_entity_files(env: Environment, config: ProjectConfig, entity: Entity, java_base: str) -> dict[str, str]:
    output = {}
    ctx = _entity_context(entity, config)

    templates_entity = [
        ("entity/entity.java.j2",               f"{java_base}/{config.folder_mapping.entity}/{entity.name}.java"),
        ("entity/request_dto.java.j2",          f"{java_base}/{config.folder_mapping.dto}/request/{entity.name}RequestDTO.java"),
        ("entity/response_dto.java.j2",         f"{java_base}/{config.folder_mapping.dto}/response/{entity.name}ResponseDTO.java"),
        ("entity/mapper.java.j2",                f"{java_base}/{config.folder_mapping.mapper}/{entity.name}Mapper.java"),
        ("entity/repository.java.j2",            f"{java_base}/{config.folder_mapping.repository}/{entity.name}Repository.java"),
        ("entity/service.java.j2",               f"{java_base}/{config.folder_mapping.service}/{entity.name}Service.java"),
        ("entity/service_impl.java.j2",          f"{java_base}/{config.folder_mapping.service}/{entity.name}ServiceImpl.java"),
        ("entity/controller.java.j2",            f"{java_base}/{config.folder_mapping.controller}/{entity.name}Controller.java"),
        ("entity/not_found_exception.java.j2",   f"{java_base}/{config.folder_mapping.exception}/{entity.name}NotFoundException.java"),
    ]

    for template_name, dest_path in templates_entity:
        template = env.get_template(template_name)
        output[dest_path] = template.render(**ctx)

    return output


def generate_single_entity(config: ProjectConfig, entity: Entity) -> dict[str, str]:
    """
    Generates Java files for a single entity (without global configurations).
    """
    env = _make_env()
    java_base = f"src/main/java/{config.package_path}"
    return _generate_entity_files(env, config, entity, java_base)


# ---------------------------------------------------------------------------
# Jinja2 Contexts
# ---------------------------------------------------------------------------

def _entity_context(entity: Entity, config: ProjectConfig) -> dict:
    """Builds the Jinja2 context for an entity's templates."""
    return {
        "entity":       entity,
        "base_package": config.base_package,
        "api_prefix":   config.api_prefix,
        "pom_features": config.pom_features,
        # practical shortcuts in templates
        "entity_name":  entity.name,
        "entity_lower": entity.name_lower,
        "fields":       entity.fields,
        "relations":    entity.relations,
        "extra_imports": entity.extra_imports,
    }


def _global_context(config: ProjectConfig) -> dict:
    """Builds the Jinja2 context for global templates."""
    return {
        "base_package": config.base_package,
        "api_prefix":   config.api_prefix,
        "entities":     config.entities,
        "pom_features": config.pom_features,
    }