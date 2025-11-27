"""
Random utilities
"""

from typing import Iterable


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
