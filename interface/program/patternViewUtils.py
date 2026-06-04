from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from typing import Callable

if __name__ == "__main__":
    import sys

    sys.path.append(".")

from utils.constants import (
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
    DRUM_NAMES,
    HEX_KEYMAP,
    KEYBOARD_MAP,
    NOTE_DELTAS,
    NOTE_NAMES_FLAT,
    NOTE_NAMES_SHARP,
    NOTES_PER_OCTAVE,
)
from utils.misc import hex2
from utils.types_ import effect, note, velocity


@dataclass
class PatternViewClipboardChannel:
    channelOffset: int
    notes: dict[tuple[int, int], note | None] = field(default_factory=lambda: dict())
    velocities: dict[tuple[int, int], velocity | None] = field(
        default_factory=lambda: dict()
    )
    effects: dict[tuple[int, int], effect | None] = field(
        default_factory=lambda: dict()
    )


@dataclass
class Target:
    channel: int
    row: int
    column: PVLM
    subcolumn: int

    @property
    def horizontalComparisonKey(self):
        """(Channel #, is in effect column, column # (even is note, odd is velocity))"""
        c = self.column
        return (
            self.channel,
            c == PVLM.EFFECT,
            (self.subcolumn * 2) + (1 if c == PVLM.VELOCITY else 0),
        )

    @property
    def horizontalComparisonKeyView(self):
        """(Channel #, is in effect column, column # (even is note, odd is velocity))"""
        c = self.column
        return (
            CHANNEL_ORDER_INVERSE[self.channel],
            c == PVLM.EFFECT,
            (self.subcolumn * 2) + (1 if c == PVLM.VELOCITY else 0),
        )

    @staticmethod
    def columnGreaterThan(a: Target, b: Target) -> bool:
        return a.horizontalComparisonKey > b.horizontalComparisonKey


@dataclass
@total_ordering
class PatternViewLabelMode[T]:
    t: T
    parentName: str
    width: int
    setter: str
    getter: str
    fromView: Callable[[str], T]
    toView: Callable[[T, int], str]
    order: int

    def __gt__(self, other) -> bool:
        if not isinstance(other, PatternViewLabelMode):
            raise TypeError()
        return self.order > other.order

    def __str__(self) -> str:
        return f"PVLM"

    def __repr__(self) -> str:
        return f"PVLM"


def fromEffectString(s: str) -> tuple[int, ...]:
    l = list()
    for i in range(0, len(s), 2):
        sub = s[i : i + 2]
        l.append(int(sub, 16))
    return tuple(l)


def toEffectString(t: tuple[int, ...]) -> str:
    return "".join(hex2(n) for n in t)


@total_ordering
class PatternViewLabelModes(Enum):
    def __gt__(self, other) -> bool:
        if not isinstance(other, PatternViewLabelModes):
            raise TypeError()
        return self.value > other.value

    NOTE = PatternViewLabelMode(
        t=note,
        parentName="noteFrame",
        width=3,
        setter="setNote",
        getter="getNote",
        fromView=lambda _: _,
        # fmt: off
        toView=lambda v, c: (
            "STP"
            if v == "stop"
            else (
                NOTE_NAMES_SHARP[v % NOTES_PER_OCTAVE] + str(v // NOTES_PER_OCTAVE) # type: ignore
                if c != DRUM_CHANNEL
                else DRUM_NAMES[v] # type: ignore
            )
        ),
        order=0,
        # fmt: on
    )
    VELOCITY = PatternViewLabelMode(
        t=velocity,
        parentName="noteFrame",
        width=2,
        setter="setVelocity",
        getter="getVelocity",
        fromView=lambda s: int(s, 16),
        toView=lambda v, _: hex2(v),  # type: ignore
        order=1,
    )
    EFFECT = PatternViewLabelMode(
        t=effect,
        parentName="effectFrame",
        width=6,
        setter="setEffect",
        getter="getEffect",
        fromView=fromEffectString,
        toView=lambda v, _: toEffectString(v),  # type: ignore
        order=2,
    )


PVLM = PatternViewLabelModes

if __name__ == "__main__":
    t1 = Target(2, 2, PVLM.NOTE, 2)
    t2 = Target(2, 4, PVLM.NOTE, 2)
    print(t1 == t2)
