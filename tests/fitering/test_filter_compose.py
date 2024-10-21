from t4_devkit.filtering import BoxFilter, FilterParams


def test_composite_filter(dummy_box3ds, dummy_box2ds, dummy_tf_buffer) -> None:
    """Test `BoxFilter` compositing the box filters.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
        dummy_box2ds (list[Box2D]): List of 2D boxes.
        dummy_tf_buffer (TransformBuffer): Transformation buffer.
    """
    params = FilterParams(
        labels=["car"],
        uuids=["car3d_1", "car2d_1"],
        min_distance=0.0,
        max_distance=2.0,
        min_xy=(0.0, 0.0),
        max_xy=(2.0, 2.0),
        min_speed=0.5,
        max_speed=2.0,
        min_num_points=0,
    )

    box_filter = BoxFilter(params, dummy_tf_buffer)

    answer3d = box_filter(dummy_box3ds)
    answer2d = box_filter(dummy_box2ds)

    assert len(answer3d) == 1
    assert len(answer2d) == 1
