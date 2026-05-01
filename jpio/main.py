"""
main.py
-------
Point d'entrée du CLI JPIO.
Déclare le groupe de commandes Click et enregistre toutes les sous-commandes.

Après pip install, la commande `jpio` est disponible partout
grâce à la config [project.scripts] dans pyproject.toml :
    jpio = "jpio.main:cli"
"""

import click
from jpio.commands.new import start_command
from jpio.commands.scan import scan_command
from jpio.commands.add import add_command


@click.group()
@click.version_option(version="0.2.0", prog_name="JPIO")
def cli():
    """
    \b
    JPIO — Java Project Input/Output
    Spring Boot Scaffolding CLI

    Lancez `jpio start` depuis la racine de votre projet Spring Boot.
    """
    pass


cli.add_command(start_command)
cli.add_command(scan_command)
cli.add_command(add_command)


if __name__ == "__main__":
    cli()