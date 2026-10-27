import sqlite3
from pathlib import Path

import pytest

from algorithm_visualizer.data import MAX_VALUES, load_numbers, parse_numbers
from algorithm_visualizer.storage import HistoryStore


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1 2 3", [1, 2, 3]),
        ("4,5;6", [4, 5, 6]),
        ("13\n342\n\n43\n", [13, 342, 43]),
        ("  -3, 0 , 9 ", [-3, 0, 9]),
    ],
)
def test_parse_numbers(text: str, expected: list[int]) -> None:
    assert parse_numbers(text) == expected


@pytest.mark.parametrize("text", ["", "   \n ", "1 two 3", "1.5"])
def test_parse_numbers_rejects_bad_input(text: str) -> None:
    with pytest.raises(ValueError):
        parse_numbers(text)


def test_parse_numbers_rejects_too_many() -> None:
    with pytest.raises(ValueError, match="limit"):
        parse_numbers(" ".join(["1"] * (MAX_VALUES + 1)))


def test_load_numbers_reads_example_file() -> None:
    example = Path(__file__).parent.parent / "examples" / "numbers.txt"
    assert load_numbers(example)[:3] == [13, 342, 43]


def test_history_round_trip(tmp_path: Path) -> None:
    with HistoryStore(tmp_path / "nested" / "history.sqlite3") as store:
        first = store.add("Bubble Sort", [3, 1, 2], True, 3, 2, 0.5)
        second = store.add("Heap Sort", [9, 8], False, 1, 1, 0.1)

        runs = store.runs()
        assert [run.id for run in runs] == [second.id, first.id]
        assert runs[1].numbers == (3, 1, 2)
        assert runs[1].ascending is True
        assert runs[0].ascending is False
        assert runs[1].created_at is not None
        assert store.count() == 2

        store.clear()
        assert store.runs() == []


def _legacy_encrypt(text: str) -> str:
    alphabet = "abcde5f6g1hi7jklmn8op9q2rs0tuv3wx4yz. "
    return "".join(alphabet[(alphabet.find(c) + 5) % 38] for c in text)


def test_imports_legacy_database_once(tmp_path: Path) -> None:
    legacy_path = tmp_path / "SQLDB.sqlite3"
    legacy = sqlite3.connect(legacy_path)
    legacy.execute(
        "CREATE TABLE tblMain (EventID INTEGER PRIMARY KEY, NumbersPicked TEXT,"
        " AlgorithmChosen TEXT, TimeTaken TEXT)"
    )
    legacy.executemany(
        "INSERT INTO tblMain VALUES (?, ?, ?, ?)",
        [
            (1, _legacy_encrypt("3 4 5"), _legacy_encrypt("bubble sort"), _legacy_encrypt("0.25")),
            (2, _legacy_encrypt(""), _legacy_encrypt("insertion sort"), _legacy_encrypt("0.1")),
        ],
    )
    legacy.commit()
    legacy.close()

    with HistoryStore(":memory:") as store:
        assert store.import_legacy(legacy_path) == 1
        assert store.import_legacy(legacy_path) == 0
        (run,) = store.runs()
        assert run.algorithm == "Bubble Sort"
        assert run.numbers == (3, 4, 5)
        assert run.duration_ms == pytest.approx(250)
        assert run.ascending is None


def test_import_legacy_ignores_missing_file(tmp_path: Path) -> None:
    with HistoryStore(":memory:") as store:
        assert store.import_legacy(tmp_path / "missing.sqlite3") == 0
