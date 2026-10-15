from __future__ import annotations

from typing import Sequence

from typing_extensions import TYPE_CHECKING

from .context import SanityContext
from .registry import CHECKERS
from .result import SanityResult

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ["sanity_check"]


def sanity_check(
    data_root: PathLike,
    revision: str | None = None,
    *,
    excludes: Sequence[str] | None = None,
    fix: bool = False,
    checksum: bool = False,
) -> SanityResult:
    """Run sanity checks on the given data root.

    Args:
        data_root (PathLike): The root directory of the data.
        revision (str | None, optional): The revision to check. If None, the latest revision is used.
        excludes (Sequence[str] | None, optional): A list of rule names or groups to exclude.
        fix (bool, optional): Attempt to fix the issues reported by the sanity check.
        checksum (bool, optional): Verify the SHA-256 of every file listed in `manifest.json`
            (1.0 only). Reads every file, including videos and rosbags.

    Returns:
        A SanityResult object.
    """
    context = SanityContext.from_path(data_root, revision=revision, checksum=checksum)

    # only the rules of the dataset's schema version
    checkers = CHECKERS.build(excludes=excludes, version=context.schema_version)
    reports = [checker(context, fix=fix) for checker in checkers]

    return SanityResult.from_context(context, reports)
