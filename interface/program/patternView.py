"""
Interface for editing the message data in a pattern.
"""

import tkinter as tk
from tkinter import ttk


class PatternView(tk.Frame):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, background="green", relief="raised")
