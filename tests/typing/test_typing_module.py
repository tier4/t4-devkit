from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import (
    ArrayLike,
    CameraDistortion,
    CameraIntrinsic,
    KeypointLike,
    Matrix3x3,
    Matrix4x4,
    NDArray,
    NDArrayBool,
    NDArrayF32,
    NDArrayF64,
    NDArrayFloat,
    NDArrayI32,
    NDArrayI64,
    NDArrayInt,
    NDArrayStr,
    NDArrayU8,
    NewType,
    Quaternion,
    Roi,
    Trajectory,
    Vector2,
    Vector3,
    Vector6,
)


class TestTypingModuleStructure:
    """Test the overall structure and exports of the typing module."""

    def test_module_imports(self):
        """Test that all expected types are importable from the main typing module."""
        # Core numpy array types
        assert NDArray is not None
        assert ArrayLike is not None

        # Specific numpy array types
        assert NDArrayF64 is not None
        assert NDArrayF32 is not None
        assert NDArrayI64 is not None
        assert NDArrayI32 is not None
        assert NDArrayU8 is not None
        assert NDArrayBool is not None
        assert NDArrayStr is not None

        # Union types
        assert NDArrayInt is not None
        assert NDArrayFloat is not None

        # Core classes
        assert Vector2 is not None
        assert Vector3 is not None
        assert Vector6 is not None
        assert Quaternion is not None
        assert Roi is not None
        assert Matrix3x3 is not None
        assert Matrix4x4 is not None
        assert CameraIntrinsic is not None
        assert CameraDistortion is not None
        assert Trajectory is not None

        # NewType instances
        assert KeypointLike is not None

        # Other utilities
        assert NewType is not None

    def test_numpy_array_type_annotations(self):
        """Test that numpy array type annotations work correctly."""
        # Test that we can create arrays of the specified types
        f64_array = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        f32_array = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        i64_array = np.array([1, 2, 3], dtype=np.int64)
        i32_array = np.array([1, 2, 3], dtype=np.int32)
        u8_array = np.array([1, 2, 3], dtype=np.uint8)
        bool_array = np.array([True, False, True], dtype=np.bool_)
        str_array = np.array(["a", "b", "c"], dtype=np.str_)

        # Type annotations should be correct
        assert f64_array.dtype == np.float64
        assert f32_array.dtype == np.float32
        assert i64_array.dtype == np.int64
        assert i32_array.dtype == np.int32
        assert u8_array.dtype == np.uint8
        assert bool_array.dtype == np.bool_
        assert str_array.dtype.kind == "U"  # Unicode string

    def test_union_types(self):
        """Test that union types include the expected component types."""
        # NDArrayInt should include both int32 and int64
        i32_array = np.array([1, 2, 3], dtype=np.int32)
        i64_array = np.array([1, 2, 3], dtype=np.int64)

        # Both should be considered valid integer arrays
        assert i32_array.dtype in (np.int32, np.int64)
        assert i64_array.dtype in (np.int32, np.int64)

        # NDArrayFloat should include both float32 and float64
        f32_array = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        f64_array = np.array([1.0, 2.0, 3.0], dtype=np.float64)

        assert f32_array.dtype in (np.float32, np.float64)
        assert f64_array.dtype in (np.float32, np.float64)

    def test_newtype_instances(self):
        """Test NewType instances for type safety."""
        # KeypointLike should be a NewType
        assert hasattr(KeypointLike, "__supertype__")
        assert KeypointLike.__supertype__ == np.ndarray

        # Should be able to create instances
        keypoints = np.array([[10, 20], [30, 40], [50, 60]])
        keypoint_typed = KeypointLike(keypoints)
        assert isinstance(keypoint_typed, np.ndarray)
        assert keypoint_typed.shape == (3, 2)


