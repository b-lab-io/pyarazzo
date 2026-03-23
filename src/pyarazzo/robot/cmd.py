"""Robot Framework Commands.

This module provides CLI commands for generating Robot Framework test scripts from Arazzo specifications.
"""

import logging
import uuid

import click

from pyarazzo.exceptions import ArazzoError, GenerationError
from pyarazzo.model.arazzo import ArazzoSpecificationLoader
from pyarazzo.robot.generator import RobotFrameworkGeneratorVisitor

LOGGER = logging.getLogger(__name__)


@click.group()
def robot() -> None:
    """Robot Framework related commands."""


@robot.command()
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
    help="Output directory for generated Robot Framework files",
)
def generate(spec_path: str, output_dir: str) -> None:
    """Generate Robot Framework test scripts from Arazzo specification."""
    correlation_id = str(uuid.uuid4())
    try:
        LOGGER.info(f"[{correlation_id}] Starting Robot Framework generation from {spec_path}")
        specification = ArazzoSpecificationLoader.load(spec_path)
        visitor = RobotFrameworkGeneratorVisitor(output_dir, correlation_id=correlation_id)
        specification.accept(visitor)
        LOGGER.info(f"[{correlation_id}] Robot Framework tests generated successfully")
        click.echo(f"Robot Framework tests generated successfully to {output_dir}")
    except ArazzoError as error:
        LOGGER.error(f"[{correlation_id}] ArazzoError: {error}")
        click.echo(f"Error: {error}", err=True)
        raise click.Abort from error
    except Exception as error:  # noqa: BLE001
        LOGGER.error(f"[{correlation_id}] Unexpected error: {error}")
        click.echo(f"Unexpected error generating Robot Framework: {error}", err=True)
        raise click.Abort from GenerationError(f"Robot Framework generation failed: {error!s}")
