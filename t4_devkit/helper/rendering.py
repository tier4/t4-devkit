from __future__ import annotations

import concurrent
import concurrent.futures
import os.path as osp
from concurrent.futures import Future
from typing import TYPE_CHECKING, Sequence

import numpy as np
import rerun as rr
import yaml
from PIL import Image

from t4_devkit.common.geometry import view_points
from t4_devkit.common.timestamp import microseconds2seconds, seconds2microseconds
from t4_devkit.dataclass import LidarPointCloud, RadarPointCloud, SegmentationPointCloud
from t4_devkit.schema import SensorModality
from t4_devkit.viewer import (
    PointCloudColorMode,
    RerunViewer,
    ViewerBuilder,
    ViewerConfig,
    format_entity,
    pointcloud_color,
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
    from t4_devkit.typing import NDArrayF64, NDArrayU8

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
        self._sample_data_to_lidarseg_filename: dict[str, str] | None = (
            {lidarseg.sample_data_token: lidarseg.filename for lidarseg in self._t4.lidarseg}
            if self._t4.lidarseg
            else None
        )

        self._executor = concurrent.futures.ThreadPoolExecutor()

    def _init_viewer(
        self,
        app_id: str,
        *,
        render_ann: bool = True,
        save_dir: str | None = None,
    ) -> RerunViewer:
        cameras = [
            sensor.channel for sensor in self._t4.sensor if sensor.modality == SensorModality.CAMERA
        ]

        builder = ViewerBuilder().with_spatial3d().with_spatial2d(cameras=cameras)

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
        viewer = self._init_viewer(app_id, render_ann=True, save_dir=save_dir)

        # self._render_map(viewer)

        scene: Scene = self._t4.scene[0]
        first_sample: Sample = self._t4.get("sample", scene.first_sample_token)
        max_timestamp_us = first_sample.timestamp + seconds2microseconds(max_time_seconds)

        concurrent.futures.wait(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
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
                    self._render_annotation3ds(
                        viewer=viewer,
                        first_sample_token=scene.first_sample_token,
                        max_timestamp_us=max_timestamp_us,
                        future_seconds=future_seconds,
                    )
                ),
                self._executor.submit(
                    self._render_annotation2ds(
                        viewer=viewer,
                        first_sample_token=scene.first_sample_token,
                        max_timestamp_us=max_timestamp_us,
                    )
                ),
            ]
        )

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
        viewer = self._init_viewer(app_id, render_ann=True, save_dir=save_dir)

        self._render_map(viewer)

        concurrent.futures.wait(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=first_lidar_tokens,
                max_timestamp_us=max_timestamp_us,
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
                    self._render_annotation3ds(
                        viewer=viewer,
                        first_sample_token=first_sample.token,
                        max_timestamp_us=max_timestamp_us,
                        future_seconds=future_seconds,
                        instance_tokens=instance_tokens,
                    )
                ),
                self._executor.submit(
                    self._render_annotation2ds(
                        viewer=viewer,
                        first_sample_token=first_sample.token,
                        max_timestamp_us=max_timestamp_us,
                        instance_tokens=instance_tokens,
                    )
                ),
            ],
        )

    def render_pointcloud(
        self,
        *,
        max_time_seconds: float = np.inf,
        ignore_distortion: bool = True,
        save_dir: str | None = None,
    ) -> None:
        """Render pointcloud on 3D and 2D view.

        Args:
            max_time_seconds (float, optional): Max time length to be rendered [s].
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.
            save_dir (str | None, optional): Directory path to save the recording.
                Viewer will be spawned if it is None, otherwise not.

        TODO:
            Add an option of rendering radar channels.
        """
        # initialize viewer
        app_id = f"pointcloud@{self._t4.dataset_id}"
        viewer = self._init_viewer(app_id, render_ann=False, save_dir=save_dir)

        self._render_map(viewer)

        # search first lidar sample data token
        first_lidar_token: str | None = None
        for sensor in self._t4.sensor:
            if sensor.modality != SensorModality.LIDAR:
                continue
            first_lidar_token = sensor.first_sd_token

        if first_lidar_token is None:
            raise ValueError("There is no 3D pointcloud data.")

        first_lidar_sample_data: Sample = self._t4.get("sample_data", first_lidar_token)
        max_timestamp_us = first_lidar_sample_data.timestamp + seconds2microseconds(
            max_time_seconds
        )

        concurrent.futures.wait(
            self._render_lidar_and_ego(
                viewer=viewer,
                first_lidar_tokens=[first_lidar_token],
                max_timestamp_us=max_timestamp_us,
            )
            + self._render_points_on_cameras(
                first_point_sample_data_token=first_lidar_token,
                max_timestamp_us=max_timestamp_us,
                min_dist=1.0,
                ignore_distortion=ignore_distortion,
            ),
        )

    def _render_map(self, viewer: RerunViewer) -> None:
        lanelet_path = osp.join(self._t4.map_dir, "lanelet2_map.osm")
        viewer.render_map(lanelet_path)

    def _render_sensor_calibration(self, viewer: RerunViewer, sample_data_token: str) -> None:
        sample_data: SampleData = self._t4.get("sample_data", sample_data_token)
        calibration: CalibratedSensor = self._t4.get(
            "calibrated_sensor", sample_data.calibrated_sensor_token
        )
        sensor: Sensor = self._t4.get("sensor", calibration.sensor_token)
        if sensor.modality == SensorModality.CAMERA:
            viewer.render_calibration(
                sensor=sensor,
                calibration=calibration,
                resolution=(sample_data.width, sample_data.height),
            )
        else:
            viewer.render_calibration(sensor=sensor, calibration=calibration)

    def _render_lidar_and_ego(
        self,
        viewer: RerunViewer,
        first_lidar_tokens: list[str],
        max_timestamp_us: float,
        color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
    ) -> list[Future]:
        def _render_single_lidar(first_lidar_token: str) -> None:
            self._render_sensor_calibration(viewer=viewer, sample_data_token=first_lidar_token)

            current_lidar_token = first_lidar_token
            while current_lidar_token != "":
                sample_data: SampleData = self._t4.get("sample_data", current_lidar_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                ego_pose: EgoPose = self._t4.get("ego_pose", sample_data.ego_pose_token)
                viewer.render_ego(ego_pose=ego_pose)

                # render segmentation pointcloud if available, otherwise render raw pointcloud
                if (
                    self._sample_data_to_lidarseg_filename
                    and sample_data.token in self._sample_data_to_lidarseg_filename
                ):
                    label_filename = self._sample_data_to_lidarseg_filename[sample_data.token]
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

                current_lidar_token = sample_data.next

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

    def _render_points_on_cameras(
        self,
        first_point_sample_data_token: str,
        max_timestamp_us: float,
        *,
        min_dist: float = 1.0,
        ignore_distortion: bool = True,
        color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
    ) -> list[Future]:
        def _render_points_on_single_camera(camera: str) -> None:
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

                points_on_image, colors, image = self._project_pointcloud(
                    point_sample_data_token=current_point_sample_data_token,
                    camera_sample_data_token=camera_sample_data_token,
                    min_dist=min_dist,
                    ignore_distortion=ignore_distortion,
                    color_mode=color_mode,
                )

                rr.set_time_seconds(ViewerConfig.timeline, microseconds2seconds(sample.timestamp))

                rr.log(format_entity(ViewerConfig.ego_entity, camera), rr.Image(image))
                rr.log(
                    format_entity(ViewerConfig.ego_entity, camera, "pointcloud"),
                    rr.Points2D(positions=points_on_image.T, colors=colors),
                )

                current_point_sample_data_token = sample_data.next

        return [
            self._executor.submit(_render_points_on_single_camera, sensor.channel)
            for sensor in self._t4.sensor
            if sensor.modality == SensorModality.CAMERA
        ]

    def _project_pointcloud(
        self,
        point_sample_data_token: str,
        camera_sample_data_token: str,
        min_dist: float = 1.0,
        *,
        ignore_distortion: bool = True,
        color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
    ) -> tuple[NDArrayF64, NDArrayF64, NDArrayU8]:
        """Project pointcloud on image plane.

        Args:
            point_sample_data_token (str): Sample data token of lidar or radar sensor.
            camera_sample_data_token (str): Sample data token of camera.
            min_dist (float, optional): Distance from the camera below which points are discarded.
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.
            color_mode (PointCloudColorMode, optional): Color mode for pointcloud.

        Returns:
            Projected points [2, n], their color values [n, 3], and an image.
        """
        point_sample_data: SampleData = self._t4.get("sample_data", point_sample_data_token)
        pc_filepath = osp.join(self._t4.data_root, point_sample_data.filename)
        if point_sample_data.modality == SensorModality.LIDAR:
            pointcloud = LidarPointCloud.from_file(pc_filepath)
        elif point_sample_data.modality == SensorModality.RADAR:
            pointcloud = RadarPointCloud.from_file(pc_filepath)
        else:
            raise ValueError(f"Expected sensor lidar/radar, but got {point_sample_data.modality}")

        camera_sample_data: SampleData = self._t4.get("sample_data", camera_sample_data_token)
        if camera_sample_data.modality != SensorModality.CAMERA:
            f"Expected camera, but got {camera_sample_data.modality}"

        img = Image.open(osp.join(self._t4.data_root, camera_sample_data.filename))

        # 1. transform the pointcloud to the ego vehicle frame for the timestamp to the sweep.
        point_cs_record: CalibratedSensor = self._t4.get(
            "calibrated_sensor", point_sample_data.calibrated_sensor_token
        )
        pointcloud.rotate(point_cs_record.rotation.rotation_matrix)
        pointcloud.translate(point_cs_record.translation)

        # 2. transform from ego to the global frame.
        point_ego_pose: EgoPose = self._t4.get("ego_pose", point_sample_data.ego_pose_token)
        pointcloud.rotate(point_ego_pose.rotation.rotation_matrix)
        pointcloud.translate(point_ego_pose.translation)

        # 3. transform from global into the ego vehicle frame for the timestamp of the image
        camera_ego_pose: EgoPose = self._t4.get("ego_pose", camera_sample_data.ego_pose_token)
        pointcloud.translate(-camera_ego_pose.translation)
        pointcloud.rotate(camera_ego_pose.rotation.rotation_matrix.T)

        # 4. transform from ego into the camera
        camera_cs_record: CalibratedSensor = self._t4.get(
            "calibrated_sensor", camera_sample_data.calibrated_sensor_token
        )
        pointcloud.translate(-camera_cs_record.translation)
        pointcloud.rotate(camera_cs_record.rotation.rotation_matrix.T)

        distortion = None if ignore_distortion else camera_cs_record.camera_distortion

        points_on_img = view_points(
            points=pointcloud.points[:3, :],
            intrinsic=camera_cs_record.camera_intrinsic,
            distortion=distortion,
            normalize=True,
        )[:2]

        colors = pointcloud_color(pointcloud, color_mode)
        depths = pointcloud.points[2, :]

        mask = np.ones(colors.shape[0], dtype=bool)
        mask = np.logical_and(mask, depths > min_dist)  # mask by depths
        # mask by size of points on image
        mask = np.logical_and(mask, 1 < points_on_img[0])
        mask = np.logical_and(mask, points_on_img[0] < img.size[0] - 1)
        mask = np.logical_and(mask, 1 < points_on_img[1])
        mask = np.logical_and(mask, points_on_img[1] < img.size[1] - 1)
        points_on_img = points_on_img[:, mask]
        colors = colors[mask]

        return points_on_img, colors, np.array(img, dtype=np.uint8)

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
