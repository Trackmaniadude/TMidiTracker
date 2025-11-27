"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import tkinter as tk
from tkinter import ttk

from interface.program.patternView import PatternView
from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from utils.constants import CHANNEL_COUNT


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content

        for channel in range(CHANNEL_COUNT):
            view = PatternView(self.__content)
            view.pack(side="left", expand=True)

            view.setPattern(program.currentSong.getPattern(channel, 0))
