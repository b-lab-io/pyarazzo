"""Test for OpenAPI Loader functionality."""

import pytest

from pyarazzo.model.openapi import OpenApiLoader


@pytest.mark.parametrize("path", [("./tests/data/models/pet-coupons.openapi.yaml")])
def test_load_local_spec(path: str) -> None:
    """Test the trasnformation from yaml/json to an object model."""
    operations = OpenApiLoader.load(path)
    assert operations is not None
    assert len(operations.items()) == 7
