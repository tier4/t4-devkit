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

You need to install `uv`. For details, please refer to [OFFICIAL DOCUMENT](https://docs.astral.sh/uv/).

```shell
git clone git@github.com:tier4/t4-devkit.git
cd t4-devkit
uv sync --python 3.10
```

The virtual environment can be activated with:

```shell
source .venv/bin/activate
```
