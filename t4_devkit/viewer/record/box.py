from __future__ import annotations

from typing import TYPE_CHECKING, overload

import numpy as np
import rerun as rr
import rerun.components as rrc
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, Future
    from t4_devkit.typing import QuaternionLike, RoiLike, Vector3Like

__all__ = ["BatchBox3D", "BatchBox2D"]


@define
class BatchBox3D:
    """A class to store 3D boxes data for rendering.

    Attributes:
        label2id (dict[str, int]): Key-value of map of label name and its ID.
        records (list[Record]): List of 3D box records for rendering.
    """

    label2id: dict[str, int] = field(factory=dict)
    records: list[Record] = field(init=False, factory=list)

    @define
    class Record:
        """Inner class to represent a record of 3D box instance for rendering."""

        center: Vector3Like
        rotation: rr.Quaternion
        size: Vector3Like
        class_id: int
        uuid: int | None = field(default=None)
        velocity: Vector3Like | None = field(default=None)
        future: Future | None = field(default=None)

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
        if box.semantic_label.name not in self.label2id:
            self.label2id[box.semantic_label.name] = len(self.label2id)

        self._append_with_elements(
            center=box.position,
            rotation=box.rotation,
            size=box.size,
            class_id=self.label2id[box.semantic_label.name],
            uuid=box.uuid,
            velocity=box.velocity,
            future=box.future,
        )

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
        rotation_xyzw = np.roll(rotation.q, shift=-1)

        width, length, height = size

        self.records.append(
            self.Record(
                center=center,
                rotation=rr.Quaternion(xyzw=rotation_xyzw),
                size=(length, width, height),
                class_id=class_id,
                uuid=uuid,
                velocity=velocity,
                future=future,
            )
        )

    def as_boxes3d(self) -> rr.Boxes3D:
        """Return 3D boxes data as a `rr.Boxes3D`.

        Returns:
            `rr.Boxes3D` object.
        """
        sizes, centers, rotations, class_ids, labels = map(
            list, zip(*((r.size, r.center, r.rotation, r.class_id, r.uuid) for r in self.records))
        )

        return rr.Boxes3D(
            sizes=sizes,
            centers=centers,
            rotations=rotations,
            fill_mode=rrc.FillMode.Solid,
            labels=labels,
            class_ids=class_ids,
            show_labels=False,
        )

    def as_arrows3d(self) -> rr.Arrows3D:
        """Return velocities data as a `rr.Arrows3D`.

        Returns:
            `rr.Arrows3D` object.
        """
        velocities, centers, class_ids = map(
            list,
            zip(
                *(
                    (r.velocity, r.center, r.class_id)
                    for r in self.records
                    if r.velocity is not None
                )
            ),
        )

        return rr.Arrows3D(
            vectors=velocities,
            origins=centers,
            class_ids=class_ids,
        )

    def as_linestrips3d(self) -> rr.LineStrips3D:
        """Return future trajectories data as a list of `rr.LineStrips3D`.

        Returns:
            `rr.LineStrips3D` object for each box.
        """
        class_ids = [
            record.class_id
            for record in self.records
            if record.future is not None
            for _ in range(record.future.num_mode)
        ]

        stripes = [
            waypoints
            for record in self.records
            if record.future is not None
            for _, waypoints in record.future
        ]
        return rr.LineStrips3D(strips=stripes, class_ids=class_ids)


@define
class BatchBox2D:
    """A class to store 2D boxes data for rendering.

    Attributes:
        label2id (dict[str, int]): Key-value of map of label name and its ID.
        records (list[Record]): List of 2D box records for rendering.
    """

    label2id: dict[str, int] = field(factory=dict)
    records: list[Record] = field(init=False, factory=list)

    @define
    class Record:
        """Inner class to represent a record of 2D box instance for rendering."""

        roi: RoiLike
        class_id: int
        uuid: str | None = field(default=None)

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
        if box.semantic_label.name not in self.label2id:
            self.label2id[box.semantic_label.name] = len(self.label2id)

        if box.roi is not None:
            self._append_with_elements(
                roi=box.roi.roi,
                class_id=self.label2id[box.semantic_label.name],
                uuid=box.uuid,
            )

    def _append_with_elements(self, roi: RoiLike, class_id: int, uuid: str | None = None) -> None:
        self.records.append(self.Record(roi=roi, class_id=class_id, uuid=uuid))

    def as_boxes2d(self) -> rr.Boxes2D:
        """Return 2D boxes data as a `rr.Boxes2D`.

        Returns:
            `rr.Boxes2D` object.
        """
        rois, class_ids, labels = map(
            list, zip(*((r.roi, r.class_id, r.uuid) for r in self.records))
        )

        return rr.Boxes2D(
            array=rois,
            array_format=rr.Box2DFormat.XYXY,
            labels=labels,
            class_ids=class_ids,
            show_labels=False,
        )
