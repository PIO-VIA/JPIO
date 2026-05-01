# JPIO — Java Project Input/Output

> **A CLI tool that scaffolds production-ready Spring Boot projects in seconds.**
> Stop writing boilerplate. Start building features.

---

## Table of Contents

- [Overview](#overview)
- [Why JPIO?](#why-jpio)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Project Architecture](#project-architecture)
- [Generated Structure](#generated-structure)
- [Supported Relations](#supported-relations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Overview

**JPIO** (Java Project Input/Output) is an open-source Python CLI that automates the creation of Spring Boot project scaffolding. You describe your entities and their relationships interactively in the terminal — JPIO generates all the layers: Entity, DTO, Mapper, Repository, Service, ServiceImpl, Controller, and Exceptions.

Built for developers who are tired of copy-pasting the same boilerplate across every new project.

---

## Why JPIO?

Every Spring Boot project starts the same way:

```
mkdir config controller entity dto mapper repository service exception
```

Then you write the same `JpaRepository` interfaces, the same CRUD controllers, the same `GlobalExceptionHandler`, the same `SwaggerConfig`... over and over again.

**JPIO eliminates that entirely.**

| Without JPIO | With JPIO |
|---|---|
| ~30–60 min of boilerplate setup | ~2 minutes |
| Manual folder creation | Auto-generated structure |
| Copy-paste error-prone | Template-driven, consistent |
| Forgotten files | Nothing is missed |

---

## Installation

```bash
pip install jpio-cli
```

**Requirements:**
- Python 3.9+
- pip

---

## Quick Start

```bash
# Create a new Spring Boot project
jpio new

# Follow the interactive prompts:
# ? Project name     : ecommerce-api
# ? Base package     : com.yourname.ecommerce
# ? Database         : MySQL
#
# --- Entity 1 ---
# ? Entity name      : Product
# ? Fields           : name (String), price (Double), stock (Integer)
# ? Has relations?   : Yes → ManyToMany → Category
#
# --- Entity 2 ---
# ? Entity name      : Category
# ? Fields           : name (String)
#
# ? Add another entity? No
#
# ✅ Project generated in ./ecommerce-api/
```

---

## Commands

| Command | Description |
|---|---|
| `jpio new` | Create a new Spring Boot project interactively |
| `jpio add` | Add a new entity to an existing JPIO project |
| `jpio scan` | Display the current state of a JPIO project |

### `jpio new`
Launches the full interactive wizard. Asks for project metadata (name, package, database), then collects entities and their fields and relations. Generates the complete project structure.

### `jpio add`
Run inside an existing JPIO project. Prompts for a new entity and appends the generated files without touching existing code. Reads `.jpio.json` to stay aware of existing entities.

### `jpio scan`
Reads `.jpio.json` and displays a summary table of the project: entities, fields, relations, and generated files.

---

## Project Architecture

This section describes the internal architecture of JPIO itself (the CLI tool).

```
jpio/
├── jpio/
│   ├── main.py                        # CLI entry point (Click)
│   ├── commands/
│   │   ├── new.py                     # `jpio new` — full project wizard
│   │   ├── add_entity.py              # `jpio add` — add entity to existing project
│   │   └── scan.py                    # `jpio scan` — display project state
│   ├── core/
│   │   ├── models.py                  # Dataclasses: Field, Relation, Entity, ProjectConfig
│   │   ├── analyzer.py                # Interactive prompts → builds ProjectConfig
│   │   ├── generator.py               # ProjectConfig → Jinja2 render → Java code strings
│   │   └── writer.py                  # Java code strings → files on disk
│   ├── utils/
│   │   ├── console.py                 # Rich: colors, spinners, tables, success/error output
│   │   └── file_helper.py             # Path manipulation, mkdir, safe file operations
│   └── templates/
│       ├── entity/
│       │   ├── entity.java.j2                  # JPA Entity class
│       │   ├── dto.java.j2                     # Data Transfer Object
│       │   ├── mapper.java.j2                  # DTO <-> Entity mapper
│       │   ├── repository.java.j2              # Spring Data JPA repository
│       │   ├── service.java.j2                 # Service interface
│       │   ├── service_impl.java.j2            # Service implementation
│       │   ├── controller.java.j2              # REST controller (CRUD)
│       │   └── not_found_exception.java.j2     # EntityNotFoundException
│       ├── exception/
│       │   └── global_exception_handler.java.j2  # @ControllerAdvice handler
│       ├── config/
│       │   └── swagger_config.java.j2          # SpringDoc OpenAPI config
│       └── project/
│           ├── pom.xml.j2                      # Maven dependencies
│           └── application.properties.j2       # Spring Boot config
├── tests/
│   ├── test_analyzer.py
│   ├── test_generator.py
│   └── test_writer.py
├── pyproject.toml
├── README.md
└── .jpio.json                         # Project snapshot (entities, relations, config)
```

### Data Flow

```
jpio new
   │
   ▼
analyzer.py       ← interactive prompts (questionary)
   │ returns ProjectConfig
   ▼
generator.py      ← Jinja2 renders templates
   │ returns { filepath: java_code_string }
   ▼
writer.py         ← creates directories and files on disk
   │
   ▼
console.py        ← prints success report
   │
   ▼
.jpio.json        ← saves project snapshot for future `add` and `scan`
```

### Core Models (`core/models.py`)

```python
@dataclass
class Field:
    name: str          # e.g. "price"
    type: str          # e.g. "Double"
    nullable: bool

@dataclass
class Relation:
    kind: str          # "OneToMany" | "ManyToMany" | "ManyToOne"
    target: str        # e.g. "Category"
    mapped_by: str     # owning side field name

@dataclass
class Entity:
    name: str          # e.g. "Product"
    fields: list[Field]
    relations: list[Relation]

@dataclass
class Enum:
    name: str          # e.g. "Role"
    values: list[str]  # e.g. ["USER", "ADMIN"]

@dataclass
class ProjectConfig:
    project_name: str
    base_package: str
    database: str
    entities: list[Entity]
    enums: list[Enum]
```

---

## Generated Structure

For a project `ecommerce-api` with package `com.pio.ecommerce` and two entities `Product` and `Category`:

```
ecommerce-api/
├── pom.xml
└── src/
    └── main/
        ├── java/
        │   └── com/pio/ecommerce/
        │       ├── EcommerceApiApplication.java
        │       ├── config/
        │       │   └── SwaggerConfig.java
        │       ├── controller/
        │       │   ├── ProductController.java
        │       │   └── CategoryController.java
        │       ├── dto/
        │       │   ├── request/
        │       │   │   ├── ProductRequestDTO.java
        │       │   │   └── CategoryRequestDTO.java
        │       │   └── response/
        │       │       ├── ProductResponseDTO.java
        │       │       └── CategoryResponseDTO.java
        │       ├── exception/
        │       │   ├── GlobalExceptionHandler.java
        │       │   ├── ProductNotFoundException.java
        │       │   └── CategoryNotFoundException.java
        │       ├── mapper/
        │       │   ├── ProductMapper.java
        │       │   └── CategoryMapper.java
        │       ├── models/
        │       │   ├── entity/
        │       │   │   ├── Product.java
        │       │   │   └── Category.java
        │       │   └── enum/
        │       │       └── Role.java
        │       ├── repository/
        │       │   ├── ProductRepository.java
        │       │   └── CategoryRepository.java
        │       └── service/
        │           ├── ProductService.java
        │           ├── ProductServiceImpl.java
        │           ├── CategoryService.java
        │           └── CategoryServiceImpl.java
        └── resources/
            └── application.properties
```

---

## Supported Relations

| Relation | Description | Example |
|---|---|---|
| `OneToMany` | One entity has many of another | `Order` → `OrderItem` |
| `ManyToOne` | Many entities belong to one | `OrderItem` → `Order` |
| `ManyToMany` | Both sides have many | `Product` ↔ `Category` |

Relations are declared interactively. JPIO automatically handles:
- The `@JoinTable` annotation for `ManyToMany`
- The `mappedBy` attribute on the inverse side
- The correct field type (`List<TargetEntity>`)

---

## Roadmap

- [x] MVP: interactive wizard + full CRUD scaffold generation
- [x] OneToMany / ManyToMany relation support
- [x] `jpio add` command for existing projects
- [x] `jpio scan` project inspector
- [x] Enums support & Request/Response DTO separation (v0.2.0)
- [ ] `jpio add enum` command for existing projects
- [ ] IntelliJ IDEA plugin
- [ ] VS Code extension
- [ ] Spring Security scaffolding (optional layer)
- [ ] Lombok support toggle
- [ ] MapStruct vs manual mapper toggle

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request to discuss the proposed change.

```bash
git clone https://github.com/PIO-VIA/JPIO.git
cd JPIO
pip install -e ".[dev]"
```

---

## License

MIT © PIO