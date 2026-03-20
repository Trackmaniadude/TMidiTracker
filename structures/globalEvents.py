"""Event list"""

import tkinter as tk

from utils.event import Event

TimingChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for timing are changed."""
StructureChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for song structure are changed."""
SongReloaded: Event = Event()
"""Fired when program.currentSong is changed. Intended for reloading the interface."""
ProjectModified: Event = Event()
"""Fired on any change that should mark the project as modified."""

Copy: Event[tk.Misc] = Event()
"""Fired when the copy command is used. Argument is currently focused widget."""
Paste: Event[tk.Misc] = Event()
"""Fired when the paste command is used. Argument is currently focused widget."""
