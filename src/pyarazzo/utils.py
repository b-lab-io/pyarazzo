from  typing import Any
from urllib.error import HTTPError

import click
import yaml
import json
import requests
import jsonschema
from jsonschema import validate, ValidationError
import jsonref
from openapi_pydantic import OpenAPI

import importlib.resources


with importlib.resources.open_text('pyarazzo', 'schema.yaml') as schema_file:
    schema = yaml.safe_load(schema_file)


def load_spec(spec:str) -> dict:
    if spec.endswith(('.yaml', '.yml')):
        click.echo(f"Assuming Yaml file format")
        with open(spec, 'r') as file:
            spec_data = yaml.safe_load(file)
    elif spec.endswith('.json'):
        click.echo(f"Assuming Json file format")
        with open(spec, 'r') as file:
            spec_data = json.load(file)
    else:
        raise click.ClickException(f"Unsupported file type for specification file: {spec}")
    
    assert isinstance(spec_data, dict)
    return spec_data


def schema_validation(spec: dict):
   
    try:
        validate(instance=spec, schema=schema)
        click.echo("Specification file is valid.")
    except ValidationError as e:
        raise click.ClickException(f"Unsupported file type for specification file: {spec}")




