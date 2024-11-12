from t4_devkit.schema import SampleAnnotation


def test_sample_annotation_json(sample_annotation_json) -> None:
    """Test loading sample annotation from a json file."""
    _ = SampleAnnotation.from_json(sample_annotation_json)


def test_sample_annotation(sample_annotation_dict) -> None:
    """Test loading sample annotation from a dictionary."""
    _ = SampleAnnotation.from_dict(sample_annotation_dict)
