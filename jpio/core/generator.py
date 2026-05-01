"""
core/generator.py
-----------------
Prend un ProjectConfig et retourne un dictionnaire :
    { chemin_relatif_fichier: contenu_java_string }

Utilise Jinja2 pour rendre les templates .j2 en code Java.
Ne touche pas au disque — c'est le rôle de writer.py.
"""

from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape

from jpio.core.models import ProjectConfig, Entity


# ---------------------------------------------------------------------------
# Environnement Jinja2
# ---------------------------------------------------------------------------

def _make_env() -> Environment:
    """
    Crée l'environnement Jinja2 pointant vers jpio/templates/.
    PackageLoader cherche les templates dans le package installé,
    ce qui fonctionne aussi bien en développement qu'après pip install.
    """
    return Environment(
        loader=select_autoescape(
            enabled_extensions=("j2",),
            default_for_string=True,
        ),
        # On utilise FileSystemLoader en pointant vers le dossier templates
        # relatif à ce fichier pour la portabilité.
        **_loader_kwargs(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _loader_kwargs() -> dict:
    from jinja2 import FileSystemLoader
    templates_dir = Path(__file__).parent.parent / "templates"
    return {"loader": FileSystemLoader(str(templates_dir))}


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def generate_all(config: ProjectConfig) -> dict[str, str]:
    """
    Génère tous les fichiers Java pour le projet.

    Retourne :
        dict dont les clés sont les chemins relatifs depuis la racine du projet
        et les valeurs sont le contenu Java généré.

    Exemple de clé :
        "src/main/java/com/pio/ecommerce/entity/Product.java"
    """
    env    = _make_env()
    output = {}

    java_base = f"src/main/java/{config.package_path}"

    # ── Fichiers par entité ──────────────────────────────────────────────────
    for entity in config.entities:
        ctx = _entity_context(entity, config)

        templates_entity = [
            ("entity/entity.java.j2",               f"{java_base}/entity/{entity.name}.java"),
            ("entity/dto.java.j2",                   f"{java_base}/dto/{entity.name}DTO.java"),
            ("entity/mapper.java.j2",                f"{java_base}/mapper/{entity.name}Mapper.java"),
            ("entity/repository.java.j2",            f"{java_base}/repository/{entity.name}Repository.java"),
            ("entity/service.java.j2",               f"{java_base}/service/{entity.name}Service.java"),
            ("entity/service_impl.java.j2",          f"{java_base}/service/{entity.name}ServiceImpl.java"),
            ("entity/controller.java.j2",            f"{java_base}/controller/{entity.name}Controller.java"),
            ("entity/not_found_exception.java.j2",   f"{java_base}/exception/{entity.name}NotFoundException.java"),
        ]

        for template_name, dest_path in templates_entity:
            template = env.get_template(template_name)
            output[dest_path] = template.render(**ctx)

    # ── Fichiers globaux (une seule fois par projet) ─────────────────────────
    global_ctx = _global_context(config)

    global_templates = [
        ("exception/global_exception_handler.java.j2",
         f"{java_base}/exception/GlobalExceptionHandler.java"),
        ("config/swagger_config.java.j2",
         f"{java_base}/config/SwaggerConfig.java"),
    ]

    for template_name, dest_path in global_templates:
        template = env.get_template(template_name)
        output[dest_path] = template.render(**global_ctx)

    # ── application.properties (append) ────────────────────────────────────
    template = env.get_template("project/application.properties.j2")
    output["__append__:src/main/resources/application.properties"] = \
        template.render(**global_ctx)

    return output


# ---------------------------------------------------------------------------
# Contextes Jinja2
# ---------------------------------------------------------------------------

def _entity_context(entity: Entity, config: ProjectConfig) -> dict:
    """Construit le contexte Jinja2 pour les templates d'une entité."""
    return {
        "entity":       entity,
        "base_package": config.base_package,
        "api_prefix":   config.api_prefix,
        # raccourcis pratiques dans les templates
        "entity_name":  entity.name,
        "entity_lower": entity.name_lower,
        "fields":       entity.fields,
        "relations":    entity.relations,
        "extra_imports": entity.extra_imports,
    }


def _global_context(config: ProjectConfig) -> dict:
    """Construit le contexte Jinja2 pour les templates globaux."""
    return {
        "base_package": config.base_package,
        "api_prefix":   config.api_prefix,
        "entities":     config.entities,
    }