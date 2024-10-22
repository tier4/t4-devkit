from __future__ import annotations

import struct
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeVar

import numpy as np

if TYPE_CHECKING:
    from typing_extensions import Self

    from t4_devkit.typing import NDArrayFloat, NDArrayU8

__all__ = [
    "PointCloud",
    "LidarPointCloud",
    "RadarPointCloud",
    "SegmentationPointCloud",
    "PointCloudLike",
]


@dataclass
class PointCloud:
    """Abstract base dataclass for pointcloud data."""

    points: NDArrayFloat

    def __post_init__(self) -> None:
        assert self.points.shape[0] == self.num_dims()

    @staticmethod
    @abstractmethod
    def num_dims() -> int:
        """Return the number of the point dimensions.

        Returns:
            int: The number of the point dimensions.
        """
        pass

    @classmethod
    @abstractmethod
    def from_file(cls, filepath: str) -> Self:
        """Create an object from pointcloud file.

        Args:
            filepath (str): File path of the pointcloud file.

        Returns:
            Self instance.
        """
        pass

    def num_points(self) -> int:
        """Return the number of points.

        Returns:
            int: _description_
        """
        return self.points.shape[1]

    def translate(self, x: NDArrayFloat) -> None:
        for i in range(3):
            self.points[i, :] = self.points[i, :] + x[i]

    def rotate(self, matrix: NDArrayFloat) -> None:
        self.points[:3, :] = np.dot(matrix, self.points[:3, :])

    def transform(self, matrix: NDArrayFloat) -> None:
        self.points[:3, :] = matrix.dot(
            np.vstack((self.points[:3, :], np.ones(self.num_points())))
        )[:3, :]


@dataclass
class LidarPointCloud(PointCloud):
    """A dataclass to represent lidar pointcloud."""

    @staticmethod
    def num_dims() -> int:
        return 4

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        assert filepath.endswith(".bin"), f"Unexpected filetype: {filepath}"

        scan = np.fromfile(filepath, dtype=np.float32)
        points = scan.reshape((-1, 5))[:, : cls.num_dims()]
        return cls(points.T)


@dataclass
class RadarPointCloud(PointCloud):
    # class variables
    invalid_states: ClassVar[list[int]] = [0]
    dynprop_states: ClassVar[list[int]] = range(7)
    ambig_states: ClassVar[list[int]] = [3]

    @staticmethod
    def num_dims() -> int:
        return 18

    @classmethod
    def from_file(
        cls,
        filepath: str,
        invalid_states: list[int] | None = None,
        dynprop_states: list[int] | None = None,
        ambig_states: list[int] | None = None,
    ) -> Self:
        assert filepath.endswith(".pcd"), f"Unexpected filetype: {filepath}"

        metadata = []
        with open(filepath, "rb") as f:
            for line in f:
                line = line.strip().decode("utf-8")
                metadata.append(line)
                if line.startswith("DATA"):
                    break

            data_binary = f.read()

        # Get the header rows and check if they appear as expected.
        assert metadata[0].startswith("#"), "First line must be comment"
        assert metadata[1].startswith("VERSION"), "Second line must be VERSION"
        sizes = metadata[3].split(" ")[1:]
        types = metadata[4].split(" ")[1:]
        counts = metadata[5].split(" ")[1:]
        width = int(metadata[6].split(" ")[1])
        height = int(metadata[7].split(" ")[1])
        data = metadata[10].split(" ")[1]
        feature_count = len(types)
        assert width > 0
        assert len([c for c in counts if c != c]) == 0, "Error: COUNT not supported!"
        assert height == 1, "Error: height != 0 not supported!"
        assert data == "binary"

        # Lookup table for how to decode the binaries.
        unpacking_lut = {
            "F": {2: "e", 4: "f", 8: "d"},
            "I": {1: "b", 2: "h", 4: "i", 8: "q"},
            "U": {1: "B", 2: "H", 4: "I", 8: "Q"},
        }
        types_str = "".join([unpacking_lut[t][int(s)] for t, s in zip(types, sizes)])

        # Decode each point.
        offset = 0
        point_count = width
        points = []
        for i in range(point_count):
            point = []
            for p in range(feature_count):
                start_p = offset
                end_p = start_p + int(sizes[p])
                assert end_p < len(data_binary)
                point_p = struct.unpack(types_str[p], data_binary[start_p:end_p])[0]
                point.append(point_p)
                offset = end_p
            points.append(point)

        # A NaN in the first point indicates an empty pointcloud.
        point = np.array(points[0])
        if np.any(np.isnan(point)):
            return cls(np.zeros((feature_count, 0)))

        # Convert to numpy matrix.
        points = np.array(points).transpose()

        # If no parameters are provided, use default settings.
        invalid_states = cls.invalid_states if invalid_states is None else invalid_states
        dynprop_states = cls.dynprop_states if dynprop_states is None else dynprop_states
        ambig_states = cls.ambig_states if ambig_states is None else ambig_states

        # Filter points with an invalid state.
        valid = [p in invalid_states for p in points[-4, :]]
        points = points[:, valid]

        # Filter by dynProp.
        valid = [p in dynprop_states for p in points[3, :]]
        points = points[:, valid]

        # Filter by ambig_state.
        valid = [p in ambig_states for p in points[11, :]]
        points = points[:, valid]

        return cls(points)


@dataclass
class SegmentationPointCloud(PointCloud):
    labels: NDArrayU8

    @staticmethod
    def num_dims() -> int:
        return 4

    @classmethod
    def from_file(cls, point_filepath: str, label_filepath: str) -> Self:
        scan = np.fromfile(point_filepath, dtype=np.float32)
        points = scan.reshape((-1, 5))[:, : cls.num_dims()]
        labels = np.fromfile(label_filepath, dtype=np.uint8)
        return cls(points.T, labels)


PointCloudLike = TypeVar("PointCloudLike", bound=PointCloud)
