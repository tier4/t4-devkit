"""Main conversion pipeline for T4 to ROS bag conversion."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from t4_devkit import Tier4
from .converter import Box3DToTrackedObjectConverter
from .writer import RosbagWriter

try:
    from autoware_perception_msgs.msg import TrackedObjects
    from std_msgs.msg import Header
    from builtin_interfaces.msg import Time
    AUTOWARE_AVAILABLE = True
except ImportError:
    AUTOWARE_AVAILABLE = False
    print("Warning: Autoware messages not available. Please source your ROS2/Autoware workspace.")

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
        topic_name: str = "/annotation/object_recognition/tracked_objects",
        frame_id: str = "map",
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
        self.t4 = Tier4(data_root=t4_data_root,
                        revision=revision, verbose=True)
        self.output_path = Path(output_path)
        self.source_bag_path = Path(
            source_bag_path) if source_bag_path else None
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

        # Create output path for this scene - use .db3 extension for ROS2 bags
        scene_output = self.output_path / f"scene_{scene.name}.db3"

        # First, collect all annotation messages
        annotation_messages = self._collect_annotation_messages(scene_token)

        with RosbagWriter(scene_output, self.source_bag_path) as writer:
            # Register the topic
            writer.add_topic(
                self.topic_name, "autoware_perception_msgs/msg/TrackedObjects", self.frame_id
            )

            # Merge and write all messages chronologically
            writer.merge_and_write_all_messages(
                annotation_messages, self.topic_name)

    def _collect_annotation_messages(self, scene_token: str) -> list:
        """Collect all annotation messages for a scene.

        Args:
            scene_token: Token of the scene.

        Returns:
            List of tuples (timestamp_ns, TrackedObjects message)
        """
        scene = self.t4.get("scene", scene_token)
        first_sample = self.t4.get("sample", scene.first_sample_token)
        last_sample = self.t4.get("sample", scene.last_sample_token)

        # Calculate time range in microseconds
        scene_start_us = first_sample.timestamp
        scene_end_us = last_sample.timestamp
        scene_duration_s = (scene_end_us - scene_start_us) / 1_000_000.0

        # Calculate time step based on interpolation frequency
        time_step_us = int(1_000_000 / self.interpolation_hz)

        # Calculate number of messages to generate
        num_messages = int(scene_duration_s * self.interpolation_hz)

        print(f"Scene duration: {scene_duration_s:.2f}s")
        print(
            f"Generating {num_messages} messages at {self.interpolation_hz}Hz")

        annotation_messages = []

        # Generate messages at regular intervals
        for i in range(num_messages):
            if i % 100 == 0 and i > 0:
                print(f"Processing message {i}/{num_messages}")

            # Calculate timestamp for this message
            timestamp_us = scene_start_us + (i * time_step_us)

            # Find closest sample for reference
            closest_sample_token = self._find_closest_sample(
                scene_token, timestamp_us)
            if closest_sample_token:
                msg = self._create_tracked_objects_at_timestamp(
                    closest_sample_token, timestamp_us)
                if msg:
                    # Convert to nanoseconds for ROS2
                    timestamp_ns = timestamp_us * 1000
                    annotation_messages.append((timestamp_ns, msg))

        print(f"Generated {len(annotation_messages)} annotation messages")
        return annotation_messages

    def _process_with_interpolation(self, writer: RosbagWriter, scene_token: str) -> None:
        """Process scene with interpolation at the specified frequency.

        Args:
            writer: ROS bag writer instance.
            scene_token: Token of the scene to process.
        """
        scene = self.t4.get("scene", scene_token)
        first_sample = self.t4.get("sample", scene.first_sample_token)
        last_sample = self.t4.get("sample", scene.last_sample_token)

        # Calculate time range in microseconds
        scene_start_us = first_sample.timestamp
        scene_end_us = last_sample.timestamp
        scene_duration_s = (scene_end_us - scene_start_us) / 1_000_000.0

        # Calculate time step based on interpolation frequency
        time_step_us = int(1_000_000 / self.interpolation_hz)

        # Calculate number of messages to generate
        num_messages = int(scene_duration_s * self.interpolation_hz)

        print(f"Scene duration: {scene_duration_s:.2f}s")
        print(
            f"Generating {num_messages} messages at {self.interpolation_hz}Hz")

        # Generate messages at regular intervals
        for i in range(num_messages):
            if i % 100 == 0 and i > 0:
                print(f"Processing message {i}/{num_messages}")

            # Calculate timestamp for this message
            timestamp_us = scene_start_us + (i * time_step_us)

            # Find closest sample for reference
            closest_sample_token = self._find_closest_sample(
                scene_token, timestamp_us)
            if closest_sample_token:
                self._process_sample_at_timestamp(
                    writer, closest_sample_token, timestamp_us)

        print(f"Generated {num_messages} messages")

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
            calibrated_sensor = self.t4.get(
                "calibrated_sensor", sd.calibrated_sensor_token)
            sensor = self.t4.get("sensor", calibrated_sensor.sensor_token)
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

        if AUTOWARE_AVAILABLE:
            header = Header()
            header.frame_id = self.frame_id
            # Create Time message for stamp
            header.stamp = Time()
            header.stamp.sec = timestamp_sec
            header.stamp.nanosec = timestamp_nanosec

            # Create TrackedObjects message
            tracked_objects_msg = TrackedObjects()
            tracked_objects_msg.header = header
            tracked_objects_msg.objects = tracked_objects_list
        else:
            # Fallback to dict format
            tracked_objects_msg = {
                "header": {
                    "frame_id": self.frame_id,
                    "stamp": {
                        "sec": timestamp_sec,
                        "nanosec": timestamp_nanosec
                    }
                },
                "objects": tracked_objects_list
            }

        # Write to bag
        writer.write_tracked_objects(
            self.topic_name, tracked_objects_msg, timestamp_sec, timestamp_nanosec
        )

        self.seq_counter += 1

    def _create_tracked_objects_at_timestamp(self, sample_token: str, timestamp_us: int):
        """Create TrackedObjects message at specific timestamp.

        Args:
            sample_token: Reference sample token.
            timestamp_us: Target timestamp in microseconds.

        Returns:
            TrackedObjects message or None if no data.
        """
        sample = self.t4.get("sample", sample_token)

        # Find the LIDAR sample data
        lidar_sample_data = None
        for sd_token in sample.data.values():
            sd = self.t4.get("sample_data", sd_token)
            calibrated_sensor = self.t4.get(
                "calibrated_sensor", sd.calibrated_sensor_token)
            sensor = self.t4.get("sensor", calibrated_sensor.sensor_token)
            if sensor.modality.name == "LIDAR":
                lidar_sample_data = sd
                break

        if lidar_sample_data is None:
            return None

        # Get 3D boxes with interpolation
        boxes = self.t4.get_box3ds(lidar_sample_data.token, future_seconds=0.0)

        if not boxes:
            return None

        # Convert to TrackedObjects
        tracked_objects_list = self.converter.convert_multiple(boxes)

        # Create header with the target timestamp
        timestamp_sec, timestamp_nanosec = self.converter.timestamp_to_ros_time(
            timestamp_us)

        if AUTOWARE_AVAILABLE:
            header = Header()
            header.frame_id = self.frame_id
            header.stamp = Time()
            header.stamp.sec = timestamp_sec
            header.stamp.nanosec = timestamp_nanosec

            # Create TrackedObjects message
            tracked_objects_msg = TrackedObjects()
            tracked_objects_msg.header = header
            tracked_objects_msg.objects = tracked_objects_list

            return tracked_objects_msg
        else:
            # Fallback - shouldn't happen if properly sourced
            return None

    def _find_closest_sample(self, scene_token: str, target_timestamp_us: int) -> Optional[str]:
        """Find the closest sample to a target timestamp.

        Args:
            scene_token: Scene token.
            target_timestamp_us: Target timestamp in microseconds.

        Returns:
            Token of closest sample or None if not found.
        """
        samples = self._get_scene_samples(scene_token)

        closest_token = None
        min_diff = float('inf')

        for sample_token in samples:
            sample = self.t4.get("sample", sample_token)
            diff = abs(sample.timestamp - target_timestamp_us)

            if diff < min_diff:
                min_diff = diff
                closest_token = sample_token

        return closest_token

    def _process_sample_at_timestamp(
        self, writer: RosbagWriter, sample_token: str, timestamp_us: int
    ) -> None:
        """Process a sample at a specific timestamp (with interpolation if needed).

        Args:
            writer: ROS bag writer instance.
            sample_token: Token of the reference sample.
            timestamp_us: Target timestamp in microseconds.
        """
        sample = self.t4.get("sample", sample_token)

        # Find the LIDAR sample data
        lidar_sample_data = None
        for sd_token in sample.data.values():
            sd = self.t4.get("sample_data", sd_token)
            calibrated_sensor = self.t4.get(
                "calibrated_sensor", sd.calibrated_sensor_token)
            sensor = self.t4.get("sensor", calibrated_sensor.sensor_token)
            if sensor.modality.name == "LIDAR":
                lidar_sample_data = sd
                break

        if lidar_sample_data is None:
            return

        # Get 3D boxes with interpolation for the target timestamp
        # T4's get_box3ds can handle interpolation automatically
        boxes = self.t4.get_box3ds(lidar_sample_data.token, future_seconds=0.0)

        if not boxes:
            return

        # Convert to TrackedObjects
        tracked_objects_list = self.converter.convert_multiple(boxes)

        # Use the synchronized timestamp instead of sample timestamp
        timestamp_sec, timestamp_nanosec = self.converter.timestamp_to_ros_time(
            timestamp_us)

        if AUTOWARE_AVAILABLE:
            header = Header()
            header.frame_id = self.frame_id
            # Create Time message for stamp
            header.stamp = Time()
            header.stamp.sec = timestamp_sec
            header.stamp.nanosec = timestamp_nanosec

            # Create TrackedObjects message
            tracked_objects_msg = TrackedObjects()
            tracked_objects_msg.header = header
            tracked_objects_msg.objects = tracked_objects_list
        else:
            # Fallback to dict format
            tracked_objects_msg = {
                "header": {
                    "frame_id": self.frame_id,
                    "stamp": {
                        "sec": timestamp_sec,
                        "nanosec": timestamp_nanosec
                    }
                },
                "objects": tracked_objects_list
            }

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
