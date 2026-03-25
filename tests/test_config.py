"""Tests for the config module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarazzo.config import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_YAML,
    DEFAULT_CONFIG,
    HTTP_REQUEST_TIMEOUT,
    AppConfig,
    ContentTypeConfig,
    FileFormat,
    PlantUMLConfig,
)


def test_file_format_enum_json() -> None:
    """Test FileFormat enum for JSON."""
    assert FileFormat.JSON.value == "json"
    assert FileFormat.JSON.extensions == [".json"]


def test_file_format_enum_yaml() -> None:
    """Test FileFormat enum for YAML."""
    assert FileFormat.YAML.value == "yaml"
    assert FileFormat.YAML.extensions == [".yaml", ".yml"]


def test_plantuml_config_defaults() -> None:
    """Test PlantUMLConfig has correct defaults."""
    config = PlantUMLConfig()
    assert config.skin_param == "backgroundColor #EEEBDC"
    assert config.handwritten is True


def test_plantuml_config_custom_values() -> None:
    """Test PlantUMLConfig with custom values."""
    config = PlantUMLConfig(skin_param="backgroundColor #FFFFFF", handwritten=False)
    assert config.skin_param == "backgroundColor #FFFFFF"
    assert config.handwritten is False


def test_content_type_config_defaults() -> None:
    """Test ContentTypeConfig has correct defaults."""
    config = ContentTypeConfig()
    assert config.json_type == "application/json"
    assert "application/yaml" in config.yaml_types
    assert "text/yaml" in config.yaml_types


def test_content_type_config_alias_support() -> None:
    """Test ContentTypeConfig supports field aliases."""
    # Using aliases to construct
    config = ContentTypeConfig(json_type="custom/json", yaml_types=["my/yaml"])  # type: ignore[call-arg]
    assert config.json_type == "custom/json"
    assert config.yaml_types == ["my/yaml"]


def test_app_config_defaults() -> None:
    """Test AppConfig has correct defaults."""
    config = AppConfig()
    assert config.http_request_timeout == 30
    assert isinstance(config.plantuml, PlantUMLConfig)
    assert isinstance(config.content_types, ContentTypeConfig)


def test_app_config_frozen() -> None:
    """Test that AppConfig is frozen (immutable)."""
    config = DEFAULT_CONFIG
    with pytest.raises(ValidationError):
        config.http_request_timeout = 60


def test_default_config_instance() -> None:
    """Test DEFAULT_CONFIG is properly initialized."""
    assert DEFAULT_CONFIG.http_request_timeout == 30
    assert DEFAULT_CONFIG.plantuml.skin_param == "backgroundColor #EEEBDC"


def test_backward_compatibility_http_timeout() -> None:
    """Test backward compatibility for HTTP_REQUEST_TIMEOUT."""
    assert HTTP_REQUEST_TIMEOUT == 30
    assert DEFAULT_CONFIG.http_request_timeout == HTTP_REQUEST_TIMEOUT


def test_backward_compatibility_content_types() -> None:
    """Test backward compatibility for content type configs."""
    assert CONTENT_TYPE_JSON == "application/json"
    assert "application/yaml" in CONTENT_TYPE_YAML
    assert "text/yaml" in CONTENT_TYPE_YAML
