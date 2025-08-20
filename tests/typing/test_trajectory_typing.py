from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import Trajectory


class TestTrajectory:
    """Test cases for Trajectory class."""

    def test_creation_from_3d_list(self):
        """Test Trajectory creation from 3D list."""
        # Trajectory with 2 modes, 3 timesteps, 3D coordinates
        trajectory_data = [
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # Mode 1
            [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1], [7.1, 8.1, 9.1]],  # Mode 2
        ]
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (2, 3, 3)  # (M, T, D)
        assert np.array_equal(traj, trajectory_data)

    def test_creation_from_numpy_array(self):
        """Test Trajectory creation from numpy array."""
        trajectory_data = np.random.rand(3, 5, 3)  # 3 modes, 5 timesteps, 3D
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (3, 5, 3)
        assert np.array_equal(traj, trajectory_data)

    def test_creation_single_mode(self):
        """Test Trajectory creation with single mode."""
        # Single mode trajectory (1, T, 3)
        trajectory_data = [[[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]]]
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (1, 4, 3)
        assert np.array_equal(traj, trajectory_data)

    def test_creation_single_timestep(self):
        """Test Trajectory creation with single timestep."""
        # Multiple modes, single timestep (M, 1, 3)
        trajectory_data = [[[1, 2, 3]], [[4, 5, 6]], [[7, 8, 9]]]
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (3, 1, 3)
        assert np.array_equal(traj, trajectory_data)

    def test_creation_mixed_numeric_types(self):
        """Test Trajectory creation with mixed numeric types."""
        trajectory_data = [
            [[1, 2.5, 3], [4.0, 5, 6.2]],
            [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]],
        ]
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (2, 2, 3)
        assert traj[0, 0, 1] == 2.5
        assert traj[1, 1, 2] == 6.1

    def test_creation_large_trajectory(self):
        """Test Trajectory creation with large dimensions."""
        # Many modes, many timesteps
        trajectory_data = np.random.rand(10, 50, 3)  # 10 modes, 50 timesteps
        traj = Trajectory(trajectory_data)
        assert isinstance(traj, Trajectory)
        assert traj.shape == (10, 50, 3)

    def test_invalid_shape_2d_array(self):
        """Test that Trajectory raises ValueError for 2D array."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([[1, 2, 3], [4, 5, 6]])

    def test_invalid_shape_1d_array(self):
        """Test that Trajectory raises ValueError for 1D array."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([1, 2, 3])

    def test_invalid_shape_4d_array(self):
        """Test that Trajectory raises ValueError for 4D array."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([[[[1, 2, 3]]]])

    def test_invalid_coordinate_dimension_2d(self):
        """Test that Trajectory raises ValueError for 2D coordinates."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([[[1, 2], [3, 4], [5, 6]]])  # Only 2D coordinates

    def test_invalid_coordinate_dimension_4d(self):
        """Test that Trajectory raises ValueError for 4D coordinates."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([[[1, 2, 3, 4], [5, 6, 7, 8]]])  # 4D coordinates

    def test_invalid_empty_array(self):
        """Test that Trajectory raises ValueError for empty array."""
        with pytest.raises(ValueError, match="Trajectory must be the shape of \\(M, T, 3\\)"):
            Trajectory([])

    def test_invalid_inconsistent_timesteps(self):
        """Test that Trajectory handles inconsistent timestep dimensions."""
        # This should fail during numpy array creation or shape validation
        inconsistent_data = [
            [[1, 2, 3], [4, 5, 6]],  # 2 timesteps
            [[1, 2, 3]],  # 1 timestep
        ]
        with pytest.raises((ValueError, np.exceptions.VisibleDeprecationWarning)):
            Trajectory(inconsistent_data)

    def test_trajectory_indexing(self):
        """Test trajectory indexing and slicing."""
        trajectory_data = [
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],  # Mode 1
            [[10, 11, 12], [13, 14, 15], [16, 17, 18]],  # Mode 2
        ]
        traj = Trajectory(trajectory_data)

        # Mode indexing
        mode_0 = traj[0]
        expected_mode_0 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert np.array_equal(mode_0, expected_mode_0)

        # Specific waypoint indexing
        waypoint = traj[1, 2]  # Mode 1, timestep 2
        expected_waypoint = np.array([16, 17, 18])
        assert np.array_equal(waypoint, expected_waypoint)

        # Coordinate indexing
        z_coord = traj[0, 1, 2]  # Mode 0, timestep 1, z coordinate
        assert z_coord == 6

        # Slicing modes
        all_modes_timestep_0 = traj[:, 0]
        expected = np.array([[1, 2, 3], [10, 11, 12]])
        assert np.array_equal(all_modes_timestep_0, expected)

    def test_trajectory_properties(self):
        """Test trajectory properties."""
        traj = Trajectory(np.random.rand(4, 6, 3))

        # Shape properties
        assert traj.shape == (4, 6, 3)
        assert traj.ndim == 3
        assert traj.size == 72  # 4 * 6 * 3

        # Mode and timestep access
        num_modes, num_timesteps, num_coords = traj.shape
        assert num_modes == 4
        assert num_timesteps == 6
        assert num_coords == 3

    def test_trajectory_arithmetic_operations(self):
        """Test arithmetic operations on trajectories."""
        traj1 = Trajectory([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])
        traj2 = Trajectory([[[1, 1, 1], [2, 2, 2]], [[3, 3, 3], [4, 4, 4]]])

        # Addition
        result = traj1 + traj2
        expected = np.array([[[2, 3, 4], [6, 7, 8]], [[10, 11, 12], [14, 15, 16]]])
        assert np.array_equal(result, expected)

        # Subtraction
        result = traj1 - traj2
        expected = np.array([[[0, 1, 2], [2, 3, 4]], [[4, 5, 6], [6, 7, 8]]])
        assert np.array_equal(result, expected)

        # Scalar multiplication
        result = traj1 * 2
        expected = np.array([[[2, 4, 6], [8, 10, 12]], [[14, 16, 18], [20, 22, 24]]])
        assert np.array_equal(result, expected)

    def test_trajectory_numpy_compatibility(self):
        """Test that Trajectory works with numpy functions."""
        traj = Trajectory([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])

        # Test various numpy functions
        assert np.sum(traj) == 78  # Sum of all elements
        assert np.mean(traj) == 6.5  # Mean of all elements
        assert np.max(traj) == 12
        assert np.min(traj) == 1

        # Test array functions
        assert np.allclose(traj.T.T, traj)  # Double transpose
        assert traj.flatten().shape == (12,)

    def test_trajectory_distance_calculations(self):
        """Test distance calculations on trajectories."""
        # Simple linear trajectory
        traj = Trajectory([[[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]])

        # Calculate distances between consecutive waypoints
        waypoints = traj[0]  # Get first (and only) mode
        distances = []
        for i in range(len(waypoints) - 1):
            dist = np.linalg.norm(waypoints[i + 1] - waypoints[i])
            distances.append(dist)

        # All distances should be 1 (moving 1 unit in x direction each step)
        expected_distances = [1.0, 1.0, 1.0]
        assert np.allclose(distances, expected_distances)

    def test_trajectory_interpolation(self):
        """Test trajectory interpolation operations."""
        # Create a simple trajectory with two waypoints
        traj = Trajectory([[[0, 0, 0], [10, 10, 10]]])
        mode_0 = traj[0]

        # Linear interpolation between waypoints
        alpha = 0.5  # Midpoint
        interpolated = (1 - alpha) * mode_0[0] + alpha * mode_0[1]
        expected = np.array([5, 5, 5])  # Midpoint
        assert np.array_equal(interpolated, expected)

    def test_trajectory_transformation(self):
        """Test applying transformations to trajectories."""
        # Original trajectory
        traj = Trajectory([[[1, 0, 0], [0, 1, 0], [0, 0, 1]]])

        # Apply translation
        translation = np.array([1, 2, 3])
        translated = traj + translation

        expected = np.array([[[2, 2, 3], [1, 3, 3], [1, 2, 4]]])
        assert np.array_equal(translated, expected)

        # Apply scaling
        scale = 2.0
        scaled = traj * scale

        expected = np.array([[[2, 0, 0], [0, 2, 0], [0, 0, 2]]])
        assert np.array_equal(scaled, expected)

    def test_trajectory_mode_operations(self):
        """Test operations on different trajectory modes."""
        # Multi-mode trajectory
        traj = Trajectory(
            [
                [[0, 0, 0], [1, 1, 1], [2, 2, 2]],  # Mode 1: linear
                [[0, 0, 0], [1, 0, 0], [2, 0, 0]],  # Mode 2: x-axis only
                [[0, 0, 0], [0, 1, 0], [0, 2, 0]],  # Mode 3: y-axis only
            ]
        )

        # Extract individual modes
        linear_mode = traj[0]
        x_mode = traj[1]
        y_mode = traj[2]

        # Verify mode properties
        assert linear_mode.shape == (3, 3)
        assert x_mode.shape == (3, 3)
        assert y_mode.shape == (3, 3)

        # Check that modes have different patterns
        assert not np.array_equal(linear_mode, x_mode)
        assert not np.array_equal(x_mode, y_mode)

    def test_trajectory_temporal_analysis(self):
        """Test temporal analysis of trajectories."""
        # Create trajectory with time-varying pattern
        t = np.linspace(0, 2 * np.pi, 10)
        circular_trajectory = np.stack([np.cos(t), np.sin(t), np.zeros_like(t)], axis=1)
        traj = Trajectory([circular_trajectory])

        # Extract positions at different times
        start_pos = traj[0, 0]  # t=0
        quarter_pos = traj[0, len(t) // 4]  # t=π/2
        half_pos = traj[0, len(t) // 2]  # t=π

        # Verify circular motion properties
        # At t=0: should be approximately [1, 0, 0]
        assert abs(start_pos[0] - 1.0) < 0.1
        assert abs(start_pos[1]) < 0.1

        # At t=π/2: should be approximately [0, 1, 0]
        assert abs(quarter_pos[0]) < 0.5
        assert abs(quarter_pos[1] - 1.0) < 0.5

        # At t=π: should be approximately [-1, 0, 0]
        assert abs(half_pos[0] + 1.0) < 0.5
        assert abs(half_pos[1]) < 0.5

    def test_trajectory_velocity_calculation(self):
        """Test velocity calculation from trajectories."""
        # Linear motion trajectory
        traj = Trajectory([[[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]]])
        waypoints = traj[0]

        # Calculate velocities (finite differences)
        velocities = []
        for i in range(len(waypoints) - 1):
            velocity = waypoints[i + 1] - waypoints[i]
            velocities.append(velocity)

        # Constant velocity should be [1, 1, 1] for each step
        expected_velocity = np.array([1, 1, 1])
        for vel in velocities:
            assert np.allclose(vel, expected_velocity)

    def test_trajectory_equality(self):
        """Test trajectory equality comparison."""
        traj1 = Trajectory([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])
        traj2 = Trajectory([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])
        traj3 = Trajectory([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 13]]])

        assert np.array_equal(traj1, traj2)
        assert not np.array_equal(traj1, traj3)

    def test_trajectory_concatenation(self):
        """Test trajectory concatenation operations."""
        # Two trajectory segments
        traj1 = Trajectory([[[0, 0, 0], [1, 1, 1]]])
        traj2 = Trajectory([[[2, 2, 2], [3, 3, 3]]])

        # Concatenate along time axis
        combined = np.concatenate([traj1, traj2], axis=1)
        expected_shape = (1, 4, 3)  # 1 mode, 4 timesteps, 3D
        assert combined.shape == expected_shape

        # Verify concatenated trajectory
        expected_waypoints = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]])
        assert np.array_equal(combined[0], expected_waypoints)

    def test_trajectory_statistical_analysis(self):
        """Test statistical analysis of trajectories."""
        # Create trajectory with known statistics
        traj_data = [
            [[0, 0, 0], [2, 2, 2], [4, 4, 4]],  # Mode 1
            [[1, 1, 1], [3, 3, 3], [5, 5, 5]],  # Mode 2
        ]
        traj = Trajectory(traj_data)

        # Calculate statistics across modes
        mean_trajectory = np.mean(traj, axis=0)
        expected_mean = np.array([[0.5, 0.5, 0.5], [2.5, 2.5, 2.5], [4.5, 4.5, 4.5]])
        assert np.array_equal(mean_trajectory, expected_mean)

        # Calculate statistics across time
        mean_per_mode = np.mean(traj, axis=1)
        expected_mode_means = np.array([[2, 2, 2], [3, 3, 3]])
        assert np.array_equal(mean_per_mode, expected_mode_means)

    def test_trajectory_bounds_calculation(self):
        """Test calculating bounding boxes for trajectories."""
        traj = Trajectory(
            [
                [[-1, -2, -3], [1, 2, 3], [0, 0, 0]],  # Mode 1
                [[-2, -1, -1], [2, 1, 1], [0, 0, 0]],  # Mode 2
            ]
        )

        # Calculate overall bounds
        min_bounds = np.min(traj, axis=(0, 1))  # Min across modes and time
        max_bounds = np.max(traj, axis=(0, 1))  # Max across modes and time

        expected_min = np.array([-2, -2, -3])
        expected_max = np.array([2, 2, 3])

        assert np.array_equal(min_bounds, expected_min)
        assert np.array_equal(max_bounds, expected_max)

    def test_trajectory_memory_efficiency(self):
        """Test memory efficiency for large trajectories."""
        # Create a reasonably large trajectory
        large_traj = Trajectory(np.random.rand(5, 100, 3))

        # Should be able to access without memory issues
        assert large_traj.shape == (5, 100, 3)
        assert large_traj[0, 0, 0] is not None
        assert large_traj[-1, -1, -1] is not None

        # Should be able to perform operations
        subset = large_traj[:, :10, :]  # First 10 timesteps
        assert subset.shape == (5, 10, 3)
