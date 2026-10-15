# Dataset Requirements 1.0

The rules `t4sanity` checks on T4Dataset 1.0 datasets. The 0.x rules are in [Dataset Requirements](../requirement.md).

## How Rules Apply

- `t4sanity` reads the dataset version first (`manifest.json` present → 1.0) and runs only the rules for that version. The `Applies to` column says which.
- A rule ID keeps its meaning. Rules that mean the same for both versions keep their 0.x ID. Rules that change meaning get a new ID, numbered after the last 0.x ID of the group, so `--exclude` keeps working.
- The 0.x rules are not changed: 0.x datasets get exactly the same report as before 1.0.
- Rules within one record (field types, value ranges, `null` instead of `""`, the `sensor` block matching `modality`, the distortion model matching the number of coefficients, ...) are enforced when building the record, and reported by the format rules (`FMT`). The other groups check what involves several records or files.
- A 1.0 rule is skipped when the tables or files it needs could not be read, instead of failing; the format or structure rule that failed says why.
- Fixable 1.0 rules write tables, so they also update the hashes in `manifest.json`.

## Structure (`STR`)

| ID       | Name                             | Severity  | Fixable | Applies to | Description                                                                                                                                                                                                                |
| -------- | -------------------------------- | --------- | ------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `STR001` | `version-dir-presence`           | `WARNING` | `N/A`   | 0.x, 1.0   | `version/` directory exists under the dataset root directory.                                                                                                                                                              |
| `STR002` | `annotation-dir-presence`        | `ERROR`   | `N/A`   | 0.x, 1.0   | `annotation/` directory exists under the dataset root directory.                                                                                                                                                           |
| `STR003` | `data-dir-presence`              | `ERROR`   | `N/A`   | 0.x, 1.0   | `data/` directory exists under the dataset root directory.                                                                                                                                                                 |
| `STR004` | `map-dir-presence`               | `WARNING` | `N/A`   | 0.x, 1.0   | `map/` directory exists under the dataset root directory.                                                                                                                                                                  |
| `STR005` | `bag-dir-presence`               | `WARNING` | `N/A`   | 0.x, 1.0   | `input_bag/` directory exists under the dataset root directory.                                                                                                                                                            |
| `STR008` | `lanelet-file-presence`          | `WARNING` | `N/A`   | 0.x, 1.0   | `lanelet2_map.osm` file exists under the `map/` directory.                                                                                                                                                                 |
| `STR009` | `pointcloud-map-dir-presence`    | `WARNING` | `N/A`   | 0.x, 1.0   | `pointcloud_map.pcd` directory exists under the `map/` directory.                                                                                                                                                          |
| `STR010` | `schema-version-supported`       | `ERROR`   | `N/A`   | 1.0        | `manifest.json` declares a supported `schema_version` (major version 1). If not, no other 1.0 rule runs.                                                                                                                   |
| `STR011` | `manifest-files-presence`        | `ERROR`   | `N/A`   | 1.0        | Every file listed in `manifest.json` (`tables` and `assets`) exists.                                                                                                                                                       |
| `STR012` | `manifest-files-checksum`        | `ERROR`   | `N/A`   | 1.0        | Every listed file has the listed `sha256`, and every asset the listed `bytes`. Opt-in (`--checksum`), since it reads every file (videos, rosbags); without it, the rule reports a `WARNING` that hashes were not verified. |
| `STR013` | `manifest-files-complete`        | `WARNING` | `N/A`   | 1.0        | Every file under `annotation/`, `data/`, `map/` and `input_bag/` is listed in `manifest.json`.                                                                                                                             |
| `STR014` | `manifest-required-tables`       | `ERROR`   | `N/A`   | 1.0        | `manifest.json` lists every required table: `sample`, `sample_data`, `ego_pose`, `sensor`, `scene`, `log`, `vehicle`.                                                                                                      |
| `STR015` | `manifest-identity-matches-dirs` | `WARNING` | `N/A`   | 1.0        | `manifest.json` `dataset_id` and `version` match the names of the dataset and version directories.                                                                                                                         |

## Format (`FMT`)

Each table file is a list of records that build into the 1.0 table class, with all its field and within-record rules.

