from textkit_slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_trims_and_collapses():
    assert slugify("  a   b  ") == "a-b"


def test_symbols():
    assert slugify("rock & roll!") == "rock-roll"
