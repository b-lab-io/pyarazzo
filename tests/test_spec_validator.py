"""Tests for workflow specification validator."""

from __future__ import annotations

import yaml

from pyarazzo.model.arazzo import ArazzoSpecification
from pyarazzo.spec.validator import WorkflowValidationVisitor


def test_validator_detects_missing_required_parameters() -> None:
    """Test that validator correctly identifies missing required parameters."""
    # Create a test specification with missing required parameters
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        spec_dict = yaml.safe_load(f)

    # Remove the page parameter from a step that requires it
    # The buy-available-pet workflow's find-pet step has page, but let's remove it
    for wf in spec_dict["workflows"]:
        if wf["workflowId"] == "buy-available-pet":
            # Remove the page parameter reference
            for step in wf["steps"]:
                if step["stepId"] == "find-pet":
                    # Filter out the page reference by keeping only non-reference params
                    step["parameters"] = [
                        p
                        for p in step["parameters"]
                        if "reference" not in p or "$components.parameters.page" not in str(p.get("reference", ""))
                    ]

    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    is_valid, errors, _ = validator.validate()
    # The spec should have missing required parameter errors
    assert is_valid is False
    # Should have errors about missing the page parameter
    assert any("missing required" in e for e in errors)


def test_validator_loads_openapi_spec() -> None:
    """Test that validator properly loads OpenAPI specifications."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
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
        spec_dict = yaml.safe_load(f)

    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    _, errors, _ = validator.validate()

    # Check for dependency-related errors, if any exist
    dependency_errors = [e for e in errors if "depends on" in e]
    # The test spec should not have broken dependencies
    assert len(dependency_errors) == 0


def test_validator_with_specific_workflow_id() -> None:
    """Test that validator can validate a specific workflow."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
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

        _, errors, _ = validator.validate()

        # Should not have error about workflow not found
        workflow_not_found = [e for e in errors if "not found in specification" in e]
        assert len(workflow_not_found) == 0


def test_validator_detects_nonexistent_workflow_id() -> None:
    """Test that validator detects when workflow filter doesn't match."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        spec_dict = yaml.safe_load(f)

    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
        workflow_id="nonexistent-workflow-id",
    )

    is_valid, errors, _ = validator.validate()

    # Should have error about workflow not found
    assert is_valid is False
    assert any("not found in specification" in e for e in errors)


def test_validator_url_resolution_with_relative_paths() -> None:
    """Test that validator resolves relative URLs correctly."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
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
        spec_dict = yaml.safe_load(f)

    # Modify spec to point to non-existent file
    spec_dict["sourceDescriptions"][0]["url"] = "/nonexistent/path/spec.json"
    spec = ArazzoSpecification(**spec_dict)

    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    _, errors, _ = validator.validate()

    # Should have errors about failing to load OpenAPI spec
    assert any("Failed to load OpenAPI spec" in e for e in errors)


def test_validator_detects_reusable_parameter_usage() -> None:
    """Test that validator detects when reusable objects are used for parameters."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        spec_dict = yaml.safe_load(f)

    # The spec already has reusable parameters in components (page, pageSize)
    # used by the buy-available-pet workflow
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    is_valid, _, _ = validator.validate()

    # Validator should process the spec without errors
    # (the spec is valid because reusable parameters are properly defined)
    assert is_valid is True


def test_validator_detects_invalid_reusable_reference() -> None:
    """Test that validator detects invalid reusable parameter references."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        spec_dict = yaml.safe_load(f)

    # Add components with valid parameter but reference invalid one
    spec_dict["components"] = {
        "parameters": {
            "validParam": {
                "name": "x-valid",
                "in": "header",
                "value": "ok",
            },
        },
    }

    # Modify first step to have a reusable reference to non-existent parameter
    if spec_dict["workflows"][0]["steps"]:
        spec_dict["workflows"][0]["steps"][0]["parameters"] = [
            {
                "reference": "#/components/parameters/nonExistentParam",
            },
        ]

    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    is_valid, errors, _ = validator.validate()

    # Should have errors about non-existent reusable parameter
    assert is_valid is False
    assert any("non-existent reusable parameter" in e for e in errors)


def test_validator_validates_reusable_with_components() -> None:
    """Test that validator correctly validates reusable parameter references when components exist."""
    with open("./tests/data/models/v1/pet-coupons-example.yaml") as f:
        spec_dict = yaml.safe_load(f)

    # The components already exist in the spec with page and pageSize parameters
    # Let's verify that reusable parameters from components are properly validated
    spec = ArazzoSpecification(**spec_dict)
    validator = WorkflowValidationVisitor(
        specification=spec,
        spec_path="./tests/data/models/v1/pet-coupons-example.yaml",
    )

    _, errors, _ = validator.validate()

    # Should not have errors about missing page or pageSize reusable parameters
    # since they are defined in components
    page_errors = [e for e in errors if "page" in e and "non-existent" in e]
    assert len(page_errors) == 0
    assert len(page_errors) == 0
