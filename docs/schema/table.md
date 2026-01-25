# Schema Tables

## Type Definition

### Primitive Types

| Expression      | Description                                                      |
| --------------- | ---------------------------------------------------------------- |
| `str`           | String                                                           |
| `int`           | Integer                                                          |
| `float`         | Floating point number                                            |
| `bool`          | Boolean                                                          |
| `enum[X,Y,...]` | Enumerated type with possible values X, Y, ...                   |
| `[T;N]`         | Array of N elements of type T                                    |
| `[T;N,M,...]`   | Array of type T with N, M, or other specified number of elements |
| `option[T]`     | Optional value of type T by default `None`                       |

### Special Types

Some schema contains special types as follows, which are written in key-value pairs in JSON format.

#### `RLE`

The `RLE` type is used to represent run-length encoding of a 2D semantic mask:

```json
RLE {
  "size":                   <[int;2]> -- Mask size [width, height].
  "counts":                 <str> -- Encoded counts, where each count is represented as a pair of integers separated by a comma.
}
```

#### `AutolabelModel`

The `AutolabelModel` type used in `autolabel_metadata` fields has the following structure:

```json
AutolabelModel {
  "name":                     <str> -- Name of the model used for annotation. Can include version information.
  "score":                    <float> -- Label score for the annotation from this model (range: 0.0–1.0).
  "uncertainty":              <option[float]> -- Model-reported uncertainty for the annotation (range: 0.0–1.0). Lower values imply higher confidence.
}
```

#### `Indicators`

The `Indicators` represents the status of vehicle indicators:

```json
Indicators {
  "left":                   <enum["on", "off"]> -- Left indicator status.
  "right":                  <enum["on", "off"]> -- Right indicator status.
  "hazard":                 <enum["on", "off"]> -- Hazard indicator status.
}
```

#### `AdditionalInfo`

The `AdditionalInfo` represents additional information about the vehicle:

```json
AdditionalInfo {
  "speed":                  <option[float]> -- Vehicle speed in meters per second.
}
```

## Mandatory Tables

The following mandatory tables are required for the dataset, so `Tier` class raises runtime error if not found.

### Attribute

- Filename: `attribute.json`

An attribute is a property of an instance that can change while the category remains the same.

For example, a `pedestrian` category can have the following attributes:

- `sitting`: Indicates whether the pedestrian is sitting.
- `standing`: Indicates whether the pedestrian is standing.
- `lying_down`: Indicates whether the pedestrian is lying down.

```json
attribute {
  "token":             <str> -- Unique record identifier.
  "name":              <str> -- Name of the attribute.
  "description":       <str> -- Description of the attribute.
}
```

### CalibratedSensor

- Filename: `calibrated_sensor.json`

Definition of a particular sensor (e.g. LiDAR, camera, radar) as calibrated on a particular vehicle.

All extrinsic parameters are given with respect to the **world coordinate frame**.

```json
calibrated_sensor {
  "token":              <str> -- Unique record identifier.
  "sensor_token":       <str> -- Foreign key to the `Sensor` table.
  "translation":        <[float;3]> -- Extrinsic translation of the sensor. Coordinate system origin in meters: (x, y, z).
  "rotation":           <[float;4]> -- Extrinsic rotation of the sensor. Coordinate system orientation as quaternion: (w, x, y, z).
  "camera_intrinsic":   <[[float;3];3]> -- Intrinsic camera calibration matrix. Empty list `[]` for sensors other than cameras.
  "camera_distortion":  <[float;4,5,8,12,14]> -- Distortion coefficients of the camera following OpenCV convention. Supports 4, 5, 8, 12, or 14 elements for different distortion models. Empty list `[]` for sensors other than cameras.
}
```

### Category

- Filename: `category.json`

Taxonomy of object categories, such as `vehicle.truck`, `vehicle.car`, etc.

```json
category {
  "token":              <str> -- Unique record identifier.
  "name":               <str> -- Name of the category.
  "description":        <str> -- Description of the category.
  "index":              <option[int]> -- Category index, this is added to support `lidarseg`, or `None` when it doesn't support `lidarseg`.
  "has_orientation":    <bool> -- Indicates whether annotations for this category may include an `orientation` field (e.g., traffic light arrows). If omitted, it is treated as `false`.
  "has_number":         <bool> -- Indicates whether annotations for this category may include a `number` field (e.g., numeric traffic lights). If omitted, it is treated as `false`.
}
```

