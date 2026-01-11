"""Tests for exception handling."""

from __future__ import annotations

import pytest

from pyarazzo.exceptions import (
    ArazzoException,
    GenerationError,
    LoadError,
    SpecificationError,
    ValidationError,
)


def test_base_exception() -> None:
    """Test ArazzoException is raised and caught."""
    with pytest.raises(ArazzoException):
        raise ArazzoException("Test error")


def test_specification_error_inheritance() -> None:
    """Test SpecificationError inherits from ArazzoException."""
    with pytest.raises(ArazzoException):
        raise SpecificationError("Invalid spec")


def test_load_error_inheritance() -> None:
    """Test LoadError inherits from ArazzoException."""
    with pytest.raises(ArazzoException):
        raise LoadError("Failed to load")


def test_validation_error_inheritance() -> None:
    """Test ValidationError inherits from ArazzoException."""
    with pytest.raises(ArazzoException):
        raise ValidationError("Validation failed")


def test_generation_error_inheritance() -> None:
    """Test GenerationError inherits from ArazzoException."""
    with pytest.raises(ArazzoException):
        raise GenerationError("Generation failed")


def test_exception_message_preservation() -> None:
    """Test exception messages are preserved."""
    msg = "Custom error message"
    try:
        raise LoadError(msg)
    except LoadError as e:
        assert str(e) == msg
