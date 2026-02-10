from __future__ import annotations

import concurrent
import concurrent.futures
import os.path as osp
import warnings
from concurrent.futures import Future
from enum import Enum
from typing import TYPE_CHECKING, Sequence

import numpy as np
import yaml

from t4_devkit.common.timestamp import microseconds2seconds, seconds2microseconds
from t4_devkit.dataclass import LidarPointCloud, RadarPointCloud, SegmentationPointCloud
from t4_devkit.schema import SensorModality
from t4_devkit.viewer import (
    EntityPath,
    PointCloudColorMode,
    RerunViewer,
    ViewerBuilder,
    format_entity,
)

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


class RenderingMode(Enum):
    SCENE = "scene"
    INSTANCE = "instance"
    POINTCLOUD = "pointcloud"


class RenderingHelper:
    """Help `Tier4` class with rendering tasks."""

    def __init__(self, t4: Tier4) -> None:
        """Construct a new object.

        Args:
            t4 (Tier4): `Tier4` instance.
        """
        self._t4 = t4
        self._label2id: dict[str, int] = {
            category.name: category.index for category in self._t4.category
        }
        self._sample_data_to_lidarseg_filename: dict[str, str] = {
            lidarseg.sample_data_token: lidarseg.filename for lidarseg in self._t4.lidarseg
        }

        self._executor = concurrent.futures.ThreadPoolExecutor()

    def _has_lidarseg(self) -> bool:
        return bool(self._sample_data_to_lidarseg_filename)

    def _find_lidarseg_file(self, sample_data_token: str) -> str | None:
        return self._sample_data_to_lidarseg_filename.get(sample_data_token)

    def _init_viewer(
        self,
        app_id: str,
        *,
        contents: list[str] | None = None,
        render_ann: bool = True,
        save_dir: str | None = None,
    ) -> RerunViewer:
        """Initialize viewer instance.

        Args:
            app_id (str): Viewer application ID.
            contents (list[str] | None, optional): List of contents to project 3D objects onto 2D spaces.
            render_ann (bool, optional): Indicates whether to render annotations.
            save_dir (str | None, optional): Directory path to save the rendering record.
        """
        cameras = [
            sensor.channel for sensor in self._t4.sensor if sensor.modality == SensorModality.CAMERA
        ]

        builder = (
            ViewerBuilder().with_spatial3d().with_spatial2d(cameras=cameras, contents=contents)
        )

        if render_ann:
            builder = builder.with_labels(self._label2id)

        global_map_filepath = osp.join(self._t4.data_root, "map/global_map_center.pcd.yaml")
        if osp.exists(global_map_filepath):
            with open(global_map_filepath) as f:
                map_metadata: dict = yaml.safe_load(f)
            map_origin: dict = map_metadata["/**"]["ros__parameters"]["map_origin"]
            latitude, longitude = map_origin["latitude"], map_origin["longitude"]
            builder = builder.with_streetmap((latitude, longitude))
        elif osp.exists(osp.join(self._t4.map_dir, "lanelet2_map.osm")):
            builder = builder.with_streetmap()

        return builder.build(app_id, save_dir=save_dir)

    def _load_contents(self, mode: RenderingMode, entity_child: str = "") -> list[str] | None:
        """Load contents to project 3D objects onto 2D spaces.

        Args:
            mode (RenderingMode): RenderingMode enum.
            entity_child (str, optional): Child entity path.

        Returns:
            list[str] | None: List of entity paths to be used as 2D projection contents.
                Returns `None` to indicate that no 3D entities should be projected onto
                2D spaces (e.g., when 2D annotations are available).
        """
        match mode:
            case RenderingMode.SCENE | RenderingMode.INSTANCE:
                # project 3D boxes/velocities/futures on image if there is no 2D annotation
                entity_root = format_entity(EntityPath.MAP, entity_child)
                if len(self._t4.object_ann) == 0 and len(self._t4.surface_ann) == 0:
                    contents = [
                        format_entity(entity_root, "box"),
                        format_entity(entity_root, "velocity"),
                        format_entity(entity_root, "future"),
                    ]
                else:
                    contents = None
            case RenderingMode.POINTCLOUD:
                contents = [format_entity(EntityPath.BASE_LINK, entity_child)]

        return contents

    def render_scene(
        self,
        *,
        max_time_seconds: float = np.inf,
        future_seconds: float = 0.0,
        save_dir: str | None = None,
    ) -> None:
        """Render specified scene.

        Args:
            max_time_seconds (float, optional): Max time length to be rendered [s].
            future_seconds (float, optional): Future time in [s].
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.
        """
        # search first sample data tokens
        first_lidar_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.LIDAR
        ]
        first_radar_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.RADAR
        ]
        first_camera_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.CAMERA
        ]

        app_id = f"scene@{self._t4.dataset_id}"
        contents = self._load_contents(RenderingMode.SCENE)
        viewer = self._init_viewer(app_id, contents=contents, render_ann=True, save_dir=save_dir)

        self._try_render_map(viewer)

        scene: Scene = self._t4.scene[0]
        first_sample: Sample = self._t4.get("sample", scene.first_sample_token)
        max_timestamp_us = first_sample.timestamp + seconds2microseconds(max_time_seconds)

        pointcloud_color_mode = (
            PointCloudColorMode.SEGMENTATION
            if self._has_lidarseg()
            else PointCloudColorMode.DISTANCE
        )

        futures = (
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
                color_mode=pointcloud_color_mode,
            )
            + self._render_radars(
                viewer=viewer,
                first_radar_tokens=first_radar_tokens,
                max_timestamp_us=max_timestamp_us,
            )
            + self._render_cameras(
                viewer=viewer,
                first_camera_tokens=first_camera_tokens,
                max_timestamp_us=max_timestamp_us,
            )
            + [
                self._executor.submit(
                    self._render_annotation3ds,
                    viewer=viewer,
                    first_sample_token=scene.first_sample_token,
                    max_timestamp_us=max_timestamp_us,
                    future_seconds=future_seconds,
                ),
                self._executor.submit(
                    self._render_annotation2ds,
                    viewer=viewer,
                    first_sample_token=scene.first_sample_token,
                    max_timestamp_us=max_timestamp_us,
                ),
            ]
        )

        _handle_futures(futures)

    def render_instance(
        self,
        instance_token: str | Sequence[str],
        *,
        future_seconds: float = 0.0,
        save_dir: str | None = None,
    ) -> None:
        """Render particular instance.

        Args:
            instance_token (str | Sequence[str]): Instance token(s).
            future_seconds (float, optional): Future time in [s].
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

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

        if first_sample is None or last_sample is None:
            warnings.warn(
                f"There is no sample for the corresponding instance(s): {instance_tokens}",
                stacklevel=2,
            )
            return

        max_timestamp_us = last_sample.timestamp

        # search first sample data tokens
        first_lidar_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.LIDAR
        ]
        first_radar_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.RADAR
        ]
        first_camera_tokens: list[str] = [
            sensor.first_sd_token
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.CAMERA
        ]

        app_id = f"instance@{self._t4.dataset_id}"
        contents = self._load_contents(RenderingMode.INSTANCE)
        viewer = self._init_viewer(app_id, contents=contents, render_ann=True, save_dir=save_dir)

        self._try_render_map(viewer)

        pointcloud_color_mode = (
            PointCloudColorMode.SEGMENTATION
            if self._has_lidarseg()
            else PointCloudColorMode.DISTANCE
        )

        futures = (
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
                color_mode=pointcloud_color_mode,
            )
            + self._render_radars(
                viewer=viewer,
                first_radar_tokens=first_radar_tokens,
                max_timestamp_us=max_timestamp_us,
            )
            + self._render_cameras(
                viewer=viewer,
                first_camera_tokens=first_camera_tokens,
                max_timestamp_us=max_timestamp_us,
            )
            + [
                self._executor.submit(
                    self._render_annotation3ds,
                    viewer=viewer,
                    first_sample_token=first_sample.token,
                    max_timestamp_us=max_timestamp_us,
                    future_seconds=future_seconds,
                    instance_tokens=instance_tokens,
                ),
                self._executor.submit(
                    self._render_annotation2ds,
                    viewer=viewer,
                    first_sample_token=first_sample.token,
                    max_timestamp_us=max_timestamp_us,
                    instance_tokens=instance_tokens,
                ),
            ]
        )

        _handle_futures(futures)

    def render_pointcloud(
        self,
        *,
        max_time_seconds: float = np.inf,
        save_dir: str | None = None,
    ) -> None:
        """Render pointcloud on 3D and 2D view.

        Args:
            max_time_seconds (float, optional): Max time length to be rendered [s].
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        TODO:
            Add an option of rendering radar channels.
        """
        # search first lidar sample data token
        first_lidar_token: str | None = None
        first_camera_tokens: list[str] = []
        for sensor in self._t4.sensor:
            if sensor.modality == SensorModality.LIDAR:
                first_lidar_token = sensor.first_sd_token
            elif sensor.modality == SensorModality.CAMERA:
                first_camera_tokens.append(sensor.first_sd_token)

        if first_lidar_token is None:
            raise ValueError("There is no 3D pointcloud data.")

        first_lidar_sample_data: SampleData = self._t4.get("sample_data", first_lidar_token)
        max_timestamp_us = first_lidar_sample_data.timestamp + seconds2microseconds(
            max_time_seconds
        )

        app_id = f"pointcloud@{self._t4.dataset_id}"
        contents = self._load_contents(
            RenderingMode.POINTCLOUD,
            entity_child=first_lidar_sample_data.channel,
        )
        viewer = self._init_viewer(app_id, contents=contents, render_ann=False, save_dir=save_dir)

        self._try_render_map(viewer)

        # TODO: support rendering segmentation pointcloud on camera
        futures = self._render_lidar_and_ego(
            viewer=viewer,
            first_lidar_tokens=[first_lidar_token],
            max_timestamp_us=max_timestamp_us,
        ) + self._render_cameras(
            viewer=viewer,
            first_camera_tokens=first_camera_tokens,
            max_timestamp_us=max_timestamp_us,
        )

        _handle_futures(futures)

    def _try_render_map(self, viewer: RerunViewer) -> None:
        lanelet_path = osp.join(self._t4.map_dir, "lanelet2_map.osm")
        if not osp.exists(lanelet_path):
            return
        viewer.render_map(lanelet_path)

    def _render_sensor_calibration(self, viewer: RerunViewer, sample_data_token: str) -> None:
        sample_data: SampleData = self._t4.get("sample_data", sample_data_token)
        calibration: CalibratedSensor = self._t4.get(
            "calibrated_sensor", sample_data.calibrated_sensor_token
        )
        sensor: Sensor = self._t4.get("sensor", calibration.sensor_token)
        resolution = (
            (sample_data.width, sample_data.height)
            if sensor.modality == SensorModality.CAMERA
            else None
        )
        viewer.render_calibration(sensor=sensor, calibration=calibration, resolution=resolution)

    def _render_lidar_and_ego(
        self,
        viewer: RerunViewer,
        first_lidar_tokens: list[str],
        max_timestamp_us: float,
        *,
        color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
    ) -> list[Future]:
        def _render_single_lidar(first_lidar_token: str) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_lidar_token)

            current_lidar_token = first_lidar_token
            while current_lidar_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_lidar_token)
                current_lidar_token = sample_data.next

                if max_timestamp_us < sample_data.timestamp:
                    break

                ego_pose: EgoPose = self._t4.get("ego_pose", sample_data.ego_pose_token)
                viewer.render_ego(ego_pose=ego_pose)

                # render segmentation pointcloud if available, otherwise render raw pointcloud
                if color_mode == PointCloudColorMode.SEGMENTATION:
                    label_filename = self._find_lidarseg_file(sample_data.token)
                    if label_filename is None:
                        continue

                    pointcloud = SegmentationPointCloud.from_file(
                        point_filepath=osp.join(self._t4.data_root, sample_data.filename),
                        label_filepath=osp.join(self._t4.data_root, label_filename),
                    )
                else:
                    pointcloud = LidarPointCloud.from_file(
                        osp.join(self._t4.data_root, sample_data.filename)
                    )

                viewer.render_pointcloud(
                    seconds=microseconds2seconds(sample_data.timestamp),
                    channel=sample_data.channel,
                    pointcloud=pointcloud,
                    color_mode=color_mode,
                )

        return [self._executor.submit(_render_single_lidar, token) for token in first_lidar_tokens]

    def _render_radars(
        self,
        viewer: RerunViewer,
        first_radar_tokens: list[str],
        max_timestamp_us: float,
    ) -> list[Future]:
        def _render_single_radar(first_radar_token: str) -> None:
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
                    seconds=microseconds2seconds(sample_data.timestamp),
                    channel=sample_data.channel,
                    pointcloud=pointcloud,
                )

                current_radar_token = sample_data.next

        return [self._executor.submit(_render_single_radar, token) for token in first_radar_tokens]

    def _render_cameras(
        self,
        viewer: RerunViewer,
        first_camera_tokens: list[str],
        max_timestamp_us: float,
    ) -> list[Future]:
        def _render_single_camera(first_camera_token: str) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_camera_token)

            current_camera_token = first_camera_token
            while current_camera_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_camera_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                viewer.render_image(
                    seconds=microseconds2seconds(sample_data.timestamp),
                    camera=sample_data.channel,
                    image=osp.join(self._t4.data_root, sample_data.filename),
                )

                current_camera_token = sample_data.next

        return [
            self._executor.submit(_render_single_camera, token) for token in first_camera_tokens
        ]

    def _render_annotation3ds(
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
            viewer.render_box3ds(microseconds2seconds(sample.timestamp), boxes)

            current_sample_token = sample.next

    def _render_annotation2ds(
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
                    if obj_ann.instance_token not in instance_tokens:
                        continue
                    boxes.append(box)
                    sample_data: SampleData = self._t4.get("sample_data", obj_ann.sample_data_token)
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
            viewer.render_box2ds(microseconds2seconds(sample.timestamp), boxes)

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
                    seconds=microseconds2seconds(sample.timestamp), camera=camera, **data
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
    if ann.mask is None:
        return camera_masks

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


def _handle_futures(futures: list[Future]) -> None:
    """Wait for all futures and raise exception if any.

    Args:
        futures (list[Future]): List of futures.
    """
    if not futures:
        return

    concurrent.futures.wait(futures)
    for future in futures:
        if not future.done():
            continue
        future.result()
