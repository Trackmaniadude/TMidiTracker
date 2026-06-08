from dataclasses import dataclass
from typing import TYPE_CHECKING

from structures.effectClasses import AbstractEffect, EffectCategory

if TYPE_CHECKING:
    from structures.channel import Channel
    from structures.player import Player


class Extended(EffectCategory):
    pass


# FF00-FFFE
