# Dataset Requirements

## Structure (`STR`)

| ID       | Name                          | Severity  | Description                                                          |
| -------- | ----------------------------- | --------- | -------------------------------------------------------------------- |
| `STR001` | `version-dir-presence`        | `WARNING` | `version/` directory exists under the dataset root directory.        |
| `STR002` | `annotation-dir-presence`     | `ERROR`   | `annotation/` directory exists under the dataset root directory.     |
| `STR003` | `data-dir-presence`           | `ERROR`   | `data/` directory exists under the dataset root directory.           |
| `STR004` | `map-dir-presence`            | `WARNING` | `map/` directory exists under the dataset root directory.            |
| `STR005` | `bag-dir-presence`            | `WARNING` | `input_bag/` directory exists under the dataset root directory.      |
| `STR006` | `status-file-presence`        | `WARNING` | `status.json` file exists under the dataset root directory.          |
| `STR007` | `schema-files-presence`       | `ERROR`   | Mandatory schema JSON files exist under the `annotation/` directory. |
| `STR008` | `lanelet-file-presence`       | `WARNING` | `lanelet2_map.osm` file exists under the `map/` directory.           |
| `STR009` | `pointcloud-map-dir-presence` | `WARNING` | `pointcloud_map.pcd` directory exists under the `map/` directory.    |

## Schema Record (`REC`)

| ID       | Name                          | Severity | Description                                                                              |
| -------- | ----------------------------- | -------- | ---------------------------------------------------------------------------------------- |
| `REC001` | `scene-single`                | `ERROR`  | `Scene` record is a single.                                                              |
| `REC002` | `sample-not-empty`            | `ERROR`  | `Sample` record is not empty.                                                            |
| `REC003` | `sample-data-not-empty`       | `ERROR`  | `SampleData` record is not empty.                                                        |
| `REC004` | `ego-pose-not-empty`          | `ERROR`  | `EgoPose` record is not empty.                                                           |
| `REC005` | `calibrated-sensor-non-empty` | `ERROR`  | `CalibratedSensor` record is not empty.                                                  |
| `REC006` | `instance-not-empty`          | `ERROR`  | `Instance` record is not empty if either 'SampleAnnotation' or 'ObjectAnn' is not empty. |

## Reference (`REF`)

| ID       | Name                                  | Severity | Description                                                               |
| -------- | ------------------------------------- | -------- | ------------------------------------------------------------------------- |
| `REF001` | `scene-to-log`                        | `ERROR`  | `Scene.log_token` refers to `Log` record.                                 |
| `REF002` | `scene-to-first-sample`               | `ERROR`  | `Scene.first_sample_token` refers to `Sample` record.                     |
| `REF003` | `scene-to-last-sample`                | `ERROR`  | `Scene.last_sample_token` refers to `Sample` record.                      |
| `REF004` | `sample-to-scene`                     | `ERROR`  | `Sample.scene_token` refers to `Scene` record.                            |
| `REF005` | `sample-data-to-sample`               | `ERROR`  | `SampleData.sample_token` refers to `Sample` record.                      |
| `REF006` | `sample-data-to-ego-pose`             | `ERROR`  | `SampleData.ego_pose_token` refers to `EgoPose` record.                   |
| `REF007` | `sample-data-to-calibrated-sensor`    | `ERROR`  | `SampleData.calibrated_sensor_token` refers to `CalibratedSensor` record. |
| `REF008` | `calibrated-sensor-to-sensor`         | `ERROR`  | `CalibratedSensor.sensor_token` refers to `Sensor` record.                |
| `REF009` | `instance-to-category`                | `ERROR`  | `Instance.category_token` refers to `Category` record.                    |
| `REF010` | `instance-to-first-sample-annotation` | `ERROR`  | `Instance.first_annotation_token` refers to `SampleAnnotation` record.    |
| `REF011` | `instance-to-last-sample-annotation`  | `ERROR`  | `Instance.last_annotation_token` refers to `SampleAnnotation` record.     |
| `REF012` | `lidarseg-to-sample-data`             | `ERROR`  | `LidarSeg.sample_data_token` refers to `SampleData` record.               |
| `REF013` | `sample-data-filename-presence`       | `ERROR`  | `SampleData.filename` exists.                                             |
| `REF014` | `sample-data-info-filename-presence`  | `ERROR`  | `SampleData.info_filename` exists if it is not `None`.                    |
| `REF015` | `lidarseg-filename-presence`          | `ERROR`  | `LidarSeg.filename` exists if `lidarseg.json` exists.                     |

## Format (`FMT`)

| ID       | Name                      | Severity | Description                                       |
| -------- | ------------------------- | -------- | ------------------------------------------------- |
| `FMT001` | `attribute-field`         | `ERROR`  | All types of `Attribute` fields are valid.        |
| `FMT002` | `calibrated-sensor-field` | `ERROR`  | All types of `CalibratedSensor` fields are valid. |
| `FMT003` | `category-field`          | `ERROR`  | All types of `Category` fields are valid.         |
| `FMT004` | `ego-pose-field`          | `ERROR`  | All types of `EgoPose` fields are valid.          |
| `FMT005` | `instance-field`          | `ERROR`  | All types of `Instance` fields are valid.         |
| `FMT006` | `log-field`               | `ERROR`  | All types of `Log` fields are valid.              |
| `FMT007` | `map-field`               | `ERROR`  | All types of `Map` fields are valid.              |
| `FMT008` | `sample-field`            | `ERROR`  | All types of `Sample` fields are valid.           |
| `FMT009` | `sample-annotation-field` | `ERROR`  | All types of `SampleAnnotation` fields are valid. |
| `FMT010` | `sample-data-field`       | `ERROR`  | All types of `SampleData` fields are valid.       |
| `FMT011` | `scene-field`             | `ERROR`  | All types of `Scene` fields are valid.            |
| `FMT012` | `sensor-field`            | `ERROR`  | All types of `Sensor` fields are valid.           |
| `FMT013` | `visibility-field`        | `ERROR`  | All types of `Visibility` fields are valid.       |
| `FMT014` | `lidarseg-field`          | `ERROR`  | All types of `Lidarseg` fields are valid.         |
| `FMT015` | `object-ann-field`        | `ERROR`  | All types of `ObjectAnn` fields are valid.        |
| `FMT016` | `surface-ann-field`       | `ERROR`  | All types of `SurfaceAnn` fields are valid.       |
| `FMT017` | `keypoint-field`          | `ERROR`  | All types of `Keypoint` fields are valid.         |
| `FMT018` | `vehicle-state-field`     | `ERROR`  | All types of `VehicleState` fields are valid.     |

## Tier4 Instance (`TIV`)

| ID       | Name         | Severity | Description                                     |
| -------- | ------------ | -------- | ----------------------------------------------- |
| `TIV001` | `load-tier4` | `ERROR`  | Ensure `Tier4` instance is loaded successfully. |
