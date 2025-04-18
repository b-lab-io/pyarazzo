import click
from pathlib import Path

from pyarazzo.doc.generator import MarkdownGeneratorVisitor
from pyarazzo.model.arazzo import ArazzoLoader, ArazzoSpec
from pyarazzo.utils import load_spec


@click.group()
def doc():
    """Documentation related commands"""
    pass

@doc.command()
@click.option('-s', '--spec', 'spec_path', type=click.Path(exists=True), required=True,
              help='Path to the Arazzo specification file')
@click.option('-o', '--output', 'output_dir', type=click.Path(), default='.',
              help='Path ')
def generate(spec_path, output_dir):
    """Generate documentation from Arazzo specification"""
  
    try:
        # Here you would add the logic to:
        specification = ArazzoLoader.load(spec_path)
        visitor:MarkdownGeneratorVisitor = MarkdownGeneratorVisitor(output_dir)
        specification.accept(visitor)

        click.echo(f"Generating documentation from {spec_path} done")
    except Exception as e:
        click.echo(f"Error generating documentation: {str(e)}", err=True)
        raise click.Abort()
