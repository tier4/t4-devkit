from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from typing_extensions import Self

    from t4_devkit.typing import NDArrayFloat


@dataclass
class PointCloud:
    points: NDArrayFloat

    def __post_init__(self) -> None:
        assert self.points.shape[1] == self.num_dims()

    @staticmethod
    @abstractmethod
    def num_dims() -> int:
        pass

    @classmethod
    @abstractmethod
    def from_file(cls, filepath: str) -> Self:
        pass

    def num_pts(self) -> int:
        return self.points.shape[0]


@dataclass
class LidarPointCloud(PointCloud):
    @staticmethod
    def num_dims() -> int:
        return 4

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        assert filepath.endswith(".bin"), f"Unexpected filetype: {filepath}"

        scan = np.fromfile(filepath, dtype=np.float32)
        points = scan.reshape((-1, 5))[:, : cls.num_dims()]
        return cls(points)
