from __future__ import annotations

from typing import TYPE_CHECKING, overload

import numpy as np
import rerun as rr

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D
    from t4_devkit.typing import RoiType, RotationType, SizeType, TranslationType, VelocityType

__all__ = ["BoxData3D", "BoxData2D"]


class BoxData3D:
    """A class to store 3D boxes data for rendering."""

    def __init__(self, label2id: dict[str, int] | None = None) -> None:
        """Construct a new object.

        Args:
            label2id (dict[str, int] | None, optional): Key-value mapping which maps label name to its class ID.
        """
        self._centers: list[TranslationType] = []
        self._rotations: list[rr.Quaternion] = []
        self._sizes: list[SizeType] = []
        self._class_ids: list[int] = []
        self._uuids: list[int] = []
        self._velocities: list[VelocityType] = []

        self._label2id: dict[str, int] = {} if label2id is None else label2id

    @overload
    def append(self, box: Box3D) -> None:
        """Append a 3D box data with a Box3D object.

        Args:
            box (Box3D): `Box3D` object.
        """
        pass

    @overload
    def append(
        self,
        center: TranslationType,
        rotation: RotationType,
        size: SizeType,
        class_id: int,
        uuid: str | None = None,
        velocity: VelocityType | None = None,
    ) -> None:
        """Append a 3D box data with its elements.

        Args:
            center (TranslationType): 3D position in the order of (x, y, z).
            rotation (RotationType): Quaternion.
            size (SizeType): Box size in the order of (width, height, length).
            class_id (int): Class ID.
            velocity (VelocityType | None, optional): Box velocity. Defaults to None.
            uuid (str | None, optional): Unique identifier.
        """
        pass

    def append(self, *args, **kwargs) -> None:
        if len(args) + len(kwargs) == 1:
            self._append_with_box(*args, **kwargs)
        else:
            self._append_with_elements(*args, **kwargs)

    def _append_with_box(self, box: Box3D) -> None:
        self._centers.append(box.position)

        rotation_xyzw = np.roll(box.rotation.q, shift=-1)
        self._rotations.append(rr.Quaternion(xyzw=rotation_xyzw))

        width, length, height = box.size
        self._sizes.append((length, width, height))

        if box.semantic_label.name not in self._label2id:
            self._label2id[box.semantic_label.name] = len(self._label2id)

        self._class_ids.append(self._label2id[box.semantic_label.name])

        if box.velocity is not None:
            self._velocities.append(box.velocity)

        if box.uuid is not None:
            self._uuids.append(box.uuid[:6])

    def _append_with_elements(
        self,
        center: TranslationType,
        rotation: RotationType,
        size: SizeType,
        class_id: int,
        velocity: VelocityType | None = None,
        uuid: str | None = None,
    ) -> None:
        self._centers.append(center)

        rotation_xyzw = np.roll(rotation.q, shift=-1)
        self._rotations.append(rr.Quaternion(xyzw=rotation_xyzw))

        width, length, height = size
        self._sizes.append((length, width, height))

        self._class_ids.append(class_id)

        if velocity is not None:
            self._velocities.append(velocity)

        if uuid is not None:
            self._uuids.append(uuid)

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

    def __init__(self, label2id: dict[str, int] | None = None) -> None:
        """Construct a new object.

        Args:
            label2id (dict[str, int] | None, optional): Key-value mapping which maps label name to its class ID.
        """
        self._rois: list[RoiType] = []
        self._uuids: list[str] = []
        self._class_ids: list[int] = []

        self._label2id: dict[str, int] = {} if label2id is None else label2id

    @overload
    def append(self, box: Box2D) -> None:
        """Append a 2D box data with a `Box2D` object.

        Args:
            box (Box2D): `Box2D` object.
        """
        pass

    @overload
    def append(self, roi: RoiType, class_id: int, uuid: str | None = None) -> None:
        """Append a 2D box data with its elements.

        Args:
            roi (RoiType): ROI in the order of (xmin, ymin, xmax, ymax).
            class_id (int): Class ID.
            uuid (str | None, optional): Unique identifier.
        """
        pass

    def append(self, *args, **kwargs) -> None:
        if len(args) + len(kwargs) == 1:
            self._append_with_box(*args, **kwargs)
        else:
            self._append_with_elements(*args, **kwargs)

    def _append_with_box(self, box: Box2D) -> None:
        self._rois.append(box.roi.roi)

        if box.semantic_label.name not in self._label2id:
            self._label2id[box.semantic_label.name] = len(self._label2id)

        self._class_ids.append(self._label2id[box.semantic_label.name])

        if box.uuid is not None:
            self._uuids.append(box.uuid)

    def _append_with_elements(self, roi: RoiType, class_id: int, uuid: str | None = None) -> None:
        self._rois.append(roi)

        self._class_ids.append(class_id)

        if uuid is not None:
            self._uuids.append(uuid)

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
