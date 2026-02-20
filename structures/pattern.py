"""
Pattern object. Contains message data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel

import logging
from dataclasses import dataclass

from structures import program
from utils.misc import clamp
from utils.reactiveClass import ReactiveClass
from utils.types_ import *

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

        self.song = song
        self.channel = channel

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
            del self.notes[row, column]
        if velocity is not None:
            self.velocities[row, column] = clamp(velocity, 0, 127)

    def getEffect(self, row: int, column: int) -> effect | None:
        return self.effects.get((row, column))

    def setEffect(self, row: int, column: int, effect: effect | None):
        if effect is None and (row, column) in self.effects:
            del self.effects[row, column]
        if effect is not None:
            self.effects[row, column] = effect