### EgoPose

- Filename: `ego_pose.json`

Definition of the ego vehicle's pose at a particular timestamp.

This includes both the vehicle's position and orientation in space, typically referred in a global coordinate system such as the map or odometry frame.

```json
ego_pose {
  "token":              <str> -- Unique record identifier.
  "translation":        <[float;3]> -- Location of the ego vehicle. Coordinate system origin in meters: (x, y, z).
  "rotation":           <[float;4]> -- Rotation of the ego vehicle. Coordinate system orientation as quaternion: (w, x, y, z).
  "twist":              <option[[float;6]]> -- Linear and angular velocity in the local coordinate system of the ego vehicle. Coordinate system velocity as vector: (vx, vy, vz, yaw_rate, pitch_rate, roll_rate).
  "acceleration":       <option[[float;3]]> -- Linear acceleration in the **local** coordinate system of the ego vehicle, (ax, ay, az).
  "geocoordinate":      <option[[float;3]]> -- Geographical coordinates of the ego vehicle. Coordinate system origin in meters: (latitude, longitude, altitude).
}
```

### Instance

- Filename: `instance.json`

A particular object instance. This table is an enumeration of all object instances we observed.

Note that instances are not tracked across scenes.
For example, even if an object has the same instance in scene A and B, it should be considered as two different instances.

```json
instance {
  "token":                  <str> -- Unique record identifier.
  "category_token":         <str> -- Foreign key to the `Category` table.
  "instance_name":          <str> -- Consists of the dataset name and the instance ID separated by colons `::`, such as `<DATASET_ID>::<INSTANCE_ID>`.
  "nbr_annotations":        <int> -- Number of annotations associated with this instance.
  "first_annotation_token": <str> -- Foreign key to the first `SampleAnnotation` table associated with this instance. Empty string `""` if the dataset only contains 2D annotations.
  "last_annotation_token":  <str> -- Foreign key to the last `SampleAnnotation` table associated with this instance. Empty string `""` if the dataset only contains 2D annotations.
}
```

### Log

- Filename: `log.json`

Log information on the data from which the data was collected.

```json
log {
  "token":                  <str> -- Unique record identifier.
  "logfile":                <str> -- Path to the log file.
  "vehicle":                <str> -- Name of the vehicle.
  "data_captured":          <str> -- Data captured by the vehicle given as `YYYY-MM-DD-HH-MM-SS`.
  "location":               <str> -- Location of the vehicle.
}
```

### Map

- Filename: `map.json`

```json
map {
  "token":                  <str> -- Unique record identifier.
  "log_tokens":             <[str;N]> -- List of foreign keys to the `Log` table associated with this map.
  "category":               <str> -- Category of the map.
  "filename":               <str> -- Relative path to the binary file of the map mask.
}
```

### Sample

- Filename: `sample.json`

A sample is an annotated keyframe. The timestamp of a sample is the same as that of a LiDAR sample data.

```json
sample {
  "token":                  <str> -- Unique record identifier.
  "timestamp":              <int> -- Unix timestamp in microseconds, which is the same as the `timestamp` field in the corresponding LiDAR `SampleData` table.
  "scene_token":            <str> -- Foreign key to the `Scene` table associated with this sample.
  "next":                   <str> -- Foreign key to the next `Sample` table associated with this sample. Empty string `""` if this is the last sample.
  "prev":                   <str> -- Foreign key to the previous `Sample` table associated with this sample. Empty string `""` if this is the first sample.
}
```

### SampleAnnotation

- Filename: `sample_annotation.json`

An annotation for 3D objects in a sample. All location data are given with respect to **the global coordinate system**.

