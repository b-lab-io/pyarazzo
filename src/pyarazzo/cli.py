"""Entry point module of the tool."""

import logging
import sys
from importlib.metadata import PackageNotFoundError, version

import click

from pyarazzo.doc.cmd import doc
from pyarazzo.exceptions import ArazzoError

LOGGER = logging.getLogger(__name__)

try:
    __version__ = version("pyarazzo")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

name = "pyarazzo"


HELP_BLURB = (
    "To see help text, you can run:\n"
    "\n"
    "  pyarazzo --help\n"
    "  pyarazzo <command> --help\n"
    "  pyarazzo <command> <subcommand> --help\n"
)

# generated from https://texteditor.com/ascii-art/
# pylint: disable=anomalous-backslash-in-string
LOGO = (
    "                       ___                              \n"
    "    ____  __  __      /   |  _________ _________  ____  \n"
    "   / __ \\/ / / /_____/ /| | / ___/ __ `/_  /_  / / __ \\ \n"
    "  / /_/ / /_/ /_____/ ___ |/ /  / /_/ / / /_/ /_/ /_/ / \n"
    " / .___/\\__, /     /_/  |_/_/   \\__,_/ /___/___/\\____/  \n"
    "/_/    /____/                                             "
)

USAGE = "pyarazzo [verbose options] <command> <subcommand> [parameters]\n" + f"{HELP_BLURB}"


@click.group()
@click.version_option(__version__)
@click.option("-v", "--verbose", count=True)
def cli(verbose: int) -> None:
    """Cli group.

    Args:
        verbose (int): verbose level
    """
    if verbose == 1:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    elif verbose > 1:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.WARNING)


# adding commands subgroups
cli.add_command(doc)


def main() -> None:
    """Main function."""
    try:
        click.echo(LOGO)
        ctx = cli.make_context("cli", sys.argv[1:])
        with ctx:
            result = cli.invoke(ctx)
            sys.exit(result)
    except click.exceptions.Exit as error:
        # click lib uses a exception to terminate the program
        # also in success case
        sys.exit(error.exit_code)
    except ArazzoError as error:
        LOGGER.exception("An ArazzoError occurred")
        click.echo(f"Error: {error}", err=True)
        sys.exit(-1)
    except click.ClickException as error:
        LOGGER.exception("A Click exception occurred")
        click.echo(f"Click Error: {error}", err=True)
        sys.exit(-1)
    except Exception as error:
        LOGGER.exception("Unexpected error")
        click.echo(f"Unexpected error: {error}", err=True)
        sys.exit(-2)
