"""
Handles the interactive questionnaire for Spring Security JWT.
Produces a SecurityConfig object from user responses.
"""

import questionary
from jpio.core.models import ProjectConfig, SecurityConfig, Field, Enum
from jpio.core.analyzer import QSTYLE, _collect_fields

def run_security_wizard(config: ProjectConfig) -> SecurityConfig:
    """
    Runs the security questionnaire and returns a SecurityConfig.
    """
    
    # 1. Username Field
    username_field = questionary.select(
        "Field used as login identifier:",
        choices=["email", "username", "[ Enter manually ]"],
        default="email",
        style=QSTYLE
    ).ask()
    
    if username_field == "[ Enter manually ]":
        username_field = questionary.text(
            "Enter custom login field name:",
            style=QSTYLE
        ).ask()
    
    # 2. Existing User Entity
    has_existing_user = questionary.confirm(
        "Does your project already have a User entity?",
        default=False,
        style=QSTYLE
    ).ask()
    
    existing_user_entity = ""
    extra_user_fields = []
    
    if has_existing_user:
        choices = [e.name for e in config.entities]
        choices.append("[ Enter name manually ]")
        
        selection = questionary.select(
            "Select or enter existing User entity:",
            choices=choices,
            style=QSTYLE
        ).ask()
        
        if selection == "[ Enter name manually ]":
            existing_user_entity = questionary.text(
                "Enter existing User entity name:",
                style=QSTYLE
            ).ask().strip()
        else:
            existing_user_entity = selection

        print(f"  [bold yellow]⚠[/bold yellow] Important: Your [bold]{existing_user_entity}[/bold] entity must:")
        print(f"     1. Implement [bold]org.springframework.security.core.userdetails.UserDetails[/bold]")
        print(f"     2. Have a repository [bold]{existing_user_entity}Repository[/bold] with method [bold]findBy{username_field.capitalize()}[/bold]")
        print(f"     3. (Recommended) Use Lombok [bold]@Builder[/bold] for the AuthController to work as generated.")
    
    if not existing_user_entity:
        print("  [bold cyan]ℹ[/bold cyan] User.java will be generated with: id, " + username_field + ", password, role.")
        add_extra = questionary.confirm(
            "Would you like to add extra fields to the new User entity?",
            default=False,
            style=QSTYLE
        ).ask()
        
        if add_extra:
            # We reuse the _collect_fields from analyzer.py
            # existing_enums is passed to allow selecting enums
            extra_user_fields = _collect_fields(config.enums)
            
    # 3. JWT Secret
    jwt_secret = questionary.text(
        "JWT Secret Key (min 32 chars recommended):",
        default="jpio-secret-key-change-me-in-production",
        style=QSTYLE
    ).ask()
    
    # 4. JWT Expiration
    jwt_expiration_hours = questionary.text(
        "JWT validity duration (in hours):",
        default="24",
        validate=lambda v: v.isdigit() or "Please enter a number.",
        style=QSTYLE
    ).ask()
    jwt_expiration_hours = int(jwt_expiration_hours)
    
    # 5. Public Routes
    public_routes = []
    print("  [bold cyan]ℹ[/bold cyan] Default public routes: /auth/**, /swagger-ui/**, /swagger-ui.html, /api-docs/**")
    
    while True:
        route = questionary.text(
            "Add an extra public route (e.g., /api/public/**, empty to finish):",
            style=QSTYLE
        ).ask()
        
        if not route or not route.strip():
            break
            
        public_routes.append(route.strip())
        
    return SecurityConfig(
        username_field=username_field,
        jwt_secret=jwt_secret,
        jwt_expiration_hours=jwt_expiration_hours,
        public_routes=public_routes,
        existing_user_entity=existing_user_entity,
        extra_user_fields=extra_user_fields
    )
