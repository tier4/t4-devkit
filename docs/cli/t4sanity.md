`t4sanity` performs sanity checks on T4 datasets, reporting any issues in a structured format.
It checks the dataset directories and versions, tries to load them using the `Tier4` library, and reports any exceptions or warnings.

```shell
$ t4sanity -h

 Usage: t4sanity [OPTIONS] DB_PARENT

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    db_parent      TEXT  Path to parent directory of the databases. [required]                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v             Show the application version and exit.                                           │
│ --output              -o       TEXT  Path to output JSON file.                                                        │
│ --revision            -rv      TEXT  Specify if you want to check the specific version.                               │
│ --exclude             -e       TEXT  Exclude specific rules or rule groups.                                           │
│ --include-warning     -iw            Indicates whether to report any warnings.                                        │
│ --detail              -d             Indicates whether to display detailed reports.                                   │
│ --install-completion                 Install completion for the current shell.                                        │
│ --show-completion                    Show completion for the current shell, to copy it or customize the installation. │
│ --help                -h             Show this message and exit.                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Shell Completion

Run the following command to install completion, and reload shell.

```{ .shell .copy }
t4sanity --install-completion
```

## Usages

As an example, we have the following the dataset structure:

```shell
<DB_PARENT>
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

Then, you can run sanity checks with `t4sanity <DB_PARENT>`:

```shell
$ t4sanity <DB_PARENT>

>>>Sanity checking...: 1it [00:00,  9.70it/s]

============================= Summary =============================
+-----------+---------+---------+-------+---------+----------+-------+
| DatasetID | Version | Status  | Rules | Success | Failures | Skips |
+-----------+---------+---------+-------+---------+----------+-------+
| dataset1  |    0    | SUCCESS |  44   |   44    |    0     |   0   |
+-----------+---------+---------+-------+---------+----------+-------+
| dataset2  |    0    | SUCCESS |  44   |   44    |    0     |   0   |
+-----------+---------+---------+-------+---------+----------+-------+
```

Also, `-d; --detail` option helps us to display detailed information about each check:

```shell
$ t4sanity <DB_PARENT> -d

>>>Sanity checking...: 1it [00:00,  9.70it/s]

=== DatasetID: dataset1 ===
  STR001: ✅
  STR002: ✅
  STR003: ✅
  STR004: ✅
  STR005: ✅
  STR006: ✅
  STR007: ✅
  STR008: ✅
  ...

============================= Summary =============================
+-----------+---------+---------+-------+---------+----------+-------+
| DatasetID | Version | Status  | Rules | Success | Failures | Skips |
+-----------+---------+---------+-------+---------+----------+-------+
| dataset1  |    0    | SUCCESS |  44   |   44    |    0     |   0   |
+-----------+---------+---------+-------+---------+----------+-------+
| dataset2  |    0    | SUCCESS |  44   |   44    |    0     |   0   |
+-----------+---------+---------+-------+---------+----------+-------+
```

### Dump Results as JSON

To dump results into JSON, use the `-o; --output` option:

```shell
t4sanity <DB_PARENT> -o results.json
```

Then a JSON file named `results.json` will be generated as follows:

```json
[
  {
    "dataset_id": "<DatasetID: str>",
    "version": <Version: int>,
    "reports": {
      "<RuleID: str>": {
          "id": "<RuleID: str>",
          "name": "<RuleName: str>",
          "description": "<Description: str>",
          "status": "<SUCCESS/FAILURE/SKIPPED: str>",
          "reasons": "<[<Reason1>, <Reason2>, ...]: [str; N] | null>" // Failure or skipped reasons, null if success
      },
    }
  }
]
```

### Exclude Checks

With `-e; --excludes` option enables us to exclude specific checks by specifying the **rule IDs or groups**:

```shell
t4sanity <DB_PARENT> -e STR001 -e FMT
```
