"""Documentation Commands.

This module provides CLI commands for generating documentation from Arazzo specifications.
"""

import logging
import uuid

import click

from pyarazzo.doc.generator import SimpleMarkdownGeneratorVisitor
from pyarazzo.exceptions import ArazzoError, GenerationError
from pyarazzo.model.arazzo import ArazzoSpecificationLoader

LOGGER = logging.getLogger(__name__)


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
    correlation_id = str(uuid.uuid4())
    try:
        LOGGER.info(f"[{correlation_id}] Starting documentation generation from {spec_path}")
        specification = ArazzoSpecificationLoader.load(spec_path)
        visitor: SimpleMarkdownGeneratorVisitor = SimpleMarkdownGeneratorVisitor(
            output_dir, correlation_id=correlation_id,
        )
        specification.accept(visitor)
        LOGGER.info(f"[{correlation_id}] Documentation generated successfully")
        click.echo(f"Documentation generated successfully from {spec_path} to {output_dir}")
    except ArazzoError as error:
        LOGGER.exception(f"[{correlation_id}] ArazzoError")
        click.echo(f"Error: {error}", err=True)
        raise click.Abort from error
    except Exception as error:
        LOGGER.exception(f"[{correlation_id}] Unexpected error")
        click.echo(f"Unexpected error generating documentation: {error}", err=True)
        raise click.Abort from GenerationError(f"Documentation generation failed: {error!s}")
