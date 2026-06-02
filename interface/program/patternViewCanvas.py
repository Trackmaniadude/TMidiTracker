"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from interface.program.patternViewUtils import PVLM, PatternViewLabelModes, Target
from utils.event import Connection

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from interface.program.patternViewFrame import PatternViewFrame

import logging
import tkinter as tk
from tkinter import ttk

import mido

from interface.theme import Colors
from interface.utilities.prebuilts import Buttons
from structures import program
from structures.globalEvents import StructureChanged
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
from utils.types_ import *

_logger = logging.getLogger(__name__)

ASPECT = 12 / 20

ROW_HEIGHT = 20
CHAR_WIDTH = int(ROW_HEIGHT * ASPECT)

NOTE_WIDTH = CHAR_WIDTH * 3
VEL_WIDTH = CHAR_WIDTH * 2
NOTEVEL_WIDTH = NOTE_WIDTH + VEL_WIDTH
EFFECT_WIDTH = CHAR_WIDTH * 4


BIG = 999999


class Tags:
    GRID_LIGHT = "GRID_LIGHT"
    GRID_DARK = "GRID_DARK"
    HIGHLIGHT_MINOR = "HIGHLIGHT_MINOR"
    HIGHLIGHT_MAJOR = "HIGHLIGHT_MAJOR"


class PatternViewCanvas(ttk.Frame):
    """Display/edit the data of a single pattern."""

    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=2, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.connections: list[Connection] = list()

        ### Build Layout
        # Frames
        self.noteFrame = ttk.Frame(
            self, relief="sunken", borderwidth=2, width=0, height=0
        )
        self.effectFrame = ttk.Frame(
            self, relief="sunken", borderwidth=2, width=0, height=0
        )

        # Labels
        self.noteLabel = ttk.Label(self, text=f"#{self.pattern.channel.channel + 1}")
        self.effectLabel = ttk.Label(self, text="")

        # Controls
        self.noteDel = Buttons.Decrement(self)
        self.noteAdd = Buttons.Increment(self)
        self.effectDel = Buttons.Decrement(self)
        self.effectAdd = Buttons.Increment(self)

        # Layout
        self.noteLabel.grid(row=0, column=0, sticky="ew")
        self.noteDel.grid(row=0, column=1, sticky="ew")
        self.noteAdd.grid(row=0, column=2, sticky="ew")

        self.effectLabel.grid(row=0, column=3, sticky="ew")
        self.effectDel.grid(row=0, column=4, sticky="ew")
        self.effectAdd.grid(row=0, column=5, sticky="ew")

        self.noteFrame.grid(row=1, column=0, columnspan=3)
        self.effectFrame.grid(row=1, column=3, columnspan=3)

        self.columnconfigure([0, 3], weight=1)

        ### Behavior
        self.noteDel.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "noteColumns",
                    getattr(self.pattern.channel, "noteColumns") - 1,
                ),
                self.buildLabels(),
            )
        )
        self.noteAdd.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "noteColumns",
                    getattr(self.pattern.channel, "noteColumns") + 1,
                ),
                self.buildLabels(),
            )
        )
        self.effectDel.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "effectColumns",
                    getattr(self.pattern.channel, "effectColumns") - 1,
                ),
                self.buildLabels(),
            )
        )
        self.effectAdd.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "effectColumns",
                    getattr(self.pattern.channel, "effectColumns") + 1,
                ),
                self.buildLabels(),
            )
        )

        StructureChanged.connect(
            lambda changes: (
                (self.buildLabels(), self.refreshLabels())
                if "patternLength" in changes
                else None
            ),
            self.connections,
        )

        ### Finish
        self.buildLabels()

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def buildLabels(self):
        """Build interface"""
        # Easier to just replace the frames
        if hasattr(self, "noteCanvas"):
            self.noteCanvas.destroy()
            self.effectCanvas.destroy()
        self.noteCanvas = tk.Canvas(
            self.noteFrame,
            highlightthickness=0,
            width=0,
            height=0,
            background=Colors.BG.Default,
        )
        self.effectCanvas = tk.Canvas(
            self.effectFrame,
            highlightthickness=0,
            width=0,
            height=0,
            background=Colors.BG.Default,
        )
        self.noteCanvas.pack(fill="both", expand=True)
        self.effectCanvas.pack(fill="both", expand=True)

        rows = program.p.currentSong.patternLength
        notes = self.pattern.channel.noteColumns
        effects = self.pattern.channel.effectColumns

        self.noteCanvas.config(width=NOTEVEL_WIDTH * notes, height=ROW_HEIGHT * rows)
        self.effectCanvas.config(width=EFFECT_WIDTH * effects, height=ROW_HEIGHT * rows)

        for row in range(rows):
            y1 = row * ROW_HEIGHT
            y2 = ((row + 1) * ROW_HEIGHT) - 1
            self.noteCanvas.create_line(0, y1, BIG, y1, tags=[Tags.GRID_LIGHT])
            self.noteCanvas.create_line(0, y2, BIG, y2, tags=[Tags.GRID_DARK])
            self.effectCanvas.create_line(0, y1, BIG, y1, tags=[Tags.GRID_LIGHT])
            self.effectCanvas.create_line(0, y2, BIG, y2, tags=[Tags.GRID_DARK])

            if row % program.p.currentSong.majorSubdiv == 0:
                self.noteCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MAJOR]
                )
                self.effectCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MAJOR]
                )
            elif row % program.p.currentSong.minorSubdiv == 0:
                self.noteCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MINOR]
                )
                self.effectCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MINOR]
                )

        for col in range(notes):
            x1 = col * NOTEVEL_WIDTH
            x2 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH - 1
            x3 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH
            x4 = ((col + 1) * NOTEVEL_WIDTH) - 1
            self.noteCanvas.create_line(x1, 0, x1, BIG, tags=[Tags.GRID_LIGHT])
            self.noteCanvas.create_line(x2, 0, x2, BIG, tags=[Tags.GRID_DARK])
            self.noteCanvas.create_line(x3, 0, x3, BIG, tags=[Tags.GRID_LIGHT])
            self.noteCanvas.create_line(x4, 0, x4, BIG, tags=[Tags.GRID_DARK])

        for col in range(effects):
            x1 = col * EFFECT_WIDTH
            x2 = ((col + 1) * EFFECT_WIDTH) - 1
            self.effectCanvas.create_line(x1, 0, x1, BIG, tags=[Tags.GRID_LIGHT])
            self.effectCanvas.create_line(x2, 0, x2, BIG, tags=[Tags.GRID_DARK])

        self.__paint()

        self.refreshLabels()

    def __paint(self):
        def p(c: tk.Canvas):
            # Colors
            c.itemconfig(Tags.HIGHLIGHT_MINOR, fill=Colors.BG.Shade1)
            c.itemconfig(Tags.HIGHLIGHT_MAJOR, fill=Colors.BG.Shade2)
            c.itemconfig(Tags.GRID_LIGHT, fill=Colors.Grid.Highlight)
            c.itemconfig(Tags.GRID_DARK, fill=Colors.Grid.Shadow)

            # Order
            c.tag_raise(Tags.HIGHLIGHT_MINOR)
            c.tag_raise(Tags.HIGHLIGHT_MAJOR)
            c.tag_raise(Tags.GRID_DARK)
            c.tag_raise(Tags.GRID_LIGHT)

        p(self.noteCanvas)
        p(self.effectCanvas)

    def refreshLabels(self):
        """Sync interface with model"""

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.buildLabels()
        self.refreshLabels()
