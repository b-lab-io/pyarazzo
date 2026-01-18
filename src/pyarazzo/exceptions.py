"""Custom exceptions for pyarazzo."""


class ArazzoError(Exception):
    """Base exception for all pyarazzo errors."""


class SpecificationError(ArazzoError):
    """Raised when specification is invalid or malformed."""


class LoadError(ArazzoError):
    """Raised when specification cannot be loaded from source."""


class ValidationError(ArazzoError):
    """Raised when specification fails schema validation."""


class GenerationError(ArazzoError):
    """Raised when generation process fails."""
