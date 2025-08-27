# Sensor Data

## LiDAR Point Cloud

LiDAR directory contains point cloud data as the name of `<LIDAR_CONCAT>` or `<LIDAR_TOP>`:

```shell
data/
└── LIDAR_CONCAT
    ├── <FRAME_ID>.pcd.bin
    ...
```

Each file contains `(x, y, z, intensity, ring_idx(=-1))`, and location coordinates are given with respect to the ego vehicle coordinate system.

Each file can be loaded using as follows:

```python
# Using NumPy
import numpy as np

def load_lidar_point_cloud(file_path) -> np.ndarray:
    data = np.fromfile(file_path, dtype=np.float32) # (N*5,)
    return data.reshape((-1, 5)) # (N, 5)

# Using t4-devkit
from t4_devkit.dataclass import LidarPointCloud

def load_lidar_point_cloud_t4(file_path) -> LidarPointCloud:
    return LidarPointCloud.from_file(file_path)
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
