from datakit_csv import to_csv_row


def test_plain_fields():
    assert to_csv_row(["a", "b", 1]) == "a,b,1"


def test_empty_row():
    assert to_csv_row([]) == ""


def test_whitespace_is_preserved():
    assert to_csv_row(["a ", " b"]) == "a , b"
