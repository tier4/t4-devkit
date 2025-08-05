from __future__ import annotations

import os.path as osp
import warnings
from typing import TYPE_CHECKING, Sequence, overload

import numpy as np
import rerun as rr
import rerun.blueprint as rrb
from typing_extensions import Self

from t4_devkit.common.timestamp import us2sec
from t4_devkit.schema import SensorModality

from .color import distance_color
from .geography import calculate_geodetic_point
from .record import BatchBox2D, BatchBox3D, BatchSegmentation2D

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box2D, Box3D, Future, PointCloudLike
    from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor
    from t4_devkit.typing import (
        CamIntrinsicLike,
        NDArrayU8,
        QuaternionLike,
        RoiLike,
        Vector3Like,
    )

__all__ = ["RerunViewer", "format_entity"]


def format_entity(*entities: Sequence[str]) -> str:
    """Format entity path.

    Args:
        *entities: Entity path(s).

    Returns:
        Formatted entity path.

    Examples:
        >>> format_entity("map")
        "map"
        >>> format_entity("map", "map/base_link")
        "map/base_link"
        >>> format_entity("map", "map/base_link", "camera")
        "map/base_link/camera"
    """
    if not entities:
        return ""

    flattened = []
    for entity in entities:
        for part in entity.split("/"):
            if part and flattened and flattened[-1] == part:
                continue
            flattened.append(part)
    return "/".join(flattened)


