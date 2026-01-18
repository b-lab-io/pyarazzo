"""Configuration and constants for pyarazzo.

This module contains all configurable constants used throughout the application,
including HTTP settings, PlantUML configuration, and Robot Framework keywords.
"""

# HTTP request timeout in seconds
HTTP_REQUEST_TIMEOUT = 30

# PlantUML diagram settings
PLANTUML_SETTINGS = {
    "skin_param": "backgroundColor #EEEBDC",
    "handwritten": True,
}

# Robot Framework step keyword mappings
ROBOT_STEP_KEYWORD_MAP = {
    "log": "Log",
    "http_request": "RequestsLibrary.Request",
    "request": "RequestsLibrary.Request",
    "assert": "Should Be True",
    "sleep": "Sleep",
}

# Supported file formats
SUPPORTED_FORMATS = {
    "json": ".json",
    "yaml": [".yaml", ".yml"],
}

# Content type mappings
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_YAML = ["application/yaml", "text/yaml"]
