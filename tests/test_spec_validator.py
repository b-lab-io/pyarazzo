"""Tests for workflow specification validator."""

from __future__ import annotations

import pytest
from pyarazzo.model.arazzo import ArazzoSpecification, ParameterObject, Step, Workflow
from pyarazzo.spec.validator import WorkflowValidationVisitor


def test_validator_detects_missing_required_parameters() -> None:
    """Test that validator detects missing required parameters in workflows."""
    # Load a test specification
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )
    
    is_valid, errors, warnings = validator.validate()
    # The spec should have missing required parameters
    assert is_valid is False
    # Should have errors about missing required parameters
    assert any("missing required" in e for e in errors)


def test_validator_loads_openapi_spec() -> None:
    """Test that validator properly loads OpenAPI specifications."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )
    
    # Verify operations were loaded
    assert len(validator.operation_registry.operations) > 0


def test_validator_validates_workflow_dependencies() -> None:
    """Test that validator checks workflow dependencies."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )
    
    is_valid, errors, warnings = validator.validate()
    
    # Check for dependency-related errors, if any exist
    dependency_errors = [e for e in errors if "depends on" in e]
    # The test spec should not have broken dependencies
    assert len(dependency_errors) == 0


def test_validator_with_specific_workflow_id() -> None:
    """Test that validator can validate a specific workflow."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    
    # Get the first workflow ID if one exists
    if spec.workflows:
        workflow_id = spec.workflows[0].workflow_id
        validator = WorkflowValidationVisitor(
            specification=spec,
            spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
            workflow_id=workflow_id,
        )
        
        is_valid, errors, warnings = validator.validate()
        
        # Should not have error about workflow not found
        workflow_not_found = [e for e in errors if "not found in specification" in e]
        assert len(workflow_not_found) == 0


def test_validator_detects_nonexistent_workflow_id() -> None:
    """Test that validator detects when workflow filter doesn't match."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
        workflow_id="nonexistent-workflow-id",
    )
    
    is_valid, errors, warnings = validator.validate()
    
    # Should have error about workflow not found
    assert is_valid is False
    assert any("not found in specification" in e for e in errors)


def test_validator_url_resolution_with_relative_paths() -> None:
    """Test that validator resolves relative URLs correctly."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    spec = ArazzoSpecification(**spec_dict)
    
    # Pass a spec path with a relative directory
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )
    
    # Verify operations were loaded (url resolution worked)
    assert len(validator.operation_registry.operations) > 0
    assert len(validator.errors) == 0, f"Unexpected errors: {validator.errors}"


def test_validator_handles_missing_openapi_spec() -> None:
    """Test that validator handles missing OpenAPI specs gracefully."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        import yaml
        spec_dict = yaml.safe_load(f)
    
    # Modify spec to point to non-existent file
    spec_dict["sourceDescriptions"][0]["url"] = "/nonexistent/path/spec.json"
    spec = ArazzoSpecification(**spec_dict)
    
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )
    
    is_valid, errors, warnings = validator.validate()
    
    # Should have errors about failing to load OpenAPI spec
    assert any("Failed to load OpenAPI spec" in e for e in errors)
