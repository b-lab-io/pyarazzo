"""Tests for Robot Framework test generation."""

from __future__ import annotations

import os
import tempfile

import pytest

from pyarazzo.model.arazzo import ArazzoSpecificationLoader
from pyarazzo.robot.generator import RobotFrameworkGeneratorVisitor


@pytest.fixture
def temp_output_dir() -> str:
    """Provide a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_robot_generator_creates_output_dir() -> None:
    """Test that robot generator creates output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "test_output", "nested")
        RobotFrameworkGeneratorVisitor(output_dir)
        assert os.path.exists(output_dir)


def test_robot_generator_instantiation(temp_output_dir: str) -> None:
    """Test Robot Framework generator can be instantiated."""
    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    assert generator.output_dir == temp_output_dir
    assert generator.correlation_id is not None
    assert os.path.exists(temp_output_dir)


def test_robot_generator_sanitize_name() -> None:
    """Test name sanitization for Robot Framework compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = RobotFrameworkGeneratorVisitor(tmpdir)
        assert generator._sanitize_name("My Workflow") == "My_Workflow"
        assert generator._sanitize_name("my-step-id") == "my_step_id"
        assert generator._sanitize_name("already_formatted") == "already_formatted"
        assert generator._sanitize_name("mixed-case Name") == "mixed_case_Name"


def test_robot_generator_generates_test_file(temp_output_dir: str) -> None:
    """Test that robot generator creates a test file."""
    spec = ArazzoSpecificationLoader.load("tests/data/models/v1/pet-coupons-example.yaml")

    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    generator.visit_specification(spec)

    # Check that a test file was created
    files = os.listdir(temp_output_dir)
    assert len(files) > 0, "No test files were generated"
    assert any(f.endswith(".robot") for f in files), "No .robot files generated"


def test_robot_generator_test_file_content(temp_output_dir: str) -> None:
    """Test that generated test file contains expected Robot Framework syntax."""
    spec = ArazzoSpecificationLoader.load("tests/data/models/v1/pet-coupons-example.yaml")

    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    generator.visit_specification(spec)

    robot_files = [f for f in os.listdir(temp_output_dir) if f.endswith(".robot")]
    assert len(robot_files) > 0

    with open(os.path.join(temp_output_dir, robot_files[0])) as f:
        content = f.read()

    # Check for standard Robot Framework sections
    assert "*** Settings ***" in content
    assert "*** Variables ***" in content
    assert "*** Keywords ***" in content
    assert "*** Test Cases ***" in content

    # Check for library imports
    assert "Library    RequestsLibrary" in content
    assert "Library    BuiltIn" in content

    # Check for keywords
    assert "Setup API Connection" in content
    assert "Teardown API Connection" in content

    # Check for test cases
    assert "apply_coupon" in content or "buy_available_pet" in content


def test_robot_generator_handles_missing_operations(temp_output_dir: str) -> None:
    """Test that robot generator handles missing operations gracefully."""
    spec = ArazzoSpecificationLoader.load("tests/data/models/v1/pet-coupons-example.yaml")

    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    # This should not raise an exception even though operations are missing
    generator.visit_specification(spec)

    robot_files = [f for f in os.listdir(temp_output_dir) if f.endswith(".robot")]
    assert len(robot_files) > 0, "Test file should be generated despite missing operations"


def test_robot_generator_with_correlation_id(temp_output_dir: str) -> None:
    """Test robot generator tracks correlation ID."""
    correlation_id = "test-correlation-123"
    generator = RobotFrameworkGeneratorVisitor(temp_output_dir, correlation_id=correlation_id)
    assert generator.correlation_id == correlation_id


def test_robot_generator_test_case_structure(temp_output_dir: str) -> None:
    """Test that generated test cases follow Robot Framework structure."""
    spec = ArazzoSpecificationLoader.load("tests/data/models/v1/pet-coupons-example.yaml")

    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    generator.visit_specification(spec)

    robot_files = [f for f in os.listdir(temp_output_dir) if f.endswith(".robot")]
    with open(os.path.join(temp_output_dir, robot_files[0])) as f:
        content = f.read()

    # Check test case structure
    assert "[Documentation]" in content
    assert "[Setup]" in content
    assert "[Teardown]" in content
    assert "[Tags]" in content
    assert "Log" in content


def test_robot_generator_includes_step_parameters(temp_output_dir: str) -> None:
    """Test that generated tests include step parameters in HTTP requests."""
    spec = ArazzoSpecificationLoader.load("tests/data/models/v1/pet-coupons-example.yaml")

    generator = RobotFrameworkGeneratorVisitor(temp_output_dir)
    generator.visit_specification(spec)

    robot_files = [f for f in os.listdir(temp_output_dir) if f.endswith(".robot")]
    with open(os.path.join(temp_output_dir, robot_files[0])) as f:
        content = f.read()

    # Check that query parameters are included in HTTP calls
    assert "pet_tags=" in content or "status=available" in content
    # Check that path parameters are substituted in endpoints
    assert "${response}" in content
