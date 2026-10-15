`t4migrate` migrates a 0.x dataset to a new [1.0](../schema/v1/index.md) dataset. The 0.x dataset is only read.

```shell
$ t4migrate -h

 Usage: t4migrate [OPTIONS] {data_root} {output_dir}

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_root       <str>  0.x dataset: the <DATASET_ID>/<VERSION> directory with annotation/. [required]           │
│ *    output_dir      <str>  Parent directory: the dataset goes to <OUTPUT_DIR>/<DATASET_ID>/<DATASET_VERSION>.       │
│                             [required]                                                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│    --version             -v             Show the application version and exit.                                       │
│ *  --dataset-version     -d      <int>  Version of the 1.0 dataset (given by Web.Auto). [required]                   │
│    --dataset-id                  <str>  Dataset ID, if not the 0.x dataset's.                                        │
│    --keep-images                        Copy camera images as they are instead of encoding one AV1 video per         │
│                                         channel.                                                                     │
│    --help                -h             Show this message and exit.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Usage

```shell
t4migrate <0.x DATASET_ID>/<VERSION> <OUTPUT_DIR> --dataset-version <DATASET_VERSION>
```

This writes `<OUTPUT_DIR>/<DATASET_ID>/<DATASET_VERSION>`, prints the migration notes, and runs [`t4sanity`](./t4sanity.md) on the result. It exits with `1` if a sanity rule fails.

The dataset version is given by the caller: Web.Auto assigns it when the new version is uploaded. An existing output folder is never overwritten.

## What Changes

- Tables are converted as described in [Loading 0.x Datasets](../schema/v1/index.md#loading-0x-datasets).
- Each LiDAR channel becomes one Parquet file, one row group per frame:
  - fields get their 1.0 types (e.g. `intensity` uint8) when every value fits; otherwise they keep their 0.x type, with a warning and a migration note;
  - a ring (`channel`) of `-1` on every point (not recorded) is dropped, with a note;
  - `.info` files become the `source_index` / `source_timestamp` columns;
  - lidarseg becomes the `label` / `instance` columns (`instance` is `0`: 0.x labels are semantic only). Category `0` must be `unpainted`.
- Each camera channel becomes one AV1 video, frames in timestamp order (or the images are copied with `--keep-images`). Frames with `is_valid: false` are encoded as they are.
- `map/` and `input_bag/` are copied as they are.
- `manifest.json` has `migrated_from_schema_version: "0.x"` and the migration notes. Provenance that 0.x does not store (Web.Auto IDs, topics) is empty, for backfilling.
