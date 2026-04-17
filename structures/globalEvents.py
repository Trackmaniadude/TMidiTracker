"""Event list"""

import tkinter as tk

from utils.event import Event

TimingChanged: Event[list[str]] = Event("TimingChanged")
"""changes: list[str] - When settings for timing are changed."""
StructureChanged: Event[list[str]] = Event("StructureChanged")
"""changes: list[str] - When settings for song structure are changed."""
SongReloaded: Event = Event("SongReloaded")
"""Fired when program.currentSong is changed. Intended for reloading the interface."""
ProjectModified: Event = Event("ProjectModified")
"""Fired on any change that should mark the project as modified."""

Cut: Event[tk.Misc] = Event("Cut")
"""Fired when the cut command is used. Argument is currently focused widget."""
Copy: Event[tk.Misc] = Event("Copy")
"""Fired when the copy command is used. Argument is currently focused widget."""
Paste: Event[tk.Misc] = Event("Paste")
"""Fired when the paste command is used. Argument is currently focused widget."""
