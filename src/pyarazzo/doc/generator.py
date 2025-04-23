"""Doc generation package."""
import logging
import os

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
        self.content = ""
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
            self.content = ""
            self.visit_workflow(wf)

    def visit_workflow(self, workflow: Workflow) -> None:
        """Generate markdown content for a workflow, including PlantUML diagram."""
        LOGGER.info(f"Generation of workflow: {workflow.workflow_id}")
        filename = os.path.join(
            self.output_dir, f"{workflow.workflow_id.root.replace(' ', '_').lower()}.md",
        )

        # Start building the markdown content
        self.content = f"# {workflow.workflow_id}\n\n"
        self.content += f"{workflow.description}\n\n"

        # Add PlantUML diagram
        self.content += "## Workflow Diagram\n\n"
        self.content += "```plantuml\n"
        self.content += "@startuml\n"
        self.content += "skinparam backgroundColor #EEEBDC\n"
        self.content += "skinparam handwritten true\n\n"

        self.content += f'participant "{workflow.workflow_id}" as {self.plantumlify(workflow.workflow_id.root)}\n'

        # Adding steps to the diagram
        for step in workflow.steps:
            self.content += (
                f'participant "{step.step_id}" as {self.plantumlify(step.step_id.root)}\n'
            )

        if workflow.depends_on:
            for depending_wf in workflow.depends_on:
                self.content += f"WF_{self.plantumlify(depending_wf)} --> {self.plantumlify(workflow.workflow_id.root)}\n"

        # Adding dependencies to the diagram        for step in workflow.steps:
        for step in workflow.steps:
            self.content += f"{self.plantumlify(workflow.workflow_id.root)} --> {self.plantumlify(step.step_id.root)} : {step.description}\n"

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
        self.content = f"### {step.step_id}\n\n"
        self.content += f"**ID**: {step.step_id}\n\n"
        self.content += f"{step.description}\n\n"

        # if step.depends_on:
        #     content += "**Dependencies**:\n"
        #     for dependency in step.depends_on:
        #         content += f"- {dependency}\n"
        #     content += "\n"



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

    def visit_components(self, instance: ComponentsObject)-> None:
        """Visit ComponentsObject instance.

        Args:
            instance (Info): _description_
        """
