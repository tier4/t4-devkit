`t4ann` manages annotation records in a T4 dataset from the command line.

    $ t4ann -h

     Usage: t4ann [OPTIONS] COMMAND [ARGS]...

    ╭─ Options ────────────────────────────────────────────────────────────────╮
    │ --version             -v        Show the application version and exit.   │
    │ --install-completion            Install completion for the current shell.│
    │ --show-completion               Show completion for the current shell.   │
    │ --help                -h        Show this message and exit.              │
    ╰──────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────╮
    │ clear  Clear the annotation records                                      │
    ╰──────────────────────────────────────────────────────────────────────────╯

## Shell Completion

Run the following command to install completion, and reload shell.

    ```shell
    t4ann --install-completion
    ```

## Usages

### Clear Annotation Records

`clear` replaces annotation-related tables, including category, attribute, instance, 3D/2D
annotations, keypoints, and segmentation records, with empty JSON arrays. Sensor data and
`visibility.json` are preserved.

For options, run `t4ann clear -h`.

    ```shell
    t4ann clear <DATA_ROOT>
    ```

!!! warning

    This command overwrites annotation tables. Referenced files such as lidar segmentation
    binaries and statistics in `status.json` are not removed or updated.

### Create a New Version

Use `--new-version; -n` to preserve the source dataset and clear annotations in a new numeric
version.

    ```shell
    t4ann clear <DATA_ROOT> --new-version
    ```

The version number is incremented from the highest existing numeric version. Version `0` is
created when the dataset has no version directories.
