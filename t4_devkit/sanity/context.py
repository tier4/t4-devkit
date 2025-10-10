from __future__ import annotations

from pathlib import Path

from attrs import define
from returns.maybe import Maybe
from returns.pipeline import is_successful
from returns.result import Result, safe
from typing_extensions import Self

from t4_devkit import DBMetadata, load_metadata
from t4_devkit.schema.name import SchemaName


@define
class SanityContext:
    metadata: Maybe[DBMetadata]

    @classmethod
    def from_path(cls, data_root: str, revision: str | None = None) -> Self:
        metadata_result = _load_metadata_safe(data_root, revision=revision)
        metadata = metadata_result.unwrap() if is_successful(metadata_result) else None
        return cls(Maybe.from_optional(metadata))

    @property
    def data_root(self) -> Maybe[Path]:
        return self.metadata.map(lambda m: Path(m.data_root))

    @property
    def dataset_id(self) -> Maybe[str]:
        return self.metadata.map(lambda m: m.dataset_id)

    @property
    def version(self) -> Maybe[str]:
        return self.metadata.map(lambda m: m.version)

    @property
    def annotation_dir(self) -> Maybe[Path]:
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("annotation"))

    @property
    def sensor_data_dir(self) -> Maybe[Path]:
        pass

    @property
    def map_dir(self) -> Maybe[Path]:
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("map"))

    @property
    def bag_dir(self) -> Maybe[Path]:
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("input_bag"))

    @property
    def status_json(self) -> Maybe[Path]:
        return self.metadata.map(lambda m: Path(m.data_root).joinpath("status.json"))

    def to_schema_file(self, schema: SchemaName) -> Maybe[Path]:
        return self.data_root.map(lambda root: root.joinpath(schema.filename))


@safe
def _load_metadata_safe(
    data_root: str,
    revision: str | None = None,
) -> Result[DBMetadata, Exception]:
    return load_metadata(data_root, revision=revision)
