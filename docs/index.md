# T4 devkit

`t4-devkit` is a toolkit to load and operate T4 dataset.

<div align="center">
    <img src="assets/render_scene.gif" width="800" alt="RENDER SAMPLE"/>
</div>

## Dataset Format

For details of T4 dataset format, please refer to [tier4_perception_dataset/t4_format_3d_detailed.md](https://github.com/tier4/tier4_perception_dataset/blob/main/docs/t4_format_3d_detailed.md).

## Feature supports

### Visualization

| Feature | Task                        | Support |
| :------ | :-------------------------- | :-----: |
| 3D      | 3D Boxes                    |   ✅    |
|         | PointCloud Segmentation     |         |
|         | Raw PointCloud              |   ✅    |
|         | 3D Trajectories             |         |
|         | TF Links                    |   ✅    |
| 2D      | 2D Boxes                    |   ✅    |
|         | Image Segmentation          |   ✅    |
|         | Raw Image                   |   ✅    |
|         | Raw PointCloud on Image     |   ✅    |
| Map     | Vector Map                  |         |
|         | Ego Position on Street View |   ✅    |

### Evaluation

| Feature | Task                    | Support |
| :------ | :---------------------- | :-----: |
| 3D      | 3D Detection            |         |
|         | 3D Tracking             |         |
|         | 3D Motion Prediction    |         |
|         | PointCloud Segmentation |         |
| 2D      | 2D Detection            |         |
|         | 2D Tracking             |         |
|         | Image Segmentation      |         |
|         | Classification          |         |
