"""
Random utilities
"""

from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, Iterable, overload

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison

    from utils.types_ import SupportsMath


class NoDefault(Enum):
    NO_DEFAULT = object()


NO_DEFAULT = NoDefault.NO_DEFAULT


@overload
def minmax[T: SupportsRichComparison](
    iterable: Iterable[T], /, *, key: None = None, default: T | NoDefault = NO_DEFAULT
) -> tuple[T, T]:
    """Return the minimum and maximum of a container."""


@overload
def minmax[T, C: SupportsRichComparison](
    iterable: Iterable[T],
    /,
    *,
    key: Callable[[T], C],
    default: T | NoDefault = NO_DEFAULT,
) -> tuple[T, T]:
    """Return the minimum and maximum of a container."""


@overload
def minmax[T1: SupportsRichComparison, T2: SupportsRichComparison](
    value1: T1, value2: T2, /, *, key: None = None
) -> tuple[T1 | T2, T1 | T2]:
    """Return the minimum and maximum of two values. Mostly useful if you're sampling two values but can't otherwise gaurantee their order."""


@overload
def minmax[T1, T2, C: SupportsRichComparison](
    value1: T1, value2: T2, /, *, key: Callable[[T1 | T2], C]
) -> tuple[T1 | T2, T1 | T2]:
    """Return the minimum and maximum of two values. Mostly useful if you're sampling two values but can't otherwise gaurantee their order."""


def minmax(a: Any, b: Any = None, /, *, key: Any = None, default: Any = NO_DEFAULT):
    """Return the minimum and maximum of some values."""
    if b is None:
        if default is NO_DEFAULT:
            return (min(a, key=key), max(a, key=key))
        else:
            return (min(a, key=key, default=default), max(a, key=key, default=default))
    return (min(a, b, key=key), max(a, b, key=key))


# min(None, None)
# min(3, 4)
# min("h", None)
# min([None, 3])
# minmax(None, None)
# minmax(3, 4)
# minmax("h", None)
# minmax([None, 3], default=3)


def intKey2dToJson(key: tuple[int, int]) -> str:
    """Take 2d int keys and make them json compatible."""
    return f"{key[0]}|{key[1]}"


def intKey2dFromJson(key: str) -> tuple[int, int]:
    """Take 2d int keys from json compatible"""
    l = key.split("|")
    return (int(l[0]), int(l[1]))


def collapse2dDict[T](
    dct: dict[tuple[int, int], T], default: T = None
) -> list[list[T]]:
    """Take a dict using keys of the form (int, int) and convert to a 2d array (list of lists). Makes more sense for dense matrices."""
    maxRows = max(k[0] for k in dct.keys()) + 1
    maxCols = max(k[1] for k in dct.keys()) + 1
    out = [[default for _ in range(maxCols)] for _ in range(maxRows)]
    for k, v in dct.items():
        r, c = k
        out[r][c] = v
    return out


def flatten[T](it: Iterable[Iterable[T]]):
    return chain.from_iterable(it)


def incrementFilename(filename: str) -> str:
    """Take a string, and if it has a number at the end, increment it. If it doesn't, make it -01."""
    n = None
    s = filename
    for i in range(1, len(filename)):
        try:
            n = int(filename[-i:])
            s = filename[:-i]
        except:
            break
    if n is None:
        return f"{s}-01"
    if n < 0:
        return f"{s}{n-1:03d}"
        # If you use '-' as a separator, it gets interpreted as a negative number.
        # So just decrement it so it looks like it's going up.
    else:
        return f"{s}{n+1:02d}"


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


def mapRange[T: SupportsMath](a: T, b: T, c: T, d: T, i: float) -> T:
    """Map value i from range [a:b] to range [c:d]"""
    if b - a == 0:
        return (0.5 * (d - c)) + c
    return (((i - a) / (b - a)) * (d - c)) + c


def clamp[T: SupportsRichComparison](v: T, v1: T, v2: T) -> T:
    mn = min(v1, v2)
    mx = max(v1, v2)
    return max(mn, min(mx, v))


def hex2(n: int) -> str:
    n = clamp(n, 0, 255)
    s = hex(n)[2:].upper()
    if len(s) == 1:
        return "0" + s
    return s


BracketDictAccess = lambda v: v.__dict__
"""
Cursed little class that lets us modify a class's  __dict__ via [brackets].
This is almost entirely so DictSettingsEditors can edit classes.
"""
if not TYPE_CHECKING:

    class BracketDictAccess:
        def __init__(self, target: type) -> None:
            self.target = target

            for name in dir(self.target.__dict__):
                if name.startswith("_"):
                    continue
                if name in dir(self):
                    continue

                def a(name):
                    setattr(
                        self,
                        name,
                        lambda *args, **kwargs: getattr(self.target.__dict__, name)(
                            *args, **kwargs
                        ),
                    )

                a(name)

        def __getitem__(self, key):
            return getattr(self.target, key)

        def __setitem__(self, key, value):
            setattr(self.target, key, value)


if __name__ == "__main__":
    print(hex2(0))
    print(hex2(6))
    print(hex2(12))
    print(hex2(37))
    print(hex2(155))
    print(hex2(-5))
    print(hex2(15555))
