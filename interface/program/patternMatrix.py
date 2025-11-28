"""
View/editor for the pattern matrix.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.song import Song
    from structures.channel import Channel
    from structures.pattern import Pattern

from interface.utilities.doubleScrollFrame import DScrollFrame

import logging
import tkinter as tk
from tkinter import ttk

_logger = logging.getLogger(__name__)


class PatternMatrix(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=200, height=200)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.__content = sf.content
