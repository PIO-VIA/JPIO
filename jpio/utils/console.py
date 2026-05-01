"""
utils/console.py
----------------
Tout ce qui est affiché dans le terminal passe par ici.
On centralise Rich pour garder un style cohérent partout dans JPIO.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# ---------------------------------------------------------------------------
# Bannière de démarrage
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Affiche la bannière JPIO au lancement."""
    banner = Text()
    banner.append("  🔧 JPIO", style="bold cyan")
    banner.append(" — Java Project Input/Output\n", style="bold white")
    banner.append("  Spring Boot Scaffolding CLI", style="dim white")
    banner.append("  •  v0.1.0", style="dim cyan")

    console.print(
        Panel(banner, border_style="cyan", padding=(1, 4), box=box.DOUBLE)
    )
    console.print()


# ---------------------------------------------------------------------------
# Messages de statut
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
    """Affiche un séparateur de section."""
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")
    console.print()


# ---------------------------------------------------------------------------
# Rapport de génération final
# ---------------------------------------------------------------------------

def print_file_created(filepath: str) -> None:
    """Affiche un fichier créé pendant la génération."""
    filename = filepath.split("/")[-1]
    console.print(f"  [green]✔[/green]  [dim]{filepath.rsplit('/', 1)[0]}/[/dim][white]{filename}[/white]")


def print_summary(
    project_name: str,
    entity_count: int,
    file_count: int,
) -> None:
    """Affiche le panneau de résumé final après génération."""
    console.print()

    summary = Text()
    summary.append(f"  ✅  Génération terminée !\n\n", style="bold green")
    summary.append(f"  Projet   : ", style="dim white")
    summary.append(f"{project_name}\n", style="bold white")
    summary.append(f"  Entités  : ", style="dim white")
    summary.append(f"{entity_count}\n", style="bold cyan")
    summary.append(f"  Fichiers : ", style="dim white")
    summary.append(f"{file_count} créés", style="bold cyan")

    console.print(
        Panel(summary, border_style="green", padding=(1, 4), box=box.DOUBLE)
    )
    console.print()


# ---------------------------------------------------------------------------
# Table de scan (jpio scan)
# ---------------------------------------------------------------------------

def print_scan_table(entities: list[dict]) -> None:
    """
    Affiche un tableau récapitulatif des entités du projet.

    entities : liste de dicts avec clés 'name', 'fields', 'relations'
    """
    table = Table(
        title="[bold cyan]JPIO — État du projet[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white on #1a1a2e",
        show_lines=True,
    )

    table.add_column("Entité",    style="bold cyan",  min_width=16)
    table.add_column("Champs",    style="white",       min_width=30)
    table.add_column("Relations", style="yellow",      min_width=24)

    for entity in entities:
        fields_str    = ", ".join(
            f"{f['name']}: {f['java_type']}" for f in entity["fields"]
        )
        relations_str = ", ".join(
            f"{r['kind']} → {r['target']}" for r in entity["relations"]
        ) or "[dim]aucune[/dim]"

        table.add_row(entity["name"], fields_str, relations_str)

    console.print()
    console.print(table)
    console.print()