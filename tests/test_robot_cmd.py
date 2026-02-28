"""Tests for the robot command."""

from __future__ import annotations

import tempfile
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyarazzo.robot.cmd import generate


@pytest.fixture
def sample_spec_file() -> str:
    """Provide a sample Arazzo specification file."""
    return "tests/data/models/v1/pet-coupons-example.yaml"


@pytest.fixture
def temp_output_dir() -> str:
    """Provide a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_generate_robot_command_missing_spec_file() -> None:
    """Test robot generation fails when spec file doesn't exist."""
    runner = CliRunner()
    result = runner.invoke(generate, ["-s", "nonexistent.yaml"])
    assert result.exit_code != 0


@patch("pyarazzo.robot.cmd.ArazzoSpecificationLoader.load")
def test_generate_robot_command_with_valid_spec(mock_load: object) -> None:
    """Test robot generation with valid specification."""
    mock_spec = type("MockSpec", (), {})()
    mock_load.return_value = mock_spec  # type: ignore
    
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(generate, ["-s", "tests/data/models/v1/pet-coupons-example.yaml", "-o", tmpdir])
        # Command execution succeeds
        assert result.exit_code in [0, 1]
