"""pyarazzo package.

CLI to manipulate and build on top of the Arazzo Specification.

This package provides tools for:
- Loading and validating Arazzo workflow specifications
- Generating documentation from specifications
- Generating Robot Framework test cases from workflows
"""

from __future__ import annotations

from pyarazzo.exceptions import (
    ArazzoError,
    GenerationError,
    LoadError,
    SpecificationError,
    ValidationError,
)

__all__: list[str] = [
    "ArazzoError",
    "GenerationError",
    "LoadError",
    "SpecificationError",
    "ValidationError",
]
