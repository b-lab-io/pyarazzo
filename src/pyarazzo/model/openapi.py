from typing import Dict, enum, Annotated
from pydantic import BaseModel, Field, field_validator

class HttpMethod(str, enum):
    get = "get"
    post = "post"
    put = "put"
    patch = "patch"
    delete = "delete"
    options = "options"
    head = "head"
    trace = "trace"

class Operation (BaseModel):

    operationId: Annotated[
        str,
        Field(
            description='',
        ),
    ]
    method : HttpMethod
    path: str
    headers: dict = None
    parameters : dict = None
    body: dict = None


class OperationRegistry(BaseModel):
    operations: Dict[str, Operation] = Field(..., description="Dictionary of operations keyed by ID")

    @field_validator('operations')
    def check_unique_ids(cls, v):
        if len(v) != len(set(v.keys())):
            raise ValueError("Duplicate IDs found in operations")
        return v
    

class OpenApiLoader:

    @staticmethod
    def _is_remote()-> bool:
        return False
    
    @staticmethod
    def _download_file(url: str) -> dict:
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Determine the file type based on the URL extension
            if url.endswith('.json'):
                # Parse the JSON content
                return response.json()
            elif url.endswith('.yaml') or url.endswith('.yml'):
                # Parse the YAML content
                return yaml.safe_load(response.text)
            else:
                raise ValueError("Unsupported file type. Only JSON and YAML files are supported.")
        else:
            raise HTTPError(f"Failed to download file. Status code: {response.status_code}")

    @staticmethod
    def load(url:str) -> OpenAPI:
        
        spec_dict = None
        # detect if http or path 
        if OpenApiLoader._is_remote(url):
            spec_dict = OpenApiLoader._download_file(url)
        else:
            with open(url, 'r') as file:
                spec_dict = json.load(file)

        # resolve all $ref
        resolved_data = jsonref.load(spec_dict)
        open_api_spec = OpenAPI(**resolved_data)

        # just accumulate all parameters at the operation level
        for path, path_item in open_api_spec.paths.items():
            params = path_item.parameters
            for _method, operation in path_item.operations.items():
                operation.parameter.append(params)

        return open_api_spec
