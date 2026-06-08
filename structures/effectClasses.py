import logging
from typing import TYPE_CHECKING

from mido import Message, MetaMessage

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player

_logger = logging.getLogger(__name__)


class AbstractEffect:
    """Effect base class"""

    displayName: str
    """Display name."""
    prefix: tuple[int, ...]
    """Effect prefix. This identifies the effect."""
    color: str = "#000000"
    """Effect display color."""
    params: list[str] = [""]
    """Effect parameters. Should be a string list of the format [parameter layout, [parameter identifier, parameter name]]"""
    help: str = "DEFAULT HELP"
    """Help message."""

    @classmethod
    def actuate(
        cls, channel: Channel, player: Player, data: tuple[int, ...]
    ) -> None | list[Message | MetaMessage]:
        """Run effect code. May directly fiddle with channel data, or return MIDI messages."""
        _logger.warning(
            f"UNIMPLEMENTED EFFECT: {cls.__qualname__}, Channel {channel.channel}, Data {data}"
        )

    @classmethod
    def prefixString(cls) -> str:
        out = ""
        for n in cls.prefix:
            if n < 16:
                out += "0" + hex(n)[2:]
            else:
                out += hex(n)[2:]
        return out.upper()


# class EffectCategories:
#     MISC = ("Misc", "#000000")
#     PITCH = ("Pitch", "#000000")
#     TIME = ("Time", "#000000")
#     MISC = ("Misc", "#000000")


class EffectCategory:
    """
    For visual categorization of effects. Does not change effect indexing.

    To add an effect to a category, the effect should inherit the category.

    To make a subcategory, subclass the category instead of this class.
    """
