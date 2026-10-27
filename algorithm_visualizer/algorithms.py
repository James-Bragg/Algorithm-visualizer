"""Sorting algorithms written as step generators.

Each algorithm sorts a list in place and yields a :class:`Step` for every
comparison and every change it makes, so a view can replay the work one
operation at a time. The algorithms know nothing about drawing.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, auto


class Op(Enum):
    COMPARE = auto()  # values at i and j were compared
    SWAP = auto()  # values at i and j were swapped
    WRITE = auto()  # ``value`` was written to index i
    SORTED = auto()  # index i holds its final value


@dataclass(frozen=True, slots=True)
class Step:
    op: Op
    i: int
    j: int = -1
    value: int = 0

    @property
    def is_move(self) -> bool:
        return self.op in (Op.SWAP, Op.WRITE)


SortFn = Callable[[list[int], bool], Iterator[Step]]


def _before(a: int, b: int, ascending: bool) -> bool:
    """Return True if ``a`` must come strictly before ``b``."""
    return a < b if ascending else a > b


def _swap(values: list[int], i: int, j: int) -> Step:
    values[i], values[j] = values[j], values[i]
    return Step(Op.SWAP, i, j)


def bubble_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    for end in range(len(values) - 1, 0, -1):
        swapped = False
        for j in range(end):
            yield Step(Op.COMPARE, j, j + 1)
            if _before(values[j + 1], values[j], ascending):
                yield _swap(values, j, j + 1)
                swapped = True
        yield Step(Op.SORTED, end)
        if not swapped:
            break


def insertion_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    for i in range(1, len(values)):
        j = i
        while j > 0:
            yield Step(Op.COMPARE, j - 1, j)
            if not _before(values[j], values[j - 1], ascending):
                break
            yield _swap(values, j - 1, j)
            j -= 1


def selection_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    n = len(values)
    for i in range(n - 1):
        best = i
        for j in range(i + 1, n):
            yield Step(Op.COMPARE, best, j)
            if _before(values[j], values[best], ascending):
                best = j
        if best != i:
            yield _swap(values, i, best)
        yield Step(Op.SORTED, i)


def merge_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    yield from _merge_sort(values, 0, len(values), ascending)


def _merge_sort(values: list[int], lo: int, hi: int, ascending: bool) -> Iterator[Step]:
    if hi - lo < 2:
        return
    mid = (lo + hi) // 2
    yield from _merge_sort(values, lo, mid, ascending)
    yield from _merge_sort(values, mid, hi, ascending)

    merged: list[int] = []
    i, j = lo, mid
    while i < mid and j < hi:
        yield Step(Op.COMPARE, i, j)
        if _before(values[j], values[i], ascending):
            merged.append(values[j])
            j += 1
        else:
            merged.append(values[i])
            i += 1
    merged.extend(values[i:mid])
    merged.extend(values[j:hi])

    for k, value in enumerate(merged, start=lo):
        values[k] = value
        yield Step(Op.WRITE, k, value=value)


def quick_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    lo, hi = 0, len(values) - 1
    yield from _quick_sort(values, lo, hi, ascending)


def _quick_sort(values: list[int], lo: int, hi: int, ascending: bool) -> Iterator[Step]:
    # Recurse into the smaller partition and loop on the larger one so the
    # recursion depth stays logarithmic even on adversarial input.
    while lo < hi:
        mid = (lo + hi) // 2
        if mid != hi:
            yield _swap(values, mid, hi)
        pivot = values[hi]
        store = lo
        for k in range(lo, hi):
            yield Step(Op.COMPARE, k, hi)
            if _before(values[k], pivot, ascending):
                if k != store:
                    yield _swap(values, store, k)
                store += 1
        if store != hi:
            yield _swap(values, store, hi)
        yield Step(Op.SORTED, store)

        if store - lo < hi - store:
            yield from _quick_sort(values, lo, store - 1, ascending)
            lo = store + 1
        else:
            yield from _quick_sort(values, store + 1, hi, ascending)
            hi = store - 1


def heap_sort(values: list[int], ascending: bool = True) -> Iterator[Step]:
    n = len(values)
    for root in range(n // 2 - 1, -1, -1):
        yield from _sift_down(values, root, n, ascending)
    for end in range(n - 1, 0, -1):
        yield _swap(values, 0, end)
        yield Step(Op.SORTED, end)
        yield from _sift_down(values, 0, end, ascending)


def _sift_down(values: list[int], root: int, size: int, ascending: bool) -> Iterator[Step]:
    while (child := 2 * root + 1) < size:
        if child + 1 < size:
            yield Step(Op.COMPARE, child, child + 1)
            if _before(values[child], values[child + 1], ascending):
                child += 1
        yield Step(Op.COMPARE, root, child)
        if not _before(values[root], values[child], ascending):
            return
        yield _swap(values, root, child)
        root = child


@dataclass(frozen=True)
class Algorithm:
    name: str
    sort: SortFn
    summary: str
    best: str
    average: str
    worst: str
    space: str
    stable: bool


ALGORITHMS: dict[str, Algorithm] = {
    algorithm.name: algorithm
    for algorithm in (
        Algorithm(
            "Bubble Sort",
            bubble_sort,
            "Swaps adjacent out-of-order pairs; each pass carries the next extreme value "
            "to the end.",
            "O(n)",
            "O(n²)",
            "O(n²)",
            "O(1)",
            stable=True,
        ),
        Algorithm(
            "Insertion Sort",
            insertion_sort,
            "Grows a sorted prefix by sliding each new value left until it is in place.",
            "O(n)",
            "O(n²)",
            "O(n²)",
            "O(1)",
            stable=True,
        ),
        Algorithm(
            "Selection Sort",
            selection_sort,
            "Scans the unsorted part for the next value in order and swaps it to the front.",
            "O(n²)",
            "O(n²)",
            "O(n²)",
            "O(1)",
            stable=False,
        ),
        Algorithm(
            "Merge Sort",
            merge_sort,
            "Splits the list in half, sorts each half, then merges the sorted halves.",
            "O(n log n)",
            "O(n log n)",
            "O(n log n)",
            "O(n)",
            stable=True,
        ),
        Algorithm(
            "Quick Sort",
            quick_sort,
            "Partitions around a pivot so values fall on the correct side, then recurses.",
            "O(n log n)",
            "O(n log n)",
            "O(n²)",
            "O(log n)",
            stable=False,
        ),
        Algorithm(
            "Heap Sort",
            heap_sort,
            "Builds a heap, then repeatedly swaps its root to the end of the unsorted region.",
            "O(n log n)",
            "O(n log n)",
            "O(n log n)",
            "O(1)",
            stable=False,
        ),
    )
}


@dataclass(frozen=True, slots=True)
class RunStats:
    comparisons: int
    moves: int
    seconds: float


def measure(sort: SortFn, values: Sequence[int], ascending: bool = True) -> RunStats:
    """Run ``sort`` on a copy of ``values`` without any drawing and time it."""
    data = list(values)
    comparisons = moves = 0
    start = time.perf_counter()
    for step in sort(data, ascending):
        if step.op is Op.COMPARE:
            comparisons += 1
        elif step.is_move:
            moves += 1
    return RunStats(comparisons, moves, time.perf_counter() - start)
