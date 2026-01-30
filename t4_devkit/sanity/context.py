from __future__ import annotations

from pathlib import Path

from attrs import define
from returns.maybe import Maybe, Some
from returns.pipeline import is_successful
from typing_extensions import Self

from t4_devkit import DBMetadata
from t4_devkit.common import save_json
from t4_devkit.schema.name import SchemaName

from .safety import load_metadata_safe


@define
class SanityContext:
    metadata: Maybe[DBMetadata]

    @classmethod
    def from_path(cls, data_root: str, revision: str | None = None) -> Self:
        metadata_result = load_metadata_safe(data_root, revision=revision)
        metadata = metadata_result.unwrap() if is_successful(metadata_result) else None
        return cls(Maybe.from_optional(metadata))

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

    def to_schema_file(self, schema: SchemaName) -> Maybe[Path]:
        """Convert schema name to file path, which is <data_root>/annotation/<schema_name>.json."""
        return self.annotation_dir.map(lambda ann: ann.joinpath(schema.filename))

    def save_records(self, schema: SchemaName, records: list[dict]) -> bool:
        """Save schema data to file."""
        match self.to_schema_file(schema):
            case Some(filepath):
                try:
                    save_json(records, filepath)
                    return True
                except Exception as e:
                    print(f"Error saving schema: {e}")
                    return False
        return False
