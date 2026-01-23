from __future__ import annotations

import pytest

from t4_devkit.schema.tables.autolabel_metadata import (
    AutolabelMetadata,
    AutolabelMixin,
    AutolabelModel,
)


class TestAutolabelModel:
    """Test cases for AutolabelModel class that are not covered elsewhere."""

    def test_to_autolabel_model_type_error(self):
        """Test to_autolabel_model raises TypeError for invalid input."""
        with pytest.raises(
            TypeError,
            match="Input must be None or a list of \\[dicts or AutolabelModel\\] instances",
        ):
            AutolabelModel.to_autolabel_model("invalid_input")

    def test_to_autolabel_model_type_error_with_dict(self):
        """Test to_autolabel_model raises TypeError when input is a dict instead of list."""
        with pytest.raises(
            TypeError,
            match="Input must be None or a list of \\[dicts or AutolabelModel\\] instances",
        ):
            AutolabelModel.to_autolabel_model({"name": "model1", "score": 0.8})

    def test_to_autolabel_model_type_error_with_number(self):
        """Test to_autolabel_model raises TypeError when input is a number."""
        with pytest.raises(
            TypeError,
            match="Input must be None or a list of \\[dicts or AutolabelModel\\] instances",
        ):
            AutolabelModel.to_autolabel_model(123)


class TestAutolabelMetadata:
    """Test cases for AutolabelMetadata class that are not covered elsewhere."""

    def test_to_autolabel_metadata_type_error(self):
        """Test to_autolabel_metadata raises TypeError for invalid input."""
        with pytest.raises(
            TypeError,
            match="Input must be None, a dict, an AutolabelMetadata instance, or a list of \\[dicts or AutolabelModel\\] instances.",
        ):
            AutolabelMetadata.to_autolabel_metadata("invalid_input")

    def test_to_autolabel_metadata_type_error_with_number(self):
        """Test to_autolabel_metadata raises TypeError when input is a number."""
        with pytest.raises(
            TypeError,
            match="Input must be None, a dict, an AutolabelMetadata instance, or a list of \\[dicts or AutolabelModel\\] instances.",
        ):
            AutolabelMetadata.to_autolabel_metadata(123)


class TestAutolabelMixin:
    """Test cases for AutolabelMixin class that are not covered elsewhere."""

    def test_autolabel_mixin_error_automatic_true_no_metadata(self):
        """Test AutolabelMixin raises TypeError when automatic_annotation=True but autolabel_metadata=None."""
        with pytest.raises(
            TypeError, match="autolabel_metadata must be provided when automatic_annotation is True"
        ):
            AutolabelMixin(automatic_annotation=True, autolabel_metadata=None)

    def test_autolabel_mixin_error_automatic_false_with_metadata(self):
        """Test AutolabelMixin raises TypeError when automatic_annotation=False but autolabel_metadata is provided."""
        metadata = AutolabelMetadata(models=[AutolabelModel(name="test_model", score=0.8)])
        with pytest.raises(
            TypeError, match="autolabel_metadata must be None when automatic_annotation is False"
        ):
            AutolabelMixin(automatic_annotation=False, autolabel_metadata=metadata)

    def test_autolabel_mixin_error_default_automatic_with_metadata(self):
        """Test AutolabelMixin raises TypeError when default automatic_annotation=False but autolabel_metadata is provided."""
        metadata = AutolabelMetadata(models=[AutolabelModel(name="test_model", score=0.8)])
        with pytest.raises(
            TypeError, match="autolabel_metadata must be None when automatic_annotation is False"
        ):
            AutolabelMixin(autolabel_metadata=metadata)
