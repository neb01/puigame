"""Set of flags that widgets use to control State options."""

from enum import Flag, auto


class State(Flag):
    """Possible widget state flags."""

    BASE = 0
    DISABLED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    CHECKED = auto()
    EDITING = auto()
