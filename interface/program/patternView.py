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

from interface.theme import Note
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


class PatternViewLabel(ttk.Label):
    def __init__(
        self,
        parent: PatternView,
        mode: PatternViewLabelModes,
        row: int,
        column: int,
    ):
        super().__init__(getattr(parent, mode.value.parentName))
        width = mode.value.width
        self.config(text="", width=width, relief="solid", borderwidth=2)

        self.view = parent
        self.mode = mode
        self.row = row
        self.column = column

        self.inputing: bool = False
        self.clearOnNextInput: bool = False

        self.connections: list[Connection] = list()

        self.__style: str = ""
        self.__text: str = ""
        self.entryTextProxy: str = ""
        """TODO: not need this because of sequencing issues"""

        # Target this entry on click
        self.bind(
            "<Button-1>",
            lambda *_: self.view.viewFrame.setTarget(
                self.view.pattern.channel.channel,
                self.row,
                self.mode,
                self.column,
            ),
        )
        self.bind(
            "<Shift-Button-1>",
            lambda *_: self.view.viewFrame.setTarget(
                self.view.pattern.channel.channel,
                self.row,
                self.mode,
                self.column,
                setSecondary=True,
            ),
        )

        # Note inputs have separate behavior to velocity and effect inputs
        if mode == PVLM.NOTE:

            def delete():
                self.view.pattern.setNote(self.row, self.column, None)
                self.view.viewFrame.stepTarget(
                    program.p.stepSize, focus=True, stepPattern=False
                )

            def backspace():
                target = max(0, self.row - program.p.stepSize)
                self.view.pattern.setNote(target, self.column, None)
                self.view.viewFrame.setTarget(row=target, focus=True)

            def stop():
                self.view.pattern.setNote(self.row, self.column, "stop")
                self.view.viewFrame.stepTarget(
                    program.p.stepSize, focus=True, stepPattern=False
                )

            def play(note: int | Literal["stop"] | None):
                # Returns an event func to allow instancing values of the function
                def onEvent(*_):
                    if type(note) is int:
                        n = note + (program.p.currentOctave * NOTES_PER_OCTAVE)
                        if program.p.playbackInEdit:
                            message = mido.Message(
                                "note_on",
                                channel=self.view.pattern.channel.channel,
                                note=n,
                                velocity=64,
                            )
                            program.p.currentPort.send(message)
                        self.view.pattern.setNote(self.row, self.column, n)
                        self.view.viewFrame.stepTarget(program.p.stepSize, focus=True)
                        self.refresh()

                return onEvent

            def release(note):
                # Returns an event func to allow instancing values of the function
                def onEvent(*_):
                    if type(note) is int:
                        n = note + (program.p.currentOctave * NOTES_PER_OCTAVE)
                        message = mido.Message(
                            "note_off",
                            channel=self.view.pattern.channel.channel,
                            note=n,
                            velocity=0,
                        )
                        program.p.currentPort.send(message)

                return onEvent

            for key, note in KEYBOARD_MAP.items():
                self.bind(f"<KeyPress-{key}>", play(note))
                self.bind(f"<KeyRelease-{key}>", release(note))
            self.bind(f"<Tab>", lambda *_: stop())
            self.bind(f"<BackSpace>", lambda *_: backspace())
            self.bind(f"<Delete>", lambda *_: delete())

        else:  # Velocity and Effect

            def keyPress(letter: str):
                def onEvent(*_):
                    if self.clearOnNextInput:
                        self.clearOnNextInput = False
                        self.entryTextProxy = ""
                    self.entryTextProxy += letter
                    self.text = self.entryTextProxy

                    if mode == PVLM.VELOCITY and len(self.entryTextProxy) == 2:
                        self.view.viewFrame.stepTarget(
                            program.p.stepSize, focus=True, stepPattern=False
                        )

                return onEvent

            def backspace():
                # Remove a character. If no characters, remove previous entry and jump to it.
                self.clearOnNextInput = False
                if len(self.entryTextProxy) == 0:
                    target = max(0, self.row - program.p.stepSize)
                    self.view.viewFrame.setTarget(row=target, focus=True)
                    if mode == PVLM.VELOCITY:
                        self.view.pattern.setVelocity(target, self.column, None)
                    if mode == PVLM.EFFECT:
                        self.view.pattern.setEffect(target, self.column, None)
                else:
                    self.entryTextProxy = self.entryTextProxy[:-1]
                    self.text = self.entryTextProxy

            def delete():
                if mode == PVLM.VELOCITY:
                    self.view.pattern.setVelocity(self.row, self.column, None)
                if mode == PVLM.EFFECT:
                    self.view.pattern.setEffect(self.row, self.column, None)
                self.entryTextProxy = ""
                self.text = ""
                self.refresh()
                self.view.viewFrame.stepTarget(
                    program.p.stepSize, focus=True, stepPattern=False
                )

            def enter():
                self.view.viewFrame.stepTarget(
                    program.p.stepSize, focus=True, stepPattern=False
                )

            def setClearOnNext():
                self.clearOnNextInput = True

            def focus():
                self.entryTextProxy = self.getTextValue()
                self.refresh()

            def finalize():
                self.clearOnNextInput = False

                if mode == PVLM.VELOCITY:
                    if self.entryTextProxy == "":
                        self.view.pattern.setVelocity(self.row, self.column, None)
                    else:
                        self.view.pattern.setVelocity(
                            self.row, self.column, int(self.entryTextProxy, 16)
                        )
                    self.refresh()

                if mode == PVLM.EFFECT:
                    if len(self.entryTextProxy) % 2 != 0:
                        self.entryTextProxy = "0" + self.entryTextProxy
                    nums: list[int] = list()
                    for i in range(0, len(self.entryTextProxy), 2):
                        nums.append(int(self.entryTextProxy[i : i + 2], 16))
                    self.view.pattern.setEffect(self.row, self.column, tuple(nums))
                    self.refresh()

            for letter in HEX_KEYMAP:
                self.bind(f"{letter}", keyPress(letter.upper()))
            self.bind("<FocusOut>", lambda *_: finalize())
            self.bind("<FocusIn>", lambda *_: focus())
            self.bind("<Delete>", lambda *_: delete())
            self.bind("<BackSpace>", lambda *_: backspace())
            self.bind("<Return>", lambda *_: enter())
            self.bind("<Button-1>", lambda *_: setClearOnNext(), "+")

        # Keyboard Navigation
        self.bind(
            "<Up>",
            lambda *_: self.view.viewFrame.stepTarget(1, focus=True, direction="Up"),
        )
        self.bind(
            "<Down>",
            lambda *_: self.view.viewFrame.stepTarget(1, focus=True, direction="Down"),
        )
        self.bind(
            "<Left>",
            lambda *_: self.view.viewFrame.stepTarget(1, focus=True, direction="Left"),
        )
        self.bind(
            "<Right>",
            lambda *_: self.view.viewFrame.stepTarget(1, focus=True, direction="Right"),
        )
        self.bind(
            "<Shift-Up>",
            lambda *_: self.view.viewFrame.stepTarget(
                1, focus=True, direction="Up", moveSecondary=True
            ),
        )
        self.bind(
            "<Shift-Down>",
            lambda *_: self.view.viewFrame.stepTarget(
                1, focus=True, direction="Down", moveSecondary=True
            ),
        )
        self.bind(
            "<Shift-Left>",
            lambda *_: self.view.viewFrame.stepTarget(
                1, focus=True, direction="Left", moveSecondary=True
            ),
        )
        self.bind(
            "<Shift-Right>",
            lambda *_: self.view.viewFrame.stepTarget(
                1, focus=True, direction="Right", moveSecondary=True
            ),
        )

        # Increment/Decrement
        self.bind(
            "<equal>",
            lambda *_: self.increment(0),
        )
        self.bind(
            "<minus>",
            lambda *_: self.decrement(0),
        )
        self.bind(
            "<Control-equal>",
            lambda *_: self.increment(1),
        )
        self.bind(
            "<Control-minus>",
            lambda *_: self.decrement(1),
        )

        StructureChanged.connect(lambda *_: self.refresh(), self.connections)

        self.refresh()

    def destroy(self) -> None:
        for connection in self.connections:
            connection.disconnect()
        return super().destroy()

    def increment(self, scale: int):
        if self.view.viewFrame.target.column == PVLM.NOTE:
            notes, _, _ = self.view.viewFrame.getUsedIndicesInSelection()
            for channel, row, column in notes:
                pattern = program.p.currentSong.getPatternByLocation(
                    channel, program.p.currentMatrixRow
                )
                currentNote = pattern.getNote(row, column)
                if currentNote is None:
                    return
                if currentNote == "stop":
                    return
                pattern.setNote(row, column, currentNote + NOTE_DELTAS[scale])
            self.view.viewFrame.refreshLabels()

    def decrement(self, scale: int):
        if self.view.viewFrame.target.column == PVLM.NOTE:
            notes, _, _ = self.view.viewFrame.getUsedIndicesInSelection()
            for channel, row, column in notes:
                pattern = program.p.currentSong.getPatternByLocation(
                    channel, program.p.currentMatrixRow
                )
                currentNote = pattern.getNote(row, column)
                if currentNote is None:
                    return
                if currentNote == "stop":
                    return
                pattern.setNote(row, column, currentNote - NOTE_DELTAS[scale])
            self.view.viewFrame.refreshLabels()

    def getTextValue(self):
        getter = getattr(self.view.pattern, self.mode.value.getter)
        value = getter(self.row, self.column)
        if value is None:
            return ""
        else:
            return self.mode.value.toView(value, self.view.pattern.channel.channel)

    def refresh(self):
        self.text = self.getTextValue()

        # Highlight
        target = self.view.viewFrame.target
        target2 = self.view.viewFrame.secondaryTarget
        highlight = False

        if target2 is None:
            if self.row == target.row:
                highlight = True
            elif self.channel == target.channel:
                if self.mode == target.column:
                    if self.column == target.subcolumn:
                        highlight = True
        else:
            minRow = min(target.row, target2.row)
            maxRow = max(target.row, target2.row)
            if self.row >= minRow and self.row <= maxRow:
                mn = min(
                    target.horizontalComparisonKey, target2.horizontalComparisonKey
                )
                mx = max(
                    target.horizontalComparisonKey, target2.horizontalComparisonKey
                )
                c = Target(
                    self.channel, self.row, self.mode, self.column
                ).horizontalComparisonKey
                if c >= mn and c <= mx:
                    highlight = True

        if self.row % program.p.currentSong.majorSubdiv == 0:
            style = Note.MajorTarget if highlight else Note.Major
        elif self.row % program.p.currentSong.minorSubdiv == 0:
            style = Note.MinorTarget if highlight else Note.Minor
        else:
            style = Note.DefaultTarget if highlight else Note.Default

        self.style = cast(str, style)

    @property
    def positionTarget(self) -> Target:
        return Target(self.channel, self.row, self.mode, self.column)

    @property
    def channel(self) -> int:
        return self.view.pattern.channel.channel

    @property
    def style(self) -> str:
        return self.__style

    @style.setter
    def style(self, newStyle: str):
        if newStyle != self.__style:
            self.__style = newStyle
            self.config(style=self.style)

    @property
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, newText: str):
        if newText != self.__text:
            self.__text = newText
            self.config(text=newText)
            if self.mode == PVLM.EFFECT:
                self.config(width=len(newText))


