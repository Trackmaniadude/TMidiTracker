"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

import logging
import tkinter as tk
from functools import cached_property
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, Literal

import mido

import utils.tk as tkutil
from interface.program.patternViewUtils import PVLM, PatternViewLabelModes, Target
from interface.theme import Colors
from interface.utilities.prebuilts import Buttons
from structures import program
from structures.globalEvents import Copy, Cut, Paste, StructureChanged
from utils.constants import (
    CHANNEL_ORDER_INVERSE,
    DRUM_CHANNEL,
    DRUM_NAMES,
    HEX_KEYMAP,
    KEYBOARD_MAP,
    MAX_VELOCITY,
    NOTE_DELTAS,
    NOTE_NAMES_FLAT,
    NOTE_NAMES_SHARP,
    NOTES_PER_OCTAVE,
    VALUE_DELTAS,
)
from utils.event import Connection
from utils.misc import clamp, hex2, minmax
from utils.types_ import *

if TYPE_CHECKING:
    from interface.program.patternViewFrame import PatternViewFrame
    from structures.pattern import Pattern

_logger = logging.getLogger(__name__)

ASPECT = 8 / 20
FONT_SCALE = 0.5

ROW_HEIGHT = 21
CHAR_WIDTH = int(ROW_HEIGHT * ASPECT)
FONT_SIZE = int(ROW_HEIGHT * FONT_SCALE)

WIDTH_PAD = 4
WIDTH_PAD_H = WIDTH_PAD // 2

NOTE_WIDTH = (CHAR_WIDTH * 3) + WIDTH_PAD
VEL_WIDTH = (CHAR_WIDTH * 2) + WIDTH_PAD
NOTEVEL_WIDTH = NOTE_WIDTH + VEL_WIDTH
EFFECT_WIDTH = (CHAR_WIDTH * 6) + WIDTH_PAD

BIG = 999999

EFFECT_COL_MIN_WIDTH = 3


class Tags:
    GRID_LIGHT = "GRID_LIGHT"
    GRID_DARK = "GRID_DARK"
    HIGHLIGHT_MINOR = "HIGHLIGHT_MINOR"
    HIGHLIGHT_MAJOR = "HIGHLIGHT_MAJOR"
    SELECTION = "SELECTION"
    CURSOR = "CURSOR"
    TARGET = "TARGET"


