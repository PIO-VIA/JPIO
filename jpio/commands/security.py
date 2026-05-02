"""
Command: jpio security
Adds Spring Security JWT layer to an existing JPIO project.
"""

import json
from pathlib import Path
import click

from jpio.core.models import ProjectConfig
from jpio.core.security_analyzer import run_security_wizard
from jpio.core.security_generator import generate_security
from jpio.core.writer import write_all
from jpio.utils.console import (
    print_banner,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_security_plan,
)
from jpio.utils.file_helper import (
    is_spring_boot_project,
    detect_project_name,
    inject_security_dependencies,
)

@click.command("security")
def security_command():
    """
    Add Spring Security JWT authentication to the project.
    """
    print_banner()
    
    base_path = Path(".")
    
    # 1. Verification
    if not is_spring_boot_project(base_path):
        print_error("No Spring Boot project detected in this folder.")
        raise SystemExit(1)
        
    jpio_file = base_path / ".jpio.json"
    if not jpio_file.exists():
        print_error(
            "No .jpio.json file found.\n"
            "   Run [bold]jpio start[/bold] first to initialize the project."
        )
        raise SystemExit(1)
        
    # Check if security is already in pom.xml
    pom_content = (base_path / "pom.xml").read_text(encoding="utf-8")
    if "spring-boot-starter-security" in pom_content:
        print_warning("Spring Security is already detected in this project.")
        raise SystemExit(0)
        
    # 2. Load Config
    data = json.loads(jpio_file.read_text(encoding="utf-8"))
    config = ProjectConfig.from_dict(data)
    
    # 3. Security Wizard
    security_config = run_security_wizard(config)
    
    # 4. Show Plan
    print_security_plan(security_config)
    if not questionary.confirm("Do you want to proceed with the generation?", default=True).ask():
        print_info("Security addition cancelled.")
        raise SystemExit(0)
        
    # 5. Generation
    print_info("Generating security files...")
    generated = generate_security(config, security_config)
    
    # 6. Writing
    file_count = write_all(generated, base_path)
    
    # 7. Dependencies
    print_info("Injecting dependencies into pom.xml...")
    if inject_security_dependencies(base_path):
        print_success("pom.xml updated with Spring Security and JJWT dependencies.")
    else:
        print_warning("Could not update pom.xml (dependencies might already exist).")
        
    # 8. Update .jpio.json
    config.security = security_config
    jpio_file.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print_success(".jpio.json updated with security configuration.")
    
    # 9. Final Success
    print_success("Spring Security JWT layer successfully added!")
    print_info("Note: You may need to refresh your IDE or rebuild the project.")

import questionary # Added import here just in case, though it's usually in analyzer
