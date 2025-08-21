from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import Quaternion


class TestQuaternion:
    """Test cases for Quaternion class."""

    def test_creation_from_list(self):
        """Test Quaternion creation from list."""
        q = Quaternion([1.0, 0.0, 0.0, 0.0])  # w, x, y, z
        assert isinstance(q, Quaternion)
        assert q.w == 1.0
        assert q.x == 0.0
        assert q.y == 0.0
        assert q.z == 0.0

    def test_creation_from_tuple(self):
        """Test Quaternion creation from tuple."""
        q = Quaternion((0.0, 1.0, 0.0, 0.0))  # w, x, y, z
        assert isinstance(q, Quaternion)
        assert q.w == 0.0
        assert q.x == 1.0
        assert q.y == 0.0
        assert q.z == 0.0

    def test_creation_from_numpy_array(self):
        """Test Quaternion creation from numpy array."""
        arr = np.array([0.0, 0.0, 1.0, 0.0])  # w, x, y, z
        q = Quaternion(arr)
        assert isinstance(q, Quaternion)
        assert q.w == 0.0
        assert q.x == 0.0
        assert q.y == 1.0
        assert q.z == 0.0

    def test_creation_identity_quaternion(self):
        """Test creation of identity quaternion."""
        q = Quaternion([1.0, 0.0, 0.0, 0.0])
        assert q.w == 1.0
        assert q.x == 0.0
        assert q.y == 0.0
        assert q.z == 0.0

        # Should represent no rotation
        assert abs(q.norm - 1.0) < 1e-10

    def test_creation_from_rotation_matrix(self):
        """Test Quaternion creation from rotation matrix."""
        # Identity matrix should give identity quaternion
        identity_matrix = np.eye(3)
        q = Quaternion(matrix=identity_matrix)
        assert isinstance(q, Quaternion)
        # Should be close to identity quaternion [1, 0, 0, 0]
        assert abs(q.w - 1.0) < 1e-10
        assert abs(q.x) < 1e-10
        assert abs(q.y) < 1e-10
        assert abs(q.z) < 1e-10

    def test_creation_from_axis_angle(self):
        """Test Quaternion creation from axis and angle."""
        # 90 degree rotation around z-axis
        axis = [0, 0, 1]
        angle = np.pi / 2
        q = Quaternion(axis=axis, angle=angle)
        assert isinstance(q, Quaternion)

        # Check that it's normalized
        assert abs(q.norm - 1.0) < 1e-10

        # For 90° rotation around z-axis: w = cos(45°), z = sin(45°)
        expected_w = np.cos(angle / 2)
        expected_z = np.sin(angle / 2)
        assert abs(q.w - expected_w) < 1e-10
        assert abs(q.x) < 1e-10
        assert abs(q.y) < 1e-10
        assert abs(q.z - expected_z) < 1e-10

    def test_quaternion_properties(self):
        """Test quaternion properties."""
        q = Quaternion([0.7071, 0.0, 0.0, 0.7071])  # ~45° rotation around z

        # Test norm
        assert abs(q.norm - 1.0) < 1e-3

        # Test conjugate
        conj = q.conjugate
        assert conj.w == q.w
        assert conj.x == -q.x
        assert conj.y == -q.y
        assert conj.z == -q.z

        # Test inverse
        inv = q.inverse
        # For unit quaternions, inverse should equal conjugate
        assert abs(inv.w - conj.w) < 1e-3
        assert abs(inv.x - conj.x) < 1e-3
        assert abs(inv.y - conj.y) < 1e-3
        assert abs(inv.z - conj.z) < 1e-3

    def test_quaternion_multiplication(self):
        """Test quaternion multiplication."""
        # Identity quaternion
        q_identity = Quaternion([1.0, 0.0, 0.0, 0.0])

        # 90° rotation around z-axis
        q_z90 = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)

        # Multiplying by identity should not change the quaternion
        result = q_z90 * q_identity
        assert abs(result.w - q_z90.w) < 1e-10
        assert abs(result.x - q_z90.x) < 1e-10
        assert abs(result.y - q_z90.y) < 1e-10
        assert abs(result.z - q_z90.z) < 1e-10

    def test_vector_rotation(self):
        """Test rotating vectors with quaternions."""
        # 90° rotation around z-axis
        q = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)

        # Rotate vector [1, 0, 0] -> should become [0, 1, 0]
        vector = np.array([1.0, 0.0, 0.0])
        rotated = q.rotate(vector)

        expected = np.array([0.0, 1.0, 0.0])
        assert np.allclose(rotated, expected, atol=1e-10)

    def test_vector_rotation_multiple_vectors(self):
        """Test rotating multiple vectors at once."""
        # 90° rotation around z-axis
        q = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)

        # Multiple vectors - test one at a time due to pyquaternion limitations
        vectors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

        rotated = []
        for vector in vectors:
            rotated.append(q.rotate(vector))
        rotated = np.array(rotated)

        expected = np.array(
            [
                [0.0, 1.0, 0.0],  # [1,0,0] -> [0,1,0]
                [-1.0, 0.0, 0.0],  # [0,1,0] -> [-1,0,0]
                [0.0, 0.0, 1.0],  # [0,0,1] -> [0,0,1] (unchanged, rotation around z)
            ]
        )

        assert np.allclose(rotated, expected, atol=1e-3)

    def test_quaternion_to_rotation_matrix(self):
        """Test conversion to rotation matrix."""
        # Identity quaternion
        q_identity = Quaternion([1.0, 0.0, 0.0, 0.0])
        matrix = q_identity.rotation_matrix

        # Should be 3x3 identity matrix
        expected = np.eye(3)
        assert np.allclose(matrix, expected, atol=1e-10)

    def test_quaternion_to_transformation_matrix(self):
        """Test conversion to 4x4 transformation matrix."""
        q = Quaternion([1.0, 0.0, 0.0, 0.0])
        transform = q.transformation_matrix

        # Should be 4x4 identity matrix
        expected = np.eye(4)
        assert np.allclose(transform, expected, atol=1e-10)

    def test_quaternion_normalization(self):
        """Test quaternion normalization."""
        # Create non-normalized quaternion
        q = Quaternion([2.0, 0.0, 0.0, 0.0])

        # Normalize it
        q_normalized = q.normalised

        # Should have unit norm
        assert abs(q_normalized.norm - 1.0) < 1e-10

        # Should be in same direction
        assert q_normalized.w > 0  # Should be positive since original w was positive

    def test_quaternion_euler_conversion(self):
        """Test conversion to/from Euler angles."""
        # Test with known rotation
        # 90° rotation around z-axis
        q = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)

        # Convert to Euler angles (should be approximately [0, 0, π/2])
        euler = q.yaw_pitch_roll

        # Check that yaw is approximately π/2, pitch and roll are approximately 0
        assert abs(euler[0] - np.pi / 2) < 1e-6  # yaw
        assert abs(euler[1]) < 1e-6  # pitch
        assert abs(euler[2]) < 1e-6  # roll

    def test_quaternion_slerp(self):
        """Test spherical linear interpolation."""
        # Start and end quaternions
        q1 = Quaternion([1.0, 0.0, 0.0, 0.0])  # Identity
        q2 = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)  # 90° around z

        # Interpolate halfway
        q_mid = Quaternion.slerp(q1, q2, 0.5)

        # Should be 45° rotation around z
        expected_angle = np.pi / 4
        expected_w = np.cos(expected_angle / 2)
        expected_z = np.sin(expected_angle / 2)

        assert abs(q_mid.w - expected_w) < 1e-6
        assert abs(q_mid.x) < 1e-6
        assert abs(q_mid.y) < 1e-6
        assert abs(q_mid.z - expected_z) < 1e-6

    def test_quaternion_array_access(self):
        """Test accessing quaternion as array."""
        q = Quaternion([0.7071, 0.0, 0.0, 0.7071])

        # Test q property (returns as array [w, x, y, z])
        arr = q.q
        assert isinstance(arr, np.ndarray)
        assert len(arr) == 4
        assert arr[0] == q.w
        assert arr[1] == q.x
        assert arr[2] == q.y
        assert arr[3] == q.z

    def test_quaternion_equality(self):
        """Test quaternion equality comparison."""
        q1 = Quaternion([1.0, 0.0, 0.0, 0.0])
        q2 = Quaternion([1.0, 0.0, 0.0, 0.0])
        q3 = Quaternion([0.0, 1.0, 0.0, 0.0])

        # Note: pyquaternion might not implement __eq__ in a standard way
        # So we test component-wise equality
        assert q1.w == q2.w and q1.x == q2.x and q1.y == q2.y and q1.z == q2.z
        assert not (q1.w == q3.w and q1.x == q3.x and q1.y == q3.y and q1.z == q3.z)

    def test_quaternion_string_representation(self):
        """Test string representation of quaternions."""
        q = Quaternion([1.0, 0.0, 0.0, 0.0])
        str_repr = str(q)

        # Should contain the quaternion values
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_invalid_quaternion_creation(self):
        """Test invalid quaternion creation scenarios."""
        # Test with wrong number of elements
        with pytest.raises((ValueError, TypeError)):
            Quaternion([1.0, 0.0, 0.0])  # Only 3 elements

        with pytest.raises((ValueError, TypeError)):
            Quaternion([1.0, 0.0, 0.0, 0.0, 0.0])  # 5 elements

    def test_quaternion_composition(self):
        """Test composition of multiple rotations."""
        # Two 45° rotations around z should equal one 90° rotation
        q_45_1 = Quaternion(axis=[0, 0, 1], angle=np.pi / 4)
        q_45_2 = Quaternion(axis=[0, 0, 1], angle=np.pi / 4)
        q_90 = Quaternion(axis=[0, 0, 1], angle=np.pi / 2)

        # Compose the two 45° rotations
        q_composed = q_45_2 * q_45_1

        # Should be approximately equal to the 90° rotation
        # Check by comparing the effect on a test vector
        test_vector = np.array([1.0, 0.0, 0.0])

        result_composed = q_composed.rotate(test_vector)
        result_90 = q_90.rotate(test_vector)

        assert np.allclose(result_composed, result_90, atol=1e-10)

    def test_quaternion_inverse_rotation(self):
        """Test that inverse quaternion undoes rotation."""
        # Create a rotation
        q = Quaternion(axis=[1, 1, 1], angle=np.pi / 3)  # 60° around [1,1,1]
        q_inv = q.inverse

        # Test vector
        vector = np.array([1.0, 2.0, 3.0])

        # Rotate and then rotate back
        rotated = q.rotate(vector)
        back_to_original = q_inv.rotate(rotated)

        # Should get back the original vector
        assert np.allclose(back_to_original, vector, atol=1e-10)

    def test_quaternion_axis_angle_extraction(self):
        """Test extracting axis and angle from quaternion."""
        # Create quaternion with known axis and angle
        original_axis = np.array([0, 0, 1])
        original_angle = np.pi / 3

        q = Quaternion(axis=original_axis, angle=original_angle)

        # Extract axis and angle
        try:
            extracted_axis = q.axis
            extracted_angle = q.angle

            # Check axis (should be unit vector in same direction)
            assert np.allclose(extracted_axis, original_axis, atol=1e-10)

            # Check angle
            assert abs(extracted_angle - original_angle) < 1e-10

        except AttributeError:
            # If these properties don't exist, create alternative test
            # Check that rotation matrix produces expected result
            matrix = q.rotation_matrix
            test_vector = np.array([1.0, 0.0, 0.0])
            rotated = matrix @ test_vector

            # Manual calculation of expected result
            expected = np.array([np.cos(original_angle), np.sin(original_angle), 0.0])

            assert np.allclose(rotated, expected, atol=1e-10)
