"""Creating and parsing the lists of numbers that get sorted."""

from __future__ import annotations

import random
import re
from pathlib import Path

MIN_SIZE = 5
MAX_SIZE = 150
MAX_VALUES = 300

_SEPARATORS = re.compile(r"[\s,;]+")


def parse_numbers(text: str) -> list[int]:
    """Parse whole numbers separated by whitespace, commas or semicolons.

    Raises ``ValueError`` with a user-facing message if the text is empty,
    contains anything that is not a whole number, or is too long.
    """
    tokens = [token for token in _SEPARATORS.split(text.strip()) if token]
    if not tokens:
        raise ValueError("No numbers found.")

    values: list[int] = []
    invalid: list[str] = []
    for token in tokens:
        try:
            values.append(int(token))
        except ValueError:
            invalid.append(token)

    if invalid:
        shown = ", ".join(repr(token) for token in invalid[:5])
        more = f" and {len(invalid) - 5} more" if len(invalid) > 5 else ""
        raise ValueError(f"These aren't whole numbers: {shown}{more}.")
    if len(values) > MAX_VALUES:
        raise ValueError(f"That's {len(values)} numbers; the limit is {MAX_VALUES}.")
    return values


def load_numbers(path: str | Path) -> list[int]:
    return parse_numbers(Path(path).read_text(encoding="utf-8-sig"))


def random_values(count: int, low: int = 5, high: int = 100) -> list[int]:
    return [random.randint(low, high) for _ in range(count)]
