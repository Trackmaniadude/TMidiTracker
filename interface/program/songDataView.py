"""View and edit song metadata."""

import tkinter as tk
from tkinter import ttk


class SongDataView(ttk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        ttk.Label(self, text="SONG DATA VIEWER").pack()
