# Dataset Requirements

## Structure (`STR`)

| ID       | Name                          | Severity | Description                                                          |
| -------- | ----------------------------- | -------- | -------------------------------------------------------------------- |
| `STR001` | `version-dir-presence`        | `Warn`   | `version/` directory exists under the dataset root directory.        |
| `STR002` | `annotation-dir-presence`     | `Error`  | `annotation/` directory exists under the dataset root directory.     |
| `STR003` | `data-dir-presence`           | `Error`  | `data/` directory exists under the dataset root directory.           |
| `STR004` | `map-dir-presence`            | `Warn`   | `map/` directory exists under the dataset root directory.            |
| `STR005` | `bag-dir-presence`            | `Warn`   | `input_bag/` directory exists under the dataset root directory.      |
| `STR006` | `status-file-presence`        | `Warn`   | `status.json` file exists under the dataset root directory.          |
| `STR007` | `schema-files-presence`       | `Error`  | Mandatory schema JSON files exist under the `annotation/` directory. |
| `STR008` | `lanelet-file-presence`       | `Warn`   | `lanelet2_map.osm` file exists under the `map/` directory.           |
| `STR009` | `pointcloud-map-dir-presence` | `Warn`   | `pointcloud_map.pcd` directory exists under the `map/` directory.    |

## Schema Record (`REC`)

| ID       | Name                          | Severity | Description                             |
| -------- | ----------------------------- | -------- | --------------------------------------- |
| `REC001` | `scene-single`                | `Error`  | `Scene` record is a single.             |
| `REC002` | `sample-not-empty`            | `Error`  | `Sample` record is not empty.           |
| `REC003` | `sample-data-not-empty`       | `Error`  | `SampleData` record is not empty.       |
| `REC004` | `ego-pose-not-empty`          | `Error`  | `EgoPose` record is not empty.          |
| `REC005` | `calibrated-sensor-non-empty` | `Error`  | `CalibratedSensor` record is not empty. |
| `REC006` | `instance-not-empty`          | `Error`  | `Instance` record is not empty.         |

## Reference (`REF`)

| ID       | Name                                  | Severity | Description                                                               |
| -------- | ------------------------------------- | -------- | ------------------------------------------------------------------------- |
| `REF001` | `scene-to-log`                        | `Error`  | `Scene.log_token` refers to `Log` record.                                 |
| `REF002` | `scene-to-first-sample`               | `Error`  | `Scene.first_sample_token` refers to `Sample` record.                     |
| `REF003` | `scene-to-last-sample`                | `Error`  | `Scene.last_sample_token` refers to `Sample` record.                      |
| `REF004` | `sample-to-scene`                     | `Error`  | `Sample.scene_token` refers to `Scene` record.                            |
| `REF005` | `sample-data-to-sample`               | `Error`  | `SampleData.sample_token` refers to `Sample` record.                      |
| `REF006` | `sample-data-to-ego-pose`             | `Error`  | `SampleData.ego_pose_token` refers to `EgoPose` record.                   |
| `REF007` | `sample-data-to-calibrated-sensor`    | `Error`  | `SampleData.calibrated_sensor_token` refers to `CalibratedSensor` record. |
| `REF008` | `calibrated-sensor-to-sensor`         | `Error`  | `CalibratedSensor.sensor_token` refers to `Sensor` record.                |
| `REF009` | `instance-to-category`                | `Error`  | `Instance.category_token` refers to `Category` record.                    |
| `REF010` | `instance-to-first-sample-annotation` | `Error`  | `Instance.first_annotation_token` refers to `SampleAnnotation` record.    |
| `REF011` | `instance-to-last-sample-annotation`  | `Error`  | `Instance.last_annotation_token` refers to `SampleAnnotation` record.     |
| `REF012` | `lidarseg-to-sample-data`             | `Error`  | `LidarSeg.sample_data_token` refers to `SampleData` record.               |
| `REF013` | `sample-data-filename-presence`       | `Error`  | `SampleData.filename` exists.                                             |
| `REF014` | `sample-data-info-filename-presence`  | `Error`  | `SampleData.info_filename` exists if it is not `None`.                    |
| `REF015` | `lidarseg-filename-presence`          | `Error`  | `LidarSeg.filename` exists if `lidarseg.json` exists.                     |

## Format (`FMT`)

| ID       | Name                      | Severity | Description                                       |
| -------- | ------------------------- | -------- | ------------------------------------------------- |
| `FMT001` | `attribute-field`         | `Error`  | All types of `Attribute` fields are valid.        |
| `FMT002` | `calibrated-sensor-field` | `Error`  | All types of `CalibratedSensor` fields are valid. |
| `FMT003` | `category-field`          | `Error`  | All types of `Category` fields are valid.         |
| `FMT004` | `ego-pose-field`          | `Error`  | All types of `EgoPose` fields are valid.          |
| `FMT005` | `instance-field`          | `Error`  | All types of `Instance` fields are valid.         |
| `FMT006` | `log-field`               | `Error`  | All types of `Log` fields are valid.              |
| `FMT007` | `map-field`               | `Error`  | All types of `Map` fields are valid.              |
| `FMT008` | `sample-field`            | `Error`  | All types of `Sample` fields are valid.           |
| `FMT009` | `sample-annotation-field` | `Error`  | All types of `SampleAnnotation` fields are valid. |
| `FMT010` | `sample-data-field`       | `Error`  | All types of `SampleData` fields are valid.       |
| `FMT011` | `scene-field`             | `Error`  | All types of `Scene` fields are valid.            |
| `FMT012` | `sensor-field`            | `Error`  | All types of `Sensor` fields are valid.           |
| `FMT013` | `visibility-field`        | `Error`  | All types of `Visibility` fields are valid.       |
| `FMT014` | `lidarseg-field`          | `Error`  | All types of `Lidarseg` fields are valid.         |
| `FMT015` | `object-ann-field`        | `Error`  | All types of `ObjectAnn` fields are valid.        |
| `FMT016` | `surface-ann-field`       | `Error`  | All types of `SurfaceAnn` fields are valid.       |
| `FMT017` | `keypoint-field`          | `Error`  | All types of `Keypoint` fields are valid.         |
| `FMT018` | `vehicle-state-field`     | `Error`  | All types of `VehicleState` fields are valid.     |

## Tier4 Instance (`TIV`)

| ID       | Name         | Severity | Description                                     |
| -------- | ------------ | -------- | ----------------------------------------------- |
| `TIV001` | `load-tier4` | `Error`  | Ensure `Tier4` instance is loaded successfully. |
