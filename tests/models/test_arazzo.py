"""Test Arazzo model conformity."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pyarazzo.model.arazzo import ArazzoSpecification


@pytest.mark.parametrize("path", [("./tests/data/models/v1/pet-coupons-example.yaml")])
def test_valid_spec(path: str) -> None:
    """Test the trasnformation from yaml/json to an object model."""
    spec_dict = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    spec = ArazzoSpecification(**spec_dict)
    assert spec is not None


@pytest.mark.parametrize("path", [("./tests/data/models/v1/invalid-arazzo-version.yaml")])
def test_invalid_spec(path: str) -> None:
    """Test invalid transformation from yaml/json to an object model."""
    spec_dict = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        ArazzoSpecification(**spec_dict)


def test_valid_arazzo_1_1_spec() -> None:
    """Test deserialization of Arazzo 1.1 features ($self, timeout, dependsOn)."""
    spec_dict = yaml.safe_load(Path("./tests/data/models/v1/arazzo-1.1-sample.yaml").read_text(encoding="utf-8"))
    spec = ArazzoSpecification(**spec_dict)
    assert spec is not None
    assert spec.arazzo == "1.1.0"
    assert spec.self_field == "./arazzo-1.1-sample.yaml"
    assert len(spec.workflows) == 1

    wf = spec.workflows[0]
    assert len(wf.steps) == 2

    step1 = wf.steps[0]
    assert str(step1.step_id) == "check-pet"
    assert step1.timeout == 1000
    assert step1.depends_on is None

    step2 = wf.steps[1]
    assert str(step2.step_id) == "order-pet"
    assert step2.timeout == 2000
    assert step2.depends_on == ["check-pet"]


@pytest.mark.parametrize("version", ["1.0.0", "1.0.1", "1.1.0"])
def test_valid_arazzo_versions(version: str) -> None:
    """Test that ArazzoSpecification accepts both 1.0.x and 1.1.x versions."""
    spec_dict = yaml.safe_load(Path("./tests/data/models/v1/pet-coupons-example.yaml").read_text(encoding="utf-8"))
    spec_dict["arazzo"] = version
    spec = ArazzoSpecification(**spec_dict)
    assert spec.arazzo == version
