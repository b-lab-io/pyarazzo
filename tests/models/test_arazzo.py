"""Test Arazzo model conformity."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pyarazzo.model.arazzo import ArazzoSpecification


@pytest.mark.parametrize("path", [("./tests/data/models/v1/pet-coupons-example.yaml")])
def test_valid_spec(path: str) -> None:
    """Test the trasnformation from yaml/json to an object model."""
    spec_dict = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    spec = ArazzoSpecification(**spec_dict)
    assert spec is not None


@pytest.mark.parametrize("path", [("./tests/data/models/v1/invalid-arazzo-version.yaml")])
def test_invalid_spec(path: str) -> None:
    """Test invalid trasnformation from yaml/json to an object model."""
    spec_dict = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        ArazzoSpecification(**spec_dict)
