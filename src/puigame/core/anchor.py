"""The Anchor enum: named points on a rect."""

from enum import Enum, auto


class Anchor(Enum):
    """Nine named points on a rect, used to position widgets."""

    CENTRE = auto()
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    MID_LEFT = auto()
    MID_RIGHT = auto()
    MID_TOP = auto()
    MID_BOTTOM = auto()
