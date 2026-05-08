# JPIO — Java Project Input/Output

[![PyPI version](https://img.shields.io/pypi/v/jpio-cli.svg)](https://pypi.org/project/jpio-cli/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.x-brightgreen.svg)](https://spring.io/projects/spring-boot)

JPIO is a comprehensive Command Line Interface (CLI) utility designed to streamline the development lifecycle of Spring Boot applications. By automating the generation of production-ready architectural layers, JPIO allows developers to focus on core business logic rather than repetitive boilerplate code.

---

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Technical Architecture](#technical-architecture)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

In modern Java development, initializing a new microservice or adding a new resource often involves creating multiple repetitive files: Entities, DTOs, Mappers, Repositories, Services, and Controllers. JPIO automates this process through an interactive, template-driven engine that adheres to industry best practices and clean architecture principles.

Unlike simple scaffolding tools, JPIO maintains a state of your project, allowing it to manage complex entity relationships and perform static analysis on existing code to generate relevant unit tests.

---

## Core Features

### 1. Advanced Scaffolding Engine
JPIO generates a complete vertical slice of your application based on entity definitions. This includes:
- **JPA Entities**: With proper annotations and relationship mappings.
- **Data Transfer Objects (DTOs)**: Separate request and response DTOs for better API contract management.
- **Mappers**: Logic to convert between Entities and DTOs.
- **Spring Data Repositories**: Standard interface declarations.
- **Service Layer**: Separation of concerns with Interfaces and Implementation classes.
- **REST Controllers**: Full CRUD endpoints with standard HTTP status codes.

### 2. Relationship Management
Support for complex JPA relationships:
- **OneToMany / ManyToOne**: Bidirectional or unidirectional support.
- **ManyToMany**: Automatic generation of join tables and mapping attributes.
- **Inverse Mapping**: Automatic detection and configuration of `mappedBy` attributes.

### 3. Integrated Security Scaffolding
Inject a robust security layer into any project with a single command. The security module provides:
- JWT-based authentication flow.
- Security configuration with filter chains.
- Pre-configured User and Role management.
- Authentication endpoints (Login/Register).

### 4. Smart Unit Test Generation
Leveraging a specialized Java parser, JPIO analyzes your source code to generate high-coverage JUnit 5 tests:
- **Universal Support**: Operates on any Spring Boot project, regardless of whether it was initialized with JPIO.
- **Mockito Integration**: Automatic mocking of dependencies and constructor injection.
- **WebMvcTest Support**: Specialized test templates for Controller layer validation.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- Java 17 or higher (required for the `test` command analysis)
- Pip or Pipx

### Installation via Pip
```bash
pip install jpio-cli
```

---

## Quick Start

To initialize a new project or add business layers to an existing Spring Boot application, navigate to the root directory (where `pom.xml` is located) and execute:

```bash
jpio start
```

Follow the interactive prompts to define your entities and their properties. JPIO will automatically detect your base package and configuration format (YAML or Properties).

---

## Command Reference

| Command | Description | Options |
|:---|:---|:---|
| `start` | Launches the interactive project initialization wizard. | N/A |
| `add` | Appends a new entity to an existing JPIO-managed project. | N/A |
| `security` | Injects a Spring Security + JWT authentication layer. | N/A |
| `test` | Analyzes code and generates JUnit 5 + Mockito tests. | `--only`, `--type` |
| `scan` | Displays a detailed report of entities and project state. | N/A |

### Automated Testing Example
To generate tests for a specific service implementation:
```bash
jpio test --only ProductService --type service
```

---

## Technical Architecture

JPIO is built with a modular internal structure to ensure reliability and extensibility:

- **Core Engine**: Handles the logic for project analysis and configuration state.
- **Parser Module**: A specialized Java utility (packaged as a JAR) that performs deep static analysis of source files.
- **Template Engine**: Powered by Jinja2, providing flexible and customizable code generation.
- **Console UI**: Utilizes `Rich` and `Questionary` for a robust and safe user experience, including graceful interruption handling (Ctrl+C).

### Standard Project Layout
Projects generated or managed by JPIO typically follow this structure:

```text
src/main/java/[package]/
├── config/             # Infrastructure configuration (Security, OpenAPI)
├── controller/         # REST API Controllers
├── dto/                # Request/Response Data Transfer Objects
├── mapper/             # Object mapping logic
├── models/
│   ├── entity/         # JPA Entities
│   └── enum/           # Type-safe enumerations
├── repository/         # Data access layer
├── security/           # JWT and Security filters
└── service/            # Business logic interfaces and implementations
```

---

## Roadmap

- **Completed**: Core CRUD scaffolding and relationship support.
- **Completed**: Spring Security JWT integration (v0.5.0).
- **Completed**: Smart Unit Test generation (v0.6.0).
- **Completed**: Universal project support and interruption handling (v0.6.5).
- **Planned**: `jpio add enum` command for standalone enum generation.
- **Planned**: MapStruct integration for high-performance mapping.
- **Future**: Native IDE plugins for IntelliJ IDEA and VS Code.

---

## Contributing

Contributions are essential to the evolution of JPIO. To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/name`).
3. Install development dependencies: `pip install -e ".[dev]"`.
4. Validate changes with `pytest`.
5. Submit a detailed Pull Request.

---

<p align="center">
  Built with ❤️ by <b>PIO</b>
</p>
