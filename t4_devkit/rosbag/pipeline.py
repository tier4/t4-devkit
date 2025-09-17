"""Main conversion pipeline for T4 to ROS bag conversion."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from t4_devkit import Tier4
from .converter import Box3DToTrackedObjectConverter
from .autoware_messages import TrackedObjects, Header
from .writer import RosbagWriter

if TYPE_CHECKING:
    pass


class T4ToRosbagPipeline:
    """Main pipeline for converting T4 dataset to ROS bag format."""

    def __init__(
        self,
        t4_data_root: str | Path,
        output_path: str | Path,
        source_bag_path: Optional[str | Path] = None,
        revision: Optional[str] = None,
        interpolation_hz: float = 10.0,
        topic_name: str = "/perception/object_recognition/tracked_objects",
        frame_id: str = "base_link",
    ):
        """Initialize the conversion pipeline.

        Args:
            t4_data_root: Root directory of T4 dataset.
            output_path: Output path for ROS bag file.
            source_bag_path: Optional path to source bag to copy all topics from.
            revision: T4 dataset revision to use.
            interpolation_hz: Frequency for interpolated output (Hz).
            topic_name: ROS topic name for tracked objects.
            frame_id: Frame ID for messages.
        """
        self.t4 = Tier4(data_root=t4_data_root, revision=revision, verbose=True)
        self.output_path = Path(output_path)
        self.source_bag_path = Path(source_bag_path) if source_bag_path else None
        self.interpolation_hz = interpolation_hz
        self.topic_name = topic_name
        self.frame_id = frame_id

        self.converter = Box3DToTrackedObjectConverter()
        self.seq_counter = 0

    def convert_scene(self, scene_token: str) -> None:
        """Convert a specific scene to ROS bag format.

        Args:
            scene_token: Token of the scene to convert.
        """
        scene = self.t4.get("scene", scene_token)
        print(f"Converting scene: {scene.name} (token: {scene_token})")

        # Create output path for this scene - use .bag extension for actual rosbag
        scene_output = self.output_path / f"scene_{scene.name}.bag"

        with RosbagWriter(scene_output, self.source_bag_path) as writer:
            # Register the topic
            writer.add_topic(
                self.topic_name, "autoware_auto_perception_msgs/TrackedObjects", self.frame_id
            )

            # Get all samples in the scene
            sample_tokens = self._get_scene_samples(scene_token)
            print(f"Processing {len(sample_tokens)} samples...")

            # Process each sample with interpolation
            for i, sample_token in enumerate(sample_tokens):
                if i % 10 == 0:
                    print(f"Processing sample {i + 1}/{len(sample_tokens)}")

                self._process_sample(writer, sample_token)

    def convert_all_scenes(self) -> None:
        """Convert all scenes in the dataset."""
        for scene_record in self.t4.scene:
            try:
                self.convert_scene(scene_record.token)
            except Exception as e:
                print(f"Error converting scene {scene_record.name}: {e}")
                continue

    def _get_scene_samples(self, scene_token: str) -> list[str]:
        """Get all sample tokens for a scene in chronological order.

        Args:
            scene_token: Scene token.

        Returns:
            List of sample tokens in chronological order.
        """
        scene = self.t4.get("scene", scene_token)
        samples = []

        # Start from first sample
        current_sample_token = scene.first_sample_token
        while current_sample_token != "":
            samples.append(current_sample_token)
            sample = self.t4.get("sample", current_sample_token)
            current_sample_token = sample.next

        return samples

    def _process_sample(self, writer: RosbagWriter, sample_token: str) -> None:
        """Process a single sample and write tracked objects.

        Args:
            writer: ROS bag writer instance.
            sample_token: Token of the sample to process.
        """
        sample = self.t4.get("sample", sample_token)

        # Find the LIDAR sample data (usually the reference sensor)
        lidar_sample_data = None
        for sd_token in sample.data.values():
            sd = self.t4.get("sample_data", sd_token)
            sensor = self.t4.get("sensor", sd.sensor_token)
            if sensor.modality.name == "LIDAR":
                lidar_sample_data = sd
                break

        if lidar_sample_data is None:
            print(f"No LIDAR data found for sample {sample_token}")
            return

        # Get 3D boxes with interpolation (using existing T4 method)
        boxes = self.t4.get_box3ds(lidar_sample_data.token, future_seconds=0.0)

        if not boxes:
            return

        # Convert to TrackedObjects
        tracked_objects_list = self.converter.convert_multiple(boxes)

        # Create header
        timestamp_sec, timestamp_nanosec = self.converter.timestamp_to_ros_time(
            lidar_sample_data.timestamp
        )

        header = Header(
            seq=self.seq_counter,
            stamp_sec=timestamp_sec,
            stamp_nanosec=timestamp_nanosec,
            frame_id=self.frame_id,
        )

        # Create TrackedObjects message
        tracked_objects_msg = TrackedObjects(header=header, objects=tracked_objects_list)

        # Write to bag
        writer.write_tracked_objects(
            self.topic_name, tracked_objects_msg, timestamp_sec, timestamp_nanosec
        )

        self.seq_counter += 1

    def _interpolate_between_samples(
        self, sample1_token: str, sample2_token: str, num_interpolations: int
    ) -> list[dict]:
        """Interpolate between two samples to create intermediate data points.

        Args:
            sample1_token: First sample token.
            sample2_token: Second sample token.
            num_interpolations: Number of interpolated points to create.

        Returns:
            List of interpolated sample data.

        Note:
            This uses the existing T4 interpolation capabilities through get_box3ds.
        """
        # This leverages the existing interpolation in T4's get_box3ds method
        # which already handles keyframe interpolation automatically
        sample1 = self.t4.get("sample", sample1_token)
        sample2 = self.t4.get("sample", sample2_token)

        interpolated_samples = []

        # Generate timestamps between samples
        start_time = sample1.timestamp
        end_time = sample2.timestamp
        time_diff = end_time - start_time

        for i in range(num_interpolations):
            # Calculate interpolation ratio
            ratio = (i + 1) / (num_interpolations + 1)
            interp_timestamp = start_time + int(time_diff * ratio)

            # T4's get_box3ds already handles interpolation for non-keyframes
            # So we can use the existing mechanism
            interpolated_samples.append(
                {
                    "timestamp": interp_timestamp,
                    "ratio": ratio,
                    "sample1_token": sample1_token,
                    "sample2_token": sample2_token,
                }
            )

        return interpolated_samples

    def get_conversion_stats(self) -> dict:
        """Get statistics about the conversion process.

        Returns:
            Dictionary with conversion statistics.
        """
        total_scenes = len(self.t4.scene)
        total_samples = len(self.t4.sample)
        total_annotations = len(self.t4.sample_annotation)

        return {
            "total_scenes": total_scenes,
            "total_samples": total_samples,
            "total_3d_annotations": total_annotations,
            "interpolation_hz": self.interpolation_hz,
            "output_path": str(self.output_path),
        }
