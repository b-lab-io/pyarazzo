"""Workflow validation logic for Arazzo specifications."""

from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any

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


class ValidationError(Exception):
    """Raised when a validation error occurs."""



class WorkflowValidationVisitor(ArazzoVisitor):
    """Visitor for validating workflows against OpenAPI specifications."""

    def __init__(
        self,
        specification: ArazzoSpecification,
        spec_path: str | None = None,
        workflow_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize the workflow validation visitor.

        Args:
            specification: The Arazzo specification to validate
            spec_path: Path to the specification file (used to resolve relative URLs)
            workflow_id: Optional workflow ID to validate (if None, validates all)
            correlation_id: Correlation ID for tracing
        """
        self.specification = specification
        self.spec_path = spec_path
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.operation_registry = OperationRegistry(operations={})
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.initialization_errors: list[str] = []
        self._load_operations()

    def _load_operations(self) -> None:
        """Load all operations from source descriptions."""
        for source in self.specification.source_descriptions:
            if source.type == SourceType.openapi:
                try:
                    # Resolve relative URLs based on spec file location
                    url = self._resolve_source_url(source.url)
                    self.operation_registry.append(openapi_spec=url)
                except OSError as e:
                    self.initialization_errors.append(
                        f"Failed to load OpenAPI spec '{source.url}' from source '{source.name}': {e}",
                    )

    def _resolve_source_url(self, url: str) -> str:
        """Resolve a source URL relative to the specification file.

        Args:
            url: The URL to resolve (can be absolute or relative)

        Returns:
            The resolved URL
        """
        # If URL is remote, return as-is
        if url.startswith(("http://", "https://", "ftp://")):
            return url

        # If we have a spec path and the URL is relative, resolve it
        if self.spec_path and not os.path.isabs(url):
            spec_dir = os.path.dirname(os.path.abspath(self.spec_path))
            return os.path.normpath(os.path.join(spec_dir, url))

        return url

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Validate the specification.

        Returns:
            Tuple of (is_valid, errors, warnings) where is_valid is True if no errors
        """
        self.errors = []
        self.warnings = []

        # Include initialization errors (e.g., failed to load OpenAPI specs)
        self.errors.extend(self.initialization_errors)

        # Accept the specification with this visitor
        self.visit_specification(self.specification)

        return len(self.errors) == 0, self.errors, self.warnings

    def visit_specification(self, spec: ArazzoSpecification) -> None:
        """Visit the specification and validate workflows.

        Args:
            spec: The Arazzo specification
        """
        LOGGER.info(f"[{self.correlation_id}] Validating specification: {spec.info.title}")

        # Validate that required source descriptions exist
        if not spec.source_descriptions:
            self.errors.append("No source descriptions defined in specification")
            return

        # Validate workflows
        workflows_to_validate = spec.workflows
        if self.workflow_id:
            workflows_to_validate = [
                w for w in spec.workflows if str(w.workflow_id) == self.workflow_id
            ]
            if not workflows_to_validate:
                self.errors.append(f"Workflow '{self.workflow_id}' not found in specification")
                return

        for workflow in workflows_to_validate:
            workflow.accept(self)

    def visit_workflow(self, workflow: Workflow) -> None:
        """Validate a workflow.

        Args:
            workflow: The workflow to validate
        """
        LOGGER.info(
            f"[{self.correlation_id}] Validating workflow: {workflow.workflow_id}",
        )

        # Validate workflow dependencies
        if workflow.depends_on:
            for dep_id in workflow.depends_on:
                if not any(w.workflow_id == dep_id for w in self.specification.workflows):
                    self.errors.append(
                        f"Workflow '{workflow.workflow_id}' depends on non-existent workflow '{dep_id}'",
                    )

        # Validate steps
        if not workflow.steps:
            self.errors.append(f"Workflow '{workflow.workflow_id}' has no steps")
            return

        for step in workflow.steps:
            step.accept(self)

    def visit_step(self, step: Step) -> None:
        """Validate a step.

        Args:
            step: The step to validate
        """
        step_id = str(step.step_id)

        # Check that step has at least one of: operationId, operationPath, or workflowId
        has_operation_id = step.operation_id is not None
        has_operation_path = step.operation_path is not None
        has_workflow_id = step.workflow_id is not None

        if not (has_operation_id or has_operation_path or has_workflow_id):
            self.errors.append(
                f"Step '{step_id}' must specify one of: operationId, operationPath, or workflowId",
            )
            return

        # Validate operationId exists in registry
        if has_operation_id:
            if step.operation_id not in self.operation_registry.operations:
                self.errors.append(
                    f"Step '{step_id}' references non-existent operation '{step.operation_id}'",
                )
            else:
                operation = self.operation_registry.operations[step.operation_id]
                self._validate_step_parameters(step, operation, step_id)

        # Validate workflowId exists
        if has_workflow_id:
            workflow_id = str(step.workflow_id)
            if not any(w.workflow_id == workflow_id for w in self.specification.workflows):
                self.errors.append(
                    f"Step '{step_id}' references non-existent workflow '{workflow_id}'",
                )

        # Validate success criteria
        if step.success_criteria:
            for criterion in step.success_criteria:
                self._validate_criterion(criterion, step_id)

    def _validate_step_parameters(
        self, step: Step, operation: ApiOperation, step_id: str,
    ) -> None:
        """Validate step parameters against OpenAPI operation constraints.

        Checks:
        - Parameters are defined in the operation
        - Required parameters are provided
        - Parameter locations (header, query, path) match OpenAPI definition
        - ReusableObject references are valid and point to existing parameters

        Args:
            step: The step to validate
            operation: The OpenAPI operation definition
            step_id: The step ID for error messages
        """
        # Collect step parameters by name
        step_params: dict[str, ParameterObject | ReusableObject] = {}
        if step.parameters:
            for param in step.parameters:
                if isinstance(param, ParameterObject):
                    step_params[param.name] = param
                elif isinstance(param, ReusableObject):
                    # Extract parameter name from reference
                    param_name = self._extract_param_name_from_reference(param.reference)
                    if param_name and self._validate_reusable_reference(param.reference, param_name, step_id):
                        # Validate the reference exists in components
                        step_params[param_name] = param
                    # If reference is invalid, _validate_reusable_reference already added error

        # Check for required parameters from operation
        required_params = {
            name: param for name, param in operation.parameters.items()
            if param.required
        }

        # Validate required parameters are provided
        missing_required = set(required_params.keys()) - set(step_params.keys())
        for param_name in missing_required:
            param_def = required_params[param_name]
            param_location = param_def.param_in.value if hasattr(param_def.param_in, "value") else str(param_def.param_in)
            self.errors.append(
                f"Step '{step_id}' missing required {param_location} parameter '{param_name}'",
            )

        # Validate provided parameters
        for param_name, step_param in step_params.items():
            if param_name not in operation.parameters:
                self.warnings.append(
                    f"Step '{step_id}' parameter '{param_name}' not defined in operation '{operation.operation_id}'",
                )
            # Validate parameter location matches (only for direct ParameterObject)
            elif isinstance(step_param, ParameterObject):
                op_param = operation.parameters[param_name]
                if hasattr(step_param, "in_"):
                    # If step parameter has explicit location, validate it matches
                    op_param_location = op_param.param_in.value if hasattr(op_param.param_in, "value") else str(op_param.param_in)
                    if step_param.in_ != op_param_location:
                        self.warnings.append(
                            f"Step '{step_id}' parameter '{param_name}' location '{step_param.in_}' doesn't match operation definition '{op_param_location}'",
                        )

    def _validate_criterion(self, criterion: Any, step_id: str) -> None:
        """Validate a success criterion.

        Args:
            criterion: The criterion to validate
            step_id: The step ID for error messages
        """
        if not criterion.condition:
            self.errors.append(
                f"Criterion in step '{step_id}' has no condition",
            )

    def _extract_param_name_from_reference(self, reference: str) -> str | None:
        """Extract parameter name from a reference.

        Supports two formats:
        - JSON Pointer: #/components/parameters/paramName
        - Runtime Expression: $components.parameters.paramName

        Args:
            reference: A JSON reference or runtime expression string

        Returns:
            The parameter name, or None if reference format is invalid
        """
        # Pattern for JSON Pointer references like #/components/parameters/paramName
        json_pointer_match = re.match(r"^#/components/parameters/([A-Za-z0-9_\-]+)$", reference)
        if json_pointer_match:
            return json_pointer_match.group(1)

        # Pattern for runtime expression references like $components.parameters.paramName
        runtime_expr_match = re.match(r"^\$components\.parameters\.([A-Za-z0-9_\-]+)$", reference)
        if runtime_expr_match:
            return runtime_expr_match.group(1)

        return None

    def _validate_reusable_reference(self, reference: str, param_name: str, step_id: str) -> bool:
        """Validate that a reusable object reference is valid.

        Args:
            reference: The reference string (JSON Pointer or runtime expression)
            param_name: The extracted parameter name
            step_id: The step ID for error messages

        Returns:
            True if reference is valid, False otherwise
        """
        # Check if specification has components
        if not self.specification.components:
            self.errors.append(
                f"Step '{step_id}' uses reusable parameter '{param_name}' but specification has no components",
            )
            return False

        # Check if components has parameters
        if not self.specification.components.parameters:
            self.errors.append(
                f"Step '{step_id}' uses reusable parameter '{param_name}' but components has no parameters",
            )
            return False

        # Check if the referenced parameter exists
        if param_name not in self.specification.components.parameters:
            self.errors.append(
                f"Step '{step_id}' references non-existent reusable parameter '{param_name}' via '{reference}'",
            )
            return False

        return True

    def visit_info(self, instance: Info) -> None:
        """Visit info object."""

    def visit_source_description(self, instance: SourceDescriptionObject) -> None:
        """Visit source description."""

    def visit_criterion_expression_type(
        self, instance: CriterionExpressionTypeObject,
    ) -> None:
        """Visit criterion expression type."""

    def visit_reusable(self, instance: ReusableObject) -> None:
        """Visit reusable object."""

    def visit_parameter(self, instance: ParameterObject) -> None:
        """Visit parameter object."""

    def visit_payload_replacement(self, instance: PayloadReplacementObject) -> None:
        """Visit payload replacement object."""

    def visit_components(self, instance: ComponentsObject) -> None:
        """Visit components object."""
