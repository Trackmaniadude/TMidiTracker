import logging

import mido

from structures.globalEvents import SongReloaded
from structures.player import Player
from structures.song import Song
from utils.event import Event
from utils.reactiveClass import ReactiveClass

_logger = logging.getLogger(__name__)


class Program(ReactiveClass):
    """
    Singleton class maintaining program state that is not tied to the current project, as well as other program globals.
    """

    def __init__(self):
        super().__init__()

        # fmt: off
        self.currentPortName: str = mido.get_output_names()[0] # pyright: ignore[reportAttributeAccessIssue]
        self.currentPort: mido.ports.BaseOutput = mido.open_output(self.currentPortName)  # pyright: ignore[reportAttributeAccessIssue]
        # fmt: on
        # TODO: handle no port connected

        self.songPlayer: Player = Player()

        self.stepSize: int = 1
        """How many rows to step after making an entry. 0 to disable."""

        try:
            self.currentSong: Song = Song.fromFile("startup.tmt")
        except:
            self.currentSong: Song = Song()
        """Current active song object."""

        self.currentOctave: int = 4
        """Base octave for entering notes."""

        self.allowEditingPattern: bool = False
        """Allow making edits to the program, or just treat inputs as keyboard playing."""

        self.playbackInEdit: bool = True
        """When entering a note, play it."""

        self.currentMatrixRow: int = 0
        """Current row in pattern matrix."""
        self.currentPatternRow: int = 0
        """Current row in patterns."""

        # Files
        self.currentFile: str | None = None
        self.projectModified: bool = False

        # Events
        self.setupContainerListen()
        self.Changed.connect(
            lambda name, *_: (SongReloaded.fire() if name == "currentSong" else None)
        )
        SongReloaded.connect(lambda *_: _logger.debug("Song was reloaded!"))

    def close(self):
        self.currentPort.close()


p = Program()
