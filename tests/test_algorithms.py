import random

import pytest

from algorithm_visualizer.algorithms import ALGORITHMS, Op, measure

CASES = [
    [],
    [7],
    [2, 1],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [3, 3, 3, 3],
    [0, -4, 12, -4, 8, 0],
    [13, 342, 43, 123, 43, 23, 243, 53, 23, 43, 321, 43, 323],
]


def random_cases(count: int = 25) -> list[list[int]]:
    rng = random.Random(1234)
    return [[rng.randint(-50, 50) for _ in range(rng.randint(0, 60))] for _ in range(count)]


@pytest.mark.parametrize("name", ALGORITHMS)
@pytest.mark.parametrize("ascending", [True, False])
@pytest.mark.parametrize("values", CASES + random_cases())
def test_sorts_correctly(name: str, ascending: bool, values: list[int]) -> None:
    data = list(values)
    for _ in ALGORITHMS[name].sort(data, ascending):
        pass
    assert data == sorted(values, reverse=not ascending)


@pytest.mark.parametrize("name", ALGORITHMS)
@pytest.mark.parametrize("values", CASES + random_cases())
def test_steps_replay_to_the_same_result(name: str, values: list[int]) -> None:
    """The view relies on the steps alone describing every change."""
    data = list(values)
    replay = list(values)
    for step in ALGORITHMS[name].sort(data, True):
        assert 0 <= step.i < len(values)
        if step.op in (Op.COMPARE, Op.SWAP):
            assert 0 <= step.j < len(values)
        if step.op is Op.SWAP:
            replay[step.i], replay[step.j] = replay[step.j], replay[step.i]
        elif step.op is Op.WRITE:
            replay[step.i] = step.value
    assert replay == data


@pytest.mark.parametrize("name", ALGORITHMS)
def test_sorted_marks_are_final(name: str) -> None:
    values = random_cases(1)[0]
    data = list(values)
    marked = {}
    for step in ALGORITHMS[name].sort(data, True):
        if step.op is Op.SORTED:
            marked[step.i] = data[step.i]
    expected = sorted(values)
    assert all(expected[i] == value for i, value in marked.items())


def test_quick_sort_handles_large_sorted_input_without_deep_recursion() -> None:
    data = list(range(5000))
    for _ in ALGORITHMS["Quick Sort"].sort(data, False):
        pass
    assert data == list(range(4999, -1, -1))


def test_measure_counts_and_leaves_input_alone() -> None:
    values = [3, 1, 2]
    stats = measure(ALGORITHMS["Bubble Sort"].sort, values)
    assert values == [3, 1, 2]
    assert stats.comparisons == 3
    assert stats.moves == 2
    assert stats.seconds >= 0
