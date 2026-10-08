# Schema Tables 1.0

Tables are stored as JSON files in `annotation/`, one file per table, each a list of records. Every table file is listed in `manifest.json` with its SHA-256.

Types follow the notation in [Schema Tables](../table.md#type-definition). In addition:

- Missing references are `null`, never an empty string `""`.
- Timestamps are Unix time in microseconds (`int`).
- Translations are `(x, y, z)` in meters and rotations are quaternions `(w, x, y, z)`.

## Common Types

### `AnnotationType`

How a label was made: `enum["manual", "auto", "pseudo", "corrected", "interpolated", "synthetic"]`.

Every label table (`sample_annotation`, `object_ann`, `surface_ann`, `keypoint`, `traffic_light`, `scenario`, `caption`) has these three fields:

```json
"annotation_type":    <AnnotationType> -- How the label was made.
"provenance":         <option[str]> -- Vendor, model name and version, or tool.
"confidence":         <option[float]> -- Confidence in [0, 1]. `null` for manual labels.
```

They replace `automatic_annotation` and `autolabel_metadata` from 0.x. For 0.x readers, `automatic_annotation = (annotation_type != "manual")`.

### `Pose`

```json
Pose {
  "translation":      <[float;3]> -- (x, y, z) in meters.
  "rotation":         <[float;4]> -- Quaternion (w, x, y, z).
}
```

## Required Tables

### Sample

- Filename: `sample.json`

An annotation keyframe. Unchanged from 0.x, except that missing links are `null`.

```json
sample {
  "token":            <str> -- Unique record identifier.
  "timestamp":        <int> -- Unix timestamp in microseconds.
  "scene_token":      <str> -- Foreign key to the `Scene` table.
  "next":             <option[str]> -- Foreign key to the next `Sample`. `null` for the last sample.
  "prev":             <option[str]> -- Foreign key to the previous `Sample`. `null` for the first sample.
}
```

### SampleData

- Filename: `sample_data.json`

One observation of one sensor channel. Channel-level facts (calibration, image size, file encoding) are on the `Sensor` table.

```json
sample_data {
  "token":            <str> -- Unique record identifier.
  "sample_token":     <option[str]> -- Foreign key to the `Sample` table. `null` if this is not a key frame.
  "ego_pose_token":   <str> -- Foreign key to the `EgoPose` table.
  "sensor_token":     <str> -- Foreign key to the `Sensor` table. Replaces `calibrated_sensor_token`.
  "filename":         <option[str]> -- Path to the channel file (video or point cloud container), or to a per-frame file for datasets that keep 0.x files.
  "frame_index":      <option[int]> -- Index of the frame inside the channel file, starting at 0. `null` for per-frame files.
  "fileformat":       <enum["jpg", "png", "pcd", "bin", "pcd.bin", "av1_mp4", "parquet"]> -- Format of the file.
  "num_points":       <option[int]> -- Number of points in the frame. LiDAR only.
  "timestamp":        <int> -- Unix timestamp in microseconds (ROS header stamp of this observation).
  "is_key_frame":     <bool> -- Whether this is an annotation keyframe.
  "is_valid":         <bool> -- `false` if the frame has a sensor drop or synchronization failure.
  "next":             <option[str]> -- Foreign key to the next `SampleData` of the same channel.
  "prev":             <option[str]> -- Foreign key to the previous `SampleData` of the same channel.
}
```

### EgoPose

- Filename: `ego_pose.json`

The ego vehicle's pose at a given time, in the map frame.

```json
ego_pose {
  "token":            <str> -- Unique record identifier.
  "translation":      <[float;3]> -- Position in meters.
  "rotation":         <[float;4]> -- Orientation as quaternion (w, x, y, z).
  "timestamp":        <int> -- Unix timestamp in microseconds.
  "twist":            <option[[float;6]]> -- (vx, vy, vz, yaw_rate, pitch_rate, roll_rate) in the vehicle frame.
  "acceleration":     <option[[float;3]]> -- (ax, ay, az) in the vehicle frame.
  "geocoordinate":    <option[[float;3]]> -- (latitude, longitude, altitude).
  "source":           <enum["localization", "post_processed", "gnss_ins"]> -- Where the pose came from.
  "frame":            <str> -- Coordinate frame, e.g. "map".
  "covariance":       <option[[float;36]]> -- 6×6 pose covariance, row-major.
}
```

### Sensor

- Filename: `sensor.json`

One row per sensor channel, with its calibration and how its data is stored. Merges `sensor` and `calibrated_sensor` from 0.x. A recalibration is a new row for the same channel.

Exactly one modality block is present, matching `modality`. All fields inside a block are required when the block is present.

```json
sensor {
  "token":            <str> -- Unique record identifier.
  "channel":          <str> -- Channel name, e.g. "CAM_FRONT", "LIDAR_CONCAT".
  "modality":         <enum["camera", "lidar", "radar"]> -- Sensor modality.
  "translation":      <[float;3]> -- Sensor position relative to base_link, in meters.
  "rotation":         <[float;4]> -- Sensor orientation relative to base_link, as quaternion (w, x, y, z).
  "camera":           <option[Camera]> -- Present when `modality` is "camera".
  "lidar":            <option[Lidar]> -- Present when `modality` is "lidar".
  "radar":            <option[object]> -- Not defined in 1.0.
  "hardware":         <option[Hardware]> -- Sensor hardware identity.
}
```

```json
Camera {
  "width":            <int> -- Image width in pixels.
  "height":           <int> -- Image height in pixels.
  "intrinsic":        <[[float;3];3]> -- Camera matrix.
  "distortion":       <[float;N]> -- Distortion coefficients, following `distortion_model`.
  "distortion_model": <enum["plumb_bob", "rational_polynomial", "equidistant", "none"]> -- From CameraInfo.
  "is_rectified":     <bool> -- Whether the stored images are already rectified.
  "video":            <option[Video]> -- How the video is encoded. `null` for per-frame image files.
}

Video {
  "path":             <str> -- Path to the video file, e.g. "data/CAM_FRONT/CAM_FRONT.mp4".
  "format":           <enum["av1_mp4"]> -- Container and codec.
  "codec_profile":    <str> -- Encoder settings, e.g. "svt-av1 preset6 crf26 intra".
  "pixel_format":     <str> -- e.g. "yuv420p full-range bt601".
  "bit_depth":        <int> -- Bits per channel, 8 or 10.
  "frame_count":      <int> -- Number of frames in the file.
  "timescale":        <int> -- MP4 track timescale (ticks per second). Equal to the frame rate, so pts == frame_index.
}
```

```json
Lidar {
  "container": {
    "format":         <enum["parquet", "pcd", "bin"]> -- File format.
    "path":           <option[str]> -- Path to the file, e.g. "data/LIDAR_CONCAT/LIDAR_CONCAT.parquet". `null` for per-frame files.
    "frame_count":    <int> -- Number of frames.
    "compression":    <str> -- Compression profile, e.g. "zstd", or "none".
  }
  "fields":           <[{"name": str, "dtype": str};N]> -- Point fields in column order, e.g. {"name": "x", "dtype": "float32"}.
  "source_channels":  <[str;N]> -- LiDAR channels merged into this one. Empty if not a concatenation.
  "frame_id":         <str> -- Coordinate frame of the stored points, "base_link" by default.
  "is_undistorted":   <bool> -- Whether points are motion and scan compensated.
}
```

```json
Hardware {
  "make":             <option[str]> -- Manufacturer, e.g. "Hesai".
  "model":            <option[str]> -- Model, e.g. "OT128".
  "serial_number":    <option[str]> -- Serial number.
  "firmware_version": <option[str]> -- Firmware version.
}
```

### Scene

- Filename: `scene.json`

Unchanged from 0.x.

```json
scene {
  "token":              <str> -- Unique record identifier.
  "name":               <str> -- Name of the scene.
  "description":        <option[str]> -- Description of the scene.
  "log_token":          <str> -- Foreign key to the `Log` table.
  "nbr_samples":        <int> -- Number of samples in the scene.
  "first_sample_token": <str> -- Foreign key to the first `Sample`.
  "last_sample_token":  <str> -- Foreign key to the last `Sample`.
}
```

### Log

- Filename: `log.json`

```json
log {
  "token":            <str> -- Unique record identifier.
  "logfile":          <option[str]> -- Path to the log file.
  "vehicle_token":    <str> -- Foreign key to the `Vehicle` table.
  "data_captured":    <str> -- Capture time, ISO 8601.
  "location":         <option[str]> -- Location of the recording.
  "map_token":        <option[str]> -- Foreign key to the `Map` table. `null` if there is no map.
}
```

### Vehicle

- Filename: `vehicle.json`

Vehicle identity and dimensions.

```json
vehicle {
  "token":                <str> -- Unique record identifier.
  "model":                <str> -- Vehicle model.
  "length":               <float> -- Length in meters.
  "width":                <float> -- Width in meters.
  "height":               <float> -- Height in meters.
  "wheel_base":           <float> -- Wheel base in meters.
  "rear_axle_to_center":  <option[float]> -- Distance from the rear axle to the vehicle center, in meters.
  "sensor_rig_id":        <option[str]> -- Sensor rig ID.
  "name":                 <option[str]> -- Vehicle name, e.g. "j6_gen2_04".
}
```

## Optional Tables

The following tables are optional. Which ones a dataset contains is declared in `manifest.json` (`capabilities`).

### Map

- Filename: `map.json`

Map identity. Lane data stays in the lanelet2 file.

```json
map {
  "token":              <str> -- Unique record identifier.
  "log_tokens":         <[str;N]> -- Foreign keys to the `Log` table.
  "format":             <enum["lanelet2_osm"]> -- Map format.
  "filename":           <str> -- Path to the map file.
  "sha256":             <str> -- SHA-256 of the map file.
  "map_id":             <str> -- Web.Auto area_map_id.
  "version_id":         <str> -- Web.Auto area_map_version_id.
  "projector": {
    "type":             <option[enum["MGRS", "TransverseMercator", "LocalCartesianUTM"]]> -- Map projection.
    "mgrs_grid":        <option[str]> -- MGRS grid.
    "origin": {
      "lat":            <option[float]> -- Latitude in degrees.
      "lon":            <option[float]> -- Longitude in degrees.
      "alt":            <option[float]> -- Altitude in meters.
    }
  }
  "source":             <enum["webauto", "manual"]> -- Where the map came from.
  "name":               <option[str]> -- Map name.
}
```

### VehicleState

- Filename: `vehicle_state.json`

Measured vehicle signals at their native rate (not resampled).

```json
vehicle_state {
  "token":                  <str> -- Unique record identifier.
  "timestamp":              <int> -- Unix timestamp in microseconds.
  "accel_pedal":            <option[float]> -- Accelerator pedal position.
  "brake_pedal":            <option[float]> -- Brake pedal position.
  "steer_pedal":            <option[float]> -- Steering position.
  "steering_tire_angle":    <option[float]> -- Steering tire angle in radians.
  "steering_wheel_angle":   <option[float]> -- Steering wheel angle in radians.
  "shift_state":            <option[enum["PARK", "REVERSE", "NEUTRAL", "DRIVE", "LOW", "NONE", "unknown"]]> -- Gear.
  "indicators":             <option[Indicators]> -- Turn indicator and hazard state.
  "longitudinal_velocity":  <option[float]> -- Velocity in m/s.
  "lateral_velocity":       <option[float]> -- Velocity in m/s.
  "heading_rate":           <option[float]> -- Heading rate in rad/s.
  "source":                 <enum["can", "vehicle_interface", "imu"]> -- Where the signals came from.
}
```

`Indicators` is defined in [Schema Tables](../table.md#indicators).

### Category

- Filename: `category.json`

```json
category {
  "token":            <str> -- Unique record identifier.
  "name":             <str> -- Category name.
  "description":      <option[str]> -- Description.
  "index":            <option[int]> -- Label value for point-wise labels. Required when point-wise labels are present.
  "has_orientation":  <bool> -- Whether annotations of this category may have `orientation`.
  "has_number":       <bool> -- Whether annotations of this category may have `number`.
}
```

### Attribute

- Filename: `attribute.json`

Unchanged from 0.x.

```json
attribute {
  "token":            <str> -- Unique record identifier.
  "name":             <str> -- Attribute name.
  "description":      <option[str]> -- Description.
}
```

### Visibility

- Filename: `visibility.json`

Unchanged from 0.x.

```json
visibility {
  "token":            <str> -- Unique record identifier.
  "level":            <enum["full", "most", "partial", "none"]> -- Visibility level.
  "description":      <option[str]> -- Description.
}
```

### Instance

- Filename: `instance.json`

An object identity. How each label was made is recorded on the label rows, not here.

```json
instance {
  "token":                  <str> -- Unique record identifier.
  "category_token":         <str> -- Foreign key to the `Category` table.
  "instance_name":          <str> -- `<DATASET_ID>::<INSTANCE_ID>`.
  "nbr_annotations":        <int> -- Number of annotations of this instance.
  "first_annotation_token": <option[str]> -- Foreign key to the first `SampleAnnotation` or `ObjectAnn`.
  "last_annotation_token":  <option[str]> -- Foreign key to the last `SampleAnnotation` or `ObjectAnn`.
  "map_element": {
    "id":                   <option[int]> -- lanelet2 element ID: traffic-light lamp, sign, crosswalk, stop line, lane.
    "type":                 <option[enum["node", "way", "relation"]]> -- lanelet2 element type. IDs are only unique within a type.
  }
}
```

### SampleAnnotation

- Filename: `sample_annotation.json`

A 3D box in the map frame.

```json
sample_annotation {
  "token":            <str> -- Unique record identifier.
  "sample_token":     <str> -- Foreign key to the `Sample` table.
  "instance_token":   <str> -- Foreign key to the `Instance` table.
  "attribute_tokens": <[str;N]> -- Foreign keys to the `Attribute` table.
  "visibility_token": <str> -- Foreign key to the `Visibility` table.
  "translation":      <[float;3]> -- Box center in meters.
  "size":             <[float;3]> -- (width, length, height) in meters.
  "rotation":         <[float;4]> -- Quaternion (w, x, y, z).
  "velocity":         <option[[float;3]]> -- (vx, vy, vz) in m/s.
  "acceleration":     <option[[float;3]]> -- (ax, ay, az) in m/s².
  "num_lidar_pts":    <int> -- Number of LiDAR points in the box.
  "num_radar_pts":    <int> -- Number of radar points in the box.
  "next":             <option[str]> -- Foreign key to the next `SampleAnnotation` of the instance.
  "prev":             <option[str]> -- Foreign key to the previous `SampleAnnotation` of the instance.
  "annotation_type":  <AnnotationType> -- See [AnnotationType](#annotationtype).
  "provenance":       <option[str]>
  "confidence":       <option[float]>
}
```

### ObjectAnn

- Filename: `object_ann.json`

A 2D box with an optional instance mask, linked to an instance.

```json
object_ann {
  "token":              <str> -- Unique record identifier.
  "sample_data_token":  <str> -- Foreign key to the `SampleData` table.
  "instance_token":     <str> -- Foreign key to the `Instance` table.
  "category_token":     <str> -- Foreign key to the `Category` table.
  "attribute_tokens":   <[str;N]> -- Foreign keys to the `Attribute` table.
  "bbox":               <[float;4]> -- (xmin, ymin, xmax, ymax) in pixels.
  "mask":               <option[RLE]> -- Instance mask.
  "orientation":        <option[float]> -- Arrow orientation in radians, for categories with `has_orientation`.
  "number":             <option[int]> -- Displayed digit, for categories with `has_number`.
  "annotation_type":    <AnnotationType>
  "provenance":         <option[str]>
  "confidence":         <option[float]>
}
```

`RLE` is defined in [Schema Tables](../table.md#rle).

### SurfaceAnn

- Filename: `surface_ann.json`

A 2D semantic mask of a region without object identity (road, sidewalk, sky).

```json
surface_ann {
  "token":              <str> -- Unique record identifier.
  "sample_data_token":  <str> -- Foreign key to the `SampleData` table.
  "category_token":     <str> -- Foreign key to the `Category` table.
  "mask":               <option[RLE]> -- Semantic mask.
  "annotation_type":    <AnnotationType>
  "provenance":         <option[str]>
  "confidence":         <option[float]>
}
```

### Keypoint

- Filename: `keypoint.json`

```json
keypoint {
  "token":              <str> -- Unique record identifier.
  "sample_data_token":  <str> -- Foreign key to the `SampleData` table.
  "instance_token":     <str> -- Foreign key to the `Instance` table.
  "category_tokens":    <[str;N]> -- Foreign keys to the `Category` table, one per keypoint.
  "keypoints":          <[[float;2];N]> -- (x, y) in pixels.
  "num_keypoints":      <int> -- Number of keypoints.
  "annotation_type":    <AnnotationType>
  "provenance":         <option[str]>
  "confidence":         <option[float]>
}
```

### TrafficLight

- Filename: `traffic_light.json`

The state of one traffic light at one time, keyed by its lanelet2 regulatory element (= Autoware `TrafficLightGroup.traffic_light_group_id`).

```json
traffic_light {
  "token":                  <str> -- Unique record identifier.
  "timestamp":              <int> -- Unix timestamp in microseconds.
  "regulatory_element_id":  <int> -- lanelet2 traffic light regulatory element ID.
  "elements":               <[TrafficLightElement;N]> -- Bulb states, as in Autoware `TrafficLightElement`.
  "object_ann_token":       <option[str]> -- Foreign key to the `ObjectAnn` the state was read from.
  "instance_token":         <option[str]> -- Foreign key to the lamp `Instance`, for states read from 2D labels.
  "annotation_type":        <AnnotationType>
  "provenance":             <option[str]> -- e.g. vendor, recognition model and version, "v2x".
}

TrafficLightElement {
  "color":        <enum["red", "amber", "green", "white", "unknown"]>
  "shape":        <enum["circle", "left_arrow", "right_arrow", "up_arrow", "up_left_arrow", "up_right_arrow", "down_arrow", "down_left_arrow", "down_right_arrow", "cross", "unknown"]>
  "status":       <enum["solid_on", "solid_off", "flashing", "unknown"]>
  "confidence":   <option[float]> -- Confidence in [0, 1].
}
```

### Route

- Filename: `route.json`

The mission route, from Autoware `LaneletRoute`. A re-route adds a new row.

```json
route {
  "token":                <str> -- Unique record identifier.
  "log_token":            <str> -- Foreign key to the `Log` table.
  "map_token":            <str> -- Foreign key to the `Map` table.
  "valid_from":           <int> -- Start of validity, Unix microseconds (inclusive).
  "valid_until":          <option[int]> -- End of validity, Unix microseconds (exclusive). `null` if valid until the end.
  "route_uuid":           <option[str]> -- `LaneletRoute.uuid`.
  "start_pose":           <Pose> -- Start pose in the map frame.
  "goal_pose":            <Pose> -- Goal pose in the map frame.
  "segments":             <[RouteSegment;N]> -- Route segments, in order.
  "allow_modification":   <option[bool]> -- `LaneletRoute.allow_modification`.
  "source":               <enum["mission_planner", "manual", "derived"]> -- Where the route came from.
  "provenance":           <option[str]> -- Where the message was found, e.g. "own_bag", "route_json".
}

RouteSegment {
  "preferred_primitive_id":   <int> -- Preferred lanelet ID.
  "primitive_ids":            <[int;N]> -- All lanelet IDs of the segment.
}
```

### Scenario

- Filename: `scenario.json`

A tagged time interval, e.g. from CodSceneClassifier.

```json
scenario {
  "token":                  <str> -- Unique record identifier.
  "log_token":              <str> -- Foreign key to the `Log` table.
  "start_timestamp":        <int> -- Start, Unix microseconds (inclusive).
  "end_timestamp":          <int> -- End, Unix microseconds (exclusive).
  "key_timestamp":          <option[int]> -- Key moment, Unix microseconds.
  "status":                 <option[enum["whitelist", "blacklist"]]>
  "lateral_decision":       <option[str]>
  "longitudinal_decision":  <option[str]>
  "events":                 <[str;N]>
  "scenery":                <option[object]> -- Kept as given by the classifier.
  "dynamic_entities":       <option[object]> -- Kept as given by the classifier.
  "justification":          <option[str]>
  "taxonomy": {
    "id":                   <str> -- Taxonomy ID, e.g. "cod-scene".
    "version":              <str> -- Taxonomy version, e.g. "0.1.1".
  }
  "annotation_type":        <AnnotationType>
  "provenance":             <option[str]> -- e.g. "cod-scene-classifier 1.0.2".
  "raw":                    <option[object]> -- Original record.
}
```

### Caption

- Filename: `caption.json`

Natural-language text about a time window, for VLM/VLA training.

```json
caption {
  "token":              <str> -- Unique record identifier.
  "log_token":          <str> -- Foreign key to the `Log` table.
  "start_timestamp":    <int> -- Start of the window, Unix microseconds.
  "end_timestamp":      <int> -- End of the window. Equal to `start_timestamp` for a single moment.
  "sample_data_token":  <option[str]> -- Foreign key to the `SampleData` the caption describes, if it is about one image or sweep.
  "scenario_token":     <option[str]> -- Foreign key to a `Scenario`.
  "instance_tokens":    <option[[str;N]]> -- Foreign keys to the `Instance`s the text refers to.
  "caption_type":       <enum["description", "reasoning", "instruction", "question_answer"]> -- Kind of text.
  "text":               <str> -- The text.
  "language":           <str> -- Language code, e.g. "en", "ja".
  "annotation_type":    <AnnotationType> -- VLM-generated captions are "auto".
  "provenance":         <option[str]> -- VLM name and version, prompt ID, annotator or vendor.
  "confidence":         <option[float]>
}
```
