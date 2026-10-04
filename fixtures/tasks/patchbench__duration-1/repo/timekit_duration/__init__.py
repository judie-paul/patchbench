"""Parse durations such as '1h30m' into seconds."""

import re

UNITS = {"s": 1, "m": 1, "h": 3600}


def parse_duration(text: str) -> int:
    total = 0
    for amount, unit in re.findall(r"(\d+)([smh])", text):
        total += int(amount) * UNITS[unit]
    return total
