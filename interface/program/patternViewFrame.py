"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import tkinter as tk
from tkinter import ttk

from interface.program.patternView import PatternView
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
        self.row = 0

        self.views: list[PatternView] = list()

        for channel in range(program.currentSong.displayChannelCount):
            view = PatternView(
                self.__content, program.currentSong.getPattern(channel, 0)
            )
            view.pack(side="left", expand=True)
            self.views.append(view)

    def setRow(self, row: int):
        self.row = row

        for channel, view in enumerate(self.views):
            view.setPattern(program.currentSong.getPatternByLocation(channel, row))
