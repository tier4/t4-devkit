from __future__ import annotations

import os.path as osp
import warnings
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Sequence

import numpy as np
import rerun as rr
import rerun.blueprint as rrb

from t4_devkit.common.timestamp import us2sec
from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor, SensorModality
from t4_devkit.typing import CamIntrinsicType, NDArrayU8, RotationType, TranslationType

from .color import distance_color
from .rendering_data import BoxData2D, BoxData3D

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, PointCloud


__all__ = ["Tier4Viewer"]


class Tier4Viewer:
    # entity paths
    map_entity = "map"
    ego_entity = "map/base_link"
    timeline = "timestamp"

    def __init__(
        self,
        app_id: str,
        cameras: Sequence[str] | None = None,
        *,
        without_3d: bool = False,
        spawn: bool = True,
    ) -> None:
        """Construct a new object.

        Args:
            app_id (str): Application ID.
            cameras (Sequence[str] | None, optional): Sequence of camera names.
            without_3d (bool, optional): Whether to render objects without the 3D space.
            spawn (bool, optional): Whether to spawn the viewer.
        """
        self.app_id = app_id
        self.without_3d = without_3d
        self.cameras = cameras

        view_container = []
        if not without_3d:
            view_container.append(
                rrb.Horizontal(
                    rrb.Spatial3DView(name="3D", origin=self.map_entity),
                    column_shares=[3, 1],
                )
            )

        if self.cameras is not None:
            camera_space_views = [
                rrb.Spatial2DView(name=name, origin=osp.join(self.ego_entity, name))
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

    def save(self, save_dir: str) -> None:
        """Save recording result as `{app_id}.rrd`.

        Args:
            save_dir (str): Directory path to save the result.
        """
        filepath = osp.join(save_dir, f"{self.app_id}.rrd")
        rr.save(filepath, default_blueprint=self.blueprint)

    def render_box3ds(self, seconds: float, boxes: Sequence[Box3D]) -> None:
        """Render 3D boxes.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box3D]): Sequence of `Box3D`s.
        """
        rr.set_time_seconds(self.timeline, seconds)

        box_data: dict[str, BoxData3D] = {}
        for box in boxes:
            if box.frame_id not in box_data:
                box_data[box.frame_id] = BoxData3D()
            else:
                box_data[box.frame_id].append(box)

        for frame_id, data in box_data.items():
            # record boxes 3d
            rr.log(
                osp.join(self.map_entity, frame_id, "box"),
                data.as_boxes3d(),
            )
            # record velocities
            rr.log(
                osp.join(self.map_entity, frame_id, "velocity"),
                data.as_arrows3d(),
            )

    def render_box2ds(self, seconds: float, boxes: Sequence[Box2D]) -> None:
        """Render 2D boxes.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box2D]): Sequence of `Box2D`s.
        """
        if self.cameras is None:
            warnings.warn("There is no camera space.")
            return

        rr.set_time_seconds(self.timeline, seconds)

        box_data: dict[str, BoxData2D] = {}
        for box in boxes:
            if box.frame_id not in box_data:
                box_data[box.frame_id] = BoxData2D()
            else:
                box_data[box.frame_id].append(box)

        for frame_id, data in box_data.items():
            rr.log(
                osp.join(self.ego_entity, frame_id, "box"),
                data.as_boxes2d(),
            )

    def render_pointcloud(self, seconds: float, channel: str, pointcloud: PointCloud) -> None:
        """Render pointcloud.

        Args:
            seconds (float): Timestamp in [sec].
            channel (str): Name of the pointcloud sensor channel.
            pointcloud (PointCloud): Inherence object of `PointCloud`.
        """
        rr.set_time_seconds(self.timeline, seconds)

        colors = distance_color(np.linalg.norm(pointcloud.points[:3].T, axis=1))
        rr.log(
            osp.join(self.ego_entity, channel),
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
        if self.cameras is None or camera not in self.cameras:
            warnings.warn(f"There is no camera space: {camera}")
            return

        rr.set_time_seconds(self.timeline, seconds)

        if isinstance(image, str):
            rr.log(osp.join(self.ego_entity, camera), rr.ImageEncoded(image))
        else:
            rr.log(osp.join(self.ego_entity, camera), rr.Image(image))

    @singledispatchmethod
    def render_ego(self, *args, **kwargs) -> None:
        raise TypeError("Unexpected parameter types.")

    @render_ego.register
    def _render_ego_with_schema(self, ego_pose: EgoPose) -> None:
        """Render an ego pose.

        Args:
            ego_pose (EgoPose): `EgoPose` object.
        """
        rr.set_time_seconds(self.timeline, us2sec(ego_pose.timestamp))

        rotation_xyzw = np.roll(ego_pose.rotation.q, shift=-1)
        rr.log(
            self.ego_entity,
            rr.Transform3D(
                translation=ego_pose.translation,
                rotation=rr.Quaternion(xyzw=rotation_xyzw),
                from_parent=False,
            ),
        )

    @render_ego.register
    def _render_ego_without_schema(
        self,
        seconds: float,
        translation: TranslationType,
        rotation: RotationType,
    ) -> None:
        rr.set_time_seconds(self.timeline, seconds)

        rotation_xyzw = np.roll(rotation.q, shift=-1)
        rr.log(
            self.ego_entity,
            rr.Transform3D(
                translation=translation,
                rotation=rr.Quaternion(xyzw=rotation_xyzw),
                from_parent=False,
            ),
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
        rotation_xyzw = np.roll(calibration.rotation.q, shift=-1)

        rr.log(
            osp.join(self.ego_entity, sensor.channel),
            rr.Transform3D(
                translation=calibration.translation,
                rotation=rr.Quaternion(xyzw=rotation_xyzw),
            ),
            static=True,
        )

        if sensor.modality == SensorModality.CAMERA:
            rr.log(
                osp.join(self.ego_entity, sensor.channel),
                rr.Pinhole(image_from_camera=calibration.camera_intrinsic),
                static=True,
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
            osp.join(self.ego_entity, channel),
            rr.Transform3D(translation=translation, rotation=rr.Quaternion(xyzw=rotation_xyzw)),
            static=True,
        )

        if modality == SensorModality.CAMERA:
            rr.log(
                osp.join(self.ego_entity, channel),
                rr.Pinhole(image_from_camera=camera_intrinsic),
                static=True,
            )