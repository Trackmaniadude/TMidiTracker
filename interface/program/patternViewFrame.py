"""
Horizontal list of each channels' current pattern.
AKA the main editing window.
"""

import tkinter as tk
from tkinter import ttk

from interface.utilities.tk_scroll_demo import ScrollFrame


class PatternViewFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)

        sf = ScrollFrame(self)
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
