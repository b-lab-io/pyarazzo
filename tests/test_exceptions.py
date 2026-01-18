"""Tests for exception handling."""

from __future__ import annotations

import pytest

from pyarazzo.exceptions import (
    ArazzoError,
    GenerationError,
    LoadError,
    SpecificationError,
    ValidationError,
)


def test_base_exception() -> None:
    """Test ArazzoError is raised and caught."""
    with pytest.raises(ArazzoError):
        raise ArazzoError("Test error")


def test_specification_error_inheritance() -> None:
    """Test SpecificationError inherits from ArazzoError."""
    with pytest.raises(ArazzoError):
        raise SpecificationError("Invalid spec")


def test_load_error_inheritance() -> None:
    """Test LoadError inherits from ArazzoError."""
    with pytest.raises(ArazzoError):
        raise LoadError("Failed to load")


def test_validation_error_inheritance() -> None:
    """Test ValidationError inherits from ArazzoError."""
    with pytest.raises(ArazzoError):
        raise ValidationError("Validation failed")


def test_generation_error_inheritance() -> None:
    """Test GenerationError inherits from ArazzoError."""
    with pytest.raises(ArazzoError):
        raise GenerationError("Generation failed")


def test_exception_message_preservation() -> None:
    """Test exception messages are preserved."""
    msg = "Custom error message"
    with pytest.raises(LoadError) as exc_info:
        raise LoadError(msg)
    assert str(exc_info.value) == msg
