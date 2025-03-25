from __future__ import annotations

from typing import TYPE_CHECKING, overload

import numpy as np
import rerun as rr
import rerun.components as rrc
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, Future
    from t4_devkit.typing import QuaternionLike, RoiLike, Vector3Like

__all__ = ["BoxData3D", "BoxData2D"]


@define
class BoxData3D:
    """A class to store 3D boxes data for rendering.

    Attributes:
        label2id (dict[str, int]): Key-value of map of label name and its ID.
        centers (list[Vector3Like]): List of 3D center positions in the order of (x, y, z).
        rotations (list[rr.Quaternion]): List of quaternions.
        sizes (list[Vector3Like]): List of 3D box dimensions in the order of (width, length, height).
        class_ids (list[int]): List of label class IDs.
        uuids (list[str]): List of unique identifier IDs.
        velocities (list[Velocities]): List of velocities in the order of (vx, vy, vz).
    """

    label2id: dict[str, int] = field(factory=dict)

    centers: list[Vector3Like] = field(init=False, factory=list)
    rotations: list[rr.Quaternion] = field(init=False, factory=list)
    sizes: list[Vector3Like] = field(init=False, factory=list)
    class_ids: list[int] = field(init=False, factory=list)
    uuids: list[str] = field(init=False, factory=list)
    velocities: list[Vector3Like] = field(init=False, factory=list)
    future: list[Future] = field(init=False, factory=list)

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
        center: Vector3Like,
        rotation: QuaternionLike,
        size: Vector3Like,
        class_id: int,
        uuid: str | None = None,
        velocity: Vector3Like | None = None,
        future: Future | None = None,
    ) -> None:
        """Append a 3D box data with its elements.

        Args:
            center (Vector3Like): 3D position in the order of (x, y, z).
            rotation (QuaternionLike): Quaternion.
            size (Vector3Like): Box size in the order of (width, height, length).
            class_id (int): Class ID.
            uuid (str | None, optional): Unique identifier.
            velocity (Vector3Like | None, optional): Box velocity.
            future (Future | None, optional): Future trajectory.
        """
        pass

    def append(self, *args, **kwargs) -> None:
        if len(args) + len(kwargs) == 1:
            self._append_with_box(*args, **kwargs)
        else:
            self._append_with_elements(*args, **kwargs)

    def _append_with_box(self, box: Box3D) -> None:
        self.centers.append(box.position)

        rotation_xyzw = np.roll(box.rotation.q, shift=-1)
        self.rotations.append(rr.Quaternion(xyzw=rotation_xyzw))

        width, length, height = box.size
        self.sizes.append((length, width, height))

        if box.semantic_label.name not in self.label2id:
            self.label2id[box.semantic_label.name] = len(self.label2id)

        self.class_ids.append(self.label2id[box.semantic_label.name])

        if box.velocity is not None:
            self.velocities.append(box.velocity)

        if box.uuid is not None:
            self.uuids.append(box.uuid)

        if box.future is not None:
            self.future.append(box.future)

    def _append_with_elements(
        self,
        center: Vector3Like,
        rotation: QuaternionLike,
        size: Vector3Like,
        class_id: int,
        velocity: Vector3Like | None = None,
        uuid: str | None = None,
        future: Future | None = None,
    ) -> None:
        self.centers.append(center)

        rotation_xyzw = np.roll(rotation.q, shift=-1)
        self.rotations.append(rr.Quaternion(xyzw=rotation_xyzw))

        width, length, height = size
        self.sizes.append((length, width, height))

        self.class_ids.append(class_id)

        if velocity is not None:
            self.velocities.append(velocity)

        if uuid is not None:
            self.uuids.append(uuid)

        if future is not None:
            self.future.append(future)

    def as_boxes3d(self) -> rr.Boxes3D:
        """Return 3D boxes data as a `rr.Boxes3D`.

        Returns:
            `rr.Boxes3D` object.
        """
        labels = None if len(self.uuids) == 0 else self.uuids
        return rr.Boxes3D(
            sizes=self.sizes,
            centers=self.centers,
            rotations=self.rotations,
            fill_mode=rrc.FillMode.Solid,
            labels=labels,
            class_ids=self.class_ids,
            show_labels=False,
        )

    def as_arrows3d(self) -> rr.Arrows3D:
        """Return velocities data as a `rr.Arrows3D`.

        Returns:
            `rr.Arrows3D` object.
        """
        return rr.Arrows3D(
            vectors=self.velocities,
            origins=self.centers,
            class_ids=self.class_ids,
        )

    def as_linestrips3d(self) -> rr.LineStrips3D:
        """Return future trajectories data as a list of `rr.LineStrips3D`.

        Returns:
            `rr.LineStrips3D` object for each box.
        """
        stripes = []
        class_ids = []
        for class_id, future in zip(self.class_ids, self.future):
            class_ids += [class_id] * future.num_mode
            stripes += [waypoints for _, waypoints in future]
        return rr.LineStrips3D(strips=stripes, class_ids=class_ids)


@define
class BoxData2D:
    """A class to store 2D boxes data for rendering.

    Attributes:
        label2id (dict[str, int]): Key-value of map of label name and its ID.
        rois (list[RoiLike]): List of ROIs in the order of (xmin, ymin, xmax, ymax).
        class_ids (list[int]): List of label class IDs.
        uuids (list[str]): List of unique identifier IDs.
    """

    label2id: dict[str, int] = field(factory=dict)
    rois: list[RoiLike] = field(init=False, factory=list)
    class_ids: list[int] = field(init=False, factory=list)
    uuids: list[str] = field(init=False, factory=list)

    @overload
    def append(self, box: Box2D) -> None:
        """Append a 2D box data with a `Box2D` object.

        Args:
            box (Box2D): `Box2D` object.
        """
        pass

    @overload
    def append(self, roi: RoiLike, class_id: int, uuid: str | None = None) -> None:
        """Append a 2D box data with its elements.

        Args:
            roi (RoiLike): ROI in the order of (xmin, ymin, xmax, ymax).
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
        self.rois.append(box.roi.roi)

        if box.semantic_label.name not in self.label2id:
            self.label2id[box.semantic_label.name] = len(self.label2id)

        self.class_ids.append(self.label2id[box.semantic_label.name])

        if box.uuid is not None:
            self.uuids.append(box.uuid)

    def _append_with_elements(self, roi: RoiLike, class_id: int, uuid: str | None = None) -> None:
        self.rois.append(roi)

        self.class_ids.append(class_id)

        if uuid is not None:
            self.uuids.append(uuid)

    def as_boxes2d(self) -> rr.Boxes2D:
        """Return 2D boxes data as a `rr.Boxes2D`.

        Returns:
            `rr.Boxes2D` object.
        """
        labels = None if len(self.uuids) == 0 else self.uuids
        return rr.Boxes2D(
            array=self.rois,
            array_format=rr.Box2DFormat.XYXY,
            labels=labels,
            class_ids=self.class_ids,
            show_labels=False,
        )
