# T4 Dataset to ROS2 Bag Annotation Injector

## Project Overview

This project aims to parse T4 dataset 3D bounding box annotations and inject them into a ROS2 bag file as TrackedObjects messages. The annotations will be interpolated from their original sample rate (1-2Hz) to match the perception pipeline frequency (10Hz), synchronized with existing tracking topics.

## Key Requirements

1. **Input**: T4 dataset containing:
   - Annotation files (JSON format with 3D bounding boxes)
   - ROS2 bag file with perception data

2. **Output**: Modified ROS2 bag with:
   - Original topics preserved
   - New topic: `/perception/object_recognition/tracking/ground_truth` (TrackedObjects type)
   - Annotations interpolated to 10Hz
   - Timestamps synchronized with existing `/perception/object_recognition/tracking/objects`

3. **Processing Pipeline**:
   - Parse T4 annotations at original frequency
   - Interpolate bounding boxes to match target timestamps
   - Convert to TrackedObjects format
   - Inject into bag with proper synchronization

## Implementation Architecture

### Phase 1: Data Loading and Parsing
```
T4 Dataset → T4 Devkit → Annotation Objects → Bounding Box Data
```

### Phase 2: Temporal Alignment
```
ROS Bag Timeline → Extract Target Timestamps → Map to T4 Annotations
```

### Phase 3: Interpolation
```
Sparse Annotations → Linear/SLERP Interpolation → Dense Annotations
```

### Phase 4: Message Conversion
```
T4 Box3D → TrackedObject → TrackedObjects Message
```

### Phase 5: Bag Injection
```
Original Bag → Copy → Add New Topic → Write Synchronized Messages
```

## Detailed Implementation Steps

### Step 1: Environment Setup
- Install required dependencies:
  - `t4-devkit` (existing)
  - `rosbag2_py` for bag manipulation
  - `rclpy` for ROS2 message handling
  - `numpy` for interpolation
  - `pyquaternion` for rotation interpolation

### Step 2: T4 Dataset Loading
```python
# Load T4 dataset using existing devkit
from t4_devkit import Tier4

t4 = Tier4(data_root, verbose=False)
# Access scenes, samples, and annotations
```

### Step 3: ROS Bag Analysis
```python
# Open original bag and analyze structure
import rosbag2_py

reader = rosbag2_py.SequentialReader()
# Read tracking topic timestamps for synchronization
```

### Step 4: Annotation Extraction Pipeline

**4.1 Build Annotation Timeline**
- Extract all SampleAnnotation records for the scene
- Group by instance_token (track ID)
- Build temporal index for efficient lookup

**4.2 Coordinate System Mapping**
- T4 uses global "map" frame coordinates
- Transform to vehicle frame if needed
- Handle sensor calibration data

### Step 5: Interpolation Engine

**5.1 Position Interpolation**
- Use linear interpolation for box centers
- Handle edge cases (start/end of tracks)
- Validate interpolated positions

**5.2 Orientation Interpolation**
- Use Quaternion SLERP for smooth rotation
- Handle orientation discontinuities
- Preserve heading consistency

**5.3 Velocity Estimation**
- Use existing `box_velocity` method from T4
- Calculate from position differences if unavailable
- Apply smoothing filters

### Step 6: Message Construction

**6.1 TrackedObject Mapping**
```python
# T4 Box3D → TrackedObject conversion
tracked_obj = TrackedObject()
tracked_obj.object_id.uuid = box.uuid  # instance_token
tracked_obj.existence_probability = box.confidence
tracked_obj.classification = map_t4_to_autoware_class(box.semantic_label)
tracked_obj.kinematics.pose_with_covariance.pose.position = box.position
tracked_obj.kinematics.pose_with_covariance.pose.orientation = box.rotation
tracked_obj.kinematics.twist_with_covariance.twist.linear = box.velocity
tracked_obj.shape = create_bounding_box_shape(box.shape)
```

**6.2 Classification Mapping**
- Map T4 categories to Autoware object types
- Handle attribute mapping
- Set appropriate confidence scores

### Step 7: Temporal Synchronization

**7.1 Timeline Alignment**
```python
# For each message in /perception/object_recognition/tracking/objects
for target_timestamp in tracking_timestamps:
    # Find closest T4 sample
    closest_sample = find_nearest_sample(target_timestamp)
    
    # Interpolate if necessary
    if needs_interpolation:
        boxes = interpolate_boxes_at_timestamp(target_timestamp)
    else:
        boxes = get_boxes_at_sample(closest_sample)
    
    # Convert and write
    msg = create_tracked_objects_msg(boxes, target_timestamp)
```

**7.2 Interpolation Triggers**
- Calculate time delta between samples
- Interpolate if delta > threshold (e.g., 50ms)
- Use nearest neighbor for small deltas

### Step 8: Bag Writing

**8.1 Bag Setup**
```python
writer = rosbag2_py.SequentialWriter()
# Copy original bag metadata
# Add new topic definition
```

