"""Custom exceptions for pyarazzo."""


class ArazzoException(Exception):
    """Base exception for all pyarazzo errors."""


class SpecificationError(ArazzoException):
    """Raised when specification is invalid or malformed."""


class LoadError(ArazzoException):
    """Raised when specification cannot be loaded from source."""


class ValidationError(ArazzoException):
    """Raised when specification fails schema validation."""


class GenerationError(ArazzoException):
    """Raised when generation process fails."""
