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
    KEYBOARD_MAP,
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
        toView=lambda v, c: (
            "STP"
            if v == "stop"
            else (
                NOTE_NAMES_SHARP[v % NOTES_PER_OCTAVE] + str(v // NOTES_PER_OCTAVE)
                if c != DRUM_CHANNEL
                else DRUM_NAMES[v]
            )
        ),
    )
    VELOCITY = PatternViewLabelMode(
        velocity,
        parentName="noteFrame",
        width=2,
        setter="setVelocity",
        getter="getVelocity",
        fromView=lambda s: int(s, 16),
        toView=lambda v, _: hex2(v),
    )
    EFFECT = PatternViewLabelMode(
        effect,
        parentName="effectFrame",
        width=6,
        setter="setEffect",
        getter="getEffect",
        fromView=fromEffectString,
        toView=lambda v, _: toEffectString(v),
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

        self.entryVar = tk.StringVar(self)
        self.entry = ttk.Entry(self, width=width, textvariable=self.entryVar)

        self.__style: str = ""
        self.__text: str = ""

        self.bind("<FocusIn>", lambda *_: self.startEntry())
        if mode == PVLM.NOTE:

            def press(note: int | Literal["stop"] | None):
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
                    else:
                        n = note
                    self.view.pattern.setNote(self.row, self.column, n)
                    self.refresh()

                return onEvent

            def release(note):
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
                self.bind(f"<KeyPress-{key}>", press(note))
                self.bind(f"<KeyRelease-{key}>", release(note))
            self.bind(f"<Tab>", press("stop"))
            self.bind(f"<BackSpace>", press(None))
            self.bind(f"<Delete>", press(None))
            self.bind("<FocusOut>", lambda *_: self.endEntry())
        else:
            self.entry.bind("<FocusOut>", lambda *_: self.endEntry())

    def startEntry(self):
        program.p.songPlayer.setPlaybackCursor(None, self.row)

        self.inputing = True
        self.view.viewFrame.setTarget(
            self.view.pattern.channel.channel,
            self.row,
            self.mode,
            self.column,
        )
        if self.mode == PVLM.NOTE:
            pass
        else:
            self.entry.grid(row=0, column=0, sticky="nesw")
            self.entry.focus()

    def endEntry(self):
        self.inputing = False

        if self.mode == PVLM.NOTE:
            pass
        else:
            self.entry.grid_forget()

            value = self.entryVar.get()
            try:
                if value == "":
                    value = None
                else:
                    value = self.mode.value.fromView(value)
                    setter = getattr(self.view.pattern, self.mode.value.setter)
                    setter(self.row, self.column, value)
            except:
                pass

        self.refresh()

    def refresh(self):
        getter = getattr(self.view.pattern, self.mode.value.getter)
        value = getter(self.row, self.column)
        if value is None:
            text = ""
        else:
            text = self.mode.value.toView(value, self.view.pattern.channel.channel)
        self.text = text

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
            self.__text = newText
            self.config(text=newText)
            self.entryVar.set(newText)


class PatternView(ttk.Frame):
    def __init__(
        self, parent: tk.Misc, viewFrame: PatternViewFrame, initialPattern: Pattern
    ):
        super().__init__(parent, borderwidth=1, relief="raised")

        self.pattern: Pattern = initialPattern
        self.viewFrame: PatternViewFrame = viewFrame

        self.__labels: set[PatternViewLabel] = set()

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
            self.__labels.remove(label)
            label.destroy()

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
                self.__labels.add(note)
                self.__labels.add(velocity)

        # Effects
        for row in range(rows):
            for column in range(effects):
                effect = PatternViewLabel(self, PVLM.EFFECT, row, column)
                effect.grid(row=row, column=column)
                self.__labels.add(effect)

    def refreshLabels(self):
        for label in self.__labels:
            label.refresh()

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.buildLabels()
        self.refreshLabels()
