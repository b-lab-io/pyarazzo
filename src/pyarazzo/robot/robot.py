import click
from arazzo import *
from robot.api import TestSuite
from robot.model.visitor import SuiteVisitor
from openapi_pydantic import OpenAPI
from utils import OpenApiLoader
from model.openapi import OperationRegistry


class RobotGenerator(ArazzoVisitor):

    def __init__(self):
        super().__init__()
        self.model = None
        self.workflows = []
        self.testsuites = []
        self.operations = OperationRegistry()

    # @abstractmethod
    # def visit_info(self, instance: Info):
    #     pass

    def visit_source_decription_object(self, instance: SourceDescriptionObject):
        click.echo(f"loading description {instance.name}")

        if instance.type != SourceType.arazzo:
            click.echo(f"ignoring source {instance.name} of type arazzo")
            return

        # loading open api spec
        open_api_spec:OpenAPI = OpenApiLoader.load(instance.url)
        operations = OpenApiLoader.extract_operations(open_api_spec)

        for operation in operations:

             self.operations
       

        for path_key in open_api_spec.paths.keys():
            path_item = open_api_spec.paths[path_key]

            if path_item.get is not None:
                pass

        






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

    #@abstractmethod
    def visit_workflow_object(self, instance: WorkflowObject):
        click.echo(f"{instance.workflowId}")
        suite:TestSuite = TestSuite(instance.workflowId)

        test = suite.tests.create(instance.workflowId)

        for step in instance.steps:
            step.ac

       
        self.testsuites.append(suite)
        pass

    #@abstractmethod
    def visit_components_onject(self, instance: ComponentsObject):
        pass

    #@abstractmethod
    def visit_model(self, instance: Model):
        self.model = instance

        for source in instance.sourceDescriptions:
            source.accept(self)


        # Todo ordonate Workflows

        click.echo("analyzing model")
        for workflow in instance.workflows:
            workflow.accept(self)
        pass


class RobotSerializer(SuiteVisitor):
    pass