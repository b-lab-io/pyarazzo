"""Doc generation package."""
import logging
import os

from pyarazzo.model.arazzo import (
    ArazzoSpecification,
    ArazzoVisitor,
    ComponentsObject,
    CriterionExpressionTypeObject,
    Info,
    MetaData,
    ParameterObject,
    PayloadReplacementObject,
    ReusableObject,
    SourceDescriptionObject,
    Step,
    Workflow,
)

LOGGER = logging.getLogger(__name__)

class SimpleMarkdownGeneratorVisitor(ArazzoVisitor):
    """Visitor that generates markdown files for workflows."""

    def __init__(self, output_dir: str) -> None:
        """Constructor.

        Args:
            output_dir (str): _description_
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plantumlify(self, name: str) -> str:
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
        for wf in spec.workflows:
            self.visit_workflow(wf)

    def visit_workflow(self, workflow: Workflow) -> None:
        """Generate markdown content for a workflow, including PlantUML diagram."""
        LOGGER.info(f"Generation of workflow: {workflow.workflowId}")
        filename = os.path.join(
            self.output_dir, f"{workflow.workflowId.replace(' ', '_').lower()}.md",
        )

        # Start building the markdown content
        content = f"# {workflow.workflowId}\n\n"
        content += f"{workflow.description}\n\n"

        # Add PlantUML diagram
        content += "## Workflow Diagram\n\n"
        content += "```plantuml\n"
        content += "@startuml\n"
        content += "skinparam backgroundColor #EEEBDC\n"
        content += "skinparam handwritten true\n\n"

        content += f'participant "{workflow.workflowId}" as {self.plantumlify(workflow.workflowId)}\n'

        # Adding steps to the diagram
        for step in workflow.steps:
            content += (
                f'participant "{step.stepId}" as {self.plantumlify(step.stepId)}\n'
            )

        if workflow.dependsOn:
            for depending_wf in workflow.dependsOn:
                content += f"WF_{self.plantumlify(depending_wf)} --> {self.plantumlify(workflow.workflowId)}\n"

        # Adding dependencies to the diagram        for step in workflow.steps:
        for step in workflow.steps:
            content += f"{self.plantumlify(workflow.workflowId)} --> {self.plantumlify(step.stepId)} : {step.description}\n"

        content += "@enduml\n```\n\n"

        # Add step descriptions
        content += "## Steps\n\n"
        for step in workflow.steps:
            step_content = step.accept(self)
            content += step_content

        # Write to file
        with open(filename, "w") as f:
            f.write(content)

        LOGGER.info(f"Generated: {filename}")

    def visit_step(self, step: Step) -> str:
        """Generate markdown content for a step."""
        content = f"### {step.stepId}\n\n"
        content += f"**ID**: {step.stepId}\n\n"
        content += f"{step.description}\n\n"

        # if step.depends_on:
        #     content += "**Dependencies**:\n"
        #     for dependency in step.depends_on:
        #         content += f"- {dependency}\n"
        #     content += "\n"

        return content


    def visit_info(self, instance: Info)-> None:
        """Visit Info instance.

        Args:
            instance (Info): _description_
        """

    def visit_source_decription(self, instance: SourceDescriptionObject)-> None:
        """Visit SourceDescriptionObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_criterion_expression_type(self, instance: CriterionExpressionTypeObject)-> None:
        """Visit CriterionExpressionTypeObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_reusable(self, instance: ReusableObject)-> None:
        """Visit ReusableObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_parameter(self, instance: ParameterObject)-> None:
        """Visit ParameterObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_payload_replacement(self, instance: PayloadReplacementObject)-> None:
        """Visit PayloadReplacementObject instance.

        Args:
            instance (Info): _description_
        """

    def visit_meta_data(self, instance: MetaData)-> None:
        """Visit MetaData instance.

        Args:
            instance (Info): _description_
        """

    def visit_components(self, instance: ComponentsObject)-> None:
        """Visit ComponentsObject instance.

        Args:
            instance (Info): _description_
        """
