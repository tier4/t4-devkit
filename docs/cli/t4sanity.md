`t4sanity` performs sanity checks on T4 datasets, reporting any issues regarding the [dataset requirements](../schema/requirement.md).

```shell
$ t4sanity -h

 Usage: t4sanity [OPTIONS] DB_PARENT

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    data_root      TEXT  Path to root directory of a dataset. [default: None] [required]                             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -v             Show the application version and exit.                                           │
│ --output              -o       TEXT  Path to output JSON file. [default: None]                                        │
│ --revision            -rv      TEXT  Specify if you want to check the specific version. [default: None]               │
│ --exclude             -e       TEXT  Exclude specific rules or rule groups. [default: None]                           │
│ --include-warning     -iw            Indicates whether to report any warnings.                                        │
│ --strict              -s             Indicates whether warnings are treated as failures.                              │
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
<DATA_ROOT; (DATASET ID)>
├── <VERSION>
│    ├── annotation
│    ├── data
|    ...
```

Then, you can run sanity checks with `t4sanity <DATA_ROOT>`:

```shell
$ t4sanity <DATA_ROOT>

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

+-----------+---------+--------+--------+---------+----------+
| DatasetID | Version | Passed | Failed | Skipped | Warnings |
+-----------+---------+--------+--------+---------+----------+
| dataset1  |         |   49   |   0    |    2    |    3     |
+-----------+---------+--------+--------+---------+----------+
```

### Dump Results as JSON

To dump results into JSON, use the `-o; --output` option:

```shell
t4sanity <DATA_ROOT> -o result.json
```

Then a JSON file named `result.json` will be generated as follows:

```json
{
  "dataset_id": "<DatasetID: str>",
  "version": <Version: int>,
  "reports": [
    {
        "id": "<RuleID: str>",
        "name": "<RuleName: str>",
        "severity": "<WARNING/ERROR: str>",
        "description": "<Description: str>",
        "status": "<PASSED/FAILED/SKIPPED: str>",
        "reasons": "<[<Reason1>, <Reason2>, ...]: [str; N] | null>" // Failed or skipped reasons, null if passed
    },
  ]
}
```

### Exclude Checks

With `-e; --excludes` option enables us to exclude specific checks by specifying the **rule IDs or groups**:

```shell
# Exclude STR001 and all FMT-relevant rules
t4sanity <DATA_ROOT> -e STR001 -e FMT
```

### Strict Mode

Basically, rules whose **severity is WARNING** will be treated as success.

With `-s; --strict` option enables us to treat warnings as failures:

```shell
# Run strict mode
t4sanity <DATA_ROOT> -s
```
