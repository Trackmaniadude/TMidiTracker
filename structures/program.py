import logging

import mido

from structures.globalEvents import ProjectModified, SongReloaded
from structures.player import Player
from structures.song import Song
from utils.event import Event
from utils.reactiveClass import ReactiveClass

_logger = logging.getLogger(__name__)


dummyPort = mido.ports.BaseOutput()


class Program(ReactiveClass):
    """
    Singleton class maintaining program state that is not tied to the current project, as well as other program globals.
    """

    def __init__(self):
        super().__init__()

        self.currentPort: mido.ports.BaseOutput = dummyPort

        # Auto connect to first available port
        ports = self.getAvailablePorts()
        self.setPort(ports[0] if len(ports) > 0 else None)

        self.songPlayer: Player = Player()
        self.songPlayer.startLiveDaemon()

        self.stepSize: int = 1
        """How many rows to step after making an entry. 0 to disable."""

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
        self.getAttributeChangedEvent("currentSong").connect(
            lambda *_: SongReloaded.fire()
        )
        self.getAttributeChangedEvent("projectModified").connect(
            lambda *_: ProjectModified.fire()
        )
        SongReloaded.connect(lambda *_: _logger.debug("Song was reloaded!"))

    def getAvailablePorts(self) -> list[str]:
        return mido.get_output_names()  # type: ignore
        # Mido doesn't export some functions for some reason, even though they're intended for use

    def setPort(self, portname: str | None):
        self.currentPort.close()
        _logger.info(f"Switching output port to '{portname}'")
        try:
            self.currentPort = mido.open_output(portname)  # type: ignore
            # Mido doesn't export some functions for some reason, even though they're intended for use
        except Exception as e:
            if portname != None:
                _logger.error(f"Could not open given port: {e}")
            self.currentPort = dummyPort

    def close(self):
        self.currentPort.close()


p = Program()
"""Main program data object. Singleton."""
