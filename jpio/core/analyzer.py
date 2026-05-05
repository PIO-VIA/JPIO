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

from jpio.utils.console import console

class UserAbortedError(Exception):
    """Levée quand l'utilisateur annule le wizard."""
    pass

def _ask(prompt):
    answer = prompt.ask()
    if answer is None:
        raise UserAbortedError()
    return answer



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
        base_package = _ask(questionary.text(
            "Base package (e.g., com.yourname.myproject):",
            style=QSTYLE,
        ))

    # ── API Prefix ─────────────────────────────────────────────────────────
    api_prefix = _ask(questionary.text(
        "API route prefix:",
        default="/api/v1",
        style=QSTYLE,
    ))

    # ── Enum Collection ────────────────────────────────────────────
    enums: list[Enum] = []
    has_enums = _ask(questionary.confirm(
        "Would you like to define Enums for this project?",
        default=False,
        style=QSTYLE,
    ))

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
                retry = _ask(questionary.confirm(
                    "No entities defined yet. Would you like to try again?",
                    default=True,
                    style=QSTYLE
                ))
                if not retry:
                    break
                continue
            else:
                print_info("Entity creation cancelled.")

        if referenced_names:
            print_info(f"Entities referenced but not yet defined: [bold cyan]{', '.join(referenced_names)}[/bold cyan]")
            add_another = _ask(questionary.confirm(
                f"Would you like to define {referenced_names[0]} now?",
                default=True,
                style=QSTYLE,
            ))
        else:
            add_another = _ask(questionary.confirm(
                "Add another entity?",
                default=True,
                style=QSTYLE,
            ))

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
    try:
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
                add_another = _ask(questionary.confirm(
                    f"Would you like to define {referenced_names[0]} now?",
                    default=True,
                    style=QSTYLE,
                ))
            else:
                add_another = _ask(questionary.confirm(
                    "Add another entity?",
                    default=False,
                    style=QSTYLE,
                ))

            if not add_another:
                break
            entity_number += 1

        return entities

    except UserAbortedError:
        console.print(
            "\n  [bold yellow]⚠[/bold yellow]  "
            "Wizard annulé par l'utilisateur.\n"
        )
        raise SystemExit(0)

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
    name = _ask(questionary.text(
        "Entity name (e.g., Product):",
        default=suggested_name or "",
        validate=lambda v: (
            "Name cannot be empty." if not v.strip()
            else "This name already exists." if v.strip() in existing_entity_names
            else True
        ),
        style=QSTYLE,
    ))

    if not name:
        return None

    name = name.strip()
    name = name[0].upper() + name[1:]

    fields: list[Field] = []
    relations: list[Relation] = []

    print_info(f"Configuring entity [bold cyan]{name}[/bold cyan]")

    while True:
        action = _ask(questionary.select(
            f"What would you like to add to {name}?",
            choices=[
                "Add Field",
                "Add Relation",
                "Save Entity & Continue",
                "Discard Entity (Delete)"
            ],
            style=QSTYLE
        ))

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
                if not _ask(questionary.confirm("Are you sure you want to save it as is?", default=False, style=QSTYLE)):
                    continue
            break
            
        elif action == "Discard Entity (Delete)":
            if _ask(questionary.confirm(f"Discard entity {name}? All its fields and relations will be lost.", default=False, style=QSTYLE)):
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
        field_name = _ask(questionary.text(
            f"  Field {field_number} — Name (empty to finish):",
            style=QSTYLE,
        ))

        if not field_name or not field_name.strip():
            break

        field_name = field_name.strip()
        # camelCase convention: first letter lowercase
        field_name = field_name[0].lower() + field_name[1:]

        type_choices = SUPPORTED_JAVA_TYPES.copy()
        if enums:
            type_choices.extend([f"Enum: {e.name}" for e in enums])

        java_type_choice = _ask(questionary.select(
            f"  Field {field_number} — Type:",
            choices=type_choices,
            style=QSTYLE,
        ))

        is_enum = False
        java_type = java_type_choice
        if java_type_choice.startswith("Enum: "):
            is_enum = True
            java_type = java_type_choice.split("Enum: ")[1]

        nullable = _ask(questionary.confirm(
            f"  Field {field_number} — Nullable?",
            default=True,
            style=QSTYLE,
        ))

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
        name = _ask(questionary.text(
            f"Enum {enum_number} — Name (empty to finish):",
            style=QSTYLE,
        ))

        if not name or not name.strip():
            break

        name = name.strip()
        name = name[0].upper() + name[1:]

        values_str = _ask(questionary.text(
            "  Values (comma-separated, e.g., PENDING, ACTIVE):",
            style=QSTYLE,
        ))

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

        kind = _ask(questionary.select(
            "  Relation type:",
            choices=SUPPORTED_RELATIONS,
            style=QSTYLE,
        ))

        # Target: existing entities + free input (new entity to come)
        target_choices = existing_entity_names + ["[ Other — enter name ]"]
        target_choice  = _ask(questionary.select(
            "  Target entity:",
            choices=target_choices,
            style=QSTYLE,
        ))

        if target_choice == "[ Other — enter name ]":
            target = _ask(questionary.text(
                "  Target entity name:",
                style=QSTYLE,
            ))
            target = target.strip()
            target = target[0].upper() + target[1:]
        else:
            target = target_choice

        # mapped_by: inverse side
        mapped_by = ""
        owner     = True

        if kind in ("OneToMany", "ManyToMany"):
            mapped_by = _ask(questionary.text(
                f"  Field name on {target} side referencing {entity_name} "
                f"(mappedBy):",
                default=entity_name[0].lower() + entity_name[1:] + "s",
                style=QSTYLE,
            ))
            owner = _ask(questionary.confirm(
                f"  Is {entity_name} the owning side "
                f"(has the @JoinTable)?",
                default=True,
                style=QSTYLE,
            ))

        relations.append(Relation(
            kind=kind,
            target=target,
            mapped_by=mapped_by,
            owner=owner,
        ))

        add_another = _ask(questionary.confirm(
            f"Add another relation for {entity_name}?",
            default=False,
            style=QSTYLE,
        ))

        if not add_another:
            break

        relation_number += 1

    return relations