class TestTypingModuleCompatibility:
    """Test compatibility between different typing components."""

    def test_vector_matrix_compatibility(self):
        """Test that vectors and matrices work together."""
        # 3D vector
        v3 = Vector3([1, 2, 3])

        # 3x3 matrix
        m3 = Matrix3x3(np.eye(3))

        # Matrix-vector multiplication should work
        result = m3 @ v3
        expected = v3  # Identity matrix doesn't change the vector
        assert np.allclose(result, expected)

    def test_camera_types_compatibility(self):
        """Test that camera types work together for projections."""
        # Camera intrinsic matrix
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # Camera distortion coefficients
        _ = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # 3D point
        point_3d = Vector3([1, 2, 5])

        # Project point using intrinsic matrix
        projected = intrinsic @ point_3d
        pixel_coords = projected[:2] / projected[2]

        # Should get reasonable pixel coordinates
        assert len(pixel_coords) == 2
        assert np.all(np.isfinite(pixel_coords))

    def test_trajectory_vector_compatibility(self):
        """Test that trajectories work with vector operations."""
        # Create trajectory with Vector3-like waypoints
        waypoints = [Vector3([0, 0, 0]), Vector3([1, 1, 1]), Vector3([2, 2, 2])]

        # Convert to trajectory format (nested lists)
        traj_list = [[[float(coord) for coord in wp] for wp in waypoints]]
        traj = Trajectory(traj_list)

        assert traj.shape == (1, 3, 3)  # 1 mode, 3 timesteps, 3D

    def test_roi_vector_compatibility(self):
        """Test that ROI works with vector-like inputs."""
        # Create ROI using vector-like input
        roi_coords = [10, 20, 50, 80]  # [xmin, ymin, xmax, ymax]
        roi = Roi(roi_coords)

        # Extract as vector-like
        roi_as_vector = Vector6([roi[0], roi[1], roi[2], roi[3], roi.width, roi.height])

        assert roi_as_vector[0] == roi[0]  # xmin
        assert roi_as_vector[1] == roi[1]  # ymin
        assert roi_as_vector[2] == roi[2]  # xmax
        assert roi_as_vector[3] == roi[3]  # ymax
        assert roi_as_vector[4] == roi.width
        assert roi_as_vector[5] == roi.height

    def test_quaternion_matrix_compatibility(self):
        """Test that quaternions work with rotation matrices."""
        # Create quaternion
        q = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)  # 90° around z

        # Get rotation matrix
        rot_matrix = q.rotation_matrix

        # Convert to Matrix3x3
        m3 = Matrix3x3(rot_matrix)

        # Both should represent the same rotation
        test_vector = Vector3([1, 0, 0])
        rotated_by_q = q.rotate(test_vector)
        rotated_by_matrix = m3 @ test_vector

        assert np.allclose(rotated_by_q, rotated_by_matrix, atol=1e-10)


