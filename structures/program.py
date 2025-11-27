"""
Singleton class maintaining program state.
"""

from structures.song import Song

currentSong: Song = Song()
"""Current active song object."""

currentOctave: int = 5
"""Base octave for entering notes."""

livePlayback: bool = False
"""Instead of entering notes, play out."""


def close():
    pass
