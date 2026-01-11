"""Concrete visitor implementation for generating Robot Framework test cases from Arazzo models.

This module provides a visitor that traverses an Arazzo specification and generates
Robot Framework test suites and test cases, enabling automated testing of workflows.
"""

import logging
from typing import Any

from robot.model import TestCase, TestSuite

from pyarazzo.config import ROBOT_STEP_KEYWORD_MAP
from pyarazzo.model.arazzo import (
    ArazzoSpecification,
    ArazzoVisitor,
    FailureActionObject,
    ParameterObject,
    PayloadReplacementObject,
    SourceDescriptionObject,
    Step,
    SuccessActionObject,
    Workflow,
)

LOGGER = logging.getLogger(__name__)


class ArazzoRobotFrameworkVisitor(ArazzoVisitor):
    """Concrete visitor that traverses an Arazzo model and generates a
    robot.api.TestSuite using the visitor pattern.
    """

    def __init__(self) -> None:
        """Initialize the visitor with empty test suites and keyword mappings."""
        self.suites: list[TestSuite] = []
        self.current_suite: TestSuite | None = None
        self.step_keyword_map = ROBOT_STEP_KEYWORD_MAP

    def visit_specification(self, spec: ArazzoSpecification):
        """Entry point: visit the root Arazzo specification."""
        # The didea here is we have fully described and extended WFs and we can process them
        # directly

        # Visit workflows
        if spec.workflows:
            for workflow in spec.workflows:
                self.visit_workflow(workflow)
                self.suites.append(self.current_suite)
                self.current_suite = None

    def visit_info(self, info: Any) -> None:
        """Visit Info element (metadata)."""
        if self.suite:
            self.suite.doc = info.summary or info.title

    def visit_components(self, components: Any) -> None:
        """Visit ComponentsObject (reusable definitions)."""
        # Components may define reusable parameters, request bodies, etc.
        # For now, we document them

    def visit_source_description(self, source: SourceDescriptionObject) -> None:
        """Visit SourceDescriptionObject."""

    def visit_workflow(self, workflow: Workflow) -> None:
        """Visit a Workflow and create a TestCase in the suite."""
        suite_name = workflow.workflow_id.root
        self.current_suite = TestSuite(suite_name)

        # Set documentation from summary
        if workflow.summary:
            self.current_suite.doc = workflow.summary

        # Visit steps in order
        if workflow.steps:
            for step in workflow.steps:
                step.accept(self)

    def visit_step(self, step: Step) -> None:
        """Visit a Step and add a keyword call to the test case."""
        if not self.current_suite:
            LOGGER.warning("No current suite to add steps to.")
            return

        # Extract step metadata
        step_name = step.step_id.root if step.step_id else "Unnamed Step"
        description = step.description or ""

        # Create a test case
        test = TestCase(name=step_name, parent=self.current_suite, doc=description)

        test.body.create_keyword()

        # Add steps to the test case
        test.body.create_step("Create Session", args=["test_session", "https://jsonplaceholder.typicode.com"])
        test.body.create_step("${response}=", args=["GET On Session", "test_session", "/posts/1"])
        test.body.create_step("Should Be Equal As Integers", args=["${response.status_code}", "200"])
        test.body.create_step("Delete All Sessions")

        # Create keyword call
        # test_case

        # #kw = test_case..create(keyword_name, args=args)
        # if description:
        #     kw.doc = description

        # Handle success/failure actions (nested workflows or criteria)
        if step.success_criteria:
            for criterion in step.success_criteria:
                self.visit_criterion_expression_type(criterion, test_case, "success")

        if step.on_failure:
            for action in step.on_failure:
                self.visit_failure_action(action, test_case)

        if step.on_success:
            for action in step.on_success:
                self.visit_success_action(action, test_case)

    def visit_parameter(self, param: ParameterObject) -> tuple:
        """Visit a Parameter and return (name, value) tuple."""
        name = param.name if hasattr(param, "name") else "param"
        value = getattr(param, "value", None)
        return (name, value)

    def visit_success_action(self, action: SuccessActionObject, test_case: Any) -> None:
        """Visit a SuccessActionObject (may reference another workflow or emit output)."""
        if not test_case:
            return

        # If action points to another workflow, add comment and reference
        if hasattr(action, "workflowId") and action.workflow_id:
            workflow_ref = str(action.workflow_id)
            kw = test_case.keywords.create("Log", args=[f"On success: continue to workflow {workflow_ref}"])

    def visit_failure_action(self, action: FailureActionObject, test_case: Any) -> None:
        """Visit a FailureActionObject (may emit output or exit)."""
        if not test_case:
            return

        if hasattr(action, "httpStatusCode"):
            code = action.httpStatusCode
            kw = test_case.keywords.create("Log", args=[f"On failure: HTTP {code}"])

    def visit_criterion_expression_type(self, criterion: Any, test_case: Any, ctype: str = "success") -> None:
        """Visit a CriterionObject and add assertion/condition checks."""
        if not test_case:
            return

        # Extract condition
        condition = getattr(criterion, "condition", None) or getattr(criterion, "expression", None)
        if condition:
            kw = test_case.keywords.create("Should Be True", args=[str(condition)])

    # Private helpers

    def _resolve_step_keyword(self, step: Step) -> str:
        """Determine the Robot Framework keyword name for a step.
        Uses operationId, stepType, or defaults to 'Log'.
        """
        # Try operationId first (often references an operation from OpenAPI)
        if hasattr(step, "operationId") and step.operation_id:
            op_id = str(step.operation_id).lower()
            if op_id in self.step_keyword_map:
                return self.step_keyword_map[op_id]
            return op_id.title()

        # Try requestBody presence -> assume HTTP request
        if hasattr(step, "requestBody") and step.request_body:
            return "RequestsLibrary.Request"

        # Default
        return "Log"

    def _resolve_step_arguments(self, step: Step) -> list[str]:
        """Extract arguments from a step (e.g., parameters, request body)."""
        args = []

        # Add parameters
        if hasattr(step, "parameters") and step.parameters:
            for param in step.parameters:
                name, value = self.visit_parameter(param)
                if value:
                    args.append(f"{name}={value}")

        # Add request body if present
        if hasattr(step, "requestBody") and step.request_body:
            body = step.request_body
            if hasattr(body, "payload"):
                args.append(str(body.payload))

        # Fallback: add step description as argument
        if not args and hasattr(step, "description"):
            desc = step.description
            if desc:
                args.append(desc)

        return args

    def visit_payload_replacement(self, instance: PayloadReplacementObject) -> None:
        """Visit PayloadReplacementObject."""

    def visit_reusable(self, reusable: Any) -> None:
        """Visit Reusable definitions."""

    def visit_source_description(self, source: SourceDescriptionObject) -> None:
        """Visit SourceDescriptionObject."""
