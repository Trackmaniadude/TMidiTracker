"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable, Literal, cast

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern
    from interface.program.patternViewFrame import PatternViewFrame

import logging
import tkinter as tk
from tkinter import ttk

import mido

from interface.theme import Note
from structures import program
from utils.constants import (
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
from utils.types import *

_logger = logging.getLogger(__name__)


@dataclass
class PatternViewLabelMode[T]:
    t: T
    parentName: str
    width: int
    setter: str
    getter: str
    fromView: Callable[[str], T]
    toView: Callable[[T, int], str]


def fromEffectString(s: str) -> tuple[int, ...]:
    l = list()
    for i in range(0, len(s), 2):
        sub = s[i : i + 2]
        l.append(int(sub, 16))
    return tuple(l)


def toEffectString(t: tuple[int, ...]) -> str:
    return "".join(hex2(n) for n in t)


class PatternViewLabelModes(Enum):
    NOTE = PatternViewLabelMode(
        note,
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
        # fmt: on
    )
    VELOCITY = PatternViewLabelMode(
        velocity,
        parentName="noteFrame",
        width=2,
        setter="setVelocity",
        getter="getVelocity",
        fromView=lambda s: int(s, 16),
        toView=lambda v, _: hex2(v),  # type: ignore
    )
    EFFECT = PatternViewLabelMode(
        effect,
        parentName="effectFrame",
        width=6,
        setter="setEffect",
        getter="getEffect",
        fromView=fromEffectString,
        toView=lambda v, _: toEffectString(v),  # type: ignore
    )


PVLM = PatternViewLabelModes


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

        # self.entryVar = tk.StringVar(self)
        # self.entry = ttk.Entry(self, width=width, textvariable=self.entryVar)

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

        # Note inputs have separate behavior to velocity and effect inputs
        if mode == PVLM.NOTE:

            def delete():
                self.view.pattern.setNote(self.row, self.column, None)
                self.view.viewFrame.stepTarget(program.p.stepSize, focus=True)

            def backspace():
                target = max(0, self.row - program.p.stepSize)
                self.view.pattern.setNote(target, self.column, None)
                self.view.viewFrame.setTarget(row=target, focus=True)

            def stop():
                self.view.pattern.setNote(self.row, self.column, "stop")
                self.view.viewFrame.stepTarget(program.p.stepSize, focus=True)

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
                    self.entryTextProxy += letter
                    self.text = self.entryTextProxy

                return onEvent

            def backspace():
                # Remove a character. If no characters, remove previous entry and jump to it.
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
                self.view.viewFrame.stepTarget(program.p.stepSize, focus=True)

            def enter():
                self.view.viewFrame.stepTarget(program.p.stepSize, focus=True)

            def focus():
                self.entryTextProxy = self.getTextValue()
                self.refresh()

            def finalize():
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
                        self.entryTextProxy = ""
                    nums: list[int] = list()
                    for i in range(0, len(self.entryTextProxy), 2):
                        nums.append(int(self.entryTextProxy[i : i + 2], 16))
                    self.view.pattern.setEffect(self.row, self.column, tuple(nums))
                    print(nums)
                    self.refresh()

            for letter in HEX_KEYMAP:
                self.bind(f"{letter}", keyPress(letter))
            self.bind("<FocusOut>", lambda *_: finalize())
            self.bind("<FocusIn>", lambda *_: focus())
            self.bind("<Delete>", lambda *_: delete())
            self.bind("<BackSpace>", lambda *_: backspace())
            self.bind("<Return>", lambda *_: enter())
            # TODO: should clicking clear? YES

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

        # Increment/Decrement
        self.bind(
            "<Shift-Up>",
            lambda *_: self.increment(0),
        )
        self.bind(
            "<Shift-Down>",
            lambda *_: self.decrement(0),
        )
        self.bind(
            "<Control-Up>",
            lambda *_: self.increment(1),
        )
        self.bind(
            "<Control-Down>",
            lambda *_: self.decrement(1),
        )
        self.bind(
            "<Control-Shift-Up>",
            lambda *_: self.increment(2),
        )
        self.bind(
            "<Control-Shift-Down>",
            lambda *_: self.decrement(2),
        )

    def increment(self, scale: int):
        if self.view.viewFrame.target.column == PVLM.NOTE:
            currentNote = self.view.pattern.getNote(self.row, self.column)
            if currentNote is None:
                return
            if currentNote == "stop":
                return
            self.view.pattern.setNote(
                self.row, self.column, currentNote + NOTE_DELTAS[scale]
            )
            self.refresh()

    def decrement(self, scale: int):
        if self.view.viewFrame.target.column == PVLM.NOTE:
            currentNote = self.view.pattern.getNote(self.row, self.column)
            if currentNote is None:
                return
            if currentNote == "stop":
                return
            self.view.pattern.setNote(
                self.row, self.column, currentNote - NOTE_DELTAS[scale]
            )
            self.refresh()

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
        highlight = False

        if self.row == target.row:
            highlight = True
        elif self.view.pattern.channel.channel == target.channel:
            if self.mode == target.column:
                if self.column == target.subcolumn:
                    highlight = True

        if self.row % program.p.currentSong.majorSubdiv == 0:
            style = Note.MajorTarget if highlight else Note.Major
        elif self.row % program.p.currentSong.minorSubdiv == 0:
            style = Note.MinorTarget if highlight else Note.Minor
        else:
            style = Note.DefaultTarget if highlight else Note.Default

        self.style = cast(str, style)

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
            self.__lastText = self.__text
            self.__text = newText
            self.config(text=newText)
            # self.entryVar.set(newText)


class PatternView(ttk.Frame):
    """Display/edit the data of a single pattern."""

    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=1, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.__labels: set[PatternViewLabel] = set()

        self.labelLookup: dict[
            tuple[int, PatternViewLabelModes, int], PatternViewLabel
        ] = dict()
        """Row (int), Column (PatternViewLabelModes), Subcolumn (int)"""

        self.noteFrame = ttk.Frame(self, relief="ridge", borderwidth=2)
        self.effectFrame = ttk.Frame(self, relief="ridge", borderwidth=2)

        self.noteFrame.grid(row=0, column=0)
        self.effectFrame.grid(row=0, column=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.buildLabels()
        self.refreshLabels()

    def buildLabels(self):
        # Remove old labels
        for label in self.__labels:
            # self.__labels.remove(label)
            label.destroy()
        self.__labels = set()
        self.labelLookup = dict()

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
                effect.grid(row=row, column=column)
                self.__labels.add(effect)

                self.labelLookup[row, PVLM.EFFECT, column] = effect

    def refreshLabels(self):
        for label in self.__labels:
            label.refresh()

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.buildLabels()
        self.refreshLabels()
