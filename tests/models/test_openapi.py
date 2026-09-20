"""Test for OpenAPI Loader functionality."""

import pytest

from pyarazzo.model.openapi import OpenApiLoader


@pytest.mark.parametrize("path", [("./tests/data/models/pet-coupons.openapi.yaml")])
def test_load_local_spec(path: str) -> None:
    """Test the transformation from yaml/json to an object model."""
    operations = OpenApiLoader.load(path)
    assert operations is not None
    assert len(operations.items()) == 11


def test_load_openapi_3_1_spec() -> None:
    """Test loading an OpenAPI 3.1 specification."""
    operations = OpenApiLoader.load("./tests/data/models/petstore-3.1.openapi.yaml")
    assert operations is not None
    assert "listPets" in operations
    assert "createPet" in operations
    assert "getPet" in operations
    assert "orderPet" in operations
    assert operations["getPet"].method.value == "get"
    assert operations["orderPet"].method.value == "post"


def test_operation_registry_with_source_name() -> None:
    """Test OperationRegistry indexing with source_name and flexible lookup."""
    from pyarazzo.model.openapi import OperationRegistry

    registry = OperationRegistry()
    registry.append("./tests/data/models/petstore-3.1.openapi.yaml", source_name="petstore-api")

    # Bare lookup
    assert "getPet" in registry
    assert registry["getPet"].operation_id == "getPet"
    assert registry.get("getPet") is not None

    # Qualified lookup
    qualified = "$sourceDescriptions.petstore-api.getPet"
    assert qualified in registry
    assert registry[qualified].operation_id == "getPet"
    assert registry.get(qualified) is not None

    # Fallback lookup (different or missing source name still resolves bare operation)
    other_qualified = "$sourceDescriptions.unknown-source.getPet"
    assert other_qualified in registry
    assert registry.get(other_qualified) is not None
    assert registry[other_qualified].operation_id == "getPet"

    # Non-existent operation
    assert "nonExistent" not in registry
    assert registry.get("nonExistent") is None
    with pytest.raises(KeyError):
        _ = registry["nonExistent"]