| ID       | Name                      | Severity | Fixable | Applies to | Description                                                                                |
| -------- | ------------------------- | -------- | ------- | ---------- | ------------------------------------------------------------------------------------------ |
| `FMT020` | `manifest-field`          | `ERROR`  | `N/A`   | 1.0        | All `manifest.json` fields are valid.                                                      |
| `FMT021` | `sample-field`            | `ERROR`  | `N/A`   | 1.0        | All `Sample` records are valid.                                                            |
| `FMT022` | `sample-data-field`       | `ERROR`  | `N/A`   | 1.0        | All `SampleData` records are valid.                                                        |
| `FMT023` | `ego-pose-field`          | `ERROR`  | `N/A`   | 1.0        | All `EgoPose` records are valid.                                                           |
| `FMT024` | `sensor-field`            | `ERROR`  | `N/A`   | 1.0        | All `Sensor` records are valid, including exactly one modality block, matching `modality`. |
| `FMT025` | `scene-field`             | `ERROR`  | `N/A`   | 1.0        | All `Scene` records are valid.                                                             |
| `FMT026` | `log-field`               | `ERROR`  | `N/A`   | 1.0        | All `Log` records are valid.                                                               |
| `FMT027` | `vehicle-field`           | `ERROR`  | `N/A`   | 1.0        | All `Vehicle` records are valid.                                                           |
| `FMT028` | `map-field`               | `ERROR`  | `N/A`   | 1.0        | All `Map` records are valid.                                                               |
| `FMT029` | `vehicle-state-field`     | `ERROR`  | `N/A`   | 1.0        | All `VehicleState` records are valid.                                                      |
| `FMT030` | `category-field`          | `ERROR`  | `N/A`   | 1.0        | All `Category` records are valid.                                                          |
| `FMT031` | `attribute-field`         | `ERROR`  | `N/A`   | 1.0        | All `Attribute` records are valid.                                                         |
| `FMT032` | `visibility-field`        | `ERROR`  | `N/A`   | 1.0        | All `Visibility` records are valid.                                                        |
| `FMT033` | `instance-field`          | `ERROR`  | `N/A`   | 1.0        | All `Instance` records are valid.                                                          |
| `FMT034` | `sample-annotation-field` | `ERROR`  | `N/A`   | 1.0        | All `SampleAnnotation` records are valid.                                                  |
| `FMT035` | `object-ann-field`        | `ERROR`  | `N/A`   | 1.0        | All `ObjectAnn` records are valid.                                                         |
| `FMT036` | `keypoint-field`          | `ERROR`  | `N/A`   | 1.0        | All `Keypoint` records are valid.                                                          |
| `FMT037` | `traffic-light-field`     | `ERROR`  | `N/A`   | 1.0        | All `TrafficLight` records are valid.                                                      |
| `FMT038` | `route-field`             | `ERROR`  | `N/A`   | 1.0        | All `Route` records are valid.                                                             |
| `FMT039` | `scenario-field`          | `ERROR`  | `N/A`   | 1.0        | All `Scenario` records are valid.                                                          |
| `FMT040` | `caption-field`           | `ERROR`  | `N/A`   | 1.0        | All `Caption` records are valid.                                                           |

## Schema Record (`REC`)

