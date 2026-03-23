"""Specification Commands.

This module provides CLI commands for working with Arazzo specifications.
"""

import logging
import uuid

import click

from pyarazzo.exceptions import ArazzoError
from pyarazzo.model.arazzo import ArazzoSpecificationLoader
from pyarazzo.spec.validator import WorkflowValidationVisitor

LOGGER = logging.getLogger(__name__)


@click.group()
def spec() -> None:
    """Specification related commands."""


@spec.command()
@click.option(
    "-s",
    "--spec",
    "spec_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to the Arazzo specification file",
)
@click.option(
    "-w",
    "--workflow",
    "workflow_id",
    type=str,
    default=None,
    help="Optional workflow ID to validate (if not specified, validates all workflows)",
)
def validate(spec_path: str, workflow_id: str | None) -> None:
    """Validate an Arazzo specification for workflow executability.

    Validates that:
    - All referenced operations exist in OpenAPI specs
    - All required parameters are provided
    - Workflow dependencies are satisfied
    - Workflows and steps are properly defined
    """
    correlation_id = str(uuid.uuid4())
    try:
        LOGGER.info(
            f"[{correlation_id}] Starting validation of specification: {spec_path}",
        )

        # Load the specification
        specification = ArazzoSpecificationLoader.load(spec_path)

        # Create validator and run validation
        validator = WorkflowValidationVisitor(
            specification=specification,
            spec_path=spec_path,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )

        is_valid, errors, warnings = validator.validate()

        # Display results
        click.echo()
        click.echo(f"Specification: {spec_path}")
        if workflow_id:
            click.echo(f"Workflow: {workflow_id}")
        click.echo()

        if errors:
            click.echo(f"❌ Validation FAILED with {len(errors)} error(s):", err=True)
            for i, error in enumerate(errors, 1):
                click.echo(f"  {i}. {error}", err=True)
            click.echo()

        if warnings:
            click.echo(f"⚠️  {len(warnings)} warning(s):")
            for i, warning in enumerate(warnings, 1):
                click.echo(f"  {i}. {warning}")
            click.echo()

        if is_valid:
            click.echo("✅ Validation PASSED")
            LOGGER.info(f"[{correlation_id}] Validation completed successfully")
            if warnings:
                LOGGER.warning(f"[{correlation_id}] Validation passed with {len(warnings)} warnings")
        else:
            LOGGER.error(f"[{correlation_id}] Validation failed with {len(errors)} errors")

    except ArazzoError as error:
        LOGGER.exception(f"[{correlation_id}] ArazzoError")
        click.echo(f"Error: {error}", err=True)
        raise click.Abort from error
    except Exception as error:
        LOGGER.exception(f"[{correlation_id}] Unexpected error")
        click.echo(f"Unexpected error: {error}", err=True)
        raise click.Abort from error
