# Sensor Data 1.0

Each sensor channel is stored as a single file, `data/<CHANNEL>/<CHANNEL>.<FORMAT>`. A frame is addressed by `sample_data.filename` (the file) and `sample_data.frame_index` (the frame inside it), starting at 0.

How the file is written is described on the channel's `sensor` row (`camera.video` or `lidar.container`, see [Schema Tables](./table.md#sensor)).

## Camera

One intra-only AV1 video per channel:

```shell
data/
└── CAM_FRONT/
    └── CAM_FRONT.mp4
```

| Setting         | Value                                                              |
| --------------- | ------------------------------------------------------------------ |
| Container       | MP4                                                                |
| Codec           | AV1, encoded with SVT-AV1 (preset 6, CRF 26)                       |
| Frame types     | Intra-only: every frame is a keyframe (`-g 1`)                     |
| Pixel format    | `yuv420p`, full range, BT.601                                      |
| Track timescale | Equal to the frame rate, so a frame's pts equals its `frame_index` |

Because every frame is a keyframe, any frame can be decoded without decoding its neighbours. Readers seek by `frame_index`.

Datasets migrated from 0.x without re-encoding keep one image file per frame (`.jpg` or `.png`). In that case `sensor.camera.video` is `null` and `sample_data.frame_index` is `null`.

## LiDAR

One Parquet file per channel, with one row group per frame:

```shell
data/
└── LIDAR_CONCAT/
    └── LIDAR_CONCAT.parquet
```

- Columns are the point fields listed in `sensor.lidar.fields`, in that order, e.g. `x, y, z, intensity, ring`.
- Each row is one point. Row group `frame_index` holds all points of that frame.
- Compression is lossless (zstd), so values are bit-exact.
- Frame of reference is given in `sensor.lidar.frame_id` (`base_link` by default).

### Point-wise Labels

When `manifest.json` lists `segmentation3d` in `capabilities.tasks`, the LiDAR file has two extra columns for panoptic labels, listed in `sensor.lidar.fields` like any other field:

| Column     | Type    | Value                                                                                                  |
| ---------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `label`    | `uint8` | [`category.index`](./table.md#category) of the point's category; `0` for unpainted points              |
| `instance` | `int16` | [`instance.instance_index`](./table.md#instance) of the point's object; `-1` for points with no object |

Each column reserves one value:

- `label` `0` is the `unpainted` category: points the annotator did not label. When point-wise labels are present, `category.json` has a category named `unpainted` with `index` `0`.
- `instance` `-1` means no object: points of categories without `is_thing` (road, vegetation) and unpainted points. `instance_index` runs from `0` to `32767`.

Labeled frames have a value for every point. Frames without labels (for example, non-key frames) have `null` in both columns for every point, because a Parquet file has the same columns in every frame. Readers leave out a column that is `null` for the whole frame.

This replaces the `lidarseg` table and the `lidarseg/` folder of 0.x.

0.x datasets loaded without migration keep one `.pcd.bin` or `.pcd` file per frame, as described in [Sensor Data](../data.md). In that case `lidar.container.format` is `bin` or `pcd` and `sample_data.frame_index` is `null`.

## Radar

Radar is not defined in 1.0.