```json
sample_annotation {
  "token":                  <str> -- Unique record identifier.
  "sample_token":           <str> -- Foreign key to the `Sample` table associated with this annotation.
  "instance_token":         <str> -- Foreign key to the `Instance` table associated with this annotation.
  "attribute_tokens":       <[str;N]> -- Foreign keys to the `Attribute` table associated with this annotation.
  "visibility_token":       <str> -- Foreign key to the `Visibility` table associated with this annotation.
  "translation":            <[float;3]> -- Center location of the cuboid in meters as (x, y, z).
  "rotation":               <[float;4]> -- Quaternion representing the orientation of the cuboid as (w, x, y, z).
  "size":                   <[float;3]> -- Size of the cuboid in meters as (width, length, height).
  "velocity":               <option[[float;3]]> -- Velocity of the cuboid in meters per second as (vx, vy, vz).
  "acceleration":           <option[[float;3]]> -- Acceleration of the cuboid in meters per second squared as (ax, ay, az).
  "num_lidar_pts":          <int> -- Number of lidar points within the cuboid.
  "num_radar_pts":          <int> -- Number of radar points within the cuboid.
  "next":                   <str> -- Foreign key to the `SampleAnnotation` table associated with the next annotation in the sequence. Empty string `""` if this is the last annotation.
  "prev":                   <str> -- Foreign key to the `SampleAnnotation` table associated with the previous annotation in the sequence. Empty string `""` if this is the first annotation.
  "automatic_annotation":   <bool> -- Indicates whether the annotation was automatically generated. Defaults to `false`.
  "autolabel_metadata":     <option[[AutolabelModel;N]]> -- List of models used for autolabeling. Required if `automatic_annotation` is `true`.
}
```

### SampleData

- Filename: `sample_data.json`

A sensor data, such as image, point cloud, or radar return.
If the `is_key_frame=True`, the timestamp should be very close to the associated sample's timestamp.

```json
sample_data {
  "token":                    <str> -- Unique record identifier.
  "sample_token":             <str> -- Foreign key to the `Sample` table. Empty string `""` if this is not a key frame.
  "ego_pose_token":           <str> -- Foreign key to the `EgoPose` table.
  "calibrated_sensor_token":  <str> -- Foreign key to the `CalibratedSensor` table.
  "filename":                 <str> -- Relative path from a dataset root directory to the sensor data file.
  "fileformat":               <enum["jpg", "png", "pcd", "bin", "pcd.bin"]> -- File format of the sensor data file.
  "width":                    <int> -- Width of the image in pixels.
  "height":                   <int> -- Height of the image in pixels.
  "timestamp":                <int> -- unix timestamp in microseconds.
  "is_key_frame":             <bool> -- Indicates whether this is a key frame.
  "next":                     <str> -- Foreign key to the `SampleData` table associated with the next data in the sequence. Empty string `""` if this is the last data.
  "prev":                     <str> -- Foreign key to the `SampleData` table associated with the previous data in the sequence. Empty string `""` if this is the first data.
  "is_valid":                 <bool> -- Indicates whether this data is valid. Defaults to `true`.
  "info_filename":            <option[str]> -- Relative path to metadata-blob file.
  "autolabel_metadata":       <option[[AutolabelModel;N]]> -- List of models used for autolabeling applied to this entire sample_data item (e.g., image or scan).
}
```

### Scene

- Filename: `scene.json`

A scene is a sequence of consecutive frames extracted from a log.
In T4 format, only one scene is included in a single dataset.

```json
scene {
  "token":                    <str> -- Unique record identifier.
  "name":                     <str> -- Name of the scene, given as `{PROJECT_NAME}_{SCENE_TOKEN}`.
  "description":              <str> -- Description of the scene.
  "log_token":                <str> -- Foreign key to the `Log` table associated with the log that contains this scene.
  "nbr_samples":              <int> -- Number of samples in the scene.
  "first_sample_token":       <str> -- Foreign key to the `Sample` table associated with the first data in the scene.
  "last_sample_token":        <str> -- Foreign key to the `Sample` table associated with the last data in the scene.
}
```

### Sensor

- Filename: `sensor.json`

A description of sensor types.

```json
sensor {
  "token":                    <str> -- Unique record identifier.
  "channel":                  <str> -- Channel of the sensor.
  "modality":                 <enum["camera", "lidar", "radar"]> -- Modality of the sensor.
}
```

### Visibility

- Filename: `visibility.json`

A description of annotation visibility status.

Visibility level is classified into 4 bins below:

- full: The annotation is fully visible.
- most: The annotation is mostly visible, more than 50%.
- partial: The annotation is partially visible, more than 10% but less than 50%.
- none: The annotation is not visible.

```json
visibility {
  "token":                    <str> -- Unique record identifier.
  "level":                    <enum["full", "most", "partial", "none"]> -- Level of visibility of the annotation.
  "description":              <str> -- Description of the visibility level.
}
```

