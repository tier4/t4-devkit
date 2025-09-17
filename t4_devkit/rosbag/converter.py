"""Conversion utilities for T4 Box3D to Autoware TrackedObject."""

from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

from .autoware_messages import (
    TrackedObject,
    TrackedObjectKinematics,
    ObjectClassification,
    Shape,
    Point,
    Quaternion,
    Vector3,
    Pose,
    Twist,
    Accel,
    PoseWithCovariance,
    TwistWithCovariance,
    AccelWithCovariance,
    UUID,
    Polygon,
)

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box3D


class Box3DToTrackedObjectConverter:
    """Converts T4 Box3D objects to Autoware TrackedObject messages."""

    def __init__(self):
        """Initialize the converter."""
        # Mapping from T4 semantic labels to Autoware classification constants
        self.label_mapping = {
            "car": ObjectClassification.CAR,
            "truck": ObjectClassification.TRUCK,
            "bus": ObjectClassification.BUS,
            "trailer": ObjectClassification.TRAILER,
            "motorcycle": ObjectClassification.MOTORCYCLE,
            "bicycle": ObjectClassification.BICYCLE,
            "pedestrian": ObjectClassification.PEDESTRIAN,
            "animal": ObjectClassification.ANIMAL,
        }

    def convert(self, box: Box3D) -> TrackedObject:
        """Convert a Box3D to TrackedObject.

        Args:
            box: T4 Box3D object to convert.

        Returns:
            TrackedObject message with converted data.
        """
        # Generate or use existing object ID
        if box.uuid:
            object_id = self._string_to_uuid(box.uuid)
        else:
            object_id = UUID.generate()

        # Convert classification
        classification = self._convert_classification(box)

        # Convert kinematics
        kinematics = self._convert_kinematics(box)

        # Convert shape
        shape = self._convert_shape(box)

        return TrackedObject(
            object_id=object_id,
            existence_probability=float(box.confidence),
            classification=[classification],
            kinematics=kinematics,
            shape=shape,
        )

    def _string_to_uuid(self, uuid_string: str) -> UUID:
        """Convert a string UUID to UUID message format.

        Args:
            uuid_string: String representation of UUID.

        Returns:
            UUID message.
        """
        # For simplicity, hash the string to generate consistent bytes
        import hashlib

        hash_bytes = hashlib.md5(uuid_string.encode()).digest()
        return UUID(uuid=list(hash_bytes))

    def _convert_classification(self, box: Box3D) -> ObjectClassification:
        """Convert T4 semantic label to ObjectClassification.

        Args:
            box: T4 Box3D object.

        Returns:
            ObjectClassification message.
        """
        label_name = box.semantic_label.name.lower()
        label_id = self.label_mapping.get(label_name, ObjectClassification.UNKNOWN)

        return ObjectClassification(label=label_id, probability=float(box.confidence))

    def _convert_kinematics(self, box: Box3D) -> TrackedObjectKinematics:
        """Convert T4 box kinematics to TrackedObjectKinematics.

        Args:
            box: T4 Box3D object.

        Returns:
            TrackedObjectKinematics message.
        """
        # Create pose
        position = Point(
            x=float(box.position[0]), y=float(box.position[1]), z=float(box.position[2])
        )

        orientation = Quaternion(
            x=float(box.rotation.x),
            y=float(box.rotation.y),
            z=float(box.rotation.z),
            w=float(box.rotation.w),
        )

        pose = Pose(position=position, orientation=orientation)

        # Create default covariance (6x6 matrix flattened to 36 elements)
        # Use identity matrix with small values for demonstration
        pose_covariance = [0.0] * 36
        for i in range(6):
            pose_covariance[i * 6 + i] = 0.01  # Small diagonal values

        pose_with_covariance = PoseWithCovariance(pose=pose, covariance=pose_covariance)

        # Create twist (velocity)
        if box.velocity is not None:
            linear_velocity = Vector3(
                x=float(box.velocity[0]), y=float(box.velocity[1]), z=float(box.velocity[2])
            )
        else:
            linear_velocity = Vector3(x=0.0, y=0.0, z=0.0)

        angular_velocity = Vector3(x=0.0, y=0.0, z=0.0)  # Default to zero

        twist = Twist(linear=linear_velocity, angular=angular_velocity)

        twist_covariance = [0.0] * 36
        for i in range(6):
            twist_covariance[i * 6 + i] = 0.01

        twist_with_covariance = TwistWithCovariance(twist=twist, covariance=twist_covariance)

        # Create acceleration (default to zero)
        linear_accel = Vector3(x=0.0, y=0.0, z=0.0)
        angular_accel = Vector3(x=0.0, y=0.0, z=0.0)
        accel = Accel(linear=linear_accel, angular=angular_accel)

        accel_covariance = [0.0] * 36
        for i in range(6):
            accel_covariance[i * 6 + i] = 0.01

        acceleration_with_covariance = AccelWithCovariance(accel=accel, covariance=accel_covariance)

        # Determine orientation availability
        orientation_availability = TrackedObjectKinematics.AVAILABLE

        # Check if object is stationary based on velocity
        is_stationary = False
        if box.velocity is not None:
            velocity_magnitude = np.linalg.norm(box.velocity)
            is_stationary = velocity_magnitude < 0.1  # Less than 0.1 m/s

        return TrackedObjectKinematics(
            pose_with_covariance=pose_with_covariance,
            twist_with_covariance=twist_with_covariance,
            acceleration_with_covariance=acceleration_with_covariance,
            orientation_availability=orientation_availability,
            is_stationary=is_stationary,
        )

    def _convert_shape(self, box: Box3D) -> Shape:
        """Convert T4 box shape to Autoware Shape.

        Args:
            box: T4 Box3D object.

        Returns:
            Shape message.
        """
        dimensions = Vector3(
            x=float(box.shape.size[0]),  # length
            y=float(box.shape.size[1]),  # width
            z=float(box.shape.size[2]),  # height
        )

        # For bounding box, footprint can be empty
        footprint = Polygon(points=[])

        return Shape(type=Shape.BOUNDING_BOX, footprint=footprint, dimensions=dimensions)

    def convert_multiple(self, boxes: list[Box3D]) -> list[TrackedObject]:
        """Convert multiple Box3D objects to TrackedObject messages.

        Args:
            boxes: List of Box3D objects to convert.

        Returns:
            List of TrackedObject messages.
        """
        return [self.convert(box) for box in boxes]

    @staticmethod
    def timestamp_to_ros_time(unix_timestamp: int) -> tuple[int, int]:
        """Convert unix timestamp (microseconds) to ROS time (sec, nanosec).

        Args:
            unix_timestamp: Unix timestamp in microseconds.

        Returns:
            Tuple of (seconds, nanoseconds).
        """
        # Convert microseconds to seconds and nanoseconds
        seconds = unix_timestamp // 1_000_000
        remaining_microseconds = unix_timestamp % 1_000_000
        nanoseconds = remaining_microseconds * 1000
        return int(seconds), int(nanoseconds)
