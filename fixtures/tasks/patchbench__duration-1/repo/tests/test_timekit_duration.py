from timekit_duration import parse_duration


def test_seconds():
    assert parse_duration("45s") == 45


def test_hours():
    assert parse_duration("2h") == 7200


def test_empty_is_zero():
    assert parse_duration("") == 0
