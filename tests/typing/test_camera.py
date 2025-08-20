from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import CameraDistortion, CameraIntrinsic


class TestCameraIntrinsic:
    """Test cases for CameraIntrinsic class."""

    def test_creation_from_3x3_array(self):
        """Test CameraIntrinsic creation from 3x3 numpy array."""
        intrinsic_data = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float64)
        cam = CameraIntrinsic(intrinsic_data)
        assert isinstance(cam, CameraIntrinsic)
        assert cam.shape == (3, 3)
        assert np.array_equal(cam, intrinsic_data)

    def test_creation_from_3x3_list(self):
        """Test CameraIntrinsic creation from 3x3 list."""
        intrinsic_data = [[800, 0, 320], [0, 800, 240], [0, 0, 1]]
        cam = CameraIntrinsic(intrinsic_data)
        assert isinstance(cam, CameraIntrinsic)
        assert cam.shape == (3, 3)
        expected = np.array(intrinsic_data)
        assert np.array_equal(cam, expected)

    def test_creation_from_9_element_array(self):
        """Test CameraIntrinsic creation from 9-element array (flattened)."""
        # Row-major order: [fx, s, cx, 0, fy, cy, 0, 0, 1]
        intrinsic_data = [800, 0, 320, 0, 800, 240, 0, 0, 1]
        cam = CameraIntrinsic(intrinsic_data)
        assert isinstance(cam, CameraIntrinsic)
        assert cam.shape == (3, 3)

        expected = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        assert np.array_equal(cam, expected)

    def test_creation_identity_matrix(self):
        """Test CameraIntrinsic creation with identity matrix."""
        identity = np.eye(3)
        cam = CameraIntrinsic(identity)
        assert isinstance(cam, CameraIntrinsic)
        assert cam.shape == (3, 3)
        assert np.array_equal(cam, identity)

    def test_typical_camera_parameters(self):
        """Test CameraIntrinsic with typical camera parameters."""
        # Typical camera intrinsic matrix
        fx, fy = 800.0, 800.0  # Focal lengths
        cx, cy = 320.0, 240.0  # Principal point
        s = 0.0  # Skew parameter

        intrinsic = [[fx, s, cx], [0, fy, cy], [0, 0, 1]]
        cam = CameraIntrinsic(intrinsic)

        assert cam[0, 0] == fx  # fx
        assert cam[1, 1] == fy  # fy
        assert cam[0, 2] == cx  # cx
        assert cam[1, 2] == cy  # cy
        assert cam[0, 1] == s  # skew
        assert cam[2, 2] == 1  # homogeneous coordinate

    def test_creation_with_mixed_types(self):
        """Test CameraIntrinsic creation with mixed numeric types."""
        intrinsic_data = [[800, 0, 320.5], [0, 800.0, 240], [0, 0, 1]]
        cam = CameraIntrinsic(intrinsic_data)
        assert isinstance(cam, CameraIntrinsic)
        assert cam.shape == (3, 3)
        assert cam[0, 2] == 320.5
        assert cam[1, 1] == 800.0

    def test_invalid_shape_2x2(self):
        """Test that CameraIntrinsic raises ValueError for 2x2 matrix."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([[1, 2], [3, 4]])

    def test_invalid_shape_4x4(self):
        """Test that CameraIntrinsic raises ValueError for 4x4 matrix."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic(np.eye(4))

    def test_invalid_shape_3x2(self):
        """Test that CameraIntrinsic raises ValueError for 3x2 matrix."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([[1, 2], [3, 4], [5, 6]])

    def test_invalid_shape_2x3(self):
        """Test that CameraIntrinsic raises ValueError for 2x3 matrix."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([[1, 2, 3], [4, 5, 6]])

    def test_invalid_1d_array_wrong_length(self):
        """Test that CameraIntrinsic raises ValueError for 1D array with wrong length."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([1, 2, 3, 4, 5, 6, 7, 8])  # 8 elements

        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])  # 10 elements

    def test_invalid_empty_array(self):
        """Test that CameraIntrinsic raises ValueError for empty array."""
        with pytest.raises(ValueError, match="CameraIntrinsic must be a 3x3 array"):
            CameraIntrinsic([])

    def test_matrix_operations(self):
        """Test basic matrix operations on CameraIntrinsic."""
        cam1 = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        cam2 = CameraIntrinsic([[1000, 0, 400], [0, 1000, 300], [0, 0, 1]])

        # Addition
        result = cam1 + cam2
        expected = np.array([[1800, 0, 720], [0, 1800, 540], [0, 0, 2]])
        assert np.array_equal(result, expected)

        # Scalar multiplication
        result = cam1 * 2
        expected = np.array([[1600, 0, 640], [0, 1600, 480], [0, 0, 2]])
        assert np.array_equal(result, expected)

    def test_matrix_multiplication(self):
        """Test matrix multiplication with CameraIntrinsic."""
        cam = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # 3D point in homogeneous coordinates
        point_3d = np.array([1, 2, 5])  # (x, y, z)

        # Project to image coordinates
        projected = cam @ point_3d

        # Convert from homogeneous to pixel coordinates
        pixel_x = projected[0] / projected[2]
        pixel_y = projected[1] / projected[2]

        # Expected: x' = fx * x/z + cx, y' = fy * y/z + cy
        expected_x = 800 * (1 / 5) + 320  # 160 + 320 = 480
        expected_y = 800 * (2 / 5) + 240  # 320 + 240 = 560

        assert abs(pixel_x - expected_x) < 1e-10
        assert abs(pixel_y - expected_y) < 1e-10

    def test_matrix_determinant(self):
        """Test determinant calculation for CameraIntrinsic."""
        # Typical camera matrix should have non-zero determinant
        cam = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        det = np.linalg.det(cam)

        # For this matrix: det = 800 * 800 * 1 = 640000
        assert abs(det - 640000) < 1e-6

    def test_matrix_inverse(self):
        """Test inverse calculation for CameraIntrinsic."""
        cam = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        cam_inv = np.linalg.inv(cam)

        # Check that cam * cam_inv = identity
        identity = cam @ cam_inv
        expected_identity = np.eye(3)
        assert np.allclose(identity, expected_identity, atol=1e-10)

    def test_indexing_and_access(self):
        """Test indexing and element access."""
        cam = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # Element access
        assert cam[0, 0] == 800  # fx
        assert cam[1, 1] == 800  # fy
        assert cam[0, 2] == 320  # cx
        assert cam[1, 2] == 240  # cy
        assert cam[2, 2] == 1  # homogeneous

        # Row access
        assert np.array_equal(cam[0], [800, 0, 320])
        assert np.array_equal(cam[1], [0, 800, 240])
        assert np.array_equal(cam[2], [0, 0, 1])

    def test_camera_parameter_extraction(self):
        """Test extracting camera parameters from intrinsic matrix."""
        fx, fy = 800.0, 750.0
        cx, cy = 320.5, 240.2
        s = 0.1  # Small skew

        cam = CameraIntrinsic([[fx, s, cx], [0, fy, cy], [0, 0, 1]])

        # Extract parameters
        extracted_fx = cam[0, 0]
        extracted_fy = cam[1, 1]
        extracted_cx = cam[0, 2]
        extracted_cy = cam[1, 2]
        extracted_s = cam[0, 1]

        assert extracted_fx == fx
        assert extracted_fy == fy
        assert extracted_cx == cx
        assert extracted_cy == cy
        assert extracted_s == s

    def test_numpy_compatibility(self):
        """Test that CameraIntrinsic works with numpy functions."""
        cam = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # Test various numpy functions
        assert np.trace(cam) == 1601  # 800 + 800 + 1
        assert np.sum(cam) == 2161  # Sum of all elements
        assert np.linalg.norm(cam) > 0

        # Test matrix properties
        assert np.allclose(cam.T.T, cam)  # Double transpose
        assert cam.shape == (3, 3)
        assert cam.size == 9


class TestCameraDistortion:
    """Test cases for CameraDistortion class."""

    def test_creation_from_5_element_array(self):
        """Test CameraDistortion creation from 5-element array."""
        distortion_data = [0.1, -0.2, 0.001, 0.002, 0.05]
        dist = CameraDistortion(distortion_data)
        assert isinstance(dist, CameraDistortion)
        assert dist.shape == (5,)
        assert np.array_equal(dist, distortion_data)

    def test_creation_from_numpy_array(self):
        """Test CameraDistortion creation from numpy array."""
        distortion_data = np.array([0.1, -0.2, 0.001, 0.002, 0.05])
        dist = CameraDistortion(distortion_data)
        assert isinstance(dist, CameraDistortion)
        assert dist.shape == (5,)
        assert np.array_equal(dist, distortion_data)

    def test_creation_from_list(self):
        """Test CameraDistortion creation from list."""
        distortion_data = [0.1, -0.2, 0.001, 0.002, 0.05]
        dist = CameraDistortion(distortion_data)
        assert isinstance(dist, CameraDistortion)
        assert dist.shape == (5,)
        assert np.array_equal(dist, distortion_data)

    def test_creation_from_tuple(self):
        """Test CameraDistortion creation from tuple."""
        distortion_data = (0.1, -0.2, 0.001, 0.002, 0.05)
        dist = CameraDistortion(distortion_data)
        assert isinstance(dist, CameraDistortion)
        assert dist.shape == (5,)
        assert np.array_equal(dist, distortion_data)

    def test_typical_distortion_parameters(self):
        """Test CameraDistortion with typical distortion parameters."""
        # Brown-Conrady model: [k1, k2, p1, p2, k3]
        k1, k2, k3 = 0.1, -0.05, 0.01  # Radial distortion coefficients
        p1, p2 = 0.001, 0.002  # Tangential distortion coefficients

        dist = CameraDistortion([k1, k2, p1, p2, k3])

        assert dist[0] == k1  # k1
        assert dist[1] == k2  # k2
        assert dist[2] == p1  # p1
        assert dist[3] == p2  # p2
        assert dist[4] == k3  # k3

    def test_zero_distortion(self):
        """Test CameraDistortion with zero distortion (undistorted camera)."""
        zero_distortion = [0.0, 0.0, 0.0, 0.0, 0.0]
        dist = CameraDistortion(zero_distortion)
        assert isinstance(dist, CameraDistortion)
        assert np.allclose(dist, zero_distortion)
        assert np.sum(dist) == 0.0

    def test_creation_with_mixed_types(self):
        """Test CameraDistortion creation with mixed numeric types."""
        distortion_data = [0.1, -0.2, 0, 0.002, 0.05]
        dist = CameraDistortion(distortion_data)
        assert isinstance(dist, CameraDistortion)
        assert dist[0] == 0.1
        assert dist[1] == -0.2
        assert dist[2] == 0.0
        assert dist[3] == 0.002
        assert dist[4] == 0.05

    def test_invalid_length_too_short(self):
        """Test that CameraDistortion raises ValueError for arrays too short."""
        with pytest.raises(ValueError, match="CameraDistortion must be a 1D array of length 5"):
            CameraDistortion([0.1, -0.2, 0.001, 0.002])  # 4 elements

    def test_invalid_length_too_long(self):
        """Test that CameraDistortion raises ValueError for arrays too long."""
        with pytest.raises(ValueError, match="CameraDistortion must be a 1D array of length 5"):
            CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05, 0.01])  # 6 elements

    def test_invalid_empty_array(self):
        """Test that CameraDistortion raises ValueError for empty array."""
        with pytest.raises(ValueError, match="CameraDistortion must be a 1D array of length 5"):
            CameraDistortion([])

    def test_invalid_2d_array(self):
        """Test that CameraDistortion raises ValueError for 2D array."""
        with pytest.raises(ValueError):
            CameraDistortion([[0.1, -0.2], [0.001, 0.002], [0.05]])

    def test_invalid_single_element(self):
        """Test that CameraDistortion raises ValueError for single element."""
        with pytest.raises(ValueError, match="CameraDistortion must be a 1D array of length 5"):
            CameraDistortion([0.1])

    def test_arithmetic_operations(self):
        """Test arithmetic operations on CameraDistortion."""
        dist1 = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])
        dist2 = CameraDistortion([0.05, -0.1, 0.0005, 0.001, 0.025])

        # Addition
        result = dist1 + dist2
        expected = np.array([0.15, -0.3, 0.0015, 0.003, 0.075])
        assert np.allclose(result, expected)

        # Subtraction
        result = dist1 - dist2
        expected = np.array([0.05, -0.1, 0.0005, 0.001, 0.025])
        assert np.allclose(result, expected)

        # Scalar multiplication
        result = dist1 * 2
        expected = np.array([0.2, -0.4, 0.002, 0.004, 0.1])
        assert np.allclose(result, expected)

    def test_indexing_and_access(self):
        """Test indexing and element access."""
        dist = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # Element access
        assert dist[0] == 0.1
        assert dist[1] == -0.2
        assert dist[2] == 0.001
        assert dist[3] == 0.002
        assert dist[4] == 0.05

        # Negative indexing
        assert dist[-1] == 0.05
        assert dist[-2] == 0.002

        # Slicing
        assert np.array_equal(dist[:2], [0.1, -0.2])  # Radial k1, k2
        assert np.array_equal(dist[2:4], [0.001, 0.002])  # Tangential p1, p2
        assert dist[4] == 0.05  # Radial k3

    def test_distortion_parameter_extraction(self):
        """Test extracting specific distortion parameters."""
        k1, k2, p1, p2, k3 = 0.15, -0.25, 0.003, 0.004, 0.08
        dist = CameraDistortion([k1, k2, p1, p2, k3])

        # Extract radial distortion coefficients
        radial_k1_k2 = dist[:2]
        radial_k3 = dist[4]
        assert np.array_equal(radial_k1_k2, [k1, k2])
        assert radial_k3 == k3

        # Extract tangential distortion coefficients
        tangential = dist[2:4]
        assert np.array_equal(tangential, [p1, p2])

    def test_numpy_compatibility(self):
        """Test that CameraDistortion works with numpy functions."""
        dist = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # Test various numpy functions
        assert np.sum(dist) == pytest.approx(-0.047)
        assert np.mean(dist) == pytest.approx(-0.0094)
        assert np.std(dist) > 0
        assert np.linalg.norm(dist) > 0

        # Test array properties
        assert dist.shape == (5,)
        assert dist.size == 5
        assert dist.ndim == 1

    def test_distortion_magnitude(self):
        """Test measuring distortion magnitude."""
        # High distortion
        high_dist = CameraDistortion([0.5, -0.8, 0.01, 0.02, 0.3])

        # Low distortion
        low_dist = CameraDistortion([0.01, -0.02, 0.001, 0.002, 0.005])

        # Zero distortion
        zero_dist = CameraDistortion([0.0, 0.0, 0.0, 0.0, 0.0])

        # Compare magnitudes using L2 norm
        high_magnitude = np.linalg.norm(high_dist)
        low_magnitude = np.linalg.norm(low_dist)
        zero_magnitude = np.linalg.norm(zero_dist)

        assert high_magnitude > low_magnitude > zero_magnitude
        assert zero_magnitude == 0.0


class TestCameraInteroperability:
    """Test interoperability between CameraIntrinsic and CameraDistortion."""

    def test_camera_model_combination(self):
        """Test using CameraIntrinsic and CameraDistortion together."""
        # Camera intrinsic parameters
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # Camera distortion parameters
        distortion = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # Both should be compatible for camera modeling
        assert isinstance(intrinsic, CameraIntrinsic)
        assert isinstance(distortion, CameraDistortion)
        assert intrinsic.shape == (3, 3)
        assert distortion.shape == (5,)

    def test_camera_projection_pipeline(self):
        """Test complete camera projection pipeline."""
        # Set up camera model
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        _ = CameraDistortion([0.0, 0.0, 0.0, 0.0, 0.0])  # No distortion for simplicity

        # 3D point
        point_3d = np.array([1.0, 2.0, 5.0])

        # Step 1: Project using intrinsic matrix (assuming no distortion)
        projected_homogeneous = intrinsic @ point_3d

        # Step 2: Convert to pixel coordinates
        pixel_x = projected_homogeneous[0] / projected_homogeneous[2]
        pixel_y = projected_homogeneous[1] / projected_homogeneous[2]

        # Expected results: x' = fx*x/z + cx, y' = fy*y/z + cy
        expected_x = 800 * (1.0 / 5.0) + 320  # 160 + 320 = 480
        expected_y = 800 * (2.0 / 5.0) + 240  # 320 + 240 = 560

        assert abs(pixel_x - expected_x) < 1e-10
        assert abs(pixel_y - expected_y) < 1e-10

    def test_parameter_validation(self):
        """Test that camera parameters are physically reasonable."""
        # Valid camera parameters
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        distortion = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # Check that focal lengths are positive
        fx, fy = intrinsic[0, 0], intrinsic[1, 1]
        assert fx > 0
        assert fy > 0

        # Check that principal point is reasonable (within image bounds for typical images)
        cx, cy = intrinsic[0, 2], intrinsic[1, 2]
        assert cx > 0
        assert cy > 0

        # Check that distortion parameters are reasonable (not extremely large)
        max_distortion = np.max(np.abs(distortion))
        assert max_distortion < 10  # Reasonable upper bound for distortion coefficients

    def test_camera_calibration_matrix_properties(self):
        """Test properties that should hold for camera calibration matrices."""
        # Typical camera intrinsic matrix
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])

        # Should be upper triangular (approximately)
        assert intrinsic[1, 0] == 0  # Below diagonal
        assert intrinsic[2, 0] == 0  # Below diagonal
        assert intrinsic[2, 1] == 0  # Below diagonal

        # Bottom-right element should be 1
        assert intrinsic[2, 2] == 1

        # Should have positive determinant
        det = np.linalg.det(intrinsic)
        assert det > 0

    def test_type_consistency(self):
        """Test that types are maintained through operations."""
        intrinsic = CameraIntrinsic([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
        distortion = CameraDistortion([0.1, -0.2, 0.001, 0.002, 0.05])

        # Test that they remain the correct types after creation
        assert type(intrinsic).__name__ == "CameraIntrinsic"
        assert type(distortion).__name__ == "CameraDistortion"

        # Test shapes are maintained
        assert intrinsic.shape == (3, 3)
        assert distortion.shape == (5,)
