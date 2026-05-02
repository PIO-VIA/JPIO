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
# Go to your Spring Boot project root
cd my-spring-project

# Launch the JPIO wizard
jpio start

# Follow the interactive prompts:
# ? API route prefix     : /api/v1
#
# --- Entity 1 ---
# ? Entity name          : Product
# ? Fields               : name (String), price (Double), stock (Integer)
# ? Has relations?       : Yes → ManyToMany → Category
#
# --- Entity 2 ---
# ? Entity name          : Category
# ? Fields               : name (String)
#
# ? Add another entity? No
#
# ✅ Business layers generated!
```

---

## Commands

| Command | Description |
|---|---|
| `jpio start` | Initialize and scaffold business layers for a project |
| `jpio add` | Add a new entity to an existing JPIO project |
| `jpio security` | Add a complete Spring Security JWT layer |
| `jpio scan` | Display the current state of a JPIO project |

### `jpio start`
Launches the full interactive wizard. Detects your existing package structure, `pom.xml` dependencies, and configuration format (`properties` vs `yaml`). Generates the complete CRUD structure for your entities.

### `jpio add`
Run inside an existing JPIO project. Prompts for a new entity and appends the generated files without touching existing code. Reads `.jpio.json` to stay aware of existing entities and relationships.

### `jpio security`
Adds a complete **Spring Security + JWT** implementation to your project.
- Generates `SecurityConfig`, `JwtUtil`, `JwtAuthenticationFilter`, and `UserDetailsServiceImpl`.
- Generates authentication endpoints (`/auth/login`, `/auth/register`) and DTOs.
- Automatically creates a `User` entity and `Role` enum if not already present.
- Injects required dependencies into your `pom.xml`.

### `jpio scan`
Reads `.jpio.json` and displays a summary table of the project: entities, fields, and relations.

---

## Project Architecture

```
jpio/
├── jpio/
│   ├── main.py                        # CLI entry point (Click)
│   ├── commands/
│   │   ├── new.py                     # `jpio start` — full project wizard
│   │   ├── add.py                     # `jpio add` — add entity
│   │   ├── security.py                # `jpio security` — security flow
│   │   └── scan.py                    # `jpio scan` — display project state
│   ├── core/
│   │   ├── models.py                  # Dataclasses: Field, Relation, Entity, ProjectConfig
│   │   ├── analyzer.py                # Interactive prompts → builds ProjectConfig
│   │   ├── security_analyzer.py       # Security wizard
│   │   ├── generator.py               # Jinja2 rendering engine
│   │   ├── security_generator.py      # Security file generation
│   │   └── writer.py                  # Java code strings → files on disk
│   ├── utils/
│   │   ├── console.py                 # Rich: banners, tables, success/error output
│   │   └── file_helper.py             # Path manipulation, pom.xml dependency injection
│   └── templates/
│       ├── entity/                    # CRUD templates
│       ├── exception/                 # Global exception handling templates
│       ├── config/                    # Swagger/SpringDoc templates
│       ├── security/                  # Spring Security JWT templates
│       └── project/                   # application.properties/yaml templates
├── tests/
│   ├── test_analyzer.py
│   ├── test_generator.py
│   ├── test_security_generator.py
│   └── test_writer.py
├── pyproject.toml
└── README.md
```

---

## Generated Structure

For a project with package `com.pio.ecommerce` and two entities `Product` and `Category`:

```
src/main/java/com/pio/ecommerce/
├── config/
│   ├── SecurityConfig.java            # (If security added)
│   └── SwaggerConfig.java
├── controller/
│   ├── AuthController.java            # (If security added)
│   ├── ProductController.java
│   └── CategoryController.java
├── dto/
│   ├── request/
│   │   ├── LoginRequestDTO.java
│   │   ├── ProductRequestDTO.java
│   │   └── CategoryRequestDTO.java
│   └── response/
│       ├── AuthResponseDTO.java
│       ├── ProductResponseDTO.java
│       └── CategoryResponseDTO.java
├── security/                          # JWT Logic (If security added)
│   ├── JwtUtil.java
│   └── JwtAuthenticationFilter.java
├── models/
│   ├── entity/
│   │   ├── User.java                  # (If security added)
│   │   ├── Product.java
│   │   └── Category.java
│   └── enum/
│       └── Role.java
├── repository/
│   ├── UserRepository.java
│   ├── ProductRepository.java
│   └── CategoryRepository.java
└── service/
    ├── ProductService.java
    └── ProductServiceImpl.java
```

---

## Supported Relations

| Relation | Description | Example |
|---|---|---|
| `OneToMany` | One entity has many of another | `Order` → `OrderItem` |
| `ManyToOne` | Many entities belong to one | `OrderItem` → `Order` |
| `ManyToMany` | Both sides have many | `Product` ↔ `Category` |

JPIO automatically handles:
- The `@JoinTable` annotation for `ManyToMany`
- The `mappedBy` attribute on the inverse side
- Pluralization and correct field types (`List<Target>`)

---

## Roadmap

- [x] MVP: interactive wizard + full CRUD scaffold generation
- [x] OneToMany / ManyToMany relation support
- [x] `jpio add` command for existing projects
- [x] `jpio scan` project inspector
- [x] Enums support & Request/Response DTO separation
- [x] Spring Security scaffolding (v0.5.0)
- [ ] `jpio add enum` command for existing projects
- [ ] IntelliJ IDEA plugin
- [ ] VS Code extension
- [ ] Lombok support toggle
- [ ] MapStruct vs manual mapper toggle

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request.

```bash
git clone https://github.com/PIO-VIA/JPIO.git
cd JPIO
pip install -e ".[dev]"
```

---

## License

MIT © PIO