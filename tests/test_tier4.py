from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from t4_devkit.dataclass import Box2D, Box3D, SemanticLabel
from t4_devkit.schema import SchemaName
from t4_devkit.tier4 import DBMetadata, Tier4, load_metadata, load_table
from t4_devkit.typing import Quaternion


@pytest.fixture(scope="session")
def sample_dataset_path() -> Path:
    return Path(__file__).parent / "sample/t4dataset"


class TestDBMetadata:
    """Test cases for DBMetadata class."""

    def test_db_metadata_creation(self):
        """Test DBMetadata instantiation."""
        metadata = DBMetadata(
            data_root="/path/to/data",
            dataset_id="test_dataset",
            version="1",
        )

        assert metadata.data_root == "/path/to/data"
        assert metadata.dataset_id == "test_dataset"
        assert metadata.version == "1"


class TestLoadMetadata:
    """Test cases for load_metadata function."""

    def test_load_metadata_with_status_file(self, sample_dataset_path):
        """Test loading metadata when status.json exists."""
        if not sample_dataset_path.exists():
            pytest.skip("Sample dataset not available")

        metadata = load_metadata(sample_dataset_path.as_posix())

        assert metadata.data_root == sample_dataset_path.as_posix()
        assert metadata.dataset_id == "t4dataset"
        assert metadata.version is None

    def test_load_metadata_without_status_file(self, tmp_path):
        """Test loading metadata when status.json doesn't exist."""
        with patch("os.path.exists", return_value=False):
            metadata = load_metadata(str(tmp_path), None)

            assert metadata.data_root == str(tmp_path)
            assert metadata.dataset_id == tmp_path.name
            assert metadata.version is None

    def test_load_metadata_with_specific_revision(self, tmp_path):
        """Test loading metadata with specific revision."""
        metadata = load_metadata(str(tmp_path), "v2.0.0")

        # When revision is specified, it's appended to the data_root
        expected_path = str(tmp_path / "v2.0.0")
        assert metadata.data_root == expected_path
        assert metadata.version == "v2.0.0"


class TestLoadTable:
    """Test cases for load_table function."""

    def test_load_table_success(self, sample_dataset_path):
        """Test successful table loading."""
        if not sample_dataset_path.exists():
            pytest.skip("Sample dataset not available")

        # Create a dummy annotation file
        annotation_dir = sample_dataset_path.joinpath("annotation")

        result = load_table(annotation_dir.as_posix(), SchemaName.ATTRIBUTE)

        # The result should be the return value of the schema class, not its length
        assert isinstance(result, list)

    def test_load_table_file_not_exists(self, tmp_path):
        """Test table loading when file doesn't exist for optional schema."""
        annotation_dir = tmp_path / "annotation"
        annotation_dir.mkdir()

        # Use an optional schema for this test (keypoint is actually optional)
        result = load_table(str(annotation_dir), SchemaName.KEYPOINT)
        assert result == []


