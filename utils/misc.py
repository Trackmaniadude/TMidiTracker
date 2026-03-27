"""
Random utilities
"""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Callable, Iterable, overload

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison


@overload
def minmax[
    T: SupportsRichComparison
](a: Iterable[T], *, key: None = None) -> tuple[T, T]:
    """Return the minimum and maximum of a container."""


@overload
def minmax[
    T, C: SupportsRichComparison
](a: Iterable[T], *, key: Callable[[T], C]) -> tuple[T, T]:
    """Return the minimum and maximum of a container."""


@overload
def minmax[
    T1: SupportsRichComparison, T2: SupportsRichComparison
](a: T1, b: T2, *, key: None = None) -> tuple[T1 | T2, T1 | T2]:
    """Return the minimum and maximum of two values. Mostly useful if you're sampling two values but can't otherwise gaurantee their order."""


@overload
def minmax[
    T1, T2, C: SupportsRichComparison
](a: T1, b: T2, *, key: Callable[[T1 | T2], C]) -> tuple[T1 | T2, T1 | T2]:
    """Return the minimum and maximum of two values. Mostly useful if you're sampling two values but can't otherwise gaurantee their order."""


# min(None, None)
# min(3, 4)
# min("h", None)
# min([None, 3])
# minmax(None, None)
# minmax(3, 4)
# minmax("h", None)
# minmax([None, 3])


def minmax(a, b=None, *, key=None):
    """Return the minimum and maximum of some values."""
    if b is None:
        return (min(a, key=key), max(a, key=key))
    return (min(a, b, key=key), max(a, b, key=key))


def intKey2dToJson(key: tuple[int, int]) -> str:
    """Take 2d int keys and make them json compatible."""
    return f"{key[0]}|{key[1]}"


def intKey2dFromJson(key: str) -> tuple[int, int]:
    """Take 2d int keys from json compatible"""
    l = key.split("|")
    return (int(l[0]), int(l[1]))


def collapse2dDict[
    T
](dct: dict[tuple[int, int], T], default: T = None) -> list[list[T]]:
    """Take a dict using keys of the form (int, int) and convert to a 2d array (list of lists). Makes more sense for dense matrices."""
    maxRows = max(k[0] for k in dct.keys()) + 1
    maxCols = max(k[1] for k in dct.keys()) + 1
    out = [[default for _ in range(maxCols)] for _ in range(maxRows)]
    for k, v in dct.items():
        r, c = k
        out[r][c] = v
    return out


def formatTime(t: float, alwaysShowHour: bool = False) -> str:
    """Format a number of seconds."""
    sec = int(t % 60)
    min = int((t / 60) % 60)
    hou = int(((t / 60) / 60) % 60)
    if hou != 0 or alwaysShowHour:
        return f"{hou}:{min:02d}:{sec:02d}"
    else:
        return f"{min}:{sec:02d}"


def itemFromSet[T](set: set[T]) -> T | None:
    """Get an arbitrary item from a set, or None if it is empty."""
    try:
        return next(iter(set))
    except StopIteration:
        return None


def mapRange(a, b, c, d, i: float):
    """Map value i from range [a:b] to range [c:d]"""
    if b - a == 0:
        return (0.5 * (d - c)) + c
    return (((i - a) / (b - a)) * (d - c)) + c


def clamp(v, v1, v2):
    mn = min(v1, v2)
    mx = max(v1, v2)
    return max(mn, min(mx, v))


def hex2(n: int) -> str:
    n = clamp(n, 0, 255)
    s = hex(n)[2:].upper()
    if len(s) == 1:
        return "0" + s
    return s


if __name__ == "__main__":
    print(hex2(0))
    print(hex2(6))
    print(hex2(12))
    print(hex2(37))
    print(hex2(155))
    print(hex2(-5))
    print(hex2(15555))
