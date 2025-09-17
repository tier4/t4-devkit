"""ROS bag writer interface for T4 to ROS bag conversion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import rclpy
    from rclpy.serialization import serialize_message
    from rosbag2_py import SequentialWriter, SequentialReader, StorageOptions, ConverterOptions, TopicMetadata
    from autoware_perception_msgs.msg import TrackedObjects
    ROSBAG2_AVAILABLE = True
except ImportError:
    ROSBAG2_AVAILABLE = False
    print("Warning: rosbag2_py not available. Please source your ROS2/Autoware workspace.")


class RosbagWriter:
    """ROS bag writer that creates actual .bag files and copies all topics from source bag.

    This writer can:
    1. Copy all topics from an existing source ROS bag
    2. Add new topics (like tracked objects from T4 annotations)
    3. Create proper .bag files using rosbag2_py
    4. Fallback to JSON format if rosbag2_py is not available
    """

    def __init__(self, output_path: str | Path, source_bag_path: Optional[str | Path] = None):
        """Initialize the ROS bag writer.

        Args:
            output_path: Path to output the bag data.
            source_bag_path: Optional path to source bag to copy topics from.
        """
        self.output_path = Path(output_path)
        self.source_bag_path = Path(source_bag_path) if source_bag_path else None
        self.messages: List[Dict[str, Any]] = []
        self.topic_info: Dict[str, Dict[str, str]] = {}
        self.writer = None
        self.use_rosbag2 = ROSBAG2_AVAILABLE and str(output_path).endswith(('.bag', '.mcap', '.db3'))
        self.annotation_topics = []  # Track which topics are our annotations

        if self.use_rosbag2:
            self._setup_rosbag2_writer()

    def _setup_rosbag2_writer(self):
        """Setup rosbag2 writer for actual bag file creation."""
        if not ROSBAG2_AVAILABLE:
            return

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup storage and converter options for a new bag
        storage_options = StorageOptions(
            uri=str(self.output_path.with_suffix('')),  # rosbag2 adds extension
            storage_id='mcap'  # Use MCAP format
        )

        converter_options = ConverterOptions(
            input_serialization_format='cdr',
            output_serialization_format='cdr'
        )

        self.writer = SequentialWriter()
        self.writer.open(storage_options, converter_options)
        
        # If there's a source bag, we'll copy its messages in __enter__
        if self.source_bag_path and self.source_bag_path.exists():
            self.need_to_copy_source = True
        else:
            self.need_to_copy_source = False

    def add_topic(self, topic_name: str, message_type: str, frame_id: str = "base_link"):
        """Register a topic for publishing messages.

        Args:
            topic_name: Name of the ROS topic.
            message_type: Type of ROS message (e.g., 'autoware_perception_msgs/TrackedObjects').
            frame_id: Frame ID for the messages.
        """
        self.topic_info[topic_name] = {"message_type": message_type, "frame_id": frame_id}
        self.annotation_topics.append(topic_name)  # Track this as an annotation topic

        if self.use_rosbag2:
            self._add_rosbag2_topic(topic_name, message_type)

    def _add_rosbag2_topic(self, topic_name: str, message_type: str, serialization_format: str = 'cdr'):
        """Add a topic to the rosbag2 writer."""
        if not self.writer:
            return

        topic_metadata = TopicMetadata(
            name=topic_name,
            type=message_type,
            serialization_format=serialization_format
        )

        self.writer.create_topic(topic_metadata)

    def write_tracked_objects(
        self,
        topic_name: str,
        tracked_objects: TrackedObjects,
        timestamp_sec: int,
        timestamp_nanosec: int,
    ) -> None:
        """Write TrackedObjects message to the bag.

        Args:
            topic_name: Name of the topic to publish to.
            tracked_objects: TrackedObjects message to write.
            timestamp_sec: Timestamp seconds.
            timestamp_nanosec: Timestamp nanoseconds.
        """
        if self.use_rosbag2:
            self._write_tracked_objects_rosbag2(topic_name, tracked_objects, timestamp_sec, timestamp_nanosec)
        else:
            self._write_tracked_objects_json(topic_name, tracked_objects, timestamp_sec, timestamp_nanosec)

    def _write_tracked_objects_rosbag2(
        self,
        topic_name: str,
        tracked_objects: TrackedObjects,
        timestamp_sec: int,
        timestamp_nanosec: int,
    ) -> None:
        """Write TrackedObjects to rosbag2 format."""
        try:
            # Calculate timestamp in nanoseconds since epoch
            timestamp_ns = timestamp_sec * 1_000_000_000 + timestamp_nanosec

            # Use proper ROS2 serialization
            serialized_data = serialize_message(tracked_objects)
            self.writer.write(topic_name, serialized_data, timestamp_ns)

        except Exception as e:
            print(f"Error writing tracked objects to rosbag2: {e}")
            # Fallback to JSON method
            self._write_tracked_objects_json(topic_name, tracked_objects, timestamp_sec, timestamp_nanosec)

    def _write_tracked_objects_json(
        self,
        topic_name: str,
        tracked_objects,
        timestamp_sec: int,
        timestamp_nanosec: int,
    ) -> None:
        """Write TrackedObjects to JSON format (fallback)."""
        # Handle both dict and message object formats
        if isinstance(tracked_objects, dict):
            message_content = tracked_objects
        else:
            # It's a real TrackedObject message
            message_content = {
                "header": {
                    "stamp": {
                        "sec": tracked_objects.header.stamp.sec,
                        "nanosec": tracked_objects.header.stamp.nanosec,
                    },
                    "frame_id": tracked_objects.header.frame_id,
                },
                "objects": [self._serialize_tracked_object(obj) for obj in tracked_objects.objects],
            }
        
        message_data = {
            "topic": topic_name,
            "timestamp": {"sec": timestamp_sec, "nanosec": timestamp_nanosec},
            "message": message_content,
        }

        self.messages.append(message_data)

    def _serialize_tracked_object(self, obj) -> Dict[str, Any]:
        """Serialize a TrackedObject to dictionary format.

        Args:
            obj: TrackedObject to serialize (can be dict or message).

        Returns:
            Dictionary representation.
        """
        # If it's already a dict, return it
        if isinstance(obj, dict):
            return obj
            
        # Otherwise serialize the message object
        return {
            "object_id": {"uuid": obj.object_id.uuid},
            "existence_probability": obj.existence_probability,
            "classification": [
                {"label": cls.label, "probability": cls.probability} for cls in obj.classification
            ],
            "kinematics": {
                "pose_with_covariance": {
                    "pose": {
                        "position": {
                            "x": obj.kinematics.pose_with_covariance.pose.position.x,
                            "y": obj.kinematics.pose_with_covariance.pose.position.y,
                            "z": obj.kinematics.pose_with_covariance.pose.position.z,
                        },
                        "orientation": {
                            "x": obj.kinematics.pose_with_covariance.pose.orientation.x,
                            "y": obj.kinematics.pose_with_covariance.pose.orientation.y,
                            "z": obj.kinematics.pose_with_covariance.pose.orientation.z,
                            "w": obj.kinematics.pose_with_covariance.pose.orientation.w,
                        },
                    },
                    "covariance": obj.kinematics.pose_with_covariance.covariance,
                },
                "twist_with_covariance": {
                    "twist": {
                        "linear": {
                            "x": obj.kinematics.twist_with_covariance.twist.linear.x,
                            "y": obj.kinematics.twist_with_covariance.twist.linear.y,
                            "z": obj.kinematics.twist_with_covariance.twist.linear.z,
                        },
                        "angular": {
                            "x": obj.kinematics.twist_with_covariance.twist.angular.x,
                            "y": obj.kinematics.twist_with_covariance.twist.angular.y,
                            "z": obj.kinematics.twist_with_covariance.twist.angular.z,
                        },
                    },
                    "covariance": obj.kinematics.twist_with_covariance.covariance,
                },
                "acceleration_with_covariance": {
                    "accel": {
                        "linear": {
                            "x": obj.kinematics.acceleration_with_covariance.accel.linear.x,
                            "y": obj.kinematics.acceleration_with_covariance.accel.linear.y,
                            "z": obj.kinematics.acceleration_with_covariance.accel.linear.z,
                        },
                        "angular": {
                            "x": obj.kinematics.acceleration_with_covariance.accel.angular.x,
                            "y": obj.kinematics.acceleration_with_covariance.accel.angular.y,
                            "z": obj.kinematics.acceleration_with_covariance.accel.angular.z,
                        },
                    },
                    "covariance": obj.kinematics.acceleration_with_covariance.covariance,
                },
                "orientation_availability": obj.kinematics.orientation_availability,
                "is_stationary": obj.kinematics.is_stationary,
            },
            "shape": {
                "type": obj.shape.type,
                "dimensions": {
                    "x": obj.shape.dimensions.x,
                    "y": obj.shape.dimensions.y,
                    "z": obj.shape.dimensions.z,
                },
                "footprint": {
                    "points": [
                        {"x": point.x, "y": point.y, "z": point.z}
                        for point in obj.shape.footprint.points
                    ]
                },
            },
        }

    def write_metadata(self) -> None:
        """Write metadata about topics and message types."""
        metadata = {
            "topics": self.topic_info,
            "message_count": len(self.messages),
            "format_version": "1.0",
            "description": "T4 dataset converted to ROS bag format",
        }

        metadata_path = self.output_path.parent / f"{self.output_path.stem}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def finalize(self) -> None:
        """Write all messages to output file and create metadata."""
        if self.use_rosbag2:
            self._finalize_rosbag2()
        else:
            self._finalize_json()

    def _finalize_rosbag2(self) -> None:
        """Finalize rosbag2 writer."""
        if not self.writer:
            return

        # Close the writer
        self.writer.close()

        print(f"Created ROS bag: {self.output_path}")
        if self.source_bag_path:
            print(f"Copied all topics from: {self.source_bag_path}")
        print(f"Added {len([t for t in self.topic_info.keys()])} new topics")

    def _finalize_json(self) -> None:
        """Finalize JSON writer (fallback)."""
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sort messages by timestamp
        self.messages.sort(key=lambda x: (x["timestamp"]["sec"], x["timestamp"]["nanosec"]))

        # Write messages to JSON file
        with open(self.output_path, "w") as f:
            json.dump(self.messages, f, indent=2)

        # Write metadata
        self.write_metadata()

        print(f"Wrote {len(self.messages)} messages to {self.output_path}")
        print(
            f"Metadata written to {self.output_path.parent}/{self.output_path.stem}_metadata.json"
        )

    def merge_and_write_all_messages(self, annotation_messages: list, topic_name: str = None):
        """Merge source bag messages with annotation messages and write chronologically.
        
        Args:
            annotation_messages: List of tuples (timestamp_ns, tracked_objects_msg)
            topic_name: Topic name for annotation messages
        """
        if not self.source_bag_path or not self.use_rosbag2:
            # No source bag, just write annotations
            for timestamp_ns, msg in annotation_messages:
                serialized_data = serialize_message(msg)
                # Use the topic_name from annotation_topics if not provided
                if not topic_name and self.annotation_topics:
                    topic_name = self.annotation_topics[0]
                self.writer.write(topic_name, serialized_data, timestamp_ns)
            return
            
        try:
            # Setup reader for source bag
            if self.source_bag_path.is_dir():
                uri = str(self.source_bag_path)
            else:
                # For .db3 files, use the parent directory (where metadata.yaml is)
                uri = str(self.source_bag_path.parent)
                
            storage_options = StorageOptions(
                uri=uri,
                storage_id=''  # Auto-detect
            )
            
            converter_options = ConverterOptions(
                input_serialization_format='cdr',
                output_serialization_format='cdr'
            )
            
            reader = SequentialReader()
            reader.open(storage_options, converter_options)
            
            # First, register all topics
            topic_types = reader.get_all_topics_and_types()
            for topic_metadata in topic_types:
                if topic_metadata.name not in self.annotation_topics:
                    self._add_rosbag2_topic(
                        topic_metadata.name,
                        topic_metadata.type,
                        topic_metadata.serialization_format
                    )
            
            # Read all source messages into a list
            source_messages = []
            while reader.has_next():
                (topic, data, timestamp) = reader.read_next()
                if topic not in self.annotation_topics:
                    source_messages.append((timestamp, topic, data))
            
            print(f"Read {len(source_messages)} messages from source bag")
            
            # Convert annotation messages to same format
            annotation_tuples = []
            # Use the topic_name from annotation_topics if not provided
            if not topic_name and self.annotation_topics:
                topic_name = self.annotation_topics[0]
            for timestamp_ns, msg in annotation_messages:
                serialized_data = serialize_message(msg)
                annotation_tuples.append((timestamp_ns, topic_name, serialized_data))
            
            print(f"Prepared {len(annotation_tuples)} annotation messages")
            
            # Merge and sort all messages by timestamp
            all_messages = source_messages + annotation_tuples
            all_messages.sort(key=lambda x: x[0])
            
            print(f"Writing {len(all_messages)} total messages in chronological order...")
            
            # Write all messages in chronological order
            for timestamp, topic, data in all_messages:
                self.writer.write(topic, data, timestamp)
            
            print(f"Successfully wrote all messages")
            
        except Exception as e:
            print(f"Error merging messages: {e}")
            raise
    
    def _copy_source_bag_messages(self):
        """Copy all messages and topics from source bag."""
        if not self.source_bag_path or not self.use_rosbag2:
            return
            
        try:
            # Setup reader for source bag
            if self.source_bag_path.is_dir():
                uri = str(self.source_bag_path)
            else:
                # For .db3 files, use the parent directory (where metadata.yaml is)
                uri = str(self.source_bag_path.parent)
                
            storage_options = StorageOptions(
                uri=uri,
                storage_id=''  # Auto-detect
            )
            
            converter_options = ConverterOptions(
                input_serialization_format='cdr',
                output_serialization_format='cdr'
            )
            
            reader = SequentialReader()
            reader.open(storage_options, converter_options)
            
            # First, register all topics from source bag
            topic_types = reader.get_all_topics_and_types()
            for topic_metadata in topic_types:
                # Skip if it's our annotation topic (we'll add it separately)
                if topic_metadata.name not in self.annotation_topics:
                    self._add_rosbag2_topic(
                        topic_metadata.name,
                        topic_metadata.type,
                        topic_metadata.serialization_format
                    )
            
            # Now copy all messages
            message_count = 0
            while reader.has_next():
                (topic, data, timestamp) = reader.read_next()
                # Skip if it's our annotation topic (in case of re-running)
                if topic not in self.annotation_topics:
                    self.writer.write(topic, data, timestamp)
                    message_count += 1
                    
            # reader doesn't need explicit close in rosbag2_py
            print(f"Copied {message_count} messages from source bag: {self.source_bag_path}")
            
        except Exception as e:
            print(f"Error copying source bag: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        # Copy source bag messages if needed
        if hasattr(self, 'need_to_copy_source') and self.need_to_copy_source:
            self._copy_source_bag_messages()
        return self

    def copy_message(self, topic: str, data: bytes, timestamp_ns: int) -> None:
        """Copy a raw message from source bag to output bag.

        Args:
            topic: Topic name
            data: Serialized message data
            timestamp_ns: Timestamp in nanoseconds
        """
        if self.use_rosbag2 and self.writer:
            self.writer.write(topic, data, timestamp_ns)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically finalize."""
        self.finalize()
