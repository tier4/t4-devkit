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
│ --strict              -s             Indicates whether warnings are treated as failures.                              │
│ --fix                 -f             Attempt to fix the issues reported by the sanity check.                          │
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

+-----------+---------+--------+--------+---------+----------+-------+
| DatasetID | Version | Passed | Failed | Skipped | Warnings | Fixed |
+-----------+---------+--------+--------+---------+----------+-------+
| dataset1  |    0    |   49   |   0    |    2    |    3     |   0   |
+-----------+---------+--------+--------+---------+----------+-------+
```

### Exclude Checks

With `-e; --exclude` option enables us to exclude specific checks by specifying the **rule IDs or groups**:

```shell
# Exclude STR001 and all FMT-relevant rules
t4sanity <DATA_ROOT> -e STR001 -e FMT
```

### Strict Mode

Basically, rules whose **severity is WARNING** will be treated as success.

With `-s; --strict` option enables us to treat warnings as failures:

```shell
# Run strict mode
t4sanity <DATA_ROOT> --strict
```

### Fix Issues

With `-f; --fix` option enables to fix issues automatically:

```shell
# Fix issues automatically
t4sanity <DATA_ROOT> --fix

>>>Sanity checking...: 1it [00:00,  9.70it/s]

=== DatasetID: dataset1 ===
  ...
  REC007: --> FIXED ✅
     - All categories either must have an 'index' set or all have a 'null' index.
  ...

+-----------+---------+--------+--------+---------+----------+-------+
| DatasetID | Version | Passed | Failed | Skipped | Warnings | Fixed |
+-----------+---------+--------+--------+---------+----------+-------+
| dataset1  |    0    |   49   |   0    |    2    |    3     |   1   |
+-----------+---------+--------+--------+---------+----------+-------+
```

The generated report contains failure or warning reasons, but it's considered as passed if the fix was successful.

### Exit Status Logic

`t4sanity` CLI returns the exit code based on the following conditions:

| Condition                                                                          | `--strict`        | `--fix` | Exit Code | Notes                                                                     |
| ---------------------------------------------------------------------------------- | ----------------- | ------- | --------- | ------------------------------------------------------------------------- |
| At least one `Severity.ERROR` rule failed                                          | N/A               | `False` | 1         | Always fails the run                                                      |
| At least one `Severity.ERROR` rule failed, but fixed                               | N/A               | `True`  | 0         | Run is considered successful, error reasons are reported and `Fixed=true` |
| At least one `Severity.WARNING` rule failed, no `Severity.ERROR` failed            | `False` (default) | N/A     | 0         | Run is considered successful, warnings are reported                       |
| At least one `Severity.WARNING` rule failed, no `Severity.ERROR` failed            | `True`            | `False` | 1         | Treat warnings as failures; exit with failure                             |
| At least one `Severity.WARNING` rule failed, no `Severity.ERROR` failed, but fixed | `True`            | `True`  | 0         | Run is considered successful, warnings are reported and `Fixed=true`      |
| All rules passed or skipped                                                        | N/A               | N/A     | 0         | Run is considered successful                                              |

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
        "reasons": "<[<Reason1>, <Reason2>, ...]: [str; N] | null>",
        "fixed": "<Fixed: bool>"
    },
  ]
}
```

Here is the description of the JSON format:

- `dataset_id`: The ID of the dataset.
- `version`: The version of the dataset.
- `reports`: An array of rule reports.
  - `id`: The ID of the rule.
  - `name`: The name of the rule.
  - `severity`: How important a rule is.
  - `description`: A description of the rule.
  - `status`: What happened when it ran.
  - `reasons`: An array of reasons for failure or skipped rules, null if passed.
  - `fixed`: Whether the rule was fixed.
