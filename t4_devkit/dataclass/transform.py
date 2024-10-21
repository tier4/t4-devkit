from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, overload

import numpy as np
from pyquaternion import Quaternion
from typing_extensions import Self

from t4_devkit.typing import NDArray, RotationType

if TYPE_CHECKING:
    from t4_devkit.typing import ArrayLike

__all__ = ["TransformBuffer", "HomogeneousMatrix", "TransformLike"]


@dataclass
class TransformBuffer:
    buffer: dict[tuple[str, str], HomogeneousMatrix] = field(default_factory=dict, init=False)

    def set_transform(self, matrix: HomogeneousMatrix) -> None:
        """Set transform matrix to the buffer.
        Also, if its inverse transformation has not been registered, registers it too.

        Args:
            matrix (HomogeneousMatrix): Transformation matrix.
        """
        src = matrix.src
        dst = matrix.dst
        if (src, dst) not in self.buffer:
            self.buffer[(src, dst)] = matrix

        if (dst, src) not in self.buffer:
            self.buffer[(dst, src)] = matrix.inv()

    def lookup_transform(self, src: str, dst: str) -> HomogeneousMatrix | None:
        if src == dst:
            return HomogeneousMatrix(np.zeros(3), Quaternion(), src=src, dst=dst)
        return self.buffer[(src, dst)] if (src, dst) in self.buffer else None

    def do_transform(self, src: str, dst: str, *args: TransformLike) -> TransformLike | None:
        return self.buffer[(src, dst)].transform(args) if (src, dst) in self.buffer else None


@dataclass
class HomogeneousMatrix:
    def __init__(
        self,
        position: ArrayLike,
        rotation: ArrayLike | RotationType,
        src: str,
        dst: str,
    ) -> None:
        """Construct a new object.

        Args:
            position (ArrayLike): 3D position.
            rotation (ArrayLike | RotationType): 3x3 rotation matrix or quaternion.
            src (str): Source frame ID.
            dst (str): Destination frame ID.
        """
        self.position = position if isinstance(position, np.ndarray) else np.array(position)

        if isinstance(rotation, np.ndarray) and rotation.ndim == 2:
            rotation = Quaternion(matrix=rotation)
        elif not isinstance(rotation, Quaternion):
            rotation = Quaternion(rotation)
        self.rotation = rotation

        self.src = src
        self.dst = dst

        self.matrix = _generate_homogeneous_matrix(position, rotation)

    @classmethod
    def from_matrix(
        cls,
        matrix: NDArray | HomogeneousMatrix,
        src: str,
        dst: str,
    ) -> Self:
        """Construct a new object from a homogeneous matrix.

        Args:
            matrix (NDArray | HomogeneousMatrix): 4x4 homogeneous matrix.
            src (str): Source frame ID.
            dst (str): Destination frame ID.

        Returns:
            Self: Constructed instance.
        """
        position, rotation = _extract_position_and_rotation_from_matrix(matrix)
        return cls(position, rotation, src, dst)

    @property
    def shape(self) -> tuple[int, ...]:
        """Return a shape of the homogeneous matrix.

        Returns:
            Return the shape of (4, 4).
        """
        return self.matrix.shape

    @property
    def yaw_pitch_roll(self) -> tuple[float, float, float]:
        """Return yaw, pitch and roll.

        NOTE:
            yaw: Rotation angle around the z-axis in [rad], in the range `[-pi, pi]`.
            pitch: Rotation angle around the y'-axis in [rad], in the range `[-pi/2, pi/2]`.
            roll: Rotation angle around the x"-axis in [rad], in the range `[-pi, pi]`.

        Returns:
            Yaw, pitch and roll in [rad].
        """
        return self.rotation.yaw_pitch_roll

    @property
    def rotation_matrix(self) -> NDArray:
        """Return a 3x3 rotation matrix.

        Returns:
            3x3 rotation matrix.
        """
        return self.rotation.rotation_matrix

    def dot(self, other: HomogeneousMatrix) -> HomogeneousMatrix:
        """Return a dot product of myself and another.

        Args:
            other (HomogeneousMatrix): `HomogeneousMatrix` object.

        Raises:
            ValueError: `self.src` and `other.dst` must be the same frame ID.

        Returns:
            Result of a dot product.
        """
        if self.src != other.dst:
            raise ValueError(f"self.src != other.dst: self.src={self.src}, other.dst={other.dst}")

        ret_mat = self.matrix.dot(other.matrix)
        position, rotation = _extract_position_and_rotation_from_matrix(ret_mat)
        return HomogeneousMatrix(position, rotation, src=other.src, dst=self.dst)

    def inv(self) -> HomogeneousMatrix:
        """Return a inverse matrix of myself.

        Returns:
            Inverse matrix.
        """
        ret_mat = np.linalg.inv(self.matrix)
        position, rotation = _extract_position_and_rotation_from_matrix(ret_mat)
        return HomogeneousMatrix(position, rotation, src=self.src, dst=self.dst)

    @overload
    def transform(self, position: ArrayLike) -> NDArray:
        """Transform a position by myself.

        Args:
            position (ArrayLike): 3D position.

        Returns:
            Transformed position.
        """
        pass

    @overload
    def transform(
        self,
        position: ArrayLike,
        rotation: RotationType,
    ) -> tuple[NDArray, Quaternion]:
        """Transform position and rotation by myself.

        Args:
            position (ArrayLike): 3D position.
            rotation (RotationType): 3x3 rotation matrix or quaternion.

        Returns:
            Transformed position and quaternion.
        """
        pass

    @overload
    def transform(self, matrix: HomogeneousMatrix) -> HomogeneousMatrix:
        """Transform a homogeneous matrix by myself.

        Args:
            matrix (HomogeneousMatrix): `HomogeneousMatrix` object.

        Returns:
            Transformed `HomogeneousMatrix` object.
        """
        pass

    def transform(self, *args, **kwargs):
        # TODO(ktro2828): Refactoring this operations.
        s = len(args)
        if s == 0:
            if not kwargs:
                raise ValueError("At least 1 argument specified")

            if "position" in kwargs:
                position = kwargs["position"]
                if "matrix" in kwargs:
                    raise ValueError("Cannot specify `position` and `matrix` at the same time.")
                elif "rotation" in kwargs:
                    rotation = kwargs["rotation"]
                    return self.__transform_position_and_rotation(position, rotation)
                else:
                    return self.__transform_position(position)
            elif "matrix" in kwargs:
                matrix = kwargs["matrix"]
                return self.__transform_matrix(matrix)
            else:
                raise KeyError(f"Unexpected keys are detected: {list(kwargs.keys())}")
        elif s == 1:
            arg = args[0]
            if isinstance(arg, HomogeneousMatrix):
                return self.__transform_matrix(matrix=arg)
            else:
                return self.__transform_position(position=arg)
        elif s == 2:
            position, rotation = args
            return self.__transform_position_and_rotation(position, rotation)
        else:
            raise ValueError(f"Unexpected number of arguments {s}")

    def __transform_position(self, position: ArrayLike) -> NDArray:
        rotation = Quaternion()
        matrix = _generate_homogeneous_matrix(position, rotation)
        ret_mat = self.matrix.dot(matrix)
        ret_pos, _ = _extract_position_and_rotation_from_matrix(ret_mat)
        return ret_pos

    def __transform_position_and_rotation(
        self,
        position: ArrayLike,
        rotation: RotationType,
    ) -> tuple[NDArray, Quaternion]:
        matrix = _generate_homogeneous_matrix(position, rotation)
        ret_mat = self.matrix.dot(matrix)
        return _extract_position_and_rotation_from_matrix(ret_mat)

    def __transform_matrix(self, matrix: HomogeneousMatrix) -> HomogeneousMatrix:
        return matrix.dot(self)


