from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, overload

import numpy as np
from attrs import define, field, validators
from pyquaternion import Quaternion
from typing_extensions import Self

from t4_devkit.common.converter import to_quaternion
from t4_devkit.common.validator import is_vector3
from t4_devkit.typing import NDArray, QuaternionLike

if TYPE_CHECKING:
    from t4_devkit.typing import ArrayLike, Vector3Like

__all__ = [
    "TransformBuffer",
    "HomogeneousMatrix",
    "TranslateItemLike",
    "RotateItemLike",
    "TransformItemLike",
]


@define
class TransformBuffer:
    """A buffer class to store transformation matrices.

    Attributes:
        buffer (dict[tuple[str, str], HomogeneousMatrix]): Matrix buffer whose key is `(src, dst)`.
    """

    buffer: dict[tuple[str, str], HomogeneousMatrix] = field(factory=dict, init=False)

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
        """Look up the transform matrix corresponding to the `src` and `dst` frame ID.

        Args:
            src (str): Source frame ID.
            dst (str): Destination frame ID.

        Returns:
            Returns `HomogeneousMatrix` if the corresponding matrix can be found,
                otherwise it returns `None`.
        """
        if src == dst:
            return HomogeneousMatrix.as_identity(src)
        return self.buffer[(src, dst)] if (src, dst) in self.buffer else None

    def do_translate(self, src: str, dst: str, *args, **kwargs) -> TranslateItemLike | None:
        """Translate specified items with the matrix corresponding to `src` and `dst` frame ID.

        Args:
            src (str): Source frame ID.
            dst (str): Destination frame ID.

        Returns:
            TranslateItemLike | None: Returns translated items if the corresponding matrix can be found,
                otherwise it returns `None`.
        """
        tf_matrix = self.lookup_transform(src, dst)
        return tf_matrix.translate(*args, **kwargs) if tf_matrix is not None else None

    def do_rotate(self, src: str, dst: str, *args, **kwargs) -> RotateItemLike | None:
        """Rotate specified items with the matrix corresponding to `src` and `dst` frame ID.

        Args:
            src (str): Source frame ID.
            dst (str): Destination frame ID.

        Returns:
            TranslateItemLike | None: Returns rotated items if the corresponding matrix can be found,
                otherwise it returns `None`.
        """
        tf_matrix = self.lookup_transform(src, dst)
        return tf_matrix.rotate(*args, **kwargs) if tf_matrix is not None else None

    def do_transform(self, src: str, dst: str, *args, **kwargs) -> TransformItemLike | None:
        """Transform specified items with the matrix corresponding to `src` and `dst` frame ID.

        Args:
            src (str): Source frame ID.
            dst (str): Destination frame ID.

        Returns:
            TranslateItemLike | None: Returns transformed items if the corresponding matrix can be found,
                otherwise it returns `None`.
        """
        tf_matrix = self.lookup_transform(src, dst)
        return tf_matrix.transform(*args, **kwargs) if tf_matrix is not None else None


