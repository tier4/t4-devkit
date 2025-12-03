from __future__ import annotations

import struct
from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeVar

import numpy as np
from attrs import define, field

from t4_devkit.common.io import load_json

if TYPE_CHECKING:
    from typing_extensions import Self

    from t4_devkit.typing import NDArrayFloat, NDArrayU8

__all__ = [
    "PointCloud",
    "LidarPointCloud",
    "RadarPointCloud",
    "SegmentationPointCloud",
    "PointCloudLike",
    "PointCloudMetainfo",
    "PointcloudSourceInfo",
    "Stamp",
]


@define
class Stamp:
    """A dataclass to represent timestamp.

    Attributes:
        sec (int): Seconds.
        nanosec (int): Nanoseconds.
    """

    sec: int
    nanosec: int


@define
class PointcloudSourceInfo:
    """A dataclass to represent pointcloud source information.

    Attributes:
        sensor_token (str): source sensor identifier. References token field from Sensor table.
        idx_begin (int): Begin index of points for the source in the concatenated pointcloud structure.
        length (int): Length of points for the source in the concatenated pointcloud structure.
        stamp (Stamp): Timestamp.
    """

    sensor_token: str
    idx_begin: int
    length: int
    stamp: Stamp = field(converter=lambda x: Stamp(**x) if isinstance(x, dict) else x)


@define
class PointCloudMetainfo:
    """A dataclass to represent pointcloud metadata.

    Attributes:
        stamp (Stamp): Timestamp.
        sources (list[PointcloudSourceInfo]): List of source information.
    """

    stamp: Stamp = field(converter=lambda x: Stamp(**x) if isinstance(x, dict) else x)
    sources: list[PointcloudSourceInfo] = field(factory=list)

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        """Create an instance from a JSON file.

        Args:
            filepath (str): Path to the JSON file containing metadata.

        Returns:
            Self: PointCloudMetainfo instance.
        """
        data = load_json(filepath)
        stamp = Stamp(**data["stamp"])
        sources = []
        for source_data in data.get("sources", []):
            sources.append(PointcloudSourceInfo(**source_data))
        return cls(stamp=stamp, sources=sources)

    @property
    def source_tokens(self) -> list[str]:
        """Get the list of source sensor tokens.

        Returns:
            list[str]: List of sensor tokens.
        """
        return [source.sensor_token for source in self.sources]


@define
class PointCloud:
    """Abstract base dataclass for pointcloud data."""

    points: NDArrayFloat = field(converter=np.array)
    metainfo: PointCloudMetainfo | None = field(default=None)

    @points.validator
    def _check_dims(self, attribute, value) -> None:
        if value.shape[0] != self.num_dims():
            raise ValueError(
                f"Expected point dimension is {self.num_dims()}, but got {value.shape[0]}"
            )

    @metainfo.validator
    def _validate_metainfo(self, attribute, value) -> None:
        """Validate that sources in metainfo form non-overlapping parts covering all points.

        This validator ensures backward compatibility by allowing None metainfo.
        """
        if value is None:
            # Backward compatibility: metainfo is optional
            return

        if not value.sources:
            # No sources to validate
            return

        num_points = self.num_points()

        # Collect all intervals defined by sources
        intervals = []
        for source_info in value.sources:
            source_token = source_info.sensor_token
            idx_begin = source_info.idx_begin
            length = source_info.length
            idx_end = idx_begin + length

            # Check bounds
            if idx_begin < 0:
                raise ValueError(f"Source '{source_token}' has negative idx_begin: {idx_begin}")
            if length < 0:
                raise ValueError(f"Source '{source_token}' has negative length: {length}")
            if idx_end > num_points:
                raise ValueError(
                    f"Source '{source_token}' exceeds point cloud size: "
                    f"idx_begin={idx_begin}, length={length}, but num_points={num_points}"
                )

            intervals.append((idx_begin, idx_end, source_token))

        # Sort intervals by start index
        intervals.sort(key=lambda x: x[0])

        # Check for non-overlapping and complete coverage
        expected_start = 0
        for idx_begin, idx_end, source_token in intervals:
            if idx_begin != expected_start:
                if idx_begin > expected_start:
                    raise ValueError(
                        f"Gap detected: points [{expected_start}:{idx_begin}) are not covered by any source"
                    )
                else:
                    raise ValueError(
                        f"Overlap detected: source '{source_token}' starts at {idx_begin}, "
                        f"but previous source ends at {expected_start}"
                    )
            expected_start = idx_end

        # Check if all points are covered
        if expected_start != num_points:
            raise ValueError(
                f"Incomplete coverage: sources cover up to index {expected_start}, "
                f"but num_points={num_points}"
            )

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


@define
class LidarPointCloud(PointCloud):
    """A dataclass to represent lidar pointcloud.

    Attributes:
        points (NDArrayFloat): Points matrix in the shape of (4, N).
    """

    @staticmethod
    def num_dims() -> int:
        return 4

    @classmethod
    def from_file(cls, filepath: str, metainfo_filepath: str | None = None) -> Self:
        assert filepath.endswith(".bin"), f"Unexpected filetype: {filepath}"

        scan = np.fromfile(filepath, dtype=np.float32)
        points = scan.reshape((-1, 5))[:, : cls.num_dims()]

        metainfo = (
            PointCloudMetainfo.from_file(metainfo_filepath)
            if metainfo_filepath is not None
            else None
        )

        return cls(points.T, metainfo=metainfo)


@define
class RadarPointCloud(PointCloud):
    """A dataclass to represent radar pointcloud.

    Attributes:
        points (NDArrayFloat): Points matrix in the shape of (18, N).
    """

    # class variables
    invalid_states: ClassVar[list[int]] = [0]
    dynprop_states: ClassVar[list[int]] = list(range(7))
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
        metainfo_filepath: str | None = None,
    ) -> Self:
        assert filepath.endswith(".pcd"), f"Unexpected filetype: {filepath}"

        metadata: list[str] = []
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
            metainfo = (
                PointCloudMetainfo.from_file(metainfo_filepath)
                if metainfo_filepath is not None
                else None
            )
            return cls(np.zeros((feature_count, 0)), metainfo=metainfo)

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

        metainfo = (
            PointCloudMetainfo.from_file(metainfo_filepath)
            if metainfo_filepath is not None
            else None
        )
        return cls(points, metainfo=metainfo)


@define
class SegmentationPointCloud(PointCloud):
    """A dataclass to represent segmentation pointcloud.

    Attributes:
        points (NDArrayFloat): Points matrix in the shape of (4, N).
        labels (NDArrayU8): Label matrix.
    """

    labels: NDArrayU8 = field(converter=lambda x: np.array(x, dtype=np.uint8), kw_only=True)

    @staticmethod
    def num_dims() -> int:
        return 4

    @classmethod
    def from_file(
        cls, point_filepath: str, label_filepath: str, metainfo_filepath: str | None = None
    ) -> Self:
        scan = np.fromfile(point_filepath, dtype=np.float32)
        points = scan.reshape((-1, 5))[:, : cls.num_dims()]
        labels = np.fromfile(label_filepath, dtype=np.uint8)
        metainfo = (
            PointCloudMetainfo.from_file(metainfo_filepath)
            if metainfo_filepath is not None
            else None
        )
        return cls(points.T, labels=labels, metainfo=metainfo)


PointCloudLike = TypeVar("PointCloudLike", bound=PointCloud)
