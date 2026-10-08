# Dataset Schema 1.0

!!! warning

    T4Dataset 1.0 is under development. This page is the agreed specification; `t4-devkit` support is being added step by step.

T4Dataset 1.0 is the next major version of the dataset format. Datasets written before 1.0 are referred to as **0.x** and are described in [Dataset Schema](../index.md).

Main changes from 0.x:

- Every dataset has a `manifest.json` that declares the schema version, identity, contents and checksums. It replaces `status.json`.
- `sensor` and `calibrated_sensor` are merged into a single `sensor` table with a modality-specific block (`camera` or `lidar`).
- Camera images are stored as one AV1 video per channel, and LiDAR point clouds as one Parquet file per channel. `sample_data.frame_index` addresses a frame inside that file.
- Every label row records how it was made: `annotation_type`, `provenance` and `confidence`.
- New tables for planning and language data: `vehicle`, `route`, `scenario`, `caption`. `traffic_light` is keyed by the lanelet2 regulatory element.
- Missing references are `null` instead of an empty string `""`.

## Version Detection

A dataset is 1.0 or later if `manifest.json` exists at the dataset root. Otherwise it is a 0.x dataset.

Readers must read `manifest.json` first and check `schema_version` before reading any table. A reader that does not support the declared version must report it as unsupported instead of guessing.

## Directory Structure

```shell
<DATASET_ID>/
└── <DATASET_VERSION>/
    ├── manifest.json        ...dataset identity, versions, contents and checksums
    ├── annotation/          ...schema tables in JSON format
    ├── data/                ...sensor data, one file per channel
    │   ├── <CAMERA_CHANNEL>/
    │   │   └── <CAMERA_CHANNEL>.mp4
    │   └── <LIDAR_CHANNEL>/
    │       └── <LIDAR_CHANNEL>.parquet
    ├── input_bag/           ...original ROS bag file
    └── map/                 ...map files
```

See [Schema Tables](./table.md) for the tables and [Sensor Data](./data.md) for the sensor files.

## manifest.json

`manifest.json` is always JSON. It is written by the dataset producer and updated whenever a table or sensor file changes.

```json
manifest {
  "schema_version":                 <str> -- Version of this specification, e.g. "1.0.0". Not the t4-devkit version.
  "dataset_id":                     <str> -- Dataset ID (= Web.Auto annotation_dataset_id).
  "version":                        <int> -- Dataset version (= Web.Auto version_id).
  "created_at":                     <str> -- Creation time of the dataset from the rosbag, ISO 8601.
  "generators":                     <[Generator;N]> -- Every tool and library that produced this dataset.
  "capabilities":                   <Capabilities> -- What the dataset contains.
  "annotation_specifications":      <{str: AnnotationSpecification}> -- Annotation specification per task.
  "tables":                         <{str: TableEntry}> -- Every table file, keyed by table name.
  "assets":                         <[AssetEntry;N]> -- Every sensor, map and input bag file.
  "provenance":                     <Provenance> -- Where the data came from.
  "project_id":                     <option[str]> -- Web.Auto project ID.
  "source_project_id":              <option[str]> -- Web.Auto source project ID.
  "is_synthetic":                   <bool> -- Whether the data is synthetic (= Web.Auto is_synthetic_data).
  "is_discontinuous":               <option[bool]> -- Whether the recording has gaps (= Web.Auto).
  "migrated_from_schema_version":   <option[str]> -- Source version if the dataset was migrated, e.g. "0.x". `null` for datasets produced as 1.0.
  "migration_notes":                <option[[str;N]]> -- Notes on anything lost or changed during migration.
}
```

Only stable Web.Auto identifiers are stored. Values that change in Web.Auto after the dataset is produced (environment, map names, vehicle IDs) are not copied into the dataset.

### `Generator`

```json
Generator {
  "name":       <str> -- Tool or library name, e.g. "t4-devkit", "tier4_perception_dataset".
  "version":    <str> -- Version or commit hash.
}
```

### `Capabilities`

```json
Capabilities {
  "tasks":          <[enum[detection3d, detection2d, segmentation2d, segmentation3d, keypoint, traffic_light, prediction, planning];N]> -- Tasks the dataset can be used for.
  "modalities": {
    "camera":       <[str;N]> -- Camera channel names.
    "lidar":        <[str;N]> -- LiDAR channel names.
    "radar":        <[str;N]> -- Radar channel names.
  }
  "map":            <bool> -- Whether a lanelet2 map is included.
  "route":          <bool> -- Whether the `route` table is filled.
  "traffic_light":  <bool> -- Whether the `traffic_light` table is filled.
  "vehicle_state":  <bool> -- Whether the `vehicle_state` table is filled.
  "scenario":       <bool> -- Whether the `scenario` table is filled.
}
```

### `AnnotationSpecification`

```json
AnnotationSpecification {
  "id":         <str> -- Annotation specification ID.
  "version":    <option[str]> -- Specification version, e.g. "4.1.9". `null` if unknown.
}
```

### `TableEntry` and `AssetEntry`

```json
TableEntry {
  "path":       <str> -- Path relative to the dataset root, e.g. "annotation/sample.json".
  "sha256":     <str> -- SHA-256 of the file.
}

AssetEntry {
  "path":       <str> -- Path relative to the dataset root, e.g. "data/CAM_FRONT/CAM_FRONT.mp4".
  "sha256":     <str> -- SHA-256 of the file.
  "bytes":      <int> -- File size in bytes.
}
```

There is one `AssetEntry` per file, including each file in `input_bag/`.

### `Provenance`

```json
Provenance {
  "rosbag": {
    "log_file_ids":     <[str;N]> -- Web.Auto log_file_id(s). Empty for force-pushed datasets.
    "storage":          <option[enum[sqlite3, mcap, other]]> -- rosbag storage format.
    "record_start":     <str> -- Recording start, ISO 8601 UTC.
    "record_end":       <str> -- Recording end, ISO 8601 UTC.
  }
  "topics":                     <{str: str}> -- ROS topic used for each channel, keyed by channel name.
  "process_config_id":          <option[str]> -- Web.Auto processing configuration ID.
  "process_config_version_id":  <option[int]> -- Web.Auto processing configuration version.
}
```
