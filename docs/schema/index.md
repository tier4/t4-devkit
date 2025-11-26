# Dataset Schema

## Directory Structure

```shell
<DATASET_ID>/
└── <DATASET_VERSION>/
    ├── annotation/    ...schema tables in JSON format
    ├── data/          ...sensor raw data
    ├── input_bag/     ...original ROS bag file
    ├── map/           ...map files
    ├── lidarseg/      ...[OPTIONAL] LiDAR segmentation annotation
    └── status.json    ...dataset status information
```

## Schema Tables

Annotation information is stored in the `annotation` directory.

See [the document of dataset schema](./table.md) for details.

## Sensor Data

Raw sensor data is stored in the `data` directory.

See [the document of sensor data](./data.md) for details.

## Map Data

Map data is stored in the `map` directory.

It is structured as follows:

```shell
map/
├── lanelet2_map.osm    ...lanelet2 map file
└── pointcloud_map.pcd/ ...pointcloud map directory
```

## LiDAR Segmentation Annotation

T4 dataset can include 3D LiDAR segmentation annotation optionally.
The format is exactly the same as the [nuScenes format](https://www.nuscenes.org/nuscenes) with one additional `lidarseg.json` file.

Note that every `<lidarseg_token>.bin` consists of category labels for every LiDAR pointcloud at a keyframe.

```shell
lidarseg/
└── annotation/
    ├── <lidarseg_token>.bin    ...category labels for every LiDAR pointcloud at a keyframe
    ...
```

## status.json

`status.json` contains the information about the configuration used to generate the dataset.
