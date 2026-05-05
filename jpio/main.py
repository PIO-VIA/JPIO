"""
Entry point for the JPIO CLI.
Declares the Click command group and registers all subcommands.

After pip install, the `jpio` command is available everywhere
thanks to the [project.scripts] config in pyproject.toml:
    jpio = "jpio.main:cli"
"""

import click
from jpio.core.analyzer import UserAbortedError
from jpio.commands.new import start_command
from jpio.commands.scan import scan_command
from jpio.commands.add import add_command
from jpio.commands.security import security_command
from jpio.commands.test import test_command


@click.group()
@click.version_option(version="0.6.5", prog_name="JPIO")
def cli():
    """
    \b
    JPIO — Java Project Input/Output
    Spring Boot Scaffolding CLI

    Run `jpio start` from the root of your Spring Boot project.
    """
    pass


def cli_safe():
    from jpio.utils.console import console
    try:
        cli(standalone_mode=False)
    except (KeyboardInterrupt, EOFError, UserAbortedError):
        console.print(
            "\n\n  [bold yellow]⚠[/bold yellow]  "
            "Opération annulée par l'utilisateur.\n"
        )
        raise SystemExit(0)
    except click.exceptions.Abort:
        console.print(
            "\n\n  [bold yellow]⚠[/bold yellow]  "
            "Opération annulée.\n"
        )
        raise SystemExit(0)


cli.add_command(start_command)
cli.add_command(scan_command)
cli.add_command(add_command)
cli.add_command(security_command)
cli.add_command(test_command)


if __name__ == "__main__":
    cli_safe()