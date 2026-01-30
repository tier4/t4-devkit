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

## Shell Completion

Run the following command to install completion, and reload shell.

```{ .shell .copy }
t4viz --install-completion
```

## Usages

### Scene

This command performs the same behavior with [`Tier4.render_scene(...)`](../tutorials/render.md#rendering-scene).

For options, run `t4viz scene -h`.

```shell
t4viz scene <DATA_ROOT> [OPTIONS]
```

### Specific Instance(s)

This command performs the same behavior with [`Tier4.render_instance(...)`](../tutorials/render.md#rendering-instances).

For options, run `t4viz instance -h`.

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN> [OPTIONS]
```

You can also specify multiple instance tokens:

```shell
t4viz instance <DATA_ROOT> <INSTANCE_TOKEN1> <INSTANCE_TOKEN2> ... [OPTIONS]
```

### PointCloud

This command performs the same behavior with [`Tier4.render_pointcloud(...)`](../tutorials/render.md#rendering-pointcloud).

For options, run `t4viz pointcloud -h`.

```shell
t4viz pointcloud <DATA_ROOT> [OPTIONS]
```

### Future Trajectories

`scene` and `instance` commands support visualizing future trajectories for each object.

By specifying `-f [--future]` option, you can render them in the particular time length:

```shell
t4viz <COMMAND> ... -f <FUTURE_LENGTH[s]>
```

### Save Recording as `.rrd`

You can save visualized recording with `-o [--output]` option as follows:

```shell
t4viz <COMMAND> ... -o <OUTPUT_DIR>
```

Note that if you specify `--output` option, viewer will not be spawned.