class PatternView(ttk.Frame):
    """Display/edit the data of a single pattern."""

    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=2, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.connections: list[Connection] = list()

        self.__labels: set[PatternViewLabel] = set()

        self.labelLookup: dict[
            tuple[int, PatternViewLabelModes, int], PatternViewLabel
        ] = dict()
        """Row (int), Column (PatternViewLabelModes), Subcolumn (int)"""

        ### Build Layout
        # Frames
        self.noteFrame = ttk.Frame(self, relief="sunken", borderwidth=2)
        self.effectFrame = ttk.Frame(self, relief="sunken", borderwidth=2)

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
        # Remove old labels
        for label in self.__labels:
            label.destroy()
        self.__labels.clear()
        self.labelLookup.clear()

        # Notes
        rows = program.p.currentSong.patternLength
        notes = self.pattern.channel.noteColumns
        effects = self.pattern.channel.effectColumns

        for row in range(rows):
            for column in range(notes):
                note = PatternViewLabel(self, PVLM.NOTE, row, column)
                note.grid(row=row, column=column * 2)
                velocity = PatternViewLabel(self, PVLM.VELOCITY, row, column)
                velocity.grid(row=row, column=(column * 2) + 1)

                self.labelLookup[row, PVLM.NOTE, column] = note
                self.labelLookup[row, PVLM.VELOCITY, column] = velocity

                self.__labels.add(note)
                self.__labels.add(velocity)

        # Effects
        for row in range(rows):
            for column in range(effects):
                effect = PatternViewLabel(self, PVLM.EFFECT, row, column)
                effect.grid(row=row, column=column, sticky="ew")
                self.__labels.add(effect)

                self.labelLookup[row, PVLM.EFFECT, column] = effect

    def refreshLabels(self):
        for label in self.__labels:
            label.refresh()

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.buildLabels()
        self.refreshLabels()
