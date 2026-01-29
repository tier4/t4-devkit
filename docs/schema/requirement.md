# Dataset Requirements

## Structure (`STR`)

| ID       | Name                          | Severity  | Fixable | Description                                                          |
| -------- | ----------------------------- | --------- | ------- | -------------------------------------------------------------------- |
| `STR001` | `version-dir-presence`        | `WARNING` | `N/A`   | `version/` directory exists under the dataset root directory.        |
| `STR002` | `annotation-dir-presence`     | `ERROR`   | `N/A`   | `annotation/` directory exists under the dataset root directory.     |
| `STR003` | `data-dir-presence`           | `ERROR`   | `N/A`   | `data/` directory exists under the dataset root directory.           |
| `STR004` | `map-dir-presence`            | `WARNING` | `N/A`   | `map/` directory exists under the dataset root directory.            |
| `STR005` | `bag-dir-presence`            | `WARNING` | `N/A`   | `input_bag/` directory exists under the dataset root directory.      |
| `STR006` | `status-file-presence`        | `WARNING` | `N/A`   | `status.json` file exists under the dataset root directory.          |
| `STR007` | `schema-files-presence`       | `ERROR`   | `N/A`   | Mandatory schema JSON files exist under the `annotation/` directory. |
| `STR008` | `lanelet-file-presence`       | `WARNING` | `N/A`   | `lanelet2_map.osm` file exists under the `map/` directory.           |
| `STR009` | `pointcloud-map-dir-presence` | `WARNING` | `N/A`   | `pointcloud_map.pcd` directory exists under the `map/` directory.    |

## Schema Record (`REC`)

| ID       | Name                          | Severity | Fixable | Description                                                                                     |
| -------- | ----------------------------- | -------- | ------- | ----------------------------------------------------------------------------------------------- |
| `REC001` | `scene-single`                | `ERROR`  | `N/A`   | `Scene` record is a single.                                                                     |
| `REC002` | `sample-not-empty`            | `ERROR`  | `N/A`   | `Sample` record is not empty.                                                                   |
| `REC003` | `sample-data-not-empty`       | `ERROR`  | `N/A`   | `SampleData` record is not empty.                                                               |
| `REC004` | `ego-pose-not-empty`          | `ERROR`  | `N/A`   | `EgoPose` record is not empty.                                                                  |
| `REC005` | `calibrated-sensor-non-empty` | `ERROR`  | `N/A`   | `CalibratedSensor` record is not empty.                                                         |
| `REC006` | `instance-not-empty`          | `ERROR`  | `N/A`   | `Instance` record is not empty if either `SampleAnnotation` or `ObjectAnnotation` is not empty. |
| `REC007` | `category-indices-consistent` | `ERROR`  | `YES`   | `Category` records must either all have a unique `index` or all have a `null` index.            |

## Reference (`REF`)

### Record Reference (A to B)

| ID       | Name                                  | Severity | Fixable | Description                                                               |
| -------- | ------------------------------------- | -------- | ------- | ------------------------------------------------------------------------- |
| `REF001` | `scene-to-log`                        | `ERROR`  | `N/A`   | `Scene.log_token` refers to `Log` record.                                 |
| `REF002` | `scene-to-first-sample`               | `ERROR`  | `N/A`   | `Scene.first_sample_token` refers to `Sample` record.                     |
| `REF003` | `scene-to-last-sample`                | `ERROR`  | `N/A`   | `Scene.last_sample_token` refers to `Sample` record.                      |
| `REF004` | `sample-to-scene`                     | `ERROR`  | `N/A`   | `Sample.scene_token` refers to `Scene` record.                            |
| `REF005` | `sample-data-to-sample`               | `ERROR`  | `N/A`   | `SampleData.sample_token` refers to `Sample` record.                      |
| `REF006` | `sample-data-to-ego-pose`             | `ERROR`  | `N/A`   | `SampleData.ego_pose_token` refers to `EgoPose` record.                   |
| `REF007` | `sample-data-to-calibrated-sensor`    | `ERROR`  | `N/A`   | `SampleData.calibrated_sensor_token` refers to `CalibratedSensor` record. |
| `REF008` | `calibrated-sensor-to-sensor`         | `ERROR`  | `N/A`   | `CalibratedSensor.sensor_token` refers to `Sensor` record.                |
| `REF009` | `instance-to-category`                | `ERROR`  | `N/A`   | `Instance.category_token` refers to `Category` record.                    |
| `REF010` | `instance-to-first-sample-annotation` | `ERROR`  | `N/A`   | `Instance.first_annotation_token` refers to `SampleAnnotation` record.    |
| `REF011` | `instance-to-last-sample-annotation`  | `ERROR`  | `N/A`   | `Instance.last_annotation_token` refers to `SampleAnnotation` record.     |
| `REF012` | `lidarseg-to-sample-data`             | `ERROR`  | `N/A`   | `LidarSeg.sample_data_token` refers to `SampleData` record.               |

