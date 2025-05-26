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
│ --ignore-warning      -iw        Indicates whether to ignore warnings                                                │
│ --install-completion             Install completion for the current shell.                                           │
│ --show-completion                Show completion for the current shell, to copy it or customize the installation.    │
│ --help                -h         Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
