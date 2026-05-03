"""
Everything displayed in the terminal goes through here.
Rich is centralized to maintain a consistent style throughout JPIO.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# ---------------------------------------------------------------------------
# Startup Banner
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Displays the JPIO banner at launch with ASCII art."""
    ascii_art = """
      _ ____ ___ ___  
     | |  _ \\_ _/ _ \\ 
  _  | | |_) | | | | |
 | |_| |  __/| | |_| |
  \\___/|_|  |___\\___/ 
"""
    
    banner = Text(ascii_art, justify="center", style="bold cyan")
    banner.append("\n — Java Project Input/Output\n", style="bold white")
    banner.append(" Spring Boot Scaffolding CLI", style="dim white")
    banner.append("  •  v0.6.0", style="dim cyan")

    console.print(
        Panel(banner, border_style="cyan", padding=(1, 2), box=box.DOUBLE)
    )
    console.print()


# ---------------------------------------------------------------------------
# Status Messages
# ---------------------------------------------------------------------------

def print_success(message: str) -> None:
    console.print(f"  [bold green]✔[/bold green]  {message}")


def print_error(message: str) -> None:
    console.print(f"  [bold red]✘[/bold red]  {message}")


def print_info(message: str) -> None:
    console.print(f"  [bold cyan]ℹ[/bold cyan]  {message}")


def print_warning(message: str) -> None:
    console.print(f"  [bold yellow]⚠[/bold yellow]  {message}")


def print_section(title: str) -> None:
    """Displays a section separator."""
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")
    console.print()


# ---------------------------------------------------------------------------
# Final Generation Report
# ---------------------------------------------------------------------------

def print_file_created(filepath: str) -> None:
    """Displays a file created during generation."""
    filename = filepath.split("/")[-1]
    console.print(f"  [green]✔[/green]  [dim]{filepath.rsplit('/', 1)[0]}/[/dim][white]{filename}[/white]")


def print_summary(
    project_name: str,
    entity_count: int,
    file_count: int,
) -> None:
    """Displays the final summary panel after generation."""
    console.print()

    summary = Text()
    summary.append(f"  ✅  Generation completed!\n\n", style="bold green")
    summary.append(f"  Project   : ", style="dim white")
    summary.append(f"{project_name}\n", style="bold white")
    summary.append(f"  Entities  : ", style="dim white")
    summary.append(f"{entity_count}\n", style="bold cyan")
    summary.append(f"  Files     : ", style="dim white")
    summary.append(f"{file_count} created", style="bold cyan")

    console.print(
        Panel(summary, border_style="green", padding=(1, 4), box=box.DOUBLE)
    )
    console.print()


# ---------------------------------------------------------------------------
# Folder Detection Report
# ---------------------------------------------------------------------------

def print_folder_mapping_report(mapping) -> None:
    """
    Displays a summary table of detected folders.
    
    mapping: FolderMapping object
    """
    table = Table(
        title="[bold cyan]JPIO — Folder Mapping[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white",
    )

    table.add_column("Logical Layer", style="dim white")
    table.add_column("Actual Folder",  style="bold cyan")

    # Sorted for clean display
    sorted_mapping = sorted(mapping.to_dict().items())

    for layer, folder in sorted_mapping:
        table.add_row(layer.capitalize(), folder)

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Scan Table (jpio scan)
# ---------------------------------------------------------------------------

def print_scan_table(entities: list[dict]) -> None:
    """
    Displays a summary table of project entities.

    entities: list of dicts with keys 'name', 'fields', 'relations'
    """
    table = Table(
        title="[bold cyan]JPIO — Project State[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white on #1a1a2e",
        show_lines=True,
    )

    table.add_column("Entity",    style="bold cyan",  min_width=16)
    table.add_column("Fields",    style="white",       min_width=30)
    table.add_column("Relations", style="yellow",      min_width=24)

    for entity in entities:
        fields_str    = ", ".join(
            f"{f['name']}: {f['java_type']}" for f in entity["fields"]
        )
        relations_str = ", ".join(
            f"{r['kind']} → {r['target']}" for r in entity["relations"]
        ) or "[dim]none[/dim]"

        table.add_row(entity["name"], fields_str, relations_str)

    console.print()
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Security Plan
# ---------------------------------------------------------------------------

def print_security_plan(security_config) -> None:
    """
    Displays a summary of the security configuration before generation.
    """
    table = Table(
        title="[bold cyan]JPIO — Security Implementation Plan[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white",
    )

    table.add_column("Setting", style="dim white")
    table.add_column("Value",   style="bold cyan")

    table.add_row("Username Field", security_config.username_field)
    table.add_row("JWT Secret",     security_config.jwt_secret[:8] + "...")
    table.add_row("JWT Expiration", f"{security_config.jwt_expiration_hours} hours")
    
    user_type = f"Existing ({security_config.existing_user_entity})" if security_config.existing_user_entity else "New (generated User.java)"
    table.add_row("User Entity",    user_type)

    routes = ", ".join(security_config.public_routes) if security_config.public_routes else "none"
    table.add_row("Public Routes",  routes)

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Test Reports (jpio test)
# ---------------------------------------------------------------------------

def print_parse_report(parse_result: "ParseResult") -> None:
    """
    Displays a summary table of the code analysis.
    """
    table = Table(
        title="[bold cyan]JPIO — Source Code Analysis[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white",
    )

    table.add_column("Class", style="bold white")
    table.add_column("Type",  style="cyan")
    table.add_column("Methods", style="dim white", justify="right")

    for cls in parse_result.classes:
        table.add_row(
            cls.name,
            cls.class_type,
            str(len(cls.methods))
        )

    console.print(table)
    console.print()


def print_test_summary(test_plan: "TestPlan", file_count: int) -> None:
    """
    Displays the final test generation summary.
    """
    total_methods = sum(len(tc.test_methods) for tc in test_plan.test_classes)
    
    # Distribution
    dist = {}
    for tc in test_plan.test_classes:
        dist[tc.test_type] = dist.get(tc.test_type, 0) + 1

    dist_str = " | ".join([f"{k.replace('_IMPL', '').capitalize()}: {v}" for k, v in dist.items()])

    summary = Text()
    summary.append(f"  ✅  Test generation completed!\n\n", style="bold green")
    summary.append(f"  Test Files : ", style="dim white")
    summary.append(f"{file_count} created\n", style="bold cyan")
    summary.append(f"  Methods    : ", style="dim white")
    summary.append(f"{total_methods} @Test generated\n", style="bold cyan")
    summary.append(f"  Details    : ", style="dim white")
    summary.append(f"{dist_str}", style="dim white")

    console.print(
        Panel(summary, border_style="green", padding=(1, 4), box=box.DOUBLE)
    )
    console.print()