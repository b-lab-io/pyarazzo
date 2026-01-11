"""Robot framework command sub group."""

import json
from pathlib import Path

import click

from pyarazzo.model.arazzo import ArazzoSpecificationLoader
from pyarazzo.robot.visitor import ArazzoRobotFrameworkVisitor


@click.group()
def robot() -> None:
    """Robot framework related commands."""


@robot.command("generate")
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
@click.option(
    "--format",
    type=click.Choice(["robot", "json"]),
    default="robot",
    help="Output format (default: robot)",
)
def generate(spec_path: str, output_dir: str, format: str) -> None:
    """Generate a Robot Framework .robot file from an Arazzo specification.

    Example:
        pyarazzo robot generate workflows.yaml tests.robot
    """
    try:
        # Parse the Arazzo specification file

        spec = ArazzoSpecificationLoader.load(spec_path)

        visitor = ArazzoRobotFrameworkVisitor()
        suite = visitor.visit_specification(spec)
        click.echo(f"Generated test suite: {suite.name}")

        # Write output
        if format == "robot":
            output_path = Path(f"{output_dir}/{suite.name.replace(' ', '_').lower()}.robot")
            suite.save(str(output_path))
            click.echo(f"✓ Wrote Robot Framework suite to {output_path}")
        elif format == "json":
            # Export as JSON for inspection
            output_path = Path(f"{output_dir}/{suite.name.replace(' ', '_').lower()}.json")
            data = {
                "name": suite.name,
                "doc": suite.doc,
                "tests": [
                    {
                        "name": tc.name,
                        "doc": tc.doc,
                        "keywords": [{"name": kw.name, "args": kw.args, "doc": kw.doc} for kw in tc.keywords],
                    }
                    for tc in suite.tests
                ],
            }
            output_path.write_text(json.dumps(data, indent=2))
            click.echo(f"✓ Wrote JSON export to {output_path}")
    except Exception as exc:
        click.echo(f"Error generating test suite: {exec!s}", err=True)
        raise click.Abort from exc
