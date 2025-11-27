"""
Singleton class maintaining program state.
"""

from structures.song import Song

currentSong: Song = Song()
