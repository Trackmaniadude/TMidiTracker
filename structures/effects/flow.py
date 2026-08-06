from dataclasses import dataclass
from typing import TYPE_CHECKING

from mido import Message, MetaMessage

from structures import program
from structures.effectClasses import AbstractEffect, EffectCategory
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Flow(EffectCategory):
    displayName = "Flow"
    description = "Effects that control song playback position."


# F0-FE


class End(Flow, AbstractEffect):
    displayName = "End Song"
    prefix = (0xF0,)
    params = ["F0"]
    help = "Stops playback."

    @classmethod
    def actuate(
        cls, channel: Channel, player: program.Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        player.pause()


class Loop(Flow, AbstractEffect):
    displayName = "Loop"
    prefix = (0xF4,)
    params = [
        "F4mm[pp][ll]",
        "mm",
        "Matrix Row",
        "[pp]",
        "Pattern Row",
        "[ll]",
        "Repeat Limit",
    ]
    help = (
        "Jump to another row, and optionally position in that row."
        "\nAlso has an optional repetition limit. Not specifying this will repeat "
        "indefinitely in live playback, or use the repeat amount for offline playback."
    )

    storeName = "LoopEffect{mat}{pat}"  # Was that the bite of '87??

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        storeName = cls.storeName.format(
            mat=player.currentMatrixRow, pat=player.currentPatternRow
        )

        matrixRow = data[0]
        patternRow = data[1] if len(data) > 1 else 0
        repeat = (
            data[2]
            if len(data) > 2
            else (None if player.isLive() else program.p.currentSong.loopCount)
        )

        if repeat is not None:
            count: int = channel.playbackState.effectData.get(storeName, repeat) - 1
            channel.playbackState.effectData[storeName] = count
            if count <= 0:
                del channel.playbackState.effectData[storeName]
                return

        player.nextMatrixRow = matrixRow
        player.nextPatternRow = patternRow


class Jump(Flow, AbstractEffect):
    displayName = "Jump"
    prefix = (0xF5,)
    params = [
        "F5mm[pp][cc]",
        "mm",
        "Matrix Row",
        "[pp]",
        "Pattern Row",
        "[cc]",
        "Countdown",
    ]
    help = (
        "Jump to another row, and optionally position in that row."
        "\nAlso has an optional countdown. Specifying this will ignore "
        "the jump until it has been passed n-1 times (so specifying 2 "
        "will jump the second time around)"
    )

    storeName = "JumpEffect{mat}{pat}"

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        storeName = cls.storeName.format(
            mat=player.currentMatrixRow, pat=player.currentPatternRow
        )

        matrixRow = data[0]
        patternRow = data[1] if len(data) > 1 else 0
        countdown = data[2] if len(data) > 2 else 1

        count: int = channel.playbackState.effectData.get(storeName, countdown) - 1
        channel.playbackState.effectData[storeName] = count
        if count <= 0:
            del channel.playbackState.effectData[storeName]
            player.nextMatrixRow = matrixRow
            player.nextPatternRow = patternRow


class JumpRel(Flow, AbstractEffect):
    displayName = "Jump Relative"
    prefix = (0xF6,)
    params = [
        "F6mm[pp][cc]",
        "mm",
        "Matrix Row Offset",
        "[pp]",
        "Pattern Row Offset",
        "[cc]",
        "Countdown",
    ]
    help = (
        "Jump to another row, and optionally position in that row. "
        "Rows are specified as offsets. However, pattern offset only applies "
        "if row offset is 0, otherwise pattern is set absolute."
        "\nAlso has an optional countdown. Specifying this will ignore "
        "the jump until it has been passed n-1 times (so specifying 2 "
        "will jump the second time around)"
    )

    storeName = "JumpRelativeEffect{mat}{pat}"

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        storeName = cls.storeName.format(
            mat=player.currentMatrixRow, pat=player.currentPatternRow
        )

        matrixRow = data[0]
        patternRow = data[1] if len(data) > 1 else 0
        countdown = data[2] if len(data) > 2 else 1

        count: int = channel.playbackState.effectData.get(storeName, countdown) - 1
        channel.playbackState.effectData[storeName] = count
        if count <= 0:
            del channel.playbackState.effectData[storeName]
            player.nextMatrixRow = player.currentMatrixRow + matrixRow
            if matrixRow == 0:
                player.nextPatternRow = player.currentPatternRow + patternRow
            else:
                player.nextPatternRow = patternRow
