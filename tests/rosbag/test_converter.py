"""Tests for Box3D to TrackedObject conversion."""

from __future__ import annotations

import pytest
import numpy as np
from pyquaternion import Quaternion

from t4_devkit.dataclass import Box3D, SemanticLabel, Shape, ShapeType
from t4_devkit.rosbag.converter import Box3DToTrackedObjectConverter
from t4_devkit.rosbag.messages import TrackedObject, Point, Quaternion as ROSQuaternion, Vector3


class TestBox3DToTrackedObjectConverter:
    """Test cases for Box3D to TrackedObject conversion."""

    @pytest.fixture
    def converter(self) -> Box3DToTrackedObjectConverter:
        """Create a converter instance."""
        return Box3DToTrackedObjectConverter()

    @pytest.fixture
    def sample_box3d(self) -> Box3D:
        """Create a sample Box3D for testing."""
        return Box3D(
            unix_time=1000000,  # microseconds
            frame_id="base_link",
            semantic_label=SemanticLabel(name="car", attributes=["moving"]),
            confidence=0.95,
            uuid="test_car_123",
            position=np.array([10.0, 5.0, 1.5]),
            rotation=Quaternion(w=1.0, x=0.0, y=0.0, z=0.0),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=np.array([4.5, 2.0, 1.8])),
            velocity=np.array([15.0, 0.0, 0.0])
        )

    def test_convert_basic_fields(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test basic field conversion."""
        result = converter.convert(sample_box3d)

        assert isinstance(result, TrackedObject)
        assert result.object_id == "test_car_123"
        assert result.classification == "car"
        assert result.confidence == 0.95

    def test_convert_position(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test position conversion."""
        result = converter.convert(sample_box3d)

        assert isinstance(result.position, Point)
        assert result.position.x == 10.0
        assert result.position.y == 5.0
        assert result.position.z == 1.5

    def test_convert_orientation(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test orientation conversion."""
        result = converter.convert(sample_box3d)

        assert isinstance(result.orientation, ROSQuaternion)
        assert result.orientation.w == 1.0
        assert result.orientation.x == 0.0
        assert result.orientation.y == 0.0
        assert result.orientation.z == 0.0

    def test_convert_size(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test size conversion."""
        result = converter.convert(sample_box3d)

        assert isinstance(result.size, Vector3)
        assert result.size.x == 4.5  # length
        assert result.size.y == 2.0  # width
        assert result.size.z == 1.8  # height

    def test_convert_velocity(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test velocity conversion."""
        result = converter.convert(sample_box3d)

        assert isinstance(result.velocity, Vector3)
        assert result.velocity.x == 15.0
        assert result.velocity.y == 0.0
        assert result.velocity.z == 0.0

    def test_convert_no_velocity(self, converter: Box3DToTrackedObjectConverter):
        """Test conversion when velocity is None."""
        box_no_velocity = Box3D(
            unix_time=1000000,
            frame_id="base_link",
            semantic_label=SemanticLabel(name="pedestrian"),
            position=np.array([5.0, 2.0, 1.0]),
            rotation=Quaternion(w=1.0, x=0.0, y=0.0, z=0.0),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=np.array([0.6, 0.6, 1.7])),
            velocity=None
        )

        result = converter.convert(box_no_velocity)

        assert result.velocity.x == 0.0
        assert result.velocity.y == 0.0
        assert result.velocity.z == 0.0

    def test_convert_no_uuid(self, converter: Box3DToTrackedObjectConverter):
        """Test conversion when UUID is not provided."""
        box_no_uuid = Box3D(
            unix_time=1000000,
            frame_id="base_link",
            semantic_label=SemanticLabel(name="bicycle"),
            position=np.array([3.0, 1.0, 1.0]),
            rotation=Quaternion(w=1.0, x=0.0, y=0.0, z=0.0),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=np.array([2.0, 0.7, 1.5])),
            uuid=None
        )

        result = converter.convert(box_no_uuid)

        # Should generate an object_id
        assert result.object_id.startswith("bicycle_")
        assert result.classification == "bicycle"

    def test_convert_multiple(self, converter: Box3DToTrackedObjectConverter, sample_box3d: Box3D):
        """Test conversion of multiple boxes."""
        box2 = Box3D(
            unix_time=1000000,
            frame_id="base_link",
            semantic_label=SemanticLabel(name="truck"),
            position=np.array([20.0, 10.0, 2.0]),
            rotation=Quaternion(w=0.707, x=0.0, y=0.0, z=0.707),
            shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=np.array([8.0, 2.5, 3.0])),
            uuid="truck_456"
        )

        boxes = [sample_box3d, box2]
        results = converter.convert_multiple(boxes)

        assert len(results) == 2
        assert results[0].classification == "car"
        assert results[1].classification == "truck"
        assert results[0].object_id == "test_car_123"
        assert results[1].object_id == "truck_456"

    def test_timestamp_conversion(self, converter: Box3DToTrackedObjectConverter):
        """Test timestamp conversion from microseconds to ROS time."""
        # Test timestamp: 1,234,567,890 microseconds = 1234.567890 seconds
        unix_timestamp = 1234567890
        sec, nanosec = converter.timestamp_to_ros_time(unix_timestamp)

        assert sec == 1234
        assert nanosec == 567890000  # 567890 microseconds = 567890000 nanoseconds

    def test_timestamp_conversion_edge_cases(self, converter: Box3DToTrackedObjectConverter):
        """Test timestamp conversion edge cases."""
        # Test zero
        sec, nanosec = converter.timestamp_to_ros_time(0)
        assert sec == 0
        assert nanosec == 0

        # Test exactly 1 second
        sec, nanosec = converter.timestamp_to_ros_time(1000000)
        assert sec == 1
        assert nanosec == 0

        # Test less than 1 second
        sec, nanosec = converter.timestamp_to_ros_time(500000)
        assert sec == 0
        assert nanosec == 500000000