from __future__ import annotations

from functools import cached_property
from pathlib import Path

from attrs import define, field
from returns.converters import result_to_maybe
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import safe
from typing_extensions import TYPE_CHECKING, Self

from t4_devkit import DBMetadata
from t4_devkit.common.io import file_sha256
from t4_devkit.lanelet import LaneletParser
from t4_devkit.schema import SchemaName
from t4_devkit.schema.v1 import MANIFEST_FILENAME, SCHEMAS, Manifest
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
    _records: dict[V1SchemaName, Maybe[list]] = field(factory=dict, init=False, repr=False)

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
                return result_to_maybe(load_json_safe(x))
        return Nothing

    @cached_property
    def manifest(self) -> Maybe[Manifest]:
        """Return the manifest, or Nothing if it cannot be read or is not valid."""
        match self.raw_manifest:
            case Some(data):
                return result_to_maybe(load_manifest_safe(data))
        return Nothing

    def to_table_file(self, table: V1SchemaName) -> Maybe[Path]:
        """Return the path of a 1.0 table file listed in `manifest.json`, or Nothing if unlisted."""
        match self.manifest, self.data_root:
            case Some(manifest), Some(data_root) if table.value in manifest.tables:
                return Some(data_root.joinpath(manifest.tables[table.value].path))
        return Nothing

    def load_table(self, table: V1SchemaName) -> Maybe[list[dict]]:
        """Return the raw records of a 1.0 table as read (read once), or Nothing if unlisted or
        unreadable."""
        if table not in self._tables:
            match self.to_table_file(table):
                case Some(path):
                    self._tables[table] = result_to_maybe(load_json_safe(path))
                case _:
                    self._tables[table] = Nothing
        return self._tables[table]

    def load_records(self, table: V1SchemaName) -> Maybe[list]:
        """Return the 1.0 records of a table (built once): empty for an unlisted optional table,
        Nothing if the table is required and unlisted, unreadable, or has an invalid record
        (reported by STR014 and the format rules)."""
        if table not in self._records:
            self._records[table] = self._build_records(table)
        return self._records[table]

    @cached_property
    def lanelet_map(self) -> Maybe[LaneletParser]:
        """Return the lanelet2 map of the dataset (read once): the file of the first `Map`
        record, or Nothing if there is none or it cannot be read."""
        match self.load_records(V1SchemaName.MAP), self.data_root:
            case Some([map_record, *_]), Some(data_root):
                return result_to_maybe(_parse_lanelet_safe(data_root.joinpath(map_record.filename)))
        return Nothing

    def save_table(self, table: V1SchemaName, records: list[dict]) -> bool:
        """Save the raw records of a 1.0 table, and its new SHA-256 in `manifest.json`.

        Returns:
            True if both files were written.
        """
        filepath = self.to_table_file(table).value_or(None)
        if filepath is None or not is_successful(save_json_safe(records, filepath)):
            return False
        manifest = self.raw_manifest.unwrap()
        manifest["tables"][table.value]["sha256"] = file_sha256(filepath)
        saved = is_successful(save_json_safe(manifest, self.manifest_json.unwrap()))
        # read again on next use
        self._tables.pop(table, None)
        self._records.pop(table, None)
        return saved

    def to_schema_file(self, schema: SchemaName) -> Maybe[Path]:
        """Convert schema name to file path, which is <data_root>/annotation/<schema_name>.json."""
        return self.annotation_dir.map(lambda ann: ann.joinpath(schema.filename))

    def save_records(self, schema: SchemaName, records: list[dict]) -> bool:
        """Save schema data to file (for 1.0, also its SHA-256 in `manifest.json`)."""
        if self.schema_version == SchemaVersion.V1:
            return self.save_table(V1SchemaName(schema.value), records)
        match self.to_schema_file(schema):
            case Some(filepath):
                result = save_json_safe(records, filepath)
                if is_successful(result):
                    return True
                else:
                    print(f"Error saving schema: {result.failure()}")
                    return False
        return False

    def _build_records(self, table: V1SchemaName) -> Maybe[list]:
        match self.manifest:
            case Some(manifest):
                if table.value not in manifest.tables:
                    return Some([]) if table.is_optional() else Nothing
                match self.load_table(table):
                    case Some(records):
                        return result_to_maybe(_build_safe(table, records))
        return Nothing


@safe
def _build_safe(table: V1SchemaName, records: list[dict]) -> list:
    """Build the 1.0 records of a table; fails on the first invalid record."""
    return [SCHEMAS.get(table).from_dict(record) for record in records]


@safe
def _parse_lanelet_safe(path: Path) -> LaneletParser:
    return LaneletParser(path.as_posix(), verbose=False)
