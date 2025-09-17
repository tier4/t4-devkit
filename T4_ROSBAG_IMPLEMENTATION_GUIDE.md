# T4 to ROS2 Bag Implementation Guide - Code Reuse Analysis

## Existing T4-Devkit Capabilities to Reuse

### 1. **Interpolation System (ALREADY IMPLEMENTED)**
Location: `t4_devkit/tier4.py:600-662` in `get_boxes()` method

**What it does:**
- Interpolates 3D bounding boxes between keyframes
- Handles position with linear interpolation
- Handles rotation with Quaternion SLERP
- Manages instance tracking across frames

**How to reuse:**
```python
# Direct usage for interpolation at any timestamp
boxes = t4.get_boxes(sample_data_token, future_seconds=0.0)
```

### 2. **Velocity Calculation (ALREADY IMPLEMENTED)**
Location: `t4_devkit/tier4.py:678-699` in `box_velocity()` method

**What it does:**
- Returns annotated velocity if available
- Estimates velocity from position differences
- Handles edge cases with NaN values

**How to reuse:**
```python
velocity = t4.box_velocity(sample_annotation_token)
```

### 3. **Timeseries Helper (ALREADY IMPLEMENTED)**
Location: `t4_devkit/helper/timeseries.py`

**What it does:**
- Fetches annotations within time windows
- Handles forward/backward time exploration
- Returns timestamps with annotations

**How to reuse:**
```python
from t4_devkit.helper import TimeseriesHelper
helper = TimeseriesHelper(t4)
timestamps, anns = helper.get_sample_annotations_until(
    instance_token, sample_token, seconds=1.0
)
```

### 4. **Box3D Data Structure (ALREADY IMPLEMENTED)**
Location: `t4_devkit/dataclass/box.py`

**What it provides:**
- Complete 3D box representation
- Coordinate transforms
- Serialization support
- All fields needed for TrackedObject

**Fields available:**
- `unix_time`: Timestamp in microseconds
- `position`: 3D center point
- `rotation`: Quaternion orientation
- `velocity`: 3D velocity vector
- `shape`: Dimensions (length, width, height)
- `semantic_label`: Category and attributes
- `confidence`: Detection confidence
- `uuid`: Instance identifier
- `num_points`: LiDAR point count
- `visibility`: Visibility level

### 5. **Coordinate Transformations (ALREADY IMPLEMENTED)**
Location: `t4_devkit/tier4.py` various transform methods

**What it provides:**
- Sensor to ego transforms
- Ego to global transforms
- Full transform chains

**How to reuse:**
```python
# Transform box from global to ego frame
box_ego = t4.transform_box_to_ego(box_global, ego_pose)
```

### 6. **CLI Framework (ALREADY IMPLEMENTED)**
Location: `t4_devkit/cli/`

**What it provides:**
- Typer-based CLI structure
- Argument parsing patterns
- Progress bar integration

**How to reuse:**
```python
# Extend existing CLI pattern
from t4_devkit.cli import cli
@cli.command("inject-rosbag")
def inject_rosbag(...):
    pass
```

### 7. **Timestamp Utilities (ALREADY IMPLEMENTED)**
Location: `t4_devkit/common/timestamp.py`

**What it provides:**
- Microsecond to second conversion
- Timestamp formatting
- Time range calculations

**How to reuse:**
```python
from t4_devkit.common.timestamp import us2sec, sec2us
```

## New Code Required

### 1. **ROS2 Bag Interface Module** (NEW)
```python
# t4_devkit/rosbag/reader.py
class RosbagReader:
    - Read bag metadata
    - Extract topic timestamps
    - Stream message reading
    
# t4_devkit/rosbag/writer.py
class RosbagWriter:
    - Copy bag structure
    - Add new topic
    - Write synchronized messages
```

### 2. **Message Converter** (NEW)
```python
# t4_devkit/rosbag/converter.py
class T4ToAutowareConverter:
    - Box3D → TrackedObject
    - Category mapping
    - Coordinate frame conversion
```

### 3. **Synchronization Engine** (NEW)
```python
# t4_devkit/rosbag/sync.py
class TimeSync:
    - Find nearest annotations
    - Trigger interpolation
    - Maintain temporal order
```

### 4. **Main Injection Pipeline** (NEW)
```python
# t4_devkit/rosbag/injector.py
class AnnotationInjector:
    - Orchestrate full pipeline
    - Handle batch processing
    - Progress tracking
```

## Simplified Implementation Using Existing Code

### Step 1: Load and Prepare Data
```python
from t4_devkit import Tier4

# Initialize T4 (existing)
t4 = Tier4(data_root, verbose=False)

# Get scene and samples (existing)
scene = t4.scene[0]
samples = [t4.get('sample', token) for token in scene.sample_tokens]
```

### Step 2: Extract Target Timestamps from Rosbag
```python
import rosbag2_py

# NEW: Read tracking topic timestamps
reader = rosbag2_py.SequentialReader()
reader.open(storage_options, converter_options)

target_timestamps = []
while reader.has_next():
    topic, msg, t = reader.read_next()
    if topic == '/perception/object_recognition/tracking/objects':
        target_timestamps.append(t)
```

