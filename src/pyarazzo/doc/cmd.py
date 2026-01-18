"""Documentation Commands.

This module provides CLI commands for generating documentation from Arazzo specifications.
"""

import click

from pyarazzo.doc.generator import SimpleMarkdownGeneratorVisitor
from pyarazzo.exceptions import ArazzoError, GenerationError
from pyarazzo.model.arazzo import ArazzoSpecificationLoader


@click.group()
def doc() -> None:
    """Documentation related commands."""


@doc.command()
@click.option(
    "-s",
    "--spec",
    "spec_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to the Arazzo specification file",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(),
    default=".",
    help="Path ",
)
def generate(spec_path: str, output_dir: str) -> None:
    """Generate documentation from Arazzo specification."""
    try:
        specification = ArazzoSpecificationLoader.load(spec_path)
        visitor: SimpleMarkdownGeneratorVisitor = SimpleMarkdownGeneratorVisitor(output_dir)
        specification.accept(visitor)
        click.echo(f"Documentation generated successfully from {spec_path} to {output_dir}")
    except ArazzoError as error:
        click.echo(f"Error: {error}", err=True)
        raise click.Abort from error
    except Exception as error:  # noqa: BLE001
        click.echo(f"Unexpected error generating documentation: {error}", err=True)
        raise click.Abort from GenerationError(f"Documentation generation failed: {error!s}")
