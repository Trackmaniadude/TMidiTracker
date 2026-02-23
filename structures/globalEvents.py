"""Event list"""

from utils.event import Event

TimingChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for timing are changed."""
StructureChanged: Event[list[str]] = Event()
"""changes: list[str] - When settings for song structure are changed."""
