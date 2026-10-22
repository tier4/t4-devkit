from __future__ import annotations

from enum import Enum, unique

__all__ = ["AnnotationType"]


@unique
class AnnotationType(str, Enum):
    """How a label was made.

    Every label table has `annotation_type`, `provenance` and `confidence` fields.

    Attributes:
        MANUAL: Made by a human annotator.
        AUTO: Made by an offline auto-labeling model or pipeline, not reviewed by a human.
        PSEUDO: Taken from another system's output and used as a weak label, e.g. onboard
            perception or tracker results.
        CORRECTED: Made automatically (auto, pseudo or interpolated), then reviewed and
            corrected by a human.
        INTERPOLATED: Computed between labeled frames, not reviewed frame by frame.
        SYNTHETIC: Known by construction, from simulation or generated data.
    """

    MANUAL = "manual"
    AUTO = "auto"
    PSEUDO = "pseudo"
    CORRECTED = "corrected"
    INTERPOLATED = "interpolated"
    SYNTHETIC = "synthetic"
