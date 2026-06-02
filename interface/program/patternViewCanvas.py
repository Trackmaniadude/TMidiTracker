"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal, cast

from interface.program.patternViewUtils import PVLM, PatternViewLabelModes, Target
from utils.event import Connection

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from interface.program.patternViewFrame import PatternViewFrame

import logging
import tkinter as tk
from tkinter import ttk

import mido

import utils.tk as tkutil
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
FONT_SCALE = 0.5

ROW_HEIGHT = 20
CHAR_WIDTH = int(ROW_HEIGHT * ASPECT)
FONT_SIZE = int(ROW_HEIGHT * FONT_SCALE)

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
    SELECTION = "SELECTION"
    CURSOR = "CURSOR"


# In stacking order, so top is highest.
TAG_COLORS: dict[str, str] = {
    Tags.GRID_LIGHT: Colors.Grid.Highlight,
    Tags.GRID_DARK: Colors.Grid.Shadow,
    Tags.SELECTION: Colors.Target.Default,
    Tags.CURSOR: Colors.Target.Shade2,
    Tags.HIGHLIGHT_MAJOR: Colors.BG.Shade2,
    Tags.HIGHLIGHT_MINOR: Colors.BG.Shade1,
}
"""Colors for each tag, and also the order to stack them."""


# TODO: Probably more effort than it was worth.
# I should get that nice canvas up and running some time cause it does this for all
class ResourcePool[ID]:
    def __init__(self, get: Callable[[], ID], free: Callable[[ID], None]) -> None:
        self.__free = set[ID]()
        self.__used = set[ID]()
        self.__newFunc = get
        self.__freeFunc = free

    def get(self) -> ID:
        if len(self.__free) > 0:
            id = self.__free.pop()
        else:
            id = self.__newFunc()
        self.__used.add(id)
        return id

    def free(self, id: ID):
        self.__used.remove(id)
        self.__freeFunc(id)


class PatternViewCanvas(ttk.Frame):
    """Display/edit the data of a single pattern."""

    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=2, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.connections = list[Connection]()

        ### Build Layout
        # Frames
        self.noteFrame = ttk.Frame(
            self, relief="sunken", borderwidth=2, width=0, height=0
        )
        self.effectFrame = ttk.Frame(
            self, relief="sunken", borderwidth=2, width=0, height=0
        )
        self.noteCanvas: tk.Canvas
        self.effectCanvas: tk.Canvas

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

    @staticmethod
    def row(row: int) -> tuple[int, int]:
        """Get y coords of row. Returns (y1, y2)"""
        y1 = row * ROW_HEIGHT
        y2 = ((row + 1) * ROW_HEIGHT) - 1
        return (y1, y2)

    @staticmethod
    def col(col: int, t: Literal["note", "velocity", "effect"]) -> tuple[int, int]:
        """Get x coords of column. Returns (x1, x2)"""
        if t == "note":
            x1 = col * NOTEVEL_WIDTH
            x2 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH - 1
        elif t == "velocity":
            x1 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH
            x2 = ((col + 1) * NOTEVEL_WIDTH) - 1
        elif t == "effect":
            x1 = col * EFFECT_WIDTH
            x2 = ((col + 1) * EFFECT_WIDTH) - 1
        return (x1, x2)

    @classmethod
    def coords(
        cls, row: int, col: int, t: Literal["note", "velocity", "effect"]
    ) -> tuple[int, int, int, int]:
        """Get cell coordinates. Returns (x1, y1, x2, y2)"""
        x1, x2 = cls.col(col, t)
        y1, y2 = cls.row(row)
        return (x1, y1, x2, y2)

    @tkutil.tkQueuedAction()
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

        def canvasPools(canvas: tk.Canvas):
            def new() -> int:
                return canvas.create_text(
                    -BIG, -BIG, font=("TkFixedFont", FONT_SIZE), anchor="nw"
                )

            def free(id: int):
                canvas.itemconfig(id, text="")
                canvas.coords(id, -BIG, -BIG)

            return (new, free)

        self.noteText = ResourcePool[int](*canvasPools(self.noteCanvas))
        self.effectText = ResourcePool[int](*canvasPools(self.noteCanvas))

        # Setup constant display items
        rows = program.p.currentSong.patternLength
        notes = self.pattern.channel.noteColumns
        effects = self.pattern.channel.effectColumns

        self.noteCanvas.config(width=NOTEVEL_WIDTH * notes, height=ROW_HEIGHT * rows)
        self.effectCanvas.config(width=EFFECT_WIDTH * effects, height=ROW_HEIGHT * rows)

        self.textLookup = dict[
            tuple[int, int, Literal["note", "velocity", "effect"]], int
        ]()
        """(row, col, col_t) -> id"""

        for row in range(rows):
            y1, y2 = self.row(row)
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
            x1, x2 = self.col(col, "note")
            x3, x4 = self.col(col, "velocity")
            self.noteCanvas.create_line(x1, 0, x1, BIG, tags=[Tags.GRID_LIGHT])
            self.noteCanvas.create_line(x2, 0, x2, BIG, tags=[Tags.GRID_DARK])
            self.noteCanvas.create_line(x3, 0, x3, BIG, tags=[Tags.GRID_LIGHT])
            self.noteCanvas.create_line(x4, 0, x4, BIG, tags=[Tags.GRID_DARK])

        for col in range(effects):
            x1, x2 = self.col(col, "effect")
            self.effectCanvas.create_line(x1, 0, x1, BIG, tags=[Tags.GRID_LIGHT])
            self.effectCanvas.create_line(x2, 0, x2, BIG, tags=[Tags.GRID_DARK])

        # Color and sync
        for canvas in (self.noteCanvas, self.effectCanvas):
            for tag, color in TAG_COLORS.items():
                canvas.itemconfig(tag, fill=color)
                canvas.tag_lower(tag)

        self.refreshLabels()

    @tkutil.tkQueuedAction()
    def refreshLabels(self):
        """Sync interface with model"""
        for (row, col), note in self.pattern.notes.items():
            id = self.textLookup.get((row, col, "note")) or self.noteText.get()
            self.textLookup[row, col, "note"] = id

            x, y, _, _ = self.coords(row, col, "note")
            self.noteCanvas.coords(id, x + 2, y)
            if self.pattern.channel.channel == DRUM_CHANNEL:
                text = "STP" if note == "stop" else DRUM_NAMES[note]
            else:
                text = (
                    "STP"
                    if note == "stop"
                    else f"{NOTE_NAMES_SHARP[note % NOTES_PER_OCTAVE]}{note // NOTES_PER_OCTAVE}"
                )
            self.noteCanvas.itemconfig(id, text=text)

        for (row, col), velocity in self.pattern.velocities.items():
            id = self.textLookup.get((row, col, "velocity")) or self.noteText.get()
            self.textLookup[row, col, "velocity"] = id

            x, y, _, _ = self.coords(row, col, "velocity")
            self.noteCanvas.coords(id, x + 2, y)
            self.noteCanvas.itemconfig(id, text=velocity)

        for (row, col), effect in self.pattern.effects.items():
            id = self.textLookup.get((row, col, "effect")) or self.effectText.get()
            self.textLookup[row, col, "effect"] = id

            x, y, _, _ = self.coords(row, col, "effect")
            self.effectCanvas.coords(id, x + 2, y)
            self.effectCanvas.itemconfig(id, text=effect)

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.refreshLabels()
