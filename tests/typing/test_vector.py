from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.typing import Vector2, Vector3, Vector6


class TestVector2:
    """Test cases for Vector2 class."""

    def test_creation_from_list(self):
        """Test Vector2 creation from list."""
        v = Vector2([1.0, 2.0])
        assert isinstance(v, Vector2)
        assert v.shape == (2,)
        assert v[0] == 1.0
        assert v[1] == 2.0

    def test_creation_from_tuple(self):
        """Test Vector2 creation from tuple."""
        v = Vector2((3.0, 4.0))
        assert isinstance(v, Vector2)
        assert v.shape == (2,)
        assert v[0] == 3.0
        assert v[1] == 4.0

    def test_creation_from_numpy_array(self):
        """Test Vector2 creation from numpy array."""
        arr = np.array([5.0, 6.0])
        v = Vector2(arr)
        assert isinstance(v, Vector2)
        assert v.shape == (2,)
        assert v[0] == 5.0
        assert v[1] == 6.0

    def test_creation_from_integers(self):
        """Test Vector2 creation from integers."""
        v = Vector2([1, 2])
        assert isinstance(v, Vector2)
        assert v.shape == (2,)
        assert v[0] == 1
        assert v[1] == 2

    def test_creation_from_mixed_types(self):
        """Test Vector2 creation from mixed numeric types."""
        v = Vector2([1, 2.5])
        assert isinstance(v, Vector2)
        assert v.shape == (2,)
        assert v[0] == 1.0
        assert v[1] == 2.5

    def test_invalid_length_too_short(self):
        """Test that Vector2 raises ValueError for too few elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 2 elements"):
            Vector2([1.0])

    def test_invalid_length_too_long(self):
        """Test that Vector2 raises ValueError for too many elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 2 elements"):
            Vector2([1.0, 2.0, 3.0])

    def test_invalid_empty_array(self):
        """Test that Vector2 raises ValueError for empty array."""
        with pytest.raises(ValueError, match="Input array must have exactly 2 elements"):
            Vector2([])

    def test_invalid_2d_array(self):
        """Test that Vector2 raises ValueError for 2D array."""
        with pytest.raises(ValueError, match="Input array must have exactly 2 elements"):
            Vector2([[1, 2], [3, 4]])

    def test_mathematical_operations(self):
        """Test basic mathematical operations."""
        v1 = Vector2([1.0, 2.0])
        v2 = Vector2([3.0, 4.0])

        # Addition
        result = v1 + v2
        assert np.allclose(result, [4.0, 6.0])

        # Subtraction
        result = v2 - v1
        assert np.allclose(result, [2.0, 2.0])

        # Scalar multiplication
        result = v1 * 2
        assert np.allclose(result, [2.0, 4.0])

        # Dot product
        result = np.dot(v1, v2)
        assert result == 11.0  # 1*3 + 2*4

    def test_numpy_compatibility(self):
        """Test that Vector2 works with numpy functions."""
        v = Vector2([3.0, 4.0])

        # Norm
        norm = np.linalg.norm(v)
        assert norm == 5.0

        # Sum
        total = np.sum(v)
        assert total == 7.0

        # Mean
        mean = np.mean(v)
        assert mean == 3.5

    def test_equality(self):
        """Test equality comparison."""
        v1 = Vector2([1.0, 2.0])
        v2 = Vector2([1.0, 2.0])
        v3 = Vector2([2.0, 3.0])

        assert np.array_equal(v1, v2)
        assert not np.array_equal(v1, v3)

    def test_indexing_and_slicing(self):
        """Test indexing and slicing operations."""
        v = Vector2([1.0, 2.0])

        # Indexing
        assert v[0] == 1.0
        assert v[1] == 2.0

        # Negative indexing
        assert v[-1] == 2.0
        assert v[-2] == 1.0

        # Slicing
        assert np.array_equal(v[:1], [1.0])
        assert np.array_equal(v[1:], [2.0])


