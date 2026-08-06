from dataclasses import dataclass
from typing import TYPE_CHECKING

from structures.effectClasses import AbstractEffect, EffectCategory

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Extended(EffectCategory):
    displayName = "Extended"
    description = "Reserved category for (ideally) less common effects should we run out of space."


# FF00-FFFE
