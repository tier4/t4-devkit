## Install via GitHub

Note that the following command installs the latest `main` branch:

```shell
# e.g) with pip
pip install git+https://github.com/tier4/t4-devkit.git
```

By specifying `@<TAG_OR_BRANCH>`, you can install the particular version of `t4-devkit`:

```shell
# e.g) with pip
pip install git+https://github.com/tier4/t4-devkit.git@main
```

## Install from source

```shell
git clone git@github.com:tier4/t4-devkit.git
cd t4-devkit
uv venv --python 3.10
uv sync --all-extras
```
