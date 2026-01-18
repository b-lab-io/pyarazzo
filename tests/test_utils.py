"""Test utils package."""

import json
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
import yaml

from pyarazzo import utils
from pyarazzo.exceptions import LoadError, ValidationError


@pytest.fixture
def valid_json_file() -> Generator[str, Any]:
    """Generate a valid Json file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=".") as tmp:
        json.dump({"key": "value"}, tmp)
        tmp.flush()
        yield tmp.name


@pytest.fixture
def valid_yaml_file() -> Generator[str, Any]:
    """Generate a valid yaml file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", dir=".") as tmp:
        yaml.dump({"key": "value"}, tmp)
        tmp.flush()
        yield tmp.name


def test_load_spec_valid_json() -> None:
    """Read the test method name."""
    spec = utils.load_spec("./tests/data/test_utils_valid.json")
    assert spec is not None
    assert isinstance(spec, dict)


def test_load_spec_valid_yaml() -> None:
    """Read the test method name."""
    spec = utils.load_spec("./tests/data/test_utils_valid.yaml")
    assert spec is not None
    assert isinstance(spec, dict)


def test_load_spec_invalid_file_format() -> None:
    """Read the test method name."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", dir=".") as tmp:
        tmp.write("Invalid content")
        tmp.flush()
        with pytest.raises(LoadError):
            utils.load_spec(tmp.name)


@patch("pyarazzo.utils.requests.get")
def test_load_from_url_valid_json(mock_get: Any) -> None:
    """Read the test method name."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response
    spec = utils.load_from_url("https://example.com/spec.json")
    assert spec == {"key": "value"}


@patch("pyarazzo.utils.requests.get")
def test_load_from_url_valid_yaml(mock_get: Any) -> None:
    """Read the test method name."""
    mock_response = MagicMock()
    mock_response.text = "key: value"
    mock_response.headers = {"Content-Type": "application/yaml"}
    mock_get.return_value = mock_response
    spec = utils.load_from_url("https://example.com/spec.yaml")
    assert spec == {"key": "value"}


@patch("pyarazzo.utils.requests.get")
def test_load_from_url_unsupported_content_type(mock_get: Any) -> None:
    """Read the test method name."""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_get.return_value = mock_response
    with pytest.raises(LoadError):
        utils.load_from_url("https://example.com/spec.txt")


def test_load_from_file_valid_json(valid_json_file: Any) -> None:
    """Read the test method name."""
    spec = utils.load_from_file(valid_json_file)
    assert spec == {"key": "value"}


def test_load_from_file_valid_yaml(valid_yaml_file: Any) -> None:
    """Read the test method name."""
    spec = utils.load_from_file(valid_yaml_file)
    assert spec == {"key": "value"}


def test_load_from_file_unsupported_extension() -> None:
    """Read the test method name."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", dir=".") as tmp:
        tmp.write("Invalid content")
        tmp.flush()
        with pytest.raises(LoadError):
            utils.load_from_file(tmp.name)


def test_load_data_valid_local_file(valid_json_file: Any) -> None:
    """Read the test method name."""
    spec = utils.load_data(valid_json_file)
    assert spec == {"key": "value"}


@patch("pyarazzo.utils.requests.get")
def test_load_data_valid_url(mock_get: Any) -> None:
    """Read the test method name."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response
    spec = utils.load_data("https://example.com/spec.json")
    assert spec == {"key": "value"}


def test_schema_validation_valid_spec() -> None:
    """Read the test method name."""
    with open("./tests/data/test_utils_valid.json") as file:
        spec = json.load(file)
    utils.schema_validation(spec)  # Should not raise an exception


def test_schema_validation_invalid_spec() -> None:
    """Read the test method name."""
    spec = {"invalid_key": "value"}
    with pytest.raises(ValidationError):
        utils.schema_validation(spec)


@patch("pyarazzo.utils.requests.get")
def test_load_data_url_http_error(mock_get: Any) -> None:
    """Read the test method name."""
    mock_get.side_effect = requests.RequestException("HTTP Error")
    with pytest.raises(LoadError):
        utils.load_data("https://example.com/spec.json")


def test_load_data_invalid_local_file() -> None:
    """Read the test method name."""
    with pytest.raises(LoadError):
        utils.load_data("non_existent_file.json")


def test_load_data_invalid_json(valid_json_file: Any) -> None:
    """Read the test method name."""
    with open(valid_json_file, "w") as f:
        f.write("Invalid JSON")
    with pytest.raises(LoadError):
        utils.load_data(valid_json_file)
