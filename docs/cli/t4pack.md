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
│ verify   Verify that each '<CHANNEL>.pack' matches its .pcd.bin frames.                                          │
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
│ --revision   -rv      TEXT     Specify if you want to pack the specific version.                                 │
│ --level      -l       INTEGER  zstd compression level. [default: 19]                                             │
│ --overwrite                    Overwrite existing packs.                                                         │
│ --help       -h                Show this message and exit.                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

For example, the following command packs `data/LIDAR_CONCAT/*.pcd.bin` into `data/LIDAR_CONCAT.pack`:

```shell
t4pack pack <DATA_ROOT>
```

Every frame is verified bit-exact against its source before the pack is put in place, so an existing pack is always complete.
The source `.pcd.bin` files are kept.
A channel that is already packed is skipped unless `--overwrite` is specified.

### Verify Packs

```shell
$ t4pack verify -h

 Usage: t4pack verify [OPTIONS] DATA_ROOT

 Verify that each '<CHANNEL>.pack' matches its .pcd.bin frames.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_root      TEXT  Root directory path to the dataset. [required]                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --revision  -rv      TEXT  Specify if you want to verify the specific version.                                   │
│ --help      -h             Show this message and exit.                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

The command exits with `1` if any frame is missing from the pack or differs from its source.
