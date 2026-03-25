"""Tests for the CLI."""

from __future__ import annotations

from click.testing import CliRunner

from pyarazzo.cli import cli

# if TYPE_CHECKING:
#     import pytest


def test_main() -> None:
    """Basic CLI test."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])  # type: ignore[invalid-argument-type]
    assert result.exit_code == 0


# def test_show_help(capsys: pytest.CaptureFixture) -> None:
#     """Show help.

#     Parameters:
#         capsys: Pytest fixture to capture output.
#     """

#     with pytest.raises(SystemExit):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['-h'])
#     captured = capsys.readouterr()
#     assert "pyarazzo" in captured.out
#     assert result.exit_code != 0


# def test_show_version(capsys: pytest.CaptureFixture) -> None:
#     """Show version.

#     Parameters:
#         capsys: Pytest fixture to capture output.
#     """
#     runner = CliRunner()
#     result = runner.invoke(cli, ["-v"])# type: ignore[arg-type]

#     captured = capsys.readouterr()
#     assert debug.get_version() in captured.out
#     assert result.exit_code == 0


# def test_show_debug_info(capsys: pytest.CaptureFixture) -> None:
#     """Show debug information.

#     Parameters:
#         capsys: Pytest fixture to capture output.
#     """

#     with pytest.raises(SystemExit):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['--debug-info'])
#     captured = capsys.readouterr().out.lower()
#     assert "python" in captured
#     assert "system" in captured
#     assert "environment" in captured
#     assert "packages" in captured
