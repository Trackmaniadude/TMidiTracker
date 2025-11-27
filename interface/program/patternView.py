"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

import tkinter as tk
from tkinter import ttk

from structures import program
from utils.constants import (
    KEYBOARD_MAP,
    NOTE_NAMES_FLAT,
    NOTE_NAMES_SHARP,
    NOTES_PER_OCTAVE,
)
from utils.types import *


@dataclass
class PatternViewLabelMode[T]:
    t: T
    parentName: str
    width: int
    setter: str
    getter: str
    fromView: Callable[[str], T]
    toView: Callable[[T], str]


class PatternViewLabelModes(Enum):
    NOTE = PatternViewLabelMode(
        note,
        parentName="noteFrame",
        width=3,
        setter="setNote",
        getter="getNote",
        fromView=lambda _: _,
        toView=lambda v: "STP" if v == "stop" else NOTE_NAMES_SHARP[v % NOTES_PER_OCTAVE] + str(v // NOTES_PER_OCTAVE),
    )
    VELOCITY = PatternViewLabelMode(
        velocity,
        parentName="noteFrame",
        width=2,
        setter="setVelocity",
        getter="getVelocity",
        fromView=lambda s: int(s, 16),
        toView=lambda v: hex(v)[2:].upper(),
    )
    EFFECT = PatternViewLabelMode(
        effect,
        parentName="effectFrame",
        width=6,
        setter="setEffect",
        getter="getEffect",
        fromView=lambda _: _,
        toView=lambda _: _,
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
        self.config(text="DEF", width=width, relief="solid", borderwidth=2)

        self.view = parent
        self.mode = mode
        self.row = row
        self.column = column

        self.inputing: bool = False

        self.entry = ttk.Entry(self, width=width)

        self.bind("<FocusIn>", lambda *_: self.startEntry())
        if mode == PVLM.NOTE:
            for key, note in KEYBOARD_MAP.items():

                def f(note):
                    # There's probably a better way to do this
                    # Make the lambda "remember" what note was

                    def onEvent(*_):
                        n = note + (program.currentOctave * NOTES_PER_OCTAVE)
                        self.view.pattern.setNote(self.row, self.column, n)
                        self.refresh()

                    return onEvent

                self.bind(key, f(note))
            self.bind("<FocusOut>", lambda *_: self.endEntry())
        else:
            self.entry.bind("<FocusOut>", lambda *_: self.endEntry())

    def noteEntryEventHandler(self):
        pass

    def startEntry(self):
        self.inputing = True
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

            value = self.entry.get()
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
            text = self.mode.value.toView(value)
        self.config(text=text)


class PatternView(ttk.Frame):
    def __init__(self, parent: tk.Misc, initialPattern: Pattern):
        super().__init__(parent, borderwidth=1, relief="raised")

        self.pattern: Pattern = initialPattern

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
        rows = program.currentSong.patternLength
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
