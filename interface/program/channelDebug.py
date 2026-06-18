"""
Show the internal state of each channel.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from interface.utilities.doubleScrollFrame import DScrollFrame
from structures import program
from structures.globalEvents import SongReloaded
from utils.constants import CHANNEL_ORDER_INVERSE
from utils.reactiveClass import ReactiveClassView

if TYPE_CHECKING:
    from structures.channel import Channel


class ChannelDebug(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=200)

        sf = DScrollFrame(self, mode="DOUBLE")
        sf.pack(fill="both", expand=True)

        self.pack_propagate(False)

        self.__content = sf.content
        self.__content.configure(width=1000, height=4000)

        self.__content.pack_propagate(False)

        self.__views = list[ReactiveClassView]()
        self.__makeViews()

        SongReloaded.connect(self.__makeViews)

    def __makeViews(self):
        for view in self.__views:
            view.destroy()
        self.__views.clear()

        for i, channel in enumerate(program.p.currentSong.channels):
            view = ReactiveClassView(
                self.__content,
                channel.playbackState,
                title=f"Channel {i+1}",
                recursionLevel=1,
            )
            view.config(relief="sunken", borderwidth=2)
            view.pack(side="top", fill="x")
            self.__views.append(view)
