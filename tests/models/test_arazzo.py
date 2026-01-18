"""Test Arazzo model conformity."""

import pytest
import yaml
from pydantic import ValidationError

from pyarazzo.model.arazzo import ArazzoSpecification


@pytest.mark.parametrize("path", [("./tests/data/models/v1/pet-coupons-example.yaml")])
def test_valid_spec(path: str) -> None:
    """Test the trasnformation from yaml/json to an object model."""
    with open(path) as file:
        spec_dict = yaml.safe_load(file)
    spec = ArazzoSpecification(**spec_dict)
    assert spec is not None


@pytest.mark.parametrize("path", [("./tests/data/models/v1/invalid-arazzo-version.yaml")])
def test_invalid_spec(path: str) -> None:
    """Test invalid trasnformation from yaml/json to an object model."""
    with open(path) as file:
        spec_dict = yaml.safe_load(file)
    with pytest.raises(ValidationError):
        ArazzoSpecification(**spec_dict)
