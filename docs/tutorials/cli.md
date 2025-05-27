## Command Line Tools

### CLI Support

Following command line tools are supported:

- `t4viz`: Visualize T4 dataset features.
- `t4sanity`: Sanity checker of T4 datasets.

### `t4viz`

`t4viz` performs visualizing particular dataset attributes from command line.

```shell
$ t4viz -h

 Usage: t4viz [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v        Show the application version and exit.                                           │
│ --install-completion            Install completion for the current shell.                                        │
│ --show-completion               Show completion for the current shell, to copy it or customize the installation. │
│ --help                -h        Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ scene        Visualize a specific scene.                                                                         │
│ instance     Visualize a particular instance in the corresponding scene.                                         │
│ pointcloud   Visualize pointcloud in the corresponding scene.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Shell Completion

Run the following command to install completion, and reload shell.

```shell
t4viz --install-completion
```

#### Visualize a Scene

This command performs the same behavior with [`Tier4.render_scene(...)`](./render.md#rendering-scene).

For options, run `t4viz scene -h`.

```shell
t4viz scene <DATA_ROOT> [OPTIONS]
```

#### Visualize Specific Instance(s)

This command performs the same behavior with [`Tier4.render_instance(...)`](./render.md#rendering-instances).

For options, run `t4viz instance -h`.

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN> [OPTIONS]
```

You can also specify multiple instance tokens:

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN1> <INSTANCE_TOKEN2> ... [OPTIONS]
```

#### Visualize PointCloud

This command performs the same behavior with [`Tier4.render_pointcloud(...)`](./render.md#rendering-pointcloud).

For options, run `t4viz pointcloud -h`.

```shell
t4viz pointcloud <DATA_ROOT> [OPTIONS]
```

#### Visualize Trajectories

`scene` and `instance` commands support visualizing future trajectories for each object.

By specifying `-f [--future]` option, you can render them in the particular time length:

```shell
t4viz <COMMAND> ... -f <FUTURE_LENGTH[s]>
```

#### Save Recording as `.rrd`

You can save visualized recording with `-o [--output]` option as follows:

```shell
t4viz <COMMAND> ... -o <OUTPUT_DIR>
```

Note that if you specify `--output` option, viewer will not be spawned.

### `t4sanity`

`t4sanity` performs sanity checks on T4 datasets, reporting any issues in a structured format.
It checks the dataset directories and versions, tries to load them using the `Tier4` library, and reports any exceptions or warnings.

```shell
$ t4sanity -h

 Usage: t4sanity [OPTIONS] DB_PARENT

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    db_parent      TEXT  Path to parent directory of the databases [default: None] [required]                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v         Show the application version and exit.                                              │
│ --include-warning     -iw        Indicates whether to report any warnings.                                           │
│ --install-completion             Install completion for the current shell.                                           │
│ --show-completion                Show completion for the current shell, to copy it or customize the installation.    │
│ --help                -h         Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Examples

As an example, we have the following the dataset structure:

```shell
<DATA_ROOT>
├── dataset1
│   └── <VERSION>
│       ├── annotation
│       ├── data
|       ...
├── dataset2
│   ├── annotation
│   ├── data
|   ...
...
```

To run sanity check ignoring warnings, providing the path to the parent directory of the datasets:

```shell
$ t4sanity <DATA_ROOT>

>>> Sanity checking...: 97it [00:03, 26.60it/s]
+--------------------------------------+---------+------------------------------------------------------------------------------------------------+
|              DatasetID               | Version |                                            Message                                             |
+--------------------------------------+---------+------------------------------------------------------------------------------------------------+
| 96200480-ae59-44cb-9e4e-dd9021e250e8 |    2    | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1671, 198, 1440, 229) |
| ca346afb-ea1a-4c5c-8117-544bd9ff6aca |    2    | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1793, 99, 1440, 222)  |
...
```

To run sanity check and report any warnings, use the `-iw; --include-warning` option:

```shell
$ t4sanity <DATA_ROOT> -iw

>>> Sanity checking...: 97it [00:03, 29.31it/s]
+--------------------------------------+---------+------------------------------------------------------------------------------------------------+
|              DatasetID               | Version |                                            Message                                             |
+--------------------------------------+---------+------------------------------------------------------------------------------------------------+
| 96200480-ae59-44cb-9e4e-dd9021e250e8 |    2    | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1671, 198, 1440, 229) |
| ca346afb-ea1a-4c5c-8117-544bd9ff6aca |    2    | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1793, 99, 1440, 222)  |
| ed96b707-e7f4-4a71-9e6b-571ffd56c4c4 |    2    |        level: Not available is not supported, Visibility.UNAVAILABLE will be assigned.         |
...
```