class RerunViewer:
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
        save_dir: str | None = None,
    ) -> None:
        """Construct a new object.

        Args:
            app_id (str): Application ID.
            cameras (Sequence[str] | None, optional): Sequence of camera names.
                If `None`, any 2D spaces will not be visualized.
            with_3d (bool, optional): Whether to render objects with the 3D space.
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        Examples:
            >>> from t4_devkit.viewer import RerunViewer
            # Rendering both 3D/2D spaces
            >>> viewer = RerunViewer("myapp", cameras=["camera0", "camera1"])
            # Rendering 3D space only
            >>> viewer = RerunViewer("myapp")
            # Rendering 2D space only
            >>> viewer = RerunViewer("myapp", cameras=["camera0", "camera1"], with_3d=False)
        """
        self.app_id = app_id
        self.cameras = cameras
        self.with_3d = with_3d
        self.with_2d = self.cameras is not None
        self.label2id: dict[str, int] | None = None
        self.global_origin: tuple[float, float] | None = None

        if not (self.with_3d or self.with_2d):
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
            spawn=save_dir is None,
            default_enabled=True,
            strict=True,
            default_blueprint=self.blueprint,
        )

        # NOTE: rr.save() must be invoked before logging
        if save_dir is not None:
            self._start_saving(save_dir=save_dir)

        rr.log(self.map_entity, rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    def with_labels(self, label2id: dict[str, int]) -> Self:
        """Return myself after creating `rr.AnnotationContext` on the recording.

        Args:
            label2id (dict[str, int]): Key-value mapping which maps label name to its class ID.

        Returns:
            Self instance.

        Examples:
            >>> label2id = {"car": 0, "pedestrian": 1}
            >>> viewer = RerunViewer("myapp").with_labels(label2id)
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

    def with_global_origin(self, lat_lon: tuple[float, float]) -> Self:
        """Return myself after setting global origin.

        Args:
            lat_lon (tuple[float, float]): Global origin of map (latitude, longitude).

        Returns:
            Self instance.

        Examples:
            >>> lat_lon = (42.336849169438615, -71.05785369873047)
            >>> viewer = RerunViewer("myapp").with_global_origin(lat_lon)
        """
        self.global_origin = lat_lon
        return self

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
        """Render 3D boxes. Note that if the viewer initialized with `with_3d=False`,
        no 3D box will be rendered.

        Args:
            seconds (float): Timestamp in [sec].
            boxes (Sequence[Box3D]): Sequence of `Box3D`s.
        """
        pass

    @overload
    def render_box3ds(
        self,
        seconds: float,
        centers: Sequence[Vector3Like],
        rotations: Sequence[QuaternionLike],
        sizes: Sequence[Vector3Like],
        class_ids: Sequence[int],
        velocities: Sequence[Vector3Like] | None = None,
        uuids: Sequence[str] | None = None,
        futures: Sequence[Future] | None = None,
    ) -> None:
        """Render 3D boxes with its elements.

        Args:
            seconds (float): Timestamp in [sec].
            centers (Sequence[Vector3Like]): Sequence of 3D positions in the order of (x, y, z).
            rotations (Sequence[QuaternionLike]): Sequence of quaternions.
            sizes (Sequence[Vector3Like]): Sequence of box sizes in the order of (width, length, height).
            class_ids (Sequence[int]): Sequence of class IDs.
            velocities (Sequence[Vector3Like] | None, optional): Sequence of velocities.
            uuids (Sequence[str] | None, optional): Sequence of unique identifiers.
            futures (Sequence[Future] | None, optional): Sequence future trajectories.
        """
        pass

    def render_box3ds(self, *args, **kwargs) -> None:
        """Render 3D boxes."""
        if len(args) + len(kwargs) == 2:
            self._render_box3ds_with_boxes(*args, **kwargs)
        else:
            self._render_box3ds_with_elements(*args, **kwargs)

    def _render_box3ds_with_boxes(self, seconds: float, boxes: Sequence[Box3D]) -> None:
        if not self.with_3d:
            warnings.warn("There is no camera space.")
            return

        rr.set_time_seconds(self.timeline, seconds)

        batches: dict[str, BatchBox3D] = {}
        for box in boxes:
            if box.frame_id not in batches:
                batches[box.frame_id] = BatchBox3D(label2id=self.label2id)
            batches[box.frame_id].append(box)

        for frame_id, batch in batches.items():
            # record boxes 3d
            rr.log(
                format_entity(self.map_entity, frame_id, "box"),
                batch.as_boxes3d(),
            )
            # record velocities
            rr.log(
                format_entity(self.map_entity, frame_id, "velocity"),
                batch.as_arrows3d(),
            )
            # record futures
            rr.log(
                format_entity(self.map_entity, frame_id, "future"),
                batch.as_linestrips3d(),
            )

    def _render_box3ds_with_elements(
        self,
        seconds: float,
        centers: Sequence[Vector3Like],
        rotations: Sequence[QuaternionLike],
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

        rr.set_time_seconds(self.timeline, seconds)

        rr.log(format_entity(self.ego_entity, "box"), batch.as_boxes3d())

        if show_arrows:
            rr.log(format_entity(self.ego_entity, "velocity"), batch.as_arrows3d())

        if show_futures:
            rr.log(format_entity(self.ego_entity, "future"), batch.as_linestrips3d())

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

    def render_box2ds(self, *args, **kwargs) -> None:
        """Render 2D boxes."""
        if len(args) + len(kwargs) == 2:
            self._render_box2ds_with_boxes(*args, **kwargs)
        else:
            self._render_box2ds_with_elements(*args, **kwargs)

    def _render_box2ds_with_boxes(self, seconds: float, boxes: Sequence[Box2D]) -> None:
        if not self.with_2d:
            warnings.warn("There is no camera space.")
            return

        rr.set_time_seconds(self.timeline, seconds)

        batches: dict[str, BatchBox2D] = {}
        for box in boxes:
            if box.frame_id not in batches:
                batches[box.frame_id] = BatchBox2D(label2id=self.label2id)
            batches[box.frame_id].append(box)

        for frame_id, batch in batches.items():
            rr.log(
                format_entity(self.ego_entity, frame_id, "box"),
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
        if not self.with_2d:
            warnings.warn("There is no camera space.")
            return

        if uuids is None:
            uuids = [None] * len(rois)

        batch = BatchBox2D(label2id=self.label2id)
        for roi, class_id, uuid in zip(rois, class_ids, uuids, strict=True):
            batch.append(roi=roi, class_id=class_id, uuid=uuid)

        rr.set_time_seconds(self.timeline, seconds)
        rr.log(format_entity(self.ego_entity, camera, "box"), batch.as_boxes2d())

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

        batch = BatchSegmentation2D()
        if uuids is None:
            uuids = [None] * len(masks)
        for mask, class_id, uuid in zip(masks, class_ids, uuids, strict=True):
            batch.append(mask, class_id, uuid)

        rr.log(
            format_entity(self.ego_entity, camera, "segmentation"),
            batch.as_segmentation_image(),
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
        rotation: QuaternionLike,
        geocoordinate: Vector3Like | None = None,
    ) -> None:
        """Render an ego pose.

        Args:
            seconds (float): Timestamp in [sec].
            translation (Vector3Like): 3D position in the map coordinate system
              , in the order of (x, y, z) in [m].
            rotation (QuaternionLike): Rotation in the map coordinate system.
            geocoordinate (Vector3Like | None, optional): Coordinates in the WGS 84
                reference ellipsoid (latitude, longitude, altitude) in degrees and meters.
        """
        pass

    def render_ego(self, *args, **kwargs) -> None:
        """Render an ego pose."""
        if len(args) + len(kwargs) == 1:
            self._render_ego_with_schema(*args, **kwargs)
        else:
            self._render_ego_without_schema(*args, **kwargs)

    def _render_ego_with_schema(self, ego_pose: EgoPose) -> None:
        self._render_ego_without_schema(
            seconds=us2sec(ego_pose.timestamp),
            translation=ego_pose.translation,
            rotation=ego_pose.rotation,
            geocoordinate=ego_pose.geocoordinate,
        )

    def _render_ego_without_schema(
        self,
        seconds: float,
        translation: Vector3Like,
        rotation: QuaternionLike,
        geocoordinate: Vector3Like | None = None,
    ) -> None:
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
        elif self.global_origin is not None:
            latitude, longitude = calculate_geodetic_point(translation, self.global_origin)
            rr.log(
                self.geocoordinate_entity,
                rr.GeoPoints(lat_lon=(latitude, longitude)),
            )

    @overload
    def render_calibration(
        self,
        sensor: Sensor,
        calibration: CalibratedSensor,
    ) -> None:
        """Render a sensor calibration.

        Args:
            sensor (Sensor): `Sensor` object.
            calibration (CalibratedSensor): `CalibratedSensor` object.
        """
        pass

    @overload
    def render_calibration(
        self,
        channel: str,
        modality: str | SensorModality,
        translation: Vector3Like,
        rotation: QuaternionLike,
        camera_intrinsic: CamIntrinsicLike | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            channel (str): Name of the sensor channel.
            modality (str | SensorModality): Sensor modality.
            translation (Vector3Like): Sensor translation in ego centric coords.
            rotation (QuaternionLike): Sensor rotation in ego centric coords.
            camera_intrinsic (CamIntrinsicLike | None, optional): Camera intrinsic matrix.
                Defaults to None.
        """
        pass

    def render_calibration(self, *args, **kwargs) -> None:
        """Render a sensor calibration."""
        if len(args) + len(kwargs) == 2:
            self._render_calibration_with_schema(*args, **kwargs)
        else:
            self._render_calibration_without_schema(*args, **kwargs)

    def _render_calibration_with_schema(
        self,
        sensor: Sensor,
        calibration: CalibratedSensor,
    ) -> None:
        self._render_calibration_without_schema(
            channel=sensor.channel,
            modality=sensor.modality,
            translation=calibration.translation,
            rotation=calibration.rotation,
            camera_intrinsic=calibration.camera_intrinsic,
        )

    def _render_calibration_without_schema(
        self,
        channel: str,
        modality: str | SensorModality,
        translation: Vector3Like,
        rotation: QuaternionLike,
        camera_intrinsic: CamIntrinsicLike | None = None,
    ) -> None:
        """Render a sensor calibration.

        Args:
            channel (str): Name of the sensor channel.
            modality (str | SensorModality): Sensor modality.
            translation (Vector3Like): Sensor translation in ego centric coords.
            rotation (QuaternionLike): Sensor rotation in ego centric coords.
            camera_intrinsic (CamIntrinsicLike | None, optional): Camera intrinsic matrix.
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