| ID       | Name                           | Severity  | Fixable | Applies to | Description                                                                                                                                                                                                                                           |
| -------- | ------------------------------ | --------- | ------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `REC001` | `scene-single`                 | `ERROR`   | `N/A`   | 0.x, 1.0   | `Scene` record is a single.                                                                                                                                                                                                                           |
| `REC002` | `sample-not-empty`             | `ERROR`   | `N/A`   | 0.x, 1.0   | `Sample` record is not empty.                                                                                                                                                                                                                         |
| `REC003` | `sample-data-not-empty`        | `ERROR`   | `N/A`   | 0.x, 1.0   | `SampleData` record is not empty.                                                                                                                                                                                                                     |
| `REC004` | `ego-pose-not-empty`           | `ERROR`   | `N/A`   | 0.x, 1.0   | `EgoPose` record is not empty.                                                                                                                                                                                                                        |
| `REC006` | `instance-not-empty`           | `ERROR`   | `N/A`   | 0.x, 1.0   | `Instance` record is not empty if either `SampleAnnotation` or `ObjectAnnotation` is not empty.                                                                                                                                                       |
| `REC007` | `category-indices-consistent`  | `ERROR`   | `YES`   | 0.x, 1.0   | `Category` records must either all have a unique `index` or all have a `null` index.                                                                                                                                                                  |
| `REC008` | `sensor-not-empty`             | `ERROR`   | `N/A`   | 1.0        | `Sensor` record is not empty.                                                                                                                                                                                                                         |
| `REC009` | `sensor-index-unique`          | `ERROR`   | `N/A`   | 1.0        | `Sensor.index` values are unique.                                                                                                                                                                                                                     |
| `REC010` | `instance-index-unique`        | `ERROR`   | `N/A`   | 1.0        | `Instance.index` values are unique where set.                                                                                                                                                                                                         |
| `REC011` | `point-label-indices-presence` | `ERROR`   | `N/A`   | 1.0        | When a LiDAR file has `label` / `instance` columns, every `Category` has an `index`, and every `Instance` of an `is_thing` category an `index`.                                                                                                       |
| `REC012` | `scene-sample-count`           | `ERROR`   | `YES`   | 1.0        | `Scene.nbr_samples` equals the number of `Sample` records (frames) of the scene.                                                                                                                                                                      |
| `REC013` | `instance-annotation-count`    | `ERROR`   | `YES`   | 1.0        | `Instance.nbr_annotations` equals the number of its `SampleAnnotation` and `ObjectAnn` records, and its first / last annotation tokens point to its first / last one in time.                                                                         |
| `REC014` | `thing-category-instance`      | `ERROR`   | `N/A`   | 1.0        | `ObjectAnn.instance_token` is set exactly when its category has `is_thing`; `SampleAnnotation` and `Keypoint` instances belong to `is_thing` categories.                                                                                              |
| `REC015` | `orientation-number-allowed`   | `ERROR`   | `N/A`   | 1.0        | `ObjectAnn.orientation` / `number` are set only for categories with `has_orientation` / `has_number`.                                                                                                                                                 |
| `REC016` | `manual-label-confidence`      | `ERROR`   | `N/A`   | 1.0        | Labels with `annotation_type: manual` have `confidence: null`.                                                                                                                                                                                        |
| `REC017` | `automatic-label-provenance`   | `WARNING` | `N/A`   | 1.0        | Labels that are not `manual` have a `provenance`, and `auto` / `pseudo` labels a `confidence`.                                                                                                                                                        |
| `REC018` | `sample-frames`                | `ERROR`   | `N/A`   | 1.0        | A `Sample` has at most one `SampleData` per channel; its `timestamp` is its LiDAR frame's (its earliest frame's if it has no LiDAR); `has_key_frame` is true exactly when one of its `SampleData` is a key frame.                                     |
| `REC019` | `channel-frames`               | `ERROR`   | `N/A`   | 1.0        | For a channel stored in one file, `frame_count` (`camera.video` / `lidar.container`) equals the number of its `SampleData` records, and their `frame_index` values are `0` to `frame_count - 1`, each once.                                           |
| `REC020` | `sensor-storage-consistent`    | `ERROR`   | `N/A`   | 1.0        | `SampleData.frame_index` is `null` exactly when its sensor stores one file per frame (`camera.video: null`, `lidar.container.path: null`), and `fileformat` matches the sensor's storage.                                                             |
| `REC021` | `timestamps-ordered`           | `ERROR`   | `N/A`   | 1.0        | Timestamps increase along `next` (`Sample`, `SampleData`, `SampleAnnotation`), and `frame_index` follows timestamp order within a channel file.                                                                                                       |
| `REC022` | `timestamps-microseconds`      | `WARNING` | `N/A`   | 1.0        | Timestamps are Unix microseconds: between 2000-01-01 and 2100-01-01 (catches seconds or nanoseconds).                                                                                                                                                 |
| `REC023` | `capabilities-present`         | `ERROR`   | `N/A`   | 1.0        | Everything `manifest.json` `capabilities` declares is present: its camera / LiDAR channels have frames, `map` has a `Map` record, `route` / `traffic_light` / `vehicle_state` / `scenario` have records, and its tasks have their labels (see below). |
| `REC024` | `capabilities-complete`        | `WARNING` | `N/A`   | 1.0        | Everything present is declared in `capabilities`: the same checks as `REC023`, the other way round.                                                                                                                                                   |
| `REC025` | `no-placeholder-values`        | `WARNING` | `N/A`   | 1.0        | No placeholder values from loading or migrating 0.x: `Vehicle.model` and `Map.map_id` / `version_id` are not `"unknown"`.                                                                                                                             |
| `REC026` | `route-validity`               | `ERROR`   | `N/A`   | 1.0        | `Route.valid_until` is after `valid_from` when set, and the routes of a log do not overlap in time.                                                                                                                                                   |
| `REC027` | `unit-quaternions`             | `WARNING` | `N/A`   | 1.0        | Rotations (`Sensor`, `EgoPose`, `SampleAnnotation`, `Route` poses) are unit quaternions.                                                                                                                                                              |
| `REC028` | `labels-on-key-frames`         | `ERROR`   | `N/A`   | 1.0        | Labels sit on key frames: a `SampleAnnotation` on a `Sample` with `has_key_frame`, an `ObjectAnn` or `Keypoint` on a `SampleData` with `is_key_frame`.                                                                                                |
| `REC029` | `point-labels-reserved-zero`   | `ERROR`   | `N/A`   | 1.0        | When a LiDAR file has `label` / `instance` columns: the `Category` with `index` `0` is named `unpainted`, no `Instance.index` is `0`, and each frame's label columns are `null` on all points or on none.                                             |

