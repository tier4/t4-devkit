"""Conversion utilities for T4 Box3D to Autoware TrackedObject."""

from __future__ import annotations

import hashlib
import numpy as np
from typing import TYPE_CHECKING

try:
    # Import actual Autoware messages when sourced
    from autoware_perception_msgs.msg import (
        TrackedObject,
        TrackedObjects,
        TrackedObjectKinematics,
        ObjectClassification,
        Shape,
    )
    from geometry_msgs.msg import (
        Point,
        Point32,
        Quaternion,
        Vector3,
        Pose,
        PoseWithCovariance,
        Twist,
        TwistWithCovariance,
        Accel,
        AccelWithCovariance,
    )
    from unique_identifier_msgs.msg import UUID
    from std_msgs.msg import Header
    AUTOWARE_AVAILABLE = True
except ImportError:
    AUTOWARE_AVAILABLE = False
    print("Warning: Autoware messages not available. Please source your ROS2/Autoware workspace.")

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box3D


class Box3DToTrackedObjectConverter:
    """Converts T4 Box3D objects to Autoware TrackedObject messages."""

    def __init__(self):
        """Initialize the converter."""
        if not AUTOWARE_AVAILABLE:
            print(
                "Warning: Running without Autoware messages. Output will be JSON format only.")

        # Mapping from T4 semantic labels to Autoware classification constants
        # These constants are defined in ObjectClassification message
        self.label_mapping = {
            "car": 1,  # ObjectClassification.CAR
            "truck": 2,  # ObjectClassification.TRUCK
            "bus": 3,  # ObjectClassification.BUS
            "trailer": 4,  # ObjectClassification.TRAILER
            "motorcycle": 5,  # ObjectClassification.MOTORCYCLE
            "bicycle": 6,  # ObjectClassification.BICYCLE
            "pedestrian": 7,  # ObjectClassification.PEDESTRIAN
            # ObjectClassification.UNKNOWN (no animal class in Autoware)
            "animal": 0,
        }

    def convert(self, box: Box3D):
        """Convert a Box3D to TrackedObject.

        Args:
            box: T4 Box3D object to convert.

        Returns:
            TrackedObject message with converted data (or dict if messages not available).
        """
        if not AUTOWARE_AVAILABLE:
            return self._convert_to_dict(box)
        # Generate or use existing object ID
        if box.uuid:
            object_id = self._string_to_uuid(box.uuid)
        else:
            # Generate a random UUID if none provided
            import uuid
            uuid_bytes = uuid.uuid4().bytes
            object_id = UUID()
            object_id.uuid = list(uuid_bytes)

        # Convert classification
        classification = self._convert_classification(box)

        # Convert kinematics
        kinematics = self._convert_kinematics(box)

        # Convert shape
        shape = self._convert_shape(box)

        tracked_object = TrackedObject()
        tracked_object.object_id = object_id
        tracked_object.existence_probability = float(box.confidence)
        tracked_object.classification = [classification]
        tracked_object.kinematics = kinematics
        tracked_object.shape = shape
        return tracked_object

    def _string_to_uuid(self, uuid_string: str) -> UUID:
        """Convert a string UUID to UUID message format.

        Args:
            uuid_string: String representation of UUID.

        Returns:
            UUID message.
        """
        # Hash the string to generate consistent 16 bytes
        hash_bytes = hashlib.md5(uuid_string.encode()).digest()

        # Create UUID message
        uuid_msg = UUID()
        uuid_msg.uuid = list(hash_bytes)
        return uuid_msg

    def _convert_classification(self, box: Box3D) -> ObjectClassification:
        """Convert T4 semantic label to ObjectClassification.

        Args:
            box: T4 Box3D object.

        Returns:
            ObjectClassification message.
        """
        label_name = box.semantic_label.name.lower()
        label_id = self.label_mapping.get(label_name, 0)  # 0 = UNKNOWN

        classification = ObjectClassification()
        classification.label = label_id
        classification.probability = float(box.confidence)
        return classification

    def _convert_kinematics(self, box: Box3D) -> TrackedObjectKinematics:
        """Convert T4 box kinematics to TrackedObjectKinematics.

        Args:
            box: T4 Box3D object.

        Returns:
            TrackedObjectKinematics message.
        """
        # Create pose
        position = Point()
        position.x = float(box.position[0])
        position.y = float(box.position[1])
        position.z = float(box.position[2])

        orientation = Quaternion()
        orientation.x = float(box.rotation.x)
        orientation.y = float(box.rotation.y)
        orientation.z = float(box.rotation.z)
        orientation.w = float(box.rotation.w)

        pose = Pose()
        pose.position = position
        pose.orientation = orientation

        # Create default covariance (6x6 matrix flattened to 36 elements)
        # Use identity matrix with small values for demonstration
        pose_with_covariance = PoseWithCovariance()
        pose_with_covariance.pose = pose
        # Set small diagonal covariance values
        pose_with_covariance.covariance = [0.0] * 36
        for i in range(6):
            pose_with_covariance.covariance[i * 6 + i] = 0.01

        # Create twist (velocity)
        linear_velocity = Vector3()
        if box.velocity is not None:
            linear_velocity.x = float(box.velocity[0])
            linear_velocity.y = float(box.velocity[1])
            linear_velocity.z = float(box.velocity[2])
        else:
            linear_velocity.x = 0.0
            linear_velocity.y = 0.0
            linear_velocity.z = 0.0

        angular_velocity = Vector3()
        angular_velocity.x = 0.0
        angular_velocity.y = 0.0
        angular_velocity.z = 0.0

        twist = Twist()
        twist.linear = linear_velocity
        twist.angular = angular_velocity

        twist_with_covariance = TwistWithCovariance()
        twist_with_covariance.twist = twist
        twist_with_covariance.covariance = [0.0] * 36
        for i in range(6):
            twist_with_covariance.covariance[i * 6 + i] = 0.01

        # Create acceleration (default to zero)
        linear_accel = Vector3()
        linear_accel.x = 0.0
        linear_accel.y = 0.0
        linear_accel.z = 0.0

        angular_accel = Vector3()
        angular_accel.x = 0.0
        angular_accel.y = 0.0
        angular_accel.z = 0.0

        accel = Accel()
        accel.linear = linear_accel
        accel.angular = angular_accel

        acceleration_with_covariance = AccelWithCovariance()
        acceleration_with_covariance.accel = accel
        acceleration_with_covariance.covariance = [0.0] * 36
        for i in range(6):
            acceleration_with_covariance.covariance[i * 6 + i] = 0.01

        # Determine orientation availability (2 = AVAILABLE)
        orientation_availability = 2  # TrackedObjectKinematics.AVAILABLE

        # Check if object is stationary based on velocity
        is_stationary = False
        if box.velocity is not None:
            velocity_magnitude = np.linalg.norm(box.velocity)
            is_stationary = bool(velocity_magnitude < 0.1)  # Less than 0.1 m/s

        kinematics = TrackedObjectKinematics()
        kinematics.pose_with_covariance = pose_with_covariance
        kinematics.twist_with_covariance = twist_with_covariance
        kinematics.acceleration_with_covariance = acceleration_with_covariance
        kinematics.orientation_availability = orientation_availability
        kinematics.is_stationary = is_stationary
        return kinematics

    def _convert_shape(self, box: Box3D) -> Shape:
        """Convert T4 box shape to Autoware Shape.

        Args:
            box: T4 Box3D object.

        Returns:
            Shape message.
        """
        shape = Shape()
        shape.type = 0  # Shape.BOUNDING_BOX

        # Set dimensions. BB dimensions dont have the same order as T4 Box3D
        shape.dimensions.x = float(box.shape.size[1])  # length
        shape.dimensions.y = float(box.shape.size[0])  # width
        shape.dimensions.z = float(box.shape.size[2])  # height

        # Footprint is typically empty for bounding boxes
        # (polygon points are used for more complex shapes)

        return shape

    def convert_multiple(self, boxes: list[Box3D]) -> list[TrackedObject]:
        """Convert multiple Box3D objects to TrackedObject messages.

        Args:
            boxes: List of Box3D objects to convert.

        Returns:
            List of TrackedObject messages.
        """
        return [self.convert(box) for box in boxes]

    def _convert_to_dict(self, box: Box3D) -> dict:
        """Convert Box3D to dictionary format when ROS messages are not available.

        Args:
            box: T4 Box3D object to convert.

        Returns:
            Dictionary representation of TrackedObject.
        """
        # Generate or use existing object ID
        if box.uuid:
            uuid_bytes = hashlib.md5(box.uuid.encode()).digest()
        else:
            import uuid
            uuid_bytes = uuid.uuid4().bytes

        label_name = box.semantic_label.name.lower()
        label_id = self.label_mapping.get(label_name, 0)

        return {
            "object_id": {"uuid": list(uuid_bytes)},
            "existence_probability": float(box.confidence),
            "classification": [{
                "label": label_id,
                "probability": float(box.confidence)
            }],
            "kinematics": {
                "pose_with_covariance": {
                    "pose": {
                        "position": {
                            "x": float(box.position[0]),
                            "y": float(box.position[1]),
                            "z": float(box.position[2])
                        },
                        "orientation": {
                            "x": float(box.rotation.x),
                            "y": float(box.rotation.y),
                            "z": float(box.rotation.z),
                            "w": float(box.rotation.w)
                        }
                    },
                    "covariance": [0.01 if i == j else 0.0 for i in range(6) for j in range(6)]
                },
                "twist_with_covariance": {
                    "twist": {
                        "linear": {
                            "x": float(box.velocity[0]) if box.velocity is not None else 0.0,
                            "y": float(box.velocity[1]) if box.velocity is not None else 0.0,
                            "z": float(box.velocity[2]) if box.velocity is not None else 0.0
                        },
                        "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
                    },
                    "covariance": [0.01 if i == j else 0.0 for i in range(6) for j in range(6)]
                },
                "orientation_availability": 2,  # AVAILABLE
                "is_stationary": False if box.velocity is not None and np.linalg.norm(box.velocity) > 0.1 else True
            },
            "shape": {
                "type": 0,  # BOUNDING_BOX
                "dimensions": {
                    "x": float(box.shape.size[0]),
                    "y": float(box.shape.size[1]),
                    "z": float(box.shape.size[2])
                },
                "footprint": {"points": []}
            }
        }

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