TransformLike = NDArray | tuple[NDArray, RotationType] | HomogeneousMatrix


def _extract_position_and_rotation_from_matrix(
    matrix: NDArray | HomogeneousMatrix,
) -> tuple[NDArray, Quaternion]:
    """Extract position and rotation from a homogeneous matrix.

    Args:
        matrix (NDArray | HomogeneousMatrix): 4x4 matrix or `HomogeneousMatrix` object.

    Raises:
        ValueError: Matrix shape must be 4x4.

    Returns:
        3D position and quaternion.
    """
    if isinstance(matrix, np.ndarray):
        if matrix.shape != (4, 4):
            raise ValueError(f"Homogeneous matrix must be 4x4, but got {matrix.shape}")

        position = matrix[:3, 3]
        rotation = matrix[:3, :3]
        return position, Quaternion(matrix=rotation)
    else:
        return matrix.position, matrix.rotation


def _generate_homogeneous_matrix(
    position: ArrayLike,
    rotation: ArrayLike | RotationType,
) -> NDArray:
    """Generate a 4x4 homogeneous matrix from position and rotation.

    Args:
        position (ArrayLike): 3D position.
        rotation (ArrayLike | RotationType): 3x3 rotation matrix or quaternion.

    Returns:
        A 4x4 homogeneous matrix.
    """
    if not isinstance(position, np.ndarray):
        position = np.array(position)

    if not isinstance(rotation, Quaternion):
        if isinstance(rotation, np.ndarray) and rotation.ndim == 2:
            rotation = Quaternion(matrix=rotation)
        else:
            rotation = Quaternion(rotation)

    matrix = np.eye(4)
    matrix[:3, 3] = position
    matrix[:3, :3] = rotation.rotation_matrix
    return matrix
    return matrix
