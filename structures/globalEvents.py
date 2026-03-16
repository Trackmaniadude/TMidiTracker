"""Event list"""

from utils.event import Event

TimingChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for timing are changed."""
StructureChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for song structure are changed."""
SongReloaded: Event = Event()
"""Fired when program.currentSong is changed. Intended for reloading the interface."""
ProjectModified: Event = Event()
"""Fired on any change that should mark the project as modified."""
