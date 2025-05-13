from __future__ import annotations

import asyncio
import os.path as osp
from concurrent.futures import Future
from typing import TYPE_CHECKING, Sequence

import numpy as np
import rerun as rr
import yaml

from t4_devkit.common.timestamp import sec2us, us2sec
from t4_devkit.dataclass import LidarPointCloud, RadarPointCloud
from t4_devkit.schema import SensorModality
from t4_devkit.viewer import RerunViewer, distance_color, format_entity

if TYPE_CHECKING:
    from t4_devkit import Tier4
    from t4_devkit.schema import (
        CalibratedSensor,
        EgoPose,
        Instance,
        ObjectAnn,
        Sample,
        SampleAnnotation,
        SampleData,
        Scene,
        Sensor,
        SurfaceAnn,
    )

__all__ = ["RenderingHelper"]


class RenderingHelper:
    """Help `Tier4` class with rendering tasks."""

    def __init__(self, t4: Tier4) -> None:
        """Construct a new object.

        Args:
            t4 (Tier4): `Tier4` instance.
        """
        self._t4 = t4
        self._label2id: dict[str, int] = {
            category.name: idx for idx, category in enumerate(self._t4.category)
        }

    async def async_render_scene(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        future_seconds: float = 0.0,
        save_dir: str | None = None,
    ) -> Future:
        """Render specified scene.

        Args:
            scene_token (str): Unique identifier of scene.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            future_seconds (float, optional): Future time in [s].
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        Returns:
            Future aggregating results.
        """
        # search first sample data tokens
        first_lidar_tokens: list[str] = []
        first_radar_tokens: list[str] = []
        first_camera_tokens: list[str] = []
        for sensor in self._t4.sensor:
            sd_token = sensor.first_sd_token
            if sensor.modality == SensorModality.LIDAR:
                first_lidar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.RADAR:
                first_radar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.CAMERA:
                first_camera_tokens.append(sd_token)

        render3d = len(first_lidar_tokens) > 0 or len(first_radar_tokens) > 0
        render2d = len(first_camera_tokens) > 0

        app_id = f"scene@{scene_token}"
        viewer = self._init_viewer(
            app_id,
            render3d=render3d,
            render2d=render2d,
            render_ann=True,
            save_dir=save_dir,
        )

        scene: Scene = self._t4.get("scene", scene_token)
        first_sample: Sample = self._t4.get("sample", scene.first_sample_token)
        max_timestamp_us = first_sample.timestamp + sec2us(max_time_seconds)

        gather = await asyncio.gather(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_radars(
                viewer=viewer,
                first_radar_tokens=first_radar_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_cameras(
                viewer=viewer,
                first_camera_tokens=first_camera_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_annotation3ds(
                viewer=viewer,
                first_sample_token=scene.first_sample_token,
                max_timestamp_us=max_timestamp_us,
                future_seconds=future_seconds,
            ),
            self._render_annotation2ds(
                viewer=viewer,
                first_sample_token=scene.first_sample_token,
                max_timestamp_us=max_time_seconds,
            ),
        )

        return gather

    async def async_render_instance(
        self,
        instance_token: str | Sequence[str],
        *,
        future_seconds: float = 0.0,
        save_dir: str | None = None,
    ) -> Future:
        """Render particular instance.

        Args:
            instance_token (str | Sequence[str]): Instance token(s).
            future_seconds (float, optional): Future time in [s].
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        Returns:
            Future aggregating results.
        """
        instance_tokens = [instance_token] if isinstance(instance_token, str) else instance_token

        first_sample: Sample | None = None
        last_sample: Sample | None = None
        for token in instance_tokens:
            instance: Instance = self._t4.get("instance", token)
            first_ann: SampleAnnotation = self._t4.get(
                "sample_annotation", instance.first_annotation_token
            )
            current_first_sample: Sample = self._t4.get("sample", first_ann.sample_token)
            if first_sample is None or current_first_sample.timestamp < first_sample.timestamp:
                first_sample = current_first_sample

            last_ann: SampleAnnotation = self._t4.get(
                "sample_annotation", instance.last_annotation_token
            )
            current_last_sample: Sample = self._t4.get("sample", last_ann.sample_token)
            if last_sample is None or current_last_sample.timestamp > last_sample.timestamp:
                last_sample = current_last_sample

        scene_token = first_sample.scene_token
        max_timestamp_us = last_sample.timestamp

        # search first sample data tokens
        first_lidar_tokens: list[str] = []
        first_radar_tokens: list[str] = []
        first_camera_tokens: list[str] = []
        for sensor in self._t4.sensor:
            sd_token = sensor.first_sd_token
            if sensor.modality == SensorModality.LIDAR:
                first_lidar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.RADAR:
                first_radar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.CAMERA:
                first_camera_tokens.append(sd_token)

        render3d = len(first_lidar_tokens) > 0 or len(first_radar_tokens) > 0
        render2d = len(first_camera_tokens) > 0

        app_id = f"instance@{scene_token}"
        viewer = self._init_viewer(
            app_id,
            render3d=render3d,
            render2d=render2d,
            render_ann=True,
            save_dir=save_dir,
        )

        gather = await asyncio.gather(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_radars(
                viewer=viewer,
                first_radar_tokens=first_radar_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_cameras(
                viewer=viewer,
                first_camera_tokens=first_camera_tokens,
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_annotation3ds(
                viewer=viewer,
                first_sample_token=first_sample.token,
                max_timestamp_us=max_timestamp_us,
                future_seconds=future_seconds,
                instance_tokens=instance_tokens,
            ),
            self._render_annotation2ds(
                viewer=viewer,
                first_sample_token=first_sample.token,
                max_timestamp_us=max_timestamp_us,
                instance_tokens=instance_tokens,
            ),
        )

        return gather

    async def async_render_pointcloud(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        ignore_distortion: bool = True,
        save_dir: str | None = None,
    ) -> Future:
        """Render pointcloud on 3D and 2D view.

        Args:
            scene_token (str): Scene token.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        Returns:
            Future aggregating results.

        TODO:
            Add an option of rendering radar channels.
        """
        # initialize viewer
        app_id = f"pointcloud@{scene_token}"
        viewer = self._init_viewer(app_id, render_ann=False, save_dir=save_dir)

        # search first lidar sample data token
        first_lidar_token: str | None = None
        for sensor in self._t4.sensor:
            if sensor.modality != SensorModality.LIDAR:
                continue
            first_lidar_token = sensor.first_sd_token

        if first_lidar_token is None:
            raise ValueError("There is no 3D pointcloud data.")

        first_lidar_sample_data: Sample = self._t4.get("sample_data", first_lidar_token)
        max_timestamp_us = first_lidar_sample_data.timestamp + sec2us(max_time_seconds)

        gather = await asyncio.gather(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=[first_lidar_token],
                max_timestamp_us=max_timestamp_us,
            ),
            self._render_points_on_cameras(
                first_point_sample_data_token=first_lidar_token,
                max_timestamp_us=max_timestamp_us,
                min_dist=1.0,
                ignore_distortion=ignore_distortion,
            ),
        )

        return gather

    def _init_viewer(
        self,
        app_id: str,
        *,
        render3d: bool = True,
        render2d: bool = True,
        render_ann: bool = True,
        save_dir: str | None = None,
    ) -> RerunViewer:
        if not (render3d or render2d):
            raise ValueError("At least one of `render3d` or `render2d` must be True.")

        cameras = (
            [
                sensor.channel
                for sensor in self._t4.sensor
                if sensor.modality == SensorModality.CAMERA
            ]
            if render2d
            else None
        )

        viewer = RerunViewer(
            app_id=app_id,
            cameras=cameras,
            with_3d=render3d,
            save_dir=save_dir,
        )

        if render_ann:
            viewer = viewer.with_labels(self._label2id)

        global_map_filepath = osp.join(self._t4.data_root, "map/global_map_center.pcd.yaml")
        if osp.exists(global_map_filepath):
            with open(global_map_filepath) as f:
                map_metadata: dict = yaml.safe_load(f)
            map_origin: dict = map_metadata["/**"]["ros__parameters"]["map_origin"]
            latitude = map_origin["latitude"]
            longitude = map_origin["longitude"]
            viewer = viewer.with_global_origin((latitude, longitude))

        return viewer

    def _render_sensor_calibration(self, viewer: RerunViewer, sample_data_token: str) -> None:
        sample_data: SampleData = self._t4.get("sample_data", sample_data_token)
        calibration: CalibratedSensor = self._t4.get(
            "calibrated_sensor", sample_data.calibrated_sensor_token
        )
        sensor: Sensor = self._t4.get("sensor", calibration.sensor_token)
        viewer.render_calibration(sensor=sensor, calibration=calibration)

    async def _render_lidar_and_ego(
        self,
        viewer: RerunViewer,
        first_lidar_tokens: list[str],
        max_timestamp_us: float,
    ) -> Future:
        async def render_lidar(
            viewer: RerunViewer,
            first_lidar_token: str,
            max_timestamp_us: float,
        ) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_lidar_token)

            current_lidar_token = first_lidar_token
            while current_lidar_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_lidar_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                ego_pose: EgoPose = self._t4.get("ego_pose", sample_data.ego_pose_token)
                viewer.render_ego(ego_pose=ego_pose)

                pointcloud = LidarPointCloud.from_file(
                    osp.join(self._t4.data_root, sample_data.filename)
                )
                viewer.render_pointcloud(
                    seconds=us2sec(sample_data.timestamp),
                    channel=sample_data.channel,
                    pointcloud=pointcloud,
                )

                current_lidar_token = sample_data.next

        return await asyncio.gather(
            *[
                render_lidar(
                    viewer=viewer,
                    first_lidar_token=token,
                    max_timestamp_us=max_timestamp_us,
                )
                for token in first_lidar_tokens
            ]
        )

    async def _render_radars(
        self,
        viewer: RerunViewer,
        first_radar_tokens: list[str],
        max_timestamp_us: float,
    ) -> Future:
        async def render_radar(
            viewer: RerunViewer,
            first_radar_token: str,
            max_timestamp_us: float,
        ) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_radar_token)

            current_radar_token = first_radar_token
            while current_radar_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_radar_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                pointcloud = RadarPointCloud.from_file(
                    osp.join(self._t4.data_root, sample_data.filename)
                )
                viewer.render_pointcloud(
                    seconds=us2sec(sample_data.timestamp),
                    channel=sample_data.channel,
                    pointcloud=pointcloud,
                )

                current_radar_token = sample_data.next

        return await asyncio.gather(
            *[
                render_radar(
                    viewer=viewer,
                    first_radar_token=token,
                    max_timestamp_us=max_timestamp_us,
                )
                for token in first_radar_tokens
            ]
        )

    async def _render_cameras(
        self,
        viewer: RerunViewer,
        first_camera_tokens: list[str],
        max_timestamp_us: float,
    ) -> Future:
        async def render_camera(
            viewer: RerunViewer,
            first_camera_token: str,
            max_timestamp_us: float,
        ) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_camera_token)

            current_camera_token = first_camera_token
            while current_camera_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_camera_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                viewer.render_image(
                    seconds=us2sec(sample_data.timestamp),
                    camera=sample_data.channel,
                    image=osp.join(self._t4.data_root, sample_data.filename),
                )

                current_camera_token = sample_data.next

        return await asyncio.gather(
            *[
                render_camera(
                    viewer=viewer,
                    first_camera_token=token,
                    max_timestamp_us=max_timestamp_us,
                )
                for token in first_camera_tokens
            ]
        )

    async def _render_points_on_cameras(
        self,
        first_point_sample_data_token: str,
        max_timestamp_us: float,
        *,
        min_dist: float = 1.0,
        ignore_distortion: bool = True,
    ) -> Future:
        async def render_points_on_camera(
            first_point_sample_data_token: str,
            camera: str,
            *,
            min_dist: float = 1.0,
            ignore_distortion: bool = True,
        ) -> None:
            current_point_sample_data_token = first_point_sample_data_token
            while current_point_sample_data_token != "":
                sample_data: SampleData = self._t4.get(
                    "sample_data", current_point_sample_data_token
                )
                sample: Sample = self._t4.get("sample", sample_data.sample_token)

                if camera not in sample.data:
                    current_point_sample_data_token = sample_data.next
                    continue

                camera_sample_data_token = sample.data[camera]

                if max_timestamp_us < sample.timestamp:
                    break

                points_on_image, depths, image = self._t4.project_pointcloud(
                    point_sample_data_token=current_point_sample_data_token,
                    camera_sample_data_token=camera_sample_data_token,
                    min_dist=min_dist,
                    ignore_distortion=ignore_distortion,
                )

                rr.set_time_seconds(RerunViewer.timeline, us2sec(sample.timestamp))

                rr.log(format_entity(RerunViewer.ego_entity, camera), rr.Image(image))
                rr.log(
                    format_entity(RerunViewer.ego_entity, camera, "pointcloud"),
                    rr.Points2D(positions=points_on_image.T, colors=distance_color(depths)),
                )

                current_point_sample_data_token = sample_data.next

        return await asyncio.gather(
            *[
                render_points_on_camera(
                    first_point_sample_data_token=first_point_sample_data_token,
                    camera=sensor.channel,
                    min_dist=min_dist,
                    ignore_distortion=ignore_distortion,
                )
                for sensor in self._t4.sensor
                if sensor.modality == SensorModality.CAMERA
            ]
        )

    async def _render_annotation3ds(
        self,
        viewer: RerunViewer,
        first_sample_token: str,
        max_timestamp_us: float,
        *,
        future_seconds: float = 0.0,
        instance_tokens: Sequence[str] | None = None,
    ) -> None:
        current_sample_token = first_sample_token
        while current_sample_token != "":
            sample: Sample = self._t4.get("sample", current_sample_token)

            if max_timestamp_us < sample.timestamp:
                break

            if instance_tokens is not None:
                boxes = []
                for ann_token in sample.ann_3ds:
                    ann: SampleAnnotation = self._t4.get("sample_annotation", ann_token)
                    if ann.instance_token in instance_tokens:
                        boxes.append(self._t4.get_box3d(ann_token, future_seconds=future_seconds))
            else:
                boxes = [
                    self._t4.get_box3d(token, future_seconds=future_seconds)
                    for token in sample.ann_3ds
                ]
            viewer.render_box3ds(us2sec(sample.timestamp), boxes)

            current_sample_token = sample.next

    async def _render_annotation2ds(
        self,
        viewer: RerunViewer,
        first_sample_token: str,
        max_timestamp_us: float,
        *,
        instance_tokens: Sequence[str] | None = None,
    ) -> None:
        current_sample_token = first_sample_token
        while current_sample_token != "":
            sample: Sample = self._t4.get("sample", current_sample_token)

            if max_timestamp_us < sample.timestamp:
                break

            boxes = []
            # For segmentation masks
            # TODO: declare specific class for segmentation mask in `dataclass`
            camera_masks: dict[str, dict[str, list]] = {}

            # Object Annotation
            for obj_ann_token in sample.ann_2ds:
                obj_ann: ObjectAnn = self._t4.get("object_ann", obj_ann_token)
                box = self._t4.get_box2d(obj_ann_token)
                if instance_tokens is not None:
                    if obj_ann.instance_token in instance_tokens:
                        boxes.append(box)
                        sample_data: SampleData = self._t4.get(
                            "sample_data",
                            obj_ann.sample_data_token,
                        )
                        camera_masks = _append_mask(
                            camera_masks,
                            camera=sample_data.channel,
                            ann=obj_ann,
                            class_id=self._label2id[obj_ann.category_name],
                            uuid=box.uuid,
                        )
                else:
                    boxes.append(box)
                    sample_data: SampleData = self._t4.get("sample_data", obj_ann.sample_data_token)
                    camera_masks = _append_mask(
                        camera_masks,
                        camera=sample_data.channel,
                        ann=obj_ann,
                        class_id=self._label2id[obj_ann.category_name],
                        uuid=box.uuid,
                    )

            # Render 2D box
            viewer.render_box2ds(us2sec(sample.timestamp), boxes)

            if instance_tokens is None:
                # Surface Annotation
                for ann_token in sample.surface_anns:
                    surface_ann: SurfaceAnn = self._t4.get("surface_ann", ann_token)
                    sample_data: SampleData = self._t4.get(
                        "sample_data", surface_ann.sample_data_token
                    )
                    camera_masks = _append_mask(
                        camera_masks,
                        camera=sample_data.channel,
                        ann=surface_ann,
                        class_id=self._label2id[surface_ann.category_name],
                    )

            # Render 2D segmentation image
            for camera, data in camera_masks.items():
                viewer.render_segmentation2d(
                    seconds=us2sec(sample.timestamp), camera=camera, **data
                )

            # TODO: add support of rendering keypoints
            current_sample_token = sample.next


def _append_mask(
    camera_masks: dict[str, dict[str, list]],
    camera: str,
    ann: ObjectAnn | SurfaceAnn,
    class_id: int,
    uuid: str | None = None,
) -> dict[str, dict[str, list]]:
    """Append segmentation mask data from `ObjectAnn/SurfaceAnn`.

    TODO:
        This function should be removed after declaring specific dataclass for 2D segmentation.

    Args:
        camera_masks (dict[str, dict[str, list]]): Key-value data mapping camera name and mask data.
        camera (str): Name of camera channel.
        ann (ObjectAnn | SurfaceAnn): Annotation object.
        class_id (int): Class ID.
        uuid (str | None, optional): Unique instance identifier.

    Returns:
        dict[str, dict[str, list]]: Updated `camera_masks`.
    """
    if camera in camera_masks:
        camera_masks[camera]["masks"].append(ann.mask.decode())
        camera_masks[camera]["class_ids"].append(class_id)
        camera_masks[camera]["uuids"].append(uuid)
    else:
        camera_masks[camera] = {}
        camera_masks[camera]["masks"] = [ann.mask.decode()]
        camera_masks[camera]["class_ids"] = [class_id]
        camera_masks[camera]["uuids"] = [uuid]
    return camera_masks
