# `t4-devkit`

`t4-devkit` is a toolkit to load and operate T4 dataset.

<div align="center">
    <img src="assets/render_scene.gif" width="800" alt="RENDER SAMPLE"/>
</div>

## Feature supports

### Visualization

`t4-devkit` provides a set of visualization tools to help you understand the data.

More details, please refer to [`t4viz` CLI](./cli/t4viz.md) or [API usage](./tutorials/render.md).

| Feature | Task                        | Support |
| :------ | :-------------------------- | :-----: |
| 3D      | 3D Boxes                    |   ✅    |
|         | PointCloud Segmentation     |         |
|         | Raw PointCloud              |   ✅    |
|         | 3D Trajectories             |   ✅    |
|         | TF Links                    |   ✅    |
| 2D      | 2D Boxes                    |   ✅    |
|         | Image Segmentation          |   ✅    |
|         | Raw Image                   |   ✅    |
|         | Raw PointCloud on Image     |   ✅    |
| Map     | Vector Map                  |   ✅    |
|         | Ego Position on Street View |   ✅    |

### Sanity Checks

`t4-devkit` provides a set of sanity checks to ensure the correctness of the data.

More details, please refer to [`t4sanity` CLI](./cli/t4sanity.md) or [API usage](./tutorials/sanity.md).
