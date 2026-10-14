from __future__ import annotations

from functools import cached_property
from pathlib import Path

from attrs import define, field
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from typing_extensions import TYPE_CHECKING, Self

from t4_devkit import DBMetadata
from t4_devkit.schema import SchemaName
from t4_devkit.schema.v1 import MANIFEST_FILENAME, Manifest
from t4_devkit.schema.v1 import SchemaName as V1SchemaName

from .checker import SchemaVersion
from .safety import load_json_safe, load_manifest_safe, load_metadata_safe, save_json_safe

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike


@define(slots=False)
class SanityContext:
    """What the checkers read: the dataset paths, and for 1.0 its manifest and tables, read once.

    Attributes:
        metadata (Maybe[DBMetadata]): Dataset root, ID and version directory.
        checksum (bool): Whether to verify the SHA-256 of the files listed in `manifest.json`.
    """

    metadata: Maybe[DBMetadata]
    checksum: bool = field(default=False, kw_only=True)
    _tables: dict[V1SchemaName, Maybe[list[dict]]] = field(factory=dict, init=False, repr=False)

    @classmethod
    def from_path(
        cls, data_root: PathLike, revision: str | None = None, *, checksum: bool = False
    ) -> Self:
        metadata_result = load_metadata_safe(data_root, revision=revision)
        metadata = metadata_result.unwrap() if is_successful(metadata_result) else None
        return cls(Maybe.from_optional(metadata), checksum=checksum)

    @property
    def data_root(self) -> Maybe[Path]:
        """Return the path to dataset root directory."""
        return self.metadata.map(lambda m: Path(m.data_root))

    @property
    def dataset_id(self) -> Maybe[str]:
        """Return the dataset ID."""
        return self.metadata.map(lambda m: m.dataset_id)

    @property
    def version(self) -> Maybe[str]:
        """Return the dataset version."""
        return self.metadata.bind_optional(lambda m: m.version)

    @property
    def annotation_dir(self) -> Maybe[Path]:
        """Return the path to annotation directory, which is 'annotation'."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("annotation"))

    @property
    def sensor_data_dir(self) -> Maybe[Path]:
        """Return the path to sensor data directory, which is 'data'."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("data"))

    @property
    def map_dir(self) -> Maybe[Path]:
        """Return the path to map directory, which is 'map'."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("map"))

    @property
    def bag_dir(self) -> Maybe[Path]:
        """Return the path to bag directory, which is 'input_bag'."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("input_bag"))

    @property
    def status_json(self) -> Maybe[Path]:
        """Return the path to status JSON file, which is 'status.json'."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("status.json"))

    @property
    def manifest_json(self) -> Maybe[Path]:
        """Return the path to `manifest.json`."""
        return self.metadata.map(lambda m: Path(m.data_root).joinpath(MANIFEST_FILENAME))

    @property
    def schema_version(self) -> SchemaVersion:
        """Return 1.0 if `manifest.json` exists at the dataset root, 0.x otherwise."""
        match self.manifest_json:
            case Some(x) if x.exists():
                return SchemaVersion.V1
        return SchemaVersion.V0

    @cached_property
    def raw_manifest(self) -> Maybe[dict]:
        """Return `manifest.json` as read, or Nothing if it cannot be read."""
        match self.manifest_json:
            case Some(x) if x.exists():
                result = load_json_safe(x)
                return Some(result.unwrap()) if is_successful(result) else Nothing
        return Nothing

    @cached_property
    def manifest(self) -> Maybe[Manifest]:
        """Return the manifest, or Nothing if it cannot be read or is not valid."""
        return self.raw_manifest.bind(
            lambda data: Maybe.from_optional(load_manifest_safe(data).value_or(None))
        )

    def to_table_file(self, table: V1SchemaName) -> Maybe[Path]:
        """Return the path of a 1.0 table file listed in `manifest.json`, or Nothing if unlisted."""
        return self.manifest.bind(
            lambda m: Maybe.from_optional(m.tables.get(table.value)).map(
                lambda entry: Path(self.data_root.unwrap()).joinpath(entry.path)
            )
        )

    def load_table(self, table: V1SchemaName) -> Maybe[list[dict]]:
        """Return the raw records of a 1.0 table as read (read once), or Nothing if unlisted or
        unreadable."""
        if table not in self._tables:
            self._tables[table] = self.to_table_file(table).bind(
                lambda path: Maybe.from_optional(load_json_safe(path).value_or(None))
            )
        return self._tables[table]

    def to_schema_file(self, schema: SchemaName) -> Maybe[Path]:
        """Convert schema name to file path, which is <data_root>/annotation/<schema_name>.json."""
        return self.annotation_dir.map(lambda ann: ann.joinpath(schema.filename))

    def save_records(self, schema: SchemaName, records: list[dict]) -> bool:
        """Save schema data to file."""
        match self.to_schema_file(schema):
            case Some(filepath):
                result = save_json_safe(records, filepath)
                if is_successful(result):
                    return True
                else:
                    print(f"Error saving schema: {result.failure()}")
                    return False
        return False
