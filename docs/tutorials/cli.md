## Command Line Tools

### CLI Support

Following command line tools are supported:

- `t4viz`: Visualize T4 dataset features.

To enable shell completion, please run following commands:

### Shell Completion

#### Bash

```shell
_T4VIZ_COMPLETE=bash_source t4viz > $HOME/.t4viz-complete.bash

echo "source $HOME/.t4viz-complete.bash" >> ~/.bashrc
```

#### Fish

```shell
_T4VIZ_COMPLETE=fish_source t4viz > $HOME/.config/fish/completions/t4viz.fish
```

### `t4viz`

#### Visualize a Scene

This command performs the same behavior with [`Tier4.render_scene(...)`](./render.md#rendering-scene).

```shell
t4viz scene <DATA_ROOT> [OPTIONS]
```

Arguments

- `<DATA_ROOT>`: Root directory path to T4 dataset.
- `-f, --future <SECONDS>`: Future time seconds.
- `-o, --output <OUTPUT_DIR>`: Directory path to save recording `.rrd` file.
- `--no-show`: Indicates whether not to show viewer.

#### Visualize Specific Instance(s)

This command performs the same behavior with [`Tier4.render_instance(...)`](./render.md#rendering-instances).

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN> [OPTIONS]
```

You can also specify multiple instance tokens:

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN1> <INSTANCE_TOKEN2> ... [OPTIONS]
```

Arguments

- `<DATA_ROOT>`: Root directory path to T4 dataset.
- `<INSTANCE_TOKEN>`: Unique identifier token(s) of the instance record(s).
- `-f, --future <SECONDS>`: Future time seconds.
- `-o, --output <OUTPUT_DIR>`: Directory path to save recording `.rrd` file.
- `--no-show`: Indicates whether not to show viewer.

#### Visualize PointCloud

This command performs the same behavior with [`Tier4.render_pointcloud(...)`](./render.md#rendering-pointcloud).

```shell
t4viz pointcloud <DATA_ROOT> [OPTIONS]
```

Arguments

- `<DATA_ROOT>`: Root directory path to T4 dataset.
- `<INSTANCE_TOKEN>`: Unique identifier token of an instance record.
- `-d, --distortion`: Indicates whether not to ignore camera distortion.
- `-o, --output <OUTPUT_DIR>`: Directory path to save recording `.rrd` file.
- `--no-show`: Indicates whether not to show viewer.
