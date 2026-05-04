"""
Handles the interactive questionnaire in the terminal.
Produces a complete ProjectConfig object from user responses.
Uses questionary for prompts and Rich for display.
"""

import questionary
from pathlib import Path

from jpio.core.models import (
    ProjectConfig,
    Entity,
    Field,
    Relation,
    Enum,
    PomFeatures,
    FolderMapping,
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
# Custom questionary Style
# ---------------------------------------------------------------------------

QSTYLE = questionary.Style([
    ("qmark",        "fg:#00d7ff bold"),   # ? in cyan
    ("question",     "bold"),
    ("answer",       "fg:#00ff87 bold"),   # answer in bold green
    ("pointer",      "fg:#00d7ff bold"),   # ❯ in cyan
    ("highlighted",  "fg:#00d7ff bold"),
    ("selected",     "fg:#00ff87"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#888888 italic"),
])


# ---------------------------------------------------------------------------
# ProjectConfig Collection
# ---------------------------------------------------------------------------

def run_wizard(pom_features: PomFeatures = None, folder_mapping: FolderMapping = None) -> ProjectConfig:
    """
    Runs the complete questionnaire and returns a ProjectConfig.
    Entry point called by commands/new.py
    """
    if pom_features is None:
        pom_features = PomFeatures()
    
    if folder_mapping is None:
        folder_mapping = FolderMapping()

    base_path = Path(".")

    # ── Base Package ─────────────────────────────────────────────────────
    detected_package = detect_base_package(base_path)
    detected_name    = detect_project_name(base_path)

    if detected_package:
        print_success(f"Automatically detected package: [bold cyan]{detected_package}[/bold cyan]")
        base_package = detected_package
    else:
        print_warning("Could not automatically detect base package.")
        base_package = questionary.text(
            "Base package (e.g., com.yourname.myproject):",
            style=QSTYLE,
        ).ask()

    # ── API Prefix ─────────────────────────────────────────────────────────
    api_prefix = questionary.text(
        "API route prefix:",
        default="/api/v1",
        style=QSTYLE,
    ).ask()

    # ── Enum Collection ────────────────────────────────────────────
    enums: list[Enum] = []
    has_enums = questionary.confirm(
        "Would you like to define Enums for this project?",
        default=False,
        style=QSTYLE,
    ).ask()

    if has_enums:
        print_section("Enums")
        enums = _collect_enums()

    # ── Entity Collection ─────────────────────────────────────────────────
    entities: list[Entity] = []
    entity_names: set[str] = set()
    referenced_names: list[str] = []
    
    entity_number = 1

    while True:
        # ── Project Summary ──────────────────────────────────────────────────
        if entities or enums or referenced_names:
            print_info("Current Project State:")
            if enums:
                print_info(f"  • Enums: [bold cyan]{', '.join([e.name for e in enums])}[/bold cyan]")
            if entities:
                print_info(f"  • Entities: [bold cyan]{', '.join([e.name for e in entities])}[/bold cyan]")
            if referenced_names:
                print_info(f"  • Referenced (not yet defined): [bold yellow]{', '.join(referenced_names)}[/bold yellow]")
            print_info("")

        print_section(f"Entity {entity_number}")
        
        # If we have referenced names, suggest the first one
        default_name = referenced_names[0] if referenced_names else None
        
        entity = _collect_entity(
            entity_number, 
            list(entity_names), 
            enums, 
            suggested_name=default_name,
            referenced_names=referenced_names
        )

        if entity:
            entities.append(entity)
            entity_names.add(entity.name)
            
            # Remove from referenced if it was there
            if entity.name in referenced_names:
                referenced_names.remove(entity.name)
                
            print_success(f"Entity [bold]{entity.name}[/bold] added.")
        else:
            # Creation was cancelled or failed
            if not entities:
                retry = questionary.confirm(
                    "No entities defined yet. Would you like to try again?",
                    default=True,
                    style=QSTYLE
                ).ask()
                if not retry:
                    break
                continue
            else:
                print_info("Entity creation cancelled.")

        if referenced_names:
            print_info(f"Entities referenced but not yet defined: [bold cyan]{', '.join(referenced_names)}[/bold cyan]")
            add_another = questionary.confirm(
                f"Would you like to define {referenced_names[0]} now?",
                default=True,
                style=QSTYLE,
            ).ask()
        else:
            add_another = questionary.confirm(
                "Add another entity?",
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
        enums=enums,
        pom_features=pom_features,
        folder_mapping=folder_mapping,
    )


def run_add_wizard(existing_entity_names: list[str], existing_enums: list[Enum] = None) -> list[Entity]:
    """
    Runs the questionnaire to add entities.
    Returns a list of entities configured.
    """
    print_section("New Entities")
    entities: list[Entity] = []
    entity_names = set(existing_entity_names)
    referenced_names: list[str] = []
    
    entity_number = len(existing_entity_names) + 1

    while True:
        default_name = referenced_names[0] if referenced_names else None
        entity = _collect_entity(
            entity_number, 
            list(entity_names), 
            existing_enums, 
            suggested_name=default_name,
            referenced_names=referenced_names
        )
        
        if entity:
            entities.append(entity)
            entity_names.add(entity.name)
            if entity.name in referenced_names:
                referenced_names.remove(entity.name)
            print_success(f"Entity [bold]{entity.name}[/bold] configured.")

        if referenced_names:
            print_info(f"Entities referenced but not yet defined: [bold cyan]{', '.join(referenced_names)}[/bold cyan]")
            add_another = questionary.confirm(
                f"Would you like to define {referenced_names[0]} now?",
                default=True,
                style=QSTYLE,
            ).ask()
        else:
            add_another = questionary.confirm(
                "Add another entity?",
                default=False,
                style=QSTYLE,
            ).ask()

        if not add_another:
            break
        entity_number += 1

    return entities


# ---------------------------------------------------------------------------
# Entity Collection
# ---------------------------------------------------------------------------

def _collect_entity(
    number: int, 
    existing_entity_names: list[str], 
    enums: list[Enum] = None,
    suggested_name: str = None,
    referenced_names: list[str] = None
) -> Entity | None:
    """Collects name, fields, and relations for an entity."""

    # ── Name ─────────────────────────────────────────────────────────────────
    name = questionary.text(
        "Entity name (e.g., Product):",
        default=suggested_name or "",
        validate=lambda v: (
            "Name cannot be empty." if not v.strip()
            else "This name already exists." if v.strip() in existing_entity_names
            else True
        ),
        style=QSTYLE,
    ).ask()

    if not name:
        return None

    name = name.strip()
    name = name[0].upper() + name[1:]

    fields: list[Field] = []
    relations: list[Relation] = []

    print_info(f"Configuring entity [bold cyan]{name}[/bold cyan]")

    while True:
        action = questionary.select(
            f"What would you like to add to {name}?",
            choices=[
                "Add Field",
                "Add Relation",
                "Save Entity & Continue",
                "Discard Entity (Delete)"
            ],
            style=QSTYLE
        ).ask()

        if action == "Add Field":
            new_fields = _collect_fields(enums, start_number=len(fields) + 1)
            fields.extend(new_fields)
        
        elif action == "Add Relation":
            new_relations = _collect_relations(name, existing_entity_names, start_number=len(relations) + 1)
            relations.extend(new_relations)
            if referenced_names is not None:
                for rel in new_relations:
                    if rel.target not in existing_entity_names and rel.target not in referenced_names and rel.target != name:
                        referenced_names.append(rel.target)
            
        elif action == "Save Entity & Continue":
            if not fields and not relations:
                print_warning(f"Entity {name} has no fields and no relations.")
                if not questionary.confirm("Are you sure you want to save it as is?", default=False, style=QSTYLE).ask():
                    continue
            break
            
        elif action == "Discard Entity (Delete)":
            if questionary.confirm(f"Discard entity {name}? All its fields and relations will be lost.", default=False, style=QSTYLE).ask():
                return None
            continue

    return Entity(name=name, fields=fields, relations=relations)


# ---------------------------------------------------------------------------
# Field Collection
# ---------------------------------------------------------------------------

def _collect_fields(enums: list[Enum] = None, start_number: int = 1) -> list[Field]:
    """Collects entity fields in a loop."""
    fields: list[Field] = []
    field_number = start_number

    while True:
        field_name = questionary.text(
            f"  Field {field_number} — Name (empty to finish):",
            style=QSTYLE,
        ).ask()

        if not field_name or not field_name.strip():
            break

        field_name = field_name.strip()
        # camelCase convention: first letter lowercase
        field_name = field_name[0].lower() + field_name[1:]

        type_choices = SUPPORTED_JAVA_TYPES.copy()
        if enums:
            type_choices.extend([f"Enum: {e.name}" for e in enums])

        java_type_choice = questionary.select(
            f"  Field {field_number} — Type:",
            choices=type_choices,
            style=QSTYLE,
        ).ask()

        is_enum = False
        java_type = java_type_choice
        if java_type_choice.startswith("Enum: "):
            is_enum = True
            java_type = java_type_choice.split("Enum: ")[1]

        nullable = questionary.confirm(
            f"  Field {field_number} — Nullable?",
            default=True,
            style=QSTYLE,
        ).ask()

        fields.append(Field(name=field_name, java_type=java_type, nullable=nullable, is_enum=is_enum))
        field_number += 1

    return fields


# ---------------------------------------------------------------------------
# Enum Collection
# ---------------------------------------------------------------------------

def _collect_enums() -> list[Enum]:
    """Collects enums in a loop."""
    enums: list[Enum] = []
    enum_number = 1

    while True:
        name = questionary.text(
            f"Enum {enum_number} — Name (empty to finish):",
            style=QSTYLE,
        ).ask()

        if not name or not name.strip():
            break

        name = name.strip()
        name = name[0].upper() + name[1:]

        values_str = questionary.text(
            "  Values (comma-separated, e.g., PENDING, ACTIVE):",
            style=QSTYLE,
        ).ask()

        values = [v.strip().upper() for v in values_str.split(",") if v.strip()]
        enums.append(Enum(name=name, values=values))
        enum_number += 1

    return enums


# ---------------------------------------------------------------------------
# Relation Collection
# ---------------------------------------------------------------------------

def _collect_relations(
    entity_name: str,
    existing_entity_names: list[str],
    start_number: int = 1
) -> list[Relation]:
    """Collects entity relations in a loop."""
    relations: list[Relation] = []
    relation_number = start_number

    while True:
        print_info(f"Relation {relation_number} for {entity_name}")

        kind = questionary.select(
            "  Relation type:",
            choices=SUPPORTED_RELATIONS,
            style=QSTYLE,
        ).ask()

        # Target: existing entities + free input (new entity to come)
        target_choices = existing_entity_names + ["[ Other — enter name ]"]
        target_choice  = questionary.select(
            "  Target entity:",
            choices=target_choices,
            style=QSTYLE,
        ).ask()

        if target_choice == "[ Other — enter name ]":
            target = questionary.text(
                "  Target entity name:",
                style=QSTYLE,
            ).ask()
            target = target.strip()
            target = target[0].upper() + target[1:]
        else:
            target = target_choice

        # mapped_by: inverse side
        mapped_by = ""
        owner     = True

        if kind in ("OneToMany", "ManyToMany"):
            mapped_by = questionary.text(
                f"  Field name on {target} side referencing {entity_name} "
                f"(mappedBy):",
                default=entity_name[0].lower() + entity_name[1:] + "s",
                style=QSTYLE,
            ).ask()
            owner = questionary.confirm(
                f"  Is {entity_name} the owning side "
                f"(has the @JoinTable)?",
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
            f"Add another relation for {entity_name}?",
            default=False,
            style=QSTYLE,
        ).ask()

        if not add_another:
            break

        relation_number += 1

    return relations