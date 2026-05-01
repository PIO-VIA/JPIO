"""
core/analyzer.py
----------------
Gère le questionnaire interactif dans le terminal.
Produit un objet ProjectConfig complet à partir des réponses de l'utilisateur.
Utilise questionary pour les prompts et Rich pour l'affichage.
"""

import questionary
from pathlib import Path

from jpio.core.models import (
    ProjectConfig,
    Entity,
    Field,
    Relation,
    SUPPORTED_JAVA_TYPES,
    SUPPORTED_RELATIONS,
)
from jpio.utils.console import (
    print_section,
    print_success,
    print_info,
    print_warning,
)
from jpio.utils.file_helper import detect_base_package, detect_project_name


# ---------------------------------------------------------------------------
# Style questionary personnalisé
# ---------------------------------------------------------------------------

QSTYLE = questionary.Style([
    ("qmark",        "fg:#00d7ff bold"),   # le ? en cyan
    ("question",     "bold"),
    ("answer",       "fg:#00ff87 bold"),   # réponse en vert
    ("pointer",      "fg:#00d7ff bold"),   # ❯ en cyan
    ("highlighted",  "fg:#00d7ff bold"),
    ("selected",     "fg:#00ff87"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#888888 italic"),
])


# ---------------------------------------------------------------------------
# Collecte du ProjectConfig
# ---------------------------------------------------------------------------

def run_wizard() -> ProjectConfig:
    """
    Lance le questionnaire complet et retourne un ProjectConfig.
    Point d'entrée appelé par commands/new.py
    """
    base_path = Path(".")

    # ── Package de base ─────────────────────────────────────────────────────
    detected_package = detect_base_package(base_path)
    detected_name    = detect_project_name(base_path)

    if detected_package:
        print_success(f"Package détecté automatiquement : [bold cyan]{detected_package}[/bold cyan]")
        base_package = detected_package
    else:
        print_warning("Package de base non détecté automatiquement.")
        base_package = questionary.text(
            "Package de base (ex: com.yourname.monprojet) :",
            style=QSTYLE,
        ).ask()

    # ── Préfixe API ─────────────────────────────────────────────────────────
    api_prefix = questionary.text(
        "Préfixe des routes API :",
        default="/api/v1",
        style=QSTYLE,
    ).ask()

    # ── Collecte des entités ─────────────────────────────────────────────────
    entities: list[Entity] = []
    entity_number = 1

    while True:
        print_section(f"Entité {entity_number}")
        entity = _collect_entity(entity_number, [e.name for e in entities])

        if entity:
            entities.append(entity)
            print_success(f"Entité [bold]{entity.name}[/bold] ajoutée.")

        add_another = questionary.confirm(
            "Ajouter une autre entité ?",
            default=True,
            style=QSTYLE,
        ).ask()

        if not add_another:
            break

        entity_number += 1

    return ProjectConfig(
        base_package=base_package,
        api_prefix=api_prefix,
        entities=entities,
    )


# ---------------------------------------------------------------------------
# Collecte d'une entité
# ---------------------------------------------------------------------------

def _collect_entity(number: int, existing_entity_names: list[str]) -> Entity | None:
    """Collecte le nom, les champs et les relations d'une entité."""

    # ── Nom ─────────────────────────────────────────────────────────────────
    name = questionary.text(
        "Nom de l'entité (ex: Product) :",
        validate=lambda v: (
            "Le nom ne peut pas être vide." if not v.strip()
            else "Ce nom existe déjà." if v.strip() in existing_entity_names
            else True
        ),
        style=QSTYLE,
    ).ask()

    if not name:
        return None

    name = name.strip()
    name = name[0].upper() + name[1:]

    # ── Champs ───────────────────────────────────────────────────────────────
    print_info("Ajoutez les champs de l'entité (laissez le nom vide pour terminer).")
    fields = _collect_fields()

    # ── Relations ────────────────────────────────────────────────────────────
    relations: list[Relation] = []
    has_relations = questionary.confirm(
        f"L'entité {name} a-t-elle des relations avec d'autres entités ?",
        default=False,
        style=QSTYLE,
    ).ask()

    if has_relations:
        relations = _collect_relations(name, existing_entity_names)

    return Entity(name=name, fields=fields, relations=relations)


# ---------------------------------------------------------------------------
# Collecte des champs
# ---------------------------------------------------------------------------

def _collect_fields() -> list[Field]:
    """Collecte les champs d'une entité en boucle."""
    fields: list[Field] = []
    field_number = 1

    while True:
        field_name = questionary.text(
            f"  Champ {field_number} — Nom (vide pour terminer) :",
            style=QSTYLE,
        ).ask()

        if not field_name or not field_name.strip():
            break

        field_name = field_name.strip()
        # convention camelCase : première lettre minuscule
        field_name = field_name[0].lower() + field_name[1:]

        java_type = questionary.select(
            f"  Champ {field_number} — Type :",
            choices=SUPPORTED_JAVA_TYPES,
            style=QSTYLE,
        ).ask()

        nullable = questionary.confirm(
            f"  Champ {field_number} — Nullable ?",
            default=True,
            style=QSTYLE,
        ).ask()

        fields.append(Field(name=field_name, java_type=java_type, nullable=nullable))
        field_number += 1

    return fields


# ---------------------------------------------------------------------------
# Collecte des relations
# ---------------------------------------------------------------------------

def _collect_relations(
    entity_name: str,
    existing_entity_names: list[str],
) -> list[Relation]:
    """Collecte les relations d'une entité en boucle."""
    relations: list[Relation] = []
    relation_number = 1

    while True:
        print_info(f"Relation {relation_number} pour {entity_name}")

        kind = questionary.select(
            "  Type de relation :",
            choices=SUPPORTED_RELATIONS,
            style=QSTYLE,
        ).ask()

        # Cible : entités existantes + saisie libre (nouvelle entité à venir)
        target_choices = existing_entity_names + ["[ Autre — saisir le nom ]"]
        target_choice  = questionary.select(
            "  Entité cible :",
            choices=target_choices,
            style=QSTYLE,
        ).ask()

        if target_choice == "[ Autre — saisir le nom ]":
            target = questionary.text(
                "  Nom de l'entité cible :",
                style=QSTYLE,
            ).ask()
            target = target.strip()
            target = target[0].upper() + target[1:]
        else:
            target = target_choice

        # mapped_by : côté inverse
        mapped_by = ""
        owner     = True

        if kind in ("OneToMany", "ManyToMany"):
            mapped_by = questionary.text(
                f"  Nom du champ côté {target} qui référence {entity_name} "
                f"(mappedBy) :",
                default=entity_name[0].lower() + entity_name[1:] + "s",
                style=QSTYLE,
            ).ask()
            owner = questionary.confirm(
                f"  {entity_name} est-elle le côté propriétaire "
                f"(possède la @JoinTable) ?",
                default=True,
                style=QSTYLE,
            ).ask()

        relations.append(Relation(
            kind=kind,
            target=target,
            mapped_by=mapped_by,
            owner=owner,
        ))

        add_another = questionary.confirm(
            f"Ajouter une autre relation pour {entity_name} ?",
            default=False,
            style=QSTYLE,
        ).ask()

        if not add_another:
            break

        relation_number += 1

    return relations