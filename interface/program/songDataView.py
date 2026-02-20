"""View and edit song metadata."""

import tkinter as tk
from tkinter import ttk

from interface.utilities.doubleScrollFrame import DScrollFrame
from interface.utilities.headerFrame import HeaderFrame
from interface.utilities.validatedEntryPrebuilts import Prebuilts


class SongDataView(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, relief="raised", width=300, height=200, borderwidth=2)

        sf = DScrollFrame(self, mode="VERTICAL", propagationMode="contentDrivesFrame")
        sf.pack(fill="both", expand=True)
        self.content = sf.content
        # self.pack_propagate(False)

        metadataFrame = HeaderFrame(self.content, "Metadata", userCollapsible=True)
        metadataFrame.pack(side="top", fill="x")

        # TODO: nice modular way to do this

        ttk.Label(metadataFrame.content, text="Title").grid(
            row=0, column=0, sticky="we"
        )
        ttk.Entry(metadataFrame.content).grid(row=0, column=1, sticky="e")
        ttk.Label(metadataFrame.content, text="Author").grid(
            row=1, column=0, sticky="we"
        )
        ttk.Entry(metadataFrame.content).grid(row=1, column=1, sticky="e")
        ttk.Label(metadataFrame.content, text="Genre").grid(
            row=2, column=0, sticky="we"
        )
        ttk.Entry(metadataFrame.content).grid(row=2, column=1, sticky="e")
        ttk.Label(metadataFrame.content, text="Genre").grid(
            row=3, column=0, sticky="we", columnspan=2
        )
        t = tk.Text(metadataFrame.content, width=10, height=10)
        t.grid(row=4, column=0, sticky="we", columnspan=2)
        t.bind("<space>", lambda *_: _, "")

        metadataFrame.content.columnconfigure(0, weight=1)
        metadataFrame.collapse()
