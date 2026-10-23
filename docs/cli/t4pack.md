`t4pack` packs the `.pcd.bin` pointcloud frames of each sensor channel into a single compressed file, `data/<CHANNEL>.pack`.
See [Packed Pointcloud](../schema/data.md#packed-pointcloud) for the format.

```shell
$ t4pack -h

 Usage: t4pack [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v        Show the application version and exit.                                           │
│ --install-completion            Install completion for the current shell.                                        │
│ --show-completion               Show completion for the current shell, to copy it or customize the installation. │
│ --help                -h        Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ pack     Pack .pcd.bin frames of each channel into '<CHANNEL>.pack'.                                             │
│ verify   Verify that each '<CHANNEL>.pack' matches its .pcd.bin frames if they exist.                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Shell Completion

Run the following command to install completion, and reload shell.

```{ .shell .copy }
t4pack --install-completion
```

## Usages

### Pack Pointclouds

```shell
$ t4pack pack -h

 Usage: t4pack pack [OPTIONS] DATA_ROOT

 Pack .pcd.bin frames of each channel into '<CHANNEL>.pack'.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_root      TEXT  Root directory path to the dataset. [required]                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --revision      -rv      TEXT     Specify if you want to pack the specific version.                              │
│ --level         -l       INTEGER  zstd compression level. [default: 19]                                          │
│ --overwrite                       Overwrite existing packs.                                                      │
│ --delete-loose                    Delete .pcd.bin frames after verifying them against the pack.                  │
│ --help          -h                Show this message and exit.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

For example, the following command packs `data/LIDAR_CONCAT/*.pcd.bin` into `data/LIDAR_CONCAT.pack`:

```shell
t4pack pack <DATA_ROOT>
```

Every frame is verified bit-exact against its source before the pack is put in place, so an existing pack is always complete.
If the source values do not fit the compact `uint8`/`int8` columns, e.g. non-integer intensity, every column is stored as `float32` instead.
A channel that is already packed is skipped unless `--overwrite` is specified.
If a channel fails, it is reported as `FAILED` and the other channels are still processed, then the command exits with `1`.

The source `.pcd.bin` files are kept by default. With `--delete-loose`, they are deleted after every frame is verified against the pack again, which also applies to a channel that is already packed:

```shell
t4pack pack <DATA_ROOT> --delete-loose
```

Nothing is deleted from a channel if any of its frames is missing from the pack or differs from it, and files other than `.pcd.bin` are kept.

`t4pack pack` can be run by multiple workers at the same time, even on the same dataset: each worker writes and verifies its own temporary file, and a verified pack is put in place atomically.
`--overwrite` is refused if the existing pack contains frames whose `.pcd.bin` has already been deleted, so those frames are never lost.

### Verify Packs

```shell
$ t4pack verify -h

 Usage: t4pack verify [OPTIONS] DATA_ROOT

 Verify that each '<CHANNEL>.pack' matches its .pcd.bin frames if they exist.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_root      TEXT  Root directory path to the dataset. [required]                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --revision  -rv      TEXT  Specify if you want to verify the specific version.                                   │
│ --help      -h             Show this message and exit.                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Each frame whose `.pcd.bin` still exists is compared bit-exact with the pack, and each frame whose `.pcd.bin` has been deleted is checked to be decodable.
The command exits with `1` if any frame is missing from the pack, differs from its source or is broken.
