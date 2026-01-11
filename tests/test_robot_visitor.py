"""Tests for Robot Framework visitor."""

from __future__ import annotations

from pyarazzo.config import ROBOT_STEP_KEYWORD_MAP
from pyarazzo.robot.visitor import ArazzoRobotFrameworkVisitor


def test_robot_visitor_initialization() -> None:
    """Test that visitor initializes correctly."""
    visitor = ArazzoRobotFrameworkVisitor()
    assert visitor.suites == []
    assert visitor.current_suite is None
    assert visitor.step_keyword_map == ROBOT_STEP_KEYWORD_MAP


def test_robot_step_keyword_mapping() -> None:
    """Test that step keyword map is correctly initialized from config."""
    visitor = ArazzoRobotFrameworkVisitor()
    assert visitor.step_keyword_map["log"] == "Log"
    assert visitor.step_keyword_map["http_request"] == "RequestsLibrary.Request"
    assert visitor.step_keyword_map["assert"] == "Should Be True"
