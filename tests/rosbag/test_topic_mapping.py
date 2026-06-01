from __future__ import annotations

import pytest

from t4_devkit.rosbag.topic_mapping import TopicMapping


class TestTopicMapping:
    def test_valid(self) -> None:
        m = TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")
        assert m.channel == "LIDAR_TOP"
        assert m.topic == "/sensing/lidar/top/pointcloud"

    def test_topic_must_start_with_slash(self) -> None:
        with pytest.raises(ValueError, match="must start with '/'"):
            TopicMapping(channel="LIDAR_TOP", topic="sensing/lidar/top/pointcloud")

    def test_channel_must_not_be_empty(self) -> None:
        with pytest.raises(ValueError):
            TopicMapping(channel="", topic="/topic")

    def test_channel_must_be_string(self) -> None:
        with pytest.raises(TypeError):
            TopicMapping(channel=123, topic="/topic")  # type: ignore[arg-type]

    def test_topic_must_be_string(self) -> None:
        with pytest.raises(TypeError):
            TopicMapping(channel="LIDAR", topic=123)  # type: ignore[arg-type]

    def test_from_dict(self) -> None:
        raw = {
            "LIDAR_TOP": "/sensing/lidar/top/pointcloud",
            "LIDAR_CONCAT": "/sensing/lidar/concatenated/pointcloud",
        }
        mappings = TopicMapping.from_dict(raw)
        assert len(mappings) == 2
        assert mappings[0].channel == "LIDAR_TOP"
        assert mappings[1].channel == "LIDAR_CONCAT"

    def test_from_dict_invalid_topic(self) -> None:
        with pytest.raises(ValueError, match="must start with '/'"):
            TopicMapping.from_dict({"LIDAR": "bad_topic"})

    def test_to_channel_dict(self) -> None:
        mappings = [
            TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud"),
            TopicMapping(channel="LIDAR_CONCAT", topic="/sensing/lidar/concatenated/pointcloud"),
        ]
        d = TopicMapping.to_channel_dict(mappings)
        assert d == {
            "LIDAR_TOP": "/sensing/lidar/top/pointcloud",
            "LIDAR_CONCAT": "/sensing/lidar/concatenated/pointcloud",
        }

    def test_frozen(self) -> None:
        m = TopicMapping(channel="LIDAR_TOP", topic="/topic")
        with pytest.raises(AttributeError):
            m.channel = "OTHER"  # type: ignore[misc]
