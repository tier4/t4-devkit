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

    def test_sensor2ego_defaults_none(self) -> None:
        m = TopicMapping(channel="LIDAR_TOP", topic="/topic")
        assert m.sensor2ego_translation is None
        assert m.sensor2ego_rotation is None
        assert m.has_explicit_sensor2ego is False

    def test_sensor2ego_pair_valid(self) -> None:
        m = TopicMapping(
            channel="LIDAR_TOP",
            topic="/topic",
            sensor2ego_translation=(0.9, 0.0, 2.18),
            sensor2ego_rotation=(1.0, 0.0, 0.0, 0.0),
        )
        assert m.has_explicit_sensor2ego is True
        assert m.sensor2ego_translation == (0.9, 0.0, 2.18)
        assert m.sensor2ego_rotation == (1.0, 0.0, 0.0, 0.0)

    def test_sensor2ego_pair_required_together(self) -> None:
        with pytest.raises(ValueError, match="together"):
            TopicMapping(
                channel="LIDAR_TOP",
                topic="/topic",
                sensor2ego_translation=(0.0, 0.0, 0.0),
            )
        with pytest.raises(ValueError, match="together"):
            TopicMapping(
                channel="LIDAR_TOP",
                topic="/topic",
                sensor2ego_rotation=(1.0, 0.0, 0.0, 0.0),
            )

    def test_sensor2ego_translation_must_be_3tuple(self) -> None:
        with pytest.raises(ValueError, match="3 floats"):
            TopicMapping(
                channel="LIDAR_TOP",
                topic="/topic",
                sensor2ego_translation=(0.0, 0.0),  # type: ignore[arg-type]
                sensor2ego_rotation=(1.0, 0.0, 0.0, 0.0),
            )

    def test_sensor2ego_rotation_must_be_4tuple(self) -> None:
        with pytest.raises(ValueError, match="4 floats"):
            TopicMapping(
                channel="LIDAR_TOP",
                topic="/topic",
                sensor2ego_translation=(0.0, 0.0, 0.0),
                sensor2ego_rotation=(1.0, 0.0, 0.0),  # type: ignore[arg-type]
            )

    def test_sensor2ego_rotation_must_be_unit_norm(self) -> None:
        with pytest.raises(ValueError, match="unit-norm"):
            TopicMapping(
                channel="LIDAR_TOP",
                topic="/topic",
                sensor2ego_translation=(0.0, 0.0, 0.0),
                sensor2ego_rotation=(2.0, 0.0, 0.0, 0.0),
            )
