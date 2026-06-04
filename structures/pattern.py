"""
Pattern object. Contains message data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from structures import program
from utils.misc import clamp, intKey2dFromJson, intKey2dToJson
from utils.reactiveClass import ReactiveClass
from utils.types_ import *

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.song import Song

_logger = logging.getLogger(__name__)


@dataclass
class PatternRow:
    notes: dict[int, note]
    velocities: dict[int, velocity]
    effects: dict[int, effect]


class Pattern(ReactiveClass):
    """
    Contains pattern data, such as notes and effects.
    """

    def __init__(self, song: Song, channel: Channel) -> None:
        super().__init__()

        self.song: Song = song
        self.channel: Channel = channel

        self.notes: dict[tuple[int, int], note] = dict()
        """
        Play note/stop note commands. (Does not directly map to midi)
        (row, col) -> (int # | 'stop')
        """
        self.velocities: dict[tuple[int, int], velocity] = dict()
        """
        Note velocities. Notes use the most recent velocity command.
        (row, col) -> int
        """
        self.effects: dict[tuple[int, int], effect] = dict()
        """
        Tracker effects, like vibrato and playback control. Some effects may map to midi messages.
        (row, col) -> (int, ...)
        """

        self.Changed.connect(
            lambda name, key, old, new: setattr(program.p, "projectModified", True)
        )

        self.setupContainerListen()

    # def __repr__(self) -> str:
    #     return f"Pattern(channel: {self.channel}, noteColumns: {self.noteColumns}, effectColumns: {self.effectColumns})"

    def __str__(self) -> str:
        return f"Pattern({self.notes}, {self.velocities}, {self.effects})"

    EQ_KEYS = [
        "notes",
        "velocities",
        "effects",
    ]

    def __eq__(self, value: object) -> bool:
        return True
        # if isinstance(value, Channel):
        #     return all(getattr(self, k) == getattr(value, k) for k in self.EQ_KEYS)
        # return False

    def toDict(self) -> dict[str, Any]:
        return {
            "notes": {intKey2dToJson(k): v for k, v in self.notes.items()},
            "velocities": {intKey2dToJson(k): v for k, v in self.velocities.items()},
            "effects": {intKey2dToJson(k): v for k, v in self.effects.items()},
        }

    @classmethod
    def fromDict(cls, song: Song, channel: Channel, dct: dict[str, Any]) -> Pattern:
        out = Pattern(song, channel)
        out.updateFromDict(dct)
        return out

    def updateFromDict(self, dct: dict[str, Any]):
        """Update this pattern from a dictionary. (Intended for JSON import.)"""
        self.notes = {intKey2dFromJson(k): v for k, v in dct["notes"].items()}
        self.velocities = {intKey2dFromJson(k): v for k, v in dct["velocities"].items()}
        self.effects = {
            intKey2dFromJson(k): tuple(v) for k, v in dct["effects"].items()
        }
        self.setupContainerListen()

    def getRow(self, row: int) -> PatternRow:
        """Get all data from a row."""
        return PatternRow(
            {p[1]: n for p, n in self.notes.items() if p[0] == row},
            {p[1]: v for p, v in self.velocities.items() if p[0] == row},
            {p[1]: f for p, f in self.effects.items() if p[0] == row},
        )

    def getNote(self, row: int, column: int) -> note | None:
        return self.notes.get((row, column))

    def setNote(self, row: int, column: int, note: note | None):
        if note is None and (row, column) in self.notes:
            del self.notes[row, column]
        if note is not None:
            if type(note) is int:
                self.notes[row, column] = clamp(note, 0, 127)
            else:
                self.notes[row, column] = note

    def getVelocity(self, row: int, column: int) -> velocity | None:
        return self.velocities.get((row, column))

    def setVelocity(self, row: int, column: int, velocity: velocity | None):
        if velocity is None and (row, column) in self.velocities:
            del self.velocities[row, column]
        if velocity is not None:
            self.velocities[row, column] = clamp(velocity, 0, 127)

    def getEffect(self, row: int, column: int) -> effect | None:
        return self.effects.get((row, column))

    def setEffect(self, row: int, column: int, effect: effect | None):
        if effect is None and (row, column) in self.effects:
            del self.effects[row, column]
        if effect is not None:
            self.effects[row, column] = effect