Tasks and the labels `REC023` / `REC024` expect:

| Task             | Expected labels                                                |
| ---------------- | -------------------------------------------------------------- |
| `detection3d`    | `SampleAnnotation` records                                     |
| `detection2d`    | `ObjectAnn` records of `is_thing` categories                   |
| `segmentation2d` | `ObjectAnn` records with a `mask`                              |
| `segmentation3d` | `label` / `instance` columns in a LiDAR file                   |
| `keypoint`       | `Keypoint` records                                             |
| `traffic_light`  | `TrafficLight` records, or instances with a lamp `map_element` |
| `prediction`     | Not checked                                                    |
| `planning`       | Not checked                                                    |

## Reference (`REF`)

`null` means "no link" in 1.0, where 0.x uses `""`: a reference rule does not apply to an empty link (the shared rules keep their 0.x wording).

### Record Reference (A to B)

| ID       | Name                                  | Severity | Fixable | Applies to | Description                                                                                                                     |
| -------- | ------------------------------------- | -------- | ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `REF001` | `scene-to-log`                        | `ERROR`  | `N/A`   | 0.x, 1.0   | `Scene.log_token` refers to `Log` record.                                                                                       |
| `REF002` | `scene-to-first-sample`               | `ERROR`  | `N/A`   | 0.x, 1.0   | `Scene.first_sample_token` refers to `Sample` record.                                                                           |
| `REF003` | `scene-to-last-sample`                | `ERROR`  | `N/A`   | 0.x, 1.0   | `Scene.last_sample_token` refers to `Sample` record.                                                                            |
| `REF004` | `sample-to-scene`                     | `ERROR`  | `N/A`   | 0.x, 1.0   | `Sample.scene_token` refers to `Scene` record.                                                                                  |
| `REF005` | `sample-data-to-sample`               | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleData.sample_token` refers to `Sample` record.                                                                            |
| `REF006` | `sample-data-to-ego-pose`             | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleData.ego_pose_token` refers to `EgoPose` record.                                                                         |
| `REF009` | `instance-to-category`                | `ERROR`  | `N/A`   | 0.x, 1.0   | `Instance.category_token` refers to `Category` record.                                                                          |
| `REF010` | `instance-to-first-sample-annotation` | `ERROR`  | `N/A`   | 0.x, 1.0   | `Instance.first_annotation_token` refers to `SampleAnnotation` or `ObjectAnn` record.                                           |
| `REF011` | `instance-to-last-sample-annotation`  | `ERROR`  | `N/A`   | 0.x, 1.0   | `Instance.last_annotation_token` refers to `SampleAnnotation` or `ObjectAnn` record.                                            |
| `REF015` | `sample-data-to-sensor`               | `ERROR`  | `N/A`   | 1.0        | `SampleData.sensor_token` refers to `Sensor` record.                                                                            |
| `REF016` | `log-to-vehicle`                      | `ERROR`  | `N/A`   | 1.0        | `Log.vehicle_token` refers to `Vehicle` record.                                                                                 |
| `REF017` | `log-and-map`                         | `ERROR`  | `N/A`   | 1.0        | `Log.map_token` refers to `Map` record unless it is empty, `Map.log_tokens` refer to `Log` records, and both agree.             |
| `REF018` | `sample-annotation-references`        | `ERROR`  | `N/A`   | 1.0        | `SampleAnnotation` `sample_token`, `instance_token`, `attribute_tokens` and `visibility_token` (unless empty) refer to records. |
| `REF019` | `object-ann-references`               | `ERROR`  | `N/A`   | 1.0        | `ObjectAnn` `sample_data_token`, `instance_token` (unless empty), `category_token` and `attribute_tokens` refer to records.     |
| `REF020` | `keypoint-references`                 | `ERROR`  | `N/A`   | 1.0        | `Keypoint` `sample_data_token`, `instance_token` and `category_tokens` refer to records.                                        |
| `REF021` | `traffic-light-references`            | `ERROR`  | `N/A`   | 1.0        | `TrafficLight` `object_ann_token` and `instance_token` refer to records unless they are empty.                                  |
| `REF022` | `route-references`                    | `ERROR`  | `N/A`   | 1.0        | `Route` `log_token` and `map_token` refer to records.                                                                           |
| `REF023` | `scenario-references`                 | `ERROR`  | `N/A`   | 1.0        | `Scenario.log_token` refers to `Log` record.                                                                                    |
| `REF024` | `caption-references`                  | `ERROR`  | `N/A`   | 1.0        | `Caption` `log_token`, `sample_data_token`, `scenario_token` and `instance_tokens` refer to records unless they are empty.      |
| `REF025` | `lidar-source-channels`               | `ERROR`  | `N/A`   | 1.0        | `Lidar.source_channels` name LiDAR `Sensor` records that have no `SampleData`.                                                  |

