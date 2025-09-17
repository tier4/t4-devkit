# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

T4-devkit is a Python toolkit for loading and operating on T4 dataset, focusing on autonomous driving data visualization and validation. The project uses Rerun SDK for 3D visualization and supports various data schemas including 3D/2D boxes, point clouds, images, and vector maps.

## Development Setup & Commands

### Environment Management
```bash
# Install dependencies using uv (required)
uv sync --python 3.10

# Activate virtual environment
source .venv/bin/activate
```

### Testing
```bash
# Run all tests with coverage
uv run pytest --cov-report xml:coverage.xml --cov=t4_devkit

# Run specific test file
uv run pytest tests/test_tier4.py

# Run specific test function
uv run pytest tests/test_tier4.py::TestClassName::test_method_name
```

### Code Quality
```bash
# Format code with Ruff
uv run ruff format

# Check code style and fix issues
uv run ruff check --fix

# Run pre-commit hooks manually
pre-commit run --all-files
```

### CLI Tools
```bash
# Visualization commands (t4viz)
uv run t4viz scene <data_root> -o ./output
uv run t4viz instance <data_root> <instance_token> -o ./output
uv run t4viz pointcloud <data_root> -o ./output

# Sanity check command (t4sanity)
uv run t4sanity <db_parent> -iw
```

## Architecture & Core Components

### Main Entry Point: `Tier4` Class
Located in `t4_devkit/tier4.py`, this is the primary interface for dataset operations. It handles:
- Dataset loading and metadata management
- Schema table loading and validation
- Scene/sample/annotation data access
- Coordinate transformations and sensor calibration
- Rendering and visualization pipelines

### Schema System (`t4_devkit/schema/`)
Defines the data structure for autonomous driving datasets:
- **Tables**: Scene, Sample, SampleData, SampleAnnotation, Instance, EgoPose, CalibratedSensor
- **Annotations**: ObjectAnn (3D boxes), SurfaceAnn (segmentation), Keypoint
- **Metadata**: Category, Attribute, Visibility, Sensor, Map
- All schemas are built using the `build_schema()` factory with strict validation

### Data Classes (`t4_devkit/dataclass/`)
Core data structures for geometric representations:
- `Box3D`: 3D bounding boxes with position, rotation, size
- `Box2D`: 2D bounding boxes for image space
- `Shape`: Polygon/polyline representations
- `SemanticLabel`: Category and attribute labeling
- All classes support transformation operations and serialization

### Visualization (`t4_devkit/viewer/`)
Uses Rerun SDK for real-time 3D/2D visualization:
- `RerunViewer`: Main visualization interface
- `ViewerConfig`: Configuration for rendering options
- Supports point clouds, 3D boxes, trajectories, images, and map overlays

### CLI Tools (`t4_devkit/cli/`)
Command-line interfaces for common operations:
- `visualize.py`: Scene and instance visualization (`t4viz`)
- `sanity.py`: Dataset validation and integrity checks (`t4sanity`)

### Helper Modules
- `t4_devkit/common/`: Geometry utilities, IO operations, timestamp handling
- `t4_devkit/filtering/`: Box filtering and visibility checks
- `t4_devkit/lanelet/`: Lanelet2 map format support

## Key Design Patterns

1. **Schema-First Design**: All data structures are defined as schemas with strict validation before use
2. **Lazy Loading**: Tables are loaded on-demand from JSON files to optimize memory usage
3. **Token-Based References**: Objects reference each other using unique tokens rather than direct pointers
4. **Coordinate System Transformations**: Consistent transformation pipeline from sensor → ego → global coordinates
5. **Modular Visualization**: Separate viewer configs for different visualization modes (scene/instance/pointcloud)

## Testing Approach

Tests are organized by module in the `tests/` directory. Each module has corresponding test files that validate:
- Schema loading and validation
- Data transformations and coordinate conversions
- Visualization pipeline components
- CLI command functionality

Sample data for testing is provided in `tests/sample/t4dataset/` with minimal annotation files.