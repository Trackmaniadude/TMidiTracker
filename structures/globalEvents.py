"""Event list"""

from utils.event import Event

TimingChanged: Event[list[str]] = Event()
StructureChanged: Event[list[str]] = Event()
