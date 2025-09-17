#!/bin/bash

# Test script for T4 to ROS2 bag conversion with annotation injection

echo "=== T4 to ROS2 Bag Conversion Test ==="
echo ""

# Source ROS2 and Autoware workspace
echo "1. Sourcing ROS2 and Autoware workspace..."
source /opt/ros/humble/setup.bash
source ~/autoware/install/setup.bash

# Set environment variable to use system packages
export UV_SYSTEM_SITE_PACKAGES=1

# Test paths - update these as needed
T4_DATA_ROOT="/home/danielsanchez/.webauto/data/data/annotation_dataset/ac00a455-3c9a-46ac-97a8-276b42a4ddda/0"
SOURCE_BAG="/path/to/source.db3"  # Update this path
OUTPUT_DIR="./t4_rosbag_output"

# Create output directory
mkdir -p $OUTPUT_DIR

# Run the conversion
echo "2. Running T4 to ROS2 bag conversion..."
echo "   T4 Dataset: $T4_DATA_ROOT"
echo "   Source Bag: $SOURCE_BAG"
echo "   Output Dir: $OUTPUT_DIR"
echo ""

uv run t4rosbag convert \
    "$T4_DATA_ROOT" \
    -o "$OUTPUT_DIR" \
    --source-bag "$SOURCE_BAG" \
    --interpolation-hz 10.0 \
    --topic "/annotation/object_recognition/tracked_objects" \
    --frame-id "map"

echo ""
echo "3. Checking output..."
if [ -f "$OUTPUT_DIR/scene_*.db3" ]; then
    echo "✓ Output bag created successfully"
    
    # Check bag info
    echo ""
    echo "4. Bag information:"
    ros2 bag info "$OUTPUT_DIR"/scene_*.db3
else
    echo "✗ No output bag found"
fi

echo ""
echo "=== Test Complete ==="