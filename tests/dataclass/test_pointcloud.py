from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from t4_devkit.dataclass.pointcloud import (
    LidarPointCloud,
    PointCloudMetainfo,
    PointCloudSourceInfo,
    RadarPointCloud,
    SegmentationPointCloud,
    Stamp,
)


def _source(sensor_token: str, idx_begin: int, length: int) -> PointCloudSourceInfo:
    return PointCloudSourceInfo(
        sensor_token=sensor_token,
        idx_begin=idx_begin,
        length=length,
        stamp=Stamp(sec=1, nanosec=0),
    )


def _metainfo(sources: list[PointCloudSourceInfo], num_pts_feats: int = 5) -> PointCloudMetainfo:
    return PointCloudMetainfo(
        stamp=Stamp(sec=10, nanosec=500),
        sources=sources,
        num_pts_feats=num_pts_feats,
    )


def test_stamp_in_seconds() -> None:
    stamp = Stamp(sec=1, nanosec=250_000_000)

    assert stamp.in_seconds == 1.25


def test_pointcloud_source_info_converts_stamp_dict() -> None:
    source = PointCloudSourceInfo(
        sensor_token="lidar_front",
        idx_begin=0,
        length=2,
        stamp={"sec": 3, "nanosec": 4},
    )

    assert source.stamp == Stamp(sec=3, nanosec=4)


def test_pointcloud_metainfo_from_file(tmp_path: Path) -> None:
    filepath = tmp_path / "pointcloud.json"
    filepath.write_text(
        json.dumps(
            {
                "stamp": {"sec": 1, "nanosec": 2},
                "sources": [
                    {
                        "sensor_token": "lidar_front",
                        "idx_begin": 0,
                        "length": 2,
                        "stamp": {"sec": 3, "nanosec": 4},
                    },
                    {
                        "sensor_token": "lidar_rear",
                        "idx_begin": 2,
                        "length": 1,
                        "stamp": {"sec": 5, "nanosec": 6},
                    },
                ],
                "num_pts_feats": 6,
            }
        )
    )

    metainfo = PointCloudMetainfo.from_file(str(filepath))

    assert metainfo.stamp == Stamp(sec=1, nanosec=2)
    assert metainfo.source_tokens == ["lidar_front", "lidar_rear"]
    assert metainfo.num_pts_feats == 6
    assert metainfo.sources[0].stamp == Stamp(sec=3, nanosec=4)


def test_lidar_pointcloud_num_points_and_dimension_validation() -> None:
    pointcloud = LidarPointCloud(points=np.zeros((4, 3)))

    assert pointcloud.num_dims() == 4
    assert pointcloud.num_points() == 3

    with pytest.raises(ValueError, match="Expected point dimension is 4"):
        LidarPointCloud(points=np.zeros((3, 3)))


def test_radar_pointcloud_num_dims() -> None:
    pointcloud = RadarPointCloud(points=np.zeros((18, 2)))

    assert pointcloud.num_dims() == 18
    assert pointcloud.num_points() == 2


def test_pointcloud_transform_operations() -> None:
    pointcloud = LidarPointCloud(
        points=np.array(
            [
                [0.0, 1.0],
                [0.0, 0.0],
                [0.0, 0.0],
                [10.0, 20.0],
            ]
        )
    )

    pointcloud.translate(np.array([1.0, 2.0, 3.0]))
    assert np.allclose(
        pointcloud.points,
        np.array(
            [
                [1.0, 2.0],
                [2.0, 2.0],
                [3.0, 3.0],
                [10.0, 20.0],
            ]
        ),
    )

    pointcloud.rotate(np.diag([1.0, -1.0, 1.0]))
    assert np.allclose(
        pointcloud.points[:3, :],
        np.array(
            [
                [1.0, 2.0],
                [-2.0, -2.0],
                [3.0, 3.0],
            ]
        ),
    )

    transform = np.eye(4)
    transform[:3, 3] = np.array([1.0, 1.0, 1.0])
    pointcloud.transform(transform)
    assert np.allclose(
        pointcloud.points,
        np.array(
            [
                [2.0, 3.0],
                [-1.0, -1.0],
                [4.0, 4.0],
                [10.0, 20.0],
            ]
        ),
    )


def test_pointcloud_metainfo_accepts_complete_non_overlapping_sources() -> None:
    pointcloud = LidarPointCloud(
        points=np.zeros((4, 4)),
        metainfo=_metainfo([_source("lidar_front", 0, 2), _source("lidar_rear", 2, 2)]),
    )

    assert pointcloud.metainfo is not None
    assert pointcloud.metainfo.source_tokens == ["lidar_front", "lidar_rear"]