### Record Reference (A to A')

| ID       | Name                                | Severity | Fixable | Description                                                       |
| -------- | ----------------------------------- | -------- | ------- | ----------------------------------------------------------------- |
| `REF101` | `sample-next-to-another`            | `ERROR`  | `N/A`   | `Sample.next` refers to another one unless it is empty.           |
| `REF102` | `sample-prev-to-another`            | `ERROR`  | `N/A`   | `Sample.prev` refers to another one unless it is empty.           |
| `REF103` | `sample-annotation-next-to-another` | `ERROR`  | `N/A`   | `SampleAnnotation.next` refers to another one unless it is empty. |
| `REF104` | `sample-annotation-prev-to-another` | `ERROR`  | `N/A`   | `SampleAnnotation.prev` refers to another one unless it is empty. |
| `REF105` | `sample-data-next-to-another`       | `ERROR`  | `N/A`   | `SampleData.next` refers to another one unless it is empty.       |
| `REF106` | `sample-data-prev-to-another`       | `ERROR`  | `N/A`   | `SampleData.prev` refers to another one unless it is empty.       |

### File Reference

| ID       | Name                                 | Severity | Fixable | Description                                            |
| -------- | ------------------------------------ | -------- | ------- | ------------------------------------------------------ |
| `REF201` | `sample-data-filename-presence`      | `ERROR`  | `N/A`   | `SampleData.filename` exists.                          |
| `REF202` | `sample-data-info-filename-presence` | `ERROR`  | `N/A`   | `SampleData.info_filename` exists if it is not `None`. |
| `REF203` | `lidarseg-filename-presence`         | `ERROR`  | `N/A`   | `LidarSeg.filename` exists if `lidarseg.json` exists.  |

### External Table Reference

| ID       | Name                              | Severity | Fixable | Description                                |
| -------- | --------------------------------- | -------- | ------- | ------------------------------------------ |
| `REF301` | `pointcloud-metainfo-token-check` | `ERROR`  | `N/A`   | `PointCloudMetainfo sensor tokens` exists. |

## Format (`FMT`)

| ID       | Name                      | Severity | Fixable | Description                                       |
| -------- | ------------------------- | -------- | ------- | ------------------------------------------------- |
| `FMT001` | `attribute-field`         | `ERROR`  | `N/A`   | All types of `Attribute` fields are valid.        |
| `FMT002` | `calibrated-sensor-field` | `ERROR`  | `N/A`   | All types of `CalibratedSensor` fields are valid. |
| `FMT003` | `category-field`          | `ERROR`  | `N/A`   | All types of `Category` fields are valid.         |
| `FMT004` | `ego-pose-field`          | `ERROR`  | `N/A`   | All types of `EgoPose` fields are valid.          |
| `FMT005` | `instance-field`          | `ERROR`  | `N/A`   | All types of `Instance` fields are valid.         |
| `FMT006` | `log-field`               | `ERROR`  | `N/A`   | All types of `Log` fields are valid.              |
| `FMT007` | `map-field`               | `ERROR`  | `N/A`   | All types of `Map` fields are valid.              |
| `FMT008` | `sample-field`            | `ERROR`  | `N/A`   | All types of `Sample` fields are valid.           |
| `FMT009` | `sample-annotation-field` | `ERROR`  | `N/A`   | All types of `SampleAnnotation` fields are valid. |
| `FMT010` | `sample-data-field`       | `ERROR`  | `N/A`   | All types of `SampleData` fields are valid.       |
| `FMT011` | `scene-field`             | `ERROR`  | `N/A`   | All types of `Scene` fields are valid.            |
| `FMT012` | `sensor-field`            | `ERROR`  | `N/A`   | All types of `Sensor` fields are valid.           |
| `FMT013` | `visibility-field`        | `ERROR`  | `N/A`   | All types of `Visibility` fields are valid.       |
| `FMT014` | `lidarseg-field`          | `ERROR`  | `N/A`   | All types of `Lidarseg` fields are valid.         |
| `FMT015` | `object-ann-field`        | `ERROR`  | `N/A`   | All types of `ObjectAnn` fields are valid.        |
| `FMT016` | `surface-ann-field`       | `ERROR`  | `N/A`   | All types of `SurfaceAnn` fields are valid.       |
| `FMT017` | `keypoint-field`          | `ERROR`  | `N/A`   | All types of `Keypoint` fields are valid.         |
| `FMT018` | `vehicle-state-field`     | `ERROR`  | `N/A`   | All types of `VehicleState` fields are valid.     |

## Tier4 Instance (`TIV`)

| ID       | Name         | Severity | Fixable | Description                                     |
| -------- | ------------ | -------- | ------- | ----------------------------------------------- |
| `TIV001` | `load-tier4` | `ERROR`  | `N/A`   | Ensure `Tier4` instance is loaded successfully. |
