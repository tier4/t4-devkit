"""Autoware message data structures for ROS bag conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import uuid


@dataclass
class Point:
    """3D point representation."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Quaternion:
    """Quaternion representation for rotations."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


@dataclass
class Vector3:
    """3D vector representation."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Pose:
    """Pose with position and orientation."""
    position: Point
    orientation: Quaternion


@dataclass
class Twist:
    """Velocity representation with linear and angular components."""
    linear: Vector3
    angular: Vector3


@dataclass
class Accel:
    """Acceleration representation with linear and angular components."""
    linear: Vector3
    angular: Vector3


@dataclass
class PoseWithCovariance:
    """Pose with uncertainty."""
    pose: Pose
    covariance: List[float]  # 36 elements (6x6 matrix)


@dataclass
class TwistWithCovariance:
    """Twist with uncertainty."""
    twist: Twist
    covariance: List[float]  # 36 elements (6x6 matrix)


@dataclass
class AccelWithCovariance:
    """Acceleration with uncertainty."""
    accel: Accel
    covariance: List[float]  # 36 elements (6x6 matrix)


@dataclass
class TrackedObjectKinematics:
    """Kinematics information for a tracked object."""
    pose_with_covariance: PoseWithCovariance
    twist_with_covariance: TwistWithCovariance
    acceleration_with_covariance: AccelWithCovariance
    orientation_availability: int = 0  # UNAVAILABLE = 0, SIGN_UNKNOWN = 1, AVAILABLE = 2
    is_stationary: bool = False


@dataclass
class ObjectClassification:
    """Classification information for an object."""
    label: int  # UNKNOWN=0, CAR=1, TRUCK=2, BUS=3, TRAILER=4, MOTORCYCLE=5, BICYCLE=6, PEDESTRIAN=7
    probability: float


@dataclass
class ObjectId:
    """Unique identifier for an object."""
    uuid: List[int]  # 16 bytes

    @classmethod
    def generate(cls) -> ObjectId:
        """Generate a new random ObjectId."""
        uuid_bytes = uuid.uuid4().bytes
        return cls(uuid=list(uuid_bytes))


@dataclass
class UUID:
    """UUID representation (alias for ObjectId for compatibility)."""
    uuid: List[int]  # 16 bytes

    @classmethod
    def generate(cls) -> UUID:
        """Generate a new random UUID."""
        uuid_bytes = uuid.uuid4().bytes
        return cls(uuid=list(uuid_bytes))


@dataclass
class Polygon:
    """Polygon shape representation."""
    points: List[Point]


@dataclass
class Shape:
    """Shape information for an object."""
    type: int = 0  # BOUNDING_BOX = 0, CYLINDER = 1, POLYGON = 2
    dimensions: Vector3 = None
    footprint: Optional[List[Point]] = None

    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = Vector3()
        if self.footprint is None:
            self.footprint = []


@dataclass
class TrackedObject:
    """A tracked object in the perception system."""
    object_id: ObjectId
    existence_probability: float
    classification: List[ObjectClassification]
    kinematics: TrackedObjectKinematics
    shape: Shape


@dataclass
class Header:
    """Standard ROS header."""
    seq: int
    stamp_sec: int
    stamp_nanosec: int
    frame_id: str


@dataclass
class TrackedObjects:
    """Array of tracked objects with header."""
    header: Header
    objects: List[TrackedObject]