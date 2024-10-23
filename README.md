# T4 devkit

A toolkit to load and operate T4 dataset.

<div align="center">
    <img src="docs/assets/render_scene.gif" width="800" alt="RENDER SAMPLE"/>
</div>

## Getting started

📘 [Documentation](https://tier4.github.io/t4-devkit/) |
⚙️ [Tutorial](https://tier4.github.io/t4-devkit/tutorials/initialize/) |
🧰 [API Reference](https://tier4.github.io/t4-devkit/apis/tier4/)

### Installation

#### Install via GitHub

```shell
# e.g) with poetry
poetry add git+https://github.com/tier4/t4-devkit.git
```

#### Install from source

```shell
git clone git@github.com:tier4/t4-devkit.git
cd t4-devkit
poetry install
```

## Feature supports

### Visualization

| Feature | Task                    | Support |
| :------ | :---------------------- | :-----: |
| 3D      | 3D Boxes                |   ✅    |
|         | PointCloud Segmentation |         |
|         | Raw PointCloud          |   ✅    |
|         | 3D Trajectories         |         |
|         | TF Links                |   ✅    |
|         | Vector Map              |         |
| 2D      | 2D Boxes                |   ✅    |
|         | Image Segmentation      |   ✅    |
|         | Raw Image               |   ✅    |
|         | Raw PointCloud on Image |   ✅    |

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
