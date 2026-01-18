"""Doc generation package.

This module provides visitors for generating documentation from Arazzo specifications.
It includes markdown generation with PlantUML diagrams for workflow visualization.
"""

import logging
import os

from pyarazzo.config import PLANTUML_SETTINGS
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
    StepId,
    Workflow,
    WorkflowId,
)
from pyarazzo.model.openapi import ApiOperation, OperationRegistry

LOGGER = logging.getLogger(__name__)


class SimpleMarkdownGeneratorVisitor(ArazzoVisitor):
    """Visitor that generates markdown files for workflows."""

    def __init__(self, output_dir: str) -> None:
        """Constructor.

        Args:
            output_dir (str): output dir path
        """
        self.output_dir = output_dir
        self.content = ""
        self.operation_registry = OperationRegistry(operations={})
        os.makedirs(output_dir, exist_ok=True)

    def plantumlify(self, name: str | WorkflowId | StepId) -> str:
        """Convert a string into a plantuml string format. Removing spaces and hyphens replacing them with underscores.

        Args:
            name (str): variable name

        Returns:
            str: plantuml conforme variable name
        """
        return name.replace(" ", "_").replace("-", "_")

    def visit_specification(self, spec: ArazzoSpecification) -> None:
        """Visit the speciciation instance.

        Args:
            spec (ArazzoSpec): _description_
        """
        for source_description in spec.source_descriptions:
            source_description.accept(self)

        for wf in spec.workflows:
            self.content = ""
            wf.accept(self)

    def visit_workflow(self, workflow: Workflow) -> None:
        """Generate markdown content for a workflow, including PlantUML diagram."""
        LOGGER.info(f"Generating workflow documentation: {workflow.workflow_id}")
        filename = os.path.join(
            self.output_dir,
            f"{workflow.workflow_id.replace(' ', '_').lower()}.md",
        )

        # Start building the markdown content
        self.content = f"# {workflow.workflow_id}\n\n"
        self.content += f"{workflow.description}\n\n"

        # Add PlantUML diagram
        self.content += f"## Workflow Diagram {workflow.workflow_id}\n\n"
        self.content += "```plantuml\n"
        self.content += "@startuml\n"
        self.content += f"skinparam {PLANTUML_SETTINGS['skin_param']}\n"
        self.content += f"!option handwritten {str(PLANTUML_SETTINGS['handwritten']).lower()}\n\n"

        self.content += f'participant "{workflow.workflow_id}" as {self.plantumlify(workflow.workflow_id)}\n'

        if workflow.depends_on:
            for depending_wf in workflow.depends_on:
                self.content += f"WF_{self.plantumlify(depending_wf)} --> {self.plantumlify(workflow.workflow_id)}\n"

        # Adding dependencies to the diagram
        for step in workflow.steps:
            step_description = step.description
            called_service = self.plantumlify(step.step_id)

            if step.operation_id is not None:
                operation: ApiOperation = self.operation_registry.operations[step.operation_id]
                called_service = self.plantumlify(operation.service_name)
                step_description = f"{operation.method} {operation.path}"
                self.content += f"{self.plantumlify(workflow.workflow_id)} --> {called_service} : {step_description}\n"

            if step.workflow_id is not None:
                self.content += "group " + step.workflow_id + "\n"
                called_service = self.plantumlify(step.workflow_id)
                step_description = f"Workflow: {step.workflow_id}"
                self.content += f"{self.plantumlify(workflow.workflow_id)} --> {called_service} : {step_description}\n"
                self.content += "end\n"

        self.content += "@enduml\n```\n\n"

        # Add step descriptions
        self.content += "## Steps\n\n"
        for step in workflow.steps:
            step.accept(self)
        # Write to file
        with open(filename, "w") as f:
            f.write(self.content)

        LOGGER.info(f"Generated: {filename}")

    def visit_step(self, step: Step) -> None:
        """Generate markdown content for a step."""
        self.content += f"### {step.step_id}\n\n"
        self.content += f"**ID**: {step.step_id}\n\n"
        self.content += f"{step.description}\n\n"

        # if step.depends_on:
        #     content += "**Dependencies**:\n"
        #     for dependency in step.depends_on:
        #         content += f"- {dependency}\n"
        #     content += "\n"

    def visit_info(self, instance: Info) -> None:
        """Visit Info instance.

        Args:
            instance (Info): _description_
        """

    def visit_source_description(self, instance: SourceDescriptionObject) -> None:
        """Visit SourceDescriptionObject instance.

        Args:
            instance (SourceDescriptionObject): _description_
        """
        if instance.type != SourceType.openapi:
            raise ValueError(f"not supported source type {instance.type} for source {instance.name} ")

        self.operation_registry.append(openapi_spec=instance.url)

    def visit_criterion_expression_type(self, instance: CriterionExpressionTypeObject) -> None:
        """Visit CriterionExpressionTypeObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_reusable(self, instance: ReusableObject) -> None:
        """Visit ReusableObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_parameter(self, instance: ParameterObject) -> None:
        """Visit ParameterObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_payload_replacement(self, instance: PayloadReplacementObject) -> None:
        """Visit PayloadReplacementObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_components(self, instance: ComponentsObject) -> None:
        """Visit ComponentsObject instance.

        Args:
            instance (Info): _description_
        """