### Record Reference (A to A')

| ID       | Name                                | Severity | Fixable | Applies to | Description                                                                                      |
| -------- | ----------------------------------- | -------- | ------- | ---------- | ------------------------------------------------------------------------------------------------ |
| `REF101` | `sample-next-to-another`            | `ERROR`  | `N/A`   | 0.x, 1.0   | `Sample.next` refers to another one unless it is empty.                                          |
| `REF102` | `sample-prev-to-another`            | `ERROR`  | `N/A`   | 0.x, 1.0   | `Sample.prev` refers to another one unless it is empty.                                          |
| `REF103` | `sample-annotation-next-to-another` | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleAnnotation.next` refers to another one unless it is empty.                                |
| `REF104` | `sample-annotation-prev-to-another` | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleAnnotation.prev` refers to another one unless it is empty.                                |
| `REF105` | `sample-data-next-to-another`       | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleData.next` refers to another one unless it is empty.                                      |
| `REF106` | `sample-data-prev-to-another`       | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleData.prev` refers to another one unless it is empty.                                      |
| `REF107` | `links-mutual`                      | `ERROR`  | `N/A`   | 1.0        | `next` and `prev` agree: `A.next` has `prev` = `A` (`Sample`, `SampleData`, `SampleAnnotation`). |
| `REF108` | `links-same-stream`                 | `ERROR`  | `N/A`   | 1.0        | `SampleData.next` is of the same channel, and `SampleAnnotation.next` of the same instance.      |

### File Reference

