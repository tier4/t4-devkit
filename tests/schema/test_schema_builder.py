from t4_devkit.schema import SchemaName, build_schema


def test_build_attribute(attribute_json) -> None:
    """Test building attribute."""
    _ = build_schema(SchemaName.ATTRIBUTE, attribute_json)


def test_build_calibrated_sensor(calibrated_sensor_json) -> None:
    """Test building calibrated sensor."""
    _ = build_schema(SchemaName.CALIBRATED_SENSOR, calibrated_sensor_json)


def test_build_category(category_json) -> None:
    """Test building category."""
    _ = build_schema(SchemaName.CATEGORY, category_json)


def test_build_ego_pose(ego_pose_json) -> None:
    """Test building ego pose."""
    _ = build_schema(SchemaName.EGO_POSE, ego_pose_json)


def test_build_instance(instance_json) -> None:
    """Test building instance."""
    _ = build_schema(SchemaName.INSTANCE, instance_json)


def test_build_log(log_json) -> None:
    """Test building log."""
    _ = build_schema(SchemaName.LOG, log_json)


def test_build_map(map_json) -> None:
    """Test building map."""
    _ = build_schema(SchemaName.MAP, map_json)


def test_build_object_ann(object_ann_json) -> None:
    """Test building object ann."""
    _ = build_schema(SchemaName.OBJECT_ANN, object_ann_json)


def test_build_sample_annotation(sample_annotation_json) -> None:
    """Test building sample annotation."""
    _ = build_schema(SchemaName.SAMPLE_ANNOTATION, sample_annotation_json)


def test_build_sample_data(sample_data_json) -> None:
    """Test building sample data."""
    _ = build_schema(SchemaName.SAMPLE_DATA, sample_data_json)


def test_build_sample(sample_json) -> None:
    """Test building sample."""
    _ = build_schema(SchemaName.SAMPLE, sample_json)


def test_build_sensor(sensor_json) -> None:
    """Test building sensor."""
    _ = build_schema(SchemaName.SENSOR, sensor_json)


def test_build_surface_ann(surface_ann_json) -> None:
    """Test building surface ann."""
    _ = build_schema(SchemaName.SURFACE_ANN, surface_ann_json)


def test_build_vehicle_state(vehicle_state_json) -> None:
    """Test building vehicle state."""
    _ = build_schema(SchemaName.VEHICLE_STATE, vehicle_state_json)


def test_build_visibility(visibility_json) -> None:
    """Test building visibility."""
    _ = build_schema(SchemaName.VISIBILITY, visibility_json)