class TestTier4:
    """Comprehensive integration tests using the sample T4 dataset.

    This test class provides comprehensive integration tests that use the real sample T4 dataset
    located in tests/sample to verify end-to-end functionality of the Tier4 class.

    These tests focus on real data validation instead of mocked objects:
    - Using real data files instead of mocked objects
    - Testing complete workflows from data loading to visualization
    - Verifying data consistency across the entire schema
    - Testing performance with realistic data sizes
    """

    @pytest.fixture(scope="class")
    def sample_t4(self):
        """Create a Tier4 instance using the real sample dataset."""
        sample_dataset_path = Path(__file__).parent / "sample/t4dataset"
        if not sample_dataset_path.exists():
            pytest.skip("Sample dataset not available")
        return Tier4(sample_dataset_path.as_posix(), verbose=False)

    def test_dataset_structure_validation(self, sample_t4):
        """Validate the complete structure of the sample dataset."""
        t4 = sample_t4

        # Verify expected data counts from status.json
        assert len(t4.scene) == 1, "Expected exactly 1 scene"
        assert len(t4.sample) == 3, "Expected exactly 3 samples"
        assert len(t4.sample_data) == 9, "Expected exactly 9 sample data entries"
        assert len(t4.category) == 4, "Expected exactly 4 categories"
        assert len(t4.sensor) == 3, "Expected exactly 3 sensors"
        assert len(t4.instance) >= 3, "Expected at least 3 instances"

        # Verify sensor modalities
        sensor_modalities = {sensor.modality for sensor in t4.sensor}
        expected_modalities = {"lidar", "camera"}
        assert (
            sensor_modalities == expected_modalities
        ), f"Expected {expected_modalities}, got {sensor_modalities}"

        # Verify camera count
        camera_count = sum(1 for sensor in t4.sensor if sensor.modality == "camera")
        lidar_count = sum(1 for sensor in t4.sensor if sensor.modality == "lidar")
        assert camera_count == 2, "Expected 2 cameras"
        assert lidar_count == 1, "Expected 1 LiDAR"

    def test_schema_reference_integrity(self, sample_t4):
        """Test that all cross-schema references are valid."""
        t4 = sample_t4

        # Test sample -> scene references
        for sample in t4.sample:
            _ = t4.get("scene", sample.scene_token)

        # Test sample_data -> sample references
        for sample_data in t4.sample_data:
            _ = t4.get("sample", sample_data.sample_token)

            # Test calibrated_sensor reference
            _ = t4.get("calibrated_sensor", sample_data.calibrated_sensor_token)

            # Test ego_pose reference
            _ = t4.get("ego_pose", sample_data.ego_pose_token)

        # Test sample_annotation references
        for annotation in t4.sample_annotation:
            # Test sample reference
            _ = t4.get("sample", annotation.sample_token)

            # Test instance reference
            _ = t4.get("instance", annotation.instance_token)

            # Test visibility reference
            _ = t4.get("visibility", annotation.visibility_token)

        # Test instance -> category references
        for instance in t4.instance:
            _ = t4.get("category", instance.category_token)

    def test_complete_sample_processing_workflow(self, sample_t4):
        """Test complete workflow from sample to rendered data."""
        t4 = sample_t4

        # Process each sample
        for sample in t4.sample:
            # Get all sample data for this sample
            sample_data_list = [sd for sd in t4.sample_data if sd.sample_token == sample.token]
            assert len(sample_data_list) > 0, f"No sample data found for sample {sample.token}"

            # Process each sensor type
            for sample_data in sample_data_list:
                # Get sensor information
                calibrated_sensor = t4.get("calibrated_sensor", sample_data.calibrated_sensor_token)
                sensor = t4.get("sensor", calibrated_sensor.sensor_token)

                # Test sample data retrieval
                path, boxes, intrinsic = t4.get_sample_data(sample_data.token)
                assert isinstance(path, str), "Sample data path should be string"
                assert isinstance(boxes, list), "Boxes should be a list"

                # Verify sensor-specific properties
                if sensor.modality == "camera":
                    assert intrinsic is not None, "Camera should have intrinsic matrix"
                    assert sample_data.width > 0, "Camera should have width"
                    assert sample_data.height > 0, "Camera should have height"
                elif sensor.modality == "lidar":
                    assert intrinsic is None, "LiDAR should not have intrinsic matrix"

                # Test file path construction
                expected_path = os.path.join(t4.data_root, sample_data.filename)
                assert path == expected_path, f"Path mismatch: {path} != {expected_path}"

    def test_annotation_processing_workflows(self, sample_t4):
        """Test complete annotation processing workflows."""
        t4 = sample_t4

        # Test 3D annotation workflow
        for annotation in t4.sample_annotation:
            # Create Box3D
            box3d = t4.get_box3d(annotation.token)
            assert isinstance(box3d, Box3D), "Should create valid Box3D"

            # Verify box properties
            assert len(box3d.position) == 3, "3D box should have 3D center"
            assert len(box3d.shape.size) == 3, "3D box should have 3D size"
            assert isinstance(box3d.rotation, Quaternion), "Should have quaternion orientation"

            # Verify semantic label
            assert hasattr(box3d, "semantic_label"), "Box should have semantic label"
            assert isinstance(box3d.semantic_label, SemanticLabel), "Label should be SemanticLabel"

            # Test velocity calculation
            velocity = t4.box_velocity(annotation.token)
            assert isinstance(velocity, np.ndarray), "Velocity should be numpy array"
            assert len(velocity) == 3, "Velocity should be 3D vector"

        # Test 2D annotation workflow
        for object_ann in t4.object_ann:
            # Create Box2D
            box2d = t4.get_box2d(object_ann.token)
            assert isinstance(box2d, Box2D), "Should create valid Box2D"

            # Verify box properties
            if box2d.roi:
                assert len(box2d.roi) == 4, "2D box ROI should have 4 elements"

            # Verify semantic label
            assert hasattr(box2d, "semantic_label"), "Box should have semantic label"
            assert isinstance(box2d.semantic_label, SemanticLabel), "Label should be SemanticLabel"

    def test_keyframe_data_retrieval(self, sample_t4):
        """Test keyframe-specific data retrieval."""
        t4 = sample_t4

        for sample in t4.sample:
            # Get sample data for this keyframe
            keyframe_sample_data = [
                sd for sd in t4.sample_data if sd.sample_token == sample.token and sd.is_key_frame
            ]

            # Test 3D boxes for keyframe using sample data
            for sample_data in keyframe_sample_data:
                calibrated_sensor = t4.get("calibrated_sensor", sample_data.calibrated_sensor_token)
                sensor = t4.get("sensor", calibrated_sensor.sensor_token)

                if sensor.modality == "lidar":
                    boxes_3d = t4.get_box3ds(sample_data.token)
                    assert isinstance(boxes_3d, list), "Should return list of 3D boxes"

                    # Verify all boxes are valid
                    for box in boxes_3d:
                        assert isinstance(box, Box3D), "All items should be Box3D instances"

            # Test 2D boxes for camera data
            for sample_data in keyframe_sample_data:
                calibrated_sensor = t4.get("calibrated_sensor", sample_data.calibrated_sensor_token)
                sensor = t4.get("sensor", calibrated_sensor.sensor_token)

                if sensor.modality == "camera":
                    boxes_2d = t4.get_box2ds(sample_data.token)
                    assert isinstance(boxes_2d, list), "Should return list of 2D boxes"

                    for box in boxes_2d:
                        assert isinstance(box, Box2D), "All items should be Box2D instances"

    def test_temporal_consistency(self, sample_t4):
        """Test temporal consistency across samples."""
        t4 = sample_t4

        # Sort samples by timestamp
        sorted_samples = sorted(t4.sample, key=lambda s: s.timestamp)

        # Test sample linking
        for i, sample in enumerate(sorted_samples):
            if i > 0:
                # Previous sample should link to current
                prev_sample = sorted_samples[i - 1]
                assert prev_sample.next == sample.token, "Sample linking inconsistency"
                assert sample.prev == prev_sample.token, "Sample linking inconsistency"

            if i < len(sorted_samples) - 1:
                # Current sample should link to next
                next_sample = sorted_samples[i + 1]
                assert sample.next == next_sample.token, "Sample linking inconsistency"

        # Test annotation temporal consistency
        for annotation in t4.sample_annotation:
            if annotation.next:
                next_ann = t4.get("sample_annotation", annotation.next)
                assert next_ann.prev == annotation.token, "Annotation linking inconsistency"
                assert (
                    next_ann.instance_token == annotation.instance_token
                ), "Same instance should be tracked"

    def test_coordinate_system_consistency(self, sample_t4):
        """Test coordinate system consistency across sensors."""
        t4 = sample_t4

        for sample_data in t4.sample_data:
            calibrated_sensor = t4.get("calibrated_sensor", sample_data.calibrated_sensor_token)
            ego_pose = t4.get("ego_pose", sample_data.ego_pose_token)

            # Verify coordinate transformations exist
            assert hasattr(
                calibrated_sensor, "translation"
            ), "Calibrated sensor should have translation"
            assert hasattr(calibrated_sensor, "rotation"), "Calibrated sensor should have rotation"
            assert hasattr(ego_pose, "translation"), "Ego pose should have translation"
            assert hasattr(ego_pose, "rotation"), "Ego pose should have rotation"

            # Verify coordinate dimensions
            assert len(calibrated_sensor.translation) == 3, "Translation should be 3D"
            assert isinstance(
                calibrated_sensor.rotation, Quaternion
            ), "Rotation should be quaternion"
            assert len(ego_pose.translation) == 3, "Translation should be 3D"
            assert isinstance(ego_pose.rotation, Quaternion), "Rotation should be quaternion"

    def test_rendering_methods_integration(self, sample_t4):
        """Test that rendering methods work with real data (without actually rendering)."""
        t4 = sample_t4

        # Test that methods exist and are callable
        assert hasattr(t4, "render_scene") and callable(t4.render_scene)
        assert hasattr(t4, "render_instance") and callable(t4.render_instance)
        assert hasattr(t4, "render_pointcloud") and callable(t4.render_pointcloud)

        # We don't actually call these methods to avoid opening GUI windows
        # but we can test that the data they would need is available

        # For render_scene: need sample data
        assert len(t4.sample_data) > 0, "Need sample data for scene rendering"

        # For render_instance: need instances and annotations
        assert len(t4.instance) > 0, "Need instances for instance rendering"
        assert len(t4.sample_annotation) > 0, "Need annotations for instance rendering"

        # For render_pointcloud: need LiDAR data
        lidar_data = []
        for sd in t4.sample_data:
            calibrated_sensor = t4.get("calibrated_sensor", sd.calibrated_sensor_token)
            sensor = t4.get("sensor", calibrated_sensor.sensor_token)
            if sensor.modality == "lidar":
                lidar_data.append(sd)
        assert len(lidar_data) > 0, "Need LiDAR data for pointcloud rendering"

    def test_semantic_label_consistency(self, sample_t4):
        """Test semantic label consistency across annotations."""
        t4 = sample_t4

        # Test semantic labels for all categories
        category_labels = {}
        for category in t4.category:
            semantic_label = t4.get_semantic_label(category.token)
            assert isinstance(semantic_label, SemanticLabel), "Should create valid SemanticLabel"
            assert semantic_label.name == category.name, "Label name should match category name"
            category_labels[category.token] = semantic_label

        # Verify consistency in annotations
        for annotation in t4.sample_annotation:
            instance = t4.get("instance", annotation.instance_token)
            category = t4.get("category", instance.category_token)
            expected_label = category_labels[category.token]

            # Create box and verify label
            box3d = t4.get_box3d(annotation.token)
            assert (
                box3d.semantic_label.name == expected_label.name
            ), "Box label should match category"

    def test_error_handling_with_real_data(self, sample_t4):
        """Test error handling with real data scenarios."""
        t4 = sample_t4

        # Test invalid token handling
        with pytest.raises(KeyError):
            t4.get("sample", "invalid_token")

        # Test invalid schema handling
        with pytest.raises((KeyError, ValueError)):
            t4.get("invalid_schema", t4.sample[0].token)

        # Test invalid sample data token
        with pytest.raises(KeyError):
            t4.get_sample_data("invalid_sample_data_token")

        # Test invalid annotation token
        if t4.sample_annotation:
            with pytest.raises(KeyError):
                t4.get_box3d("invalid_annotation_token")

    def test_data_file_paths(self, sample_t4):
        """Test that data file paths are correctly constructed."""
        t4 = sample_t4

        for sample_data in t4.sample_data:
            # Test path construction
            path = t4.get_sample_data_path(sample_data.token)

            # Should be absolute path
            assert os.path.isabs(path), f"Path should be absolute: {path}"

            # Should start with data root
            assert path.startswith(t4.data_root), f"Path should start with data root: {path}"

            # Should end with expected file extension
            expected_extensions = [".jpg", ".png", ".pcd.bin", ".bin"]
            assert any(
                path.endswith(ext) for ext in expected_extensions
            ), f"Unexpected file extension: {path}"

            # Should match the filename in sample_data
            expected_path = os.path.join(t4.data_root, sample_data.filename)
            assert path == expected_path, f"Path mismatch: {path} != {expected_path}"

    def test_complete_integration_workflow(self, sample_t4):
        """Test a complete end-to-end workflow using the sample dataset."""
        t4 = sample_t4

        # Start with scene
        scene = t4.scene[0]
        assert scene.name == "minimal_test_scene"

        # Get first sample
        first_sample = t4.get("sample", scene.first_sample_token)
        assert first_sample is not None

        # Get all sample data for first sample
        sample_data_list = [sd for sd in t4.sample_data if sd.sample_token == first_sample.token]
        assert len(sample_data_list) > 0

        # Process camera data
        camera_data = None
        for sd in sample_data_list:
            calibrated_sensor = t4.get("calibrated_sensor", sd.calibrated_sensor_token)
            sensor = t4.get("sensor", calibrated_sensor.sensor_token)
            if sensor.modality == "camera":
                camera_data = sd
                break

        if camera_data:
            # Get camera sample data
            path, boxes, intrinsic = t4.get_sample_data(camera_data.token)
            assert path.endswith(".jpg")
            assert intrinsic is not None

            # Get 2D boxes for this camera
            boxes_2d = t4.get_box2ds(camera_data.token)
            assert isinstance(boxes_2d, list)

        # Process LiDAR data
        lidar_data = None
        for sd in sample_data_list:
            calibrated_sensor = t4.get("calibrated_sensor", sd.calibrated_sensor_token)
            sensor = t4.get("sensor", calibrated_sensor.sensor_token)
            if sensor.modality == "lidar":
                lidar_data = sd
                break

        if lidar_data:
            # Get LiDAR sample data
            path, boxes, intrinsic = t4.get_sample_data(lidar_data.token)
            assert path.endswith((".pcd.bin", ".bin"))
            assert intrinsic is None

        # Get 3D boxes for this sample using LiDAR data
        boxes_3d = []
        if lidar_data:
            boxes_3d = t4.get_box3ds(lidar_data.token)
            assert isinstance(boxes_3d, list)

            # Process each 3D box
            for box in boxes_3d:
                assert isinstance(box, Box3D)
                assert hasattr(box, "semantic_label")
                assert isinstance(box.semantic_label, SemanticLabel)
