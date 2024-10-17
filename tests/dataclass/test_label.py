import pytest

from t4_devkit.dataclass.label import LabelID, convert_label


@pytest.mark.parametrize(
    ("labels", "expect"),
    [
        # === object ===
        # car
        (
            (
                "car",
                "vehicle.car",
                "vehicle.construction",
                "vehicle.emergency (ambulance & police)",
                "vehicle.police",
            ),
            LabelID.CAR,
        ),
        # truck
        (("truck", "vehicle.truck", "trailer", "vehicle.trailer"), LabelID.TRUCK),
        # bus
        (("bus", "vehicle.bus", "vehicle.bus (bendy & rigid)"), LabelID.BUS),
        # bicycle
        (("bicycle", "vehicle.bicycle"), LabelID.BICYCLE),
        # motorbike
        (
            ("motorbike", "vehicle.motorbike", "motorcycle", "vehicle.motorcycle"),
            LabelID.MOTORBIKE,
        ),
        # pedestrian
        (
            (
                "pedestrian",
                "pedestrian.child",
                "pedestrian.personal_mobility",
                "pedestrian.police_officer",
                "pedestrian.stroller",
                "pedestrian.wheelchair",
                "construction_worker",
            ),
            LabelID.PEDESTRIAN,
        ),
        # animal
        ("animal", LabelID.ANIMAL),
        # unknown
        (
            (
                "movable_object.barrier",
                "movable_object.debris",
                "movable_object.pushable_pullable",
                "movable_object.trafficcone",
                "movable_object.traffic_cone",
                "static_object.bicycle_lack",
                "static_object.bollard",
                "forklift",
            ),
            LabelID.UNKNOWN,
        ),
        # === traffic light ===
        # GREEN
        (("green", "crosswalk_green"), LabelID.GREEN),
        ("green_straight", LabelID.GREEN_STRAIGHT),
        ("green_left", LabelID.GREEN_LEFT),
        ("green_right", LabelID.GREEN_RIGHT),
        # YELLOW
        ("yellow", LabelID.YELLOW),
        ("yellow_straight", LabelID.YELLOW_STRAIGHT),
        ("yellow_left", LabelID.YELLOW_LEFT),
        ("yellow_right", LabelID.YELLOW_RIGHT),
        ("yellow_straight_left", LabelID.YELLOW_STRAIGHT_LEFT),
        ("yellow_straight_right", LabelID.YELLOW_STRAIGHT_RIGHT),
        ("yellow_straight_left_right", LabelID.YELLOW_STRAIGHT_LEFT_RIGHT),
        # RED
        (("red", "crosswalk_red"), LabelID.RED),
        ("red_straight", LabelID.RED_STRAIGHT),
        ("red_left", LabelID.RED_LEFT),
        ("red_right", LabelID.RED_RIGHT),
        ("red_straight_left", LabelID.RED_STRAIGHT_LEFT),
        ("red_straight_right", LabelID.RED_STRAIGHT_RIGHT),
        ("red_straight_left_right", LabelID.RED_STRAIGHT_LEFT_RIGHT),
        (
            ("red_straight_left_diagonal", "red_straight_leftdiagonal"),
            LabelID.RED_LEFT_DIAGONAL,
        ),
        (
            ("red_straight_right_diagonal", "red_straight_rightdiagonal"),
            LabelID.RED_RIGHT_DIAGONAL,
        ),
        # unknown traffic light
        (("unknown", "crosswalk_unknown"), LabelID.UNKNOWN),
    ],
)
def test_convert_label(labels: str | tuple[str, ...], expect: LabelID) -> None:
    if isinstance(labels, str):
        labels = [labels]

    for original in labels:
        ret = convert_label(original)
        assert ret.label == expect
        assert ret.original == original
