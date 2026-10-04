"""Format one CSV row."""


def to_csv_row(fields) -> str:
    return ",".join(str(f) for f in fields)
