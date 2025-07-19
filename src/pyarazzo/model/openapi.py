"""pydantic models for Open API."""
from typing import Annotated, Dict, List, Optional, Union
from enum import Enum
import re
import json
import jsonref
import yaml
import requests
from requests.exceptions import HTTPError

from openapi_pydantic.v3.v3_0 import OpenAPI
from openapi_pydantic.v3.v3_0.parameter import Parameter
from openapi_pydantic.v3.v3_0.reference import Reference
from pydantic import BaseModel, Field, field_validator


class HttpMethod(str, Enum):
    get = "get"
    post = "post"
    put = "put"
    patch = "patch"
    delete = "delete"
    options = "options"
    head = "head"
    trace = "trace"


class Operation(BaseModel):

    service_name: Annotated[
        str,
        Field("not-set", 
            description="",
        ),
    ]

    operationId: Annotated[
        str,
        Field("not-set",
            description="",
        ),
    ]
    method: Optional[HttpMethod] = None
    path: str
    headers: dict = {}
    parameters: dict = {}
    body:  Optional[dict] = None

    def append_parameters(self, parameters: List[Union[Parameter, Reference]]):
        for param in parameters:
            if param is not None:
                for p in param:
                    if p is not None: 
                        if p.param_in == "header": 
                            self.headers.update(p)

class OperationRegistry(BaseModel):
    operations: Dict[str, OpenAPI] = Field(
        {}, description="Dictionary of operations keyed by ID"
    )

    @field_validator("operations")
    def check_unique_ids(cls, v):
        if len(v) != len(set(v.keys())):
            raise ValueError("Duplicate IDs found in operations")
        return v
    
    def append(self, openapi_spec:str):
        self.operations.update(OpenApiLoader.load(url= openapi_spec))


class OpenApiLoader:
    @staticmethod
    def _is_remote(url:str) -> bool:
        # Regular expression pattern for URL validation
        pattern = re.compile(
        r'^(https?|ftp)://'  # http:// or https:// or ftp://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(pattern, url) is not None
    @staticmethod
    def _download_file(url: str) -> dict:
        # Send a GET request to the URL
        
        response = requests.get(url)

        if response.status_code == 200:
            if url.endswith(".json"):
                return response.json()
            if url.endswith(".yaml") or url.endswith(".yml"):
                return yaml.safe_load(response.text)
            raise ValueError(
                "Unsupported file type. Only JSON and YAML files are supported."
            )
        raise HTTPError(f"Failed to download file. Status code: {response.status_code}")
    

    @staticmethod
    def _process_operation(path_item, operation_method, operation_data, operation):
        """Helper function to process an operation method."""
        operation.operationId = operation_data.operationId
        operation.method = operation_method
        operation.append_parameters([path_item.parameters, operation_data.parameters])


    @staticmethod
    def load(url: str) -> dict[str,Operation]:

        operations = {}
        spec_dict = None
        # detect if http or path
        if OpenApiLoader._is_remote(url):
            spec_dict = OpenApiLoader._download_file(url)
        else:
            with open(url) as file:
                if url.endswith(".json"):
                    spec_dict = json.load(file)
                if url.endswith(".yaml") or url.endswith(".yml"):
                    spec_dict = yaml.safe_load(file)

        # resolve all $ref
        resolved_data = jsonref.loads(json.dumps(spec_dict))

        open_api_spec = OpenAPI(**resolved_data)

        # just accumulate all parameters at the operation level

        for path_name, path_item in open_api_spec.paths.items():
          
            operation = Operation(
                service_name= open_api_spec.info.title,
                operationId="no-set",
                method=None,
                path=path_name,
                headers={},
                parameters = {},
                body= None,
            )

            method_handlers = {
                'post': (HttpMethod.post, path_item.post),
                'get': (HttpMethod.get, path_item.get),
                'put': (HttpMethod.put, path_item.put),
            }

            for _, (http_method, operation_data) in method_handlers.items():
                if operation_data is not None:
                    OpenApiLoader._process_operation(path_item , http_method, operation_data, operation)

            # TODO : Guarantee that the operationId is not missing
            operations[operation.operationId]= operation

        return operations
