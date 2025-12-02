"""
Live playback code.
"""

import logging
import time
from threading import Event, Thread

from mido import Message, MetaMessage

from structures import program  # Note: Can't use during init

_logger = logging.getLogger(__name__)


class Player:
    """
    Provides live playback of song data.
    """

    def __init__(self):

        self.resume = Event()

        self.matrixRow: int = 0
        """Current row in pattern matrix."""
        self.patternRow: int = 0
        """Current row within pattern."""

        self.grooveIndex: int = 0
        self.grooveTimer: int = 0

        self.expectedTime: float = 0
        self.actualTime: float = 0

        def playbackDaemon():
            while True:
                self.resume.wait()

                t0 = time.perf_counter()

                self.grooveTimer += 1


                mainTick = False
                if self.grooveTimer > program.p.currentSong.groove[self.grooveIndex]:
                    self.grooveTimer = 0
                    self.grooveIndex = (self.grooveIndex + 1) % len(
                        program.p.currentSong.groove
                    )
                    program.p.currentPatternRow += 1
                    if (
                        program.p.currentPatternRow
                        > program.p.currentSong.patternLength
                    ):
                        program.p.currentPatternRow = 0
                        program.p.currentMatrixRow += 1
                    mainTick = True

                messages: list[Message | MetaMessage] = list()
                for channel in program.p.currentSong.channels:
                    messages.extend(channel.tick(mainTick))

                for message in messages:
                    program.p.currentPort.send(message)


                tickLength = 1 / program.p.currentSong.clock

                self.expectedTime += tickLength
                elapsed = time.perf_counter() - t0
                self.actualTime += elapsed
                diff = self.expectedTime - self.actualTime
                sleepTime = max(0, diff)

                self.actualTime += sleepTime
                time.sleep(sleepTime)

        Thread(name="PlaybackDaemon", target=playbackDaemon, daemon=True).start()

    def setPlaybackCursor(self, matrixRow: int, patternRow: int):
        self.matrixRow = matrixRow
        self.patternRow = patternRow

    def play(self):
        self.grooveIndex = 0
        self.grooveTimer = 0
        self.resume.set()

    def pause(self):
        self.resume.clear()
