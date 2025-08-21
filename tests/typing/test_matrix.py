from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import Matrix3x3, Matrix4x4


class TestMatrix3x3:
    """Test cases for Matrix3x3 class."""

    def test_creation_from_2d_list(self):
        """Test Matrix3x3 creation from 2D list."""
        matrix_data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m = Matrix3x3(matrix_data)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert np.array_equal(m, matrix_data)

    def test_creation_from_numpy_array(self):
        """Test Matrix3x3 creation from numpy array."""
        matrix_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        m = Matrix3x3(matrix_data)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert np.array_equal(m, matrix_data)

    def test_creation_identity_matrix(self):
        """Test Matrix3x3 creation of identity matrix."""
        identity = np.eye(3)
        m = Matrix3x3(identity)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert np.array_equal(m, identity)

    def test_creation_zeros_matrix(self):
        """Test Matrix3x3 creation of zeros matrix."""
        zeros = np.zeros((3, 3))
        m = Matrix3x3(zeros)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert np.array_equal(m, zeros)

    def test_creation_ones_matrix(self):
        """Test Matrix3x3 creation of ones matrix."""
        ones = np.ones((3, 3))
        m = Matrix3x3(ones)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert np.array_equal(m, ones)

    def test_creation_from_nested_tuples(self):
        """Test Matrix3x3 creation from nested tuples."""
        matrix_data = ((1, 2, 3), (4, 5, 6), (7, 8, 9))
        m = Matrix3x3(matrix_data)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        expected = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert np.array_equal(m, expected)

    def test_creation_mixed_numeric_types(self):
        """Test Matrix3x3 creation with mixed numeric types."""
        matrix_data = [[1, 2.5, 3], [4.0, 5, 6.2], [7, 8.8, 9]]
        m = Matrix3x3(matrix_data)
        assert isinstance(m, Matrix3x3)
        assert m.shape == (3, 3)
        assert m[0, 1] == 2.5
        assert m[1, 2] == 6.2
        assert m[2, 1] == 8.8

    def test_invalid_shape_2x2(self):
        """Test that Matrix3x3 raises ValueError for 2x2 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(3, 3\\)"):
            Matrix3x3([[1, 2], [3, 4]])

    def test_invalid_shape_4x4(self):
        """Test that Matrix3x3 raises ValueError for 4x4 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(3, 3\\)"):
            Matrix3x3(np.eye(4))

    def test_invalid_shape_3x4(self):
        """Test that Matrix3x3 raises ValueError for 3x4 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(3, 3\\)"):
            Matrix3x3([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])

    def test_invalid_shape_1d_array(self):
        """Test that Matrix3x3 raises ValueError for 1D array."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(3, 3\\)"):
            Matrix3x3([1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_invalid_empty_array(self):
        """Test that Matrix3x3 raises ValueError for empty array."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(3, 3\\)"):
            Matrix3x3([])

    def test_matrix_operations(self):
        """Test basic matrix operations."""
        m1 = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        m2 = Matrix3x3([[9, 8, 7], [6, 5, 4], [3, 2, 1]])

        # Addition
        result = m1 + m2
        expected = np.array([[10, 10, 10], [10, 10, 10], [10, 10, 10]])
        assert np.array_equal(result, expected)

        # Subtraction
        result = m1 - m2
        expected = np.array([[-8, -6, -4], [-2, 0, 2], [4, 6, 8]])
        assert np.array_equal(result, expected)

        # Scalar multiplication
        result = m1 * 2
        expected = np.array([[2, 4, 6], [8, 10, 12], [14, 16, 18]])
        assert np.array_equal(result, expected)

    def test_matrix_multiplication(self):
        """Test matrix multiplication."""
        m1 = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        identity = Matrix3x3(np.eye(3))

        # Multiply by identity
        result = m1 @ identity
        assert np.allclose(result, m1)

        # Multiply identity by matrix
        result = identity @ m1
        assert np.allclose(result, m1)

    def test_matrix_determinant(self):
        """Test matrix determinant calculation."""
        # Identity matrix has determinant 1
        identity = Matrix3x3(np.eye(3))
        det = np.linalg.det(identity)
        assert abs(det - 1.0) < 1e-10

        # Known matrix with determinant 0
        singular = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        det = np.linalg.det(singular)
        assert abs(det) < 1e-10

    def test_matrix_inverse(self):
        """Test matrix inverse calculation."""
        # Invertible matrix
        m = Matrix3x3([[1, 2, 0], [0, 1, 3], [1, 0, 1]])
        m_inv = np.linalg.inv(m)

        # Check that m * m_inv = identity
        identity = m @ m_inv
        expected_identity = np.eye(3)
        assert np.allclose(identity, expected_identity, atol=1e-10)

    def test_matrix_transpose(self):
        """Test matrix transpose."""
        m = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        m_t = m.T

        expected = np.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]])
        assert np.array_equal(m_t, expected)

    def test_matrix_indexing(self):
        """Test matrix indexing and slicing."""
        m = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        # Element access
        assert m[0, 0] == 1
        assert m[1, 2] == 6
        assert m[2, 1] == 8

        # Row access
        assert np.array_equal(m[0], [1, 2, 3])
        assert np.array_equal(m[1], [4, 5, 6])
        assert np.array_equal(m[2], [7, 8, 9])

        # Column access
        assert np.array_equal(m[:, 0], [1, 4, 7])
        assert np.array_equal(m[:, 1], [2, 5, 8])
        assert np.array_equal(m[:, 2], [3, 6, 9])

    def test_matrix_equality(self):
        """Test matrix equality comparison."""
        m1 = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        m2 = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        m3 = Matrix3x3([[9, 8, 7], [6, 5, 4], [3, 2, 1]])

        assert np.array_equal(m1, m2)
        assert not np.array_equal(m1, m3)

    def test_matrix_properties(self):
        """Test matrix properties."""
        m = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        # Shape
        assert m.shape == (3, 3)

        # Size
        assert m.size == 9

        # Dimension
        assert m.ndim == 2

    def test_rotation_matrix_properties(self):
        """Test properties specific to rotation matrices."""
        # Create a rotation matrix (90° around z-axis)
        cos_90, sin_90 = 0, 1
        rotation_z_90 = Matrix3x3([[cos_90, -sin_90, 0], [sin_90, cos_90, 0], [0, 0, 1]])

        # Rotation matrices should have determinant 1
        det = np.linalg.det(rotation_z_90)
        assert abs(det - 1.0) < 1e-10

        # Rotation matrices should be orthogonal (R.T @ R = I)
        should_be_identity = rotation_z_90.T @ rotation_z_90
        expected_identity = np.eye(3)
        assert np.allclose(should_be_identity, expected_identity, atol=1e-10)


class TestMatrix4x4:
    """Test cases for Matrix4x4 class."""

    def test_creation_from_2d_list(self):
        """Test Matrix4x4 creation from 2D list."""
        matrix_data = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
        m = Matrix4x4(matrix_data)
        assert isinstance(m, Matrix4x4)
        assert m.shape == (4, 4)
        assert np.array_equal(m, matrix_data)

    def test_creation_from_numpy_array(self):
        """Test Matrix4x4 creation from numpy array."""
        matrix_data = np.random.rand(4, 4)
        m = Matrix4x4(matrix_data)
        assert isinstance(m, Matrix4x4)
        assert m.shape == (4, 4)
        assert np.array_equal(m, matrix_data)

    def test_creation_identity_matrix(self):
        """Test Matrix4x4 creation of identity matrix."""
        identity = np.eye(4)
        m = Matrix4x4(identity)
        assert isinstance(m, Matrix4x4)
        assert m.shape == (4, 4)
        assert np.array_equal(m, identity)

    def test_creation_transformation_matrix(self):
        """Test Matrix4x4 creation of transformation matrix."""
        # Homogeneous transformation matrix (translation + rotation)
        transform = np.eye(4)
        transform[:3, 3] = [1, 2, 3]  # Translation

        m = Matrix4x4(transform)
        assert isinstance(m, Matrix4x4)
        assert m.shape == (4, 4)
        assert np.array_equal(m, transform)

    def test_invalid_shape_3x3(self):
        """Test that Matrix4x4 raises ValueError for 3x3 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(4, 4\\)"):
            Matrix4x4(np.eye(3))

    def test_invalid_shape_5x5(self):
        """Test that Matrix4x4 raises ValueError for 5x5 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(4, 4\\)"):
            Matrix4x4(np.eye(5))

    def test_invalid_shape_4x3(self):
        """Test that Matrix4x4 raises ValueError for 4x3 matrix."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(4, 4\\)"):
            Matrix4x4([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])

    def test_invalid_shape_1d_array(self):
        """Test that Matrix4x4 raises ValueError for 1D array."""
        with pytest.raises(ValueError, match="Input array must be of shape \\(4, 4\\)"):
            Matrix4x4(list(range(16)))

    def test_matrix_operations(self):
        """Test basic matrix operations."""
        m1 = Matrix4x4(np.eye(4))
        m2 = Matrix4x4(np.ones((4, 4)))

        # Addition
        result = m1 + m2
        expected = np.eye(4) + np.ones((4, 4))
        assert np.array_equal(result, expected)

        # Subtraction
        result = m2 - m1
        expected = np.ones((4, 4)) - np.eye(4)
        assert np.array_equal(result, expected)

        # Scalar multiplication
        result = m1 * 5
        expected = np.eye(4) * 5
        assert np.array_equal(result, expected)

    def test_matrix_multiplication(self):
        """Test matrix multiplication."""
        m = Matrix4x4(np.random.rand(4, 4))
        identity = Matrix4x4(np.eye(4))

        # Multiply by identity
        result = m @ identity
        assert np.allclose(result, m)

        # Multiply identity by matrix
        result = identity @ m
        assert np.allclose(result, m)

    def test_homogeneous_coordinates(self):
        """Test homogeneous coordinate operations."""
        # Translation matrix
        translation = Matrix4x4(np.eye(4))
        translation[0, 3] = 5  # Translate by 5 in x
        translation[1, 3] = 3  # Translate by 3 in y
        translation[2, 3] = 1  # Translate by 1 in z

        # Point in homogeneous coordinates
        point = np.array([1, 1, 1, 1])

        # Apply transformation
        transformed = translation @ point

        # Check result
        expected = np.array([6, 4, 2, 1])  # Original + translation
        assert np.array_equal(transformed, expected)

    def test_transformation_composition(self):
        """Test composition of transformations."""
        # First transformation: translate by [1, 2, 3]
        t1 = Matrix4x4(np.eye(4))
        t1[:3, 3] = [1, 2, 3]

        # Second transformation: translate by [4, 5, 6]
        t2 = Matrix4x4(np.eye(4))
        t2[:3, 3] = [4, 5, 6]

        # Composed transformation
        composed = t2 @ t1

        # Should be equivalent to translating by [5, 7, 9]
        expected = Matrix4x4(np.eye(4))
        expected[:3, 3] = [5, 7, 9]

        assert np.allclose(composed, expected)

    def test_matrix_inverse_4x4(self):
        """Test 4x4 matrix inverse."""
        # Create invertible transformation matrix
        m = Matrix4x4(np.eye(4))
        m[:3, 3] = [1, 2, 3]  # Add translation

        # Calculate inverse
        m_inv = np.linalg.inv(m)

        # Check that m * m_inv = identity
        identity = m @ m_inv
        expected_identity = np.eye(4)
        assert np.allclose(identity, expected_identity, atol=1e-10)

    def test_matrix_determinant_4x4(self):
        """Test 4x4 matrix determinant."""
        # Identity matrix has determinant 1
        identity = Matrix4x4(np.eye(4))
        det = np.linalg.det(identity)
        assert abs(det - 1.0) < 1e-10

        # Translation matrix also has determinant 1
        translation = Matrix4x4(np.eye(4))
        translation[:3, 3] = [1, 2, 3]
        det = np.linalg.det(translation)
        assert abs(det - 1.0) < 1e-10

    def test_matrix_indexing_4x4(self):
        """Test 4x4 matrix indexing."""
        data = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
        m = Matrix4x4(data)

        # Element access
        assert m[0, 0] == 1
        assert m[1, 2] == 7
        assert m[3, 3] == 16

        # Row access
        assert np.array_equal(m[0], [1, 2, 3, 4])
        assert np.array_equal(m[3], [13, 14, 15, 16])

        # Column access
        assert np.array_equal(m[:, 0], [1, 5, 9, 13])
        assert np.array_equal(m[:, 3], [4, 8, 12, 16])

        # Submatrix access (upper 3x3)
        upper_3x3 = m[:3, :3]
        expected_3x3 = np.array([[1, 2, 3], [5, 6, 7], [9, 10, 11]])
        assert np.array_equal(upper_3x3, expected_3x3)

    def test_matrix_properties_4x4(self):
        """Test 4x4 matrix properties."""
        m = Matrix4x4(np.eye(4))

        # Shape
        assert m.shape == (4, 4)

        # Size
        assert m.size == 16

        # Dimension
        assert m.ndim == 2


class TestMatrixInteroperability:
    """Test interoperability between Matrix3x3 and Matrix4x4."""

    def test_matrix_conversion_3x3_to_4x4(self):
        """Test converting 3x3 matrix to 4x4 by embedding."""
        m3 = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        # Embed in 4x4 matrix
        m4_data = np.eye(4)
        m4_data[:3, :3] = m3
        m4 = Matrix4x4(m4_data)

        # Check that upper-left 3x3 is preserved
        assert np.array_equal(m4[:3, :3], m3)
        assert m4[3, 3] == 1
        assert np.array_equal(m4[3, :3], [0, 0, 0])
        assert np.array_equal(m4[:3, 3], [0, 0, 0])

    def test_matrix_conversion_4x4_to_3x3(self):
        """Test extracting 3x3 matrix from 4x4."""
        m4 = Matrix4x4(np.random.rand(4, 4))

        # Extract upper-left 3x3
        m3 = Matrix3x3(m4[:3, :3])

        # Check that extraction worked
        assert isinstance(m3, Matrix3x3)
        assert m3.shape == (3, 3)
        assert np.array_equal(m3, m4[:3, :3])

    def test_numpy_compatibility(self):
        """Test that matrices work with numpy functions."""
        m3 = Matrix3x3(np.random.rand(3, 3))
        m4 = Matrix4x4(np.random.rand(4, 4))

        # Test numpy functions
        assert np.allclose(np.trace(m3), np.sum(np.diag(m3)))
        assert np.allclose(np.trace(m4), np.sum(np.diag(m4)))

        # Test matrix norms
        assert np.linalg.norm(m3) > 0
        assert np.linalg.norm(m4) > 0

    def test_type_preservation(self):
        """Test that matrix types are preserved through operations."""
        m3 = Matrix3x3(np.eye(3))
        m4 = Matrix4x4(np.eye(4))

        # Operations should return numpy arrays, not necessarily the custom type
        result3 = m3 * 2
        result4 = m4 * 2

        # But they should have the correct shape
        assert result3.shape == (3, 3)
        assert result4.shape == (4, 4)
