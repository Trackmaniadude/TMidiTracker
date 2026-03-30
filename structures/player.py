"""
Live playback code.
"""

import logging
import time
from threading import Event, Thread

from mido import Message, MetaMessage, MidiFile, MidiTrack

from structures import program  # Note: Can't use during init

_logger = logging.getLogger(__name__)


class Player:
    """
    Provides playback of song data.
    """

    def __init__(self):

        self.resume = Event()

        self.lastMatrixRow: int = 0
        self.lastPatternRow: int = 0

        self.grooveIndex: int = 0
        self.grooveTimer: int = 0

        self.expectedTime: float = 0
        """For live mode, time we should wait to before starting the next tick."""
        self.actualTime: float = 0
        """For live mode, time we are currently at after processing this tick."""

        self.ticksSinceLastMessage: int = 0
        """Used for offline timing."""

        self.playing: bool = False
        self.loop: bool | int = True
        """If the player should loop. If it is set to an integer, it will count down until it hits 0, at which point playback will stop."""

        self.live: bool = False
        """If the player should run the live sequencer."""

    def tick(self) -> list[Message | MetaMessage]:
        """Run one tick on all channels, and step when needed."""
        self.grooveTimer += 1

        # Some actions are only meant to occur when we step, rather than every tick.
        mainTick = False
        # Step to next row and update groove. Also mark this as a main tick.
        # It looks kind of complex but it just handles all the cases under "move to next row"
        if (
            self.grooveIndex == -1
        ):  # Force handling of first row when started. (grooveIndex is never -1 in normal operation)
            mainTick = True
            self.grooveIndex += 1
        elif self.grooveTimer >= program.p.currentSong.groove[self.grooveIndex]:
            self.grooveTimer = 0
            self.grooveIndex = (self.grooveIndex + 1) % len(
                program.p.currentSong.groove
            )
            program.p.currentPatternRow += 1
            if program.p.currentPatternRow >= program.p.currentSong.patternLength:
                program.p.currentPatternRow = 0
                program.p.currentMatrixRow += 1
                if (
                    program.p.currentMatrixRow
                    >= program.p.currentSong.visibleMatrixRows
                ):  # EOF
                    if self.loop == True:
                        program.p.currentMatrixRow = 0
                    elif self.loop > 0:
                        program.p.currentMatrixRow = 0
                        self.loop -= 1
                    else:
                        self.pause()
                        return []
            mainTick = True

        # Tick all channels and collate generated messages
        messages: list[Message | MetaMessage] = list()
        for channel in program.p.currentSong.channels:
            messages.extend(channel.tick(mainTick))

        return messages

    def playOffline(self) -> list[Message | MetaMessage]:
        """Play the entire song out to a list of timed messages. This can be easily dumped to file."""
        s = program.p.currentSong
        out = list()

        # Send metadata
        out.append(MetaMessage("track_name", name="TRACK NAME", time=0))
        out.append(MetaMessage("set_tempo", tempo=1000000, time=0))

        if (
            self.loop == True
        ):  # If we somehow accidentally try to loop infinitely -- don't.
            self.loop = False
        self.setPlaybackCursor(0, 0)
        self.ticksSinceLastMessage = 0
        self.playing = True

        while self.playing:
            _logger.debug("TICK")
            messages = self.tick()
            self.ticksSinceLastMessage += 1
            if len(messages) > 0:
                mspt = 1000 // s.clock
                messages[0].time = self.ticksSinceLastMessage * mspt
                self.ticksSinceLastMessage = 0
            _logger.debug(messages)
            out += messages

        return out

    def toFile(self, filename: str):
        """Use playOffline to save the song to file."""
        track = MidiTrack()
        for message in self.playOffline():
            track.append(message)
        MidiFile(type=0, ticks_per_beat=1000, tracks=[track]).save(filename)

    def setLiveMode(self):
        """Set this player to live playback mode."""

        if self.live:
            return

        def playbackDaemon():
            while True:
                self.resume.wait()

                # Time how long the update takes
                t0 = time.perf_counter()

                # Play messages
                for message in self.tick():
                    program.p.currentPort.send(message)
                    _logger.debug(message)

                # Timing. We figure out how long we should wait, then adjust based off how long processing took.
                tickLength = 1 / program.p.currentSong.clock  # Target amount to wait
                self.expectedTime += tickLength  # Absolute time we want to end up at
                elapsed = time.perf_counter() - t0  # How long ticking took
                self.actualTime += elapsed  # The actual absolute time
                diff = (
                    self.expectedTime - self.actualTime
                )  # Time till time we want to be at
                sleepTime = max(0, diff)  # How long to sleep for
                self.actualTime += sleepTime  # Update actual time
                time.sleep(sleepTime)  # Sleep

        # Start playback daemon
        Thread(name="PlaybackDaemon", target=playbackDaemon, daemon=True).start()

    def setPlaybackCursor(
        self, matrixRow: int | None = None, patternRow: int | None = None
    ):
        self.grooveIndex = -1  # Set to -1 to force handling of first row
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
        self.playing = True
        self.resume.set()
        self.lastMatrixRow = program.p.currentMatrixRow
        self.lastPatternRow = program.p.currentPatternRow

    def pause(self):
        self.playing = False
        self.resume.clear()
        self.allOff()

    def togglePlayback(self):
        if self.playing:
            self.pause()
        else:
            self.play()
