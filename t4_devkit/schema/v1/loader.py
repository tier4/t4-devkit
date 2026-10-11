from __future__ import annotations

import os.path as osp
from typing import TYPE_CHECKING, Any

from attrs import define, field

from t4_devkit.common.io import load_json

from .convert_v0 import convert_v0
from .manifest import Manifest, load_manifest
from .name import SchemaName
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.schema.tables.base import SchemaTable
    from t4_devkit.typing import PathLike

__all__ = ["T4Tables", "load_dataset"]


@define
class T4Tables:
    """The tables of a loaded dataset, as 1.x records.

    Attributes:
        data_root (str): Dataset root.
        manifest (Manifest | None): The dataset manifest, or None for a 0.x dataset.
        tables (dict[SchemaName, list[SchemaTable]]): Records per table; empty for an absent optional table.
    """

    data_root: str
    manifest: Manifest | None
    tables: dict[SchemaName, list[SchemaTable]]
    _token2idx: dict[SchemaName, dict[str, int]] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self._token2idx = {
            name: {record.token: idx for idx, record in enumerate(records)}
            for name, records in self.tables.items()
        }
        self._fill_shortcuts()

    def get(self, name: str | SchemaName, token: str) -> SchemaTable:
        """Return the record of a table by its token.

        Args:
            name (str | SchemaName): Table name.
            token (str): Record token.

        Returns:
            The record.
        """
        name = SchemaName(name)
        return self.tables[name][self._token2idx[name][token]]

    def _fill_shortcuts(self) -> None:
        """Fill the shortcut fields (`init=False`) of the records, from their links."""
        for record in self.tables[SchemaName.SAMPLE_ANNOTATION]:
            instance = self.get(SchemaName.INSTANCE, record.instance_token)
            record.category_name = self.get(SchemaName.CATEGORY, instance.category_token).name

        for record in self.tables[SchemaName.OBJECT_ANN]:
            record.category_name = self.get(SchemaName.CATEGORY, record.category_token).name

        for record in self.tables[SchemaName.SAMPLE_DATA]:
            sensor = self.get(SchemaName.SENSOR, record.sensor_token)
            record.modality = sensor.modality
            record.channel = sensor.channel
            first = sensor.first_sd_token
            if (
                first is None
                or record.timestamp < self.get(SchemaName.SAMPLE_DATA, first).timestamp
            ):
                sensor.first_sd_token = record.token
            if record.is_key_frame:
                self.get(SchemaName.SAMPLE, record.sample_token).data[sensor.channel] = record.token

        for record in self.tables[SchemaName.SAMPLE_ANNOTATION]:
            self.get(SchemaName.SAMPLE, record.sample_token).ann_3ds.append(record.token)

        for record in self.tables[SchemaName.OBJECT_ANN]:
            sample_data = self.get(SchemaName.SAMPLE_DATA, record.sample_data_token)
            if sample_data.sample_token is not None:
                self.get(SchemaName.SAMPLE, sample_data.sample_token).ann_2ds.append(record.token)


def load_dataset(data_root: PathLike) -> T4Tables:
    """Load a dataset as 1.x records.

    Read the raw table dicts (0.x: converted to 1.0 dicts, best effort) -> build and validate
    the records once.

    Args:
        data_root (PathLike): Dataset root, i.e. the `<DATASET_ID>/<DATASET_VERSION>` directory.

    Returns:
        The loaded tables.

    Raises:
        FileNotFoundError: If `manifest.json` does not list a required table.
    """
    manifest = load_manifest(data_root)
    raw_tables = convert_v0(data_root) if manifest is None else _read_tables(data_root, manifest)
    tables = {
        name: [SCHEMAS.get(name).from_dict(data) for data in records]
        for name, records in raw_tables.items()
    }
    return T4Tables(data_root=str(data_root), manifest=manifest, tables=tables)


def _read_tables(data_root: PathLike, manifest: Manifest) -> dict[SchemaName, list[dict[str, Any]]]:
    """Read the raw table dicts listed in `manifest.json`.

    Args:
        data_root (PathLike): Dataset root.
        manifest (Manifest): The dataset manifest.

    Returns:
        Raw records per table; empty for an absent optional table.

    Raises:
        FileNotFoundError: If `manifest.json` does not list a required table.
    """
    raw_tables: dict[SchemaName, list[dict[str, Any]]] = {}
    for name in SchemaName:
        entry = manifest.tables.get(name.value)
        if entry is None:
            if not name.is_optional():
                raise FileNotFoundError(f"{name.value} is mandatory.")
            raw_tables[name] = []
        else:
            raw_tables[name] = load_json(osp.join(data_root, entry.path))
    return raw_tables
