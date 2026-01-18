"""pydantic models for Open API."""

import json
import re
from enum import Enum
from typing import Annotated, Any

import httpx
import jsonref
import yaml
from openapi_pydantic.v3.v3_0 import OpenAPI, Operation, PathItem
from openapi_pydantic.v3.v3_0.parameter import Parameter, ParameterLocation
from pydantic import BaseModel, Field, field_validator
from requests.exceptions import HTTPError


class HttpMethod(str, Enum):
    """Enum for HTTP methods."""

    get = "get"
    post = "post"
    put = "put"
    patch = "patch"
    delete = "delete"
    options = "options"
    head = "head"
    trace = "trace"


class ApiOperation(BaseModel):
    """Represents an OpenAPI operation with associated metadata and parameters.

    Attributes:
        service_name (str): Name of the service this operation belongs to.
        operationId (str): Unique identifier for the operation.
        method (Optional[HttpMethod]): HTTP method (e.g., GET, POST) for the operation.
        path (str): URL path for the operation.
        headers (dict): Dictionary of HTTP headers associated with the operation.
        parameters (dict): Dictionary of parameters for the operation.
        body (Optional[dict]): Request body for the operation, if applicable.

    Methods:
        append_parameters(parameters: List[Union[Parameter, Reference]]):
            Appends a list of parameters to the operation, updating both the parameters and headers.
            If a parameter is of type 'header', it is added to the headers dictionary.
    """

    service_name: Annotated[
        str,
        Field(
            "not-set",
            description="",
        ),
    ]

    operation_id: Annotated[
        str,
        Field(
            "not-set",
            description="",
        ),
    ]
    method: HttpMethod | None = None
    path: str
    headers: dict = {}
    query_parameters: dict = {}
    parameters: dict = {}
    body: dict | None = None

    def append_parameters(self, parameters: list[Parameter]) -> None:
        """Append parameters to the operation.

        This method will update the operation's parameters and headers.
        It will also update the headers if any parameter is of type 'header'.
        """
        for param in parameters:
            if param is not None and param.param_in == ParameterLocation.HEADER:
                self.headers.update(param)


class OperationRegistry(BaseModel):
    """Registry for OpenAPI operations."""

    operations: dict[str, ApiOperation] = Field(
        {},
        description="Dictionary of operations keyed by ID",
    )

    @classmethod
    @field_validator("operations")
    def check_unique_ids(cls: Any, v: dict[str, OpenAPI]) -> dict[str, OpenAPI]:
        """Ensure that all operation IDs are unique inside a workflow."""
        if len(v) != len(set(v.keys())):
            raise ValueError("Duplicate IDs found in operations")
        return v

    def append(self, openapi_spec: str) -> None:
        """Append operations from an OpenAPI specification to the registry."""
        self.operations.update(OpenApiLoader.load(url=openapi_spec))


class OpenApiLoader:
    """Loader for OpenAPI specifications."""

    @staticmethod
    def _is_remote(url: str) -> bool:
        """Check if the URL is a remote URL."""
        # Regular expression pattern for URL validation
        pattern = re.compile(
            r"^(https?|ftp)://"  # http:// or https:// or ftp://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        return re.match(pattern, url) is not None

    @staticmethod
    def _download_file(url: str) -> dict:
        """Download a file from a URL and return its content as a dictionary."""
        # Send a GET request to the URL
        try:
            response = httpx.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPError(f"Failed to download file. Status code: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise HTTPError(f"An error occurred while requesting {url}: {exc}") from exc

        if url.endswith(".json"):
            return response.json()
        if url.endswith((".yaml", ".yml")):
            return yaml.safe_load(response.text)
        raise ValueError(
            "Unsupported file type. Only JSON and YAML files are supported.",
        )

    @staticmethod
    def _process_operation(
        path_item: PathItem,
        operation_method: HttpMethod,
        operation_data: Operation,
        operation: ApiOperation,
    ) -> None:
        """Helper function to process an operation method."""
        if operation_data.operationId is None:
            raise ValueError("Operation ID is required but not provided in the OpenAPI specification.")

        operation.operation_id = operation_data.operationId
        operation.method = operation_method
        parameters_merged: list[Any] = []
        if path_item.parameters is not None:
            parameters_merged.extend(path_item.parameters)
        if operation_data.parameters is not None:
            parameters_merged.extend(operation_data.parameters)
        operation.append_parameters(parameters_merged)

    @staticmethod
    def load(url: str) -> dict[str, ApiOperation]:
        """Load OpenAPI specification from a URL or file and return operations."""
        operations = {}
        spec_dict = None
        # detect if http or path
        if OpenApiLoader._is_remote(url):
            spec_dict = OpenApiLoader._download_file(url)
        else:
            with open(url) as file:
                if url.endswith(".json"):
                    spec_dict = json.load(file)
                if url.endswith((".yaml", ".yml")):
                    spec_dict = yaml.safe_load(file)

        # resolve all $ref
        resolved_data = jsonref.loads(json.dumps(spec_dict))

        open_api_spec = OpenAPI(**resolved_data)

        # just accumulate all parameters at the operation level

        for path_name, path_item in open_api_spec.paths.items():
            operation = ApiOperation(
                service_name=open_api_spec.info.title,
                operation_id="no-set",
                method=None,
                path=path_name,
                headers={},
                parameters={},
                body=None,
            )

            method_handlers = {
                "post": (HttpMethod.post, path_item.post),
                "get": (HttpMethod.get, path_item.get),
                "put": (HttpMethod.put, path_item.put),
            }

            for _, (http_method, operation_data) in method_handlers.items():
                if operation_data is not None:
                    OpenApiLoader._process_operation(path_item, http_method, operation_data, operation)

            # TODO : Guarantee that the operationId is not missing
            operations[operation.operation_id] = operation

        return operations
