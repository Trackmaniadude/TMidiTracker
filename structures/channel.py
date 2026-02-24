"""
Contains channel information and channel playback state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from structures.song import Song

import logging

import mido

from structures import program
from structures.effects import runEffect
from utils.reactiveClass import ReactiveClass

_logger = logging.getLogger(__name__)


class ChannelPlaybackState(ReactiveClass):
    def __init__(self):
        super().__init__()

        self.velocities: dict[int, int] = dict()
        """Current velocity for each column."""
        self.activeNotes: set[int] = set()
        """All notes currently playing in this channel."""
        self.columnNotes: dict[int, int] = dict()
        """What note each column is currently playing, if any."""

        self.setupContainerListen()


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

        self.setupContainerListen()

    def tick(self, read: bool) -> list[mido.Message | mido.MetaMessage]:
        """
        Tick the channel, optionally reading commands at the current song playback position.
        Returns a list of midi messages. Messages have time set to 0; change in whatever's ticking things.
        """

        messages = list()

        currentPattern = program.p.currentSong.getPatternByLocation(
            self.channel, program.p.currentMatrixRow
        )

        if read:
            rowData = currentPattern.getRow(program.p.currentPatternRow)

            # Apply all effects first
            for col, effect in rowData.effects.items():
                if col > self.effectColumns:
                    continue
                effectMessages = runEffect(effect, self)
                if effectMessages is not None:
                    messages.extend(effectMessages)

            # Determine velocities next
            for col, vel in rowData.velocities.items():
                self.playbackState.velocities[col] = vel

            # Play notes
            for col, note in rowData.notes.items():
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
                else:
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

        return messages

    def seek(self, matrixRow: int, patternRow: int):
        """Reset and process the channel up to the given point."""
        # TODO: should this be full accurate or can I get away with one tick per row
