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
│ --output              -o    TEXT Path to output JSON file. [default: None]                                           │
│ --revision            -rv   TEXT Specify if you want to load the specific version. [default: None]                   │
│ --include-warning     -iw        Indicates whether to report any warnings.                                           │
│ --install-completion             Install completion for the current shell.                                           │
│ --show-completion                Show completion for the current shell, to copy it or customize the installation.    │
│ --help                -h         Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Shell Completion

Run the following command to install completion, and reload shell.

```{ .shell .copy }
t4sanity --install-completion
```

## Usages

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

Then, you can run sanity checks with `t4sanity <DATA_ROOT>`:

```shell
>>>Sanity checking...: 1it [00:00,  9.70it/s]
✅ No exceptions occurred!!
```

### Exclude Warnings

To run sanity check ignoring warnings, providing the path to the parent directory of the datasets:

```shell
$ t4sanity <DATA_ROOT>

>>>Sanity checking...: 2it [00:00, 18.69it/s]
⚠️  Encountered some exceptions!!
+-----------+---------+--------+------------------------------------------------------------------------------------------------+
| DatasetID | Version | Status |                                            Message                                             |
+-----------+---------+--------+------------------------------------------------------------------------------------------------+
| dataset1  |    2    | ERROR  | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1532, 198, 1440, 265) |
| dataset2  |    1    |   OK   |                                                                                                |
+-----------+---------+--------+------------------------------------------------------------------------------------------------+
```

### Include Warnings

To run sanity check and report any warnings, use the `-iw; --include-warning` option:

```shell
$ t4sanity <DATA_ROOT> -iw

>>>Sanity checking...: 2it [00:00, 21.54it/s]
⚠️  Encountered some exceptions!!
+-----------+---------+---------+------------------------------------------------------------------------------------------------+
| DatasetID | Version | Status  |                                            Message                                             |
+-----------+---------+---------+------------------------------------------------------------------------------------------------+
| dataset1  |    2    |  ERROR  | bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1532, 198, 1440, 265) |
| dataset2  |    1    | WARNING |           Category token is empty for surface ann: 0c15d9c143fb2723c16ac7e0c735b0a8            |
+-----------+---------+---------+------------------------------------------------------------------------------------------------+
```

### Dump Results as JSON

To dump results into JSON, use the `-o; --output` option:

```shell
$ t4sanity <DATA_ROOT> -o results.json

>>>Sanity checking...: 2it [00:00, 21.54it/s]
...
```

Then a JSON file named `results.json` will be generated:

```json
[
  {
    "dataset_id": "dataset1",
    "version": 2,
    "status": "ERROR",
    "message": "bbox must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: (1532, 198, 1440, 265)"
  },
  {
    "dataset_id": "dataset2",
    "version": 1,
    "status": "WARNING",
    "message": "Category token is empty for surface ann: 0c15d9c143fb2723c16ac7e0c735b0a8"
  }
]
```
