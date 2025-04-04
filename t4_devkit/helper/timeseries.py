from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.common.timestamp import us2sec

if TYPE_CHECKING:
    from t4_devkit import Tier4
    from t4_devkit.schema import ObjectAnn, Sample, SampleAnnotation, SampleData


__all__ = ["TimeseriesHelper"]


class TimeseriesHelper:
    """Help `Tier4` class with timeseries relevant operations."""

    def __init__(self, t4: Tier4) -> None:
        """Construct a new object.

        Args:
            t4 (Tier4): `Tier4` instance.
        """
        self._t4 = t4

        self._sample_and_instance_to_ann3d: dict[tuple[str, str], str] = {
            (ann.sample_token, ann.instance_token): ann.token for ann in self._t4.sample_annotation
        }
        self._sample_data_and_instance_to_ann2d: dict[tuple[str, str], str] = {
            (ann.sample_data_token, ann.instance_token): ann.token for ann in self._t4.object_ann
        }

    def get_sample_annotations_until(
        self,
        instance_token: str,
        sample_token: str,
        seconds: float,
    ) -> tuple[list[int], list[SampleAnnotation]]:
        """Return a list of sample annotations until the specified seconds.

        If `seconds>=0` explores future, otherwise past.

        Args:
            instance_token (str): Instance token of any sample annotations.
            sample_token (str): Start sample token.
            seconds (float): Time seconds until. If `>=0` explore future, otherwise past.

        Returns:
            List of timestamps and associated sample annotation records of the specified instance.
        """
        start_sample: Sample = self._t4.get("sample", sample_token)

        timestamps: list[int] = []
        anns: list[SampleAnnotation] = []
        is_successor = seconds >= 0
        current_sample_token = start_sample.next if is_successor else start_sample.prev
        while current_sample_token != "":
            current_sample: Sample = self._t4.get("sample", current_sample_token)

            if abs(us2sec(current_sample.timestamp - start_sample.timestamp)) > abs(seconds):
                break

            ann_token = self._sample_and_instance_to_ann3d.get(
                (current_sample_token, instance_token)
            )
            if ann_token is not None:
                timestamps.append(current_sample.timestamp)
                anns.append(self._t4.get("sample_annotation", ann_token))

            current_sample_token = current_sample.next if is_successor else current_sample.prev

        return timestamps, anns

    def get_object_anns_until(
        self,
        instance_token: str,
        sample_data_token: str,
        seconds: float,
    ) -> tuple[list[int], list[ObjectAnn]]:
        """Return a list of object anns until the specified seconds.

        If `seconds>=0` explores future, otherwise past.

        Args:
            instance_token (str): Instance token of any object anns.
            sample_data_token (str): Start sample data token.
            seconds (float): Time seconds until. If `>=0` explore future, otherwise past.

        Returns:
            List of timestamps and associated object annotation records of the specified instance.
        """
        start_sample_data: SampleData = self._t4.get("sample_data", sample_data_token)

        timestamps: list[int] = []
        anns: list[ObjectAnn] = []
        is_successor = seconds >= 0
        current_sample_data_token = (
            start_sample_data.next if is_successor else start_sample_data.prev
        )
        while current_sample_data_token != "":
            current_sample_data: SampleData = self._t4.get("sample_data", current_sample_data_token)

            if abs(us2sec(current_sample_data.timestamp - start_sample_data.timestamp)) > abs(
                seconds
            ):
                break

            ann_token = self._sample_data_and_instance_to_ann2d.get(
                (current_sample_data_token, instance_token)
            )
            if ann_token is not None:
                timestamps.append(current_sample_data.timestamp)
                anns.append(self._t4.get("object_ann", ann_token))

            current_sample_data_token = (
                current_sample_data.next if is_successor else current_sample_data.prev
            )

        return timestamps, anns
