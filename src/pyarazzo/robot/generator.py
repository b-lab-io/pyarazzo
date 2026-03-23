"""Robot Framework test generation from Arazzo specifications.

This module provides a visitor for generating executable Robot Framework test scripts
from Arazzo specifications, following Robot Framework best practices.
"""

import logging
import os
import uuid

from pyarazzo.model.arazzo import (
    ArazzoSpecification,
    ArazzoVisitor,
    ComponentsObject,
    CriterionExpressionTypeObject,
    Info,
    ParameterObject,
    PayloadReplacementObject,
    ReusableObject,
    SourceDescriptionObject,
    SourceType,
    Step,
    Workflow,
)
from pyarazzo.model.openapi import ApiOperation, OperationRegistry

LOGGER = logging.getLogger(__name__)


class RobotFrameworkGeneratorVisitor(ArazzoVisitor):
    """Visitor that generates executable Robot Framework test files from Arazzo specifications."""

    # Robot Framework settings
    DEFAULT_DOCUMENTATION = "Automated API workflow tests generated from Arazzo specification"
    DEFAULT_LIBRARY = "RequestsLibrary"
    BUILTIN_LIBRARY = "BuiltIn"

    def __init__(self, output_dir: str, correlation_id: str | None = None) -> None:
        """Initialize the Robot Framework generator.

        Args:
            output_dir (str): Directory to write generated test files
            correlation_id (Optional[str]): Correlation ID for tracing
        """
        self.output_dir = output_dir
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.operation_registry = OperationRegistry(operations={})
        self.content = ""
        self.spec_info: Info | None = None
        self.current_workflow: Workflow | None = None
        os.makedirs(output_dir, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Convert a name to valid Robot Framework test/keyword name format.

        Args:
            name (str): Input name

        Returns:
            str: Sanitized name for Robot Framework
        """
        return name.replace(" ", "_").replace("-", "_")

    def _generate_test_header(self, spec: ArazzoSpecification) -> str:
        """Generate Robot Framework file header with settings.

        Args:
            spec (ArazzoSpecification): The specification

        Returns:
            str: Robot Framework settings section
        """
        doc = spec.info.description or self.DEFAULT_DOCUMENTATION
        content = "*** Settings ***\n"
        content += f"Documentation    {doc}\n"
        content += f"Library    {self.DEFAULT_LIBRARY}\n"
        content += f"Library    {self.BUILTIN_LIBRARY}\n"
        content += "\n"
        return content

    def _generate_variables_section(self, workflow: Workflow) -> str:
        """Generate Variables section for workflow inputs.

        Args:
            workflow (Workflow): The workflow

        Returns:
            str: Variables section content
        """
        content = "*** Variables ***\n"
        content += "${BASE_URL}    http://localhost:8080\n"
        content += "${TIMEOUT}     10s\n"

        # Add workflow-specific variables
        if hasattr(workflow, "inputs") and workflow.inputs:
            content += "# Workflow inputs\n"
            # Variables will be populated at runtime from inputs

        content += "\n"
        return content

    def _generate_keywords_section(self) -> str:
        """Generate Custom Keywords section.

        Returns:
            str: Keywords section content
        """
        content = "*** Keywords ***\n"
        content += "Setup API Connection\n"
        content += "    [Documentation]    Initialize connection to API\n"
        content += "    Create Session    api_session    ${BASE_URL}\n"
        content += "\n"

        content += "Teardown API Connection\n"
        content += "    [Documentation]    Clean up API connection\n"
        content += "    Delete All Sessions\n"
        content += "\n"

        return content

    def _generate_test_case(self, workflow: Workflow) -> str:
        """Generate a test case for a workflow.

        Args:
            workflow (Workflow): The workflow to convert to a test case

        Returns:
            str: Test case content
        """
        test_name = self._sanitize_name(workflow.workflow_id)
        content = f"{test_name}\n"

        # Documentation
        doc = workflow.description or workflow.workflow_id
        content += f"    [Documentation]    {doc}\n"

        # Setup and Teardown
        content += "    [Setup]    Setup API Connection\n"
        content += "    [Teardown]    Teardown API Connection\n"

        # Tags
        content += "    [Tags]    API    Workflow\n"
        content += "\n"

        # Test steps
        for idx, step in enumerate(workflow.steps, 1):
            step_name = self._sanitize_name(step.step_id)

            # Log the step
            content += f"    Log    Executing step {idx}: {step.step_id}\n"

            if step.operation_id is not None:
                # Handle API operation
                if step.operation_id in self.operation_registry.operations:
                    operation: ApiOperation = self.operation_registry.operations[step.operation_id]
                    content += self._generate_http_request(operation, step)
                else:
                    # Generate placeholder HTTP call even without full operation metadata
                    content += self._generate_placeholder_http_call(step)

            if hasattr(step, "success_criteria") and step.success_criteria:
                # Handle success criteria as assertions
                content += self._generate_assertions(step)

        content += "\n"
        return content

    def _generate_http_request(self, operation: ApiOperation, step: Step) -> str:
        """Generate HTTP request keyword call.

        Args:
            operation (ApiOperation): The API operation to call
            step (Step): The workflow step

        Returns:
            str: HTTP request keyword call
        """
        content = f"    # Call {operation.service_name} {operation.method.upper()} {operation.path}\n"

        method = operation.method.value.upper() if operation.method else "GET"

        # Extract parameters from step
        query_params = []
        path_params = {}
        request_body = None

        if hasattr(step, "parameters") and step.parameters:
            for param in step.parameters:
                param_in = None
                param_name = param.name
                param_value = param.value if hasattr(param, "value") else f"${{{param_name}}}"

                if hasattr(param, "param_in"):
                    param_in = param.param_in
                elif hasattr(param, "in_"):
                    param_in = param.in_

                if param_in == "query":
                    query_params.append((param_name, param_value))
                elif param_in == "path":
                    path_params[param_name] = param_value

        # Build endpoint path with path parameters substitution
        endpoint = operation.path
        for name, value in path_params.items():
            endpoint = endpoint.replace(f"{{{name}}}", str(value))

        # Build the HTTP request call
        if method.upper() in ["GET", "DELETE", "HEAD"]:
            if query_params:
                # Build query string
                query_string = "&".join([f"{name}={value}" for name, value in query_params])
                content += (
                    f"    ${{response}}    {method} Request    "
                    f"api_session    {endpoint}?{query_string}\n"
                )
            else:
                content += (
                    f"    ${{response}}    {method} Request    "
                    f"api_session    {endpoint}\n"
                )
        elif query_params:
            # Build query string for POST/PUT/PATCH
            query_string = "&".join([f"{name}={value}" for name, value in query_params])
            content += (
                f"    ${{response}}    {method} Request    "
                f"api_session    {endpoint}?{query_string}    expected_status=any\n"
            )
        else:
            content += (
                f"    ${{response}}    {method} Request    "
                f"api_session    {endpoint}    expected_status=any\n"
            )

        content += "    Log    Response Status: ${response.status_code}\n\n"
        return content

    def _generate_placeholder_http_call(self, step: Step) -> str:
        """Generate a placeholder HTTP call when operation metadata is unavailable.

        Args:
            step (Step): The workflow step

        Returns:
            str: Placeholder HTTP call
        """
        content = f"    # TODO: Configure endpoint for operation {step.operation_id}\n"

        # Extract parameters from step
        query_params = []
        path_params = []
        request_body = None

        if hasattr(step, "parameters") and step.parameters:
            for param in step.parameters:
                if hasattr(param, "param_in"):
                    if param.param_in == "query":
                        query_params.append((param.name, param.value if hasattr(param, "value") else f"${{{param.name}}}"))
                    elif param.param_in == "path":
                        path_params.append((param.name, param.value if hasattr(param, "value") else f"${{{param.name}}}"))
                elif hasattr(param, "in_"):
                    if param.in_ == "query":
                        query_params.append((param.name, param.value if hasattr(param, "value") else f"${{{param.name}}}"))
                    elif param.in_ == "path":
                        path_params.append((param.name, param.value if hasattr(param, "value") else f"${{{param.name}}}"))

        if hasattr(step, "request_body") and step.request_body:
            request_body = step.request_body

        # Build endpoint path with path parameters
        endpoint = "/api/endpoint"
        if path_params:
            for name, value in path_params:
                endpoint += f"/{{{value}}}"

        # Generate the HTTP call
        method = "Get Request"

        if query_params:
            # Build query string
            query_string = "&".join([f"{name}={value}" for name, value in query_params])
            content += f"    ${{response}}    {method}    api_session    {endpoint}?{query_string}\n"
        elif request_body:
            content += f"    ${{response}}    Post Request    api_session    {endpoint}    json=${{request_body}}\n"
        else:
            content += f"    ${{response}}    {method}    api_session    {endpoint}\n"

        content += "    Log    Response Status: ${response.status_code}\n"
        content += "    Should Not Be Equal    ${response.status_code}    500\n\n"
        return content

    def _generate_assertions(self, step: Step) -> str:
        """Generate assertions from success criteria.

        Args:
            step (Step): The step with success criteria

        Returns:
            str: Assertion keyword calls
        """
        content = "    # Verify success criteria\n"

        if hasattr(step, "success_criteria") and step.success_criteria:
            for criterion in step.success_criteria:
                if hasattr(criterion, "condition"):
                    content += f"    Should Be True    {criterion.condition}\n"
        else:
            # Default assertion: Status code should be 2xx
            content += "    Should Be True    ${response.status_code} < 300\n"

        content += "\n"
        return content

    def visit_specification(self, spec: ArazzoSpecification) -> None:
        """Visit the Arazzo specification and generate test file.

        Args:
            spec (ArazzoSpecification): The specification to process
        """
        LOGGER.info(f"[{self.correlation_id}] Starting Robot Framework test generation")
        self.spec_info = spec.info

        # Process source descriptions to load operations
        for source_description in spec.source_descriptions:
            source_description.accept(self)

        # Generate test suite file
        self._generate_test_suite(spec)

    def _generate_test_suite(self, spec: ArazzoSpecification) -> None:
        """Generate a complete test suite file for all workflows.

        Args:
            spec (ArazzoSpecification): The specification
        """
        content = self._generate_test_header(spec)
        content += self._generate_variables_section(
            spec.workflows[0] if spec.workflows else None,
        ) if spec.workflows else ""
        content += self._generate_keywords_section()

        # Generate test cases for all workflows
        content += "*** Test Cases ***\n"
        for workflow in spec.workflows:
            content += self._generate_test_case(workflow)

        # Write to file
        suite_name = self._sanitize_name(spec.info.title.lower())
        output_file = os.path.join(self.output_dir, f"{suite_name}.robot")

        with open(output_file, "w") as f:
            f.write(content)

        LOGGER.info(f"[{self.correlation_id}] Generated Robot Framework test suite: {output_file}")

    def visit_workflow(self, workflow: Workflow) -> None:
        """Visit a workflow (currently handled in test suite generation).

        Args:
            workflow (Workflow): The workflow
        """
        self.current_workflow = workflow

    def visit_step(self, step: Step) -> None:
        """Visit a step (handled within test case generation).

        Args:
            step (Step): The step
        """

    def visit_info(self, instance: Info) -> None:
        """Visit metadata information.

        Args:
            instance (Info): The metadata
        """

    def visit_source_description(self, instance: SourceDescriptionObject) -> None:
        """Visit a source description and load operations.

        Args:
            instance (SourceDescriptionObject): The source description
        """
        if instance.type != SourceType.openapi:
            raise ValueError(f"Unsupported source type {instance.type} for source {instance.name}")

        LOGGER.info(f"[{self.correlation_id}] Loading operations from {instance.url}")
        try:
            self.operation_registry.append(openapi_spec=instance.url)
        except Exception as e:
            LOGGER.warning(
                f"[{self.correlation_id}] Could not load OpenAPI spec from {instance.url}: {e}. "
                "Continuing without API operations.",
            )

    def visit_criterion_expression_type(self, instance: CriterionExpressionTypeObject) -> None:
        """Visit a criterion expression.

        Args:
            instance (CriterionExpressionTypeObject): The criterion expression
        """

    def visit_reusable(self, instance: ReusableObject) -> None:
        """Visit a reusable object.

        Args:
            instance (ReusableObject): The reusable object
        """

    def visit_parameter(self, instance: ParameterObject) -> None:
        """Visit a parameter.

        Args:
            instance (ParameterObject): The parameter
        """

    def visit_payload_replacement(self, instance: PayloadReplacementObject) -> None:
        """Visit a payload replacement.

        Args:
            instance (PayloadReplacementObject): The payload replacement
        """

    def visit_components(self, instance: ComponentsObject) -> None:
        """Visit components object.

        Args:
            instance (ComponentsObject): The components object
        """
