"""
Entry point for the JPIO CLI.
Declares the Click command group and registers all subcommands.

After pip install, the `jpio` command is available everywhere
thanks to the [project.scripts] config in pyproject.toml:
    jpio = "jpio.main:cli"
"""

import click
from jpio.commands.new import start_command
from jpio.commands.scan import scan_command
from jpio.commands.add import add_command


@click.group()
@click.version_option(version="0.4.0", prog_name="JPIO")
def cli():
    """
    \b
    JPIO — Java Project Input/Output
    Spring Boot Scaffolding CLI

    Run `jpio start` from the root of your Spring Boot project.
    """
    pass


cli.add_command(start_command)
cli.add_command(scan_command)
cli.add_command(add_command)


if __name__ == "__main__":
    cli()