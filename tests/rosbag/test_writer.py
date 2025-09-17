"""Tests for ROS bag writer functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from t4_devkit.rosbag.writer import RosbagWriter
from t4_devkit.rosbag.messages import TrackedObjects, Header, TrackedObject, Point, Quaternion, Vector3


class TestRosbagWriter:
    """Test cases for RosbagWriter."""

    @pytest.fixture
    def temp_output_path(self) -> Path:
        """Create a temporary output path."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            return Path(tmp.name)

    @pytest.fixture
    def sample_tracked_objects(self) -> TrackedObjects:
        """Create sample TrackedObjects message."""
        header = Header(
            seq=1,
            stamp_sec=1234567890,
            stamp_nanosec=500000000,
            frame_id="base_link"
        )

        objects = [
            TrackedObject(
                object_id="car_001",
                classification="car",
                confidence=0.95,
                position=Point(x=10.0, y=5.0, z=1.5),
                orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                size=Vector3(x=4.5, y=2.0, z=1.8),
                velocity=Vector3(x=15.0, y=0.0, z=0.0),
                angular_velocity=Vector3(x=0.0, y=0.0, z=0.0)
            ),
            TrackedObject(
                object_id="pedestrian_001",
                classification="pedestrian",
                confidence=0.88,
                position=Point(x=5.0, y=2.0, z=1.0),
                orientation=Quaternion(x=0.0, y=0.0, z=0.707, w=0.707),
                size=Vector3(x=0.6, y=0.6, z=1.7),
                velocity=Vector3(x=1.0, y=0.5, z=0.0),
                angular_velocity=Vector3(x=0.0, y=0.0, z=0.1)
            )
        ]

        return TrackedObjects(header=header, objects=objects)

    def test_writer_context_manager(self, temp_output_path: Path):
        """Test RosbagWriter as context manager."""
        with RosbagWriter(temp_output_path) as writer:
            assert writer.output_path == temp_output_path
            assert len(writer.messages) == 0

        # Check that file was created
        assert temp_output_path.exists()

    def test_add_topic(self, temp_output_path: Path):
        """Test adding topics to the writer."""
        writer = RosbagWriter(temp_output_path)

        topic_name = "/perception/tracked_objects"
        message_type = "autoware_auto_perception_msgs/TrackedObjects"
        frame_id = "base_link"

        writer.add_topic(topic_name, message_type, frame_id)

        assert topic_name in writer.topic_info
        assert writer.topic_info[topic_name]["message_type"] == message_type
        assert writer.topic_info[topic_name]["frame_id"] == frame_id

    def test_write_tracked_objects(self, temp_output_path: Path, sample_tracked_objects: TrackedObjects):
        """Test writing TrackedObjects messages."""
        writer = RosbagWriter(temp_output_path)
        topic_name = "/perception/tracked_objects"

        writer.add_topic(topic_name, "autoware_auto_perception_msgs/TrackedObjects")
        writer.write_tracked_objects(topic_name, sample_tracked_objects, 1234567890, 500000000)

        assert len(writer.messages) == 1

        message = writer.messages[0]
        assert message["topic"] == topic_name
        assert message["timestamp"]["sec"] == 1234567890
        assert message["timestamp"]["nanosec"] == 500000000
        assert len(message["message"]["objects"]) == 2

    def test_message_sorting(self, temp_output_path: Path):
        """Test that messages are sorted by timestamp when finalized."""
        writer = RosbagWriter(temp_output_path)
        topic_name = "/test_topic"

        writer.add_topic(topic_name, "test_msgs/TestMessage")

        # Create messages with out-of-order timestamps
        header1 = Header(seq=1, stamp_sec=1000, stamp_nanosec=0, frame_id="base_link")
        header2 = Header(seq=2, stamp_sec=999, stamp_nanosec=500000000, frame_id="base_link")
        header3 = Header(seq=3, stamp_sec=1000, stamp_nanosec=250000000, frame_id="base_link")

        objects = []

        # Add messages in non-chronological order
        writer.write_tracked_objects(topic_name, TrackedObjects(header=header1, objects=objects), 1000, 0)
        writer.write_tracked_objects(topic_name, TrackedObjects(header=header2, objects=objects), 999, 500000000)
        writer.write_tracked_objects(topic_name, TrackedObjects(header=header3, objects=objects), 1000, 250000000)

        writer.finalize()

        # Load and check the written file
        with open(temp_output_path) as f:
            data = json.load(f)

        # Should be sorted: 999.5, 1000.25, 1000.0
        assert data[0]["timestamp"]["sec"] == 999
        assert data[0]["timestamp"]["nanosec"] == 500000000
        assert data[1]["timestamp"]["sec"] == 1000
        assert data[1]["timestamp"]["nanosec"] == 250000000
        assert data[2]["timestamp"]["sec"] == 1000
        assert data[2]["timestamp"]["nanosec"] == 0

    def test_metadata_creation(self, temp_output_path: Path):
        """Test metadata file creation."""
        with RosbagWriter(temp_output_path) as writer:
            writer.add_topic("/topic1", "msg_type1", "frame1")
            writer.add_topic("/topic2", "msg_type2", "frame2")

        # Check metadata file exists
        metadata_path = temp_output_path.parent / f"{temp_output_path.stem}_metadata.json"
        assert metadata_path.exists()

        # Load and check metadata content
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert "topics" in metadata
        assert "message_count" in metadata
        assert "format_version" in metadata
        assert "description" in metadata

        assert "/topic1" in metadata["topics"]
        assert "/topic2" in metadata["topics"]
        assert metadata["topics"]["/topic1"]["message_type"] == "msg_type1"
        assert metadata["topics"]["/topic1"]["frame_id"] == "frame1"

    def test_output_directory_creation(self):
        """Test that output directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.json"

            with RosbagWriter(output_path) as writer:
                pass

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_complete_message_structure(self, temp_output_path: Path, sample_tracked_objects: TrackedObjects):
        """Test complete message structure in output."""
        with RosbagWriter(temp_output_path) as writer:
            topic_name = "/perception/tracked_objects"
            writer.add_topic(topic_name, "autoware_auto_perception_msgs/TrackedObjects")
            writer.write_tracked_objects(topic_name, sample_tracked_objects, 1234567890, 500000000)

        # Load and verify the complete structure
        with open(temp_output_path) as f:
            data = json.load(f)

        assert len(data) == 1
        message = data[0]

        # Check top-level structure
        assert "topic" in message
        assert "timestamp" in message
        assert "message" in message

        # Check message structure
        msg_data = message["message"]
        assert "header" in msg_data
        assert "objects" in msg_data

        # Check header structure
        header = msg_data["header"]
        assert "seq" in header
        assert "stamp" in header
        assert "frame_id" in header

        # Check objects structure
        objects = msg_data["objects"]
        assert len(objects) == 2

        obj = objects[0]
        required_fields = [
            "object_id", "classification", "confidence", "position",
            "orientation", "size", "velocity", "angular_velocity"
        ]
        for field in required_fields:
            assert field in obj

        # Check nested structures
        assert "x" in obj["position"] and "y" in obj["position"] and "z" in obj["position"]
        assert "x" in obj["orientation"] and "y" in obj["orientation"] and "z" in obj["orientation"] and "w" in obj["orientation"]