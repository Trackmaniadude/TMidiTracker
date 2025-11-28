"""
Contains channel information and channel playback state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures.pattern import Pattern
    from structures.song import Song

import mido

from structures import program
from utils.reactiveClass import ReactiveClass

import logging
_logger = logging.getLogger(__name__)


@dataclass
class ChannelPlaybackState:
    velocities: dict[int, int] = field(default_factory=lambda: dict())
    """Current velocity for each subchannel."""


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

        return messages

    def seek(self, matrixRow: int, patternRow: int):
        """Reset and process the channel up to the given point."""
        # TODO: should this be full accurate or can I get away with one tick per row