### Step 3: Get Interpolated Boxes (Using Existing Code)
```python
# For each target timestamp, find the appropriate sample_data
for target_ns in target_timestamps:
    target_us = target_ns // 1000  # Convert to microseconds
    
    # Find closest sample_data (existing helper could be extended)
    closest_sd = find_closest_sample_data(t4, target_us)
    
    # Get interpolated boxes at this timestamp (EXISTING METHOD)
    boxes = t4.get_boxes(closest_sd.token)
    
    # Boxes are already interpolated!
```

### Step 4: Convert to TrackedObjects (NEW)
```python
from autoware_perception_msgs.msg import TrackedObjects, TrackedObject

def box3d_to_tracked_object(box: Box3D) -> TrackedObject:
    """Convert T4 Box3D to Autoware TrackedObject."""
    obj = TrackedObject()
    
    # Direct field mapping from existing Box3D
    obj.object_id.uuid = box.uuid
    obj.existence_probability = box.confidence
    
    # Position (already in box)
    obj.kinematics.pose_with_covariance.pose.position.x = box.position[0]
    obj.kinematics.pose_with_covariance.pose.position.y = box.position[1] 
    obj.kinematics.pose_with_covariance.pose.position.z = box.position[2]
    
    # Orientation (already quaternion in box)
    obj.kinematics.pose_with_covariance.pose.orientation = box.rotation
    
    # Velocity (already calculated by t4)
    if box.velocity is not None:
        obj.kinematics.twist_with_covariance.twist.linear.x = box.velocity[0]
        obj.kinematics.twist_with_covariance.twist.linear.y = box.velocity[1]
        obj.kinematics.twist_with_covariance.twist.linear.z = box.velocity[2]
    
    # Shape (already in box)
    obj.shape.type = Shape.BOUNDING_BOX
    obj.shape.dimensions.x = box.shape.size[0]  # length
    obj.shape.dimensions.y = box.shape.size[1]  # width
    obj.shape.dimensions.z = box.shape.size[2]  # height
    
    return obj
```

### Step 5: Write to Bag (NEW)
```python
# NEW: Bag writing logic
writer = rosbag2_py.SequentialWriter()
writer.open(output_storage, converter)

# Copy original messages and inject new ones
# at synchronized timestamps
```

## Code Reuse Summary

### Fully Reused Components (90% of complexity):
1. **Interpolation Logic** - Complete implementation in `get_boxes()`
2. **Velocity Calculation** - `box_velocity()` method
3. **Timestamp Handling** - `common/timestamp.py` utilities
4. **Data Structures** - `Box3D` class with all needed fields
5. **Dataset Loading** - `Tier4` class and schema system
6. **CLI Framework** - Typer-based structure
7. **Coordinate Transforms** - Transform methods in `Tier4`
8. **Timeseries Helpers** - Window-based annotation fetching

### New Components Required (10% of complexity):
1. **Rosbag I/O** - Reading and writing bag files
2. **Message Conversion** - Box3D to TrackedObject mapping
3. **Time Synchronization** - Aligning T4 and ROS timestamps
4. **Main Pipeline** - Orchestration logic

## Key Insights

The T4-devkit already implements the most complex parts:
- **Interpolation is fully handled** by `get_boxes()` including linear position and SLERP rotation
- **Velocity is already calculated** with fallback estimation
- **All data structures exist** with the exact fields needed

The main new work is just:
1. Reading ROS bag timestamps
2. Simple field mapping from Box3D to TrackedObject
3. Writing the new messages to the bag

## Recommended Approach

Instead of reimplementing interpolation, we should:

1. **Extend `Tier4` class** with a method like `get_boxes_at_timestamp(timestamp_us)`
2. **Create thin wrapper** for Box3D → TrackedObject conversion
3. **Focus on bag I/O** as the main new component

This approach reuses ~90% of existing code and only adds the ROS-specific integration layer.

## Example Minimal Implementation

```python
# Main implementation leveraging existing code
class T4RosbagInjector:
    def __init__(self, t4: Tier4):
        self.t4 = t4  # Reuse entire T4 infrastructure
        
    def inject_annotations(self, input_bag, output_bag, sync_topic):
        # Step 1: Read sync timestamps (NEW)
        timestamps = self.read_sync_timestamps(input_bag, sync_topic)
        
        # Step 2: Get interpolated boxes (EXISTING)
        for ts in timestamps:
            boxes = self.get_boxes_at_timestamp(ts)  # Wrapper around t4.get_boxes()
            
            # Step 3: Convert to ROS (NEW - simple mapping)
            msg = self.boxes_to_tracked_objects(boxes, ts)
            
            # Step 4: Write to bag (NEW)
            self.write_message(msg, ts)
    
    def get_boxes_at_timestamp(self, timestamp_ns):
        # Find closest sample_data
        sd_token = self.find_closest_sample_data(timestamp_ns)
        
        # Use EXISTING interpolation
        return self.t4.get_boxes(sd_token)
```

This design maximizes code reuse and minimizes new development, leveraging the robust interpolation and data handling already implemented in T4-devkit.