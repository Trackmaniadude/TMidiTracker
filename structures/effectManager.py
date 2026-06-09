"""
Channel effects
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mido import Message, MetaMessage

if __name__ == "__main__":
    import sys

    sys.path.append(".")

import logging
from typing import TYPE_CHECKING, NamedTuple

from structures import program
from structures.effectClasses import AbstractEffect, EffectCategory
from utils.constants import CHANNEL_ORDER, CHANNEL_ORDER_INVERSE
from utils.misc import mapRange
from utils.types_ import note, velocity

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player

_logger = logging.getLogger(__name__)


# TODO: given how common the pattern of effects that stay active is, maybe
# there should be a discrete structure for such "active" effects.


from structures.effects import *

effectsList: dict[tuple[int, ...], type[AbstractEffect]] = dict()


def getEffectsList(parentClass: type[EffectCategory]):
    for childClass in parentClass.__subclasses__():
        if issubclass(childClass, AbstractEffect):
            effectsList[childClass.prefix] = childClass
        else:
            getEffectsList(childClass)


getEffectsList(EffectCategory)


def getEffect(data: tuple[int, ...]) -> type[AbstractEffect] | None:
    for prefix, effect in effectsList.items():
        if data[: len(prefix)] == prefix:
            return effect
    return None


def runEffect(
    channel: Channel, player: Player, data: tuple[int, ...]
) -> None | list[Message | MetaMessage]:
    """Get an effect, and call it's actuate if it exists with data - effect prefix."""
    effect = getEffect(data)
    if effect:
        return effect.actuate(channel, player, data[len(effect.prefix) :])


if __name__ == "__main__":
    print("effects:")

    knownPrefixes = dict[tuple[int, ...], list[type[AbstractEffect]]]()

    def t(c: type[EffectCategory], l: int = 0):
        for s in c.__subclasses__():
            st = ""
            if issubclass(s, AbstractEffect):
                st = f"{s.prefixString()} - {s.__name__}"
                if s.prefix not in knownPrefixes:
                    knownPrefixes[s.prefix] = list()
                knownPrefixes[s.prefix].append(s)
            else:
                st = f"[{s.__name__}]"
            print(f"{"|  "*l}{st}")
            t(s, l + 1)

    t(EffectCategory)

    print()
    for prefix, effects in knownPrefixes.items():
        if len(effects) > 1:
            print(
                f"PREFIX {effects[0].prefixString()} USED BY {[e.__name__ for e in effects]}"
            )
    # for _, effect in effectsList.items():
    #     print(effect.__qualname__)
    #     print(effect.prefix)
    #     print(effect.color)
    # print()
    # print(getEffect((0, 0, 0)))
    # print(getEffect((0, 1, 0)))
    # print(getEffect((3, 0, 0)))
    # print(getEffect((3, 3, 3, 1)))
