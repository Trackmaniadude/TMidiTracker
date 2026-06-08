from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from mido import Message, MetaMessage

from structures import program
from structures.effectClasses import AbstractEffect, EffectCategory
from utils.constants import CHANNEL_ORDER
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Harmonization(EffectCategory):
    pass


# 30-3F


class EchoDouble(Harmonization, AbstractEffect):
    displayName = "Echo/Double"
    prefix = (0x30,)  # TODO:
    params = ["30[cc][dd][oo]", "cc", "Channel", "dd", "Delay", "oo", "Offset"]
    help = (
        "Copy notes from another channel and play them in this channel."
        " Notes can have an optional delay (for echo effects) and pitch offset (for harmonization/doubling)."
        " Offset is centered at 0x80, to allow for negative values."
        " Omitting the channel will turn off the effect."
        " Only one instance of the effect can be run per channel; adding another will override the first."
        "\n(Note: behavior of this effect when the source channel also has an Echo/Double effect is currently undefined.)"
    )

    storeName = "EchoDouble"

    class StoreValue(NamedTuple):
        targetChannel: int
        delay: int
        offset: int

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        targetChannel = CHANNEL_ORDER[data[0]] if len(data) > 0 else None
        delay = data[1] if len(data) > 1 else 0
        offset = data[2] - 0x80 if len(data) > 2 else 0

        if targetChannel is None:
            channel.playbackState.effectData.pop(cls.storeName, None)
            return

        def loop(_: None):
            data = channel.playbackState.effectData.get(cls.storeName, None)
            if data is None:
                return
            if type(data) is not cls.StoreValue:
                return  # Mostly for the type checker without using a static reference

            targetChannel, delay, offset = data

            source = program.p.currentSong.channels[targetChannel]
            notes: dict[int, note] = {
                col: (note + offset if type(note) is int else note)
                for col, note in source.playbackState.queuedNotes.items()
            }
            vels = source.playbackState.queuedVelocities.copy()

            if delay <= 0:
                channel.playbackState.queuedNotes.update(notes)
                channel.playbackState.queuedVelocities.update(vels)
            else:
                if len(notes) > 0 or len(vels) > 0:

                    def delayCallback(
                        data: tuple[dict[int, note], dict[int, velocity]],
                    ):
                        # Has to be defined in the loop body due to the schedule system indexing on the callback functions
                        # TODO: investigate the impact of doing this vs some other identifier
                        notes, vels = data
                        channel.playbackState.queuedNotes.update(notes)
                        channel.playbackState.queuedVelocities.update(vels)

                    channel.scheduleEffect(delay, delayCallback, (notes, vels))

            channel.scheduleEffect(1, loop, None)

        start = cls.storeName not in channel.playbackState.effectData
        channel.playbackState.effectData[cls.storeName] = cls.StoreValue(
            targetChannel, delay, offset
        )
        if start:
            loop(None)
