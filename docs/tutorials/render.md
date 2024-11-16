## Rendering with `Tier4`

If you want to visualize annotation results, `Tier4` supports some rendering methods as below.

### Rendering Scene

```python
>>> scene_token = t4.scene[0].token
>>> t4.render_scene(scene_token)
```

![Render Scene GIF](../assets/render_scene.gif)

### Rendering Instance

```python
>>> instance_token = t4.instance[0].token
>>> t4.render_instance(instance_token)
```

![Render Instance GIF](../assets/render_instance.gif)

### Rendering PointCloud

```python
>>> scene_token = t4.scene[0].token
>>> t4.render_pointcloud(scene_token)
```

![Render PointCloud GIF](../assets/render_pointcloud.gif)

<!-- prettier-ignore-start -->
!!! NOTE
    In case of you want to ignore camera distortion, please specify `ignore_distortion=True`.

    <!-- markdownlint-disable MD046 -->
    ```python
    >>> t4.render_pointcloud(scene_token, ignore_distortion=True)
    ```
<!-- prettier-ignore-end -->

### Save Recording

You can save the rendering result as follows:

```python
>>> t4.render_scene(scene_token, save_dir=<DIR_TO_SAVE>)
```

If you don't want to spawn the viewer, please specify `show=False` as below:

```python
>>> t4.render_scene(scene_token, save_dir=<DIR_TO_SAVE>, show=False)
```

## Rendering with `Tier4Viewer`

If you want to visualize your components, such as boxes that your ML-model estimated, `Tier4Viewer` allows you to visualize these components.  
For details, please refer to the API references.

```python
>>> from t4_devkit.viewer import Tier4Viewer
# You need to specify `cameras` if you want to 2D spaces
>>> viewer = Tier4Viewer(app_id, cameras=<CAMERA_NAMES:[str;N]>)
# Rendering 3D boxes
>>> viewer.render_box3ds(seconds, box3ds)
# Rendering 2D boxes
>>> viewer.render_box2ds(seconds, box2ds)
```
