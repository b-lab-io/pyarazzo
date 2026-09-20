"""Tests for documentation generation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pyarazzo.doc.generator import SimpleMarkdownGeneratorVisitor
from pyarazzo.exceptions import LoadError
from pyarazzo.utils import load_spec


def test_load_spec_from_file() -> None:
    """Test loading a valid specification from file."""
    spec_path = "tests/data/test_utils_valid.yaml"
    spec = load_spec(spec_path)
    assert spec is not None
    assert isinstance(spec, dict)


def test_load_spec_invalid_path() -> None:
    """Test loading from non-existent file raises LoadError."""
    with pytest.raises(LoadError) as exc_info:
        load_spec("nonexistent/file.yaml")
    assert "not found" in str(exc_info.value).lower()


def test_load_spec_unsupported_format() -> None:
    """Test loading unsupported file format raises LoadError."""
    with tempfile.NamedTemporaryFile(suffix=".txt") as f:
        f.write(b"invalid content")
        f.flush()
        with pytest.raises(LoadError) as exc_info:
            load_spec(f.name)
        assert "unsupported" in str(exc_info.value).lower()


def test_doc_generator_creates_output_dir() -> None:
    """Test that doc generator creates output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = str(Path(tmpdir) / "docs" / "nested")
        SimpleMarkdownGeneratorVisitor(output_dir)
        assert Path(output_dir).exists()


def test_doc_generation_visitor_instantiation() -> None:
    """Test that the markdown generator visitor can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimpleMarkdownGeneratorVisitor(tmpdir)
        assert generator.output_dir == tmpdir
        assert Path(tmpdir).exists()
        assert generator.operation_registry is not None
        assert generator.content == ""


def test_plantuml_name_conversion() -> None:
    """Test plantumlify converts names correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimpleMarkdownGeneratorVisitor(tmpdir)
        assert generator.plantumlify("My Workflow") == "My_Workflow"
        assert generator.plantumlify("my-step-id") == "my_step_id"
        assert generator.plantumlify("already_formatted") == "already_formatted"


def test_doc_generation_arazzo_1_1() -> None:
    """Test generating documentation for an Arazzo 1.1 specification referencing OpenAPI 3.1."""
    from pyarazzo.model.arazzo import ArazzoSpecificationLoader

    spec_path = "tests/data/models/v1/arazzo-1.1-sample.yaml"
    spec = ArazzoSpecificationLoader.load(spec_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        visitor = SimpleMarkdownGeneratorVisitor(tmpdir, spec_path=spec_path)
        spec.accept(visitor)

        output_file = Path(tmpdir) / "pet-order-workflow.md"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Verify workflow and diagram content
        assert "# pet-order-workflow" in content
        assert "PetStore_3.1_API" in content
        assert "get /pets/{petId}" in content
        assert "post /pets/{petId}/orders" in content

        # Verify step details including Arazzo 1.1 timeout and dependencies
        assert "### check-pet" in content
        assert "**Timeout**: 1000ms" in content
        assert "### order-pet" in content
        assert "**Dependencies**:" in content
        assert "- check-pet" in content
        assert "**Timeout**: 2000ms" in content
