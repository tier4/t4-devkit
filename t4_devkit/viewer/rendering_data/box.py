from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rerun as rr

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D
    from t4_devkit.typing import RoiType, SizeType, TranslationType, VelocityType

__all__ = ["BoxData3D", "BoxData2D"]


class BoxData3D:
    """A class to store 3D boxes data for rendering."""

    def __init__(self) -> None:
        self._centers: list[TranslationType] = []
        self._rotations: list[rr.Quaternion] = []
        self._sizes: list[SizeType] = []
        self._class_ids: list[int] = []
        self._uuids: list[int] = []
        self._velocities: list[VelocityType] = []

    def append(self, box: Box3D) -> None:
        """Append a 3D box data.

        Args:
            box (Box3D): `Box3D` object.
        """
        self._centers.append(box.position)

        rotation_xyzw = np.roll(box.rotation.q, shift=-1)
        self._rotations.append(rr.Quaternion(xyzw=rotation_xyzw))

        width, length, height = box.size
        self._sizes.append((length, width, height))

        self._class_ids.append(box.semantic_label.label.value)

        if box.uuid is not None:
            self._uuids.append(box.uuid[:6])

        if box.velocity is not None:
            self._velocities.append(box.velocity)

    def as_boxes3d(self) -> rr.Boxes3D:
        """Return 3D boxes data as a `rr.Boxes3D`.

        Returns:
            `rr.Boxes3D` object.
        """
        labels = None if len(self._uuids) == 0 else self._uuids
        return rr.Boxes3D(
            sizes=self._sizes,
            centers=self._centers,
            rotations=self._rotations,
            labels=labels,
            class_ids=self._class_ids,
        )

    def as_arrows3d(self) -> rr.Arrows3D:
        """Return velocities data as a `rr.Arrows3D`.

        Returns:
            `rr.Arrows3D` object.
        """
        return rr.Arrows3D(
            vectors=self._velocities,
            origins=self._centers,
            class_ids=self._class_ids,
        )


class BoxData2D:
    """A class to store 2D boxes data for rendering."""

    def __init__(self) -> None:
        self._rois: list[RoiType] = []
        self._uuids: list[str] = []
        self._class_ids: list[int] = []

    def append(self, box: Box2D) -> None:
        """Append a 2D box data.

        Args:
            box (Box2D): `Box2D` object.
        """
        self._rois.append(box.roi.roi)

        self._class_ids.append(box.semantic_label.label.value)

        if box.uuid is not None:
            self._uuids.append(box.uuid)

    def as_boxes2d(self) -> rr.Boxes2D:
        """Return 2D boxes data as a `rr.Boxes2D`.

        Returns:
            `rr.Boxes2D` object.
        """
        labels = None if len(self._uuids) == 0 else self._uuids
        return rr.Boxes2D(
            array=self._rois,
            array_format=rr.Box2DFormat.XYXY,
            labels=labels,
            class_ids=self._class_ids,
        )
