from __future__ import annotations

import os.path as osp
import time
import warnings
from typing import TYPE_CHECKING

import numpy as np
import rerun as rr
import yaml
from PIL import Image
from pyquaternion import Quaternion

from t4_devkit.common.geometry import is_box_in_image, view_points
from t4_devkit.common.timestamp import sec2us, us2sec
from t4_devkit.dataclass import (
    Box2D,
    Box3D,
    LidarPointCloud,
    RadarPointCloud,
    SemanticLabel,
    Shape,
    ShapeType,
)
from t4_devkit.schema import SchemaName, SensorModality, VisibilityLevel, build_schema
from t4_devkit.viewer import RerunViewer, distance_color, format_entity

if TYPE_CHECKING:
    from t4_devkit.typing import CamIntrinsicType, NDArrayF64, NDArrayU8, VelocityType

    from .dataclass import BoxType
    from .schema import (
        Attribute,
        CalibratedSensor,
        Category,
        EgoPose,
        Instance,
        Keypoint,
        Log,
        Map,
        ObjectAnn,
        Sample,
        SampleAnnotation,
        SampleData,
        Scene,
        SchemaTable,
        Sensor,
        SurfaceAnn,
        VehicleState,
        Visibility,
    )

__all__ = ("Tier4",)


class Tier4:
    """Database class for T4 dataset to help query and retrieve information from the database."""

    def __init__(self, version: str, data_root: str, verbose: bool = True) -> None:
        """Load database and creates reverse indexes and shortcuts.

        Args:
            version (str): Directory name of database json files.
            data_root (str): Path to the root directory of dataset.
            verbose (bool, optional): Whether to display status during load.

        Examples:
            >>> from t4_devkit import Tier4
            >>> t4 = Tier4("annotation", "data/tier4")
            ======
            Loading T4 tables in `annotation`...
            Reverse indexing...
            Done reverse indexing in 0.010 seconds.
            ======
            21 category
            8 attribute
            4 visibility
            31 instance
            7 sensor
            7 calibrated_sensor
            2529 ego_pose
            1 log
            1 scene
            88 sample
            2529 sample_data
            1919 sample_annotation
            0 object_ann
            0 surface_ann
            0 keypoint
            1 map
            Done loading in 0.046 seconds.
            ======

        """
        self.version = version
        self.data_root = data_root
        self.verbose = verbose

        if not osp.exists(self.data_root):
            raise FileNotFoundError(f"Database directory is not found: {self.data_root}")

        start_time = time.time()
        if verbose:
            print(f"======\nLoading T4 tables in `{self.version}`...")

        # assign tables explicitly
        self.attribute: list[Attribute] = self.__load_table__(SchemaName.ATTRIBUTE)
        self.calibrated_sensor: list[CalibratedSensor] = self.__load_table__(
            SchemaName.CALIBRATED_SENSOR
        )
        self.category: list[Category] = self.__load_table__(SchemaName.CATEGORY)
        self.ego_pose: list[EgoPose] = self.__load_table__(SchemaName.EGO_POSE)
        self.instance: list[Instance] = self.__load_table__(SchemaName.INSTANCE)
        self.keypoint: list[Keypoint] = self.__load_table__(SchemaName.KEYPOINT)
        self.log: list[Log] = self.__load_table__(SchemaName.LOG)
        self.map: list[Map] = self.__load_table__(SchemaName.MAP)
        self.object_ann: list[ObjectAnn] = self.__load_table__(SchemaName.OBJECT_ANN)
        self.sample_annotation: list[SampleAnnotation] = self.__load_table__(
            SchemaName.SAMPLE_ANNOTATION
        )
        self.sample_data: list[SampleData] = self.__load_table__(SchemaName.SAMPLE_DATA)
        self.sample: list[Sample] = self.__load_table__(SchemaName.SAMPLE)
        self.scene: list[Scene] = self.__load_table__(SchemaName.SCENE)
        self.sensor: list[Sensor] = self.__load_table__(SchemaName.SENSOR)
        self.surface_ann: list[SurfaceAnn] = self.__load_table__(SchemaName.SURFACE_ANN)
        self.vehicle_state: list[VehicleState] = self.__load_table__(SchemaName.VEHICLE_STATE)
        self.visibility: list[Visibility] = self.__load_table__(SchemaName.VISIBILITY)

        # make reverse indexes for common lookups
        self.__make_reverse_index__(verbose)

        if verbose:
            for schema in SchemaName:
                print(f"{len(self.get_table(schema))} {schema.value}")
            elapsed_time = time.time() - start_time
            print(f"Done loading in {elapsed_time:.3f} seconds.\n======")

    def __load_table__(self, schema: SchemaName) -> list[SchemaTable]:
        """Load schema table from a json file.

        If the schema is optional and there is no corresponding json file in dataset,
        returns empty list.

        Args:
            schema (SchemaName): An enum member of `SchemaName`.

        Returns:
            Loaded table data saved in `.json`.
        """
        filepath = osp.join(self.data_root, self.version, schema.filename)
        if not osp.exists(filepath) and schema.is_optional():
            return []

        if not osp.exists(filepath):
            raise FileNotFoundError(f"{schema.value} is mandatory.")

        return build_schema(schema, filepath)

    def __make_reverse_index__(self, verbose: bool) -> None:
        """De-normalize database to create reverse indices for common cases.

        Args:
            verbose (bool): Whether to display outputs.

        Raises:
            ValueError: Expecting `map` table has `log_tokens` key.
        """
        start_time = time.time()
        if verbose:
            print("Reverse indexing...")

        token2idx: dict[str, dict[str, int]] = {}
        for schema in SchemaName:
            token2idx[schema.value] = {}
            for idx, table in enumerate(self.get_table(schema.value)):
                table: SchemaTable
                token2idx[schema.value][table.token] = idx
        self._token2idx = token2idx

        self._label2id: dict[str, int] = {
            category.name: idx for idx, category in enumerate(self.category)
        }

        # add shortcuts
        for record in self.sample_annotation:
            instance: Instance = self.get("instance", record.instance_token)
            category: Category = self.get("category", instance.category_token)
            record.category_name = category.name

        for record in self.object_ann:
            category: Category = self.get("category", record.category_token)
            record.category_name = category.name

        for record in self.surface_ann:
            if record.category_token == "":  # NOTE: Some database contains this case
                warnings.warn(f"Category token is empty for surface ann: {record.token}")
                continue
            category: Category = self.get("category", record.category_token)
            record.category_name = category.name

        registered_channels: list[str] = []
        for record in self.sample_data:
            cs_record: CalibratedSensor = self.get(
                "calibrated_sensor", record.calibrated_sensor_token
            )
            sensor_record: Sensor = self.get("sensor", cs_record.sensor_token)
            record.modality = sensor_record.modality
            record.channel = sensor_record.channel
            # set first sample data token to the corresponding sensor channel,
            # as premise for sample data is ordered by time stamp order.
            if sensor_record.channel not in registered_channels:
                sensor_record.first_sd_token = record.token
                registered_channels.append(sensor_record.channel)

            # set sample data
            if record.is_key_frame:
                sample_record: Sample = self.get("sample", record.sample_token)
                sample_record.data[record.channel] = record.token

        for ann_record in self.sample_annotation:
            sample_record: Sample = self.get("sample", ann_record.sample_token)
            sample_record.ann_3ds.append(ann_record.token)

        for ann_record in self.object_ann:
            sd_record: SampleData = self.get("sample_data", ann_record.sample_data_token)
            sample_record: Sample = self.get("sample", sd_record.sample_token)
            sample_record.ann_2ds.append(ann_record.token)

        for ann_record in self.surface_ann:
            sd_record: SampleData = self.get("sample_data", ann_record.sample_data_token)
            sample_record: Sample = self.get("sample", sd_record.sample_token)
            sample_record.surface_anns.append(ann_record.token)

        log_to_map: dict[str, str] = {}
        for map_record in self.map:
            for log_token in map_record.log_tokens:
                log_to_map[log_token] = map_record.token
        for log_record in self.log:
            log_record.map_token = log_to_map[log_record.token]

        if verbose:
            elapsed_time = time.time() - start_time
            print(f"Done reverse indexing in {elapsed_time:.3f} seconds.\n======")

    def get_table(self, schema: str | SchemaName) -> list[SchemaTable]:
        """Return the list of dataclasses corresponding to the schema table.

        Args:
            schema (str | SchemaName): Name of schema table.

        Returns:
            List of dataclasses.
        """
        return getattr(self, SchemaName(schema))

    def get(self, schema: str | SchemaName, token: str) -> SchemaTable:
        """Return a record identified by the associated token.

        Args:
            schema (str | SchemaName): Name of schema.
            token (str): Token to identify the specific record.

        Returns:
            Table record of the corresponding token.
        """
        return self.get_table(schema)[self.get_idx(schema, token)]

    def get_idx(self, schema: str | SchemaName, token: str) -> int:
        """Return the index of the record in a table in constant runtime.

        Args:
            schema (str | SchemaName): Name of schema.
            token (str): Token of record.

        Returns:
            The index of the record in table.
        """
        schema = SchemaName(schema)
        if self._token2idx.get(schema) is None:
            raise KeyError(f"{schema} is not registered.")
        if self._token2idx[schema].get(token) is None:
            raise KeyError(f"{token} is not registered in {schema}.")
        return self._token2idx[schema][token]

    def get_sample_data_path(self, sample_data_token: str) -> str:
        """Return the file path to a raw data recorded in `sample_data`.

        Args:
            sample_data_token (str): Token of `sample_data`.

        Returns:
            File path.
        """
        sd_record: SampleData = self.get("sample_data", sample_data_token)
        return osp.join(self.data_root, sd_record.filename)

    def get_sample_data(
        self,
        sample_data_token: str,
        *,
        selected_ann_tokens: list[str] | None = None,
        as_3d: bool = True,
        as_sensor_coord: bool = True,
        visibility: VisibilityLevel = VisibilityLevel.NONE,
    ) -> tuple[str, list[BoxType], CamIntrinsicType | None]:
        """Return the data path as well as all annotations related to that `sample_data`.
        Note that output boxes is w.r.t base link or sensor coordinate system.

        Args:
            sample_data_token (str): Token of `sample_data`.
            selected_ann_tokens (list[str] | None, optional):
                Specify if you want to extract only particular annotations.
            as_3d (bool, optional): Whether to return 3D or 2D boxes.
            as_sensor_coord (bool, optional): Whether to transform boxes as sensor origin coordinate system.
            visibility (VisibilityLevel, optional): If `sample_data` is an image,
                this sets required visibility for only 3D boxes.

        Returns:
            Data path, a list of boxes and 3x3 camera intrinsic matrix.
        """
        # Retrieve sensor & pose records
        sd_record: SampleData = self.get("sample_data", sample_data_token)
        cs_record: CalibratedSensor = self.get(
            "calibrated_sensor", sd_record.calibrated_sensor_token
        )
        sensor_record: Sensor = self.get("sensor", cs_record.sensor_token)
        pose_record: EgoPose = self.get("ego_pose", sd_record.ego_pose_token)

        data_path = self.get_sample_data_path(sample_data_token)

        if sensor_record.modality == SensorModality.CAMERA:
            cam_intrinsic = cs_record.camera_intrinsic
            img_size = (sd_record.width, sd_record.height)
        else:
            cam_intrinsic = None
            img_size = None

        # Retrieve all sample annotations and map to sensor coordinate system.
        boxes: list[BoxType]
        if selected_ann_tokens is not None:
            boxes = (
                list(map(self.get_box3d, selected_ann_tokens))
                if as_3d
                else list(map(self.get_box2d, selected_ann_tokens))
            )
        else:
            boxes = (
                self.get_box3ds(sample_data_token) if as_3d else self.get_box2ds(sample_data_token)
            )

        if not as_3d:
            return data_path, boxes, cam_intrinsic

        # Make list of Box objects including coord system transforms.
        box_list: list[Box3D] = []
        for box in boxes:
            # Move box to ego vehicle coord system.
            box.translate(-pose_record.translation)
            box.rotate(pose_record.rotation.inverse)
            box.frame_id = "base_link"

            if as_sensor_coord:
                #  Move box to sensor coord system.
                box.translate(-cs_record.translation)
                box.rotate(cs_record.rotation.inverse)
                box.frame_id = sensor_record.channel

            if sensor_record.modality == SensorModality.CAMERA and not is_box_in_image(
                box,
                cam_intrinsic,
                img_size,
                visibility=visibility,
            ):
                continue
            box_list.append(box)

        return data_path, box_list, cam_intrinsic

    def get_semantic_label(
        self,
        category_token: str,
        attribute_tokens: list[str] | None = None,
    ) -> SemanticLabel:
        """Return a SemanticLabel instance from specified `category_token` and `attribute_tokens`.

        Args:
            category_token (str): Token of `Category` table.
            attribute_tokens (list[str] | None, optional): List of attribute tokens.

        Returns:
            Instantiated SemanticLabel.
        """
        category: Category = self.get("category", category_token)
        attributes: list[str] = (
            [self.get("attribute", token).name for token in attribute_tokens]
            if attribute_tokens is not None
            else []
        )

        return SemanticLabel(category.name, attributes)

    def get_box3d(self, sample_annotation_token: str) -> Box3D:
        """Return a Box3D class from a `sample_annotation` record.

        Args:
            sample_annotation_token (str): Token of `sample_annotation`.

        Returns:
            Instantiated Box3D.
        """
        ann: SampleAnnotation = self.get("sample_annotation", sample_annotation_token)
        instance: Instance = self.get("instance", ann.instance_token)
        sample: Sample = self.get("sample", ann.sample_token)

        # semantic label
        semantic_label = self.get_semantic_label(
            category_token=instance.category_token,
            attribute_tokens=ann.attribute_tokens,
        )

        shape = Shape(shape_type=ShapeType.BOUNDING_BOX, size=ann.size)

        # velocity
        velocity = self.box_velocity(sample_annotation_token=sample_annotation_token)

        return Box3D(
            unix_time=sample.timestamp,
            frame_id="map",
            semantic_label=semantic_label,
            position=ann.translation,
            rotation=ann.rotation,
            shape=shape,
            velocity=velocity,
            confidence=1.0,
            uuid=instance.token,  # TODO(ktro2828): extract uuid from `instance_name`.
        )

    def get_box2d(self, object_ann_token: str) -> Box2D:
        """Return a Box2D class from a `object_ann` record.

        Args:
            object_ann_token (str): Token of `object_ann`.

        Returns:
            Instantiated Box2D.
        """
        ann: ObjectAnn = self.get("object_ann", object_ann_token)
        instance: Instance = self.get("instance", ann.instance_token)
        sample_data: SampleData = self.get("sample_data", ann.sample_data_token)

        semantic_label = self.get_semantic_label(
            category_token=ann.category_token,
            attribute_tokens=ann.attribute_tokens,
        )

        return Box2D(
            unix_time=sample_data.timestamp,
            frame_id=sample_data.channel,
            semantic_label=semantic_label,
            roi=ann.bbox,
            confidence=1.0,
            uuid=instance.token,  # TODO(ktro2828): extract uuid from `instance_name`.
        )

    def get_box3ds(self, sample_data_token: str) -> list[Box3D]:
        """Rerun a list of Box3D classes for all annotations of a particular `sample_data` record.
        It the `sample_data` is a keyframe, this returns annotations for the corresponding `sample`.

        Args:
            sample_data_token (str): Token of `sample_data`.

        Returns:
            List of instantiated Box3D classes.
        """
        # Retrieve sensor & pose records
        sd_record: SampleData = self.get("sample_data", sample_data_token)
        curr_sample_record: Sample = self.get("sample", sd_record.sample_token)

        if curr_sample_record.prev == "" or sd_record.is_key_frame:
            # If no previous annotations available, or if sample_data is keyframe just return the current ones.
            boxes = list(map(self.get_box3d, curr_sample_record.ann_3ds))

        else:
            prev_sample_record: Sample = self.get("sample", curr_sample_record.prev)

            curr_ann_recs: list[SampleAnnotation] = [
                self.get("sample_annotation", token) for token in curr_sample_record.ann_3ds
            ]
            prev_ann_recs: list[SampleAnnotation] = [
                self.get("sample_annotation", token) for token in prev_sample_record.ann_3ds
            ]

            # Maps instance tokens to prev_ann records
            prev_inst_map = {entry.instance_token: entry for entry in prev_ann_recs}

            t0 = prev_sample_record.timestamp
            t1 = curr_sample_record.timestamp
            t = sd_record.timestamp

            # There are rare situations where the timestamps in the DB are off so ensure that t0 < t < t1.
            t = max(t0, min(t1, t))

            boxes: list[Box3D] = []
            for curr_ann in curr_ann_recs:
                if curr_ann.instance_token in prev_inst_map:
                    # If the annotated instance existed in the previous frame, interpolate center & orientation.
                    prev_ann = prev_inst_map[curr_ann.instance_token]

                    # Interpolate center.
                    position = [
                        np.interp(t, [t0, t1], [c0, c1])
                        for c0, c1 in zip(
                            prev_ann.translation,
                            curr_ann.translation,
                            strict=True,
                        )
                    ]

                    # Interpolate orientation.
                    rotation = Quaternion.slerp(
                        q0=prev_ann.rotation,
                        q1=curr_ann.rotation,
                        amount=(t - t0) / (t1 - t0),
                    )

                    instance: Instance = self.get("instance", curr_ann.instance_token)
                    semantic_label = self.get_semantic_label(
                        instance.category_token, curr_ann.attribute_tokens
                    )
                    velocity = self.box_velocity(curr_ann.token)

                    box = Box3D(
                        unix_time=t,
                        frame_id="map",
                        semantic_label=semantic_label,
                        position=position,
                        rotation=rotation,
                        shape=Shape(ShapeType.BOUNDING_BOX, curr_ann.size),
                        velocity=velocity,
                        confidence=1.0,
                        uuid=instance.token,  # TODO(ktro2828): extract uuid from `instance_name`.
                    )
                else:
                    # If not, simply grab the current annotation.
                    box = self.get_box3d(curr_ann.token)
                boxes.append(box)

        return boxes

    def get_box2ds(self, sample_data_token: str) -> list[Box2D]:
        """Rerun a list of Box2D classes for all annotations of a particular `sample_data` record.
        It the `sample_data` is a keyframe, this returns annotations for the corresponding `sample`.

        Args:
            sample_data_token (str): Token of `sample_data`.

        Returns:
            List of instantiated Box2D classes.
        """
        sd_record: SampleData = self.get("sample_data", sample_data_token)
        sample_record: Sample = self.get("sample", sd_record.sample_token)
        return list(map(self.get_box2d, sample_record.ann_2ds))

    def box_velocity(
        self, sample_annotation_token: str, max_time_diff: float = 1.5
    ) -> VelocityType:
        """Return the velocity of an annotation.
        If corresponding annotation has a true velocity, this returns it.
        Otherwise, this estimates the velocity by computing the difference
        between the previous and next frame.
        If it is failed to estimate the velocity, values are set to np.nan.

        Args:
            sample_annotation_token (str): Token of `sample_annotation`.
            max_time_diff (float, optional): Max allowed time difference
                between consecutive samples.

        Returns:
            VelocityType: Velocity in the order of (vx, vy, vz) in m/s.

        TODO:
            Currently, velocity coordinates is with respect to map, but
            if should be each box.
        """
        current: SampleAnnotation = self.get("sample_annotation", sample_annotation_token)

        # If the real velocity is annotated, returns it
        if current.velocity is not None:
            return current.velocity

        has_prev = current.prev != ""
        has_next = current.next != ""

        # Cannot estimate velocity for a single annotation.
        if not has_prev and not has_next:
            return np.array([np.nan, np.nan, np.nan])

        first: SampleAnnotation = (
            self.get("sample_annotation", current.prev) if has_prev else current
        )

        last: SampleAnnotation = (
            self.get("sample_annotation", current.next) if has_next else current
        )

        pos_last = last.translation
        pos_first = first.translation
        pos_diff = pos_last - pos_first

        last_sample: Sample = self.get("sample", last.sample_token)
        first_sample: Sample = self.get("sample", first.sample_token)
        time_last = 1e-6 * last_sample.timestamp
        time_first = 1e-6 * first_sample.timestamp
        time_diff = time_last - time_first

        if has_next and has_prev:
            # If doing centered difference, allow for up to double the max_time_diff.
            max_time_diff *= 2

        if time_diff > max_time_diff:
            # If time_diff is too big, don't return an estimate.
            return np.array([np.nan, np.nan, np.nan])
        else:
            return pos_diff / time_diff

    def project_pointcloud(
        self,
        point_sample_data_token: str,
        camera_sample_data_token: str,
        min_dist: float = 1.0,
        *,
        ignore_distortion: bool = False,
    ) -> tuple[NDArrayF64, NDArrayF64, NDArrayU8]:
        """Project pointcloud on image plane.

        Args:
            point_sample_data_token (str): Sample data token of lidar or radar sensor.
            camera_sample_data_token (str): Sample data token of camera.
            min_dist (float, optional): Distance from the camera below which points are discarded.
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.

        Returns:
            Projected points [2, n], their normalized depths [n] and an image.
        """
        point_sample_data: SampleData = self.get("sample_data", point_sample_data_token)
        pc_filepath = osp.join(self.data_root, point_sample_data.filename)
        if point_sample_data.modality == SensorModality.LIDAR:
            pointcloud = LidarPointCloud.from_file(pc_filepath)
        elif point_sample_data.modality == SensorModality.RADAR:
            pointcloud = RadarPointCloud.from_file(pc_filepath)
        else:
            raise ValueError(f"Expected sensor lidar/radar, but got {point_sample_data.modality}")

        camera_sample_data: SampleData = self.get("sample_data", camera_sample_data_token)
        if camera_sample_data.modality != SensorModality.CAMERA:
            f"Expected camera, but got {camera_sample_data.modality}"

        img = Image.open(osp.join(self.data_root, camera_sample_data.filename))

        # 1. transform the pointcloud to the ego vehicle frame for the timestamp to the sweep.
        point_cs_record: CalibratedSensor = self.get(
            "calibrated_sensor", point_sample_data.calibrated_sensor_token
        )
        pointcloud.rotate(point_cs_record.rotation.rotation_matrix)
        pointcloud.translate(point_cs_record.translation)

        # 2. transform from ego to the global frame.
        point_ego_pose: EgoPose = self.get("ego_pose", point_sample_data.ego_pose_token)
        pointcloud.rotate(point_ego_pose.rotation.rotation_matrix)
        pointcloud.translate(point_ego_pose.translation)

        # 3. transform from global into the ego vehicle frame for the timestamp of the image
        camera_ego_pose: EgoPose = self.get("ego_pose", camera_sample_data.ego_pose_token)
        pointcloud.translate(-camera_ego_pose.translation)
        pointcloud.rotate(camera_ego_pose.rotation.rotation_matrix.T)

        # 4. transform from ego into the camera
        camera_cs_record: CalibratedSensor = self.get(
            "calibrated_sensor", camera_sample_data.calibrated_sensor_token
        )
        pointcloud.translate(-camera_cs_record.translation)
        pointcloud.rotate(camera_cs_record.rotation.rotation_matrix.T)

        depths = pointcloud.points[2, :]

        distortion = None if ignore_distortion else camera_cs_record.camera_distortion

        points_on_img = view_points(
            points=pointcloud.points[:3, :],
            intrinsic=camera_cs_record.camera_intrinsic,
            distortion=distortion,
            normalize=True,
        )[:2]

        mask = np.ones(depths.shape[0], dtype=bool)
        mask = np.logical_and(mask, depths > min_dist)
        mask = np.logical_and(mask, 1 < points_on_img[0])
        mask = np.logical_and(mask, points_on_img[0] < img.size[0] - 1)
        mask = np.logical_and(mask, 1 < points_on_img[1])
        mask = np.logical_and(mask, points_on_img[1] < img.size[1] - 1)
        points_on_img = points_on_img[:, mask]
        depths = depths[mask]

        return points_on_img, depths, np.array(img, dtype=np.uint8)

    def render_scene(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        save_dir: str | None = None,
        show: bool = True,
    ) -> None:
        """Render specified scene.

        Args:
            scene_token (str): Unique identifier of scene.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            save_dir (str | None, optional): Directory path to save the recording.
            show (bool, optional): Whether to spawn rendering viewer.
        """
        # search first sample data tokens
        first_lidar_token: str | None = None
        first_radar_tokens: list[str] = []
        first_camera_tokens: list[str] = []
        for sensor in self.sensor:
            sd_token = sensor.first_sd_token
            if sensor.modality == SensorModality.LIDAR:
                first_lidar_token = sd_token
            elif sensor.modality == SensorModality.RADAR:
                first_radar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.CAMERA:
                first_camera_tokens.append(sd_token)

        render_3d = first_lidar_token is not None or len(first_radar_tokens) > 0
        render_2d = len(first_camera_tokens) > 0

        # initialize viewer
        application_id = f"t4-devkit@{scene_token}"
        viewer = self._init_viewer(
            application_id,
            render_3d=render_3d,
            render_2d=render_2d,
            render_annotation=True,
            spawn=show,
        )

        scene: Scene = self.get("scene", scene_token)
        first_sample: Sample = self.get("sample", scene.first_sample_token)
        max_timestamp_us = first_sample.timestamp + sec2us(max_time_seconds)

        # render raw data for each sensor
        if first_lidar_token is not None:
            self._render_lidar_and_ego(viewer, first_lidar_token, max_timestamp_us)
        self._render_radars(viewer, first_radar_tokens, max_timestamp_us)
        self._render_cameras(viewer, first_camera_tokens, max_timestamp_us)

        # render annotation
        self._render_annotation_3ds(viewer, scene.first_sample_token, max_timestamp_us)
        self._render_annotation_2ds(viewer, scene.first_sample_token, max_timestamp_us)

        if save_dir is not None:
            viewer.save(save_dir)

    def render_instance(
        self,
        instance_token: str,
        *,
        save_dir: str | None = None,
        show: bool = True,
    ) -> None:
        """Render particular instance.

        Args:
            instance_token (str): Instance token.
            save_dir (str | None, optional): Directory path to save the recording.
            show (bool, optional): Whether to spawn rendering viewer.
        """
        # search first sample associated with the instance
        instance: Instance = self.get("instance", instance_token)
        first_ann: SampleAnnotation = self.get("sample_annotation", instance.first_annotation_token)
        first_sample: Sample = self.get("sample", first_ann.sample_token)

        # search first sample data tokens
        first_lidar_token: str | None = None
        first_radar_tokens: list[str] = []
        first_camera_tokens: list[str] = []
        for sensor in self.sensor:
            sd_token = sensor.first_sd_token
            if sensor.modality == SensorModality.LIDAR:
                first_lidar_token = sd_token
            elif sensor.modality == SensorModality.RADAR:
                first_radar_tokens.append(sd_token)
            elif sensor.modality == SensorModality.CAMERA:
                first_camera_tokens.append(sd_token)

        render_3d = first_lidar_token is not None or len(first_radar_tokens) > 0
        render_2d = len(first_camera_tokens) > 0

        # initialize viewer
        application_id = f"t4-devkit@{instance_token}"
        viewer = self._init_viewer(
            application_id,
            render_3d=render_3d,
            render_2d=render_2d,
            render_annotation=True,
            spawn=show,
        )

        last_ann: SampleAnnotation = self.get("sample_annotation", instance.last_annotation_token)
        last_sample: Sample = self.get("sample", last_ann.sample_token)
        max_timestamp_us = last_sample.timestamp

        # render sensors
        if first_lidar_token is not None:
            self._render_lidar_and_ego(viewer, first_lidar_token, max_timestamp_us)
        self._render_radars(viewer, first_radar_tokens, max_timestamp_us)
        self._render_cameras(viewer, first_camera_tokens, max_timestamp_us)

        # render annotations
        self._render_annotation_3ds(
            viewer,
            first_sample.token,
            max_timestamp_us,
            instance_token=instance_token,
        )
        self._render_annotation_2ds(
            viewer,
            first_sample.token,
            max_timestamp_us,
            instance_token=instance_token,
        )

        if save_dir is not None:
            viewer.save(save_dir)

    def render_pointcloud(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        ignore_distortion: bool = True,
        save_dir: str | None = None,
        show: bool = True,
    ) -> None:
        """Render pointcloud on 3D and 2D view.

        Args:
            scene_token (str): Scene token.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            save_dir (str | None, optional): Directory path to save the recording.
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.
            show (bool, optional): Whether to spawn rendering viewer.

        TODO:
            Add an option of rendering radar channels.
        """
        # search first lidar sample data token
        first_lidar_token: str | None = None
        for sensor in self.sensor:
            if sensor.modality != SensorModality.LIDAR:
                continue
            first_lidar_token = sensor.first_sd_token

        if first_lidar_token is None:
            print("There is no 3D pointcloud data, abort rendering...")
            return

        # initialize viewer
        application_id = f"t4-devkit@{scene_token}"
        viewer = self._init_viewer(application_id, render_annotation=False, spawn=show)
        first_lidar_sd_record: SampleData = self.get("sample_data", first_lidar_token)
        max_timestamp_us = first_lidar_sd_record.timestamp + sec2us(max_time_seconds)

        # render pointcloud
        self._render_lidar_and_ego(
            viewer,
            first_lidar_token,
            max_timestamp_us,
            project_points=True,
            ignore_distortion=ignore_distortion,
        )

        if save_dir is not None:
            viewer.save(save_dir)

    def _init_viewer(
        self,
        application_id: str,
        *,
        render_3d: bool = True,
        render_2d: bool = True,
        render_annotation: bool = True,
        spawn: bool = False,
    ) -> RerunViewer:
        """Initialize rendering viewer.

        Args:
            application_id (str): Application ID.
            render_3d (bool, optional): Whether to render 3D space.
            render_2d (bool, optional): Whether to render 2D space.
            render_annotation (bool, optional): Whether to render annotations.
            spawn (bool, optional): Whether to spawn rendering viewer.

        Returns:
            Viewer object.
        """
        if not (render_3d or render_2d):
            raise ValueError("At least one of `render_3d` or `render_2d` must be True.")

        cameras = (
            [sensor.channel for sensor in self.sensor if sensor.modality == SensorModality.CAMERA]
            if render_2d
            else None
        )

        viewer = RerunViewer(application_id, cameras=cameras, with_3d=render_3d, spawn=spawn)

        if render_annotation:
            viewer = viewer.with_labels(self._label2id)

        global_map_filepath = osp.join(self.data_root, "map/global_map_center.pcd.yaml")
        if osp.exists(global_map_filepath):
            with open(global_map_filepath) as f:
                map_metadata: dict = yaml.safe_load(f)
            map_origin: dict = map_metadata["/**"]["ros__parameters"]["map_origin"]
            latitude = map_origin["latitude"]
            longitude = map_origin["longitude"]
            viewer = viewer.with_global_origin((latitude, longitude))

        print(f"Finish initializing {application_id} ...")

        return viewer

    def _render_lidar_and_ego(
        self,
        viewer: RerunViewer,
        first_lidar_token: str,
        max_timestamp_us: float,
        *,
        project_points: bool = False,
        ignore_distortion: bool = True,
    ) -> None:
        """Render lidar pointcloud and ego transform.

        Args:
            viewer (RerunViewer): Viewer object.
            first_lidar_token (str): First sample data token corresponding to the lidar.
            max_timestamp_us (float): Max time length in [us].
            project_points (bool, optional): Whether to project 3d points on 2d images.
            ignore_distortion (boo, optional): Whether to ignore distortion parameters.
                This argument is only used if `project_points=True`.
        """
        self._render_sensor_calibration(viewer, first_lidar_token)

        current_lidar_token = first_lidar_token

        while current_lidar_token != "":
            sample_data: SampleData = self.get("sample_data", current_lidar_token)

            if max_timestamp_us < sample_data.timestamp:
                break

            # render ego
            ego_pose: EgoPose = self.get("ego_pose", sample_data.ego_pose_token)
            viewer.render_ego(ego_pose)

            # render lidar pointcloud
            pointcloud = LidarPointCloud.from_file(osp.join(self.data_root, sample_data.filename))
            viewer.render_pointcloud(us2sec(sample_data.timestamp), sample_data.channel, pointcloud)

            if project_points:
                self._render_points_on_cameras(
                    current_lidar_token,
                    max_timestamp_us,
                    ignore_distortion=ignore_distortion,
                )

            current_lidar_token = sample_data.next

    def _render_radars(
        self,
        viewer: RerunViewer,
        first_radar_tokens: list[str],
        max_timestamp_us: float,
    ) -> None:
        """Render radar pointcloud.

        Args:
            viewer (RerunViewer): Viewer object.
            first_radar_tokens (list[str]): List of first sample data tokens corresponding to radars.
            max_timestamp_us (float): Max time length in [us].
        """
        for first_radar_token in first_radar_tokens:
            self._render_sensor_calibration(viewer, first_radar_token)

            current_radar_token = first_radar_token
            while current_radar_token != "":
                sample_data: SampleData = self.get("sample_data", current_radar_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                # render radar pointcloud
                pointcloud = RadarPointCloud.from_file(
                    osp.join(self.data_root, sample_data.filename)
                )
                viewer.render_pointcloud(
                    us2sec(sample_data.timestamp), sample_data.channel, pointcloud
                )

                current_radar_token = sample_data.next

    def _render_cameras(
        self, viewer: RerunViewer, first_camera_tokens: list[str], max_timestamp_us: float
    ) -> None:
        """Render camera images.

        Args:
            viewer (RerunViewer): Viewer object.
            first_camera_tokens (list[str]): List of first sample data tokens corresponding to cameras.
            max_timestamp_us (float): Max time length in [us].
        """
        for first_camera_token in first_camera_tokens:
            self._render_sensor_calibration(viewer, first_camera_token)

            current_camera_token = first_camera_token
            while current_camera_token != "":
                sample_data: SampleData = self.get("sample_data", current_camera_token)

                if max_timestamp_us < sample_data.timestamp:
                    break

                # render camera image
                viewer.render_image(
                    us2sec(sample_data.timestamp),
                    sample_data.channel,
                    osp.join(self.data_root, sample_data.filename),
                )

                current_camera_token = sample_data.next

    def _render_points_on_cameras(
        self,
        point_sample_data_token: str,
        max_timestamp_us: float,
        *,
        min_dist: float = 1.0,
        ignore_distortion: bool = False,
    ) -> None:
        """Render points on each camera sensor at a sample.

        Args:
            point_sample_data_token (str): Sample data token of pointcloud sensor.
            max_timestamp_us (float): Max time length in [us].
            min_dist (float, optional): Min focal distance to render points.
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.

        TODO:
            Replace operation by `RerunViewer`.
        """
        point_sample_data: SampleData = self.get("sample_data", point_sample_data_token)
        sample: Sample = self.get("sample", point_sample_data.sample_token)

        for channel, sd_token in sample.data.items():
            camera_sample_data: SampleData = self.get("sample_data", sd_token)
            if camera_sample_data.modality != SensorModality.CAMERA:
                continue

            if max_timestamp_us < camera_sample_data.timestamp:
                break

            points_on_img, depths, img = self.project_pointcloud(
                point_sample_data_token=point_sample_data_token,
                camera_sample_data_token=sd_token,
                min_dist=min_dist,
                ignore_distortion=ignore_distortion,
            )

            sensor_name = channel
            rr.set_time_seconds("timestamp", us2sec(camera_sample_data.timestamp))
            rr.log(format_entity(RerunViewer.ego_entity, sensor_name), rr.Image(img))

            rr.log(
                format_entity(RerunViewer.ego_entity, sensor_name, "pointcloud"),
                rr.Points2D(
                    positions=points_on_img.T,
                    colors=distance_color(depths),
                ),
            )

    def _render_annotation_3ds(
        self,
        viewer: RerunViewer,
        first_sample_token: str,
        max_timestamp_us: float,
        instance_token: str | None = None,
    ) -> None:
        """Render annotated 3D boxes.

        Args:
            viewer (RerunViewer): Viewer object.
            first_sample_token (str): First sample token.
            max_timestamp_us (float): Max time length in [us].
            instance_token (str | None, optional): Specify if you want to render only particular instance.
        """
        current_sample_token = first_sample_token
        while current_sample_token != "":
            sample: Sample = self.get("sample", current_sample_token)

            if max_timestamp_us < sample.timestamp:
                break

            if instance_token is not None:
                boxes = []
                for ann_token in sample.ann_3ds:
                    ann: SampleAnnotation = self.get("sample_annotation", ann_token)
                    if ann.instance_token == instance_token:
                        boxes.append(self.get_box3d(ann_token))
                        break
            else:
                boxes = list(map(self.get_box3d, sample.ann_3ds))
            viewer.render_box3ds(us2sec(sample.timestamp), boxes)

            current_sample_token = sample.next

    def _render_annotation_2ds(
        self,
        viewer: RerunViewer,
        first_sample_token: str,
        max_timestamp_us: float,
        instance_token: str | None = None,
    ) -> None:
        """Render annotated 2D boxes.

        Args:
            viewer (RerunViewer): Viewer object.
            first_sample_token (str): First sample token.
            max_timestamp_us (float): Max time length in [us].
            instance_token (str | None, optional): Specify if you want to render only particular instance.

        TODO:
            2D boxes are rendered at sample data timestamp.
            Then, they remains until next timestamp annotation is coming.
        """
        current_sample_token = first_sample_token
        while current_sample_token != "":
            sample: Sample = self.get("sample", current_sample_token)

            if max_timestamp_us < sample.timestamp:
                break

            boxes: list[Box2D] = []

            # For segmentation masks
            # TODO: declare specific class for segmentation mask in `dataclass`
            camera_masks: dict[str, dict[str, list]] = {}

            # Object Annotation
            for ann_token in sample.ann_2ds:
                ann: ObjectAnn = self.get("object_ann", ann_token)
                box = self.get_box2d(ann_token)
                boxes.append(box)

                sample_data: SampleData = self.get("sample_data", ann.sample_data_token)
                camera_masks = _append_mask(
                    camera_masks,
                    camera=sample_data.channel,
                    ann=ann,
                    class_id=self._label2id[ann.category_name],
                    uuid=box.uuid,
                )

            # Render 2D box
            viewer.render_box2ds(us2sec(sample.timestamp), boxes)

            # Surface Annotation
            for ann_token in sample.surface_anns:
                sample_data: SampleData = self.get("sample_data", ann.sample_data_token)
                ann: SurfaceAnn = self.get("surface_ann", ann_token)
                camera_masks = _append_mask(
                    camera_masks,
                    camera=sample_data.channel,
                    ann=ann,
                    class_id=self._label2id[ann.category_name],
                )

            # Render 2D segmentation image
            for camera, data in camera_masks.items():
                viewer.render_segmentation2d(
                    seconds=us2sec(sample.timestamp), camera=camera, **data
                )

            # TODO: add support of rendering keypoints
            current_sample_token = sample.next

    def _render_sensor_calibration(self, viewer: RerunViewer, sample_data_token: str) -> None:
        """Render a fixed calibrated sensor transform.

        Args:
            viewer (RerunViewer): Viewer object.
            sample_data_token (str): First sample data token corresponding to the sensor.
        """
        sample_data: SampleData = self.get("sample_data", sample_data_token)
        calibrated_sensor: CalibratedSensor = self.get(
            "calibrated_sensor", sample_data.calibrated_sensor_token
        )
        sensor: Sensor = self.get("sensor", calibrated_sensor.sensor_token)
        viewer.render_calibration(sensor, calibrated_sensor)


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
        camera_masks[camera]["uuids"] = [class_id]
    return camera_masks
    return camera_masks