| ID       | Name                            | Severity | Fixable | Applies to | Description                                                                                                                                                                                                                                        |
| -------- | ------------------------------- | -------- | ------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `REF201` | `sample-data-filename-presence` | `ERROR`  | `N/A`   | 0.x, 1.0   | `SampleData.filename` exists.                                                                                                                                                                                                                      |
| `REF204` | `sample-data-file-of-sensor`    | `ERROR`  | `N/A`   | 1.0        | For a channel stored in one file, `SampleData.filename` is its sensor's `camera.video.path` / `lidar.container.path`.                                                                                                                              |
| `REF205` | `sensor-file-description`       | `ERROR`  | `N/A`   | 1.0        | Each channel file matches its `sensor` row. Parquet: columns and dtypes are `lidar.fields`, one row group per frame. Video: codec, pixel format, bit depth, timescale and frame count are `camera.video`. Frame size is `camera.width` / `height`. |
| `REF206` | `lidar-num-points`              | `ERROR`  | `N/A`   | 1.0        | `SampleData.num_points` equals the number of points in its frame, when set.                                                                                                                                                                        |
| `REF207` | `map-file`                      | `ERROR`  | `N/A`   | 1.0        | `Map.filename` exists and has the SHA-256 `Map.sha256`.                                                                                                                                                                                            |

### External Reference

| ID       | Name                       | Severity | Fixable | Applies to | Description                                                                                                                              |
| -------- | -------------------------- | -------- | ------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `REF302` | `instance-to-map-element`  | `ERROR`  | `N/A`   | 1.0        | `Instance.map_element` refers to an element of its `type` in the lanelet2 map; for traffic-light lamps, a way with `type=traffic_light`. |
| `REF303` | `traffic-light-to-lanelet` | `ERROR`  | `N/A`   | 1.0        | `TrafficLight.regulatory_element_id` is a traffic-light regulatory element of the lanelet2 map.                                          |
| `REF304` | `route-to-lanelet`         | `ERROR`  | `N/A`   | 1.0        | `Route` segment ids are lanelets of the lanelet2 map.                                                                                    |
| `REF305` | `lidar-source-index`       | `ERROR`  | `N/A`   | 1.0        | In a merged LiDAR file, `source_index` values are the `Sensor.index` of the channel's `source_channels`.                                 |
| `REF306` | `lidar-point-labels`       | `ERROR`  | `N/A`   | 1.0        | In a LiDAR file, `label` values are `Category.index` values, and `instance` values are `Instance.index` values or `0` (no object).       |

## TIER IV Instance (`TIV`)

| ID       | Name         | Severity | Fixable | Applies to | Description                                        |
| -------- | ------------ | -------- | ------- | ---------- | -------------------------------------------------- |
| `TIV001` | `load-tier4` | `ERROR`  | `N/A`   | 0.x, 1.0   | Ensure `T4Devkit` instance is loaded successfully. |

## 0.x Rules Not Run on 1.0

| 0.x rule                                      | Why                                                                                               | 1.0 rule                     |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------- |
| `STR006` `status-file-presence`               | `manifest.json` replaces `status.json`.                                                           | `STR010`–`STR013`            |
| `STR007` `schema-files-presence`              | Required tables are listed in `manifest.json`.                                                    | `STR011`, `STR014`           |
| `FMT001`–`FMT019`                             | The 1.0 tables are different classes; `calibrated_sensor`, `surface_ann` and `lidarseg` are gone. | `FMT020`–`FMT040`            |
| `REC005` `calibrated-sensor-non-empty`        | Merged into `sensor`.                                                                             | `REC008`                     |
| `REF007` `sample-data-to-calibrated-sensor`   | `SampleData` refers to `sensor` directly.                                                         | `REF015`                     |
| `REF008` `calibrated-sensor-to-sensor`        | Merged into `sensor`.                                                                             | `REF015`                     |
| `REF012` `lidarseg-to-sample-data`            | Point-wise labels are LiDAR columns.                                                              | `REC011`, `REC029`, `REF306` |
| `REF203` `lidarseg-filename-presence`         | Point-wise labels are LiDAR columns.                                                              | `REF205`, `REF306`           |
| `REF013` `traffic-light-to-instance`          | The 0.x lamp-to-way link is `Instance.map_element`; the 1.0 `traffic_light` table holds states.   | `REF021`, `REF302`           |
| `REF014` `traffic-light-to-lanelet`           | Same as `REF013`.                                                                                 | `REF302`, `REF303`           |
| `REF202` `sample-data-info-filename-presence` | Merged LiDAR sources are LiDAR columns instead of `.info` files.                                  | `REF305`                     |
| `REF301` `pointcloud-metainfo-token-check`    | Same as `REF202`.                                                                                 | `REF025`, `REF305`           |
