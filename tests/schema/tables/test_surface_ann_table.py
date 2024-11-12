from t4_devkit.schema import SurfaceAnn


def test_surface_ann_json(surface_ann_json) -> None:
    """Test loading surface ann from a json file."""
    _ = SurfaceAnn.from_json(surface_ann_json)


def test_surface_ann(surface_ann_dict) -> None:
    """Test loading surface ann from a dictionary."""
    _ = SurfaceAnn.from_dict(surface_ann_dict)
