from __future__ import annotations

from attrs import define, field, validators

__all__ = ["TopicMapping"]


def _validate_topic_name(instance: TopicMapping, attribute: object, value: str) -> None:
    """Validate that topic name starts with '/'."""
    if not value.startswith("/"):
        raise ValueError(f"ROS topic must start with '/': got '{value}'")


def _validate_translation(
    instance: TopicMapping, attribute: object, value: tuple[float, float, float] | None
) -> None:
    """Translation must be a 3-tuple of finite floats, or ``None``."""
    if value is None:
        return
    if not isinstance(value, tuple) or len(value) != 3:
        raise ValueError(f"sensor2ego_translation must be a tuple of 3 floats; got {value!r}")
    for v in value:
        if not isinstance(v, (int, float)) or v != v or abs(v) == float("inf"):
            raise ValueError(
                f"sensor2ego_translation entries must be finite numbers; got {value!r}"
            )


def _validate_rotation(
    instance: TopicMapping,
    attribute: object,
    value: tuple[float, float, float, float] | None,
) -> None:
    """Rotation must be a (w, x, y, z) quaternion or ``None``; near-unit norm enforced."""
    if value is None:
        return
    if not isinstance(value, tuple) or len(value) != 4:
        raise ValueError(
            f"sensor2ego_rotation must be a (w, x, y, z) tuple of 4 floats; got {value!r}"
        )
    for v in value:
        if not isinstance(v, (int, float)) or v != v or abs(v) == float("inf"):
            raise ValueError(f"sensor2ego_rotation entries must be finite numbers; got {value!r}")
    norm = sum(v * v for v in value) ** 0.5
    if not (0.98 < norm < 1.02):
        raise ValueError(f"sensor2ego_rotation must be approximately unit-norm; got |q|={norm:.4f}")


@define(frozen=True)
class TopicMapping:
    """Mapping from a T4 sensor channel name to a ROS topic name.

    Attributes:
        channel (str): T4 sensor channel name (e.g. ``"LIDAR_CONCAT"``).
        topic (str): ROS topic name (e.g. ``"/sensing/lidar/concatenated/pointcloud"``).
        sensor_type (str | None): Hesai sensor model name for PandarScan topics
            (e.g. ``"OT128"``, ``"XT32"``).
            Required when the topic type is ``pandar_msgs/msg/PandarScan``.
        frame_id (str | None): TF frame ID of the sensor (e.g. ``"hesai_top"``).
            When specified and ``/tf_static`` is available in the rosbag,
            the decoded point cloud is transformed from this frame to ``base_link``.
        sensor2ego_translation (tuple[float, float, float] | None): Explicit
            ``(x, y, z)`` translation from the sensor frame to ``base_link``,
            in metres. When both ``sensor2ego_translation`` and
            ``sensor2ego_rotation`` are set, the pair overrides the
            ``/tf_static`` chain — the decoded point cloud is transformed
            using these values and any ``frame_id`` is ignored for the
            sensor → base_link step. Use this when the bag's ``/tf_static``
            is missing or holds an outdated calibration.
        sensor2ego_rotation (tuple[float, float, float, float] | None):
            Explicit ``(w, x, y, z)`` quaternion (T4 convention) paired with
            ``sensor2ego_translation``. Both must be set together.
    """

    channel: str = field(validator=[validators.instance_of(str), validators.min_len(1)])
    topic: str = field(validator=[validators.instance_of(str), _validate_topic_name])
    sensor_type: str | None = field(default=None)
    frame_id: str | None = field(default=None)
    sensor2ego_translation: tuple[float, float, float] | None = field(
        default=None, validator=_validate_translation
    )
    sensor2ego_rotation: tuple[float, float, float, float] | None = field(
        default=None, validator=_validate_rotation
    )

    def __attrs_post_init__(self) -> None:
        # Cross-field validation: translation and rotation come as a pair.
        t = self.sensor2ego_translation
        r = self.sensor2ego_rotation
        if (t is None) != (r is None):
            raise ValueError(
                "sensor2ego_translation and sensor2ego_rotation must be set "
                "together (or both left as None)."
            )

    @property
    def has_explicit_sensor2ego(self) -> bool:
        """True iff an explicit sensor → base_link calibration is supplied."""
        return self.sensor2ego_translation is not None and self.sensor2ego_rotation is not None

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
