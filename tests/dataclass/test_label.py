import pytest

from t4_devkit.dataclass.label import Label, convert_label


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
            Label.CAR,
        ),
        # truck
        (("truck", "vehicle.truck", "trailer", "vehicle.trailer"), Label.TRUCK),
        # bus
        (("bus", "vehicle.bus", "vehicle.bus (bendy & rigid)"), Label.BUS),
        # bicycle
        (("bicycle", "vehicle.bicycle"), Label.BICYCLE),
        # motorbike
        (
            ("motorbike", "vehicle.motorbike", "motorcycle", "vehicle.motorcycle"),
            Label.MOTORBIKE,
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
            Label.PEDESTRIAN,
        ),
        # animal
        ("animal", Label.ANIMAL),
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
            Label.UNKNOWN,
        ),
        # === traffic light ===
        # GREEN
        (("green", "crosswalk_green"), Label.GREEN),
        ("green_straight", Label.GREEN_STRAIGHT),
        ("green_left", Label.GREEN_LEFT),
        ("green_right", Label.GREEN_RIGHT),
        # YELLOW
        ("yellow", Label.YELLOW),
        ("yellow_straight", Label.YELLOW_STRAIGHT),
        ("yellow_left", Label.YELLOW_LEFT),
        ("yellow_right", Label.YELLOW_RIGHT),
        ("yellow_straight_left", Label.YELLOW_STRAIGHT_LEFT),
        ("yellow_straight_right", Label.YELLOW_STRAIGHT_RIGHT),
        ("yellow_straight_left_right", Label.YELLOW_STRAIGHT_LEFT_RIGHT),
        # RED
        (("red", "crosswalk_red"), Label.RED),
        ("red_straight", Label.RED_STRAIGHT),
        ("red_left", Label.RED_LEFT),
        ("red_right", Label.RED_RIGHT),
        ("red_straight_left", Label.RED_STRAIGHT_LEFT),
        ("red_straight_right", Label.RED_STRAIGHT_RIGHT),
        ("red_straight_left_right", Label.RED_STRAIGHT_LEFT_RIGHT),
        (
            ("red_straight_left_diagonal", "red_straight_leftdiagonal"),
            Label.RED_LEFT_DIAGONAL,
        ),
        (
            ("red_straight_right_diagonal", "red_straight_rightdiagonal"),
            Label.RED_RIGHT_DIAGONAL,
        ),
        # unknown traffic light
        (("unknown", "crosswalk_unknown"), Label.UNKNOWN),
    ],
)
def test_convert_object_label(labels: str | tuple[str, ...], expect: Label) -> None:
    if isinstance(labels, str):
        labels = [labels]

    for original in labels:
        ret = convert_label(original)
        assert ret.label == expect
        assert ret.original == original
