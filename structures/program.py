"""
Singleton class maintaining program state.
"""

import mido

from structures.player import Player
from structures.song import Song
from utils.reactiveClass import ReactiveClass


class Program(ReactiveClass):
    def __init__(self):
        # fmt: off
        self.currentPortName: str = mido.get_output_names()[0] # pyright: ignore[reportAttributeAccessIssue]
        self.currentPort: mido.ports.BaseOutput = mido.open_output(self.currentPortName)  # pyright: ignore[reportAttributeAccessIssue]
        # fmt: on
        # TODO: handle no port connected

        self.songPlayer: Player = Player()

        self.currentSong: Song = Song()
        """Current active song object."""

        self.currentOctave: int = 4
        """Base octave for entering notes."""

        self.allowEditingPattern: bool = False
        """Allow making edits to the program, or just treat inputs as keyboard playing."""

        self.playbackInEdit: bool = True
        """When entering a note, play it."""

        self.currentMatrixRow: int = 0
        self.currentPatternRow: int = 0

        self.setupContainerListen()

    def close(self):
        self.currentPort.close()


p = Program()
