from t4_devkit.schema import SurfaceAnn


def test_surface_ann_json(surface_ann_json) -> None:
    """Test loading surface ann from a json file."""
    _ = SurfaceAnn.from_json(surface_ann_json)


def test_surface_ann(surface_ann_dict) -> None:
    """Test loading surface ann from a dictionary."""
    _ = SurfaceAnn.from_dict(surface_ann_dict)


def test_new_surface_ann(surface_ann_dict) -> None:
    """Test generating surface ann with a new token."""
    without_token = {k: v for k, v in surface_ann_dict.items() if k != "token"}
    ret = SurfaceAnn.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != surface_ann_dict["token"]
