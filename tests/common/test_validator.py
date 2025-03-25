from __future__ import annotations

import numpy as np
import pytest
from attrs import define, field

from t4_devkit.common.validator import is_roi, is_trajectory, is_vector3, is_vector6


def test_is_vector3() -> None:
    @define
    class Foo:
        value = field(validator=is_vector3)

    # OK
    _ = Foo(np.ones(3))

    # Error cases
    with pytest.raises(ValueError):
        _ = Foo([1, 1, 1])  # Not numpy array

        _ = Foo(np.ones(2))  # Not 3D


def test_is_vector6() -> None:
    @define
    class Foo:
        value = field(validator=is_vector6)

    # OK
    _ = Foo(np.ones(6))

    # Error cases
    with pytest.raises(ValueError):
        _ = Foo([1, 1, 1, 1, 1, 1])  # Not numpy array

        _ = Foo(np.ones(4))  # Not 6D


def test_is_roi() -> None:
    @define
    class Foo:
        value = field(validator=is_roi)

    # OK
    _ = Foo([1, 1, 1, 1])
    _ = Foo((1, 1, 1, 1))
    _ = Foo(np.ones(4))

    # Error cases
    with pytest.raises(ValueError):
        _ = Foo(np.ones(3))  # Not 4D
        _ = Foo([1, 0, 1, 0])  # xmax < xmin, ymax < ymin


def test_is_trajectory() -> None:
    @define
    class Foo:
        value = field(validator=is_trajectory)

    # OK
    _ = Foo(np.ones((2, 2, 3)))

    with pytest.raises(ValueError):
        _ = Foo([1, 1, 1])  # Not numpy array
        _ = Foo(np.ones([2, 2]))  # Not (M, T, D)
        _ = Foo(np.ones([2, 2, 2]))  # Not (M, T, 3)
