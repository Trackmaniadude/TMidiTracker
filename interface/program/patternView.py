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
    def __init__(self, parent: PatternView, mode: Literal["note", "effect"]):
        if mode == "note":
            super().__init__(parent.noteFrame)
            self.config(text="A#4", width=NOTE_WIDTH)
        elif mode == "effect":
            super().__init__(parent.effectFrame)
            self.config(text="00AAFF", width=EFFECT_WIDTTH)
        self.config(relief="solid", borderwidth=2)


class PatternView(ttk.Frame):
    def __init__(self, parent: tk.Misc, initialPattern: Pattern):
        super().__init__(parent, borderwidth=1, relief="raised")

        self.__pattern: Pattern = initialPattern

        self.__labels: dict[tuple[int, int], ttk.Label] = dict()

        self.noteFrame = ttk.Frame(self, relief="ridge", borderwidth=2)
        self.effectFrame = ttk.Frame(self, relief="ridge", borderwidth=2)

        self.noteFrame.grid(row=0, column=0)
        self.effectFrame.grid(row=0, column=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.buildLabels()

    def buildLabels(self):
        # Remove old labels
        for key, label in self.__labels.items():
            label.destroy()
            del self.__labels[key]

        # Notes
        rows = program.currentSong.patternLength
        notes = self.__pattern.channel.noteColumns
        effects = self.__pattern.channel.effectColumns

        for row in range(rows):
            for column in range(notes):
                label = PatternViewLabel(self, "note")
                label.grid(row=row, column=column)
                self.__labels[row, column] = label

        # Effects
        for row in range(rows):
            for column in range(effects):
                label = PatternViewLabel(self, "effect")
                label.grid(row=row, column=column)
                self.__labels[row, column] = label

    def setPattern(self, pattern: Pattern):
        self.__pattern = pattern
        self.buildLabels()