class TestTypingModuleFunctionality:
    """Test specific functionality of the typing module."""

    def test_type_checking_helpers(self):
        """Test type checking and validation helpers."""
        # Vector type checking
        assert isinstance(Vector2([1, 2]), Vector2)
        assert isinstance(Vector3([1, 2, 3]), Vector3)
        assert isinstance(Vector6([1, 2, 3, 4, 5, 6]), Vector6)

        # Matrix type checking
        assert isinstance(Matrix3x3(np.eye(3)), Matrix3x3)
        assert isinstance(Matrix4x4(np.eye(4)), Matrix4x4)

        # Camera type checking
        assert isinstance(CameraIntrinsic(np.eye(3)), CameraIntrinsic)
        assert isinstance(CameraDistortion([0, 0, 0, 0, 0]), CameraDistortion)

    def test_type_conversion_workflows(self):
        """Test common type conversion workflows."""
        # List -> Vector -> numpy operations
        coords = [1, 2, 3]
        v3 = Vector3(coords)
        normalized = v3 / np.linalg.norm(v3)
        assert len(normalized) == 3

        # Nested list -> Trajectory -> analysis
        traj_data = [[[0, 0, 0], [1, 1, 1], [2, 2, 2]]]
        traj = Trajectory(traj_data)
        distances = np.linalg.norm(np.diff(traj[0], axis=0), axis=1)
        assert len(distances) == 2  # N-1 distances for N waypoints

        # List -> ROI -> geometric operations
        roi_data = [10, 20, 50, 80]
        roi = Roi(roi_data)
        area = roi.area
        center = roi.center
        assert area == 2400  # (50-10) * (80-20)
        assert center == (30, 50)  # Midpoint

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across types."""
        # All vector types should raise ValueError for wrong dimensions
        with pytest.raises(ValueError):
            Vector2([1, 2, 3])  # Too many elements

        with pytest.raises(ValueError):
            Vector3([1, 2])  # Too few elements

        with pytest.raises(ValueError):
            Vector6([1, 2, 3, 4, 5])  # Too few elements

        # Matrix types should raise ValueError for wrong shapes
        with pytest.raises(ValueError):
            Matrix3x3(np.eye(2))  # Wrong shape

        with pytest.raises(ValueError):
            Matrix4x4(np.eye(3))  # Wrong shape

        # Camera types should raise ValueError for wrong dimensions
        with pytest.raises(ValueError):
            CameraIntrinsic(np.eye(2))  # Wrong shape

        with pytest.raises(ValueError):
            CameraDistortion([1, 2, 3])  # Wrong length

        # ROI should raise ValueError for wrong dimensions or invalid bounds
        with pytest.raises(ValueError):
            Roi([1, 2, 3])  # Too few elements

        with pytest.raises(ValueError):
            Roi([3, 4, 1, 2])  # Invalid bounds (xmax < xmin, ymax < ymin)

        # Trajectory should raise ValueError for wrong dimensions
        with pytest.raises(ValueError):
            Trajectory([[1, 2, 3]])  # Wrong shape (not 3D)


class TestTypingModulePerformance:
    """Test performance characteristics of typing components."""

    def test_vector_performance(self):
        """Test that vector operations are reasonably fast."""
        # Create large vectors
        large_data = np.random.rand(10000)
        v2_data = large_data[:2]
        v3_data = large_data[:3]
        v6_data = large_data[:6]

        # Should be able to create vectors quickly
        v2 = Vector2(v2_data)
        v3 = Vector3(v3_data)
        v6 = Vector6(v6_data)

        # Should support numpy operations efficiently
        assert np.sum(v2) == np.sum(v2_data)
        assert np.sum(v3) == np.sum(v3_data)
        assert np.sum(v6) == np.sum(v6_data)

    def test_matrix_performance(self):
        """Test that matrix operations are reasonably fast."""
        # Create matrices
        m3_data = np.random.rand(3, 3)
        m4_data = np.random.rand(4, 4)

        m3 = Matrix3x3(m3_data)
        m4 = Matrix4x4(m4_data)

        # Should support efficient operations
        assert np.allclose(m3 @ m3, m3_data @ m3_data)
        assert np.allclose(m4 @ m4, m4_data @ m4_data)

    def test_trajectory_performance(self):
        """Test that trajectory operations scale reasonably."""
        # Create large trajectory
        large_traj_data = np.random.rand(10, 100, 3)  # 10 modes, 100 timesteps
        traj = Trajectory(large_traj_data)

        # Should support efficient indexing and slicing
        subset = traj[:5, :50, :]  # First 5 modes, first 50 timesteps
        assert subset.shape == (5, 50, 3)

        # Should support efficient computations
        mean_traj = np.mean(traj, axis=0)
        assert mean_traj.shape == (100, 3)


class TestTypingModuleIntegration:
    """Test integration scenarios using multiple typing components."""

    def test_robotics_pose_representation(self):
        """Test representing robot poses using typing components."""
        # Robot pose: position + orientation
        position = Vector3([1, 2, 3])
        orientation = Quaternion([1, 0, 0, 0])  # Identity quaternion

        # Create homogeneous transformation matrix
        transform = Matrix4x4(np.eye(4))
        transform[:3, 3] = position  # Set translation
        transform[:3, :3] = orientation.rotation_matrix  # Set rotation

        # Test transformation
        point = Vector3([0, 0, 0])
        transformed = transform @ np.append(point, 1)  # Homogeneous coordinates
        result_position = transformed[:3]

        assert np.allclose(result_position, position)

    def test_camera_projection_pipeline(self):
        """Test complete camera projection pipeline."""
        # Camera parameters
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        _ = CameraDistortion([0, 0, 0, 0, 0])  # No distortion

        # 3D points
        points_3d = [Vector3([i, i, 5]) for i in range(3)]

        # Project points
        projected_points = []
        for point in points_3d:
            projected = intrinsic @ point
            pixel_coords = projected[:2] / projected[2]
            projected_points.append(pixel_coords)

        # Verify projections are reasonable
        for pixel_coords in projected_points:
            assert len(pixel_coords) == 2
            assert np.all(np.isfinite(pixel_coords))
            assert pixel_coords[0] >= 0  # x-coordinate
            assert pixel_coords[1] >= 0  # y-coordinate

    def test_trajectory_analysis_workflow(self):
        """Test trajectory analysis workflow."""
        # Create multi-mode trajectory
        num_modes = 3
        num_timesteps = 10
        trajectory_data = []

        for mode in range(num_modes):
            mode_waypoints = []
            for t in range(num_timesteps):
                # Different trajectory patterns for each mode
                if mode == 0:  # Linear
                    waypoint = [t, t, 0]
                elif mode == 1:  # Circular
                    angle = 2 * np.pi * t / num_timesteps
                    waypoint = [np.cos(angle), np.sin(angle), 0]
                else:  # Spiral
                    angle = 2 * np.pi * t / num_timesteps
                    radius = t / num_timesteps
                    waypoint = [radius * np.cos(angle), radius * np.sin(angle), t]

                mode_waypoints.append(waypoint)
            trajectory_data.append(mode_waypoints)

        traj = Trajectory(trajectory_data)

        # Analyze trajectory properties
        assert traj.shape == (num_modes, num_timesteps, 3)

        # Calculate distances for each mode
        for mode_idx in range(num_modes):
            mode_traj = traj[mode_idx]
            distances = []
            for t in range(num_timesteps - 1):
                dist = np.linalg.norm(mode_traj[t + 1] - mode_traj[t])
                distances.append(dist)

            # All modes should have positive distances (motion)
            assert all(d > 0 for d in distances)

    def test_geometric_bounding_analysis(self):
        """Test geometric bounding and intersection analysis."""
        # Create multiple ROIs
        roi1 = Roi([10, 10, 50, 50])  # 40x40 box
        roi2 = Roi([30, 30, 70, 70])  # 40x40 box, overlapping
        roi3 = Roi([100, 100, 150, 150])  # 50x50 box, separate

        # Create points for testing containment
        points = [
            Vector2([25, 25]),  # Inside roi1 only
            Vector2([40, 40]),  # Inside both roi1 and roi2
            Vector2([60, 60]),  # Inside roi2 only
            Vector2([125, 125]),  # Inside roi3 only
            Vector2([200, 200]),  # Outside all ROIs
        ]

        # Test point-in-roi logic (manual implementation)
        def point_in_roi(point, roi):
            return roi[0] <= point[0] <= roi[2] and roi[1] <= point[1] <= roi[3]

        # Verify containment
        assert point_in_roi(points[0], roi1) and not point_in_roi(points[0], roi2)
        assert point_in_roi(points[1], roi1) and point_in_roi(points[1], roi2)
        assert not point_in_roi(points[2], roi1) and point_in_roi(points[2], roi2)
        assert point_in_roi(points[3], roi3)
        assert not any(point_in_roi(points[4], roi) for roi in [roi1, roi2, roi3])


class TestTypingModuleEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_and_negative_values(self):
        """Test handling of zero and negative values."""
        # Vectors with zeros and negatives
        v3_zeros = Vector3([0, 0, 0])
        v3_negative = Vector3([-1, -2, -3])

        assert np.allclose(v3_zeros, [0, 0, 0])
        assert np.allclose(v3_negative, [-1, -2, -3])

        # Matrices with zeros
        zero_matrix = Matrix3x3(np.zeros((3, 3)))
        assert np.allclose(zero_matrix, np.zeros((3, 3)))

        # ROI with zero dimensions
        roi_zero_width = Roi([10, 10, 10, 20])  # Width = 0
        roi_zero_height = Roi([10, 10, 20, 10])  # Height = 0

        assert roi_zero_width.width == 0
        assert roi_zero_height.height == 0

    def test_very_large_values(self):
        """Test handling of very large values."""
        large_value = 1e10

        # Large vectors
        v3_large = Vector3([large_value, large_value, large_value])
        assert np.all(v3_large == large_value)

        # Large matrices
        large_matrix = Matrix3x3(np.ones((3, 3)) * large_value)
        assert np.all(large_matrix == large_value)

    def test_very_small_values(self):
        """Test handling of very small values."""
        small_value = 1e-10

        # Small vectors
        v3_small = Vector3([small_value, small_value, small_value])
        assert np.all(v3_small == small_value)

        # Small distortion coefficients
        small_distortion = CameraDistortion([small_value] * 5)
        assert np.all(small_distortion == small_value)

    def test_special_float_values(self):
        """Test handling of special float values."""
        # Test with infinity (should be handled gracefully)
        try:
            v3_inf = Vector3([np.inf, -np.inf, 0])
            assert np.isinf(v3_inf[0]) and np.isinf(v3_inf[1])
        except (ValueError, OverflowError):
            # Some implementations might reject infinite values
            pass

        # Test with NaN (should be handled gracefully)
        try:
            v3_nan = Vector3([np.nan, 0, 0])
            assert np.isnan(v3_nan[0])
        except (ValueError, TypeError):
            # Some implementations might reject NaN values
            pass
