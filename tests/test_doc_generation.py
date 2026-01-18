"""Tests for documentation generation."""

from __future__ import annotations

import os
import tempfile

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
        output_dir = os.path.join(tmpdir, "docs", "nested")
        SimpleMarkdownGeneratorVisitor(output_dir)
        assert os.path.exists(output_dir)


def test_doc_generation_visitor_instantiation() -> None:
    """Test that the markdown generator visitor can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimpleMarkdownGeneratorVisitor(tmpdir)
        assert generator.output_dir == tmpdir
        assert os.path.exists(tmpdir)
        assert generator.operation_registry is not None
        assert generator.content == ""


def test_plantuml_name_conversion() -> None:
    """Test plantumlify converts names correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SimpleMarkdownGeneratorVisitor(tmpdir)
        assert generator.plantumlify("My Workflow") == "My_Workflow"
        assert generator.plantumlify("my-step-id") == "my_step_id"
        assert generator.plantumlify("already_formatted") == "already_formatted"
