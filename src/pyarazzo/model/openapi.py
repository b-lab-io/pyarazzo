"""pydantic models for Open API."""

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import httpx
import jsonref
import yaml
from openapi_pydantic.v3.v3_0 import (
    OpenAPI as OpenAPI30,
)
from openapi_pydantic.v3.v3_0 import (
    Operation as Operation30,
)
from openapi_pydantic.v3.v3_0 import (
    PathItem as PathItem30,
)
from openapi_pydantic.v3.v3_0.parameter import Parameter
from openapi_pydantic.v3.v3_1 import (
    OpenAPI as OpenAPI31,
)
from openapi_pydantic.v3.v3_1 import (
    Operation as Operation31,
)
from openapi_pydantic.v3.v3_1 import (
    PathItem as PathItem31,
)
from pydantic import BaseModel, Field, field_validator
from requests.exceptions import HTTPError

OpenAPI = OpenAPI30 | OpenAPI31
Operation = Operation30 | Operation31
PathItem = PathItem30 | PathItem31


class HttpMethod(StrEnum):
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
        parameters (dict): Dictionary of parameters by name with full Parameter objects
        body (Optional[dict]): Request body for the operation, if applicable.

    Methods:
        append_parameters(parameters: List[Union[Parameter, Reference]]):
            Appends a list of parameters to the operation.
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
    parameters: dict[str, Parameter] = {}
    body: dict | None = None

    def append_parameters(self, parameters: list[Parameter]) -> None:
        """Append parameters to the operation.

        Stores full Parameter objects with their metadata (required, type, etc.)
        for validation against step definitions.
        """
        for param in parameters:
            if param is None:
                continue

            # Store full Parameter object by name
            self.parameters[param.name] = param


class OperationRegistry(BaseModel):
    """Registry for OpenAPI operations."""

    operations: dict[str, ApiOperation] = Field(
        {},
        description="Dictionary of operations keyed by ID",
    )

    @classmethod
    @field_validator("operations")
    def check_unique_ids(cls: Any, v: dict[str, ApiOperation]) -> dict[str, ApiOperation]:
        """Ensure that all operation IDs are unique inside a workflow."""
        if len(v) != len(set(v.keys())):
            raise ValueError("Duplicate IDs found in operations")
        return v

    def append(self, openapi_spec: str, source_name: str | None = None) -> None:
        """Append operations from an OpenAPI specification to the registry."""
        loaded_ops = OpenApiLoader.load(url=openapi_spec)
        self.operations.update(loaded_ops)
        if source_name:
            for op_id, op in loaded_ops.items():
                self.operations[f"$sourceDescriptions.{source_name}.{op_id}"] = op

    def get(self, operation_id: str) -> ApiOperation | None:
        """Look up an operation by ID, supporting bare and qualified names."""
        if operation_id in self.operations:
            return self.operations[operation_id]
        if operation_id.startswith("$sourceDescriptions."):
            parts = operation_id.split(".")
            if len(parts) >= 3:
                bare_id = parts[-1]
                if bare_id in self.operations:
                    return self.operations[bare_id]
        return None

    def __getitem__(self, key: str) -> ApiOperation:
        """Look up an operation by ID with indexing syntax."""
        op = self.get(key)
        if op is None:
            raise KeyError(key)
        return op

    def __contains__(self, key: object) -> bool:
        """Check if an operation is contained in the registry."""
        if not isinstance(key, str):
            return False
        return self.get(key) is not None


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
    def _resolve_url(url: str, spec_path: str | None = None) -> str:
        """Resolve a source URL relative to the specification file.

        Args:
            url: The URL to resolve (can be absolute or relative)
            spec_path: Optional path to the specification file (used for relative URL resolution)

        Returns:
            The resolved URL
        """
        # If URL is remote, return as-is
        if url.startswith(("http://", "https://", "ftp://")):
            return url

        # If we have a spec path and the URL is relative, resolve it
        if spec_path and not Path(url).is_absolute():
            spec_dir = Path(spec_path).parent.resolve()
            return str((spec_dir / url).resolve())

        return url

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
            with Path(url).open(encoding="utf-8") as file:
                if url.endswith(".json"):
                    spec_dict = json.load(file)
                if url.endswith((".yaml", ".yml")):
                    spec_dict = yaml.safe_load(file)

        # resolve all $ref
        resolved_data = jsonref.loads(json.dumps(spec_dict, default=str))

        version = str(resolved_data.get("openapi", "3.0"))
        open_api_spec: OpenAPI30 | OpenAPI31
        if version.startswith("3.1"):
            open_api_spec = OpenAPI31(**resolved_data)
        else:
            open_api_spec = OpenAPI30(**resolved_data)

        # just accumulate all parameters at the operation level

        for path_name, path_item in (open_api_spec.paths or {}).items():
            method_handlers = {
                "post": (HttpMethod.post, path_item.post),
                "get": (HttpMethod.get, path_item.get),
                "put": (HttpMethod.put, path_item.put),
                "delete": (HttpMethod.delete, path_item.delete) if hasattr(path_item, "delete") else None,
                "patch": (HttpMethod.patch, path_item.patch) if hasattr(path_item, "patch") else None,
            }

            method_handlers = {k: v for k, v in method_handlers.items() if v is not None}

            for http_method, operation_data in method_handlers.values():
                if operation_data is not None:
                    operation = ApiOperation(
                        service_name=open_api_spec.info.title,
                        operation_id="no-set",
                        method=None,
                        path=path_name,
                        parameters={},
                        body=None,
                    )
                    OpenApiLoader._process_operation(path_item, http_method, operation_data, operation)
                    operations[operation.operation_id] = operation

        return operations