**8.2 Message Writing**
- Write all original messages unchanged
- Insert ground truth messages at synchronized timestamps
- Maintain message ordering

### Step 9: Validation and Quality Checks

**9.1 Data Integrity**
- Verify all tracks are continuous
- Check for interpolation artifacts
- Validate timestamp monotonicity

**9.2 Coordinate Validation**
- Ensure boxes remain in valid regions
- Check for unrealistic velocities
- Verify orientation consistency

## Key Technical Considerations

### Existing T4 Devkit Capabilities
- **Interpolation Support**: `get_boxes` method already handles interpolation between keyframes
- **Velocity Calculation**: `box_velocity` provides velocity estimates
- **Timeseries Helper**: Can fetch annotations within time windows
- **Coordinate Transforms**: Built-in sensor calibration and transform chains

### Message Type Mapping

#### T4 Box3D Fields → TrackedObject
| T4 Field | TrackedObject Field | Notes |
|----------|-------------------|--------|
| uuid/instance_token | object_id.uuid | Unique track identifier |
| position | kinematics.pose.position | 3D center point |
| rotation | kinematics.pose.orientation | Quaternion |
| shape.size | shape.dimensions | Length, width, height |
| velocity | kinematics.twist.linear | Linear velocity |
| semantic_label.category | classification[0].label | Object class |
| confidence | existence_probability | Detection confidence |
| num_points | - | Not directly mapped |
| visibility | - | Could influence confidence |

### Interpolation Strategy

1. **Between Keyframes** (already annotated samples):
   - Linear interpolation for position
   - SLERP for orientation
   - Linear for dimensions (usually constant)
   - Velocity from finite differences

2. **Track Boundaries**:
   - Start: Use first annotation without extrapolation
   - End: Use last annotation without extrapolation
   - New tracks: Fade in existence_probability
   - Ending tracks: Fade out existence_probability

3. **Missing Data Handling**:
   - Gap < 1 second: Interpolate
   - Gap > 1 second: Split into separate track segments
   - Single frame detections: Skip or mark low confidence

### Performance Optimization

1. **Caching**:
   - Pre-load all annotations for the scene
   - Build instance-to-annotation lookup tables
   - Cache interpolated results

2. **Batch Processing**:
   - Process entire scenes at once
   - Vectorize interpolation operations
   - Use numpy for bulk calculations

3. **Memory Management**:
   - Stream bag reading/writing
   - Process in chunks if needed
   - Clear caches between scenes

## Required Python Packages

```python
# Core dependencies
t4-devkit  # Existing T4 dataset toolkit
rosbag2-py  # ROS2 bag manipulation
rclpy  # ROS2 Python client
autoware-perception-msgs  # Message definitions

# Utilities
numpy  # Numerical operations
pyquaternion  # Rotation handling (already in t4-devkit)
tqdm  # Progress bars
typer  # CLI interface (already in t4-devkit)
```

## CLI Tool Design

```bash
# Basic usage
t4_to_rosbag inject \
    --t4-dataset /path/to/t4/dataset \
    --input-bag /path/to/original.bag \
    --output-bag /path/to/modified.bag \
    --topic-name /perception/object_recognition/tracking/ground_truth \
    --target-rate 10.0 \
    --sync-topic /perception/object_recognition/tracking/objects

# Advanced options
    --interpolation-method [linear|cubic]  # Position interpolation
    --max-interpolation-gap 1.0  # Max seconds to interpolate
    --coordinate-frame [map|base_link]  # Output frame
    --class-mapping config.yaml  # Custom class mappings
    --verbose  # Debug output
```

## Testing Strategy

1. **Unit Tests**:
   - Interpolation accuracy
   - Message conversion
   - Timestamp alignment

2. **Integration Tests**:
   - Small test dataset
   - Verify bag structure
   - Check message synchronization

3. **Validation Metrics**:
   - Interpolation error vs ground truth
   - Temporal alignment accuracy
   - Track continuity statistics

## Potential Challenges and Solutions

### Challenge 1: Timestamp Precision
- T4 uses microseconds, ROS uses nanoseconds
- Solution: Careful conversion with rounding

### Challenge 2: Coordinate Frame Differences
- T4 uses global map frame, ROS may use base_link
- Solution: Transform using ego_pose data

### Challenge 3: Track ID Consistency
- Instance tokens are strings, object_id needs UUID
- Solution: Hash instance tokens to generate UUIDs

### Challenge 4: Large Bag Files
- Copying entire bags can be slow
- Solution: Stream processing, parallel I/O

### Challenge 5: Annotation Gaps
- Some objects may not be annotated in every frame
- Solution: Interpolation with confidence decay

## Next Steps

1. Create project structure and boilerplate
2. Implement T4 annotation loader module
3. Build interpolation engine
4. Create message converter
5. Implement bag writer with synchronization
6. Add CLI interface
7. Write comprehensive tests
8. Document usage and examples