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

        self.lastMatrixRow: int = 0
        self.lastPatternRow: int = 0

        self.grooveIndex: int = 0
        self.grooveTimer: int = 0

        self.expectedTime: float = 0
        self.actualTime: float = 0

        self.playing: bool = False

        def playbackDaemon():
            """
            Handles timing for live playback.
            Actual message generation occurs in the channel objects.
            """
            while True:
                self.resume.wait()

                # Time how long the update takes
                t0 = time.perf_counter()

                self.grooveTimer += 1

                # Some actions are only meant to occur when we step, rather than every tick.
                mainTick = False
                # Step to next row and update groove. Also mark this as a main tick.
                # It looks kind of complex but it just handles all the cases under "move to next row"
                if self.grooveTimer >= program.p.currentSong.groove[self.grooveIndex]:
                    self.grooveTimer = 0
                    self.grooveIndex = (self.grooveIndex + 1) % len(
                        program.p.currentSong.groove
                    )
                    program.p.currentPatternRow += 1
                    if (
                        program.p.currentPatternRow
                        >= program.p.currentSong.patternLength
                    ):
                        program.p.currentPatternRow = 0
                        program.p.currentMatrixRow += 1
                        if (
                            program.p.currentMatrixRow
                            >= program.p.currentSong.visibleMatrixRows
                        ):
                            program.p.currentMatrixRow = 0
                    mainTick = True

                # Tick all channels and collate generated messages
                messages: list[Message | MetaMessage] = list()
                for channel in program.p.currentSong.channels:
                    messages.extend(channel.tick(mainTick))

                # Play messages
                for message in messages:
                    program.p.currentPort.send(message)
                    _logger.debug(message)

                # Timing. We figure out how long we should wait, then adjust based off how long processing took.
                tickLength = 1 / program.p.currentSong.clock

                self.expectedTime += tickLength
                elapsed = time.perf_counter() - t0
                self.actualTime += elapsed
                diff = self.expectedTime - self.actualTime
                sleepTime = max(0, diff)

                self.actualTime += sleepTime
                time.sleep(sleepTime)

        # Start playback daemon
        Thread(name="PlaybackDaemon", target=playbackDaemon, daemon=True).start()

    def setPlaybackCursor(
        self, matrixRow: int | None = None, patternRow: int | None = None
    ):
        self.grooveIndex = 0
        self.grooveTimer = 0
        program.p.currentMatrixRow = (
            matrixRow if matrixRow is not None else program.p.currentMatrixRow
        )
        program.p.currentPatternRow = (
            patternRow if patternRow is not None else program.p.currentPatternRow
        )

    def allOff(self):
        for channel in range(16):
            for note in range(128):
                message = Message("note_off", channel=channel, note=note)
                program.p.currentPort.send(message)

    def play(self):
        self.resume.set()
        self.lastMatrixRow = program.p.currentMatrixRow
        self.lastPatternRow = program.p.currentPatternRow

    def pause(self):
        self.resume.clear()
        self.allOff()

    def togglePlayback(self):
        if self.playing:
            self.playing = False
            self.pause()
        else:
            self.playing = True
            self.play()