<!-- prettier-ignore-start -->
??? WARNING
    Following old formats are also supported but deprecated:

    <!-- markdownlint-disable MD046 -->
    ```yaml
    - v80-100 : full
    - v60-80  : most
    - v40-60  : partial
    - v0-40   : none
    ```

    If input level does not satisfy any above cases, `VisibilityLevel.UNAVAILABLE` will be assigned.
<!-- prettier-ignore-end -->

## Optional Tables

The following tables are optional, and skipped loading by `Tier4` class if not exists.

### LidarSeg

- Filename: `lidarseg.json`

Mapping between LiDAR segmentation annotations and `SampleData` corresponding to the LiDAR point cloud associated with a keyframe.

```json
lidarseg {
  "token":                    <str> -- Unique record identifier.
  "filename":                 <str> -- Filename of the LiDAR segmentation annotation labels that is an array of unit8.
  "sample_data_token":        <str> -- Foreign key to the `SampleData` table associated with the sample data.
}
```

### ObjectAnn

- Filename: `object_ann.json`

The annotation of a foreground object (car, bike, pedestrian, etc.) in an image. Each foreground object is annotated with a 2D box, a 2D instance mask and category-specific attributes.

```json
object_ann {
  "token":                    <str> -- Unique record identifier.
  "sample_data_token":        <str> -- Foreign key to the `SampleData` table associated with the sample data.
  "instance_token":           <str> -- Foreign key to the `Instance` table associated with the instance of the object.
  "category_token":           <str> -- Foreign key to the `Category` table associated with the category of the object.
  "attribute_tokens":         <[str;N]> -- Foreign keys to the `Attribute` table associated with the attributes of the object.
  "bbox":                     <[int;4]> -- Bounding box coordinates in the format (xmin, ymin, xmax, ymax).
  "mask":                     <RLE> -- Run length encoding of instance mask.
  "orientation":              <option[float]> -- Orientation of the arrow shape within the bounding box, in radians. Present only for categories where `has_orientation` is true (e.g., traffic light arrows).
  "number":                   <option[int]> -- The digit displayed within the bounding box. Present only for categories where `has_number` is true (e.g., numeric traffic lights).
  "automatic_annotation":     <bool> -- Whether the annotation was automatically generated. Defaults to `false`.
  "autolabel_metadata":       <option[[AutolabelModel;N]]> -- List of models used for autolabeling. Required if `automatic_annotation` is `true`.
}
```

### SurfaceAnn

- Filename: `surface_ann.json`

The annotation of a background object (drivable surface) in an image. Each background object is annotated with a 2d semantic segmentation mask.

```json
surface_ann {
  "token":                    <str> -- Unique record identifier.
  "sample_data_token":        <str> -- Foreign key to the `SampleData` table associated with the sample data.
  "category_token":           <str> -- Foreign key to the `Category` table associated with the category of the surface.
  "instance_token":           <option[str]> -- Foreign key to the `Instance` table associated with the instance of the surface.
  "attribute_tokens":         <list[str]> -- Foreign keys to the `Attribute` table associated with the attributes of the surface. Defaults to `[]`.
  "mask":                     <option[RLE]> -- Run length encoding of instance mask.
  "automatic_annotation":     <bool> -- Whether the annotation was automatically generated. Defaults to `false`.
  "autolabel_metadata":       <option[[AutolabelModel;N]]> -- List of models used for autolabeling. Required if `automatic_annotation` is `true`.
}
```

### VehicleState

- Filename: `vehicle_state.json`

This table provides comprehensive information about the vehicle's state at a given timestamp, including the status of doors, indicators, steering, and other relevant information.

```json
vehicle_state {
  "token":                    <str> -- Unique record identifier.
  "timestamp":                <int> -- Unix timestamp in microseconds.
  "accel_pedal":              <option[float]> -- Accelerator pedal position percentage.
  "brake_pedal":              <option[float]> -- Brake pedal position percentage.
  "steer_pedal":              <option[float]> -- Steering wheel position percentage.
  "steering_tire_angle":      <option[float]> -- Steering tire angle in radians.
  "steering_wheel_angle":     <option[float]> -- Steering wheel angle in radians.
  "shift_state":              <option[enum["PARK", "REVERSE", "NEUTRAL", "HIGH", "FORWARD", "LOW", "NONE"]]> -- Shift state of the vehicle.
  "indicators":               <option[Indicators]> -- Indicator state of the vehicle.
  "additional_info":          <option[AdditionalInfo]> -- Additional information about the vehicle state.
}
```
