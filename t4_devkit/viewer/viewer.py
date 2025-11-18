from __future__ import annotations

import os.path as osp
import warnings
from typing import TYPE_CHECKING, Callable, Sequence, overload

import numpy as np
import rerun as rr

from t4_devkit.common.converter import to_quaternion
from t4_devkit.common.timestamp import microseconds2seconds
from t4_devkit.lanelet import LaneletParser
from t4_devkit.schema import SensorModality

from .color import PointCloudColorMode, pointcloud_color
from .config import ViewerConfig, format_entity
from .geography import calculate_geodetic_point
from .lanelet import (
    render_geographic_borders,
    render_lanelets,
    render_traffic_elements,
    render_ways,
)
from .record import BatchBox2D, BatchBox3D, BatchSegmentation2D

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, Future, PointCloudLike
    from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor
    from t4_devkit.typing import (
        CamIntrinsicLike,
        NDArrayU8,
        RoiLike,
        RotationLike,
        Vector2Like,
        Vector3Like,
    )

__all__ = ["RerunViewer"]


def _check_spatial3d(function: Callable) -> Callable:
    """Check if the viewer has the 3D view space.

    Note:
        This function is supposed to be used as a decorator for methods of RerunViewer.
    """

    def checker(viewer: RerunViewer, *args, **kwargs):
        if not viewer.config.has_spatial3d():
            warnings.warn("There is no 3D view space")
            return
        else:
            return function(viewer, *args, **kwargs)

    return checker


def _check_spatial2d(function: Callable) -> Callable:
    """Check if the viewer has the 2D view space.

    Note:
        This function is supposed to be used as a decorator for methods of RerunViewer.
    """

    def checker(viewer: RerunViewer, *args, **kwargs):
        if not viewer.config.has_spatial2d():
            warnings.warn("There is no 2D view space")
            return
        else:
            return function(viewer, *args, **kwargs)

    return checker


def _check_filepath(function: Callable) -> Callable:
    """Check if the input filepath exists.

    Note:
        This function is supposed to be used as a decorator for methods of RerunViewer.
    """

    def checker(viewer: RerunViewer, filepath: str):
        if not osp.exists(filepath):
            warnings.warn(f"File not found: {filepath}")
            return
        else:
            return function(viewer, filepath)

    return checker


