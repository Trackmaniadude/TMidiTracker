"""
Random utilities
"""

from __future__ import annotations


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