class TestVector3:
    """Test cases for Vector3 class."""

    def test_creation_from_list(self):
        """Test Vector3 creation from list."""
        v = Vector3([1.0, 2.0, 3.0])
        assert isinstance(v, Vector3)
        assert v.shape == (3,)
        assert v[0] == 1.0
        assert v[1] == 2.0
        assert v[2] == 3.0

    def test_creation_from_tuple(self):
        """Test Vector3 creation from tuple."""
        v = Vector3((4.0, 5.0, 6.0))
        assert isinstance(v, Vector3)
        assert v.shape == (3,)
        assert v[0] == 4.0
        assert v[1] == 5.0
        assert v[2] == 6.0

    def test_creation_from_numpy_array(self):
        """Test Vector3 creation from numpy array."""
        arr = np.array([7.0, 8.0, 9.0])
        v = Vector3(arr)
        assert isinstance(v, Vector3)
        assert v.shape == (3,)
        assert v[0] == 7.0
        assert v[1] == 8.0
        assert v[2] == 9.0

    def test_creation_from_integers(self):
        """Test Vector3 creation from integers."""
        v = Vector3([1, 2, 3])
        assert isinstance(v, Vector3)
        assert v.shape == (3,)
        assert v[0] == 1
        assert v[1] == 2
        assert v[2] == 3

    def test_creation_from_mixed_types(self):
        """Test Vector3 creation from mixed numeric types."""
        v = Vector3([1, 2.5, 3])
        assert isinstance(v, Vector3)
        assert v.shape == (3,)
        assert v[0] == 1.0
        assert v[1] == 2.5
        assert v[2] == 3.0

    def test_invalid_length_too_short(self):
        """Test that Vector3 raises ValueError for too few elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 3 elements"):
            Vector3([1.0, 2.0])

    def test_invalid_length_too_long(self):
        """Test that Vector3 raises ValueError for too many elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 3 elements"):
            Vector3([1.0, 2.0, 3.0, 4.0])

    def test_invalid_empty_array(self):
        """Test that Vector3 raises ValueError for empty array."""
        with pytest.raises(ValueError, match="Input array must have exactly 3 elements"):
            Vector3([])

    def test_invalid_2d_array(self):
        """Test that Vector3 raises ValueError for 2D array."""
        with pytest.raises(ValueError, match="Input array must have exactly 3 elements"):
            Vector3([[1, 2, 3], [4, 5, 6]])

    def test_mathematical_operations(self):
        """Test basic mathematical operations."""
        v1 = Vector3([1.0, 2.0, 3.0])
        v2 = Vector3([4.0, 5.0, 6.0])

        # Addition
        result = v1 + v2
        assert np.allclose(result, [5.0, 7.0, 9.0])

        # Subtraction
        result = v2 - v1
        assert np.allclose(result, [3.0, 3.0, 3.0])

        # Scalar multiplication
        result = v1 * 2
        assert np.allclose(result, [2.0, 4.0, 6.0])

        # Dot product
        result = np.dot(v1, v2)
        assert result == 32.0  # 1*4 + 2*5 + 3*6

        # Cross product
        result = np.cross(v1, v2)
        expected = np.cross([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        assert np.allclose(result, expected)

    def test_numpy_compatibility(self):
        """Test that Vector3 works with numpy functions."""
        v = Vector3([3.0, 4.0, 0.0])

        # Norm
        norm = np.linalg.norm(v)
        assert norm == 5.0

        # Sum
        total = np.sum(v)
        assert total == 7.0

        # Mean
        mean = np.mean(v)
        assert mean == pytest.approx(7.0 / 3.0)

    def test_equality(self):
        """Test equality comparison."""
        v1 = Vector3([1.0, 2.0, 3.0])
        v2 = Vector3([1.0, 2.0, 3.0])
        v3 = Vector3([2.0, 3.0, 4.0])

        assert np.array_equal(v1, v2)
        assert not np.array_equal(v1, v3)

    def test_indexing_and_slicing(self):
        """Test indexing and slicing operations."""
        v = Vector3([1.0, 2.0, 3.0])

        # Indexing
        assert v[0] == 1.0
        assert v[1] == 2.0
        assert v[2] == 3.0

        # Negative indexing
        assert v[-1] == 3.0
        assert v[-2] == 2.0
        assert v[-3] == 1.0

        # Slicing
        assert np.array_equal(v[:2], [1.0, 2.0])
        assert np.array_equal(v[1:], [2.0, 3.0])
        assert np.array_equal(v[1:3], [2.0, 3.0])


class TestVector6:
    """Test cases for Vector6 class."""

    def test_creation_from_list(self):
        """Test Vector6 creation from list."""
        v = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert isinstance(v, Vector6)
        assert v.shape == (6,)
        for i in range(6):
            assert v[i] == float(i + 1)

    def test_creation_from_tuple(self):
        """Test Vector6 creation from tuple."""
        v = Vector6((7.0, 8.0, 9.0, 10.0, 11.0, 12.0))
        assert isinstance(v, Vector6)
        assert v.shape == (6,)
        for i in range(6):
            assert v[i] == float(i + 7)

    def test_creation_from_numpy_array(self):
        """Test Vector6 creation from numpy array."""
        arr = np.array([13.0, 14.0, 15.0, 16.0, 17.0, 18.0])
        v = Vector6(arr)
        assert isinstance(v, Vector6)
        assert v.shape == (6,)
        for i in range(6):
            assert v[i] == float(i + 13)

    def test_creation_from_integers(self):
        """Test Vector6 creation from integers."""
        v = Vector6([1, 2, 3, 4, 5, 6])
        assert isinstance(v, Vector6)
        assert v.shape == (6,)
        for i in range(6):
            assert v[i] == i + 1

    def test_creation_from_mixed_types(self):
        """Test Vector6 creation from mixed numeric types."""
        v = Vector6([1, 2.5, 3, 4.0, 5, 6.2])
        assert isinstance(v, Vector6)
        assert v.shape == (6,)
        assert v[0] == 1.0
        assert v[1] == 2.5
        assert v[2] == 3.0
        assert v[3] == 4.0
        assert v[4] == 5.0
        assert v[5] == 6.2

    def test_invalid_length_too_short(self):
        """Test that Vector6 raises ValueError for too few elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 6 elements"):
            Vector6([1.0, 2.0, 3.0, 4.0, 5.0])

    def test_invalid_length_too_long(self):
        """Test that Vector6 raises ValueError for too many elements."""
        with pytest.raises(ValueError, match="Input array must have exactly 6 elements"):
            Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])

    def test_invalid_empty_array(self):
        """Test that Vector6 raises ValueError for empty array."""
        with pytest.raises(ValueError, match="Input array must have exactly 6 elements"):
            Vector6([])

    def test_invalid_2d_array(self):
        """Test that Vector6 raises ValueError for 2D array."""
        with pytest.raises(ValueError, match="Input array must have exactly 6 elements"):
            Vector6([[1, 2, 3], [4, 5, 6]])

    def test_mathematical_operations(self):
        """Test basic mathematical operations."""
        v1 = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        v2 = Vector6([6.0, 5.0, 4.0, 3.0, 2.0, 1.0])

        # Addition
        result = v1 + v2
        assert np.allclose(result, [7.0, 7.0, 7.0, 7.0, 7.0, 7.0])

        # Subtraction
        result = v1 - v2
        assert np.allclose(result, [-5.0, -3.0, -1.0, 1.0, 3.0, 5.0])

        # Scalar multiplication
        result = v1 * 2
        assert np.allclose(result, [2.0, 4.0, 6.0, 8.0, 10.0, 12.0])

        # Dot product
        result = np.dot(v1, v2)
        assert result == 56.0  # 1*6 + 2*5 + 3*4 + 4*3 + 5*2 + 6*1

    def test_numpy_compatibility(self):
        """Test that Vector6 works with numpy functions."""
        v = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        # Norm
        norm = np.linalg.norm(v)
        expected_norm = np.sqrt(1 + 4 + 9 + 16 + 25 + 36)
        assert norm == pytest.approx(expected_norm)

        # Sum
        total = np.sum(v)
        assert total == 21.0

        # Mean
        mean = np.mean(v)
        assert mean == 3.5

    def test_equality(self):
        """Test equality comparison."""
        v1 = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        v2 = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        v3 = Vector6([2.0, 3.0, 4.0, 5.0, 6.0, 7.0])

        assert np.array_equal(v1, v2)
        assert not np.array_equal(v1, v3)

    def test_indexing_and_slicing(self):
        """Test indexing and slicing operations."""
        v = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        # Indexing
        for i in range(6):
            assert v[i] == float(i + 1)

        # Negative indexing
        assert v[-1] == 6.0
        assert v[-2] == 5.0
        assert v[-6] == 1.0

        # Slicing
        assert np.array_equal(v[:3], [1.0, 2.0, 3.0])
        assert np.array_equal(v[3:], [4.0, 5.0, 6.0])
        assert np.array_equal(v[1:5], [2.0, 3.0, 4.0, 5.0])

    def test_pose_representation(self):
        """Test Vector6 as pose representation (position + rotation)."""
        # Common use case: [x, y, z, roll, pitch, yaw]
        pose = Vector6([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])

        # Extract position (first 3 elements)
        position = pose[:3]
        assert np.array_equal(position, [1.0, 2.0, 3.0])

        # Extract rotation (last 3 elements)
        rotation = pose[3:]
        assert np.array_equal(rotation, [0.1, 0.2, 0.3])


class TestVectorInteroperability:
    """Test interoperability between different vector types."""

    def test_vector_type_consistency(self):
        """Test that vector types maintain their type after operations."""
        v2 = Vector2([1.0, 2.0])
        v3 = Vector3([1.0, 2.0, 3.0])
        v6 = Vector6([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

        # Operations should preserve type where possible
        result_v2 = v2 * 2
        result_v3 = v3 * 2
        result_v6 = v6 * 2

        assert isinstance(result_v2, np.ndarray)  # May not preserve exact type due to numpy
        assert isinstance(result_v3, np.ndarray)
        assert isinstance(result_v6, np.ndarray)

        # But shape should be preserved
        assert result_v2.shape == (2,)
        assert result_v3.shape == (3,)
        assert result_v6.shape == (6,)

    def test_conversion_between_types(self):
        """Test conversion between vector types."""
        # Vector3 to Vector2 (take first 2 elements)
        v3 = Vector3([1.0, 2.0, 3.0])
        v2_from_v3 = Vector2(v3[:2])
        assert isinstance(v2_from_v3, Vector2)
        assert np.array_equal(v2_from_v3, [1.0, 2.0])

        # Vector2 to Vector3 (add zero)
        v2 = Vector2([4.0, 5.0])
        v3_from_v2 = Vector3(np.append(v2, 0.0))
        assert isinstance(v3_from_v2, Vector3)
        assert np.array_equal(v3_from_v2, [4.0, 5.0, 0.0])

    def test_numpy_array_compatibility(self):
        """Test that vectors can be used with standard numpy arrays."""
        v3 = Vector3([1.0, 2.0, 3.0])
        np_array = np.array([4.0, 5.0, 6.0])

        # Addition with numpy array
        result = v3 + np_array
        assert np.array_equal(result, [5.0, 7.0, 9.0])

        # Subtraction with numpy array
        result = np_array - v3
        assert np.array_equal(result, [3.0, 3.0, 3.0])

        # Element-wise multiplication
        result = v3 * np_array
        assert np.array_equal(result, [4.0, 10.0, 18.0])
