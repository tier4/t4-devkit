# T4 devkit

A toolkit to load and operate T4 dataset.

<div align="center">
    <img src="docs/assets/render_scene.gif" width="800" alt="RENDER SAMPLE"/>
</div>

## Getting started

<!-- TODO(ktro2828): 📝 [Dataset Schema](https://tier4.github.io/t4-devkit/schema) | -->

🏠 [Documentation](https://tier4.github.io/t4-devkit/) |
⚙️ [Tutorial](https://tier4.github.io/t4-devkit/tutorials/initialize/) |
🧰 [API Reference](https://tier4.github.io/t4-devkit/apis/tier4/)

### Installation

#### Install via GitHub

Note that the following command installs the latest `main` branch:

```shell
# e.g) with pip
pip install git+https://github.com/tier4/t4-devkit.git
```

By specifying `@<TAG_OR_BRANCH>`, you can install the particular version of `t4-devkit`:

```shell
# e.g) with pip
pip install git+https://github.com/tier4/t4-devkit.git@main
```

#### Install from source

You need to install `uv`. For details, please refer to [OFFICIAL DOCUMENT](https://docs.astral.sh/uv/).

```shell
git clone git@github.com:tier4/t4-devkit.git
cd t4-devkit
uv sync --python 3.10
```

The virtual environment can be activated with:

```shell
source .venv/bin/activate
```

## Feature supports

### Visualization

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
