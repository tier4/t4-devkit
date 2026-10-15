# Dataset Schema 1.0

T4Dataset 1.0 is the next major version of the dataset format. Datasets written before 1.0 are referred to as **0.x** and are described in [Dataset Schema](../index.md).

Main changes from 0.x:

- Every dataset has a `manifest.json` that declares the schema version, identity, contents and checksums. It replaces `status.json`.
- `sensor` and `calibrated_sensor` are merged into a single `sensor` table with a modality-specific block (`camera` or `lidar`).
- `sample` lists every frame of the recording, not only the annotated ones; `sample.has_key_frame` and `sample_data.is_key_frame` mark the annotated ones. Every `sample_data` belongs to a sample.
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

## Writing 1.0 Datasets

`DatasetWriter` writes a 1.0 dataset folder. Data files go first, then the tables and `manifest.json`:

```python
>>> from t4_devkit.schema.v1 import DatasetWriter
>>> writer = DatasetWriter("<DATASET_ID>/<DATASET_VERSION>")  # must not exist yet
>>> path, frame_count = writer.write_lidar("LIDAR_TOP", frames, fields)  # one Parquet file
>>> video = writer.write_camera("CAM_FRONT", images, frame_rate=10)  # one AV1 video
>>> writer.copy("<OLD_DATASET>/map", "map")  # files kept as they are
>>> manifest = writer.save(tables, manifest_info)  # tables, then manifest.json
```

`save` lists every table and every file under `data/`, `map/` and `input_bag/` in `manifest.json`, with its hash. It computes `capabilities` from the tables, and adds t4-devkit to `generators`. `manifest_info` gives the other manifest fields (identity, provenance, migration notes).

## Loading 0.x Datasets

`load_dataset()` reads a 0.x dataset (no `manifest.json`) by converting its tables to 1.0 records when loading, on a best-effort basis. Sensor data files stay as they are: one file per frame, and `sample_data.frame_index` is `null`.

Every 0.x frame becomes a `sample`: the files of all channels with the same frame number (e.g. `00042.jpg` and `00042.pcd.bin`, as the 0.x converter names them) form one frame. 0.x samples, which are annotated frames only, keep their tokens; 0.x samples of the same frame (one per camera image in camera-only datasets) are merged into the earliest one. A frame with a 2D label is a key frame.

Each 0.x `calibrated_sensor` row becomes a `sensor` row, keeping its token. The camera block takes its intrinsics and distortion from it, its size from `sample_data`, and the distortion model from the number of coefficients (0: `none`, 5: `plumb_bob`, 8: `rational_polynomial`). The LiDAR block is described from the first frame. The map is the dataset's own `map/` folder: `sha256` and `projector` are read from `map/lanelet2_map.osm` and `map/map_projector_info.yaml`, and map element ids (e.g. lamp ways) refer to it. An empty `log.data_captured` becomes the log's first sample time (ISO 8601, UTC).

Labels are `manual` unless 0.x marks them as autolabel (`provenance` = model names). Categories without `index` get their position in `category.json`, as the 0.x devkit reads them (all set or none). `surface_ann` rows become `object_ann` rows without an instance, with `bbox` computed from the mask. 0.x visibility `unavailable` (or any unknown level) becomes `visibility_token: null`, and the aliases `v0-40`, `v40-60`, `v60-80`, `v80-100` map to `none`, `partial`, `most`, `full`.

`vehicle_state` rows get `source: vehicle_interface` (where the 0.x converter reads them) and shift `FORWARD`/`HIGH` becomes `DRIVE`; `additional_info.speed` is dropped and the velocities are `null`. The 0.x `traffic_light` table (`primitive_id`) and `traffic_light_instance_map` table (`traffic_light_linestring_id`, which wins if both list a lamp) link a lamp instance to its lanelet2 way (`type=traffic_light`) and have no states: the way becomes that instance's `map_element` (`type: way`), and the 1.0 `traffic_light` table stays empty. Source LiDARs of a concatenation have no frames of their own in 0.x: they take the concatenated channel's format and `fields`, and `frame_count` is the number of concatenated frames whose `.info` file lists points from them.

1.0 requires some values that 0.x never stored. They are filled with these placeholders (`V0Converter.FALLBACKS`), which keep the dataset loadable but say nothing about it. In particular, `vehicle.model == "unknown"` means the vehicle dimensions are placeholders and must not be used, and `"unknown"` map IDs mean the map is not identified:

| Table / block   | Field                                                 | Placeholder                                                                                         |
| --------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `vehicle`       | `model`                                               | `"unknown"`                                                                                         |
| `vehicle`       | `length`, `width`, `height`, `wheel_base`             | `1.0`                                                                                               |
| `vehicle`       | `name`                                                | 0.x `log.vehicle`, `null` if empty                                                                  |
| `map`           | `map_id`, `version_id`                                | `"unknown"`                                                                                         |
| `map`           | `source`                                              | `"webauto"`                                                                                         |
| `ego_pose`      | `source`, `frame`                                     | `"localization"`, `"map"`                                                                           |
| `sensor.camera` | `is_rectified`                                        | `true`                                                                                              |
| `sensor.lidar`  | `frame_id`, `is_undistorted`, `container.compression` | `"base_link"`, `true`, `"none"`                                                                     |
| `sensor.lidar`  | `fields` (`.bin`)                                     | `x y z intensity channel return_type time_stamp`, cut to `num_pts_feats` (default 5), all `float32` |
