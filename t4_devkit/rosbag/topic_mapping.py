from __future__ import annotations

from attrs import define, field, validators

__all__ = ["TopicMapping"]


def _validate_topic_name(instance: TopicMapping, attribute: object, value: str) -> None:
    """Validate that topic name starts with '/'."""
    if not value.startswith("/"):
        raise ValueError(f"ROS topic must start with '/': got '{value}'")


@define(frozen=True)
class TopicMapping:
    """Mapping from a T4 sensor channel name to a ROS topic name.

    Attributes:
        channel (str): T4 sensor channel name (e.g. ``"LIDAR_CONCAT"``).
        topic (str): ROS topic name (e.g. ``"/sensing/lidar/concatenated/pointcloud"``).
    """

    channel: str = field(validator=[validators.instance_of(str), validators.min_len(1)])
    topic: str = field(validator=[validators.instance_of(str), _validate_topic_name])

    @staticmethod
    def from_dict(mapping: dict[str, str]) -> list[TopicMapping]:
        """Create a list of TopicMapping from a dict.

        Args:
            mapping: Dict mapping channel names to ROS topic names.

        Returns:
            List of TopicMapping instances.

        Raises:
            TypeError: If keys or values are not strings.
            ValueError: If a topic name does not start with ``/``.
        """
        return [TopicMapping(channel=k, topic=v) for k, v in mapping.items()]

    @staticmethod
    def to_channel_dict(mappings: list[TopicMapping]) -> dict[str, str]:
        """Convert a list of TopicMapping to a channel-to-topic dict.

        Args:
            mappings: List of TopicMapping instances.

        Returns:
            Dict mapping channel names to topic names.
        """
        return {m.channel: m.topic for m in mappings}
