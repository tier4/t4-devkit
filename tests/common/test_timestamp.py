from t4_devkit.common.timestamp import sec2us, us2sec


def test_timestamp() -> None:
    """Test timestamp conversion."""
    seconds = 1e-6

    us = sec2us(seconds)
    sec = us2sec(us)

    assert us == 1
    assert sec == 1e-6
