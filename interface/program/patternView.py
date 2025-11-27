"""
Interface for editing the message data in a pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

import tkinter as tk
from tkinter import ttk

from structures import program

NOTE_WIDTH = 4
EFFECT_WIDTTH = 6


class PatternViewLabel(ttk.Label):
    def __init__(
        self,
        parent: PatternView,
        mode: Literal["note", "effect"],
        row: int,
        column: int,
    ):
        if mode == "note":
            super().__init__(parent.noteFrame)
            width = NOTE_WIDTH
        elif mode == "effect":
            super().__init__(parent.effectFrame)
            width = EFFECT_WIDTTH
        self.config(text="DEF", width=width, relief="solid", borderwidth=2)

        self.view = parent
        self.mode = mode
        self.row = row
        self.column = column

        self.inputing: bool = False

        self.entry = ttk.Entry(self, width=width)

        self.bind("<FocusIn>", lambda *_: self.startEntry())
        self.entry.bind("<FocusOut>", lambda *_: self.endEntry())

    def startEntry(self):
        self.inputing = True
        self.entry.grid(row=0, column=0, sticky="nesw")
        self.entry.focus()

    def endEntry(self):
        self.inputing = False
        self.entry.grid_forget()

        value = self.entry.get()
        if self.mode == "note":
            self.view.pattern.setNote(self.row, self.column, value)
        elif self.mode == "effect":
            self.view.pattern.setEffect(self.row, self.column, value)

        self.refresh()

    def refresh(self):
        if self.mode == "note":
            d = self.view.pattern.getNote(self.row, self.column)
        elif self.mode == "effect":
            d = self.view.pattern.getEffect(self.row, self.column)
        else:
            raise Exception
        if d is None:
            t = ""
        else:
            t = str(d)
        self.config(text=t)


class PatternView(ttk.Frame):
    def __init__(self, parent: tk.Misc, initialPattern: Pattern):
        super().__init__(parent, borderwidth=1, relief="raised")

        self.pattern: Pattern = initialPattern

        self.__labels: dict[tuple[int, int], PatternViewLabel] = dict()

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
        for key, label in self.__labels.items():
            label.destroy()
            del self.__labels[key]

        # Notes
        rows = program.currentSong.patternLength
        notes = self.pattern.channel.noteColumns
        effects = self.pattern.channel.effectColumns

        for row in range(rows):
            for column in range(notes):
                label = PatternViewLabel(self, "note", row, column)
                label.grid(row=row, column=column)
                self.__labels[row, column] = label

        # Effects
        for row in range(rows):
            for column in range(effects):
                label = PatternViewLabel(self, "effect", row, column)
                label.grid(row=row, column=column)
                self.__labels[row, column] = label

    def refreshLabels(self):
        for label in self.__labels.values():
            label.refresh()

    def setPattern(self, pattern: Pattern):
        self.pattern = pattern
        self.buildLabels()
        self.refreshLabels()
