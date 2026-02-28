"""Configuration and constants for pyarazzo.

This module contains all configurable constants used throughout the application,
including HTTP settings, PlantUML configuration, and Robot Framework keywords.
"""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class FileFormat(str, Enum):
    """Supported file formats."""

    JSON = "json"
    YAML = "yaml"

    @property
    def extensions(self) -> list[str]:
        """Get file extensions for this format."""
        return {
            FileFormat.JSON: [".json"],
            FileFormat.YAML: [".yaml", ".yml"],
        }[self]


class PlantUMLConfig(BaseModel):
    """Configuration for PlantUML diagram generation."""

    skin_param: str = "backgroundColor #EEEBDC"
    handwritten: bool = True


class RobotFrameworkConfig(BaseModel):
    """Configuration for Robot Framework keyword mappings."""

    keywords: Annotated[
        dict[str, str],
        Field(
            default_factory=lambda: {
                "log": "Log",
                "http_request": "RequestsLibrary.Request",
                "request": "RequestsLibrary.Request",
                "assert": "Should Be True",
                "sleep": "Sleep",
            }
        ),
    ]


class ContentTypeConfig(BaseModel):
    """Configuration for content type mappings."""

    model_config = ConfigDict(populate_by_name=True)

    json_type: Annotated[str, Field(alias="json")] = "application/json"
    yaml_types: Annotated[list[str], Field(alias="yaml")] = Field(
        default_factory=lambda: ["application/yaml", "text/yaml"]
    )


class AppConfig(BaseModel):
    """Main application configuration."""

    model_config = ConfigDict(frozen=True)

    http_request_timeout: int = 30
    plantuml: PlantUMLConfig = Field(default_factory=PlantUMLConfig)
    robot_framework: RobotFrameworkConfig = Field(default_factory=RobotFrameworkConfig)
    content_types: ContentTypeConfig = Field(default_factory=ContentTypeConfig)


# Default configuration instance
DEFAULT_CONFIG = AppConfig()

# Backward compatibility exports
HTTP_REQUEST_TIMEOUT = DEFAULT_CONFIG.http_request_timeout
PLANTUML_SETTINGS = {"skin_param": DEFAULT_CONFIG.plantuml.skin_param, "handwritten": DEFAULT_CONFIG.plantuml.handwritten}
ROBOT_STEP_KEYWORD_MAP = DEFAULT_CONFIG.robot_framework.keywords
CONTENT_TYPE_JSON = DEFAULT_CONFIG.content_types.json_type
CONTENT_TYPE_YAML = DEFAULT_CONFIG.content_types.yaml_types
