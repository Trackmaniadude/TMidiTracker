"""
Contains channel information and channel playback state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

import mido

from structures import program
from structures.effects import runEffect
from utils.constants import (
    BEND_STEPS_PER_SEMITONE,
    DEFAULT_BEND_RANGE,
    PITCH_BEND_MAX,
    PITCH_BEND_MIN,
)
from utils.misc import clamp
from utils.reactiveClass import ReactiveClass
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from structures.player import Player
    from structures.song import Song

_logger = logging.getLogger(__name__)


class ChannelPlaybackState(ReactiveClass):
    def __init__(self):
        super().__init__()

        self.velocities: dict[int, int] = dict()
        """[col, velocity] Current velocity for each column."""
        self.activeNotes: set[int] = set()
        """[note] All notes currently playing in this channel."""
        self.columnNotes: dict[int, int] = dict()
        """[col, note] What note each column is currently playing, if any."""

        self.pitchBends: dict[str, float] = dict()
        """[str, offset] Pitch offsets which will be summed to get the final bend.
        A dict is used to allow multiple effects to pitch bend without conflict.
        """
        self.lastBend: float = 0
        """Track changes so we only send bend messages when needed."""

        self.queuedNotes: dict[int, note] = dict()
        """[col, note] Notes to start/stop playing this tick. Intended to allow effects to mess with notes."""
        self.queuedVelocities: dict[int, velocity] = dict()
        """[col, vel] Velocity changes to make this tick."""

        self.scheduledEffects: dict[Callable[[Any], None], tuple[int, Any]] = dict()
        """[Effect callback, ticks until call, callback args] Effects to play on a timer."""
        self.effectData: dict[str, Any] = dict()
        """[tag, data] Arbitrary data store for effects. Note: shared between all effects on this channel."""

        self.setupContainerListen()

    def reset(self):
        self.velocities.clear()
        self.activeNotes.clear()
        self.columnNotes.clear()
        self.queuedNotes.clear()
        self.queuedVelocities.clear()
        self.scheduledEffects.clear()
        self.effectData.clear()
        self.pitchBends.clear()


class Channel(ReactiveClass):
    """
    Contains data for a single channel, as well as functions for processing said channel.
    """

    def __init__(self, song: Song, channel: int) -> None:
        super().__init__()

        self.song = song
        self.channel = channel

        self.noteColumns = 2
        self.effectColumns = 1

        self.playbackState = ChannelPlaybackState()
        self.tickState: int | None = None
        """Subtick counter. Set to None once all steps are completed."""

        self.changeFilter = {"noteColumns", "effectColumns"}
        self.Changed.connect(
            lambda name, key, old, new: setattr(program.p, "projectModified", True)
        )

        self.setupContainerListen()

    def toDict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "noteColumns": self.noteColumns,
            "effectColumns": self.effectColumns,
        }

    @classmethod
    def fromDict(cls, song: Song, channel: int) -> Channel:
        out = Channel(song, channel)
        # TODO:
        return out

    def __repr__(self) -> str:
        return f"Channel(channel: {self.channel}, noteColumns: {self.noteColumns}, effectColumns: {self.effectColumns})"

    def __str__(self) -> str:
        return f"Channel({self.channel}, {self.noteColumns}, {self.effectColumns})"

    EQ_KEYS = [
        "channel",
        "noteColumns",
        "effectColumns",
    ]

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Channel):
            return all(getattr(self, k) == getattr(value, k) for k in self.EQ_KEYS)
        return False

    def clearSchedule(self):
        self.playbackState.scheduledEffects.clear()

    def scheduleEffect[T](self, ticks: int, callback: Callable[[T], None], data: T):
        """
        Set a callback to be called on the channel in n ticks.
        Used for delayed effects or effects which stay active.
        (Note: immediate schedules (time=0) can't be done during or after scheduled effect processing.)
        (Note: schedule will be cleared on stop.)
        """
        if self.tickState is not None:
            if self.tickState > 2:
                ticks -= 1
                # Scheduling callbacks during or after the scheduled effect phase will add an extra tick of delay
                # Account for that here so schedule(1) will always occur next tick.
        self.playbackState.scheduledEffects[callback] = (ticks, data)
        _logger.debug(
            f"Scheduling effect. Current schedule {self.playbackState.scheduledEffects}"
        )

    def beginTick(self):
        """Reset subtick counter to begin processing a tick."""
        self.tickState = 0

    def tickProcessing(self):
        return self.tickState is not None

    def tick(
        self, player: Player, read: bool, matrixRow: int, patternRow: int
    ) -> list[mido.Message | mido.MetaMessage]:
        """
        Tick the channel, optionally reading commands at the current song playback position.
        Returns a list of midi messages. Messages have time set to 0; change in whatever's ticking things.

        Effects are applied between collecting notes and velocites and actually playing them, to allow effects to mess with them.
        """

        # Common data
        messages = list()
        currentPattern = program.p.currentSong.getPatternByLocation(
            self.channel, matrixRow
        )
        rowData = currentPattern.getRow(patternRow)
        if self.tickState is None:
            return messages

        # Process
        if self.tickState == 0:
            # Acquire notes and velocities
            self.tickState = 1

            self.playbackState.queuedNotes.clear()
            self.playbackState.queuedVelocities.clear()

            if read:
                self.playbackState.queuedNotes.update(rowData.notes)
                self.playbackState.queuedVelocities.update(rowData.velocities)

        elif self.tickState == 1:
            # Run effects
            self.tickState = 2

            if read:
                for col, effect in rowData.effects.items():
                    if col > self.effectColumns:
                        continue
                    try:
                        effectMessages = runEffect(self, player, effect)
                    except Exception as e:
                        _logger.warning(
                            f"{(matrixRow, patternRow, self.channel)} Effect processing failed: e"
                        )
                    else:
                        if effectMessages is not None:
                            messages.extend(effectMessages)

        elif self.tickState == 2:
            # Process scheduled effects
            self.tickState = 3

            for callback, (
                ticks,
                data,
            ) in self.playbackState.scheduledEffects.copy().items():
                if ticks <= 0:
                    _logger.debug(
                        f"Playing scheduled effect. Current schedule {self.playbackState.scheduledEffects}"
                    )
                    del self.playbackState.scheduledEffects[callback]
                    try:
                        callback(data)
                    except Exception as e:
                        _logger.warning(
                            f"{(matrixRow, patternRow, self.channel)} Scheduled effect callback failed: {e}"
                        )
                else:
                    self.playbackState.scheduledEffects[callback] = (ticks - 1, data)

        elif self.tickState == 3:
            self.tickState = None

            # Velocities
            for col, vel in self.playbackState.queuedVelocities.items():
                self.playbackState.velocities[col] = vel

            # Pitch Bend
            bend = sum(self.playbackState.pitchBends.values(), start=0.0)
            if bend != self.playbackState.lastBend:
                # Convert bend to midi value
                midiBend = clamp(
                    int(bend * BEND_STEPS_PER_SEMITONE), PITCH_BEND_MIN, PITCH_BEND_MAX
                )
                messages.append(
                    mido.Message("pitchwheel", channel=self.channel, pitch=midiBend)
                )
            self.playbackState.lastBend = bend

            # Notes
            for col, note in self.playbackState.queuedNotes.items():
                prevNote = self.playbackState.columnNotes.get(col)
                if note == "stop":
                    if prevNote:
                        if prevNote in self.playbackState.activeNotes:
                            self.playbackState.activeNotes.remove(prevNote)
                            del self.playbackState.columnNotes[col]
                            messages.append(
                                mido.Message(
                                    "note_off", channel=self.channel, note=prevNote
                                )
                            )
                elif note >= 0 and note <= 127:
                    if prevNote:
                        if prevNote in self.playbackState.activeNotes:
                            self.playbackState.activeNotes.remove(prevNote)
                            messages.append(
                                mido.Message(
                                    "note_off", channel=self.channel, note=prevNote
                                )
                            )
                    self.playbackState.columnNotes[col] = note
                    self.playbackState.activeNotes.add(note)
                    velocity = self.playbackState.velocities.get(col, 64)
                    messages.append(
                        mido.Message(
                            "note_on",
                            channel=self.channel,
                            note=note,
                            velocity=velocity,
                        )
                    )
                else:
                    _logger.warning(f"Out of range note ({note})")

        return messages

    def reset(self):
        """Reset the state of this channel."""
        self.playbackState.reset()

    def initMessages(self):
        # http://midi.teragonaudio.com/tech/midispec.htm
        return [
            mido.Message(
                "control_change", channel=self.channel, control=0x65, value=0x00
            ),  # RPN Coarse: Pitch Bend Range
            mido.Message(
                "control_change", channel=self.channel, control=0x64, value=0x00
            ),  # RPN Fine: Pitch Bend Range
            mido.Message(
                "control_change",
                channel=self.channel,
                control=0x06,
                value=DEFAULT_BEND_RANGE,
            ),  # Data Entry Coarse
            mido.Message(
                "control_change", channel=self.channel, control=0x26, value=0
            ),  # Data Entry Fine
        ]

    def seek(self, matrixRow: int, patternRow: int):
        """Reset and process the channel up to the given point."""
        # TODO: should this be full accurate or can I get away with one tick per row
