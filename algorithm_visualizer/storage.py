"""SQLite-backed history of completed sorting runs."""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT,
    algorithm   TEXT    NOT NULL,
    ascending   INTEGER,
    numbers     TEXT    NOT NULL,
    comparisons INTEGER,
    moves       INTEGER,
    duration_ms REAL
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# The original version of this app obfuscated every field with a shift cipher
# over this alphabet. It is only needed to read old databases.
_LEGACY_ALPHABET = "abcde5f6g1hi7jklmn8op9q2rs0tuv3wx4yz. "
_LEGACY_SHIFT = 5
_LEGACY_DECODE = str.maketrans(
    _LEGACY_ALPHABET,
    _LEGACY_ALPHABET[-_LEGACY_SHIFT:] + _LEGACY_ALPHABET[:-_LEGACY_SHIFT],
)

_INTEGER = re.compile(r"-?\d+")


def default_db_path() -> Path:
    """Return the per-user location of the history database."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "AlgorithmVisualizer" / "history.sqlite3"


@dataclass(frozen=True, slots=True)
class Run:
    id: int
    algorithm: str
    numbers: tuple[int, ...]
    ascending: bool | None = None
    comparisons: int | None = None
    moves: int | None = None
    duration_ms: float | None = None
    created_at: datetime | None = None


class HistoryStore:
    def __init__(self, path: str | Path) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.executescript(_SCHEMA)

    def __enter__(self) -> HistoryStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def add(
        self,
        algorithm: str,
        numbers: Sequence[int],
        ascending: bool,
        comparisons: int,
        moves: int,
        duration_ms: float,
    ) -> Run:
        created_at = datetime.now(UTC)
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO runs (created_at, algorithm, ascending, numbers, comparisons,"
                " moves, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    created_at.isoformat(),
                    algorithm,
                    int(ascending),
                    _join(numbers),
                    comparisons,
                    moves,
                    duration_ms,
                ),
            )
        return Run(
            id=cursor.lastrowid,
            algorithm=algorithm,
            numbers=tuple(numbers),
            ascending=ascending,
            comparisons=comparisons,
            moves=moves,
            duration_ms=duration_ms,
            created_at=created_at,
        )

    def runs(self, limit: int = 500) -> list[Run]:
        """Return the most recent runs, newest first."""
        rows = self._conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))
        return [_row_to_run(row) for row in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]

    def clear(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM runs")

    def import_legacy(self, path: str | Path) -> int:
        """Copy runs from a database made by the original app, once.

        Returns the number of runs imported. Later calls with the same file do
        nothing, so this is safe to call on every start-up.
        """
        path = Path(path).resolve()
        key = f"legacy_import:{path}"
        if not path.is_file() or self._meta(key) is not None:
            return 0

        legacy = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        try:
            rows = legacy.execute(
                "SELECT NumbersPicked, AlgorithmChosen, TimeTaken FROM tblMain ORDER BY rowid"
            ).fetchall()
        except sqlite3.DatabaseError:
            rows = []
        finally:
            legacy.close()

        records = []
        for numbers, algorithm, seconds in rows:
            values = _parse_ints(_legacy_decode(numbers))
            if values:
                duration = _parse_float(_legacy_decode(seconds))
                records.append(
                    (
                        _legacy_decode(algorithm).strip().title(),
                        _join(values),
                        None if duration is None else duration * 1000,
                    )
                )

        with self._conn:
            self._conn.executemany(
                "INSERT INTO runs (algorithm, numbers, duration_ms) VALUES (?, ?, ?)", records
            )
            self._conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?)", (key, str(len(records)))
            )
        return len(records)

    def _meta(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else row[0]


def _join(numbers: Sequence[int]) -> str:
    return " ".join(map(str, numbers))


def _parse_ints(text: str) -> list[int]:
    return [int(token) for token in text.split() if _INTEGER.fullmatch(token)]


def _parse_float(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def _legacy_decode(text: str) -> str:
    return str(text).translate(_LEGACY_DECODE)


def _row_to_run(row: sqlite3.Row) -> Run:
    return Run(
        id=row["id"],
        algorithm=row["algorithm"],
        numbers=tuple(_parse_ints(row["numbers"])),
        ascending=None if row["ascending"] is None else bool(row["ascending"]),
        comparisons=row["comparisons"],
        moves=row["moves"],
        duration_ms=row["duration_ms"],
        created_at=None if row["created_at"] is None else datetime.fromisoformat(row["created_at"]),
    )
