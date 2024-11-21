from __future__ import annotations

import os.path as osp
import warnings
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Sequence

import numpy as np
import rerun as rr
import rerun.blueprint as rrb
from typing_extensions import Self

from t4_devkit.common.timestamp import us2sec
from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor, SensorModality
from t4_devkit.typing import (
    CamIntrinsicType,
    GeoCoordinateType,
    NDArrayU8,
    RotationType,
    TranslationType,
)

from .color import distance_color
from .rendering_data import BoxData2D, BoxData3D, SegmentationData2D

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, PointCloudLike


__all__ = ["Tier4Viewer", "format_entity"]


def format_entity(root: str, *entities) -> str:
    """Format entity path.

    Args:
        root (str): Root entity path.
        *entities: Entity path(s).

    Returns:
        Formatted entity path.

    Examples:
        >>> _format_entity("map")
        >>> "map"
        >>> _format_entity("map", "map/base_link")
        "map/base_link"
        >>> _format_entity("map", "map/base_link", "camera")
        "map/base_link/camera"
    """
    if len(entities) == 0:
        return root

    flattened = [s for t in entities for s in t.split("/")]

    if osp.basename(root) == flattened[0]:
        return osp.join(root, "/".join(flattened[1:])) if len(flattened) > 1 else root
    else:
        return osp.join(root, "/".join(entities))


