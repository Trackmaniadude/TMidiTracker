"""
Singleton class maintaining program state.
"""

import mido

from structures.player import Player
from structures.song import Song

currentPortName: str = mido.get_output_names()[0]  # type: ignore
currentPort: mido.ports.BaseOutput = mido.open_output(currentPortName)  # type: ignore

songPlayer: Player = Player()

currentSong: Song = Song()
"""Current active song object."""

currentOctave: int = 4
"""Base octave for entering notes."""

allowEditingPattern: bool = False
"""Allow making edits to the program, or just treat inputs as keyboard playing."""

playbackInEdit: bool = True
"""When entering a note, play it."""


def close():
    currentPort.close()
