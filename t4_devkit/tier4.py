from __future__ import annotations

import asyncio
import os.path as osp
import time
import warnings
from typing import TYPE_CHECKING, Sequence

import numpy as np
from pyquaternion import Quaternion

from t4_devkit.common.geometry import is_box_in_image
from t4_devkit.dataclass import (
    Box2D,
    Box3D,
    SemanticLabel,
    Shape,
    ShapeType,
)
from t4_devkit.helper import RenderingHelper, TimeseriesHelper
from t4_devkit.schema import SchemaName, SensorModality, VisibilityLevel, build_schema

if TYPE_CHECKING:
    from t4_devkit.typing import CamIntrinsicLike, Vector3Like

    from .dataclass import BoxLike
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

        # initialize helpers after finishing construction of Tier4
        self._timeseries_helper = TimeseriesHelper(self)
        self._rendering_helper = RenderingHelper(self)

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
        future_seconds: float = 0.0,
        visibility: VisibilityLevel = VisibilityLevel.NONE,
    ) -> tuple[str, list[BoxLike], CamIntrinsicLike | None]:
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
        boxes: list[BoxLike]
        if selected_ann_tokens is not None:
            boxes = (
                [
                    self.get_box3d(token, future_seconds=future_seconds)
                    for token in selected_ann_tokens
                ]
                if as_3d
                else list(map(self.get_box2d, selected_ann_tokens))
            )
        else:
            boxes = (
                self.get_box3ds(sample_data_token, future_seconds=future_seconds)
                if as_3d
                else self.get_box2ds(sample_data_token)
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

    def get_box3d(self, sample_annotation_token: str, *, future_seconds: float = 0.0) -> Box3D:
        """Return a Box3D class from a `sample_annotation` record.

        Args:
            sample_annotation_token (str): Token of `sample_annotation`.
            future_seconds (float, optional): Future time in [s].

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

        box = Box3D(
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

        if future_seconds > 0.0:
            # NOTE: Future trajectory is map coordinate frame
            timestamps, anns = self._timeseries_helper.get_sample_annotations_until(
                ann.instance_token, ann.sample_token, future_seconds
            )
            if len(anns) == 0:
                return box
            waypoints = [ann.translation for ann in anns]
            return box.with_future(timestamps=timestamps, confidences=[1.0], waypoints=[waypoints])
        else:
            return box

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

    def get_box3ds(self, sample_data_token: str, *, future_seconds: float = 0.0) -> list[Box3D]:
        """Rerun a list of Box3D classes for all annotations of a particular `sample_data` record.
        It the `sample_data` is a keyframe, this returns annotations for the corresponding `sample`.

        Args:
            sample_data_token (str): Token of `sample_data`.
            future_seconds (float, optional): Future time in [s].

        Returns:
            List of instantiated Box3D classes.
        """
        # Retrieve sensor & pose records
        sd_record: SampleData = self.get("sample_data", sample_data_token)
        curr_sample_record: Sample = self.get("sample", sd_record.sample_token)

        if curr_sample_record.prev == "" or sd_record.is_key_frame:
            # If no previous annotations available, or if sample_data is keyframe just return the current ones.
            boxes = [
                self.get_box3d(token, future_seconds=future_seconds)
                for token in curr_sample_record.ann_3ds
            ]

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
                    box = self.get_box3d(curr_ann.token, future_seconds=future_seconds)
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

    def box_velocity(self, sample_annotation_token: str, max_time_diff: float = 1.5) -> Vector3Like:
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
            Vector3Like: Velocity in the order of (vx, vy, vz) in m/s.

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

    def render_scene(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        future_seconds: float = 0.0,
        save_dir: str | None = None,
    ) -> None:
        """Render specified scene.

        Args:
            scene_token (str): Unique identifier of scene.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            future_seconds (float, optional): Future time in [s].
            save_dir (str | None, optional): Directory path to save the recording.
        """
        coroutine = self._rendering_helper.async_render_scene(
            scene_token=scene_token,
            max_time_seconds=max_time_seconds,
            future_seconds=future_seconds,
            save_dir=save_dir,
        )

        asyncio.run(coroutine)

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
        """
        coroutine = self._rendering_helper.async_render_instance(
            instance_token=instance_token,
            future_seconds=future_seconds,
            save_dir=save_dir,
        )

        asyncio.run(coroutine)

    def render_pointcloud(
        self,
        scene_token: str,
        *,
        max_time_seconds: float = np.inf,
        ignore_distortion: bool = True,
        save_dir: str | None = None,
    ) -> None:
        """Render pointcloud on 3D and 2D view.

        Args:
            scene_token (str): Scene token.
            max_time_seconds (float, optional): Max time length to be rendered [s].
            save_dir (str | None, optional): Directory path to save the recording.
            ignore_distortion (bool, optional): Whether to ignore distortion parameters.

        TODO:
            Add an option of rendering radar channels.
        """
        coroutine = self._rendering_helper.async_render_pointcloud(
            scene_token=scene_token,
            max_time_seconds=max_time_seconds,
            ignore_distortion=ignore_distortion,
            save_dir=save_dir,
        )

        asyncio.run(coroutine)
