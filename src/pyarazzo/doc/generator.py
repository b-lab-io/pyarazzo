import os
import click
#from openapi_pydantic import OpenAPI
from pyarazzo.model.arazzo import ArazzoSpec, ArazzoVisitor, SourceDescriptionObject, SourceType, Step, Workflow
#from model.openapi import OpenApiLoader, OperationRegistry


# class MarkDownGenerator(ArazzoVisitor):

#     def __init__(self):
#         super().__init__()
#         self.model = None
#         self.workflows = []
#         self.testsuites = []
#         self.operations = OperationRegistry()

#     # @abstractmethod
#     # def visit_info(self, instance: Info):
#     #     pass

#     def visit_source_decription_object(self, instance: SourceDescriptionObject):
#         click.echo(f"loading description {instance.name}")

#         if instance.type != SourceType.arazzo:
#             click.echo(f"ignoring source {instance.name} of type arazzo")
#             return

#         # loading open api spec
#         open_api_spec:OpenAPI = OpenApiLoader.load(instance.url)
#         operations = OpenApiLoader.extract_operations(open_api_spec)

#         for operation in operations:
#              self.operations
       

#         for path_key in open_api_spec.paths.keys():
#             path_item = open_api_spec.paths[path_key]

#             if path_item.get is not None:
#                 pass

        

class MarkdownGeneratorVisitor(ArazzoVisitor):
    """Visitor that generates markdown files for workflows."""
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plantumlify(self, name:str):
        return name.replace(' ', '_').replace('-', '_')

    def visit_specification(self, spec:ArazzoSpec ):

         for wf in spec.workflows:
             self.visit_workflow(wf)



    def visit_workflow(self, workflow: Workflow) -> str:
        """Generate markdown content for a workflow, including PlantUML diagram."""
        filename = os.path.join(self.output_dir, f"{workflow.workflowId.replace(' ', '_').lower()}.md")
        
        # Start building the markdown content
        content = f"# {workflow.workflowId}\n\n"
        content += f"{workflow.description}\n\n"
        
        # Add PlantUML diagram
        content += "## Workflow Diagram\n\n"
        content += "```plantuml\n"
        content += "@startuml\n"
        content += "skinparam backgroundColor #EEEBDC\n"
        content += "skinparam handwritten true\n\n"

        content += f"participant \"{workflow.workflowId}\" as {self.plantumlify(workflow.workflowId)}\n"
        
        # Adding steps to the diagram
        for step in workflow.steps:
            content += f"participant \"{step.stepId}\" as {self.plantumlify(step.stepId)}\n"

        if workflow.dependsOn:
            for depending_wf in workflow.dependsOn :
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
        
        print(f"Generated: {filename}")
        return filename

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







    # @abstractmethod
    # def visit_criterion_expression_type_object(self, instance: CriterionExpressionTypeObject):
    #     pass
    # @abstractmethod
    # def visit_reusable_object(self, instance: ReusableObject):
    #     pass
    # @abstractmethod
    # def visit_parameter_object(self, instance: ParameterObject):
    #     pass
    # @abstractmethod
    # def visit_payload_replacement_object(self, instance: PayloadReplacementObject):
    #     pass
    # @abstractmethod
    # def visit_metaData(self, instance: MetaDat):
    #     pass

    # #@abstractmethod
    # def visit_workflow_object(self, instance: Workflow):
    #     click.echo(f"{instance.workflowId}")
    #     suite:TestSuite = TestSuite(instance.workflowId)

    #     test = suite.tests.create(instance.workflowId)

    #     for step in instance.steps:
    #         step.ac

       
    #     self.testsuites.append(suite)
    #     pass

    # #@abstractmethod
    # def visit_components_onject(self, instance: ComponentsObject):
    #     pass

    # #@abstractmethod
    # def visit_model(self, instance: Model):
    #     self.model = instance

    #     for source in instance.sourceDescriptions:
    #         source.accept(self)


    #     # Todo ordonate Workflows

    #     click.echo("analyzing model")
    #     for workflow in instance.workflows:
    #         workflow.accept(self)
    #     pass