class Tier4Viewer:
    """A viewer class that renders some components powered by rerun."""

    # entity paths
    map_entity = "map"
    ego_entity = "map/base_link"
    geocoordinate_entity = "geocoordinate"
    timeline = "timestamp"

    def __init__(
        self,
        app_id: str,
        *,
        cameras: Sequence[str] | None = None,
        with_3d: bool = True,
        spawn: bool = True,
    ) -> None:
        """Construct a new object.

        Args:
            app_id (str): Application ID.
            cameras (Sequence[str] | None, optional): Sequence of camera names.
                If `None`, any 2D spaces will not be visualized.
            with_3d (bool, optional): Whether to render objects with the 3D space.
            spawn (bool, optional): Whether to spawn the viewer.

        Examples:
            >>> from t4_devkit.viewer import Tier4Viewer
            # Rendering both 3D/2D spaces
            >>> viewer = Tier4Viewer("myapp", cameras=["camera0", "camera1"])
            # Rendering 3D space only
            >>> viewer = Tier4Viewer("myapp")
            # Rendering 2D space only
            >>> viewer = Tier4Viewer("myapp", cameras=["camera0", "camera1"], with_3d=False)
        """
        self.app_id = app_id
        self.cameras = cameras
        self.with_3d = with_3d
        self.with_2d = self.cameras is not None
        self.label2id: dict[str, int] | None = None

        if not self.with_3d and not self.with_2d:
            raise ValueError("At least one of 3D or 2D spaces must be rendered.")

        view_container: list[rrb.Container | rrb.SpaceView] = []
        if self.with_3d:
            view_container.extend(
                [
                    rrb.Horizontal(
                        rrb.Spatial3DView(name="3D", origin=self.map_entity),
                        rrb.Horizontal(rrb.MapView(name="Map", origin=self.geocoordinate_entity)),
                        column_shares=[3, 1],
                    ),
                ]
            )

        if self.with_2d:
            camera_space_views = [
                rrb.Spatial2DView(name=name, origin=format_entity(self.ego_entity, name))
                for name in self.cameras
            ]
            view_container.append(rrb.Grid(*camera_space_views))

        self.blueprint = rrb.Vertical(*view_container, row_shares=[4, 2])

        rr.init(
            application_id=self.app_id,
            recording_id=None,
            spawn=spawn,
            default_enabled=True,
            strict=True,
            default_blueprint=self.blueprint,
        )

        rr.log(self.map_entity, rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    def with_labels(self, label2id: dict[str, int]) -> Self:
        """Return myself after creating `rr.AnnotationContext` on the recording.

        Args:
            label2id (dict[str, int]): Key-value mapping which maps label name to its class ID.

        Returns:
            Self instance.

        Examples:
            >>> label2id = {"car": 0, "pedestrian": 1}
            >>> viewer = Tier4Viewer("myapp").with_labels(label2id)
        """
        self.label2id = label2id

        rr.log(
            self.map_entity,
            rr.AnnotationContext(
                [
                    rr.AnnotationInfo(id=label_id, label=label)
                    for label, label_id in self.label2id.items()
                ]
            ),
            static=True,
        )

        return self

    def save(self, save_dir: str) -> None:
        """Save recording result as `save_dir/{app_id}.rrd`.

        Args:
            save_dir (str): Directory path to save the result.
        """
        filepath = osp.join(save_dir, f"{self.app_id}.rrd")
        rr.save(filepath, default_blueprint=self.blueprint)

    def render_box3ds(self, seconds: float, boxes: Sequence[Box3D]) -> None:
        """Render 3D boxes. Note that if the viewer initialized with `with_3d=False`,
        no 3D box will be rendered.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box3D]): Sequence of `Box3D`s.
        """
        if not self.with_3d:
            warnings.warn("There is no camera space.")
            return

        rr.set_time_seconds(self.timeline, seconds)

        box_data: dict[str, BoxData3D] = {}
        for box in boxes:
            if box.frame_id not in box_data:
                box_data[box.frame_id] = BoxData3D(label2id=self.label2id)
            else:
                box_data[box.frame_id].append(box)

        for frame_id, data in box_data.items():
            # record boxes 3d
            rr.log(
                format_entity(self.map_entity, frame_id, "box"),
                data.as_boxes3d(),
            )
            # record velocities
            rr.log(
                format_entity(self.map_entity, frame_id, "velocity"),
                data.as_arrows3d(),
            )

    def render_box2ds(self, seconds: float, boxes: Sequence[Box2D]) -> None:
        """Render 2D boxes. Note that if the viewer initialized without `cameras=None`,
        no 2D box will be rendered.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box2D]): Sequence of `Box2D`s.
        """
        if not self.with_2d:
            warnings.warn("There is no camera space.")
            return

        rr.set_time_seconds(self.timeline, seconds)

        box_data: dict[str, BoxData2D] = {}
        for box in boxes:
            if box.frame_id not in box_data:
                box_data[box.frame_id] = BoxData2D(label2id=self.label2id)
            else:
                box_data[box.frame_id].append(box)

        for frame_id, data in box_data.items():
            rr.log(
                format_entity(self.ego_entity, frame_id, "box"),
                data.as_boxes2d(),
            )

    def render_segmentation2d(
        self,
        seconds: float,
        camera: str,
        masks: Sequence[NDArrayU8],
        class_ids: Sequence[int],
        uuids: Sequence[str | None] | None = None,
    ) -> None:
        """Render 2D segmentation image.

        Args:
            seconds (float): Timestamp in [sec].
            camera (str): Name of camera channel.
            masks (Sequence[NDArrayU8]): Sequence of segmentation mask of each instance,
                each mask is the shape of (W, H).
            class_ids (Sequence[int]): Sequence of label ids.
            uuids (Sequence[str | None] | None, optional): Sequence of each instance ID.
        """
        if not self.with_2d or camera not in self.cameras:
            warnings.warn(f"There is no camera space: {camera}")
            return

        rr.set_time_seconds(self.timeline, seconds)

        segmentation_data = SegmentationData2D()
        if uuids is None:
            uuids = [None] * len(masks)
        for mask, class_id, uuid in zip(masks, class_ids, uuids, strict=True):
            segmentation_data.append(mask, class_id, uuid)

        rr.log(
            format_entity(self.ego_entity, camera, "segmentation"),
            segmentation_data.as_segmentation_image(),
        )

    def render_pointcloud(self, seconds: float, channel: str, pointcloud: PointCloudLike) -> None:
        """Render pointcloud.

        Args:
            seconds (float): Timestamp in [sec].
            channel (str): Name of the pointcloud sensor channel.
            pointcloud (PointCloudLike): Inherence object of `PointCloud`.
        """
        # TODO(ktro2828): add support of rendering pointcloud on images
        rr.set_time_seconds(self.timeline, seconds)

        colors = distance_color(np.linalg.norm(pointcloud.points[:3].T, axis=1))
        rr.log(
            format_entity(self.ego_entity, channel),
            rr.Points3D(
                pointcloud.points[:3].T,
                colors=colors,
            ),
        )

    def render_image(self, seconds: float, camera: str, image: str | NDArrayU8) -> None:
        """Render an image.

        Args:
            seconds (float): Timestamp in [sec].
            camera (str): Name of the camera channel.
            image (str | NDArrayU8): Image tensor or path of the image file.
        """
        if not self.with_2d or camera not in self.cameras:
            warnings.warn(f"There is no camera space: {camera}")
            return

        rr.set_time_seconds(self.timeline, seconds)

        if isinstance(image, str):
            rr.log(format_entity(self.ego_entity, camera), rr.ImageEncoded(path=image))
        else:
            rr.log(format_entity(self.ego_entity, camera), rr.Image(image))

    @singledispatchmethod
    def render_ego(self, *args, **kwargs) -> None:
        raise TypeError("Unexpected parameter types.")

    @render_ego.register
    def _render_ego_with_schema(self, ego_pose: EgoPose) -> None:
        """Render an ego pose.

        Args:
            ego_pose (EgoPose): `EgoPose` object.
        """
        self._render_ego_without_schema(
            seconds=us2sec(ego_pose.timestamp),
            translation=ego_pose.translation,
            rotation=ego_pose.rotation,
            geocoordinate=ego_pose.geocoordinate,
        )

    @render_ego.register
    def _render_ego_without_schema(
        self,
        seconds: float,
        translation: TranslationType,
        rotation: RotationType,
        geocoordinate: GeoCoordinateType | None = None,
    ) -> None:
        """Render an ego pose.

        Args:
            seconds (float): Timestamp in [sec].
            translation (TranslationType): 3D position in the map coordinate system
              , in the order of (x, y, z) in [m].
            rotation (RotationType): Rotation in the map coordinate system.
            geocoordinate (GeoCoordinateType | None, optional): Coordinates in the WGS 84
                reference ellipsoid (latitude, longitude, altitude) in degrees and meters.
        """
        rr.set_time_seconds(self.timeline, seconds)

        rotation_xyzw = np.roll(rotation.q, shift=-1)
        rr.log(
            self.ego_entity,
            rr.Transform3D(
                translation=translation,
                rotation=rr.Quaternion(xyzw=rotation_xyzw),
                relation=rr.TransformRelation.ParentFromChild,
            ),
        )

        if geocoordinate is not None:
            latitude, longitude, _ = geocoordinate
            rr.log(
                self.geocoordinate_entity,
                rr.GeoPoints(lat_lon=(latitude, longitude)),
            )

    @singledispatchmethod
    def render_calibration(self, *args, **kwargs) -> None:
        raise TypeError("Unexpected parameter types.")

    @render_calibration.register
    def _render_calibration_with_schema(
        self,
        sensor: Sensor,
        calibration: CalibratedSensor,
    ) -> None:
        """Render a sensor calibration.

        Args:
            sensor (Sensor): `Sensor` object.
            calibration (CalibratedSensor): `CalibratedSensor` object.
        """
        self._render_calibration_without_schema(
            channel=sensor.channel,
            modality=sensor.modality,
            translation=calibration.translation,
            rotation=calibration.rotation,
            camera_intrinsic=calibration.camera_intrinsic,
        )

    @render_calibration.register
    def _render_calibration_without_schema(
        self,
        channel: str,
        modality: str | SensorModality,
        translation: TranslationType,
        rotation: RotationType,
        camera_intrinsic: CamIntrinsicType | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            channel (str): Name of the sensor channel.
            modality (str | SensorModality): Sensor modality.
            translation (TranslationType): Sensor translation in ego centric coords.
            rotation (RotationType): Sensor rotation in ego centric coords.
            camera_intrinsic (CamIntrinsicType | None, optional): Camera intrinsic matrix.
                Defaults to None.
        """
        rotation_xyzw = np.roll(rotation.q, shift=-1)

        rr.log(
            format_entity(self.ego_entity, channel),
            rr.Transform3D(translation=translation, rotation=rr.Quaternion(xyzw=rotation_xyzw)),
            static=True,
        )

        if modality == SensorModality.CAMERA:
            rr.log(
                format_entity(self.ego_entity, channel),
                rr.Pinhole(image_from_camera=camera_intrinsic),
                static=True,
            )