class RerunViewer:
    """A viewer class that renders some components powered by rerun."""

    def __init__(
        self,
        app_id: str,
        config: ViewerConfig = ViewerConfig(),
        save_dir: str | None = None,
    ) -> None:
        """Construct a new object.

        Args:
            app_id (str): Application ID.
            config (ViewerConfig): Configuration of the viewer.
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        Examples:
            >>> from t4_devkit.viewer import ViewerBuilder
            >>> viewer = (
                    ViewerBuilder()
                    .with_spatial3d()
                    .with_spatial2d(cameras=["CAM_FRONT", "CAM_BACK"])
                    .with_labels(label2id={"car": 1, "pedestrian": 2})
                    .with_streetmap(latlon=[48.8566, 2.3522])
                    .build(app_id="my_viewer")
                )
        """
        self.app_id = app_id
        self.config = config
        self.blueprint = self.config.to_blueprint()

        rr.init(
            application_id=self.app_id,
            recording_id=None,
            spawn=save_dir is None,
            default_enabled=True,
            strict=True,
            default_blueprint=self.blueprint,
        )

        # NOTE: rr.save() must be invoked before logging
        if save_dir is not None:
            self._start_saving(save_dir=save_dir)

        rr.log(self.config.map_entity, rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

        rr.log(
            self.config.map_entity,
            rr.AnnotationContext(
                [
                    rr.AnnotationInfo(id=label_id, label=label)
                    for label, label_id in self.label2id.items()
                ]
            ),
            static=True,
        )

    @property
    def label2id(self) -> dict[str, int]:
        return self.config.label2id

    @property
    def latlon(self) -> Vector2Like | None:
        return self.config.latlon

    def _start_saving(self, save_dir: str) -> None:
        """Save recording result as `save_dir/{app_id}.rrd`.

        Note:
            This method must be called before any logging started.

        Args:
            save_dir (str): Directory path to save the result.
        """
        filepath = osp.join(save_dir, f"{self.app_id}.rrd")
        rr.save(filepath, default_blueprint=self.blueprint)

    @overload
    def render_box3ds(self, seconds: float, boxes: Sequence[Box3D]) -> None:
        """Render 3D boxes.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box3D]): Sequence of `Box3D`s.
        """
        pass

    @overload
    def render_box3ds(
        self,
        seconds: float,
        frame_id: str,
        centers: Sequence[Vector3Like],
        rotations: Sequence[RotationLike],
        sizes: Sequence[Vector3Like],
        class_ids: Sequence[int],
        velocities: Sequence[Vector3Like] | None = None,
        uuids: Sequence[str] | None = None,
        futures: Sequence[Future] | None = None,
    ) -> None:
        """Render 3D boxes with its elements.

        Args:
            seconds (float): Timestamp in [sec].
            frame_id (str): Frame ID.
            centers (Sequence[Vector3Like]): Sequence of 3D positions in the order of (x, y, z).
            rotations (Sequence[RotationLike]): Sequence of rotations.
            sizes (Sequence[Vector3Like]): Sequence of box sizes in the order of (width, length, height).
            class_ids (Sequence[int]): Sequence of class IDs.
            velocities (Sequence[Vector3Like] | None, optional): Sequence of velocities.
            uuids (Sequence[str] | None, optional): Sequence of unique identifiers.
            futures (Sequence[Future] | None, optional): Sequence future trajectories.
        """
        pass

    @_check_spatial3d
    def render_box3ds(self, *args, **kwargs) -> None:
        """Render 3D boxes."""
        if len(args) + len(kwargs) == 2:
            self._render_box3ds_with_boxes(*args, **kwargs)
        else:
            self._render_box3ds_with_elements(*args, **kwargs)

    def _render_box3ds_with_boxes(self, seconds: float, boxes: Sequence[Box3D]) -> None:
        rr.set_time_seconds(self.config.timeline, seconds)

        batches: dict[str, BatchBox3D] = {}
        for box in boxes:
            if box.frame_id not in batches:
                batches[box.frame_id] = BatchBox3D(label2id=self.label2id)
            batches[box.frame_id].append(box)

        for frame_id, batch in batches.items():
            # record boxes 3d
            rr.log(
                format_entity(self.config.map_entity, frame_id, "box"),
                batch.as_boxes3d(),
            )
            # record velocities
            rr.log(
                format_entity(self.config.map_entity, frame_id, "velocity"),
                batch.as_arrows3d(),
            )
            # record futures
            rr.log(
                format_entity(self.config.map_entity, frame_id, "future"),
                batch.as_linestrips3d(),
            )

    def _render_box3ds_with_elements(
        self,
        seconds: float,
        frame_id: str,
        centers: Sequence[Vector3Like],
        rotations: Sequence[RotationLike],
        sizes: Sequence[Vector3Like],
        class_ids: Sequence[int],
        velocities: Sequence[Vector3Like] | None = None,
        uuids: Sequence[str] | None | None = None,
        futures: Sequence[Future] | None = None,
    ) -> None:
        if uuids is None:
            uuids = [None] * len(centers)

        if velocities is None:
            velocities = [None] * len(centers)
            show_arrows = False
        else:
            show_arrows = True

        if futures is None:
            futures = [None] * len(centers)
            show_futures = False
        else:
            show_futures = True

        batch = BatchBox3D(label2id=self.label2id)
        for center, rotation, size, class_id, velocity, uuid, future in zip(
            centers,
            rotations,
            sizes,
            class_ids,
            velocities,
            uuids,
            futures,
            strict=True,
        ):
            batch.append(
                center=center,
                rotation=rotation,
                size=size,
                class_id=class_id,
                velocity=velocity,
                uuid=uuid,
                future=future,
            )

        rr.set_time_seconds(self.config.timeline, seconds)

        rr.log(format_entity(self.config.map_entity, frame_id, "box"), batch.as_boxes3d())

        if show_arrows:
            rr.log(
                format_entity(self.config.map_entity, frame_id, "velocity"),
                batch.as_arrows3d(),
            )

        if show_futures:
            rr.log(
                format_entity(self.config.map_entity, frame_id, "future"),
                batch.as_linestrips3d(),
            )

    @overload
    def render_box2ds(self, seconds: float, boxes: Sequence[Box2D]) -> None:
        """Render 2D boxes. Note that if the viewer initialized without `cameras=None`,
        no 2D box will be rendered.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box2D]): Sequence of `Box2D`s.
        """
        pass

    @overload
    def render_box2ds(
        self,
        seconds: float,
        camera: str,
        rois: Sequence[RoiLike],
        class_ids: Sequence[int],
        uuids: Sequence[str] | None = None,
    ) -> None:
        """Render 2D boxes with its elements.

        Args:
            seconds (float): Timestamp in [sec].
            camera (str): Camera name.
            rois (Sequence[RoiLike]): Sequence of ROIs in the order of (xmin, ymin, xmax, ymax).
            class_ids (Sequence[int]): Sequence of class IDs.
            uuids (Sequence[str] | None, optional): Sequence of unique identifiers.
        """
        pass

    @_check_spatial2d
    def render_box2ds(self, *args, **kwargs) -> None:
        """Render 2D boxes."""
        if len(args) + len(kwargs) == 2:
            self._render_box2ds_with_boxes(*args, **kwargs)
        else:
            self._render_box2ds_with_elements(*args, **kwargs)

    def _render_box2ds_with_boxes(self, seconds: float, boxes: Sequence[Box2D]) -> None:
        rr.set_time_seconds(self.config.timeline, seconds)

        batches: dict[str, BatchBox2D] = {}
        for box in boxes:
            if box.frame_id not in batches:
                batches[box.frame_id] = BatchBox2D(label2id=self.label2id)
            batches[box.frame_id].append(box)

        for frame_id, batch in batches.items():
            rr.log(
                format_entity(self.config.ego_entity, frame_id, "box"),
                batch.as_boxes2d(),
            )

    def _render_box2ds_with_elements(
        self,
        seconds: float,
        camera: str,
        rois: Sequence[RoiLike],
        class_ids: Sequence[int],
        uuids: Sequence[str] | None = None,
    ) -> None:
        if uuids is None:
            uuids = [None] * len(rois)

        batch = BatchBox2D(label2id=self.label2id)
        for roi, class_id, uuid in zip(rois, class_ids, uuids, strict=True):
            batch.append(roi=roi, class_id=class_id, uuid=uuid)

        rr.set_time_seconds(self.config.timeline, seconds)
        rr.log(format_entity(self.config.ego_entity, camera, "box"), batch.as_boxes2d())

    @_check_spatial2d
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
        rr.set_time_seconds(self.config.timeline, seconds)

        batch = BatchSegmentation2D()
        if uuids is None:
            uuids = [None] * len(masks)
        for mask, class_id, uuid in zip(masks, class_ids, uuids, strict=True):
            batch.append(mask, class_id, uuid)

        rr.log(
            format_entity(self.config.ego_entity, camera, "segmentation"),
            batch.as_segmentation_image(),
        )

    @_check_spatial3d
    def render_pointcloud(
        self,
        seconds: float,
        channel: str,
        pointcloud: PointCloudLike,
        color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
    ) -> None:
        """Render pointcloud.

        Args:
            seconds (float): Timestamp in [sec].
            channel (str): Name of the pointcloud sensor channel.
            pointcloud (PointCloudLike): Inherence object of `PointCloud`.
            color_mode (PointCloudColorMode, optional): Color mode for pointcloud.
        """
        # TODO(ktro2828): add support of rendering pointcloud on images
        rr.set_time_seconds(self.config.timeline, seconds)

        colors = pointcloud_color(pointcloud, color_mode=color_mode)
        rr.log(
            format_entity(self.config.ego_entity, channel),
            rr.Points3D(pointcloud.points[:3].T, colors=colors),
        )

    @_check_spatial2d
    def render_image(self, seconds: float, camera: str, image: str | NDArrayU8) -> None:
        """Render an image.

        Args:
            seconds (float): Timestamp in [sec].
            camera (str): Name of the camera channel.
            image (str | NDArrayU8): Image tensor or path of the image file.
        """
        rr.set_time_seconds(self.config.timeline, seconds)

        if isinstance(image, str):
            rr.log(format_entity(self.config.ego_entity, camera), rr.ImageEncoded(path=image))
        else:
            rr.log(format_entity(self.config.ego_entity, camera), rr.Image(image))

    @overload
    def render_ego(self, ego_pose: EgoPose) -> None:
        """Render an ego pose.

        Args:
            ego_pose (EgoPose): `EgoPose` object.
        """
        pass

    @overload
    def render_ego(
        self,
        seconds: float,
        translation: Vector3Like,
        rotation: RotationLike,
        geocoordinate: Vector3Like | None = None,
    ) -> None:
        """Render an ego pose.

        Args:
            seconds (float): Timestamp in [sec].
            translation (Vector3Like): 3D position in the map coordinate system
              , in the order of (x, y, z) in [m].
            rotation (RotationLike): Rotation in the map coordinate system.
            geocoordinate (Vector3Like | None, optional): Coordinates in the WGS 84
                reference ellipsoid (latitude, longitude, altitude) in degrees and meters.
        """
        pass

    @_check_spatial3d
    def render_ego(self, *args, **kwargs) -> None:
        """Render an ego pose."""
        if len(args) + len(kwargs) == 1:
            self._render_ego_with_schema(*args, **kwargs)
        else:
            self._render_ego_without_schema(*args, **kwargs)

    def _render_ego_with_schema(self, ego_pose: EgoPose) -> None:
        self._render_ego_without_schema(
            seconds=microseconds2seconds(ego_pose.timestamp),
            translation=ego_pose.translation,
            rotation=ego_pose.rotation,
            geocoordinate=ego_pose.geocoordinate,
        )

    def _render_ego_without_schema(
        self,
        seconds: float,
        translation: Vector3Like,
        rotation: RotationLike,
        geocoordinate: Vector3Like | None = None,
    ) -> None:
        rr.set_time_seconds(self.config.timeline, seconds)

        rr.log(
            self.config.ego_entity,
            rr.Transform3D(
                translation=translation,
                rotation=_to_rerun_quaternion(rotation),
                relation=rr.TransformRelation.ParentFromChild,
            ),
        )

        if geocoordinate is not None:
            latitude, longitude, _ = geocoordinate
            rr.log(
                self.config.geocoordinate_entity,
                rr.GeoPoints(lat_lon=(latitude, longitude)),
            )
        elif self.latlon is not None:
            latitude, longitude = calculate_geodetic_point(translation, self.latlon)
            rr.log(
                self.config.geocoordinate_entity,
                rr.GeoPoints(lat_lon=(latitude, longitude)),
            )

    @overload
    def render_calibration(
        self,
        sensor: Sensor,
        calibration: CalibratedSensor,
        resolution: Vector2Like | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            sensor (Sensor): `Sensor` object.
            calibration (CalibratedSensor): `CalibratedSensor` object.
            resolution (Vector2Like | None, optional): Camera resolution (width, height).
        """
        pass

    @overload
    def render_calibration(
        self,
        channel: str,
        modality: str | SensorModality,
        translation: Vector3Like,
        rotation: RotationLike,
        camera_intrinsic: CamIntrinsicLike | None = None,
        resolution: Vector2Like | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            channel (str): Name of the sensor channel.
            modality (str | SensorModality): Sensor modality.
            translation (Vector3Like): Sensor translation in ego centric coords.
            rotation (RotationLike): Sensor rotation in ego centric coords.
            camera_intrinsic (CamIntrinsicLike | None, optional): Camera intrinsic matrix.
            resolution (Vector2Like | None, optional): Camera resolution (width, height).
        """
        pass

    @_check_spatial3d
    def render_calibration(self, *args, **kwargs) -> None:
        """Render a sensor calibration."""
        if len(args) + len(kwargs) <= 3:
            self._render_calibration_with_schema(*args, **kwargs)
        else:
            self._render_calibration_without_schema(*args, **kwargs)

    def _render_calibration_with_schema(
        self,
        sensor: Sensor,
        calibration: CalibratedSensor,
        resolution: Vector2Like | None = None,
    ) -> None:
        self._render_calibration_without_schema(
            channel=sensor.channel,
            modality=sensor.modality,
            translation=calibration.translation,
            rotation=calibration.rotation,
            camera_intrinsic=calibration.camera_intrinsic,
            resolution=resolution,
        )

    def _render_calibration_without_schema(
        self,
        channel: str,
        modality: str | SensorModality,
        translation: Vector3Like,
        rotation: RotationLike,
        camera_intrinsic: CamIntrinsicLike | None = None,
        resolution: Vector2Like | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            channel (str): Name of the sensor channel.
            modality (str | SensorModality): Sensor modality.
            translation (Vector3Like): Sensor translation in ego centric coords.
            rotation (RotationLike): Sensor rotation in ego centric coords.
            camera_intrinsic (CamIntrinsicLike | None, optional): Camera intrinsic matrix.
            resolution (Vector2Like | None, optional): Camera resolution (width, height).
        """
        rr.log(
            format_entity(self.config.ego_entity, channel),
            rr.Transform3D(translation=translation, rotation=_to_rerun_quaternion(rotation)),
            static=True,
        )

        if modality == SensorModality.CAMERA:
            rr.log(
                format_entity(self.config.ego_entity, channel),
                rr.Pinhole(image_from_camera=camera_intrinsic, resolution=resolution),
                static=True,
            )

    @_check_filepath
    @_check_spatial3d
    def render_map(self, filepath: str) -> None:
        """Render vector map.

        Args:
            filepath (str): Path to OSM file.
        """
        parser = LaneletParser(filepath, verbose=False)

        root_entity = format_entity(self.config.map_entity, "vector_map")
        render_lanelets(parser, root_entity)
        render_traffic_elements(parser, root_entity)
        render_ways(parser, root_entity)

        render_geographic_borders(parser, f"{self.config.geocoordinate_entity}/vector_map")


def _to_rerun_quaternion(rotation: RotationLike) -> rr.Quaternion:
    rotation_xyzw = np.roll(to_quaternion(rotation).q, shift=-1)
    return rr.Quaternion(xyzw=rotation_xyzw)
