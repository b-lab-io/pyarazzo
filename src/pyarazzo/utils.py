"""Utils module to manipulate specifications.

This module provides utilities for:
- Loading specifications from local files or URLs
- Validating specifications against the Arazzo JSON schema
- Supporting both JSON and YAML formats
"""

import importlib.resources
import json
import logging
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from jsonschema import ValidationError, validate

from pyarazzo.config import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_YAML,
    HTTP_REQUEST_TIMEOUT,
)
from pyarazzo.exceptions import LoadError
from pyarazzo.exceptions import ValidationError as ArazzoValidationError

LOGGER = logging.getLogger(__name__)

# Load tge arazzo specification Schema for resources
with importlib.resources.files("pyarazzo").joinpath("schema.yaml").open("r", encoding="utf-8") as schema_file:
    schema = yaml.safe_load(schema_file)


def load_spec(path_or_url: str, correlation_id: str | None = None) -> dict:
    """Load a specification from file in the json or yaml format.

    Args:
        path_or_url (str): file path to the specification
        correlation_id (Optional[str]): correlation ID for tracing

    Raises:
        ArazzoValidationError: when specification fails schema validation

    Returns:
        dict: specification as a dict
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    document = load_data(path_or_url, correlation_id=correlation_id)
    try:
        validate(document, schema)
    except ValidationError as e:
        LOGGER.exception(f"[{correlation_id}] Schema validation failed for {path_or_url}")
        raise ArazzoValidationError(f"Invalid specification: {e.message}") from e
    return document


def load_from_url(url: str, correlation_id: str | None = None) -> dict:
    """Load data from an url supporting JSON and YAML formats.

    Args:
        url (str): url to a file.
        correlation_id (Optional[str]): correlation ID for tracing

    Raises:
        LoadError: when HTTP request fails or content type is unsupported.

    Returns:
        dict: Document as dict.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    try:
        response = requests.get(url, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        LOGGER.exception(f"[{correlation_id}] HTTP request failed for {url}")
        raise LoadError(f"Failed to load from URL {url}: {e!s}") from e

    content_type = response.headers.get("Content-Type", "")
    try:
        if CONTENT_TYPE_JSON in content_type or url.endswith(".json"):
            return response.json()

        if any(ct in content_type for ct in CONTENT_TYPE_YAML) or url.endswith((".yaml", ".yml")):
            return yaml.safe_load(response.text)

        raise LoadError(f"Unsupported content type: {content_type}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        LOGGER.exception(f"[{correlation_id}] Failed to parse response from {url}")
        raise LoadError(f"Failed to parse content from {url}: {e!s}") from e


def load_from_file(path: str, correlation_id: str | None = None) -> dict:
    """Load data from a local path supporting JSON and YAML formats.

    Args:
        path (str): Path to a local file.
        correlation_id (Optional[str]): correlation ID for tracing

    Raises:
        LoadError: when file cannot be read or content cannot be parsed.

    Returns:
        dict: Document as dict.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    try:
        if path.endswith(".json"):
            return json.loads(Path(path).read_text(encoding="utf-8"))
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        raise LoadError(f"Unsupported file extension: {path}")
    except FileNotFoundError as e:
        LOGGER.exception(f"[{correlation_id}] File not found: {path}")
        raise LoadError(f"File not found: {path}") from e
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        LOGGER.exception(f"[{correlation_id}] Failed to parse file: {path}")
        raise LoadError(f"Failed to parse file {path}: {e!s}") from e


def load_data(path_or_url: str, correlation_id: str | None = None) -> dict:
    """Load data from a local path or a URL, supporting JSON and YAML formats.

    Args:
        path_or_url (str): Path to a local file or a URL to a resource.
        correlation_id (Optional[str]): correlation ID for tracing

    Returns:
        dict: Data as a Python object (dict or list).

    Raises:
        LoadError: when data cannot be loaded or parsed.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    result = urlparse(path_or_url)
    if all([result.scheme, result.netloc]):
        return load_from_url(path_or_url, correlation_id=correlation_id)

    return load_from_file(path_or_url, correlation_id=correlation_id)


def schema_validation(spec: dict, correlation_id: str | None = None) -> None:
    """Validate the specification against the JSON Schema.

    Args:
        spec (dict): The specification to validate.
        correlation_id (Optional[str]): correlation ID for tracing

    Raises:
        ArazzoValidationError: when specification fails schema validation.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    try:
        validate(instance=spec, schema=schema)
        LOGGER.info(f"[{correlation_id}] Specification is valid")
    except ValidationError as exc:
        LOGGER.exception(f"[{correlation_id}] Specification validation failed")
        raise ArazzoValidationError(f"Invalid specification: {exc.message}") from exc
