"""Utils module to manipulate specifications.

This module provides utilities for:
- Loading specifications from local files or URLs
- Validating specifications against the Arazzo JSON schema
- Supporting both JSON and YAML formats
"""

import importlib.resources
import json
import logging
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
with importlib.resources.files("pyarazzo").joinpath("schema.yaml").open("r") as schema_file:
    schema = yaml.safe_load(schema_file)


def load_spec(path_or_url: str) -> dict:
    """Load a specification from file in the json or yaml format.

    Args:
        path_or_url (str): file path to the specification

    Raises:
        ArazzoValidationError: when specification fails schema validation

    Returns:
        dict: specification as a dict
    """
    document = load_data(path_or_url)
    try:
        validate(document, schema)
    except ValidationError as e:
        LOGGER.exception(f"Schema validation failed for {path_or_url}")
        raise ArazzoValidationError(f"Invalid specification: {e.message}") from e
    return document


def load_from_url(url: str) -> dict:
    """Load data from an url supporting JSON and YAML formats.

    Args:
        url (str): url to a file.

    Raises:
        LoadError: when HTTP request fails or content type is unsupported.

    Returns:
        dict: Document as dict.
    """
    try:
        response = requests.get(url, timeout=HTTP_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        LOGGER.exception(f"HTTP request failed for {url}")
        raise LoadError(f"Failed to load from URL {url}: {e!s}") from e

    content_type = response.headers.get("Content-Type", "")
    try:
        if CONTENT_TYPE_JSON in content_type or url.endswith(".json"):
            return response.json()

        if any(ct in content_type for ct in CONTENT_TYPE_YAML) or url.endswith((".yaml", ".yml")):
            return yaml.safe_load(response.text)

        raise LoadError(f"Unsupported content type: {content_type}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        LOGGER.exception(f"Failed to parse response from {url}")
        raise LoadError(f"Failed to parse content from {url}: {e!s}") from e


def load_from_file(path: str) -> dict:
    """Load data from a local path supporting JSON and YAML formats.

    Args:
        path (str): Path to a local file.

    Raises:
        LoadError: when file cannot be read or content cannot be parsed.

    Returns:
        dict: Document as dict.
    """
    try:
        if path.endswith(".json"):
            with open(path) as file:
                return json.load(file)
        elif path.endswith((".yaml", ".yml")):
            with open(path) as file:
                return yaml.safe_load(file)
        else:
            raise LoadError(f"Unsupported file extension: {path}")
    except FileNotFoundError as e:
        LOGGER.exception(f"File not found: {path}")
        raise LoadError(f"File not found: {path}") from e
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        LOGGER.exception(f"Failed to parse file: {path}")
        raise LoadError(f"Failed to parse file {path}: {e!s}") from e


def load_data(path_or_url: str) -> dict:
    """Load data from a local path or a URL, supporting JSON and YAML formats.

    Args:
        path_or_url (str): Path to a local file or a URL to a resource.

    Returns:
        dict: Data as a Python object (dict or list).

    Raises:
        LoadError: when data cannot be loaded or parsed.
    """
    result = urlparse(path_or_url)
    if all([result.scheme, result.netloc]):
        return load_from_url(path_or_url)

    return load_from_file(path_or_url)


def schema_validation(spec: dict) -> None:
    """Validate the specification against the JSON Schema.

    Args:
        spec (dict): The specification to validate.

    Raises:
        ArazzoValidationError: when specification fails schema validation.
    """
    try:
        validate(instance=spec, schema=schema)
        LOGGER.info("Specification is valid")
    except ValidationError as exc:
        LOGGER.exception("Specification validation failed")
        raise ArazzoValidationError(f"Invalid specification: {exc.message}") from exc