@define
class HomogeneousMatrix:
    position: Vector3Like = field(converter=np.array, validator=is_vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    src: str = field(validator=validators.instance_of(str))
    dst: str = field(validator=validators.instance_of(str))
    matrix: NDArray = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.matrix = _generate_homogeneous_matrix(self.position, self.rotation)

    @classmethod
    def as_identity(cls, frame_id: str) -> Self:
        """Construct a new object with identity.

        Args:
            frame_id (str): Frame ID.

        Returns:
            Constructed self instance.
        """
        return cls(np.zeros(3), Quaternion(), frame_id, frame_id)

    @classmethod
    def from_matrix(
        cls,
        matrix: NDArray | HomogeneousMatrix,
        src: str | None = None,
        dst: str | None = None,
    ) -> Self:
        """Construct a new object from a homogeneous matrix.

        Args:
            matrix (NDArray | HomogeneousMatrix): 4x4 homogeneous matrix.
            src (str | None, optional): Source frame ID.
                This must be specified only if the input matrix is `NDArray`.
            dst (str | None, optional): Destination frame ID.
                This must be specified only if the input matrix is `NDArray`.

        Returns:
            Constructed self instance.
        """
        position, rotation = _extract_position_and_rotation_from_matrix(matrix)
        if isinstance(matrix, np.ndarray):
            assert matrix.shape == (4, 4)
            assert src is not None and dst is not None
            return cls(position, rotation, src, dst)
        else:
            return cls(position, rotation, matrix.src, matrix.dst)

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
    def translate(self, position: ArrayLike) -> NDArray:
        """Translate a position by myself.

        Args:
            position (ArrayLike): 3D position.

        Returns:
            Translated position.
        """
        pass

    @overload
    def translate(self, matrix: HomogeneousMatrix) -> HomogeneousMatrix:
        """Translate a homogeneous matrix by myself.

        Args:
            matrix (HomogeneousMatrix):

        Returns:
            Translated `HomogeneousMatrix` object.
        """
        pass

    def translate(self, *args, **kwargs) -> TranslateItemLike:
        inputs = _format_transform_args(*args, **kwargs)
        if {"position"} == set(inputs.keys()):
            return self.position + inputs["position"]
        elif {"matrix"} == set(inputs.keys()):
            matrix: HomogeneousMatrix = deepcopy(inputs["matrix"])
            matrix.position = self.position + matrix.position
            return matrix
        else:
            raise ValueError(f"Unexpected arguments: {list(inputs.keys())}")

    @overload
    def rotate(self, position: ArrayLike) -> NDArray:
        """Rotate a position by myself.

        Args:
            position (ArrayLike): 3D position.

        Returns:
            Rotated position.
        """
        pass

    @overload
    def rotate(self, rotation: QuaternionLike) -> QuaternionLike:
        """Rotate a 3x3 rotation matrix or quaternion by myself.

        Args:
            rotation (QuaternionLike): 3x3 rotation matrix or quaternion.

        Returns:
            Rotated quaternion.
        """
        pass

    @overload
    def rotate(self, matrix: HomogeneousMatrix) -> HomogeneousMatrix:
        """Rotate a homogeneous matrix by myself.

        Args:
            matrix (HomogeneousMatrix): `HomogeneousMatrix` object.

        Returns:
            Rotated `HomogeneousMatrix` object.
        """
        pass

    def rotate(self, *args, **kwargs) -> RotateItemLike:
        inputs = _format_transform_args(*args, **kwargs)
        if {"position"} == set(inputs.keys()):
            return np.matmul(self.rotation_matrix, inputs["position"])
        elif {"rotation"} == set(inputs.keys()):
            rotation_matrix: NDArray = inputs["rotation"].rotation_matrix
            return np.matmul(self.rotation_matrix, rotation_matrix)
        elif {"matrix"} == set(inputs.keys()):
            matrix: HomogeneousMatrix = deepcopy(inputs["matrix"])
            matrix.rotation = Quaternion(
                matrix=np.matmul(self.rotation_matrix, matrix.rotation_matrix)
            )
            return matrix
        else:
            raise ValueError(f"Unexpected arguments: {list(inputs.keys())}")

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
    def transform(self, rotation: QuaternionLike) -> QuaternionLike:
        """Transform a rotation by myself.

        Args:
            rotation (QuaternionLike): 3x3 rotation matrix or quaternion.

        Returns:
            Transformed quaternion.
        """
        pass

    @overload
    def transform(
        self,
        position: ArrayLike,
        rotation: QuaternionLike,
    ) -> tuple[NDArray, Quaternion]:
        """Transform position and rotation by myself.

        Args:
            position (ArrayLike): 3D position.
            rotation (QuaternionLike): 3x3 rotation matrix or quaternion.

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

    def transform(self, *args, **kwargs) -> TransformItemLike:
        inputs = _format_transform_args(*args, **kwargs)
        if {"position", "rotation"} == set(inputs.keys()):
            return self.__transform_position_and_rotation(**inputs)
        elif {"position"} == set(inputs.keys()):
            return self.__transform_position(**inputs)
        elif {"rotation"} == set(inputs.keys()):
            return self.__transform_rotation(**inputs)
        elif {"matrix"} == set(inputs.keys()):
            return self.__transform_matrix(**inputs)
        else:
            raise ValueError(f"Unexpected inputs: {list(inputs.keys())}")

    def __transform_position(self, position: ArrayLike) -> NDArray:
        rotation = Quaternion()
        matrix = _generate_homogeneous_matrix(position, rotation)
        ret_mat = self.matrix.dot(matrix)
        ret_pos, _ = _extract_position_and_rotation_from_matrix(ret_mat)
        return ret_pos

    def __transform_rotation(self, rotation: QuaternionLike) -> QuaternionLike:
        position = np.zeros(3)
        matrix = _generate_homogeneous_matrix(position, rotation)
        ret_mat = self.matrix.dot(matrix)
        _, ret_rot = _extract_position_and_rotation_from_matrix(ret_mat)
        return ret_rot

    def __transform_position_and_rotation(
        self,
        position: ArrayLike,
        rotation: QuaternionLike,
    ) -> tuple[NDArray, Quaternion]:
        matrix = _generate_homogeneous_matrix(position, rotation)
        ret_mat = self.matrix.dot(matrix)
        return _extract_position_and_rotation_from_matrix(ret_mat)

    def __transform_matrix(self, matrix: HomogeneousMatrix) -> HomogeneousMatrix:
        return matrix.dot(self)


TranslateItemLike = NDArray | HomogeneousMatrix
RotateItemLike = NDArray | QuaternionLike | HomogeneousMatrix
TransformItemLike = NDArray | QuaternionLike | tuple[NDArray, QuaternionLike] | HomogeneousMatrix


def _format_transform_args(*args, **kwargs) -> dict[str, Any]:
    num_args = len(args)
    num_kwargs = len(kwargs)
    if num_args == 0 and num_kwargs == 0:
        raise ValueError("At least 1 argument specified.")

    # >>> (position), (rotation), (position, rotation), (matrix)
    if num_args == 0:
        if "position" in kwargs:
            if "matrix" in kwargs:
                raise KeyError("Cannot specify `position` and `matrix` at the same time.")
            elif "rotation" in kwargs:
                return {"position": kwargs["position"], "rotation": kwargs["rotation"]}
            else:
                return {"position": kwargs["position"]}
        elif "rotation" in kwargs:
            if "matrix" in kwargs:
                raise KeyError("Cannot specify `rotation` and `matrix` at the same time.")
            return {"rotation": kwargs["rotation"]}
        elif "matrix" in kwargs:
            return {"matrix": kwargs["matrix"]}
        else:
            raise KeyError(f"Unexpected keys are detected: {list(kwargs.keys())}.")
    # >>> (position), (rotation), (position, rotation), (matrix)
    elif num_args == 1:
        arg0 = args[0]
        if num_kwargs == 0:
            if isinstance(arg0, HomogeneousMatrix):
                return {"matrix": arg0}
            elif isinstance(arg0, Quaternion):
                return {"rotation": arg0}
            else:
                arg0 = np.asarray(arg0)
                if arg0.ndim == 1:
                    if len(arg0) == 3:
                        return {"position": arg0}
                    elif len(arg0) == 4:
                        return {"rotation": arg0}
                    else:
                        raise ValueError(f"Unexpected argument shape: {arg0.shape}.")
                else:
                    if not arg0.shape != (3, 3):
                        raise ValueError(f"Unexpected argument shape: {arg0.shape}.")
                    return {"rotation": arg0}
        elif num_kwargs == 1:
            if "rotation" not in kwargs:
                raise KeyError("Expected two arguments: position and rotation.")
            return {"position": arg0, "rotation": kwargs["rotation"]}
        else:
            raise ValueError(f"Too much arguments {num_args + num_kwargs}.")
    # >>> (position, rotation)
    elif num_args == 2:
        return {"position": args[0], "rotation": args[1]}
    else:
        raise ValueError(f"Too much arguments {num_args + num_kwargs}.")


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
    rotation: ArrayLike | QuaternionLike,
) -> NDArray:
    """Generate a 4x4 homogeneous matrix from position and rotation.

    Args:
        position (ArrayLike): 3D position.
        rotation (ArrayLike | QuaternionLike): 3x3 rotation matrix or quaternion.

    Returns:
        A 4x4 homogeneous matrix.
    """
    position = np.asarray(position)
    rotation = to_quaternion(rotation)

    matrix = np.eye(4)
    matrix[:3, 3] = position
    matrix[:3, :3] = rotation.rotation_matrix
    return matrix
