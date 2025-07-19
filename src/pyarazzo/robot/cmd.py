"""Robot framework command sub group."""

import click


@click.group()
def robot() -> None:
    """Robot framework related commands."""