@pytest.mark.parametrize(
    ("sources", "match"),
    [
        ([_source("lidar_front", -1, 1)], "negative idx_begin"),
        ([_source("lidar_front", 0, -1)], "negative length"),
        ([_source("lidar_front", 3, 2)], "exceeds point cloud size"),
        ([_source("lidar_front", 0, 1), _source("lidar_rear", 2, 2)], "Gap detected"),
        ([_source("lidar_front", 0, 3), _source("lidar_rear", 2, 2)], "Overlap detected"),
        ([_source("lidar_front", 0, 3)], "Incomplete coverage"),
    ],
)
def test_pointcloud_metainfo_rejects_invalid_source_coverage(
    sources: list[PointCloudSourceInfo], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        LidarPointCloud(points=np.zeros((4, 4)), metainfo=_metainfo(sources))


def test_pointcloud_metainfo_ignores_zero_length_sources() -> None:
    pointcloud = LidarPointCloud(
        points=np.zeros((4, 2)),
        metainfo=_metainfo([_source("empty_lidar", 0, 0), _source("lidar_front", 0, 2)]),
    )

    assert pointcloud.num_points() == 2


def test_split_by_sensor_requires_metainfo() -> None:
    pointcloud = LidarPointCloud(points=np.zeros((4, 2)))

    with pytest.raises(ValueError, match="metainfo is None"):
        pointcloud.split_by_sensor()


def test_split_by_sensor_returns_independent_lidar_pointclouds() -> None:
    points = np.arange(24, dtype=np.float32).reshape(4, 6)
    pointcloud = LidarPointCloud(
        points=points,
        metainfo=_metainfo([_source("lidar_front", 0, 2), _source("lidar_rear", 2, 4)]),
    )

    split_pointclouds = pointcloud.split_by_sensor()

    assert set(split_pointclouds) == {"lidar_front", "lidar_rear"}
    assert isinstance(split_pointclouds["lidar_front"], LidarPointCloud)
    assert isinstance(split_pointclouds["lidar_rear"], LidarPointCloud)
    assert split_pointclouds["lidar_front"].metainfo is None
    assert split_pointclouds["lidar_rear"].metainfo is None
    assert np.array_equal(split_pointclouds["lidar_front"].points, points[:, :2])
    assert np.array_equal(split_pointclouds["lidar_rear"].points, points[:, 2:6])

    split_pointclouds["lidar_front"].points[0, 0] = -1.0
    assert pointcloud.points[0, 0] != -1.0


def test_segmentation_pointcloud_split_by_sensor_splits_labels_and_copies() -> None:
    points = np.arange(24, dtype=np.float32).reshape(4, 6)
    labels = np.array([10, 11, 12, 13, 14, 15], dtype=np.uint8)
    pointcloud = SegmentationPointCloud(
        points=points,
        labels=labels,
        metainfo=_metainfo([_source("lidar_front", 0, 2), _source("lidar_rear", 2, 4)]),
    )

    split_pointclouds = pointcloud.split_by_sensor()

    assert isinstance(split_pointclouds["lidar_front"], SegmentationPointCloud)
    assert isinstance(split_pointclouds["lidar_rear"], SegmentationPointCloud)
    assert np.array_equal(split_pointclouds["lidar_front"].points, points[:, :2])
    assert np.array_equal(split_pointclouds["lidar_rear"].points, points[:, 2:6])
    assert np.array_equal(split_pointclouds["lidar_front"].labels, labels[:2])
    assert np.array_equal(split_pointclouds["lidar_rear"].labels, labels[2:6])

    split_pointclouds["lidar_front"].labels[0] = 255
    assert pointcloud.labels[0] != 255


def test_lidar_pointcloud_from_file_reads_points_and_metainfo(tmp_path: Path) -> None:
    bin_filepath = tmp_path / "pointcloud.bin"
    metainfo_filepath = tmp_path / "pointcloud.json"
    scan = np.array(
        [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [6.0, 7.0, 8.0, 9.0, 10.0],
        ],
        dtype=np.float32,
    )
    scan.tofile(bin_filepath)
    metainfo_filepath.write_text(
        json.dumps(
            {
                "stamp": {"sec": 1, "nanosec": 2},
                "sources": [
                    {
                        "sensor_token": "lidar_front",
                        "idx_begin": 0,
                        "length": 2,
                        "stamp": {"sec": 3, "nanosec": 4},
                    }
                ],
                "num_pts_feats": 5,
            }
        )
    )

    pointcloud = LidarPointCloud.from_file(str(bin_filepath), str(metainfo_filepath))

    assert np.array_equal(pointcloud.points, scan[:, :4].T)
    assert pointcloud.metainfo is not None
    assert pointcloud.metainfo.source_tokens == ["lidar_front"]


def test_segmentation_pointcloud_from_file_reads_points_labels_and_metainfo(
    tmp_path: Path,
) -> None:
    point_filepath = tmp_path / "pointcloud.bin"
    label_filepath = tmp_path / "labels.bin"
    metainfo_filepath = tmp_path / "pointcloud.json"
    scan = np.array(
        [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [6.0, 7.0, 8.0, 9.0, 10.0],
        ],
        dtype=np.float32,
    )
    labels = np.array([1, 2], dtype=np.uint8)
    scan.tofile(point_filepath)
    labels.tofile(label_filepath)
    metainfo_filepath.write_text(
        json.dumps(
            {
                "stamp": {"sec": 1, "nanosec": 2},
                "sources": [
                    {
                        "sensor_token": "lidar_front",
                        "idx_begin": 0,
                        "length": 2,
                        "stamp": {"sec": 3, "nanosec": 4},
                    }
                ],
                "num_pts_feats": 5,
            }
        )
    )

    pointcloud = SegmentationPointCloud.from_file(
        str(point_filepath), str(label_filepath), str(metainfo_filepath)
    )

    assert np.array_equal(pointcloud.points, scan[:, :4].T)
    assert np.array_equal(pointcloud.labels, labels)
    assert pointcloud.metainfo is not None
    assert pointcloud.metainfo.source_tokens == ["lidar_front"]
