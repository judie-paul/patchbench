from httpkit_headers import Headers


def test_get_exact_name():
    assert Headers({"Accept": "a"}).get("Accept") == "a"


def test_missing_returns_default():
    assert Headers().get("X-Nope", "d") == "d"


def test_set_then_get():
    h = Headers()
    h.set("Host", "example.org")
    assert h.get("Host") == "example.org"