# In stacking order, so top is highest.
TAG_COLORS: dict[str, str] = {
    Tags.GRID_LIGHT: Colors.Grid.Highlight,
    Tags.GRID_DARK: Colors.Grid.Shadow,
    Tags.SELECTION: Colors.Target.Default,
    Tags.CURSOR: Colors.Highlight.Default,
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
        self.__used.discard(id)
        self.__freeFunc(id)
        self.__free.add(id)


PVLM_TO_STR: dict[PatternViewLabelModes, Literal["note", "velocity", "effect"]] = {
    PVLM.NOTE: "note",
    PVLM.VELOCITY: "velocity",
    PVLM.EFFECT: "effect",
}


# TODO: clean up this class, it feels a bit messy
class PatternViewCanvas(ttk.Frame):
    """Display/edit the data of a single pattern."""

    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=2, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.connections = list[Connection]()
        """Connections that exist for the lifetime of the view."""
        self.patternConnections = list[Connection]()
        """Connections from the current target pattern. Are swapped out with the pattern."""

        self.entryTarget: Target | None = None
        self.entryText: str = ""
        self.entryId: int = -1

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
        self.noteLabel = ttk.Label(self, text=f"#{self.channel + 1}")
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
                self.buildStaticElements(),
            )
        )
        self.noteAdd.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "noteColumns",
                    getattr(self.pattern.channel, "noteColumns") + 1,
                ),
                self.buildStaticElements(),
            )
        )
        self.effectDel.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "effectColumns",
                    getattr(self.pattern.channel, "effectColumns") - 1,
                ),
                self.buildStaticElements(),
            )
        )
        self.effectAdd.config(
            command=lambda: (
                setattr(
                    self.pattern.channel,
                    "effectColumns",
                    getattr(self.pattern.channel, "effectColumns") + 1,
                ),
                self.buildStaticElements(),
            )
        )

        # Event Listens
        StructureChanged.connect(
            lambda changes: (
                (self.buildStaticElements(), self.refresh())
                if "patternLength" in changes
                else None
            ),
            self.connections,
        )

        program.p.getAttributeChangedEvent("currentPatternRow").connect(
            lambda *_: self.onPatternRowChange(), self.connections
        )

        # Changing the song initiates a patternViewFrame rebuild, so we don't have to worry about this going out of sync.
        # Ideally.
        program.p.currentSong.getAttributeChangedEvent("patternMatrix").connect(
            self.onPatternChange, self.connections
        )

        self.viewFrame.TargetChanged.connect(
            lambda *_: self.onTargetChange(), self.connections
        )

        ### Finish
        self.buildStaticElements()
        self.setPattern(initialPattern)

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    # region Indexing

    def row(self, row: int) -> tuple[int, int]:
        """Get y coords of row. Returns (y1, y2)"""
        y1 = row * ROW_HEIGHT
        y2 = ((row + 1) * ROW_HEIGHT) - 1
        return (y1, y2)

    def col(
        self, col: int, t: Literal["note", "velocity", "effect"]
    ) -> tuple[int, int]:
        """Get x coords of column. Returns (x1, x2)"""
        if t == "note":
            x1 = col * NOTEVEL_WIDTH
            x2 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH - 1
        elif t == "velocity":
            x1 = (col * NOTEVEL_WIDTH) + NOTE_WIDTH
            x2 = ((col + 1) * NOTEVEL_WIDTH) - 1
        elif t == "effect":
            x1 = sum(self.effectWidths[:col])
            x2 = sum(self.effectWidths[: col + 1]) - 1
        return (x1, x2)

    def coords(
        self, row: int, col: int, t: Literal["note", "velocity", "effect"]
    ) -> tuple[int, int, int, int]:
        """Get cell coordinates. Returns (x1, y1, x2, y2)"""
        x1, x2 = self.col(col, t)
        y1, y2 = self.row(row)
        return (x1, y1, x2, y2)

    def rowInv(self, y: int) -> int:
        return y // ROW_HEIGHT

    def colInv(
        self, x: int, c: tk.Canvas
    ) -> tuple[int, Literal["note", "velocity", "effect"]]:
        if c == self.noteCanvas:
            col = x // NOTEVEL_WIDTH
            return (col, "note" if x % NOTEVEL_WIDTH < NOTE_WIDTH else "velocity")
        elif c == self.effectCanvas:
            xt = 0
            for col, w in enumerate(self.effectWidths):
                xt += w
                if x < xt:
                    return (col, "effect")
            return (0, "effect")
        raise Exception

    def cell(
        self, x: int, y: int, c: tk.Canvas
    ) -> tuple[int, int, Literal["note", "velocity", "effect"]]:
        """Get cell from coordinates. Returns (row, col)"""
        row = self.rowInv(y)
        col, t = self.colInv(x, c)
        return (row, col, t)

    # endregion

    def onPatternChange(self, key, old, new):
        col, row = (
            key  # TODO: go back through and make everything the same order of row, col
        )
        if col != self.channel:
            return
        if row != program.p.currentMatrixRow:
            return
        self.setPattern(program.p.currentSong.getPatternByLocation(col, row))

    def onPatternRowChange(self):
        row = program.p.currentPatternRow
        y1, y2 = self.row(row)
        self.noteCanvas.coords(Tags.CURSOR, 0, y1, BIG, y2)
        self.effectCanvas.coords(Tags.CURSOR, 0, y1, BIG, y2)

    def onTargetChange(self):
        self.doTargetVisual()
        if self.entryTarget is not None:
            if self.target != self.entryTarget:
                self.finalizeEntry()

    def doTargetVisual(self):
        t1, t2 = minmax(
            self.viewFrame.target,
            self.viewFrame.secondaryTarget,
            key=lambda t: t.horizontalComparisonKeyView,
        )
        ch = CHANNEL_ORDER_INVERSE[self.channel]
        ch1, ch2 = CHANNEL_ORDER_INVERSE[t1.channel], CHANNEL_ORDER_INVERSE[t2.channel]

        # Target
        mainTarget = self.viewFrame.target
        if ch == CHANNEL_ORDER_INVERSE[mainTarget.channel]:
            col_t = PVLM_TO_STR[mainTarget.column]
            row = mainTarget.row
            col = mainTarget.subcolumn
            if col_t == "effect":
                self.noteCanvas.coords(Tags.TARGET, -BIG, -BIG, -BIG, -BIG)
                self.effectCanvas.coords(Tags.TARGET, *self.coords(row, col, col_t))
                self.noteCanvas.focus()
            else:
                self.noteCanvas.coords(Tags.TARGET, *self.coords(row, col, col_t))
                self.effectCanvas.coords(Tags.TARGET, -BIG, -BIG, -BIG, -BIG)
                self.effectCanvas.focus()
        else:
            self.noteCanvas.coords(Tags.TARGET, -BIG, -BIG, -BIG, -BIG)
            self.effectCanvas.coords(Tags.TARGET, -BIG, -BIG, -BIG, -BIG)

        # Do not show if selection does not cross this channel
        if ch < ch1:
            self.noteCanvas.coords(Tags.SELECTION, -BIG, -BIG, -BIG, -BIG)
            self.effectCanvas.coords(Tags.SELECTION, -BIG, -BIG, -BIG, -BIG)
            return
        if ch > ch2:
            self.noteCanvas.coords(Tags.SELECTION, -BIG, -BIG, -BIG, -BIG)
            self.effectCanvas.coords(Tags.SELECTION, -BIG, -BIG, -BIG, -BIG)
            return

        c1 = t1.subcolumn
        c2 = t2.subcolumn

        ct1 = PVLM_TO_STR[t1.column]
        ct2 = PVLM_TO_STR[t2.column]

        r1, r2 = minmax(t1.row, t2.row)

        y1, _ = self.row(r1)
        _, y2 = self.row(r2)

        if ch > ch1:
            # Lower selection is in a channel to the left
            x1n = 0
            x1e = 0
        elif ch == ch1:
            if ct1 == "effect":
                x1n = BIG
                x1e = self.col(c1, ct1)[0]
            else:
                x1n = self.col(c1, ct1)[0]
                x1e = 0
        else:
            raise Exception()

        if ch < ch2:
            # Upper selection is in a channel to the right
            x2n = BIG
            x2e = BIG
        elif ch == ch2:
            if ct2 == "effect":
                x2n = BIG
                x2e = self.col(c2, ct2)[1]
            else:
                x2n = self.col(c2, ct2)[1]
                x2e = 0
        else:
            raise Exception()

        self.noteCanvas.coords(Tags.SELECTION, x1n, y1, x2n, y2)
        self.effectCanvas.coords(Tags.SELECTION, x1e, y1, x2e, y2)

    @property
    def channel(self):
        return self.pattern.channel.channel

    @property
    def target(self):
        return self.viewFrame.target

    def finalizeEntry(self):
        target = self.entryTarget
        if target is None:
            return

        # Velocity
        if target.column == PVLM.VELOCITY:
            value = int(self.entryText, base=16)
            value = clamp(value, 0, MAX_VELOCITY)
            self.pattern.setVelocity(target.row, target.subcolumn, value)

        # Effect
        if target.column == PVLM.EFFECT:
            if self.entryText == "":
                self.pattern.setEffect(target.row, target.subcolumn, None)
                return
            values = list[int]()
            t = self.entryText
            if len(t) % 2 == 1:
                t = "0" + t
            values = tuple(int(t[i : i + 2], 16) for i in range(0, len(t), 2))
            self.pattern.setEffect(target.row, target.subcolumn, values)

        # Reset Entry
        self.entryTarget = None
        self.entryText = ""  # Technically don't need to as entrytarget is the marker
        self.entryId = -1
        self.refresh()

    def initEntry(self, target: Target | None = None):
        self.entryTarget = target or self.target

        row = self.entryTarget.row
        col = self.entryTarget.subcolumn
        col_t = PVLM_TO_STR[self.entryTarget.column]

        canvas = self.effectCanvas if col_t == "effect" else self.noteCanvas

        id = self.textLookup.get((row, col, col_t)) or (
            self.effectText.get() if col_t == "effect" else self.noteText.get()
        )
        self.textLookup[row, col, col_t] = id

        x, y, _, _ = self.coords(row, col, col_t)
        canvas.coords(id, x + WIDTH_PAD_H, y)
        canvas.itemconfig(id, text="")

        self.entryText = ""
        self.entryId = id

    def canvasBindings(self, canvas: tk.Canvas):
        def onClick(boxSelect: bool):
            def f(event: tk.Event):
                x = event.x
                y = event.y
                row, col, col_t = self.cell(x, y, canvas)
                lookup = {
                    "note": PVLM.NOTE,
                    "velocity": PVLM.VELOCITY,
                    "effect": PVLM.EFFECT,
                }
                self.viewFrame.setTarget(
                    self.channel, row, lookup[col_t], col, boxSelect=boxSelect
                )

            return f

        # Mouse interaction
        canvas.bind("<Button-1>", onClick(False))
        canvas.bind("<Shift-Button-1>", onClick(True))

        # Entries
        def createNoteEventHandlers(key: str, noteOffset: int):
            def noteOn(*_):
                if self.target.column != PVLM.NOTE:
                    return
                note = (program.p.currentOctave * NOTES_PER_OCTAVE) + noteOffset
                if program.p.playbackInEdit:
                    message = mido.Message(
                        "note_on", channel=self.channel, note=note, velocity=64
                    )
                    program.p.currentPort.send(message)
                if program.p.allowEditingPattern:
                    self.pattern.setNote(self.target.row, self.target.subcolumn, note)
                    self.viewFrame.stepTarget(program.p.stepSize)

            def noteOff(*_):
                if self.target.column != PVLM.NOTE:
                    return
                note = (program.p.currentOctave * NOTES_PER_OCTAVE) + noteOffset
                if program.p.playbackInEdit:
                    message = mido.Message(
                        "note_off", channel=self.channel, note=note, velocity=0
                    )
                    program.p.currentPort.send(message)

            canvas.bind(f"<KeyPress-{key}>", noteOn)
            canvas.bind(f"<KeyRelease-{key}>", noteOff)

        def createVelocityEventHandlers(key: str):
            if canvas != self.noteCanvas:
                return

            def e(*_):
                if self.target.column != PVLM.VELOCITY:
                    return
                if self.entryTarget is None:
                    # begin entry
                    self.initEntry()
                    self.entryText += key
                    self.noteCanvas.itemconfig(self.entryId, text=self.entryText)
                else:
                    self.entryText += key
                    self.noteCanvas.itemconfig(self.entryId, text=self.entryText)
                    enter()

            canvas.bind(key, e, "+")

        def createEffectEventHandlers(key: str):
            if canvas != self.effectCanvas:
                return

            def e(*_):
                if self.target.column != PVLM.EFFECT:
                    return
                if self.entryTarget is None:
                    # begin entry
                    self.initEntry()
                    self.entryText += key
                    self.effectCanvas.itemconfig(self.entryId, text=self.entryText)
                    self.refresh()
                else:
                    self.entryText += key
                    self.effectCanvas.itemconfig(self.entryId, text=self.entryText)
                    self.refresh()

            canvas.bind(key, e, "+")

        for key, noteOffset in KEYBOARD_MAP.items():
            createNoteEventHandlers(key, noteOffset)
        for key in HEX_KEYMAP:
            createVelocityEventHandlers(key)
            createEffectEventHandlers(key)

        def delete():
            if self.target.column == PVLM.NOTE:
                self.pattern.setNote(self.target.row, self.target.subcolumn, None)
                self.viewFrame.stepTarget(program.p.stepSize, stepPattern=False)
            elif self.target.column == PVLM.VELOCITY:
                self.pattern.setVelocity(self.target.row, self.target.subcolumn, None)
                self.viewFrame.stepTarget(program.p.stepSize, stepPattern=False)
            elif self.target.column == PVLM.EFFECT:
                self.pattern.setEffect(self.target.row, self.target.subcolumn, None)
                self.viewFrame.stepTarget(program.p.stepSize, stepPattern=False)

        def backspace():
            if self.target.column == PVLM.NOTE:
                target = max(0, self.target.row - program.p.stepSize)
                self.pattern.setNote(target, self.target.subcolumn, None)
                self.viewFrame.setTarget(row=target)
            elif self.target.column == PVLM.VELOCITY:
                target = max(0, self.target.row - program.p.stepSize)
                self.pattern.setVelocity(target, self.target.subcolumn, None)
                self.viewFrame.setTarget(row=target)
            elif self.target.column == PVLM.EFFECT:
                # If we're on a blank space, just backspace as normal.
                # If we're on a filled space, start editing it.
                effect = self.pattern.getEffect(self.target.row, self.target.subcolumn)
                if effect == ():
                    effect = None
                if effect is None:
                    target = max(0, self.target.row - program.p.stepSize)
                    self.pattern.setEffect(target, self.target.subcolumn, None)
                    self.viewFrame.setTarget(row=target)
                else:
                    if self.entryTarget is None:
                        self.initEntry()
                        t = "".join(hex2(byte) for byte in effect)
                        self.entryText = t[:-1]
                        self.effectCanvas.itemconfig(self.entryId, text=self.entryText)
                        self.refresh()
                    else:
                        self.entryText = self.entryText[:-1]
                        self.effectCanvas.itemconfig(self.entryId, text=self.entryText)
                        self.refresh()

        def stop():
            if self.target.column == PVLM.NOTE:
                self.pattern.setNote(self.target.row, self.target.subcolumn, "stop")
                self.viewFrame.stepTarget(program.p.stepSize, stepPattern=False)

        def enter():
            # No separate behavior as that is handled on target leave
            self.viewFrame.stepTarget(program.p.stepSize, stepPattern=False)

        canvas.bind(f"<Tab>", lambda *_: stop())
        canvas.bind(f"<BackSpace>", lambda *_: backspace())
        canvas.bind(f"<Delete>", lambda *_: delete())
        canvas.bind(f"<Return>", lambda *_: enter())

        # Keyboard navigation
        for dir in ("Up", "Down", "Left", "Right"):
            # Nonsense because scoping again
            f = lambda d, s, p: lambda *_: self.viewFrame.stepTarget(
                1, p, direction=d, boxSelect=s
            )
            canvas.bind(f"<{dir}>", f(dir, False, True))
            canvas.bind(f"<Shift-{dir}>", f(dir, True, False))

        canvas.bind(
            "<FocusOut>", lambda *_: canvas.coords(Tags.TARGET, -BIG, -BIG, -BIG, -BIG)
        )

        # Increment/Decrement
        def adjust(dir: Literal[-1, 1], scale: int):
            if self.viewFrame.target.column == PVLM.NOTE:
                notes, _, _ = self.viewFrame.getUsedIndicesInSelection()
                for channel, row, column in notes:
                    pattern = program.p.currentSong.getPatternByLocation(
                        channel, program.p.currentMatrixRow
                    )
                    currentNote = pattern.getNote(row, column)
                    if currentNote is None:
                        break
                    if currentNote == "stop":
                        break
                    pattern.setNote(
                        row, column, currentNote + (NOTE_DELTAS[scale] * dir)
                    )
                self.viewFrame.refresh()
            elif self.viewFrame.target.column == PVLM.VELOCITY:
                _, velocities, _ = self.viewFrame.getUsedIndicesInSelection()
                for channel, row, column in velocities:
                    pattern = program.p.currentSong.getPatternByLocation(
                        channel, program.p.currentMatrixRow
                    )
                    currentVelocity = pattern.getVelocity(row, column)
                    if currentVelocity is None:
                        break
                    pattern.setVelocity(
                        row, column, currentVelocity + (VALUE_DELTAS[scale] * dir)
                    )
                self.viewFrame.refresh()

        canvas.bind("<equal>", lambda *_: adjust(1, 0))
        canvas.bind("<minus>", lambda *_: adjust(-1, 0))
        canvas.bind("<plus>", lambda *_: adjust(1, 1))
        canvas.bind("<underscore>", lambda *_: adjust(-1, 1))
        canvas.bind("<Control-equal>", lambda *_: adjust(1, 2))
        canvas.bind("<Control-minus>", lambda *_: adjust(-1, 2))

        # Copy/Pase
        canvas.bind("<Control-x>", lambda *_: Cut.fire(self))
        canvas.bind("<Control-c>", lambda *_: Copy.fire(self))
        canvas.bind("<Control-v>", lambda *_: Paste.fire(self))

    @tkutil.tkQueuedAction()
    def buildStaticElements(self):
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

        self.canvasBindings(self.noteCanvas)
        self.canvasBindings(self.effectCanvas)

        # Drawing
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
        self.effectText = ResourcePool[int](*canvasPools(self.effectCanvas))

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
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MAJOR], width=0
                )
                self.effectCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MAJOR], width=0
                )
            elif row % program.p.currentSong.minorSubdiv == 0:
                self.noteCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MINOR], width=0
                )
                self.effectCanvas.create_rectangle(
                    0, y1, BIG, y2, tags=[Tags.HIGHLIGHT_MINOR], width=0
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
            self.effectCanvas.create_line(
                x1, 0, x1, BIG, tags=[Tags.GRID_LIGHT, f"{col}-1"]
            )
            self.effectCanvas.create_line(
                x2, 0, x2, BIG, tags=[Tags.GRID_DARK, f"{col}-2"]
            )

        # Color and sync
        for canvas in (self.noteCanvas, self.effectCanvas):
            canvas.create_rectangle(-BIG, -BIG, -BIG, -BIG, tags=[Tags.CURSOR], width=0)
            canvas.create_rectangle(
                -BIG, -BIG, -BIG, -BIG, tags=[Tags.SELECTION], width=0
            )
            canvas.create_rectangle(
                -BIG,
                -BIG,
                -BIG,
                -BIG,
                tags=[Tags.TARGET],
                width=2,
                outline=Colors.Target.Outline,
            )
            for tag, color in TAG_COLORS.items():
                canvas.itemconfig(tag, fill=color)
                canvas.tag_lower(tag)
            canvas.tag_raise(Tags.TARGET)

        self.refresh()

    @cached_property
    def effectWidths(self):
        """Pixel widths of each effect column, in order."""
        cols = self.pattern.channel.effectColumns
        maxWidths: list[int] = [EFFECT_COL_MIN_WIDTH for i in range(cols)]
        for (row, col), effect in self.pattern.effects.items():
            if col >= cols:  # If there's stale data off the side
                continue
            if (
                self.target is not None
                and row == self.target.row
                and col == self.target.subcolumn
                and self.target.column == PVLM.EFFECT
            ):
                maxWidths[col] = max(maxWidths[col], (len(self.entryText) + 1) // 2)
            else:
                maxWidths[col] = max(maxWidths[col], len(effect))
        return tuple((2 * w * CHAR_WIDTH) + WIDTH_PAD for w in maxWidths)

    @tkutil.tkQueuedAction()
    def refresh(self):
        """Sync interface with model"""
        # Invalidate cached effect widths
        if hasattr(self, "effectWidths"):
            del self.effectWidths
        # TODO: only update necessary ones (if this proves to be a performance issue)

        # Free ~~changed~~ all text items
        for (row, col, col_t), id in self.textLookup.copy().items():
            if col_t == "note":
                # if (row, col) in self.pattern.notes:
                self.noteText.free(id)
                del self.textLookup[row, col, col_t]
            elif col_t == "velocity":
                # if (row, col) in self.pattern.velocities:
                self.noteText.free(id)
                del self.textLookup[row, col, col_t]
            elif col_t == "effect":
                # if (row, col) in self.pattern.effects:
                # if self.pattern.effects[row, col] != ():
                self.effectText.free(id)
                del self.textLookup[row, col, col_t]

        # Put notes in place
        for (row, col), note in self.pattern.notes.items():
            id = self.textLookup.get((row, col, "note")) or self.noteText.get()
            self.textLookup[row, col, "note"] = id

            x, y, _, _ = self.coords(row, col, "note")
            self.noteCanvas.coords(id, x + WIDTH_PAD_H, y)
            if self.channel == DRUM_CHANNEL:
                text = "STP" if note == "stop" else DRUM_NAMES[note]
            else:
                text = (
                    "STP"
                    if note == "stop"
                    else f"{NOTE_NAMES_SHARP[note % NOTES_PER_OCTAVE]}{note // NOTES_PER_OCTAVE}"
                )
            self.noteCanvas.itemconfig(id, text=text)

        # Put velocities in place
        for (row, col), velocity in self.pattern.velocities.items():
            id = self.textLookup.get((row, col, "velocity")) or self.noteText.get()
            self.textLookup[row, col, "velocity"] = id

            x, y, _, _ = self.coords(row, col, "velocity")
            self.noteCanvas.coords(id, x + WIDTH_PAD_H, y)
            self.noteCanvas.itemconfig(id, text=hex2(velocity))

        # Put effects in place
        e = self.pattern.effects.copy()
        if (
            self.target is not None
        ):  # Add target to list, makes entry work if entering in an empty space.
            if self.target.column == PVLM.EFFECT:
                e[self.target.row, self.target.subcolumn] = ()
        for (row, col), effect in e.items():
            id = self.textLookup.get((row, col, "effect")) or self.effectText.get()
            self.textLookup[row, col, "effect"] = id

            x, y, _, _ = self.coords(row, col, "effect")
            self.effectCanvas.coords(id, x + WIDTH_PAD_H, y)
            if (
                self.target is not None
                and row == self.target.row
                and col == self.target.subcolumn
                and self.target.column == PVLM.EFFECT
            ):
                text = self.entryText
            else:
                text = "".join(hex2(byte) for byte in effect)
            self.effectCanvas.itemconfig(id, text=text)

        # Effect width
        self.effectCanvas.configure(width=sum(self.effectWidths))

        # Relocate effect vertical lines
        for col in range(self.pattern.channel.effectColumns):
            x1, x2 = self.col(col, "effect")
            self.effectCanvas.coords(f"{col}-1", x1, 0, x1, BIG)
            self.effectCanvas.coords(f"{col}-2", x2, 0, x2, BIG)

    def setupPatternListen(self):
        def onNoteChange():
            pass

        def onVelocityChange():
            pass

        def onEffectChange():
            pass

        def onAllChange():
            self.refresh()

        self.pattern.getAttributeChangedEvent("notes").connect(
            lambda *_: (onNoteChange(), onAllChange()), self.patternConnections
        )
        self.pattern.getAttributeChangedEvent("velocities").connect(
            lambda *_: (onVelocityChange(), onAllChange()), self.patternConnections
        )
        self.pattern.getAttributeChangedEvent("effects").connect(
            lambda *_: (onEffectChange(), onAllChange()), self.patternConnections
        )

    def setPattern(self, pattern: Pattern):
        for con in self.patternConnections:
            con.disconnect()
        self.patternConnections.clear()
        self.pattern = pattern
        self.setupPatternListen()
        self.refresh()
