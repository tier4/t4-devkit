from __future__ import annotations

import os.path as osp
from abc import abstractmethod

from t4_devkit.schema import SchemaName

from .base import Checker
from .result import GroupName, Report, TargetName, make_error, make_ok


class StructureChecker(Checker):
    group = GroupName("structure")

    @abstractmethod
    def __call__(self, data_root: str) -> list[Report]:
        pass


class AnnotationStructureChecker(StructureChecker):
    target = TargetName("annotation")

    def __call__(self, data_root: str) -> list[Report]:
        reports: list[Report] = []
        reports.extend(self._check_annotation_dir(data_root))
        reports.extend(self._check_schema_files(data_root))
        return reports

    def _check_annotation_dir(self, data_root: str) -> list[Report]:
        rule = "annotation-dir-exist"

        annotation_root = osp.join(data_root, "annotation")
        if not osp.exists(annotation_root):
            return [make_error(rule, f"Cannot find annotation root: {annotation_root}")]
        else:
            return [make_ok(rule)]

    def _check_schema_files(self, data_root: str):
        rule = "schema-files-exist"

        reports = []
        annotation_root = osp.join(data_root, "annotation")
        for name in SchemaName:
            filepath = osp.join(annotation_root, name.filename)
            current = f"{rule}:{name}"
            if not osp.exists(filepath) and not name.is_optional():
                reports.append(make_error(current, f"Cannot find annotation file: {filepath}"))
            else:
                reports.append(make_ok(current))
        return reports


class MapStructureChecker(StructureChecker):
    target = TargetName("map")

    def __call__(self, data_root: str) -> list[Report]:
        reports = []
        reports.extend(self._check_map_dir(data_root))
        reports.extend(self._check_lanelet_file(data_root))
        reports.extend(self._check_pointcloud_map_dir(data_root))
        return reports

    def _check_map_dir(self, data_root: str) -> list[Report]:
        rule = "map-dir-exist"

        map_root = osp.join(data_root, "map")
        if not osp.exists(map_root):
            return [make_error(rule, f"Cannot find map root: {map_root}")]
        else:
            return [make_ok(rule)]

    def _check_lanelet_file(self, data_root: str) -> list[Report]:
        rule = "lanelet-file-exist"

        lanelet_root = osp.join(data_root, "map", "lanelet2_map.osm")
        if not osp.exists(lanelet_root):
            return [make_error(rule, f"Cannot find lanelet file: {lanelet_root}")]
        else:
            return [make_ok(rule)]

    def _check_pointcloud_map_dir(self, data_root: str) -> list[Report]:
        rule = "pointcloud-map-dir-exist"

        pointcloud_map_root = osp.join(data_root, "map", "pointcloud_map")
        if not osp.exists(pointcloud_map_root):
            return [make_error(rule, f"Cannot find pointcloud map root: {pointcloud_map_root}")]
        else:
            return [make_ok(rule)]


class InputBagStructureChecker(StructureChecker):
    target = TargetName("input_bag")

    def __call__(self, data_root: str) -> list[Report]:
        reports = []
        reports.extend(self._check_input_bag_dir(data_root))
        return reports

    def _check_input_bag_dir(self, data_root: str) -> list[Report]:
        rule = "input-bag-dir-exist"

        input_bag_root = osp.join(data_root, "input_bag")
        if not osp.exists(input_bag_root):
            return [make_error(rule, f"Cannot find input bag root: {input_bag_root}")]
        else:
            return [make_ok(rule)]
