import click
from pathlib import Path
import json

from jpio.utils.console import (
    print_banner, print_info, print_success, print_error, 
    print_warning, print_parse_report, print_test_summary, print_section
)
from jpio.core.models import ProjectConfig
from jpio.core.java_parser import parse_project, check_java_available, JPIOParserError
from jpio.core.test_plan_analyzer import build_test_plan
from jpio.core.test_generator import generate_tests
from jpio.utils.file_helper import write_all

@click.command("test")
@click.option("--only", default=None,
    help="Generate only for a specific entity (e.g.: --only Product)")
@click.option("--type", "test_type_opt", default=None,
    type=click.Choice(["service", "controller", "repository", "mapper"]),
    help="Generate only a specific test type")
def test_command(only, test_type_opt):
    """
    Analyzes Java code and generates JUnit 5 + Mockito tests.
    """
    print_banner()
    base_path = Path(".")

    # 1. Check if Spring Boot project
    if not (base_path / "pom.xml").exists():
        print_error("No pom.xml found. Are you in a Spring Boot project?")
        raise click.exceptions.Exit(1)

    # 2. Check for .jpio.json
    config_path = base_path / ".jpio.json"
    if not config_path.exists():
        print_error(".jpio.json not found. Run 'jpio scan' first.")
        raise click.exceptions.Exit(1)

    try:
        with open(config_path, "r") as f:
            project_config = ProjectConfig.from_dict(json.load(f))
    except Exception as e:
        print_error(f"Error loading .jpio.json: {str(e)}")
        raise click.exceptions.Exit(1)

    # 3. Check Java availability
    print_section("Environment Verification")
    is_java, java_version = check_java_available()
    if not is_java:
        print_error("Java not found. Please install Java 17+ from https://adoptium.net")
        raise click.exceptions.Exit(1)
    
    print_success(f"Java {java_version} detected")
    print_success("Spring Boot project detected")
    print_success(f".jpio.json found — {len(project_config.entities)} entities")

    # 4. Source path
    source_path = base_path / "src" / "main" / "java"
    if not source_path.exists():
        print_error(f"Source path {source_path} not found.")
        raise click.exceptions.Exit(1)

    # 5. Parse
    print_section("Source Code Analysis")
    print_info("Analyzing source code...")
    try:
        parse_result = parse_project(source_path)
        print_parse_report(parse_result)
    except JPIOParserError as e:
        print_error(str(e))
        raise click.exceptions.Exit(1)

    # 6. Errors
    if parse_result.errors:
        for err in parse_result.errors:
            print_warning(err)

    # 7. Build test plan
    test_plan = build_test_plan(parse_result, project_config)

    # 8. Filters
    if only:
        test_plan.test_classes = [
            tc for tc in test_plan.test_classes 
            if only.lower() in tc.class_under_test.lower()
        ]
    
    if test_type_opt:
        # Map choice to internal type
        opt_map = {
            "service": "SERVICE_IMPL",
            "controller": "CONTROLLER",
            "repository": "REPOSITORY",
            "mapper": "MAPPER"
        }
        internal_type = opt_map[test_type_opt]
        test_plan.test_classes = [
            tc for tc in test_plan.test_classes 
            if tc.test_type == internal_type
        ]

    # 9. Empty plan?
    if not test_plan.test_classes:
        print_warning("No matching classes found for test generation.")
        raise click.exceptions.Exit(0)

    # 10. Generate
    print_section("Test Generation")
    print_info("Generating tests...")
    generated = generate_tests(test_plan)

    # 11. Write
    file_count = write_all(generated, base_path)

    # 12. Summary
    print_test_summary(test_plan, file_count)
