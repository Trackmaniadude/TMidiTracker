"""
Show the internal state of each channel.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.channel import Channel

import tkinter as tk
from tkinter import ttk

from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from utils.constants import CHANNEL_ORDER_INVERSE
from utils.reactiveClass import ReactiveClassView


class ChannelDebug(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=200)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.pack_propagate(False)

        self.__content = sf.content
        self.__content.configure(width=1000, height=2000)

        self.__content.pack_propagate(False)

        for i, channel in enumerate(program.p.currentSong.channels):
            # ii = CHANNEL_ORDER_INVERSE[i]
            # row = ii // DISPLAY_COL
            # col = ii % DISPLAY_COL

            view = ReactiveClassView(
                self.__content,
                channel.playbackState,
                title=f"Channel {i+1}",
                recursionLevel=1,
            )
            view.config(relief="sunken", borderwidth=2)
            view.pack(side="top", fill="x")
            # view.grid(row=row, column=col, sticky="nesw")
            # view.grid(row=i, column=0, sticky="ew")
            # view.grid_propagate(False)
