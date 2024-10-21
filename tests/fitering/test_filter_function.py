from t4_devkit.filtering.functional import (
    FilterByDistance,
    FilterByLabel,
    FilterByNumPoints,
    FilterByPosition,
    FilterBySpeed,
    FilterByUUID,
)


def test_filter_by_label(dummy_box3ds, dummy_box2ds) -> None:
    """Test `FilterByLabel` class.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
        dummy_box2ds (list[Box2D]): List of 2D boxes.
    """
    box_filter = FilterByLabel(labels=["car"])

    answer3d = [box for box in dummy_box3ds if box_filter(box)]
    answer2d = [box for box in dummy_box2ds if box_filter(box)]

    assert len(answer3d) == 1
    assert len(answer2d) == 1


def test_filter_by_uuid(dummy_box3ds, dummy_box2ds) -> None:
    """Test `FilterByUUID` class.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
        dummy_box2ds (list[Box2D]): List of 2D boxes.
    """
    box_filter = FilterByUUID(uuids=["car3d_1", "car2d_1"])

    answer3d = [box for box in dummy_box3ds if box_filter(box)]
    answer2d = [box for box in dummy_box2ds if box_filter(box)]

    assert len(answer3d) == 1
    assert len(answer2d) == 1


def test_filter_by_distance(dummy_box3ds, dummy_box2ds, dummy_tf_buffer) -> None:
    """Test `FilterByDistance`.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
        dummy_box2ds (list[Box2D]): List of 2D boxes.
        dummy_tf_buffer (TransformBuffer): Transformation buffer.
    """
    box_filter = FilterByDistance(min_distance=0.0, max_distance=10.0)

    answer3d = [
        box
        for box in dummy_box3ds
        if box_filter(box, dummy_tf_buffer.lookup_transform(box.frame_id, "base_link"))
    ]

    answer2d = [
        box
        for box in dummy_box2ds
        if box_filter(box, dummy_tf_buffer.lookup_transform(box.frame_id, "base_link"))
    ]

    assert len(answer3d) == 3
    assert len(answer2d) == 3


def test_filter_by_position(dummy_box3ds, dummy_box2ds, dummy_tf_buffer) -> None:
    """Test `FilterByPosition`.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
        dummy_box2ds (list[Box2D]): List of 2D boxes.
        dummy_tf_buffer (TransformBuffer): Transformation buffer.
    """
    box_filter = FilterByPosition(min_xy=(0.0, 0.0), max_xy=(10.0, 10.0))

    answer3d = [
        box
        for box in dummy_box3ds
        if box_filter(box, dummy_tf_buffer.lookup_transform(box.frame_id, "base_link"))
    ]

    answer2d = [
        box
        for box in dummy_box2ds
        if box_filter(box, dummy_tf_buffer.lookup_transform(box.frame_id, "base_link"))
    ]

    assert len(answer3d) == 1
    assert len(answer2d) == 3


def test_filter_by_speed(dummy_box3ds) -> None:
    """Test `FilterBySpeed`.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
    """
    box_filter = FilterBySpeed(min_speed=0.5, max_speed=2.0)

    answer = [box for box in dummy_box3ds if box_filter(box)]

    assert len(answer) == 3


def test_filter_by_num_points(dummy_box3ds) -> None:
    """Test `FilterByNumPoints`.

    Args:
        dummy_box3ds (list[Box3D]): List of 3D boxes.
    """
    box_filter = FilterByNumPoints(min_num_points=0)

    answer = [box for box in dummy_box3ds if box_filter(box)]

    assert len(answer) == 3
