# Sensor Data

## LiDAR Point Cloud

LiDAR directory contains point cloud data as the name of `<LIDAR_CONCAT>` or `<LIDAR_TOP>`:

```shell
data/
└── LIDAR_CONCAT
    ├── <FRAME_ID>.pcd.bin
    ...
```

By default, each file contains `(x, y, z, intensity, ring_idx(=-1))` as `float32` values, and location coordinates are given with respect to the ego vehicle coordinate system.

Some datasets can store additional `float32` features for each point, such as `return_type` or `timestamp`. In that case, `sample_data.info_filename` should point to a pointcloud metainfo JSON file that includes `num_pts_feats`, which describes the total number of `float32` fields in each point.

Each file can be loaded using as follows:

```python
# Using NumPy
import numpy as np

def load_lidar_point_cloud(file_path, num_pts_feats: int = 5) -> np.ndarray:
    data = np.fromfile(file_path, dtype=np.float32)
    return data.reshape((-1, num_pts_feats))

# Using t4-devkit
from t4_devkit.dataclass import LidarPointCloud

def load_lidar_point_cloud_t4(file_path, metainfo_path: str | None = None) -> LidarPointCloud:
    return LidarPointCloud.from_file(file_path, metainfo_filepath=metainfo_path)
```

When `metainfo_filepath` is provided and the file exists, `t4-devkit` uses `num_pts_feats` from the metainfo JSON to reshape the binary pointcloud correctly. If the metainfo file is omitted or unavailable, `t4-devkit` falls back to the standard 5-feature layout.

Current `LidarPointCloud` and `SegmentationPointCloud` readers keep the first 4 dimensions `(x, y, z, intensity)` after reshaping. Additional point features are used to determine the row width and are not exposed in the returned point matrix.

Example pointcloud metainfo JSON:

```json
{
  "stamp": {
    "sec": 1710000000,
    "nanosec": 123456789
  },
  "num_pts_feats": 7,
  "sources": [
    {
      "sensor_token": "<SENSOR_TOKEN>",
      "idx_begin": 0,
      "length": 120000,
      "stamp": {
        "sec": 1710000000,
        "nanosec": 123456789
      }
    }
  ]
}
```

## Camera Image

Camera directory contains raw images as the name of `<CAM_XXX>`:

```shell
data/
├── CAM_BACK
│   ├── <FRAME_ID>.jpg
│   ...
├── CAM_BACK_LEFT
├── CAM_BACK_RIGHT
├── CAM_FRONT
...
```

## Radar Object

Radar directory contains radar object tracks

```shell
data/
├── RADAR_BACK
│   ├── <FRAME_ID>.pcd
│   ...
├── RADAR_BACK_LEFT
├── RADAR_BACK_RIGHT
├── RADAR_FRONT
...
```

Each file is based on NuScenes radar data format as follows:

```shell
# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z dyn_prop id rcs vx vy vx_comp vy_comp is_quality_valid ambig_state x_rms y_rms invalid_state pdh0 vx_rms vy_rms
SIZE 4 4 4 1 2 4 4 4 4 4 1 1 1 1 1 1 1 1
TYPE F F F I I F F F F F I I I I I I I I
COUNT 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
WIDTH 112
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 112
DATA binary
```

```python
from t4_devkit.dataclass import RadarPointCloud

def load_radar_point_cloud(file_path) -> RadarPointCloud:
    return RadarPointCloud.from_file(file_path)
```
