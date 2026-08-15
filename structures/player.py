"""
Live playback code.
"""

import logging
import threading
import time
from itertools import chain
from pathlib import Path
from threading import Event, Thread
from typing import Callable, cast

from mido import Message, MetaMessage, MidiFile, MidiTrack

from structures import program  # Note: Can't use during init
from structures.channel import Channel
from structures.effectClasses import AbstractEffect
from structures.effectManager import runEffect
from structures.effects.flow import Flow
from utils import event

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
        self.grooveOverride: tuple[int, ...] | None = None

        self.expectedTime: float = 0
        """For live mode, time we should wait to before starting the next tick."""
        self.actualTime: float = 0
        """For live mode, time we are currently at after processing this tick."""

        self.ticksSinceLastMessage: int = 0
        """Used for offline timing."""

        self.playing: bool = False
        self.loop: bool | int = True
        """If the player should loop. If it is set to an integer, it will count down until it hits 0, at which point playback will stop."""

        self.liveThread: Thread | None = None
        """Live playback thread."""

        self.currentMatrixRow: int = 0
        self.currentPatternRow: int = 0
        self.nextMatrixRow: int | None = None
        self.nextPatternRow: int | None = None

        self.doInitChannels: bool = True  # TODO: reset this when changing port

    def initChannels(self):
        return chain.from_iterable(
            channel.initMessages() for channel in program.p.currentSong.channels
        )

    def isLive(self):
        return self.liveThread is not None

    def tick(self) -> list[Message | MetaMessage]:
        """Run one tick on all channels, and step when needed."""
        self.grooveTimer += 1

        self.lastMatrixRow = self.currentMatrixRow
        self.lastPatternRow = self.currentPatternRow

        groove = (
            program.p.currentSong.groove
            if self.grooveOverride is None
            else self.grooveOverride
        )

        # Some actions are only meant to occur when we step, rather than every tick.
        mainTick = False
        # Step to next row and update groove. Also mark this as a main tick.
        # It looks kind of complex but it just handles all the cases under "move to next row"
        if (
            self.grooveIndex == -1
        ):  # Force handling of first row when started. (grooveIndex is never -1 in normal operation)
            mainTick = True
            self.grooveIndex += 1
        elif (
            self.grooveTimer >= groove[self.grooveIndex % len(groove)]
        ):  # Modulo to prevent errors when changing groove
            self.grooveTimer = 0
            self.grooveIndex = (self.grooveIndex + 1) % len(groove)

            # Jump Pattern Row
            if self.nextPatternRow is not None:
                self.currentPatternRow = self.nextPatternRow - 1
                # -1 so we can just run the main logic again
                self.nextPatternRow = None

            # Jump Matrix Row
            if self.nextMatrixRow is not None:
                self.currentMatrixRow = self.nextMatrixRow
                self.nextMatrixRow = None

            # Move to next row
            self.currentPatternRow += 1
            if self.currentPatternRow >= program.p.currentSong.patternLength:
                self.currentPatternRow = 0
                self.currentMatrixRow += 1
                if (
                    self.currentMatrixRow >= program.p.currentSong.visibleMatrixRows
                ):  # EOF
                    if self.loop == True:
                        self.currentMatrixRow = 0
                    elif self.loop > 0:
                        self.currentMatrixRow = 0
                        self.loop -= 1
                    else:
                        self.pause()
                        return []
            mainTick = True

        # Tick all channels and collate generated messages
        messages: list[Message | MetaMessage] = list()
        for channel in program.p.currentSong.channels:
            channel.beginTick()
        while any(
            channel.tickProcessing() for channel in program.p.currentSong.channels
        ):
            for channel in program.p.currentSong.channels:
                channelMessages = channel.tick(
                    self, mainTick, self.currentMatrixRow, self.currentPatternRow
                )
                messages.extend(channelMessages)

        return messages

    def playOffline(
        self, statusCallback: Callable[[int, int | None], None] | None = None
    ) -> tuple[list[Message | MetaMessage], int]:
        """
        Play the entire song out to a list of timed messages. This can be easily dumped to file.
        Also returns some extra information.
          Currently: ticks per beat (since this is needed to write to file)
        """

        # Determine song length so we can tell the user export progress
        # Unfortunately this requires iterating over the song
        # Value is in rows
        def getSongLength() -> int | None:
            self.playing = True
            self.currentMatrixRow = 0
            self.currentPatternRow = 0

            t = time.time()  # Watch time just in cases song jumps cause it to never end
            maxTime = 2

            flowEffects: list[type[AbstractEffect]] = [
                cast(type[AbstractEffect], effect) for effect in Flow.__subclasses__()
            ]
            flowEffectPrefixes = {effect.prefix for effect in flowEffects}

            dummyChannel = Channel(program.p.currentSong, -1)

            totalRows = 0
            columns = {10}.intersection(range(program.p.currentSong.visibleChannels))
            while (
                self.currentMatrixRow < program.p.currentSong.visibleMatrixRows
                and self.playing
            ):
                totalRows += program.p.currentSong.patternLength
                self.nextMatrixRow = self.currentMatrixRow + 1

                # Get effects
                patterns = [
                    program.p.currentSong.getPatternByLocation(
                        column, self.currentMatrixRow
                    )
                    for column in columns
                ]
                effects = chain.from_iterable(
                    pattern.effects.values() for pattern in patterns
                )
                targetEffects = [  # Get any effects that match flow effects
                    effect
                    for effect in effects
                    if len(effect) > 0
                    and any(  # If this effect starts with any of the known effects
                        all(
                            a == b for a, b in zip(effect, testEffect)
                        )  # Basically tuple startswith
                        for testEffect in flowEffectPrefixes
                    )
                ]

                if len(targetEffects) > 0:
                    for effect in targetEffects:
                        runEffect(dummyChannel, self, effect)

                self.currentMatrixRow = self.nextMatrixRow

                if time.time() - t > maxTime:
                    return None

            # Reset some things
            self.grooveIndex = 0
            self.grooveTimer = 0
            self.grooveOverride = None

            self.currentMatrixRow = 0
            self.currentPatternRow = 0
            self.nextMatrixRow = None
            self.nextPatternRow = None

            return totalRows

        songLength = getSongLength()
        _logger.info(f"Song is roughly {songLength} rows total.")

        for channel in program.p.currentSong.channels:
            channel.reset()

        s = program.p.currentSong
        out = list()

        out.extend(self.initChannels())

        # Determine time signature (makes midi nicer)
        # Assumes a quarter note is the minor split marker, a measure is the major split marker
        # If groove does not fit evenly into minor split, will give wonky results. TODO: tell the user that, not our problem here
        # TODO: this also fails if we later change the groove.
        def getTimeSignature() -> tuple[int, int, int, int]:
            # Determine ticks per quarter (per minor split)
            ticksPerQuarter = 0
            for i in range(s.minorSubdiv):
                ticksPerQuarter += s.groove[i % len(s.groove)]

            timeSigRaw = s.majorSubdiv / s.minorSubdiv
            # If this is an integer, use that as numerator
            # If it is not an integer, double the time signature (midi takes denom as a power of two, mido takes it raw, so we do raw here)
            # If this fails after a few times, ahh well, thats on the user for being weird (if this is you, do share, weird music is fun!)
            denominator = 4  # Quarter by default
            for i in range(6):  # How silly we get
                if timeSigRaw == int(timeSigRaw):
                    break
                timeSigRaw *= 2
                denominator *= 2

            num = int(timeSigRaw)
            den = denominator
            tspb = (
                s.minorSubdiv * 2
            )  # Currently assuming minor subdiv is visually 16th notes
            return num, den, tspb, ticksPerQuarter

        numerator, denominator, tspb, ticksPerBeat = getTimeSignature()

        _logger.debug(
            f"""

EXPORTING SONG
start info (may change)
clock={s.clock}
groove={s.groove}
usPerTick={1000000 // s.clock}
ticksPerBeat={ticksPerBeat}
inferredTimeSignature={numerator}/{denominator}
thirtySecondsPerBeat={tspb}
tempo={int(1000000 / s.clock) * ticksPerBeat}
        """
        )

        # Send metadata
        out.append(MetaMessage("track_name", name="TRACK NAME", time=0))
        out.append(
            MetaMessage(
                "set_tempo", tempo=int(1000000 / s.clock) * ticksPerBeat, time=0
            )
        )
        out.append(
            MetaMessage(
                "time_signature",
                numerator=numerator,
                denominator=denominator,
                clocks_per_click=ticksPerBeat,
                notated_32nd_notes_per_beat=tspb,
                time=0,
            )
        )

        if (
            self.loop == True
        ):  # If we somehow accidentally try to loop infinitely -- don't.
            self.loop = False
        self.setPlaybackCursor(0, 0)
        self.ticksSinceLastMessage = 0
        self.playing = True

        rowsPlayed = 0
        while self.playing:
            # _logger.debug("TICK")
            messages = self.tick()
            self.ticksSinceLastMessage += 1
            if len(messages) > 0:
                messages[0].time = self.ticksSinceLastMessage
                self.ticksSinceLastMessage = 0
            # _logger.debug(messages)
            if self.grooveTimer == 0:
                rowsPlayed += 1
            if statusCallback:
                statusCallback(rowsPlayed, songLength)
            out += messages
        out.append(MetaMessage("end_of_track", time=self.ticksSinceLastMessage))

        return out, ticksPerBeat

    def toFile(
        self,
        path: Path,
        statusCallback: Callable[[int, int | None], None] | None = None,
    ):
        """Use playOffline to save the song to file."""
        track = MidiTrack()
        messages, ticksPerBeat = self.playOffline(statusCallback)
        for message in messages:
            track.append(message)
        MidiFile(type=0, ticks_per_beat=ticksPerBeat, tracks=[track]).save(
            path.resolve()
        )

    def startLiveDaemon(self):
        """Set this player to live playback mode."""

        # Don't create a new live thread if one already exists (and is alive)
        # Do reset it though
        self.doInitChannels = True
        if self.liveThread is not None:
            if self.liveThread.is_alive():
                return

        def playbackDaemon():
            while True:
                self.resume.wait()

                # Time how long the update takes
                t0 = time.perf_counter()

                # Play messages
                if self.doInitChannels:
                    for message in self.initChannels():
                        program.p.currentPort.send(message)
                    self.doInitChannels = False
                for message in self.tick():
                    program.p.currentPort.send(message)
                    # _logger.debug(message)

                # Update UI
                def updateUI():
                    # event.dumpEvents = True
                    program.p.currentMatrixRow = self.currentMatrixRow
                    program.p.currentPatternRow = self.currentPatternRow
                    # event.dumpEvents = False

                if (
                    self.currentMatrixRow != self.lastMatrixRow
                    or self.currentPatternRow != self.lastPatternRow
                ):
                    program.p.tkRoot.after("idle", updateUI)

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
        self.liveThread = Thread(
            name="PlaybackDaemon", target=playbackDaemon, daemon=True
        )
        self.liveThread.start()

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
        self.currentMatrixRow = program.p.currentMatrixRow
        self.currentPatternRow = program.p.currentPatternRow

    def allOff(self):
        for channel in range(16):
            for note in range(128):
                message = Message("note_off", channel=channel, note=note)
                program.p.currentPort.send(message)

    def play(self):
        self.playing = True
        for channel in program.p.currentSong.channels:
            channel.reset()
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
