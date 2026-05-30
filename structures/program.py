import logging
import random
import tkinter as tk
from typing import cast

import mido

from structures.globalEvents import ProjectModified, SongReloaded
from structures.player import Player
from structures.song import Song
from utils.fluidsynth import FLUIDSYNTH_EXISTS, Fluidsynth
from utils.persistence import USE_DEFAULT, Persistence
from utils.reactiveClass import ReactiveClass

_logger = logging.getLogger(__name__)


AUTOPORT_ATTEMPTS = 10
AUTOPORT_TIME = 200  # milliseconds

INTERNAL_FLUIDSYNTH_IDENTIFIER = (
    f"TMidiTracker-Internal-Fluidsynth-{hex(random.randint(0x1000000, 0xFFFFFFFF))[2:]}"
)
INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER = "INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER"


class Program(ReactiveClass):
    """
    Singleton class maintaining program state that is not tied to the current project, as well as other program globals.
    """

    def __init__(self):
        super().__init__()

        # Files
        self.currentFile: str | None = None
        self.projectModified: bool = False
        self.persistence = Persistence("PERSISTENCE")

        # Ports
        self.currentPort: mido.ports.BaseOutput = mido.ports.BaseOutput(name="No Port")

        def savePort() -> str:
            if self.currentPortName.startswith(INTERNAL_FLUIDSYNTH_IDENTIFIER):
                return INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER
            name = self.currentPortName
            prefix = name[: name.find(":")]
            return prefix

        def loadPort(value: str):
            if value is USE_DEFAULT:
                return

            def tryOpenPort(t: int):  # Mostly to allow time for Fluidsynth to boot up
                if t <= 0:
                    return
                if value == INTERNAL_FLUIDSYNTH_SAVE_IDENTIFIER:
                    if self.setPort(INTERNAL_FLUIDSYNTH_IDENTIFIER):
                        return
                else:
                    ports = cast(list[str], mido.get_output_names())  # type: ignore
                    for port in ports:
                        if port.startswith(value):
                            if self.setPort(value):
                                return
                self.tkRoot.after(AUTOPORT_TIME, tryOpenPort, t - 1)

            self.tkRoot.after(AUTOPORT_TIME, tryOpenPort, AUTOPORT_ATTEMPTS)

        self.persistence.register("lastActivePort", savePort, loadPort)

        if FLUIDSYNTH_EXISTS:
            self.fluidsynth = Fluidsynth(INTERNAL_FLUIDSYNTH_IDENTIFIER)
            self.fluidsynth.setGain(2)

        # Player
        self.songPlayer: Player = Player()
        self.songPlayer.startLiveDaemon()

        self.currentMatrixRow: int = 0
        """Current row in pattern matrix."""
        self.currentPatternRow: int = 0
        """Current row in patterns."""

        # Editor (TODO: should be editor property?)
        self.stepSize: int = 1
        """How many rows to step after making an entry. 0 to disable."""
        self.currentOctave: int = 4
        """Base octave for entering notes."""
        self.allowEditingPattern: bool = False
        """Allow making edits to the program, or just treat inputs as keyboard playing."""
        self.playbackInEdit: bool = True
        """When entering a note, play it."""

        # Other Data
        self.currentSong: Song = Song()
        """Current active song object."""

        self.tkRoot: tk.Misc
        """Interface root reference."""

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
        success = False
        if portname == self.currentPort.name:
            return True
        self.currentPort.close()
        _logger.info(f"Switching output port to '{portname}'")
        if portname is None:
            newPort = mido.ports.BaseOutput(name="No Port")
        else:
            try:
                newPort: mido.ports.BaseOutput = mido.open_output(portname)  # type: ignore
                # Mido doesn't export some functions for some reason, even though they're intended for use
            except Exception as e:
                _logger.error(f"Could not open given port: {e}")
                newPort = mido.ports.BaseOutput(name="No Port")
            else:
                success = True
        _logger.info(f"Set output port to '{newPort}'")
        self.currentPort = newPort
        return success

    @property
    def currentPortName(self):
        return cast(str, self.currentPort.name)

    def close(self):
        self.currentPort.close()


p = Program()
"""Main program data object. Singleton."""
