"""
Singleton class maintaining program state.
"""

from structures.song import Song

currentSong: Song = Song()
"""Current active song object."""

currentOctave: int = 4
"""Base octave for entering notes."""
