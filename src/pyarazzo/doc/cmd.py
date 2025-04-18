"""Documentation Commands."""

import click

from pyarazzo.doc.generator import SimpleMarkdownGeneratorVisitor
from pyarazzo.model.arazzo import ArazzoSpecificationLoader


@click.group()
def doc()-> None:
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
    "-o", "--output", "output_dir", type=click.Path(), default=".", help="Path ",
)
def generate(spec_path:str, output_dir:str)->None:
    """Generate documentation from Arazzo specification."""
    try:
        # Here you would add the logic to:
        specification = ArazzoSpecificationLoader.load(spec_path)
        visitor: SimpleMarkdownGeneratorVisitor = SimpleMarkdownGeneratorVisitor(output_dir)
        specification.accept(visitor)

        click.echo(f"Generating documentation from {spec_path} under folder {output_dir} done")
    except Exception as e:
        click.echo(f"Error generating documentation: {e!s}", err=True)
        raise click.Abort from e
