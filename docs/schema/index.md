# Dataset Schema

## Directory Structure

```shell
<DATASET_ID>/
└── <DATASET_VERSION>
    ├── annotation    ...schema tables in JSON format
    ├── data          ...sensor raw data
    ├── input_bag     ...original ROS bag file
    ├── map           ...map files
    └── status.json   ...dataset status information
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
├── lanelet2_map.osm
└── pointcloud_map.pcd
```

## status.json

`status.json` contains the information about the configuration used to generate the dataset.
