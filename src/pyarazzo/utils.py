"""Utils module to manipulate specification."""

import importlib.resources
import json
import logging
from urllib.parse import urlparse

import click
import requests
import yaml
from jsonschema import ValidationError, validate

LOGGER = logging.getLogger(__name__)

# Load tge arazzo specification Schema for resources
with importlib.resources.open_text("pyarazzo", "schema.yaml") as schema_file:
    schema = yaml.safe_load(schema_file)


def load_spec(path_or_url: str) -> dict:
    """Load a specification from file in the json or yaml format.

    Args:
        path_or_url (str): file path to the specification

    Raises:
        click.ClickException: unsupported file format

    Returns:
        dict: specification as a dict
    """
    document = load_data(path_or_url)
    validate(document, schema)
    return document


def load_from_url(url: str) -> dict:
    """Load data from an url supporting JSON and YAML formats.

    Args:
        url (str): url to a file.

    Raises:
        ValueError: unsupported file extension.

    Returns:
        dict: Document as dict.
    """
    # It's a URL, fetch and load data
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # Raise an exception for HTTP errors
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type or url.endswith(".json"):
        return response.json()

    if (
        "application/yaml" in content_type
        or "text/yaml" in content_type
        or url.endswith((".yaml", ",yml"))
    ):
        return yaml.safe_load(response.text)

    raise ValueError(f"Unsupported content type: {content_type}")


def load_from_file(path: str) -> dict:
    """Load data from a local path supporting JSON and YAML formats.

    Args:
        path (str): Path to a local file.

    Raises:
        ValueError: unsupported file extension.

    Returns:
        dict: Document as dict.
    """
    # Assume it's a local file path and load data
    if path.endswith(".json"):
        with open(path) as file:
            return json.load(file)
    elif path.endswith((".yaml", ".yml")):
        with open(path) as file:
            return yaml.safe_load(file)
    else:
        raise ValueError(f"Unsupported file extension: {path}")


def load_data(path_or_url: str) -> dict:
    """Load data from a local path or a URL, supporting JSON and YAML formats.

    :param path_or_url: Path to a local file or a URL to a resource.
    :return: Data as a Python object (dict or list).
    """
    try:
        # Check if it's a URL
        result = urlparse(path_or_url)
        if all([result.scheme, result.netloc]):
            return load_from_url(path_or_url)

        return load_from_file(path_or_url)
    except requests.RequestException as e:
        LOGGER.exception("HTTP Request error")
        raise click.Abort from e
    except FileNotFoundError as e:
        LOGGER.exception(f"File not found: {path_or_url}")
        raise click.Abort from e
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        LOGGER.exception("Data decoding error")
        raise click.Abort from e
    except ValueError as e:
        LOGGER.exception("Value error")
        raise click.Abort from e
    except Exception as e:
        LOGGER.exception("Unecptected error")
        raise click.Abort from e


def schema_validation(spec: dict) -> None:
    """Validate the specification against the Json Schema."""
    try:
        validate(instance=spec, schema=schema)
        click.echo("Specification file is valid.")
    except ValidationError as exc:
        raise click.ClickException(
            f"Unsupported file type for specification file: {spec}",
        ) from exc
